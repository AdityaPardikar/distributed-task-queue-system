"""Database maintenance and dead letter queue management.

Provides automated database maintenance (VACUUM, ANALYZE, REINDEX),
dead letter queue processing, and system health monitoring.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from dataclasses import dataclass, field

from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class MaintenanceResult:
    """Result of a maintenance operation."""

    operation: str
    success: bool
    message: str
    duration_ms: float = 0
    details: dict = field(default_factory=dict)


@dataclass
class DeadLetterEntry:
    """A task that has been moved to the dead letter queue."""

    task_id: str
    original_queue: str
    error_message: str
    retry_count: int
    failed_at: str
    payload: Optional[dict] = None


class MaintenanceManager:
    """Manages database maintenance and system health operations."""

    def __init__(self, session_factory):
        """Initialize with a SQLAlchemy session factory (sessionmaker)."""
        self.session_factory = session_factory

    def run_vacuum(self, table_name: Optional[str] = None) -> MaintenanceResult:
        """Run VACUUM on PostgreSQL database or specific table."""
        import time
        start = time.time()

        try:
            # VACUUM must run outside a transaction
            from sqlalchemy import create_engine
            engine = self.session_factory.kw.get("bind") if hasattr(self.session_factory, "kw") else None

            if engine is None:
                session = self.session_factory()
                engine = session.get_bind()
                session.close()

            with engine.connect() as conn:
                conn = conn.execution_options(isolation_level="AUTOCOMMIT")
                if table_name:
                    conn.execute(text(f"VACUUM ANALYZE {table_name}"))
                    msg = f"VACUUM ANALYZE completed for {table_name}"
                else:
                    conn.execute(text("VACUUM ANALYZE"))
                    msg = "VACUUM ANALYZE completed for all tables"

            duration = (time.time() - start) * 1000
            logger.info(msg)
            return MaintenanceResult(
                operation="vacuum", success=True, message=msg, duration_ms=duration
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            logger.error("VACUUM failed: %s", e)
            return MaintenanceResult(
                operation="vacuum",
                success=False,
                message=f"VACUUM failed: {e}",
                duration_ms=duration,
            )

    def run_reindex(self, table_name: Optional[str] = None) -> MaintenanceResult:
        """Reindex database tables."""
        import time
        start = time.time()

        try:
            session = self.session_factory()
            engine = session.get_bind()
            session.close()

            with engine.connect() as conn:
                conn = conn.execution_options(isolation_level="AUTOCOMMIT")
                if table_name:
                    conn.execute(text(f"REINDEX TABLE {table_name}"))
                    msg = f"REINDEX completed for {table_name}"
                else:
                    conn.execute(text("REINDEX DATABASE CURRENT_DATABASE()"))
                    msg = "REINDEX completed for database"

            duration = (time.time() - start) * 1000
            return MaintenanceResult(
                operation="reindex", success=True, message=msg, duration_ms=duration
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return MaintenanceResult(
                operation="reindex",
                success=False,
                message=f"REINDEX failed: {e}",
                duration_ms=duration,
            )

    def analyze_tables(self) -> MaintenanceResult:
        """Run ANALYZE on all tables to update query planner statistics."""
        import time
        start = time.time()

        try:
            session = self.session_factory()
            engine = session.get_bind()
            session.close()

            with engine.connect() as conn:
                conn = conn.execution_options(isolation_level="AUTOCOMMIT")
                conn.execute(text("ANALYZE"))

            duration = (time.time() - start) * 1000
            return MaintenanceResult(
                operation="analyze",
                success=True,
                message="ANALYZE completed for all tables",
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return MaintenanceResult(
                operation="analyze",
                success=False,
                message=f"ANALYZE failed: {e}",
                duration_ms=duration,
            )

    def get_table_bloat(self) -> list[dict]:
        """Check table bloat (PostgreSQL only)."""
        try:
            session = self.session_factory()
            result = session.execute(text("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as total_size,
                    pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) as table_size,
                    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename) - pg_relation_size(schemaname || '.' || tablename)) as index_size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC
            """))
            tables = [
                {
                    "schema": row[0],
                    "table": row[1],
                    "total_size": row[2],
                    "table_size": row[3],
                    "index_size": row[4],
                }
                for row in result
            ]
            session.close()
            return tables
        except Exception as e:
            logger.error("Table bloat check failed: %s", e)
            return []

    def get_long_running_queries(self, min_duration_seconds: int = 30) -> list[dict]:
        """Get currently running queries exceeding duration threshold."""
        try:
            session = self.session_factory()
            result = session.execute(text("""
                SELECT
                    pid,
                    now() - pg_stat_activity.query_start AS duration,
                    query,
                    state
                FROM pg_stat_activity
                WHERE (now() - pg_stat_activity.query_start) > interval ':seconds seconds'
                AND state != 'idle'
                ORDER BY duration DESC
            """), {"seconds": min_duration_seconds})

            queries = [
                {
                    "pid": row[0],
                    "duration": str(row[1]),
                    "query": row[2][:200] if row[2] else "",
                    "state": row[3],
                }
                for row in result
            ]
            session.close()
            return queries
        except Exception as e:
            logger.error("Long running queries check failed: %s", e)
            return []

    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> MaintenanceResult:
        """Clean up expired user sessions / tokens."""
        import time
        start = time.time()

        try:
            session = self.session_factory()
            cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

            # Try to clean up any session-like tables
            inspector = inspect(session.get_bind())
            tables = inspector.get_table_names()
            cleaned = 0

            if "user_sessions" in tables:
                result = session.execute(
                    text("DELETE FROM user_sessions WHERE created_at < :cutoff"),
                    {"cutoff": cutoff},
                )
                cleaned += result.rowcount

            if "refresh_tokens" in tables:
                result = session.execute(
                    text("DELETE FROM refresh_tokens WHERE expires_at < :now"),
                    {"now": datetime.now(timezone.utc)},
                )
                cleaned += result.rowcount

            session.commit()
            session.close()

            duration = (time.time() - start) * 1000
            return MaintenanceResult(
                operation="cleanup_sessions",
                success=True,
                message=f"Cleaned up {cleaned} expired sessions/tokens",
                duration_ms=duration,
                details={"cleaned_count": cleaned},
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return MaintenanceResult(
                operation="cleanup_sessions",
                success=False,
                message=f"Session cleanup failed: {e}",
                duration_ms=duration,
            )

    def cleanup_old_tasks(
        self, days: int = 90, statuses: Optional[list[str]] = None
    ) -> MaintenanceResult:
        """Archive or delete old completed/failed tasks."""
        import time
        start = time.time()

        if statuses is None:
            statuses = ["completed", "failed", "cancelled"]

        try:
            session = self.session_factory()
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            placeholders = ", ".join(f":status_{i}" for i in range(len(statuses)))
            params = {"cutoff": cutoff}
            params.update({f"status_{i}": s for i, s in enumerate(statuses)})

            result = session.execute(
                text(
                    f"DELETE FROM tasks WHERE status IN ({placeholders}) "
                    f"AND updated_at < :cutoff"
                ),
                params,
            )
            cleaned = result.rowcount
            session.commit()
            session.close()

            duration = (time.time() - start) * 1000
            return MaintenanceResult(
                operation="cleanup_tasks",
                success=True,
                message=f"Cleaned up {cleaned} old tasks (>{days} days, statuses: {statuses})",
                duration_ms=duration,
                details={"cleaned_count": cleaned, "days": days, "statuses": statuses},
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return MaintenanceResult(
                operation="cleanup_tasks",
                success=False,
                message=f"Task cleanup failed: {e}",
                duration_ms=duration,
            )

    def get_system_health(self) -> dict:
        """Get overall system health metrics."""
        health = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
        }

        # Database connectivity
        try:
            session = self.session_factory()
            session.execute(text("SELECT 1"))
            health["checks"]["database"] = {"status": "healthy", "message": "Connected"}
            session.close()
        except Exception as e:
            health["checks"]["database"] = {"status": "unhealthy", "message": str(e)}
            health["status"] = "unhealthy"

        # Database size
        try:
            session = self.session_factory()
            result = session.execute(text(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            ))
            size = result.scalar()
            health["checks"]["database_size"] = {"status": "healthy", "size": size}
            session.close()
        except Exception:
            health["checks"]["database_size"] = {"status": "unknown"}

        # Connection count
        try:
            session = self.session_factory()
            result = session.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
            ))
            count = result.scalar()
            health["checks"]["connections"] = {
                "status": "healthy" if count < 80 else "warning",
                "active_connections": count,
            }
            session.close()
        except Exception:
            health["checks"]["connections"] = {"status": "unknown"}

        # Table counts
        try:
            session = self.session_factory()
            inspector = inspect(session.get_bind())
            tables = inspector.get_table_names()
            table_counts = {}
            for table in tables:
                try:
                    result = session.execute(text(f'SELECT count(*) FROM "{table}"'))
                    table_counts[table] = result.scalar()
                except Exception:
                    table_counts[table] = -1
            health["checks"]["tables"] = {
                "status": "healthy",
                "table_count": len(tables),
                "row_counts": table_counts,
            }
            session.close()
        except Exception:
            health["checks"]["tables"] = {"status": "unknown"}

        return health

    def run_full_maintenance(self) -> list[MaintenanceResult]:
        """Run all maintenance operations."""
        results = []

        results.append(self.run_vacuum())
        results.append(self.analyze_tables())
        results.append(self.cleanup_expired_sessions())

        return results
