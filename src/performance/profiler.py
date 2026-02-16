"""Performance profiler for monitoring application performance.

Provides request timing, memory tracking, and system resource monitoring
for identifying bottlenecks and optimizing performance.
"""

import time
import os
import logging
import threading
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from functools import wraps
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class RequestMetric:
    """Metric for a single request."""

    method: str
    path: str
    status_code: int
    duration_ms: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class EndpointStats:
    """Aggregated statistics for an endpoint."""

    path: str
    method: str
    total_requests: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    error_count: int = 0
    _times: list[float] = field(default_factory=list)

    @property
    def avg_time_ms(self) -> float:
        return self.total_time_ms / self.total_requests if self.total_requests else 0

    @property
    def p50_ms(self) -> float:
        return self._percentile(50)

    @property
    def p95_ms(self) -> float:
        return self._percentile(95)

    @property
    def p99_ms(self) -> float:
        return self._percentile(99)

    @property
    def error_rate(self) -> float:
        return self.error_count / self.total_requests if self.total_requests else 0

    def _percentile(self, p: int) -> float:
        if not self._times:
            return 0
        sorted_times = sorted(self._times)
        idx = int(len(sorted_times) * p / 100)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    def record(self, duration_ms: float, status_code: int):
        self.total_requests += 1
        self.total_time_ms += duration_ms
        self.min_time_ms = min(self.min_time_ms, duration_ms)
        self.max_time_ms = max(self.max_time_ms, duration_ms)
        if status_code >= 400:
            self.error_count += 1
        self._times.append(duration_ms)
        # Keep only recent samples for percentile calculation
        if len(self._times) > 5000:
            self._times = self._times[-5000:]


class PerformanceProfiler:
    """Application performance profiler and monitor."""

    def __init__(self, max_history: int = 10000):
        self._request_log: list[RequestMetric] = []
        self._endpoint_stats: dict[str, EndpointStats] = {}
        self._max_history = max_history
        self._lock = threading.Lock()
        self._start_time = time.time()

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
    ):
        """Record a request metric."""
        with self._lock:
            # Normalize path (strip query params and IDs)
            normalized = self._normalize_path(path)
            key = f"{method}:{normalized}"

            metric = RequestMetric(
                method=method,
                path=normalized,
                status_code=status_code,
                duration_ms=duration_ms,
            )
            self._request_log.append(metric)

            if key not in self._endpoint_stats:
                self._endpoint_stats[key] = EndpointStats(
                    path=normalized, method=method
                )
            self._endpoint_stats[key].record(duration_ms, status_code)

            # Trim history
            if len(self._request_log) > self._max_history:
                self._request_log = self._request_log[-self._max_history:]

    def get_endpoint_stats(self) -> list[dict]:
        """Get performance stats for all endpoints."""
        with self._lock:
            stats = []
            for key, ep in self._endpoint_stats.items():
                stats.append({
                    "endpoint": f"{ep.method} {ep.path}",
                    "total_requests": ep.total_requests,
                    "avg_ms": round(ep.avg_time_ms, 2),
                    "min_ms": round(ep.min_time_ms, 2),
                    "max_ms": round(ep.max_time_ms, 2),
                    "p50_ms": round(ep.p50_ms, 2),
                    "p95_ms": round(ep.p95_ms, 2),
                    "p99_ms": round(ep.p99_ms, 2),
                    "error_rate": round(ep.error_rate * 100, 2),
                    "errors": ep.error_count,
                })
            return sorted(stats, key=lambda x: x["total_requests"], reverse=True)

    def get_slowest_endpoints(self, n: int = 10) -> list[dict]:
        """Get the N slowest endpoints by p95 latency."""
        stats = self.get_endpoint_stats()
        return sorted(stats, key=lambda x: x["p95_ms"], reverse=True)[:n]

    def get_system_metrics(self) -> dict:
        """Get current system resource metrics."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory = process.memory_info()
            return {
                "cpu_percent": process.cpu_percent(interval=0.1),
                "memory_rss_mb": round(memory.rss / 1024 / 1024, 2),
                "memory_vms_mb": round(memory.vms / 1024 / 1024, 2),
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "uptime_seconds": round(time.time() - self._start_time, 1),
            }
        except ImportError:
            return {
                "uptime_seconds": round(time.time() - self._start_time, 1),
                "note": "Install psutil for detailed system metrics",
            }

    def get_overall_stats(self) -> dict:
        """Get overall application performance summary."""
        with self._lock:
            total_requests = sum(
                ep.total_requests for ep in self._endpoint_stats.values()
            )
            total_errors = sum(
                ep.error_count for ep in self._endpoint_stats.values()
            )

            all_times = []
            for ep in self._endpoint_stats.values():
                all_times.extend(ep._times)

            if all_times:
                sorted_times = sorted(all_times)
                n = len(sorted_times)
                avg_ms = sum(sorted_times) / n
                p50 = sorted_times[n // 2]
                p95 = sorted_times[int(n * 0.95)] if n >= 20 else sorted_times[-1]
                p99 = sorted_times[int(n * 0.99)] if n >= 100 else sorted_times[-1]
            else:
                avg_ms = p50 = p95 = p99 = 0

            return {
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate_percent": round(
                    total_errors / total_requests * 100, 2
                ) if total_requests else 0,
                "avg_latency_ms": round(avg_ms, 2),
                "p50_latency_ms": round(p50, 2),
                "p95_latency_ms": round(p95, 2),
                "p99_latency_ms": round(p99, 2),
                "endpoints_tracked": len(self._endpoint_stats),
                "uptime_seconds": round(time.time() - self._start_time, 1),
            }

    def reset(self):
        """Reset all collected metrics."""
        with self._lock:
            self._request_log.clear()
            self._endpoint_stats.clear()

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize path by replacing UUIDs and IDs with placeholders."""
        import re
        # Replace UUIDs
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            path,
        )
        # Replace numeric IDs
        path = re.sub(r"/\d+(?=/|$)", "/{id}", path)
        # Strip query string
        path = path.split("?")[0]
        return path


def profile_function(func: Callable) -> Callable:
    """Decorator to profile function execution time."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.time() - start) * 1000
            if elapsed > 100:
                logger.warning(
                    "Slow function: %s.%s took %.2fms",
                    func.__module__, func.__name__, elapsed,
                )
            return result
        except Exception:
            elapsed = (time.time() - start) * 1000
            logger.error(
                "Function failed: %s.%s after %.2fms",
                func.__module__, func.__name__, elapsed,
            )
            raise

    return wrapper


# Global profiler instance
_profiler: Optional[PerformanceProfiler] = None


def get_profiler() -> PerformanceProfiler:
    """Get or create the global performance profiler."""
    global _profiler
    if _profiler is None:
        _profiler = PerformanceProfiler()
    return _profiler
