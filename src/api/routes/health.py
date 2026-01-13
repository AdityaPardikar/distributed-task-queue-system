"""Health check routes"""

from datetime import datetime

from fastapi import APIRouter

from src.api.schemas import HealthResponse
from src.cache.client import get_redis_client
from src.config import get_settings
from src.db.session import engine

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", version=settings.VERSION, timestamp=datetime.utcnow())


@router.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness check - verify all services"""
    try:
        # Check database
        with engine.connect() as conn:
            conn.execute("SELECT 1")

        # Check Redis
        redis = get_redis_client()
        redis.ping()

        return HealthResponse(status="ready", version=settings.VERSION, timestamp=datetime.utcnow())
    except Exception as e:
        return HealthResponse(status="not_ready", version=settings.VERSION, timestamp=datetime.utcnow())


@router.get("/info")
async def info():
    """Get application info"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "debug": settings.DEBUG,
    }
