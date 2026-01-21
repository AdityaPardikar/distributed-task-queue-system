"""Dashboard routes for system health and monitoring."""

from datetime import datetime, timedelta

import psutil
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.routes.metrics import WorkerMetrics
from src.core.broker import get_broker
from src.db.session import get_db
from src.models import Task, Worker
from src.monitoring.worker_metrics import get_worker_metrics_tracker

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class SystemStats(BaseModel):
    """System overview statistics."""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    pending_tasks: int
    running_tasks: int
    total_workers: int
    active_workers: int
    dead_workers: int
    queue_depth_high: int
    queue_depth_medium: int
    queue_depth_low: int
    system_cpu_percent: float
    system_memory_percent: float
    timestamp: datetime


class WorkerGridItem(BaseModel):
    """Worker information for grid display."""
    worker_id: str
    hostname: str
    status: str
    capacity: int
    current_load: int
    last_heartbeat: datetime | None
    uptime_seconds: int
    task_rate_per_minute: float
    total_tasks: int
    total_errors: int


class RecentTask(BaseModel):
    """Recent task information."""
    task_id: str
    task_name: str
    status: str
    priority: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: float | None
    worker_id: str | None
    error_message: str | None


class QueueMetrics(BaseModel):
    """Real-time queue metrics."""
    high_priority_depth: int
    medium_priority_depth: int
    low_priority_depth: int
    total_depth: int
    oldest_task_age_seconds: float | None
    avg_wait_time_seconds: float | None


class HourlyTaskStats(BaseModel):
    """Hourly task statistics."""
    hour: str
    submitted: int
    completed: int
    failed: int


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(db: Session = Depends(get_db)):
    """Get comprehensive system statistics overview."""
    # Task counts
    total_tasks = db.query(Task).count()
    completed = db.query(Task).filter(Task.status == "COMPLETED").count()
    failed = db.query(Task).filter(Task.status == "FAILED").count()
    pending = db.query(Task).filter(Task.status == "PENDING").count()
    running = db.query(Task).filter(Task.status == "RUNNING").count()
    
    # Worker counts
    total_workers = db.query(Worker).count()
    active_workers = db.query(Worker).filter(Worker.status == "ACTIVE").count()
    dead_workers = db.query(Worker).filter(Worker.status == "DEAD").count()
    
    # Queue depth by priority
    broker = get_broker()
    queue_high = broker.get_queue_length("HIGH")
    queue_medium = broker.get_queue_length("MEDIUM")
    queue_low = broker.get_queue_length("LOW")
    
    # System resource usage
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    return SystemStats(
        total_tasks=total_tasks,
        completed_tasks=completed,
        failed_tasks=failed,
        pending_tasks=pending,
        running_tasks=running,
        total_workers=total_workers,
        active_workers=active_workers,
        dead_workers=dead_workers,
        queue_depth_high=queue_high,
        queue_depth_medium=queue_medium,
        queue_depth_low=queue_low,
        system_cpu_percent=cpu_percent,
        system_memory_percent=memory.percent,
        timestamp=datetime.utcnow(),
    )


@router.get("/workers", response_model=list[WorkerGridItem])
async def get_workers_grid(db: Session = Depends(get_db)):
    """Get worker information for dashboard grid display."""
    workers = db.query(Worker).all()
    tracker = get_worker_metrics_tracker()
    
    grid_items = []
    for worker in workers:
        worker_id = str(worker.worker_id)
        metrics = tracker.get_worker_metrics(worker_id)
        
        grid_items.append(WorkerGridItem(
            worker_id=worker_id,
            hostname=worker.hostname,
            status=worker.status,
            capacity=worker.capacity,
            current_load=worker.current_load,
            last_heartbeat=worker.last_heartbeat,
            uptime_seconds=metrics.get("uptime_seconds", 0),
            task_rate_per_minute=metrics.get("task_rate_per_minute", 0.0),
            total_tasks=metrics.get("total_tasks", 0),
            total_errors=metrics.get("total_errors", 0),
        ))
    
    return grid_items


