"""Database optimization utilities.

Provides index analysis, connection pool monitoring, and query plan analysis
for optimizing PostgreSQL/SQLite database performance.
"""

import time
import logging
from typing import Optional
from dataclasses import dataclass

from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


@dataclass
class IndexInfo:
    """Database index information."""

    table_name: str
    index_name: str
    columns: list[str]
    is_unique: bool


@dataclass
class ConnectionPoolStats:
    """Connection pool statistics."""

    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    max_overflow: int


class DatabaseOptimizer:
    """Database optimization and monitoring utilities."""

    def __init__(self, engine: Engine):
        self.engine = engine
        self._is_postgres = "postgresql" in str(engine.url)
        self._is_sqlite = "sqlite" in str(engine.url)

    def get_connection_pool_stats(self) -> ConnectionPoolStats:
        """Get current connection pool statistics."""
        pool = self.engine.pool
        return ConnectionPoolStats(
            pool_size=pool.size() if hasattr(pool, "size") else 0,
            checked_in=pool.checkedin() if hasattr(pool, "checkedin") else 0,
            checked_out=pool.checkedout() if hasattr(pool, "checkedout") else 0,
            overflow=pool.overflow() if hasattr(pool, "overflow") else 0,
            max_overflow=getattr(pool, "_max_overflow", 0),
        )

    def get_table_sizes(self, db: Session) -> dict[str, dict]:
        """Get size information for all tables."""
        if self._is_postgres:
            return self._get_postgres_table_sizes(db)
        return self._get_sqlite_table_sizes(db)

    def _get_postgres_table_sizes(self, db: Session) -> dict[str, dict]:
        """Get PostgreSQL table sizes with row counts."""
        result = db.execute(text("""
            SELECT 
                schemaname || '.' || tablename AS table_name,
                pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS total_size,
                pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) AS data_size,
                pg_size_pretty(
                    pg_total_relation_size(schemaname || '.' || tablename) - 
                    pg_relation_size(schemaname || '.' || tablename)
                ) AS index_size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC
        """))

        tables = {}
        for row in result:
            table_name = row[0].replace("public.", "")
            tables[table_name] = {
                "total_size": row[1],
                "data_size": row[2],
                "index_size": row[3],
            }

        # Get row counts
        for table_name in tables:
            try:
                count = db.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                ).scalar()
                tables[table_name]["row_count"] = count
            except Exception:
                tables[table_name]["row_count"] = -1

        return tables

    def _get_sqlite_table_sizes(self, db: Session) -> dict[str, dict]:
        """Get SQLite table sizes with row counts."""
        result = db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = {}
        for row in result:
            table_name = row[0]
            try:
                count = db.execute(
                    text(f"SELECT COUNT(*) FROM \"{table_name}\"")
                ).scalar()
                tables[table_name] = {
                    "row_count": count,
                    "total_size": "N/A (SQLite)",
                    "data_size": "N/A",
                    "index_size": "N/A",
                }
            except Exception:
                tables[table_name] = {"row_count": -1}

        return tables

    def get_all_indexes(self) -> list[IndexInfo]:
        """Get all indexes across all tables."""
        inspector = inspect(self.engine)
        indexes = []

        for table_name in inspector.get_table_names():
            for idx in inspector.get_indexes(table_name):
                indexes.append(IndexInfo(
                    table_name=table_name,
                    index_name=idx["name"],
                    columns=idx["column_names"],
                    is_unique=idx.get("unique", False),
                ))

        return indexes

    def analyze_missing_indexes(self, db: Session) -> list[dict]:
        """Suggest missing indexes based on common query patterns."""
        suggestions = []

        # Check for foreign keys without indexes
        inspector = inspect(self.engine)
        for table_name in inspector.get_table_names():
            fks = inspector.get_foreign_keys(table_name)
            existing_indexes = {
                tuple(idx["column_names"])
                for idx in inspector.get_indexes(table_name)
            }

            for fk in fks:
                fk_cols = tuple(fk["constrained_columns"])
                if fk_cols not in existing_indexes:
                    suggestions.append({
                        "table": table_name,
                        "columns": list(fk_cols),
                        "reason": f"Foreign key to {fk['referred_table']} not indexed",
                        "priority": "HIGH",
                    })

        return suggestions

    def explain_query(self, db: Session, query_text: str) -> list[str]:
        """Run EXPLAIN on a query and return the plan."""
        try:
            if self._is_postgres:
                result = db.execute(text(f"EXPLAIN ANALYZE {query_text}"))
            else:
                result = db.execute(text(f"EXPLAIN QUERY PLAN {query_text}"))
            return [str(row) for row in result]
        except Exception as e:
            logger.error("Failed to explain query: %s", e)
            return [f"Error: {e}"]

    def run_maintenance(self, db: Session) -> dict[str, str]:
        """Run database maintenance operations."""
        results = {}

        if self._is_postgres:
            try:
                db.execute(text("ANALYZE"))
                results["analyze"] = "completed"
            except Exception as e:
                results["analyze"] = f"failed: {e}"
        elif self._is_sqlite:
            try:
                db.execute(text("ANALYZE"))
                results["analyze"] = "completed"
            except Exception as e:
                results["analyze"] = f"failed: {e}"

        return results

    def get_database_info(self, db: Session) -> dict:
        """Get comprehensive database information."""
        info = {
            "engine": str(self.engine.url).split("@")[-1] if "@" in str(self.engine.url) else str(self.engine.url),
            "dialect": self.engine.dialect.name,
            "driver": self.engine.dialect.driver,
            "pool_stats": {
                "pool_size": self.get_connection_pool_stats().pool_size,
                "checked_in": self.get_connection_pool_stats().checked_in,
                "checked_out": self.get_connection_pool_stats().checked_out,
            },
            "tables": len(inspect(self.engine).get_table_names()),
            "indexes": len(self.get_all_indexes()),
        }

        if self._is_postgres:
            try:
                version = db.execute(text("SELECT version()")).scalar()
                info["version"] = version
            except Exception:
                pass

        return info
