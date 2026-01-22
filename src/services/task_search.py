"""Task search and filtering service."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from src.models import Task


class TaskFilterOperator(str, Enum):
    """Filter operators for advanced search."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    IN = "in"
    NOT_IN = "nin"
    CONTAINS = "contains"
    STARTS_WITH = "startswith"
    ENDS_WITH = "endswith"


class TaskFilter:
    """Advanced task filtering and search."""

    @staticmethod
    def build_filters(
        status: Optional[str] = None,
        priority: Optional[int] = None,
        task_name: Optional[str] = None,
        worker_id: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        completed_after: Optional[datetime] = None,
        completed_before: Optional[datetime] = None,
        has_errors: Optional[bool] = None,
        retry_count_min: Optional[int] = None,
        retry_count_max: Optional[int] = None,
    ) -> List:
        """Build SQL filter conditions from parameters.
        
        Args:
            status: Task status filter
            priority: Task priority filter
            task_name: Task name (exact match)
            worker_id: Worker ID filter
            created_after: Only tasks created after this timestamp
            created_before: Only tasks created before this timestamp
            completed_after: Only tasks completed after this timestamp
            completed_before: Only tasks completed before this timestamp
            has_errors: Filter by error presence
            retry_count_min: Minimum retry count
            retry_count_max: Maximum retry count
            
        Returns:
            List of SQLAlchemy filter conditions
        """
        filters = []
        
        if status:
            filters.append(Task.status == status)
        
        if priority is not None:
            filters.append(Task.priority == priority)
        
        if task_name:
            filters.append(Task.task_name == task_name)
        
        if worker_id:
            filters.append(Task.worker_id == worker_id)
        
        if created_after:
            filters.append(Task.created_at >= created_after)
        
        if created_before:
            filters.append(Task.created_at <= created_before)
        
        if completed_after:
            filters.append(Task.completed_at >= completed_after)
        
        if completed_before:
            filters.append(Task.completed_at <= completed_before)
        
        if has_errors is not None:
            if has_errors:
                filters.append(Task.error_message.isnot(None))
            else:
                filters.append(Task.error_message.is_(None))
        
        if retry_count_min is not None:
            filters.append(Task.retry_count >= retry_count_min)
        
        if retry_count_max is not None:
            filters.append(Task.retry_count <= retry_count_max)
        
        return filters

    @staticmethod
    def full_text_search(
        db: Session,
        query: str,
        search_fields: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Task]:
        """Perform full-text search across task fields.
        
        Args:
            db: Database session
            query: Search query string
            search_fields: Fields to search in (default: task_name, task_args, task_kwargs)
            limit: Maximum results to return
            
        Returns:
            List of matching tasks
        """
        if not search_fields:
            search_fields = ["task_name", "task_args", "task_kwargs"]
        
        conditions = []
        search_term = f"%{query}%"
        
        if "task_name" in search_fields:
            conditions.append(Task.task_name.ilike(search_term))
        
        if "task_args" in search_fields:
            # Search in JSON fields (may not work on all databases)
            try:
                conditions.append(
                    func.cast(Task.task_args, str).ilike(search_term)
                )
            except Exception:
                pass
        
        if "task_kwargs" in search_fields:
            try:
                conditions.append(
                    func.cast(Task.task_kwargs, str).ilike(search_term)
                )
            except Exception:
                pass
        
        if not conditions:
            return []
        
        return (
            db.query(Task)
            .filter(or_(*conditions))
            .limit(limit)
            .all()
        )

    @staticmethod
    def search_with_filters(
        db: Session,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        task_name: Optional[str] = None,
        worker_id: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> Tuple[List[Task], int]:
        """Search tasks with combined filters and full-text search.
        
        Args:
            db: Database session
            status: Status filter
            priority: Priority filter
            task_name: Task name filter
            worker_id: Worker ID filter
            created_after: Created after filter
            created_before: Created before filter
            search_query: Full-text search query
            limit: Number of results to return
            offset: Pagination offset
            order_by: Field to order by
            order_desc: Sort descending
            
        Returns:
            Tuple of (tasks, total_count)
        """
        filters = TaskFilter.build_filters(
            status=status,
            priority=priority,
            task_name=task_name,
            worker_id=worker_id,
            created_after=created_after,
            created_before=created_before,
        )
        
        query = db.query(Task)
        
        # Apply basic filters
        if filters:
            query = query.filter(and_(*filters))
        
        # Apply full-text search if provided
        if search_query:
            search_results = TaskFilter.full_text_search(
                db, search_query, limit=limit * 10
            )
            search_ids = {t.task_id for t in search_results}
            if search_ids:
                query = query.filter(Task.task_id.in_(search_ids))
            else:
                return [], 0
        
        # Get total count
        total_count = query.count()
        
        # Apply ordering
        if order_by == "created_at":
            if order_desc:
                query = query.order_by(Task.created_at.desc())
            else:
                query = query.order_by(Task.created_at.asc())
        elif order_by == "priority":
            if order_desc:
                query = query.order_by(Task.priority.desc())
            else:
                query = query.order_by(Task.priority.asc())
        elif order_by == "status":
            if order_desc:
                query = query.order_by(Task.status.desc())
            else:
                query = query.order_by(Task.status.asc())
        
        # Apply pagination
        tasks = query.offset(offset).limit(limit).all()
        
        return tasks, total_count

    @staticmethod
    def get_filter_presets() -> Dict[str, Dict]:
        """Get predefined filter presets for common queries.
        
        Returns:
            Dictionary of preset names and their filter configurations
        """
        now = datetime.utcnow()
        
        return {
            "failed_today": {
                "status": "FAILED",
                "created_after": now - timedelta(days=1),
            },
            "high_priority_pending": {
                "status": "PENDING",
                "priority": 8,
            },
            "stuck_tasks": {
                "status": "RUNNING",
                "created_before": now - timedelta(hours=1),
            },
            "recently_completed": {
                "status": "COMPLETED",
                "completed_after": now - timedelta(hours=1),
            },
            "never_retried": {
                "retry_count_min": 0,
                "retry_count_max": 0,
            },
            "many_retries": {
                "retry_count_min": 3,
            },
        }

    @staticmethod
    def export_to_csv(tasks: List[Task]) -> str:
        """Export tasks to CSV format.
        
        Args:
            tasks: List of tasks to export
            
        Returns:
            CSV string
        """
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "task_id",
                "task_name",
                "status",
                "priority",
                "created_at",
                "started_at",
                "completed_at",
                "worker_id",
                "retry_count",
                "error_message",
            ],
        )
        
        writer.writeheader()
        
        for task in tasks:
            writer.writerow({
                "task_id": str(task.task_id),
                "task_name": task.task_name,
                "status": task.status,
                "priority": task.priority,
                "created_at": task.created_at.isoformat() if task.created_at else "",
                "started_at": task.started_at.isoformat() if task.started_at else "",
                "completed_at": task.completed_at.isoformat() if task.completed_at else "",
                "worker_id": str(task.worker_id) if task.worker_id else "",
                "retry_count": task.retry_count,
                "error_message": task.error_message or "",
            })
        
        return output.getvalue()


class FilterPreset:
    """Named filter presets for quick access."""
    
    def __init__(self, db: Session, preset_name: str):
        """Initialize filter preset.
        
        Args:
            db: Database session
            preset_name: Name of the preset
        """
        self.db = db
        self.preset_name = preset_name
        self.presets = TaskFilter.get_filter_presets()
    
    def execute(self, limit: int = 100, offset: int = 0) -> Tuple[List[Task], int]:
        """Execute the preset filter.
        
        Args:
            limit: Number of results
            offset: Pagination offset
            
        Returns:
            Tuple of (tasks, total_count)
        """
        if self.preset_name not in self.presets:
            return [], 0
        
        preset_config = self.presets[self.preset_name]
        
        return TaskFilter.search_with_filters(
            self.db,
            limit=limit,
            offset=offset,
            **preset_config,
        )
