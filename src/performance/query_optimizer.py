"""Query optimizer for database performance.

Provides eager loading strategies, pagination utilities, and query analysis
to eliminate N+1 queries and improve overall database performance.
"""

import time
import logging
from typing import Any, Generic, TypeVar, Optional
from dataclasses import dataclass, field

from sqlalchemy import func, text, event
from sqlalchemy.orm import Session, joinedload, selectinload, Query

from src.models import Task, Worker, Campaign, TaskResult, TaskLog, TaskExecution

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class PaginatedResult(Generic[T]):
    """Paginated query result with metadata."""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_cursor: Optional[str] = None


@dataclass
class QueryMetrics:
    """Metrics collected from query execution."""

    query_text: str
    execution_time_ms: float
    rows_returned: int
    timestamp: float = field(default_factory=time.time)


class QueryOptimizer:
    """Optimizes database queries for performance."""

    def __init__(self):
        self._query_log: list[QueryMetrics] = []
        self._max_log_size = 1000

    def get_tasks_with_relations(
        self,
        db: Session,
        *,
        status: Optional[str] = None,
        worker_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResult:
        """Fetch tasks with eagerly loaded relationships to avoid N+1 queries."""
        start = time.time()

        query = db.query(Task).options(
            joinedload(Task.worker),
            joinedload(Task.campaign),
            joinedload(Task.result),
            selectinload(Task.logs),
            selectinload(Task.executions),
        )

        if status:
            query = query.filter(Task.status == status)
        if worker_id:
            query = query.filter(Task.worker_id == worker_id)
        if campaign_id:
            query = query.filter(Task.campaign_id == campaign_id)

        total = query.count()
        total_pages = max(1, (total + page_size - 1) // page_size)

        items = (
            query.order_by(Task.priority.desc(), Task.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        elapsed = (time.time() - start) * 1000
        self._record_query("get_tasks_with_relations", elapsed, len(items))

        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    def get_tasks_cursor_paginated(
        self,
        db: Session,
        *,
        cursor: Optional[str] = None,
        page_size: int = 50,
        status: Optional[str] = None,
    ) -> PaginatedResult:
        """Cursor-based pagination for efficient large dataset traversal."""
        start = time.time()

        query = db.query(Task).options(
            joinedload(Task.worker),
            joinedload(Task.result),
        )

        if status:
            query = query.filter(Task.status == status)

        if cursor:
            query = query.filter(Task.task_id > cursor)

        query = query.order_by(Task.task_id.asc())
        items = query.limit(page_size + 1).all()

        has_next = len(items) > page_size
        if has_next:
            items = items[:page_size]

        next_cursor = items[-1].task_id if items and has_next else None
        total = db.query(func.count(Task.task_id)).scalar() or 0

        elapsed = (time.time() - start) * 1000
        self._record_query("get_tasks_cursor_paginated", elapsed, len(items))

        return PaginatedResult(
            items=items,
            total=total,
            page=1,
            page_size=page_size,
            total_pages=-1,  # Unknown with cursor pagination
            has_next=has_next,
            has_prev=cursor is not None,
            next_cursor=next_cursor,
        )

    def get_worker_with_tasks(
        self, db: Session, worker_id: str
    ) -> Optional[Worker]:
        """Fetch worker with eagerly loaded active tasks."""
        return (
            db.query(Worker)
            .options(selectinload(Worker.tasks))
            .filter(Worker.worker_id == worker_id)
            .first()
        )

    def get_campaign_summary(self, db: Session, campaign_id: str) -> dict:
        """Get campaign with aggregated task statistics in single query."""
        start = time.time()

        result = (
            db.query(
                Campaign,
                func.count(Task.task_id).label("total_tasks"),
                func.count(
                    func.nullif(Task.status != "COMPLETED", True)
                ).label("completed"),
                func.count(
                    func.nullif(Task.status != "FAILED", True)
                ).label("failed"),
                func.count(
                    func.nullif(Task.status != "PENDING", True)
                ).label("pending"),
            )
            .outerjoin(Task, Campaign.campaign_id == Task.campaign_id)
            .filter(Campaign.campaign_id == campaign_id)
            .group_by(Campaign.campaign_id)
            .first()
        )

        elapsed = (time.time() - start) * 1000
        self._record_query("get_campaign_summary", elapsed, 1 if result else 0)

        if not result:
            return {}

        campaign, total, completed, failed, pending = result
        return {
            "campaign": campaign,
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "running": total - completed - failed - pending,
        }

    def get_task_stats_by_status(self, db: Session) -> dict[str, int]:
        """Get task count grouped by status in a single query."""
        start = time.time()

        results = (
            db.query(Task.status, func.count(Task.task_id))
            .group_by(Task.status)
            .all()
        )

        elapsed = (time.time() - start) * 1000
        self._record_query("get_task_stats_by_status", elapsed, len(results))

        return {status: count for status, count in results}

    def get_slow_queries(self, threshold_ms: float = 100.0) -> list[QueryMetrics]:
        """Return queries that exceeded the given threshold."""
        return [q for q in self._query_log if q.execution_time_ms > threshold_ms]

    def get_query_stats(self) -> dict:
        """Return aggregate query performance statistics."""
        if not self._query_log:
            return {"total_queries": 0}

        times = [q.execution_time_ms for q in self._query_log]
        sorted_times = sorted(times)
        n = len(sorted_times)

        return {
            "total_queries": n,
            "avg_ms": sum(times) / n,
            "min_ms": sorted_times[0],
            "max_ms": sorted_times[-1],
            "p50_ms": sorted_times[n // 2],
            "p95_ms": sorted_times[int(n * 0.95)] if n >= 20 else sorted_times[-1],
            "p99_ms": sorted_times[int(n * 0.99)] if n >= 100 else sorted_times[-1],
            "slow_queries": len(self.get_slow_queries()),
        }

    def _record_query(self, name: str, elapsed_ms: float, rows: int):
        """Record query metrics for analysis."""
        metric = QueryMetrics(
            query_text=name,
            execution_time_ms=elapsed_ms,
            rows_returned=rows,
        )
        self._query_log.append(metric)

        if len(self._query_log) > self._max_log_size:
            self._query_log = self._query_log[-self._max_log_size:]

        if elapsed_ms > 100:
            logger.warning(
                "Slow query detected: %s took %.2fms (%d rows)",
                name, elapsed_ms, rows,
            )
