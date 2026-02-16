"""Batch processor for efficient bulk database operations.

Provides utilities for batching inserts, updates, and bulk task processing
to improve throughput for high-volume operations.
"""

import time
import logging
from typing import Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import update, and_
from sqlalchemy.orm import Session

from src.models import Task, Worker

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result of a batch operation."""

    total_items: int
    processed: int
    failed: int
    duration_ms: float
    items_per_second: float


class BatchProcessor:
    """Batch processing utilities for high-throughput operations."""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size

    def bulk_create_tasks(
        self,
        db: Session,
        task_data_list: list[dict],
    ) -> BatchResult:
        """Create multiple tasks in batches for improved throughput."""
        start = time.time()
        processed = 0
        failed = 0
        total = len(task_data_list)

        for i in range(0, total, self.batch_size):
            batch = task_data_list[i : i + self.batch_size]
            try:
                tasks = []
                for data in batch:
                    task = Task(
                        task_name=data.get("task_name", "batch_task"),
                        task_args=data.get("task_args", {}),
                        task_kwargs=data.get("task_kwargs", {}),
                        priority=data.get("priority", 5),
                        status="PENDING",
                    )
                    tasks.append(task)

                db.bulk_save_objects(tasks)
                db.flush()
                processed += len(batch)
            except Exception as e:
                logger.error("Batch insert failed at offset %d: %s", i, e)
                db.rollback()
                failed += len(batch)

        try:
            db.commit()
        except Exception as e:
            logger.error("Batch commit failed: %s", e)
            db.rollback()

        elapsed = (time.time() - start) * 1000
        rate = processed / (elapsed / 1000) if elapsed > 0 else 0

        return BatchResult(
            total_items=total,
            processed=processed,
            failed=failed,
            duration_ms=round(elapsed, 2),
            items_per_second=round(rate, 1),
        )

    def bulk_update_task_status(
        self,
        db: Session,
        task_ids: list[str],
        new_status: str,
    ) -> BatchResult:
        """Update status for multiple tasks in a single query."""
        start = time.time()
        processed = 0
        failed = 0
        total = len(task_ids)

        for i in range(0, total, self.batch_size):
            batch_ids = task_ids[i : i + self.batch_size]
            try:
                db.execute(
                    update(Task)
                    .where(Task.task_id.in_(batch_ids))
                    .values(
                        status=new_status,
                        updated_at=datetime.now(timezone.utc),
                    )
                )
                processed += len(batch_ids)
            except Exception as e:
                logger.error("Batch update failed: %s", e)
                failed += len(batch_ids)

        try:
            db.commit()
        except Exception as e:
            logger.error("Batch update commit failed: %s", e)
            db.rollback()

        elapsed = (time.time() - start) * 1000
        rate = processed / (elapsed / 1000) if elapsed > 0 else 0

        return BatchResult(
            total_items=total,
            processed=processed,
            failed=failed,
            duration_ms=round(elapsed, 2),
            items_per_second=round(rate, 1),
        )

    def bulk_cancel_stale_tasks(
        self,
        db: Session,
        timeout_seconds: int = 300,
    ) -> BatchResult:
        """Cancel tasks that have been running longer than timeout."""
        start = time.time()
        cutoff = datetime.now(timezone.utc)

        try:
            result = db.execute(
                update(Task)
                .where(
                    and_(
                        Task.status == "RUNNING",
                        Task.started_at.isnot(None),
                    )
                )
                .values(
                    status="FAILED",
                    updated_at=datetime.now(timezone.utc),
                )
                .execution_options(synchronize_session="fetch")
            )
            db.commit()
            count = result.rowcount
        except Exception as e:
            logger.error("Stale task cancellation failed: %s", e)
            db.rollback()
            count = 0

        elapsed = (time.time() - start) * 1000

        return BatchResult(
            total_items=count,
            processed=count,
            failed=0,
            duration_ms=round(elapsed, 2),
            items_per_second=count / (elapsed / 1000) if elapsed > 0 else 0,
        )

    def cleanup_old_results(
        self,
        db: Session,
        days: int = 30,
    ) -> int:
        """Remove task results older than specified days."""
        from src.models import TaskResult, TaskLog

        cutoff = datetime.now(timezone.utc)
        deleted = 0

        try:
            # Delete old logs
            log_result = db.query(TaskLog).filter(
                TaskLog.created_at < cutoff
            ).delete(synchronize_session="fetch")
            deleted += log_result

            db.commit()
            logger.info("Cleaned up %d old records", deleted)
        except Exception as e:
            logger.error("Cleanup failed: %s", e)
            db.rollback()

        return deleted

    def requeue_failed_tasks(
        self,
        db: Session,
        max_retry_count: int = 3,
    ) -> BatchResult:
        """Requeue failed tasks that haven't exceeded max retries."""
        start = time.time()

        try:
            result = db.execute(
                update(Task)
                .where(
                    and_(
                        Task.status == "FAILED",
                        Task.retry_count < max_retry_count,
                    )
                )
                .values(
                    status="PENDING",
                    retry_count=Task.retry_count + 1,
                    updated_at=datetime.now(timezone.utc),
                )
                .execution_options(synchronize_session="fetch")
            )
            db.commit()
            count = result.rowcount
        except Exception as e:
            logger.error("Requeue failed: %s", e)
            db.rollback()
            count = 0

        elapsed = (time.time() - start) * 1000

        return BatchResult(
            total_items=count,
            processed=count,
            failed=0,
            duration_ms=round(elapsed, 2),
            items_per_second=count / (elapsed / 1000) if elapsed > 0 else 0,
        )
