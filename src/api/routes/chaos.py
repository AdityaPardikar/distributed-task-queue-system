"""Chaos engineering API routes for fault injection and resilience testing."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.resilience.chaos_engineering import (
    ChaosEngineering,
    ChaosType,
    ChaosConfig,
    RetryWithBackoff,
    DeadLetterQueue,
)

router = APIRouter(prefix="/chaos", tags=["chaos-engineering"])

# Singleton instances
_chaos_engine: Optional[ChaosEngineering] = None
_dlq: Optional[DeadLetterQueue] = None


def get_chaos_engine() -> ChaosEngineering:
    """Get chaos engineering instance."""
    global _chaos_engine
    if _chaos_engine is None:
        _chaos_engine = ChaosEngineering()
    return _chaos_engine


def get_dlq() -> DeadLetterQueue:
    """Get dead letter queue instance."""
    global _dlq
    if _dlq is None:
        _dlq = DeadLetterQueue()
    return _dlq


# --- Schemas ---

class ExperimentCreate(BaseModel):
    """Schema for creating a chaos experiment."""
    experiment_id: str = Field(..., description="Unique experiment identifier")
    chaos_type: str = Field(..., description="Type of chaos: latency, error, timeout, resource_exhaustion, network_partition")
    target_pattern: str = Field(..., description="Regex pattern for target tasks/services")
    probability: float = Field(default=0.1, ge=0.0, le=1.0, description="Probability of chaos injection (0.0-1.0)")
    duration_seconds: int = Field(default=60, ge=1, le=3600, description="Experiment duration")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Chaos type specific parameters")


class ExperimentResponse(BaseModel):
    """Chaos experiment response."""
    experiment_id: str
    status: str
    message: str


class ExperimentStatus(BaseModel):
    """Experiment status information."""
    experiment_id: str
    is_active: bool
    chaos_type: Optional[str] = None
    target_pattern: Optional[str] = None
    duration_seconds: Optional[int] = None
    injections_count: int = 0


class DLQItem(BaseModel):
    """Dead letter queue item."""
    task_id: str
    error_message: str
    failed_at: str
    retry_count: int
    original_args: Optional[Dict[str, Any]] = None


class DLQAddRequest(BaseModel):
    """Request to add item to DLQ."""
    task_id: str
    error_message: str
    retry_count: int = 0
    original_args: Optional[Dict[str, Any]] = None


# --- Experiment Routes ---

@router.post("/experiments", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def start_experiment(
    experiment: ExperimentCreate,
):
    """Start a chaos engineering experiment.
    
    Chaos types:
    - `latency`: Add random latency to operations
    - `error`: Inject random errors
    - `timeout`: Force operation timeouts
    - `resource_exhaustion`: Simulate resource limits
    - `network_partition`: Simulate network failures
    
    Example:
    ```json
    {
        "experiment_id": "test-latency-001",
        "chaos_type": "latency",
        "target_pattern": "api.*",
        "probability": 0.3,
        "duration_seconds": 120,
        "parameters": {
            "min_latency_ms": 100,
            "max_latency_ms": 500
        }
    }
    ```
    """
    try:
        engine = get_chaos_engine()
        
        # Map string to ChaosType enum
        chaos_type_map = {
            "latency": ChaosType.LATENCY,
            "error": ChaosType.ERROR,
            "timeout": ChaosType.TIMEOUT,
            "resource_exhaustion": ChaosType.RESOURCE_EXHAUSTION,
            "network_partition": ChaosType.NETWORK_PARTITION,
        }
        
        if experiment.chaos_type not in chaos_type_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid chaos type: {experiment.chaos_type}. Valid types: {list(chaos_type_map.keys())}"
            )
        
        config = ChaosConfig(
            chaos_type=chaos_type_map[experiment.chaos_type],
            target_pattern=experiment.target_pattern,
            probability=experiment.probability,
            duration_seconds=experiment.duration_seconds,
            parameters=experiment.parameters or {},
        )
        
        engine.start_experiment(experiment.experiment_id, config)
        
        return ExperimentResponse(
            experiment_id=experiment.experiment_id,
            status="started",
            message=f"Chaos experiment started: {experiment.chaos_type} on '{experiment.target_pattern}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start experiment: {str(e)}"
        )


@router.delete("/experiments/{experiment_id}", response_model=ExperimentResponse)
async def stop_experiment(experiment_id: str):
    """Stop a running chaos experiment."""
    engine = get_chaos_engine()
    engine.stop_experiment(experiment_id)
    
    return ExperimentResponse(
        experiment_id=experiment_id,
        status="stopped",
        message="Chaos experiment stopped"
    )


@router.get("/experiments/{experiment_id}", response_model=ExperimentStatus)
async def get_experiment_status(experiment_id: str):
    """Get status of a chaos experiment."""
    engine = get_chaos_engine()
    
    is_active = experiment_id in engine.experiments
    
    if is_active:
        config = engine.experiments[experiment_id]
        return ExperimentStatus(
            experiment_id=experiment_id,
            is_active=True,
            chaos_type=config.chaos_type.value,
            target_pattern=config.target_pattern,
            duration_seconds=config.duration_seconds,
            injections_count=engine.injection_counts.get(experiment_id, 0),
        )
    
    return ExperimentStatus(
        experiment_id=experiment_id,
        is_active=False,
    )


@router.get("/experiments")
async def list_experiments():
    """List all active chaos experiments."""
    engine = get_chaos_engine()
    
    active = []
    for exp_id, config in engine.experiments.items():
        active.append({
            "experiment_id": exp_id,
            "chaos_type": config.chaos_type.value,
            "target_pattern": config.target_pattern,
            "probability": config.probability,
            "injections_count": engine.injection_counts.get(exp_id, 0),
        })
    
    return {
        "active_experiments": active,
        "total": len(active),
    }


@router.post("/experiments/{experiment_id}/trigger")
async def trigger_injection(
    experiment_id: str,
    target: str,
):
    """Manually trigger chaos injection for testing.
    
    This endpoint allows you to test chaos injection without running actual tasks.
    """
    engine = get_chaos_engine()
    
    if experiment_id not in engine.experiments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )
    
    config = engine.experiments[experiment_id]
    
    # Check if target matches
    import re
    if not re.search(config.target_pattern, target):
        return {
            "injected": False,
            "reason": "Target does not match pattern",
        }
    
    # Force injection (ignore probability for manual trigger)
    return {
        "injected": True,
        "chaos_type": config.chaos_type.value,
        "target": target,
        "message": "Chaos would be injected on matching operation",
    }


# --- Dead Letter Queue Routes ---

@router.get("/dlq")
async def list_dlq_items(
    limit: int = 100,
    offset: int = 0,
):
    """List items in the dead letter queue."""
    dlq = get_dlq()
    items = dlq.get_all(limit=limit)
    
    return {
        "items": items,
        "total": len(items),
        "limit": limit,
        "offset": offset,
    }


@router.post("/dlq")
async def add_to_dlq(request: DLQAddRequest):
    """Manually add a task to the dead letter queue."""
    dlq = get_dlq()
    
    dlq.add(
        task_id=request.task_id,
        error=request.error_message,
        retry_count=request.retry_count,
        original_args=request.original_args,
    )
    
    return {"message": f"Task {request.task_id} added to DLQ"}


@router.post("/dlq/{task_id}/requeue")
async def requeue_dlq_item(task_id: str):
    """Requeue a task from the dead letter queue."""
    dlq = get_dlq()
    
    success = dlq.requeue(task_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found in DLQ"
        )
    
    return {"message": f"Task {task_id} requeued"}


@router.delete("/dlq/{task_id}")
async def remove_from_dlq(task_id: str):
    """Remove a task from the dead letter queue."""
    dlq = get_dlq()
    dlq.remove(task_id)
    
    return {"message": f"Task {task_id} removed from DLQ"}


@router.delete("/dlq")
async def clear_dlq():
    """Clear all items from the dead letter queue."""
    dlq = get_dlq()
    dlq.clear()
    
    return {"message": "DLQ cleared"}


# --- Retry Configuration Routes ---

@router.get("/retry/config")
async def get_retry_config():
    """Get current retry configuration."""
    retry = RetryWithBackoff()
    
    return {
        "max_retries": retry.max_retries,
        "base_delay": retry.base_delay,
        "max_delay": retry.max_delay,
        "exponential_base": retry.exponential_base,
        "jitter": retry.jitter,
    }


@router.post("/retry/test")
async def test_retry_delays():
    """Calculate retry delays for testing purposes."""
    retry = RetryWithBackoff()
    
    delays = []
    for attempt in range(retry.max_retries):
        delay = retry.get_delay(attempt)
        delays.append({
            "attempt": attempt + 1,
            "delay_seconds": round(delay, 3),
        })
    
    return {
        "max_retries": retry.max_retries,
        "delays": delays,
        "total_max_delay": sum(d["delay_seconds"] for d in delays),
    }
