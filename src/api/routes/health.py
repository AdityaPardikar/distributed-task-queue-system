"""Health check routes"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.schemas import HealthResponse
from src.cache.client import get_redis_client
from src.config import get_settings
from src.db.session import engine, get_db
from src.models import Worker
from src.monitoring.system_status import SystemStatusMonitor

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", version=settings.VERSION, timestamp=datetime.utcnow())


@router.get("/ready", response_model=HealthResponse)
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check - verify all services"""
    errors = []
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        errors.append(f"Database: {str(e)}")

    # Check Redis
    try:
        redis = get_redis_client()
        redis.ping()
    except Exception as e:
        errors.append(f"Redis: {str(e)}")

    if errors:
        return HealthResponse(
            status="not_ready",
            version=settings.VERSION,
            timestamp=datetime.utcnow()
        )
    
    return HealthResponse(
        status="ready",
        version=settings.VERSION,
        timestamp=datetime.utcnow()
    )


@router.get("/info")
async def info():
    """Get application info"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "debug": settings.DEBUG,
    }


@router.get("/workers/status")
async def worker_health_status(db: Session = Depends(get_db)):
    """Check worker health based on heartbeat timestamps."""
    threshold = datetime.utcnow() - timedelta(seconds=settings.WORKER_DEAD_TIMEOUT_SECONDS)
    
    active_workers = db.query(Worker).filter(
        Worker.status == "ACTIVE",
        Worker.last_heartbeat >= threshold
    ).count()
    
    stale_workers = db.query(Worker).filter(
        Worker.status == "ACTIVE",
        Worker.last_heartbeat < threshold
    ).count()
    
    total_workers = db.query(Worker).count()
    
    health_status = "healthy" if stale_workers == 0 else "degraded"
    
    return {
        "status": health_status,
        "total_workers": total_workers,
        "active_workers": active_workers,
        "stale_workers": stale_workers,
        "heartbeat_threshold_seconds": settings.WORKER_DEAD_TIMEOUT_SECONDS,
    }


@router.get("/system/status")
async def system_status(db: Session = Depends(get_db)):
    """Get comprehensive system status with health score."""
    return SystemStatusMonitor.get_full_status(db)


@router.get("/system/resources")
async def system_resources():
    """Get current system resource usage."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        **SystemStatusMonitor.get_resource_usage(),
        "system": SystemStatusMonitor.get_system_info(),
    }


@router.get("/live")
async def liveness_probe():
    """Kubernetes liveness probe - minimal check that service is running."""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
