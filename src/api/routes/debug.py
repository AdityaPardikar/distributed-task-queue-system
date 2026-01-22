"""Task debugging and replay API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID

from src.db.session import get_db
from src.services.task_debugger import get_task_debugger

router = APIRouter(prefix="/tasks", tags=["task-debug"])


# Request/Response Models

class ReplayTaskRequest(BaseModel):
    """Request to replay a task."""
    preserve_retries: bool = False


class DryRunRequest(BaseModel):
    """Request to perform a dry-run task submission."""
    task_name: str
    task_args: list = []
    task_kwargs: dict = {}


class DebugModeRequest(BaseModel):
    """Request to enable debug mode."""
    duration_minutes: int = 60


class TaskExecutionEvent(BaseModel):
    """Task execution event."""
    timestamp: str
    event_type: str
    details: dict


class TaskTimelineResponse(BaseModel):
    """Task timeline response."""
    task_id: str
    task_name: str
    status: str
    created_at: str | None
    started_at: str | None
    completed_at: str | None
    failed_at: str | None
    duration_seconds: float | None
    events: list[dict]
    retry_history: list[dict]


class TaskComparisonResponse(BaseModel):
    """Task comparison response."""
    task1_id: str
    task2_id: str
    same_function: bool
    same_args: bool
    same_kwargs: bool
    same_priority: bool
    status_comparison: dict
    timing: dict
    retry_analysis: dict
    error_comparison: dict
    arguments: dict


# Debug Control Endpoints

@router.post("/{task_id}/debug", status_code=status.HTTP_200_OK)
async def enable_debug(
    task_id: UUID,
    request: DebugModeRequest,
    db: Session = Depends(get_db),
):
    """Enable debug mode for a specific task.
    
    Debug mode enables verbose logging and extended execution tracking.
    
    Args:
        task_id: Task ID
        request: Debug mode configuration
        
    Returns:
        Debug status
    """
    debugger = get_task_debugger()
    
    if request.duration_minutes < 1 or request.duration_minutes > 1440:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duration must be between 1 and 1440 minutes"
        )
    
    debugger.enable_debug_mode(str(task_id), request.duration_minutes)
    
    return {
        "task_id": str(task_id),
        "debug_enabled": True,
        "duration_minutes": request.duration_minutes,
    }


@router.get("/{task_id}/debug", status_code=status.HTTP_200_OK)
async def check_debug_status(
    task_id: UUID,
):
    """Check if debug mode is enabled for a task.
    
    Args:
        task_id: Task ID
        
    Returns:
        Debug status
    """
    debugger = get_task_debugger()
    is_enabled = debugger.is_debug_enabled(str(task_id))
    
    return {
        "task_id": str(task_id),
        "debug_enabled": is_enabled,
    }


# Execution Log Endpoints

@router.get("/{task_id}/execution-log", response_model=list[dict], status_code=status.HTTP_200_OK)
async def get_execution_log(
    task_id: UUID,
    limit: int = Query(None, ge=1, le=1000),
):
    """Get execution log for a task.
    
    Returns detailed event log for task execution including timing,
    progress events, and debugging information.
    
    Args:
        task_id: Task ID
        limit: Maximum number of log entries
        
    Returns:
        List of execution events with timestamps
    """
    debugger = get_task_debugger()
    events = debugger.get_execution_log(str(task_id), limit)
    
    return events


# Replay Endpoints

@router.post("/{task_id}/replay", status_code=status.HTTP_201_CREATED)
async def replay_task(
    task_id: UUID,
    request: ReplayTaskRequest,
    db: Session = Depends(get_db),
):
    """Replay a failed or completed task.
    
    Creates a new task with the same arguments as the original,
    allowing re-execution of failed tasks.
    
    Args:
        task_id: Original task ID
        request: Replay configuration
        
    Returns:
        New task details
    """
    debugger = get_task_debugger()
    
    # Validate task can be replayed
    validation = debugger.validate_task_replay(db, str(task_id))
    if not validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task cannot be replayed: {'; '.join(validation['reasons'])}"
        )
    
    # Replay the task
    result = debugger.replay_task(db, str(task_id), request.preserve_retries)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    return result


@router.post("/test", status_code=status.HTTP_201_CREATED)
async def test_dry_run(
    request: DryRunRequest,
    db: Session = Depends(get_db),
):
    """Create a dry-run/test task without execution.
    
    Useful for testing task submission and validation without
    actually executing the task.
    
    Args:
        request: Dry-run task details
        
    Returns:
        Test task details (will not be executed)
    """
    if not request.task_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task_name is required"
        )
    
    debugger = get_task_debugger()
    result = debugger.test_dry_run(
        db,
        request.task_name,
        request.task_args,
        request.task_kwargs,
    )
    
    return result


# Comparison & Analysis Endpoints

@router.get("/{task_id1}/compare/{task_id2}", response_model=TaskComparisonResponse, status_code=status.HTTP_200_OK)
async def compare_tasks(
    task_id1: UUID,
    task_id2: UUID,
    db: Session = Depends(get_db),
):
    """Compare two tasks to identify differences.
    
    Compares arguments, execution times, status, errors, and other
    properties to identify discrepancies between task runs.
    
    Args:
        task_id1: First task ID
        task_id2: Second task ID
        
    Returns:
        Detailed comparison
    """
    debugger = get_task_debugger()
    comparison = debugger.compare_tasks(db, str(task_id1), str(task_id2))
    
    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both tasks not found"
        )
    
    return comparison


@router.get("/{task_id}/timeline", response_model=TaskTimelineResponse, status_code=status.HTTP_200_OK)
async def get_task_timeline(
    task_id: UUID,
    db: Session = Depends(get_db),
):
    """Get execution timeline for a task.
    
    Returns detailed timeline including all execution events,
    timestamps, and state changes for thorough debugging.
    
    Args:
        task_id: Task ID
        
    Returns:
        Execution timeline with events
    """
    debugger = get_task_debugger()
    timeline = debugger.get_task_timeline(db, str(task_id))
    
    if not timeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    return timeline


@router.get("/{task_id}/similar", status_code=status.HTTP_200_OK)
async def get_similar_tasks(
    task_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Find similar tasks (same function).
    
    Locates other tasks that execute the same function, useful for
    comparing behavior across different invocations.
    
    Args:
        task_id: Reference task ID
        limit: Maximum number of similar tasks
        
    Returns:
        List of similar tasks
    """
    debugger = get_task_debugger()
    similar = debugger.get_similar_tasks(db, str(task_id), limit)
    
    return {
        "task_id": str(task_id),
        "similar_count": len(similar),
        "similar_tasks": similar,
    }


# Validation Endpoints

@router.post("/{task_id}/validate-replay", status_code=status.HTTP_200_OK)
async def validate_replay(
    task_id: UUID,
    db: Session = Depends(get_db),
):
    """Validate if a task can be safely replayed.
    
    Checks task status, arguments, and retry limits to ensure
    the task can be replayed.
    
    Args:
        task_id: Task ID
        
    Returns:
        Validation result with reasons if invalid
    """
    debugger = get_task_debugger()
    validation = debugger.validate_task_replay(db, str(task_id))
    
    if not validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation,
        )
    
    return validation


# Function Metrics Endpoints

@router.get("/function/{task_name}/metrics", status_code=status.HTTP_200_OK)
async def get_function_metrics(
    task_name: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get aggregate metrics for a task function.
    
    Analyzes all executions of a specific task function to provide
    success rates, average durations, and other performance metrics.
    
    Args:
        task_name: Task function name
        limit: Maximum tasks to analyze
        
    Returns:
        Aggregate metrics
    """
    debugger = get_task_debugger()
    metrics = debugger.get_task_metrics_for_function(db, task_name, limit)
    
    return metrics
