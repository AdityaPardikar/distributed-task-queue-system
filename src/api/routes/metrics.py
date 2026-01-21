"""Metrics routes"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.schemas import MetricsResponse
from src.db.session import get_db
from src.models import Task, Worker
from src.monitoring import metrics as monitoring_metrics
from src.monitoring.worker_metrics import get_worker_metrics_tracker

router = APIRouter(prefix="/metrics", tags=["metrics"])


class WorkerMetrics(BaseModel):
    """Schema for worker metrics response."""
    worker_id: str
    total_tasks: int
    total_errors: int
    avg_duration_seconds: float
    error_rate: float
    task_rate_per_minute: float
    uptime_seconds: int
    restart_count: int
    last_heartbeat: str | None
    last_update: str | None


class WorkerComparison(BaseModel):
    """Schema for worker comparison response."""
    total_workers: int
    aggregate: dict
    best_performer: dict
    slowest_worker: dict


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


@router.get("/workers/{worker_id}", response_model=WorkerMetrics)
async def get_worker_metrics(worker_id: str):
    """Get performance metrics for a specific worker."""
    tracker = get_worker_metrics_tracker()
    metrics = tracker.get_worker_metrics(worker_id)
    
    if not metrics:
        return {
            "worker_id": worker_id,
            "total_tasks": 0,
            "total_errors": 0,
            "avg_duration_seconds": 0.0,
            "error_rate": 0.0,
            "task_rate_per_minute": 0.0,
            "uptime_seconds": 0,
            "restart_count": 0,
            "last_heartbeat": None,
            "last_update": None,
        }
    
    return metrics


@router.get("/workers", response_model=List[WorkerMetrics])
async def get_all_workers_metrics():
    """Get performance metrics for all workers."""
    tracker = get_worker_metrics_tracker()
    return tracker.get_all_workers_metrics()


@router.get("/workers/compare", response_model=WorkerComparison)
async def compare_workers():
    """Compare performance across all workers."""
    tracker = get_worker_metrics_tracker()
    comparison = tracker.compare_workers()
    
    if not comparison:
        return {
            "total_workers": 0,
            "aggregate": {
                "total_tasks": 0,
                "total_errors": 0,
                "avg_duration_seconds": 0.0,
                "avg_task_rate_per_minute": 0.0,
            },
            "best_performer": {
                "worker_id": "N/A",
                "task_rate_per_minute": 0.0,
            },
            "slowest_worker": {
                "worker_id": "N/A",
                "avg_duration_seconds": 0.0,
            },
        }
    
    return comparison


@router.get("/workers/{worker_id}/history")
async def get_worker_task_history(worker_id: str, limit: int = 100):
    """Get recent task execution history for a worker."""
    tracker = get_worker_metrics_tracker()
    return {
        "worker_id": worker_id,
        "history": tracker.get_worker_task_history(worker_id, limit)
    }

