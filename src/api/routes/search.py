"""Task search and filtering API routes."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models import Task
from src.services.task_search import FilterPreset, TaskFilter

router = APIRouter(prefix="/search", tags=["search"])


class TaskSearchResult(BaseModel):
    """Task search result."""
    task_id: str
    task_name: str
    status: str
    priority: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    worker_id: Optional[str]
    retry_count: int
    error_message: Optional[str]


class SearchResponse(BaseModel):
    """Search response with pagination."""
    tasks: List[TaskSearchResult]
    total: int
    limit: int
    offset: int
    page: int


@router.get("/tasks", response_model=SearchResponse)
async def search_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[int] = Query(None, ge=1, le=10),
    task_name: Optional[str] = Query(None),
    worker_id: Optional[str] = Query(None),
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None, description="Full-text search query"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    order_by: str = Query("created_at", regex="^(created_at|priority|status)$"),
    order_desc: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Advanced task search with filtering and full-text search.
    
    Query Parameters:
        - status: Filter by status (PENDING, RUNNING, COMPLETED, FAILED, etc)
        - priority: Filter by priority (1-10)
        - task_name: Exact task name match
        - worker_id: Filter by worker ID
        - created_after: Only tasks created after this date
        - created_before: Only tasks created before this date
        - search: Full-text search across task name and arguments
        - limit: Number of results per page (max 1000)
        - offset: Pagination offset
        - order_by: Field to sort by (created_at, priority, status)
        - order_desc: Sort in descending order
    """
    tasks, total = TaskFilter.search_with_filters(
        db,
        status=status,
        priority=priority,
        task_name=task_name,
        worker_id=worker_id,
        created_after=created_after,
        created_before=created_before,
        search_query=search,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_desc=order_desc,
    )
    
    page = (offset // limit) + 1 if limit > 0 else 1
    
    return SearchResponse(
        tasks=[
            TaskSearchResult(
                task_id=str(t.task_id),
                task_name=t.task_name,
                status=t.status,
                priority=t.priority,
                created_at=t.created_at,
                started_at=t.started_at,
                completed_at=t.completed_at,
                worker_id=str(t.worker_id) if t.worker_id else None,
                retry_count=t.retry_count,
                error_message=t.error_message,
            )
            for t in tasks
        ],
        total=total,
        limit=limit,
        offset=offset,
        page=page,
    )


@router.get("/presets")
async def get_filter_presets():
    """Get available filter presets for quick searches."""
    return {
        "presets": list(TaskFilter.get_filter_presets().keys()),
        "description": "Use these preset names in the 'preset' parameter to apply predefined filters",
    }


@router.get("/presets/{preset_name}", response_model=SearchResponse)
async def apply_filter_preset(
    preset_name: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Apply a predefined filter preset.
    
    Available presets:
        - failed_today: Tasks that failed in the last 24 hours
        - high_priority_pending: High priority pending tasks
        - stuck_tasks: Tasks running for more than 1 hour
        - recently_completed: Tasks completed in the last hour
        - never_retried: Tasks with 0 retries
        - many_retries: Tasks with 3+ retries
    """
    preset = FilterPreset(db, preset_name)
    tasks, total = preset.execute(limit=limit, offset=offset)
    
    page = (offset // limit) + 1 if limit > 0 else 1
    
    return SearchResponse(
        tasks=[
            TaskSearchResult(
                task_id=str(t.task_id),
                task_name=t.task_name,
                status=t.status,
                priority=t.priority,
                created_at=t.created_at,
                started_at=t.started_at,
                completed_at=t.completed_at,
                worker_id=str(t.worker_id) if t.worker_id else None,
                retry_count=t.retry_count,
                error_message=t.error_message,
            )
            for t in tasks
        ],
        total=total,
        limit=limit,
        offset=offset,
        page=page,
    )


@router.get("/tasks/export/csv")
async def export_tasks_csv(
    status: Optional[str] = Query(None),
    priority: Optional[int] = Query(None, ge=1, le=10),
    task_name: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Export filtered tasks as CSV."""
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    
    tasks, _ = TaskFilter.search_with_filters(
        db,
        status=status,
        priority=priority,
        task_name=task_name,
        search_query=search,
        limit=10000,  # Export up to 10k tasks
    )
    
    csv_content = TaskFilter.export_to_csv(tasks)
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tasks_export.csv"},
    )


@router.post("/tasks/bulk-action")
async def bulk_action(
    action: str = Query(..., regex="^(retry|cancel|priority_boost)$"),
    status: Optional[str] = Query(None),
    priority: Optional[int] = Query(None, ge=1, le=10),
    search: Optional[str] = Query(None),
    new_priority: Optional[int] = Query(None, ge=1, le=10),
    db: Session = Depends(get_db),
):
    """Perform bulk actions on filtered tasks.
    
    Actions:
        - retry: Retry all matching tasks
        - cancel: Cancel all matching tasks
        - priority_boost: Change priority of matching tasks
    """
    tasks, total = TaskFilter.search_with_filters(
        db,
        status=status,
        priority=priority,
        search_query=search,
        limit=10000,
    )
    
    count = 0
    
    if action == "retry":
        for task in tasks:
            if task.status in ["FAILED", "PENDING"]:
                task.status = "PENDING"
                task.retry_count += 1
                count += 1
    
    elif action == "cancel":
        for task in tasks:
            if task.status in ["PENDING", "RUNNING"]:
                task.status = "CANCELLED"
                count += 1
    
    elif action == "priority_boost" and new_priority is not None:
        for task in tasks:
            if task.status == "PENDING":
                task.priority = new_priority
                count += 1
    
    db.commit()
    
    return {
        "action": action,
        "affected_tasks": count,
        "total_matched": total,
    }
