"""Service layer for database operations"""

from sqlalchemy.orm import Session
from src.models import Task, Worker
from uuid import UUID
from typing import Optional


class TaskService:
    """Service for task operations"""

    @staticmethod
    def get_task(db: Session, task_id: UUID) -> Optional[Task]:
        """Get task by ID"""
        return db.query(Task).filter(Task.task_id == task_id).first()

    @staticmethod
    def get_all_tasks(db: Session, skip: int = 0, limit: int = 100):
        """Get all tasks with pagination"""
        return db.query(Task).offset(skip).limit(limit).all()

    @staticmethod
    def create_task(db: Session, task_data: dict) -> Task:
        """Create a new task"""
        task = Task(**task_data)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update_task_status(db: Session, task_id: UUID, status: str) -> Task:
        """Update task status"""
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task.status = status
            db.commit()
            db.refresh(task)
        return task


class WorkerService:
    """Service for worker operations"""

    @staticmethod
    def register_worker(db: Session, worker_data: dict) -> Worker:
        """Register a new worker"""
        worker = Worker(**worker_data)
        db.add(worker)
        db.commit()
        db.refresh(worker)
        return worker

    @staticmethod
    def get_worker(db: Session, worker_id: UUID) -> Optional[Worker]:
        """Get worker by ID"""
        return db.query(Worker).filter(Worker.worker_id == worker_id).first()

    @staticmethod
    def get_all_workers(db: Session):
        """Get all workers"""
        return db.query(Worker).all()

    @staticmethod
    def update_worker_status(db: Session, worker_id: UUID, status: str):
        """Update worker status"""
        worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
        if worker:
            worker.status = status
            db.commit()
            db.refresh(worker)
        return worker
