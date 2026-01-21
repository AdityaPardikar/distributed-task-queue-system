"""Analytics API routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.analytics.trends import TaskAnalytics
from src.db.session import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


class CompletionRateTrend(BaseModel):
    """Completion rate trend data point."""
    timestamp: str
    completed: int
    failed: int
    rate: float


class WaitTimeTrend(BaseModel):
    """Wait time trend data point."""
    timestamp: str
    min_wait: float
    max_wait: float
    avg_wait: float


class PeakLoad(BaseModel):
    """Peak load time information."""
    timestamp: str
    submitted: int


class TaskTypeDistribution(BaseModel):
    """Task type distribution information."""
    task_name: str
    total: int
    completed: int
    failed: int
    pending: int
    percentage: float


class FailurePattern(BaseModel):
    """Failure pattern information."""
    task_name: str
    error: str
    count: int
    last_occurrence: datetime | None


class RetryStats(BaseModel):
    """Retry statistics for a task type."""
    task_name: str
    total_retries: int
    successful_after_retry: int
    failed_after_retry: int
    success_rate: float
    avg_retries: float


@router.get("/completion-rate-trend", response_model=list[CompletionRateTrend])
async def get_completion_rate_trend(
    hours: int = Query(24, ge=1, le=720),
    interval_minutes: int = Query(60, ge=1, le=1440),
    db: Session = Depends(get_db),
):
    """Get task completion rate trends over time."""
    trends = TaskAnalytics.get_completion_rate_trend(db, hours, interval_minutes)
    return trends


@router.get("/wait-time-trend", response_model=list[WaitTimeTrend])
async def get_wait_time_trend(
    hours: int = Query(24, ge=1, le=720),
    interval_minutes: int = Query(60, ge=1, le=1440),
    db: Session = Depends(get_db),
):
    """Get average task wait time trends."""
    trends = TaskAnalytics.get_average_wait_time_trend(db, hours, interval_minutes)
    return trends


@router.get("/peak-loads", response_model=list[PeakLoad])
async def get_peak_loads(
    hours: int = Query(24, ge=1, le=720),
    interval_minutes: int = Query(60, ge=1, le=1440),
    top_n: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get peak load times (highest task submission rates)."""
    peaks = TaskAnalytics.get_peak_load_times(db, hours, interval_minutes, top_n)
    return peaks


@router.get("/task-distribution", response_model=list[TaskTypeDistribution])
async def get_task_distribution(
    hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db),
):
    """Get distribution of tasks by type."""
    distribution = TaskAnalytics.get_task_type_distribution(db, hours)
    return distribution


@router.get("/failure-patterns", response_model=list[FailurePattern])
async def get_failure_patterns(
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get most common failure patterns."""
    patterns = TaskAnalytics.get_failed_task_patterns(db, hours, limit)
    return patterns


@router.get("/retry-success-rate")
async def get_retry_success_rate(
    hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db),
):
    """Get retry success rate by task type."""
    stats = TaskAnalytics.get_retry_success_rate(db, hours)
    return stats


@router.get("/performance-summary")
async def get_performance_summary(db: Session = Depends(get_db)):
    """Get comprehensive performance summary."""
    summary = TaskAnalytics.get_performance_summary(db)
    return summary
