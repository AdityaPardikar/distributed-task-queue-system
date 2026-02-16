"""Database backup and restore utilities.

Provides PostgreSQL pg_dump integration, automated backup scheduling,
point-in-time recovery support, and backup verification.
"""

import os
import shutil
import logging
import subprocess
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

BACKUP_DIR = Path("backups")


@dataclass
class BackupInfo:
    """Information about a database backup."""

    filename: str
    filepath: str
    size_bytes: int
    created_at: str
    checksum: str
    database_url: str
    backup_type: str  # full, incremental
    verified: bool = False


class BackupManager:
    """Manages database backups and restores."""

    def __init__(self, database_url: str, backup_dir: Optional[str] = None):
        self.database_url = database_url
        self.backup_dir = Path(backup_dir) if backup_dir else BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._is_postgres = "postgresql" in database_url
        self._is_sqlite = "sqlite" in database_url

    def create_backup(self, backup_name: Optional[str] = None) -> BackupInfo:
        """Create a database backup."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        name = backup_name or f"taskflow_backup_{timestamp}"

        if self._is_postgres:
            return self._backup_postgres(name)
        elif self._is_sqlite:
            return self._backup_sqlite(name)
        else:
            raise ValueError(f"Unsupported database type: {self.database_url}")

    def _backup_postgres(self, name: str) -> BackupInfo:
        """Create PostgreSQL backup using pg_dump."""
        filepath = self.backup_dir / f"{name}.sql"

        # Parse database URL for pg_dump
        # Format: postgresql://user:password@host:port/dbname
        url = self.database_url
        parts = url.replace("postgresql://", "").split("@")
        user_pass = parts[0].split(":")
        host_db = parts[1].split("/")
        host_port = host_db[0].split(":")

        env = os.environ.copy()
        env["PGPASSWORD"] = user_pass[1] if len(user_pass) > 1 else ""

        cmd = [
            "pg_dump",
            "-h", host_port[0],
            "-p", host_port[1] if len(host_port) > 1 else "5432",
            "-U", user_pass[0],
            "-d", host_db[1],
            "-F", "p",  # plain text format
            "-f", str(filepath),
            "--clean",
            "--if-exists",
        ]

        try:
            result = subprocess.run(
                cmd, env=env, capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                logger.error("pg_dump failed: %s", result.stderr)
                raise RuntimeError(f"pg_dump failed: {result.stderr}")

            logger.info("PostgreSQL backup created: %s", filepath)
        except FileNotFoundError:
            logger.warning("pg_dump not found, creating SQLAlchemy backup instead")
            return self._backup_via_sqlalchemy(name)

        checksum = self._calculate_checksum(filepath)
        size = filepath.stat().st_size

        return BackupInfo(
            filename=filepath.name,
            filepath=str(filepath),
            size_bytes=size,
            created_at=datetime.now(timezone.utc).isoformat(),
            checksum=checksum,
            database_url=self.database_url.split("@")[-1],  # strip credentials
            backup_type="full",
        )

    def _backup_sqlite(self, name: str) -> BackupInfo:
        """Create SQLite backup by copying the database file."""
        # Extract path from sqlite URL
        db_path = self.database_url.replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = db_path[2:]

        filepath = self.backup_dir / f"{name}.db"

        if os.path.exists(db_path):
            shutil.copy2(db_path, filepath)
        else:
            # In-memory or file doesn't exist
            raise FileNotFoundError(f"SQLite database not found: {db_path}")

        checksum = self._calculate_checksum(filepath)
        size = filepath.stat().st_size

        return BackupInfo(
            filename=filepath.name,
            filepath=str(filepath),
            size_bytes=size,
            created_at=datetime.now(timezone.utc).isoformat(),
            checksum=checksum,
            database_url=db_path,
            backup_type="full",
        )

    def _backup_via_sqlalchemy(self, name: str) -> BackupInfo:
        """Fallback: backup via SQLAlchemy data export (JSON)."""
        import json
        from sqlalchemy import create_engine, inspect, text

        engine = create_engine(self.database_url)
        inspector = inspect(engine)
        filepath = self.backup_dir / f"{name}.json"

        backup_data = {
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "database_url": self.database_url.split("@")[-1],
                "tables": [],
            },
            "tables": {},
        }

        with engine.connect() as conn:
            for table_name in inspector.get_table_names():
                backup_data["metadata"]["tables"].append(table_name)
                result = conn.execute(text(f'SELECT * FROM "{table_name}"'))
                columns = list(result.keys())
                rows = []
                for row in result:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        val = row[i]
                        if isinstance(val, datetime):
                            val = val.isoformat()
                        row_dict[col] = val
                    rows.append(row_dict)
                backup_data["tables"][table_name] = {
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                }

        with open(filepath, "w") as f:
            json.dump(backup_data, f, indent=2, default=str)

        checksum = self._calculate_checksum(filepath)
        size = filepath.stat().st_size

        return BackupInfo(
            filename=filepath.name,
            filepath=str(filepath),
            size_bytes=size,
            created_at=datetime.now(timezone.utc).isoformat(),
            checksum=checksum,
            database_url=self.database_url.split("@")[-1],
            backup_type="full",
        )

    def restore_backup(self, backup_path: str) -> bool:
        """Restore database from backup file."""
        path = Path(backup_path)

        if not path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        if path.suffix == ".sql" and self._is_postgres:
            return self._restore_postgres(path)
        elif path.suffix == ".db" and self._is_sqlite:
            return self._restore_sqlite(path)
        elif path.suffix == ".json":
            return self._restore_from_json(path)
        else:
            raise ValueError(f"Unknown backup format: {path.suffix}")

    def _restore_postgres(self, filepath: Path) -> bool:
        """Restore PostgreSQL backup."""
        url = self.database_url
        parts = url.replace("postgresql://", "").split("@")
        user_pass = parts[0].split(":")
        host_db = parts[1].split("/")
        host_port = host_db[0].split(":")

        env = os.environ.copy()
        env["PGPASSWORD"] = user_pass[1] if len(user_pass) > 1 else ""

        cmd = [
            "psql",
            "-h", host_port[0],
            "-p", host_port[1] if len(host_port) > 1 else "5432",
            "-U", user_pass[0],
            "-d", host_db[1],
            "-f", str(filepath),
        ]

        try:
            result = subprocess.run(
                cmd, env=env, capture_output=True, text=True, timeout=600
            )
            if result.returncode != 0:
                logger.error("Restore failed: %s", result.stderr)
                return False
            logger.info("PostgreSQL restore completed from: %s", filepath)
            return True
        except Exception as e:
            logger.error("Restore error: %s", e)
            return False

    def _restore_sqlite(self, filepath: Path) -> bool:
        """Restore SQLite backup."""
        db_path = self.database_url.replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = db_path[2:]

        try:
            shutil.copy2(filepath, db_path)
            logger.info("SQLite restore completed from: %s", filepath)
            return True
        except Exception as e:
            logger.error("SQLite restore failed: %s", e)
            return False

    def _restore_from_json(self, filepath: Path) -> bool:
        """Restore from JSON backup."""
        import json
        from sqlalchemy import create_engine, text

        try:
            with open(filepath) as f:
                backup_data = json.load(f)

            engine = create_engine(self.database_url)
            with engine.begin() as conn:
                for table_name, table_data in backup_data.get("tables", {}).items():
                    columns = table_data["columns"]
                    for row in table_data["rows"]:
                        cols = ", ".join(f'"{c}"' for c in columns)
                        placeholders = ", ".join(f":{c}" for c in columns)
                        sql = f'INSERT INTO "{table_name}" ({cols}) VALUES ({placeholders})'
                        conn.execute(text(sql), row)

            logger.info("JSON restore completed from: %s", filepath)
            return True
        except Exception as e:
            logger.error("JSON restore failed: %s", e)
            return False

    def list_backups(self) -> list[BackupInfo]:
        """List all available backups."""
        backups = []
        for f in sorted(self.backup_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.suffix in (".sql", ".db", ".json"):
                backups.append(BackupInfo(
                    filename=f.name,
                    filepath=str(f),
                    size_bytes=f.stat().st_size,
                    created_at=datetime.fromtimestamp(
                        f.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                    checksum=self._calculate_checksum(f),
                    database_url="",
                    backup_type="full",
                ))
        return backups

    def verify_backup(self, backup_path: str) -> dict:
        """Verify backup file integrity."""
        path = Path(backup_path)
        if not path.exists():
            return {"valid": False, "error": "File not found"}

        result = {
            "valid": True,
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "checksum": self._calculate_checksum(path),
        }

        if path.suffix == ".json":
            import json
            try:
                with open(path) as f:
                    data = json.load(f)
                result["tables"] = len(data.get("tables", {}))
                result["total_rows"] = sum(
                    t.get("row_count", 0) for t in data.get("tables", {}).values()
                )
            except json.JSONDecodeError as e:
                result["valid"] = False
                result["error"] = f"Invalid JSON: {e}"
        elif path.suffix == ".sql":
            with open(path) as f:
                content = f.read()
            result["statements"] = content.count(";")
            result["has_create"] = "CREATE TABLE" in content.upper()
            result["has_insert"] = "INSERT INTO" in content.upper()

        return result

    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """Remove old backups, keeping only the most recent N."""
        backups = sorted(
            self.backup_dir.iterdir(),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )
        removed = 0
        for f in backups[keep_count:]:
            if f.suffix in (".sql", ".db", ".json"):
                f.unlink()
                removed += 1
                logger.info("Removed old backup: %s", f.name)
        return removed

    @staticmethod
    def _calculate_checksum(filepath: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
