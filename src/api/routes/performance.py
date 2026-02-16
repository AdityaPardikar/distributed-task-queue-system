"""Performance monitoring and optimization API endpoints."""

import time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.performance.query_optimizer import QueryOptimizer
from src.performance.db_optimizer import DatabaseOptimizer
from src.performance.profiler import get_profiler
from src.performance.batch_processor import BatchProcessor
from src.db.session import engine

router = APIRouter(prefix="/performance", tags=["performance"])

query_optimizer = QueryOptimizer()
db_optimizer = DatabaseOptimizer(engine)
batch_processor = BatchProcessor()


@router.get("/stats")
async def get_performance_stats():
    """Get overall application performance statistics."""
    profiler = get_profiler()
    return {
        "overall": profiler.get_overall_stats(),
        "system": profiler.get_system_metrics(),
        "database": {
            "pool": {
                "pool_size": db_optimizer.get_connection_pool_stats().pool_size,
                "checked_in": db_optimizer.get_connection_pool_stats().checked_in,
                "checked_out": db_optimizer.get_connection_pool_stats().checked_out,
            },
            "query_stats": query_optimizer.get_query_stats(),
        },
    }


@router.get("/endpoints")
async def get_endpoint_stats():
    """Get per-endpoint performance statistics."""
    profiler = get_profiler()
    return {
        "endpoints": profiler.get_endpoint_stats(),
        "slowest": profiler.get_slowest_endpoints(10),
    }


@router.get("/database/info")
async def get_database_info(db: Session = Depends(get_db)):
    """Get database information and statistics."""
    return db_optimizer.get_database_info(db)


@router.get("/database/tables")
async def get_table_sizes(db: Session = Depends(get_db)):
    """Get table size information."""
    return db_optimizer.get_table_sizes(db)


@router.get("/database/indexes")
async def get_indexes():
    """Get all database indexes."""
    indexes = db_optimizer.get_all_indexes()
    return {
        "total_indexes": len(indexes),
        "indexes": [
            {
                "table": idx.table_name,
                "name": idx.index_name,
                "columns": idx.columns,
                "unique": idx.is_unique,
            }
            for idx in indexes
        ],
    }


@router.get("/database/suggestions")
async def get_index_suggestions(db: Session = Depends(get_db)):
    """Get missing index suggestions."""
    return {
        "suggestions": db_optimizer.analyze_missing_indexes(db),
    }


@router.post("/database/maintenance")
async def run_maintenance(db: Session = Depends(get_db)):
    """Run database maintenance tasks (ANALYZE)."""
    results = db_optimizer.run_maintenance(db)
    return {"maintenance": results}


@router.get("/queries/slow")
async def get_slow_queries(
    threshold_ms: float = Query(100.0, description="Threshold in milliseconds"),
):
    """Get slow queries above threshold."""
    slow = query_optimizer.get_slow_queries(threshold_ms)
    return {
        "threshold_ms": threshold_ms,
        "count": len(slow),
        "queries": [
            {
                "query": q.query_text,
                "time_ms": round(q.execution_time_ms, 2),
                "rows": q.rows_returned,
            }
            for q in slow
        ],
    }


@router.get("/tasks/optimized")
async def get_tasks_optimized(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Fetch tasks with optimized eager loading and pagination."""
    result = query_optimizer.get_tasks_with_relations(
        db, status=status, page=page, page_size=page_size
    )
    return {
        "items": [
            {
                "task_id": t.task_id,
                "task_name": t.task_name,
                "status": t.status,
                "priority": t.priority,
                "worker_id": t.worker_id,
                "created_at": str(t.created_at),
            }
            for t in result.items
        ],
        "pagination": {
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
            "has_next": result.has_next,
            "has_prev": result.has_prev,
        },
    }


@router.get("/tasks/cursor")
async def get_tasks_cursor(
    cursor: Optional[str] = None,
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Cursor-based pagination for large task datasets."""
    result = query_optimizer.get_tasks_cursor_paginated(
        db, cursor=cursor, page_size=page_size, status=status
    )
    return {
        "items": [
            {
                "task_id": t.task_id,
                "task_name": t.task_name,
                "status": t.status,
                "priority": t.priority,
            }
            for t in result.items
        ],
        "pagination": {
            "has_next": result.has_next,
            "next_cursor": result.next_cursor,
            "page_size": result.page_size,
        },
    }


@router.get("/tasks/stats")
async def get_task_stats(db: Session = Depends(get_db)):
    """Get task statistics aggregated by status."""
    stats = query_optimizer.get_task_stats_by_status(db)
    return {
        "by_status": stats,
        "total": sum(stats.values()),
    }


@router.post("/tasks/batch/cancel-stale")
async def cancel_stale_tasks(
    timeout_seconds: int = Query(300, ge=60),
    db: Session = Depends(get_db),
):
    """Cancel tasks that have been running longer than timeout."""
    result = batch_processor.bulk_cancel_stale_tasks(db, timeout_seconds)
    return {
        "cancelled": result.processed,
        "duration_ms": result.duration_ms,
    }


@router.post("/tasks/batch/requeue-failed")
async def requeue_failed_tasks(
    max_retries: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
):
    """Requeue failed tasks that haven't exceeded max retries."""
    result = batch_processor.requeue_failed_tasks(db, max_retries)
    return {
        "requeued": result.processed,
        "duration_ms": result.duration_ms,
    }


@router.post("/reset")
async def reset_performance_stats():
    """Reset all performance statistics."""
    profiler = get_profiler()
    profiler.reset()
    return {"status": "reset"}
