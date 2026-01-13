"""Metrics routes"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.schemas import MetricsResponse
from src.db.session import get_db
from src.models import Task, Worker

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=MetricsResponse)
async def get_metrics(db: Session = Depends(get_db)):
    """Get system metrics"""
    tasks_total = db.query(Task).count()
    tasks_completed = db.query(Task).filter(Task.status == "COMPLETED").count()
    tasks_failed = db.query(Task).filter(Task.status == "FAILED").count()
    tasks_pending = db.query(Task).filter(Task.status == "PENDING").count()

    workers_active = db.query(Worker).filter(Worker.status == "ACTIVE").count()
    workers_idle = db.query(Worker).filter(Worker.status == "IDLE").count()

    return MetricsResponse(
        tasks_total=tasks_total,
        tasks_completed=tasks_completed,
        tasks_failed=tasks_failed,
        tasks_pending=tasks_pending,
        workers_active=workers_active,
        workers_idle=workers_idle,
        queue_depth=tasks_pending,
        avg_task_duration=0.0,
    )


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    return {
        "timestamp": datetime.utcnow(),
        "tasks": {
            "total": db.query(Task).count(),
            "pending": db.query(Task).filter(Task.status == "PENDING").count(),
            "running": db.query(Task).filter(Task.status == "RUNNING").count(),
            "completed": db.query(Task).filter(Task.status == "COMPLETED").count(),
            "failed": db.query(Task).filter(Task.status == "FAILED").count(),
        },
        "workers": {
            "total": db.query(Worker).count(),
            "active": db.query(Worker).filter(Worker.status == "ACTIVE").count(),
            "idle": db.query(Worker).filter(Worker.status == "IDLE").count(),
            "busy": db.query(Worker).filter(Worker.status == "BUSY").count(),
            "dead": db.query(Worker).filter(Worker.status == "DEAD").count(),
        },
    }