@router.get("/recent-tasks", response_model=list[RecentTask])
async def get_recent_tasks(
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get recent tasks for dashboard display."""
    tasks = (
        db.query(Task)
        .order_by(Task.created_at.desc())
        .limit(limit)
        .all()
    )
    
    recent_tasks = []
    for task in tasks:
        duration = None
        if task.completed_at and task.started_at:
            duration = (task.completed_at - task.started_at).total_seconds()
        
        recent_tasks.append(RecentTask(
            task_id=str(task.task_id),
            task_name=task.task_name,
            status=task.status,
            priority=task.priority,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            duration_seconds=duration,
            worker_id=str(task.worker_id) if task.worker_id else None,
            error_message=task.error_message,
        ))
    
    return recent_tasks


@router.get("/queue-depth", response_model=QueueMetrics)
async def get_queue_depth(db: Session = Depends(get_db)):
    """Get real-time queue metrics."""
    broker = get_broker()
    
    # Get queue depths
    high_depth = broker.get_queue_length("HIGH")
    medium_depth = broker.get_queue_length("MEDIUM")
    low_depth = broker.get_queue_length("LOW")
    total_depth = high_depth + medium_depth + low_depth
    
    # Find oldest pending task
    oldest_task = (
        db.query(Task)
        .filter(Task.status == "PENDING")
        .order_by(Task.created_at.asc())
        .first()
    )
    
    oldest_age = None
    if oldest_task:
        oldest_age = (datetime.utcnow() - oldest_task.created_at).total_seconds()
    
    # Calculate average wait time for recently completed tasks
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_completed = (
        db.query(Task)
        .filter(
            Task.status == "COMPLETED",
            Task.completed_at >= one_hour_ago,
            Task.started_at.isnot(None),
        )
        .all()
    )
    
    avg_wait = None
    if recent_completed:
        wait_times = [
            (t.started_at - t.created_at).total_seconds()
            for t in recent_completed
        ]
        avg_wait = sum(wait_times) / len(wait_times)
    
    return QueueMetrics(
        high_priority_depth=high_depth,
        medium_priority_depth=medium_depth,
        low_priority_depth=low_depth,
        total_depth=total_depth,
        oldest_task_age_seconds=oldest_age,
        avg_wait_time_seconds=avg_wait,
    )


@router.get("/hourly-stats", response_model=list[HourlyTaskStats])
async def get_hourly_stats(hours: int = 24, db: Session = Depends(get_db)):
    """Get hourly task statistics for the last N hours."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Query tasks created in the last N hours
    tasks = db.query(Task).filter(Task.created_at >= cutoff).all()
    
    # Group by hour
    hourly_data = {}
    for task in tasks:
        hour_key = task.created_at.strftime("%Y-%m-%d %H:00")
        
        if hour_key not in hourly_data:
            hourly_data[hour_key] = {
                "submitted": 0,
                "completed": 0,
                "failed": 0,
            }
        
        hourly_data[hour_key]["submitted"] += 1
        if task.status == "COMPLETED":
            hourly_data[hour_key]["completed"] += 1
        elif task.status == "FAILED":
            hourly_data[hour_key]["failed"] += 1
    
    # Convert to list and sort
    stats = [
        HourlyTaskStats(
            hour=hour,
            submitted=data["submitted"],
            completed=data["completed"],
            failed=data["failed"],
        )
        for hour, data in sorted(hourly_data.items())
    ]
    
    return stats


@router.get("/daily-stats")
async def get_daily_stats(days: int = 7, db: Session = Depends(get_db)):
    """Get daily task statistics for the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Query tasks created in the last N days
    tasks = db.query(Task).filter(Task.created_at >= cutoff).all()
    
    # Group by day
    daily_data = {}
    for task in tasks:
        day_key = task.created_at.strftime("%Y-%m-%d")
        
        if day_key not in daily_data:
            daily_data[day_key] = {
                "submitted": 0,
                "completed": 0,
                "failed": 0,
                "avg_duration": [],
            }
        
        daily_data[day_key]["submitted"] += 1
        if task.status == "COMPLETED":
            daily_data[day_key]["completed"] += 1
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                daily_data[day_key]["avg_duration"].append(duration)
        elif task.status == "FAILED":
            daily_data[day_key]["failed"] += 1
    
    # Calculate averages and format
    stats = []
    for day, data in sorted(daily_data.items()):
        avg_duration = (
            sum(data["avg_duration"]) / len(data["avg_duration"])
            if data["avg_duration"]
            else 0.0
        )
        stats.append({
            "day": day,
            "submitted": data["submitted"],
            "completed": data["completed"],
            "failed": data["failed"],
            "avg_duration_seconds": round(avg_duration, 2),
        })
    
    return stats
