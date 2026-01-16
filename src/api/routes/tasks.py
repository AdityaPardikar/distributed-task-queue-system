"""Task routes"""

import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from src.api.schemas import TaskCreate, TaskListResponse, TaskResponse, TaskDetailResponse, TaskUpdate
from src.db.session import get_db
from src.models import Task
from src.core.broker import get_broker
from src.config.constants import MSG_TASK_CREATED, MSG_TASK_CANCELLED, TASK_STATUS_CANCELLED, TASK_STATUS_PENDING

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create and enqueue a new task.
    
    Args:
        task: Task creation request with name, priority, payload
        db: Database session
        
    Returns:
        Created task with ID and status
        
    Raises:
        HTTPException: If task creation or enqueueing fails
    """
    try:
        # Create task in database
        db_task = Task(
            task_name=task.task_name,
            task_args=task.task_args,
            task_kwargs=task.task_kwargs,
            priority=task.priority,
            max_retries=task.max_retries,
            timeout_seconds=task.timeout_seconds,
            scheduled_at=task.scheduled_at,
            parent_task_id=task.parent_task_id,
            campaign_id=task.campaign_id,
            status=TASK_STATUS_PENDING,
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        # Enqueue in Redis if not scheduled
        broker = get_broker()
        if not task.scheduled_at:
            # Store task metadata in Redis
            task_metadata = {
                "task_id": str(db_task.task_id),
                "task_name": db_task.task_name,
                "priority": db_task.priority,
                "status": db_task.status,
                "created_at": db_task.created_at.isoformat(),
                "payload": json.dumps({
                    "args": task.task_args,
                    "kwargs": task.task_kwargs
                })
            }
            
            # Enqueue with priority
            success = broker.enqueue_task(
                task_id=str(db_task.task_id),
                priority=task.priority,
                task_data=task_metadata
            )
            
            if not success:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to enqueue task to Redis"
                )
        else:
            # Schedule for future execution
            scheduled_timestamp = int(task.scheduled_at.timestamp())
            broker.schedule_task(str(db_task.task_id), scheduled_timestamp)

        return TaskResponse.model_validate(db_task)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str = Query(None, description="Filter by status"),
    priority: int = Query(None, ge=1, le=10, description="Filter by priority"),
    sort_by: str = Query("created_at", regex="^(created_at|priority|status)$", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db),
):
    """List tasks with advanced filtering, pagination, and sorting.
    
    Query Parameters:
    - page: Page number (default 1)
    - page_size: Items per page (1-100, default 20)
    - status: Filter by task status (PENDING, RUNNING, COMPLETED, FAILED, etc.)
    - priority: Filter by priority level (1-10)
    - sort_by: Sort by created_at, priority, or status
    - sort_order: asc or desc (default desc)
    
    Returns:
    - items: Array of tasks
    - total: Total count of matching tasks
    - page: Current page number
    - page_size: Items per page
    - has_next: Whether there are more pages
    - has_previous: Whether there are previous pages
    """
    query = db.query(Task)
    
    # Apply filters
    if status:
        query = query.filter(Task.status == status)
    
    if priority is not None:
        query = query.filter(Task.priority == priority)
    
    # Count total before pagination
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(Task, sort_by)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    # Apply pagination
    offset = (page - 1) * page_size
    tasks = query.offset(offset).limit(page_size).all()
    
    # Calculate pagination info
    has_next = (offset + page_size) < total
    has_previous = page > 1
    total_pages = (total + page_size - 1) // page_size
    
    return TaskListResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_previous=has_previous,
        total_pages=total_pages,
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: UUID, db: Session = Depends(get_db)):
    """Get detailed task information.
    
    Returns complete task data including:
    - Basic task info (name, priority, status)
    - Execution history and attempts
    - Result data if completed
    - Related tasks (parent/children)
    - Worker assignment if running
    - All timestamps and metadata
    
    Args:
        task_id: Task UUID
        
    Returns:
        Complete task details or 404 if not found
    """
    task = db.query(Task).filter(Task.task_id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    return TaskDetailResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def cancel_task(task_id: UUID, db: Session = Depends(get_db)):
    """Cancel a pending or queued task.
    
    Only tasks in PENDING or QUEUED status can be cancelled.
    Running tasks cannot be cancelled (must complete or timeout).
    
    Args:
        task_id: Task UUID to cancel
        
    Returns:
        Updated task status or error
        
    Raises:
        HTTPException: If task not found or cannot be cancelled
    """
    task = db.query(Task).filter(Task.task_id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    # Only allow cancellation of non-terminal tasks
    if task.status in ["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task with status '{task.status}'. Task is in terminal state."
        )
    
    if task.status == "RUNNING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel running task. Task must complete or timeout."
        )
    
    try:
        # Update task status in database
        task.status = "CANCELLED"
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        
        # Remove from Redis queue if present
        broker = get_broker()
        broker.redis.lrem("queue:HIGH", 0, str(task_id))
        broker.redis.lrem("queue:MEDIUM", 0, str(task_id))
        broker.redis.lrem("queue:LOW", 0, str(task_id))
        
        # Update Redis metadata
        broker.update_task_status(str(task_id), "CANCELLED")
        
        return {
            "status": "success",
            "task_id": str(task_id),
            "message": "Task cancelled successfully",
            "task": TaskResponse.model_validate(task)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )



@router.patch("/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update task properties.
    
    Allows partial updates of task attributes:
    - priority: Change task priority (1-10)
    - timeout_seconds: Update timeout duration
    - max_retries: Change max retry attempts
    - task_kwargs: Update task arguments/payload
    
    Only PENDING and QUEUED tasks can be updated.
    
    Args:
        task_id: Task UUID
        task_update: Fields to update
        
    Returns:
        Updated task
        
    Raises:
        HTTPException: If task not found or cannot be updated
    """
    task = db.query(Task).filter(Task.task_id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    # Only allow updates on non-terminal tasks
    if task.status in ["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update task in '{task.status}' state"
        )
    
    if task.status == "RUNNING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update running task. Wait for completion or cancellation."
        )
    
    try:
        # Apply updates
        if task_update.priority is not None:
            task.priority = task_update.priority
        
        if task_update.timeout_seconds is not None:
            task.timeout_seconds = task_update.timeout_seconds
        
        if task_update.max_retries is not None:
            task.max_retries = task_update.max_retries
        
        if task_update.task_kwargs is not None:
            task.task_kwargs = task_update.task_kwargs
        
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        
        # Update Redis metadata
        broker = get_broker()
        broker.update_task_status(
            str(task_id),
            "status",
            priority=task.priority,
            timeout_seconds=task.timeout_seconds,
            max_retries=task.max_retries
        )
        
        return TaskResponse.model_validate(task)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )


@router.post("/{task_id}/retry")
async def retry_task(task_id: UUID, db: Session = Depends(get_db)):
    """Retry a task"""
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Reset task status
    task.status = TASK_STATUS_PENDING
    task.retry_count = 0
    db.commit()

    # Enqueue again
    broker = get_broker()
    broker.enqueue_task(str(task_id), "MEDIUM")

    return {"detail": "Task queued for retry", "task_id": task_id}

