"""Worker-specific performance metrics and tracking."""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from prometheus_client import Gauge, Histogram

from src.cache.client import RedisClient, get_redis_client

# Worker-specific Prometheus metrics
WORKER_TASK_RATE = Gauge(
    "worker_task_rate",
    "Task processing rate per worker (tasks/minute)",
    labelnames=["worker_id"],
)
WORKER_AVG_DURATION = Gauge(
    "worker_avg_task_duration_seconds",
    "Average task execution duration per worker",
    labelnames=["worker_id"],
)
WORKER_ERROR_RATE = Gauge(
    "worker_error_rate",
    "Error rate per worker (errors/minute)",
    labelnames=["worker_id"],
)
WORKER_UPTIME = Gauge(
    "worker_uptime_seconds",
    "Worker uptime in seconds since last start",
    labelnames=["worker_id"],
)
WORKER_RESTART_COUNT = Gauge(
    "worker_restart_count",
    "Number of times worker has restarted",
    labelnames=["worker_id"],
)
WORKER_TASK_DURATION_HISTOGRAM = Histogram(
    "worker_task_duration_seconds",
    "Task execution duration histogram per worker",
    labelnames=["worker_id", "task_name"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300),
)


class WorkerMetricsTracker:
    """Track and store worker performance metrics in Redis."""

    METRICS_TTL = 86400  # 24 hours retention

    def __init__(self, redis_client: Optional[RedisClient] = None):
        """Initialize worker metrics tracker."""
        self.redis = redis_client or get_redis_client()

    def _metrics_key(self, worker_id: str) -> str:
        """Generate Redis key for worker metrics."""
        return f"worker:metrics:{worker_id}"

    def _task_log_key(self, worker_id: str) -> str:
        """Generate Redis key for worker task execution log."""
        return f"worker:task_log:{worker_id}"

    def record_task_start(
        self,
        worker_id: str,
        task_id: str,
        task_name: str,
    ) -> None:
        """Record when a worker starts processing a task."""
        timestamp = datetime.utcnow().isoformat()
        log_entry = json.dumps({
            "task_id": task_id,
            "task_name": task_name,
            "start_time": timestamp,
            "status": "running",
        })

        # Add to task log (use sorted set for time-based queries)
        score = datetime.utcnow().timestamp()
        log_key = self._task_log_key(worker_id)
        self.redis.zadd(log_key, {log_entry: score})
        self.redis.expire(log_key, self.METRICS_TTL)

    def record_task_complete(
        self,
        worker_id: str,
        task_id: str,
        task_name: str,
        duration_seconds: float,
        success: bool = True,
    ) -> None:
        """Record task completion and update worker metrics."""
        # Update task log
        timestamp = datetime.utcnow().isoformat()
        log_entry = json.dumps({
            "task_id": task_id,
            "task_name": task_name,
            "completion_time": timestamp,
            "duration": duration_seconds,
            "status": "success" if success else "failed",
        })
        score = datetime.utcnow().timestamp()
        log_key = self._task_log_key(worker_id)
        self.redis.zadd(log_key, {log_entry: score})

        # Update aggregated metrics
        metrics_key = self._metrics_key(worker_id)
        current_time = datetime.utcnow()

        # Increment counters
        self.redis.hincrby(metrics_key, "total_tasks", 1)
        if not success:
            self.redis.hincrby(metrics_key, "total_errors", 1)

        # Update duration stats (running average)
        self.redis.hincrbyfloat(metrics_key, "total_duration", duration_seconds)

        # Store last update time
        self.redis.hset(metrics_key, "last_update", current_time.isoformat())

        # Set TTL
        self.redis.expire(metrics_key, self.METRICS_TTL)

        # Update Prometheus metrics
        self._update_prometheus_metrics(worker_id)

        # Record in histogram
        WORKER_TASK_DURATION_HISTOGRAM.labels(
            worker_id=worker_id,
            task_name=task_name
        ).observe(duration_seconds)

    def record_worker_start(self, worker_id: str) -> None:
        """Record when a worker starts."""
        metrics_key = self._metrics_key(worker_id)
        current_time = datetime.utcnow()

        # Increment restart count
        restart_count = self.redis.hincrby(metrics_key, "restart_count", 1)

        # Set start time
        self.redis.hset(metrics_key, "start_time", current_time.isoformat())
        self.redis.hset(metrics_key, "last_heartbeat", current_time.isoformat())

        # Set TTL
        self.redis.expire(metrics_key, self.METRICS_TTL)

        # Update Prometheus restart count
        WORKER_RESTART_COUNT.labels(worker_id=worker_id).set(restart_count)

    def record_heartbeat(self, worker_id: str) -> None:
        """Record worker heartbeat."""
        metrics_key = self._metrics_key(worker_id)
        current_time = datetime.utcnow()

        self.redis.hset(metrics_key, "last_heartbeat", current_time.isoformat())
        self.redis.expire(metrics_key, self.METRICS_TTL)

    def get_worker_metrics(self, worker_id: str) -> Dict:
        """Get aggregated metrics for a worker."""
        metrics_key = self._metrics_key(worker_id)
        data = self.redis.hgetall(metrics_key)

        if not data:
            return {}

        # Calculate derived metrics
        total_tasks = int(data.get("total_tasks", 0))
        total_errors = int(data.get("total_errors", 0))
        total_duration = float(data.get("total_duration", 0))

        avg_duration = total_duration / total_tasks if total_tasks > 0 else 0
        error_rate = total_errors / total_tasks if total_tasks > 0 else 0

        # Calculate uptime
        start_time = data.get("start_time")
        uptime_seconds = 0
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            uptime_seconds = (datetime.utcnow() - start_dt).total_seconds()

        # Calculate task rate (tasks per minute in last hour)
        task_rate = self._calculate_task_rate(worker_id)

        return {
            "worker_id": worker_id,
            "total_tasks": total_tasks,
            "total_errors": total_errors,
            "avg_duration_seconds": round(avg_duration, 3),
            "error_rate": round(error_rate, 4),
            "task_rate_per_minute": round(task_rate, 2),
            "uptime_seconds": int(uptime_seconds),
            "restart_count": int(data.get("restart_count", 0)),
            "last_heartbeat": data.get("last_heartbeat"),
            "last_update": data.get("last_update"),
        }

    def _calculate_task_rate(self, worker_id: str) -> float:
        """Calculate task processing rate (tasks/minute) for last hour."""
        log_key = self._task_log_key(worker_id)
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).timestamp()

        # Count tasks completed in last hour
        count = self.redis.zcount(log_key, one_hour_ago, "+inf")

        # Convert to per-minute rate
        return count / 60.0

    def _update_prometheus_metrics(self, worker_id: str) -> None:
        """Update Prometheus gauges for a worker."""
        metrics = self.get_worker_metrics(worker_id)

        if not metrics:
            return

        WORKER_TASK_RATE.labels(worker_id=worker_id).set(
            metrics["task_rate_per_minute"]
        )
        WORKER_AVG_DURATION.labels(worker_id=worker_id).set(
            metrics["avg_duration_seconds"]
        )
        WORKER_ERROR_RATE.labels(worker_id=worker_id).set(
            metrics["error_rate"]
        )
        WORKER_UPTIME.labels(worker_id=worker_id).set(
            metrics["uptime_seconds"]
        )
        WORKER_RESTART_COUNT.labels(worker_id=worker_id).set(
            metrics["restart_count"]
        )

    def get_all_workers_metrics(self) -> List[Dict]:
        """Get metrics for all workers."""
        # Find all worker metric keys
        pattern = "worker:metrics:*"
        keys = self.redis.keys(pattern)

        metrics = []
        for key in keys:
            worker_id = key.split(":")[-1]
            worker_metrics = self.get_worker_metrics(worker_id)
            if worker_metrics:
                metrics.append(worker_metrics)

        return metrics

    def get_worker_task_history(
        self,
        worker_id: str,
        limit: int = 100,
    ) -> List[Dict]:
        """Get recent task execution history for a worker."""
        log_key = self._task_log_key(worker_id)

        # Get most recent entries
        entries = self.redis.zrevrange(log_key, 0, limit - 1)

        history = []
        for entry in entries:
            try:
                data = json.loads(entry)
                history.append(data)
            except json.JSONDecodeError:
                continue

        return history

    def compare_workers(self) -> Dict:
        """Compare performance across all workers."""
        all_metrics = self.get_all_workers_metrics()

        if not all_metrics:
            return {}

        # Calculate aggregate statistics
        total_tasks = sum(m["total_tasks"] for m in all_metrics)
        avg_duration = sum(m["avg_duration_seconds"] for m in all_metrics) / len(all_metrics)
        total_errors = sum(m["total_errors"] for m in all_metrics)
        avg_task_rate = sum(m["task_rate_per_minute"] for m in all_metrics) / len(all_metrics)

        # Find best/worst performers
        best_performer = max(all_metrics, key=lambda x: x["task_rate_per_minute"])
        slowest_worker = max(all_metrics, key=lambda x: x["avg_duration_seconds"])

        return {
            "total_workers": len(all_metrics),
            "aggregate": {
                "total_tasks": total_tasks,
                "total_errors": total_errors,
                "avg_duration_seconds": round(avg_duration, 3),
                "avg_task_rate_per_minute": round(avg_task_rate, 2),
            },
            "best_performer": {
                "worker_id": best_performer["worker_id"],
                "task_rate_per_minute": best_performer["task_rate_per_minute"],
            },
            "slowest_worker": {
                "worker_id": slowest_worker["worker_id"],
                "avg_duration_seconds": slowest_worker["avg_duration_seconds"],
            },
        }


# Global instance
_tracker: Optional[WorkerMetricsTracker] = None


def get_worker_metrics_tracker() -> WorkerMetricsTracker:
    """Get global worker metrics tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = WorkerMetricsTracker()
    return _tracker
