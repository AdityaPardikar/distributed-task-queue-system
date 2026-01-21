"""Metrics routes"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.schemas import MetricsResponse
from src.db.session import get_db
from src.models import Task, Worker
from src.monitoring import metrics as monitoring_metrics

router = APIRouter(prefix="/metrics", tags=["metrics"])


def _update_gauges(tasks_pending: int, workers: list[Worker]) -> None:
    """Update Prometheus gauges based on current DB state."""
    monitoring_metrics.set_queue_depth(tasks_pending)

    active_workers = len([w for w in workers if w.status == "ACTIVE"])
    monitoring_metrics.set_active_workers(active_workers)

    total_capacity = sum(w.capacity for w in workers)
    total_load = sum(w.current_load for w in workers)
    utilization = (total_load / total_capacity) if total_capacity else 0
    monitoring_metrics.set_worker_capacity_utilization(utilization)


@router.get("", response_model=MetricsResponse)
async def get_metrics(db: Session = Depends(get_db)):
    """Get system metrics"""
    tasks_total = db.query(Task).count()
    tasks_completed = db.query(Task).filter(Task.status == "COMPLETED").count()
    tasks_failed = db.query(Task).filter(Task.status == "FAILED").count()
    tasks_pending = db.query(Task).filter(Task.status == "PENDING").count()

    workers = db.query(Worker).all()
    workers_active = len([w for w in workers if w.status == "ACTIVE"])
    workers_idle = len([w for w in workers if w.status == "IDLE"])

    _update_gauges(tasks_pending, workers)

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


@router.get("/prometheus")
async def prometheus_metrics(db: Session = Depends(get_db)):
    """Expose Prometheus scrape endpoint under the API namespace."""
    tasks_pending = db.query(Task).filter(Task.status == "PENDING").count()
    workers = db.query(Worker).all()
    _update_gauges(tasks_pending, workers)
    return monitoring_metrics.prometheus_response()


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
