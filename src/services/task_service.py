"""Task service layer for business logic"""

from sqlalchemy.orm import Session
from src.models import Task
from uuid import UUID
from datetime import datetime
from typing import Optional, List


def create_task(
    db: Session,
    task_name: str,
    task_args: List = None,
    task_kwargs: dict = None,
    priority: int = 5,
    max_retries: int = 5,
    timeout_seconds: int = 300,
) -> Task:
    """Create a new task"""
    task = Task(
        task_name=task_name,
        task_args=task_args or [],
        task_kwargs=task_kwargs or {},
        priority=priority,
        max_retries=max_retries,
        timeout_seconds=timeout_seconds,
        status="PENDING",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: UUID) -> Optional[Task]:
    """Get task by ID"""
    return db.query(Task).filter(Task.task_id == task_id).first()


def update_task_status(db: Session, task_id: UUID, status: str) -> Optional[Task]:
    """Update task status"""
    task = get_task(db, task_id)
    if task:
        task.status = status
        if status == "RUNNING":
            task.started_at = datetime.utcnow()
        elif status == "COMPLETED":
            task.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
    return task


def list_tasks(db: Session, skip: int = 0, limit: int = 100, status: str = None) -> List[Task]:
    """List tasks with optional filtering"""
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    return query.offset(skip).limit(limit).all()
