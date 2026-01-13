"""Task routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from src.api.schemas import TaskCreate, TaskListResponse, TaskResponse
from src.db.session import get_db
from src.models import Task
from src.core.broker import get_broker
from src.config.constants import MSG_TASK_CREATED, MSG_TASK_CANCELLED, TASK_STATUS_CANCELLED, TASK_STATUS_PENDING

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
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
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        # Enqueue in Redis if not scheduled
        if not task.scheduled_at:
            broker = get_broker()
            priority_name = "MEDIUM"  # Default priority name
            broker.enqueue_task(str(db_task.task_id), priority_name)

        return TaskResponse.model_validate(db_task)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    """List tasks with pagination"""
    query = db.query(Task)

    if status:
        query = query.filter(Task.status == status)

    total = query.count()
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()

    return TaskListResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID, db: Session = Depends(get_db)):
    """Get task details"""
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse.model_validate(task)


@router.delete("/{task_id}")
async def cancel_task(task_id: UUID, db: Session = Depends(get_db)):
    """Cancel a task"""
    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update task status
    task.status = TASK_STATUS_CANCELLED
    db.commit()

    return {"detail": MSG_TASK_CANCELLED, "task_id": task_id}


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
