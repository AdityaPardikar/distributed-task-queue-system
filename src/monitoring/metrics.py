"""Prometheus metrics setup and helpers."""

from typing import Optional

from fastapi import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Counters
TASKS_SUBMITTED = Counter(
    "tasks_submitted_total",
    "Total tasks submitted to the system",
    labelnames=["task_name", "priority"],
)
TASKS_COMPLETED = Counter(
    "tasks_completed_total",
    "Total tasks completed successfully",
    labelnames=["task_name"],
)
TASKS_FAILED = Counter(
    "tasks_failed_total",
    "Total tasks that failed",
    labelnames=["task_name"],
)

# Gauges
QUEUE_DEPTH = Gauge("queue_depth", "Current depth of the task queue")
ACTIVE_WORKERS = Gauge("active_workers", "Number of active workers")
WORKER_CAPACITY_UTILIZATION = Gauge(
    "worker_capacity_utilization",
    "Worker capacity utilization as a ratio between 0 and 1",
)

# Histograms
TASK_EXECUTION_DURATION = Histogram(
    "task_execution_duration_seconds",
    "Task execution duration in seconds",
    labelnames=["task_name"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300),
)
TASK_WAIT_TIME = Histogram(
    "task_wait_time_seconds",
    "Time a task waits in queue before execution",
    labelnames=["task_name"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60),
)
HTTP_REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=["method", "path", "status_code"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)


def record_task_submitted(task_name: str, priority: int) -> None:
    """Increment submitted counter for a task."""
    TASKS_SUBMITTED.labels(task_name=task_name, priority=str(priority)).inc()


def record_task_completed(task_name: str) -> None:
    """Increment completed counter for a task."""
    TASKS_COMPLETED.labels(task_name=task_name).inc()


def record_task_failed(task_name: str) -> None:
    """Increment failure counter for a task."""
    TASKS_FAILED.labels(task_name=task_name).inc()


def observe_task_duration(task_name: str, duration_seconds: float) -> None:
    """Observe execution duration for a task."""
    TASK_EXECUTION_DURATION.labels(task_name=task_name).observe(duration_seconds)


def observe_task_wait(task_name: str, wait_seconds: float) -> None:
    """Observe queue wait time for a task."""
    TASK_WAIT_TIME.labels(task_name=task_name).observe(wait_seconds)


def observe_http_request(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    """Observe HTTP request latency for Prometheus histogram."""
    HTTP_REQUEST_LATENCY.labels(method=method, path=path, status_code=str(status_code)).observe(duration_seconds)


def set_queue_depth(depth: int) -> None:
    """Set queue depth gauge."""
    QUEUE_DEPTH.set(depth)


def set_active_workers(count: int) -> None:
    """Set active worker gauge."""
    ACTIVE_WORKERS.set(count)


def set_worker_capacity_utilization(ratio: Optional[float]) -> None:
    """Set worker capacity utilization gauge."""
    if ratio is None:
        WORKER_CAPACITY_UTILIZATION.set(0)
    else:
        WORKER_CAPACITY_UTILIZATION.set(max(0.0, min(1.0, ratio)))


def prometheus_response() -> Response:
    """Return a Prometheus scrape-compatible response."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
