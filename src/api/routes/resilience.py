"""Resilience and recovery API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.resilience import (
    get_graceful_degradation,
    get_auto_recovery_engine,
    get_health_checker,
    DegradationStrategy,
)

router = APIRouter(prefix="/resilience", tags=["resilience"])


# Request/Response Models

class DegradationRequest(BaseModel):
    """Request to mark service as degraded."""
    service_name: str
    strategy: DegradationStrategy
    duration_seconds: int = 300


class ThroughputLimitRequest(BaseModel):
    """Request to set throughput limit."""
    tasks_per_minute: int
    duration_seconds: int = 300


class HealthCheckRequest(BaseModel):
    """Request to perform health check."""
    component_name: str


class CircuitBreakerResetRequest(BaseModel):
    """Request to reset circuit breaker."""
    breaker_name: str


# Graceful Degradation Endpoints

@router.post("/degradation/mark", status_code=status.HTTP_200_OK)
async def mark_service_degraded(
    request: DegradationRequest,
    db: Session = Depends(get_db),
):
    """Mark a service as degraded.
    
    When a service degrades, the system automatically applies the specified
    strategy (caching results, reducing throughput, etc).
    
    Args:
        request: Degradation request
        
    Returns:
        Degradation status
    """
    degradation = get_graceful_degradation()
    
    degradation.mark_service_degraded(
        request.service_name,
        request.strategy,
        request.duration_seconds,
    )
    
    return {
        "service": request.service_name,
        "strategy": request.strategy.value,
        "duration_seconds": request.duration_seconds,
        "status": "degraded",
    }


@router.get("/degradation/status/{service_name}", status_code=status.HTTP_200_OK)
async def get_degradation_status(
    service_name: str,
):
    """Get degradation status for a service.
    
    Args:
        service_name: Service name
        
    Returns:
        Degradation status
    """
    degradation = get_graceful_degradation()
    
    is_degraded = degradation.is_service_degraded(service_name)
    strategy = degradation.get_degradation_strategy(service_name)
    
    return {
        "service": service_name,
        "is_degraded": is_degraded,
        "strategy": strategy.value if strategy else None,
    }


@router.post("/degradation/clear/{service_name}", status_code=status.HTTP_200_OK)
async def clear_degradation(
    service_name: str,
):
    """Clear degradation state for a service.
    
    Args:
        service_name: Service name
        
    Returns:
        Confirmation
    """
    degradation = get_graceful_degradation()
    
    degradation.clear_degradation(service_name)
    
    return {"service": service_name, "status": "degradation_cleared"}


@router.get("/degradation/all", status_code=status.HTTP_200_OK)
async def get_all_degraded_services():
    """Get all currently degraded services.
    
    Returns:
        Dictionary of degraded services
    """
    degradation = get_graceful_degradation()
    
    services = degradation.get_all_degraded_services()
    
    return {
        "degraded_services": len(services),
        "services": services,
    }


# Throughput Control Endpoints

@router.post("/throughput/limit", status_code=status.HTTP_200_OK)
async def set_throughput_limit(
    request: ThroughputLimitRequest,
):
    """Set throughput limit during degradation.
    
    Reduces task submission rate to prevent overwhelming the system.
    
    Args:
        request: Throughput limit request
        
    Returns:
        Limit status
    """
    degradation = get_graceful_degradation()
    
    degradation.set_throughput_limit(
        request.tasks_per_minute,
        request.duration_seconds,
    )
    
    return {
        "tasks_per_minute": request.tasks_per_minute,
        "duration_seconds": request.duration_seconds,
        "status": "limit_set",
    }


@router.get("/throughput/limit", status_code=status.HTTP_200_OK)
async def get_throughput_limit():
    """Get current throughput limit.
    
    Returns:
        Current limit or None
    """
    degradation = get_graceful_degradation()
    
    limit = degradation.get_throughput_limit()
    
    return {"throughput_limit_tpm": limit}


# Health Check Endpoints

@router.post("/health/check", status_code=status.HTTP_200_OK)
async def manual_health_check(
    request: HealthCheckRequest,
):
    """Manually trigger health check for a component.
    
    Args:
        request: Health check request
        
    Returns:
        Check result
    """
    health_checker = get_health_checker()
    
    # Placeholder check - in production, would call actual checks
    def dummy_check():
        return True
    
    is_healthy = health_checker.check_health(request.component_name, dummy_check)
    
    return {
        "component": request.component_name,
        "is_healthy": is_healthy,
    }


@router.get("/health/{component_name}", status_code=status.HTTP_200_OK)
async def get_component_health(
    component_name: str,
):
    """Get health status for a component.
    
    Args:
        component_name: Component name
        
    Returns:
        Health status with success rate
    """
    health_checker = get_health_checker()
    
    status_data = health_checker.get_component_health(component_name)
    
    return status_data


@router.get("/health/all", status_code=status.HTTP_200_OK)
async def get_all_health():
    """Get health status for all components.
    
    Returns:
        Dictionary of all component health statuses
    """
    health_checker = get_health_checker()
    
    all_status = health_checker.get_all_health_status()
    
    unhealthy_count = sum(
        1 for status in all_status.values()
        if status["status"] == "unhealthy"
    )
    
    return {
        "components_total": len(all_status),
        "healthy": len(all_status) - unhealthy_count,
        "unhealthy": unhealthy_count,
        "components": all_status,
    }


# Recovery Endpoints

@router.get("/recovery/{component_name}/status", status_code=status.HTTP_200_OK)
async def get_recovery_status(
    component_name: str,
):
    """Get recovery status for a component.
    
    Args:
        component_name: Component name
        
    Returns:
        Recovery status
    """
    recovery_engine = get_auto_recovery_engine()
    
    status_data = recovery_engine.get_recovery_status(component_name)
    
    return status_data


@router.get("/recovery/history", status_code=status.HTTP_200_OK)
async def get_recovery_history(
    component_name: str = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get recovery attempt history.
    
    Args:
        component_name: Optional component filter
        limit: Maximum entries
        
    Returns:
        Recovery history
    """
    recovery_engine = get_auto_recovery_engine()
    
    history = recovery_engine.get_recovery_history(component_name, limit)
    
    return {
        "component": component_name,
        "entries": len(history),
        "history": history,
    }


# System Resilience Summary

@router.get("/summary", status_code=status.HTTP_200_OK)
async def get_resilience_summary():
    """Get overall system resilience status.
    
    Combines degradation, health, and recovery information.
    
    Returns:
        Resilience summary
    """
    degradation = get_graceful_degradation()
    health_checker = get_health_checker()
    
    degraded_services = degradation.get_all_degraded_services()
    all_health = health_checker.get_all_health_status()
    
    unhealthy_count = sum(
        1 for status in all_health.values()
        if status["status"] == "unhealthy"
    )
    
    return {
        "system_health": {
            "components_total": len(all_health),
            "healthy": len(all_health) - unhealthy_count,
            "unhealthy": unhealthy_count,
        },
        "degradation": {
            "degraded_services_count": len(degraded_services),
            "services": list(degraded_services.keys()),
        },
        "resilience_score": (
            ((len(all_health) - unhealthy_count) / len(all_health) * 100)
            if all_health else 0
        ),
    }
