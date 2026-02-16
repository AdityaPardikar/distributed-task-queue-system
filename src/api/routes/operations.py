"""Operations API endpoints for backup, maintenance, and system health."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.db.session import get_db, engine
from src.operations.backup import BackupManager
from src.operations.config_validator import ConfigValidator
from src.operations.maintenance import MaintenanceManager
from src.config import get_settings

router = APIRouter(prefix="/operations", tags=["operations"])

settings = get_settings()


def get_backup_manager() -> BackupManager:
    return BackupManager(settings.DATABASE_URL)


def get_maintenance_manager() -> MaintenanceManager:
    from src.db.session import SessionLocal
    return MaintenanceManager(SessionLocal)


# --- Backup endpoints ---

@router.post("/backups")
async def create_backup(name: Optional[str] = None):
    """Create a database backup."""
    try:
        manager = get_backup_manager()
        backup = manager.create_backup(backup_name=name)
        return {
            "status": "success",
            "backup": {
                "filename": backup.filename,
                "filepath": backup.filepath,
                "size_bytes": backup.size_bytes,
                "checksum": backup.checksum,
                "created_at": backup.created_at,
                "type": backup.backup_type,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.get("/backups")
async def list_backups():
    """List all available backups."""
    manager = get_backup_manager()
    backups = manager.list_backups()
    return {
        "count": len(backups),
        "backups": [
            {
                "filename": b.filename,
                "filepath": b.filepath,
                "size_bytes": b.size_bytes,
                "created_at": b.created_at,
            }
            for b in backups
        ],
    }


@router.post("/backups/verify")
async def verify_backup(backup_path: str):
    """Verify integrity of a backup file."""
    manager = get_backup_manager()
    result = manager.verify_backup(backup_path)
    return result


@router.post("/backups/restore")
async def restore_backup(backup_path: str):
    """Restore database from a backup file."""
    try:
        manager = get_backup_manager()
        success = manager.restore_backup(backup_path)
        if success:
            return {"status": "success", "message": "Database restored successfully"}
        else:
            raise HTTPException(status_code=500, detail="Restore failed")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.post("/backups/cleanup")
async def cleanup_backups(keep: int = Query(default=10, ge=1, le=100)):
    """Remove old backups, keeping the most recent N."""
    manager = get_backup_manager()
    removed = manager.cleanup_old_backups(keep_count=keep)
    return {"status": "success", "removed_count": removed}


# --- Configuration endpoints ---

@router.get("/config/validate")
async def validate_config():
    """Validate current application configuration."""
    validator = ConfigValidator(env_file=".env")
    report = validator.validate_all()
    return report.to_dict()


@router.get("/config/current")
async def get_current_config():
    """Get current configuration (sensitive values masked)."""
    validator = ConfigValidator(env_file=".env")
    return {
        "config": validator.get_current_config(),
    }


# --- Maintenance endpoints ---

@router.post("/maintenance/vacuum")
async def run_vacuum(table: Optional[str] = None):
    """Run VACUUM ANALYZE on database."""
    manager = get_maintenance_manager()
    result = manager.run_vacuum(table_name=table)
    return {
        "operation": result.operation,
        "success": result.success,
        "message": result.message,
        "duration_ms": result.duration_ms,
    }


@router.post("/maintenance/reindex")
async def run_reindex(table: Optional[str] = None):
    """Reindex database tables."""
    manager = get_maintenance_manager()
    result = manager.run_reindex(table_name=table)
    return {
        "operation": result.operation,
        "success": result.success,
        "message": result.message,
        "duration_ms": result.duration_ms,
    }


@router.post("/maintenance/analyze")
async def analyze_tables():
    """Run ANALYZE on all tables for query planner optimization."""
    manager = get_maintenance_manager()
    result = manager.analyze_tables()
    return {
        "operation": result.operation,
        "success": result.success,
        "message": result.message,
        "duration_ms": result.duration_ms,
    }


@router.post("/maintenance/full")
async def run_full_maintenance():
    """Run all maintenance operations."""
    manager = get_maintenance_manager()
    results = manager.run_full_maintenance()
    return {
        "operations": [
            {
                "operation": r.operation,
                "success": r.success,
                "message": r.message,
                "duration_ms": r.duration_ms,
            }
            for r in results
        ],
        "all_successful": all(r.success for r in results),
    }


@router.post("/maintenance/cleanup-tasks")
async def cleanup_old_tasks(
    days: int = Query(default=90, ge=1, le=365),
):
    """Clean up old completed/failed tasks."""
    manager = get_maintenance_manager()
    result = manager.cleanup_old_tasks(days=days)
    return {
        "operation": result.operation,
        "success": result.success,
        "message": result.message,
        "details": result.details,
    }


@router.post("/maintenance/cleanup-sessions")
async def cleanup_sessions(
    max_age_hours: int = Query(default=24, ge=1, le=720),
):
    """Clean up expired sessions and tokens."""
    manager = get_maintenance_manager()
    result = manager.cleanup_expired_sessions(max_age_hours=max_age_hours)
    return {
        "operation": result.operation,
        "success": result.success,
        "message": result.message,
        "details": result.details,
    }


# --- System Health endpoints ---

@router.get("/health")
async def system_health():
    """Get comprehensive system health status."""
    manager = get_maintenance_manager()
    return manager.get_system_health()


@router.get("/tables/bloat")
async def table_bloat():
    """Check table bloat information."""
    manager = get_maintenance_manager()
    return {"tables": manager.get_table_bloat()}


@router.get("/queries/long-running")
async def long_running_queries(
    min_duration: int = Query(default=30, ge=1),
):
    """Get currently running queries exceeding duration threshold."""
    manager = get_maintenance_manager()
    return {"queries": manager.get_long_running_queries(min_duration_seconds=min_duration)}
