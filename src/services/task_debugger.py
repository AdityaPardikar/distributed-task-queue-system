"""Task replay and debugging tools."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from src.cache.client import RedisClient, get_redis_client
from src.models import Task
from src.core.broker import get_broker
import json


class TaskDebugger:
    """Tools for debugging and replaying tasks."""

    EXECUTION_LOG_KEY = "task:execution:log"
    DEBUG_FLAG_KEY = "task:debug"

    def __init__(self, redis_client: Optional[RedisClient] = None):
        """Initialize task debugger."""
        self.redis = redis_client or get_redis_client()
        self.broker = get_broker()

    def enable_debug_mode(self, task_id: str, duration_minutes: int = 60) -> bool:
        """Enable verbose logging for a specific task.
        
        Args:
            task_id: Task ID
            duration_minutes: How long to keep debug mode enabled
            
        Returns:
            True if debug mode enabled
        """
        self.redis.set(
            f"{self.DEBUG_FLAG_KEY}:{task_id}",
            "1",
            ttl=duration_minutes * 60,
        )
        return True

    def is_debug_enabled(self, task_id: str) -> bool:
        """Check if debug mode is enabled for task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if debug mode is enabled
        """
        return self.redis.get(f"{self.DEBUG_FLAG_KEY}:{task_id}") is not None

    def log_execution_event(
        self,
        task_id: str,
        event_type: str,
        details: Dict[str, Any],
    ) -> None:
        """Log an execution event for debugging.
        
        Args:
            task_id: Task ID
            event_type: Type of event (started, progress, completed, failed, etc)
            details: Event details dictionary
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
        }

        log_key = f"{self.EXECUTION_LOG_KEY}:{task_id}"
        self.redis.rpush(log_key, json.dumps(event))
        self.redis.expire(log_key, 86400 * 7)  # Keep for 7 days

    def get_execution_log(
        self,
        task_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve execution log for a task.
        
        Args:
            task_id: Task ID
            limit: Maximum number of events to return
            
        Returns:
            List of execution events
        """
        log_key = f"{self.EXECUTION_LOG_KEY}:{task_id}"

        if limit:
            events = self.redis.lrange(log_key, -limit, -1)
        else:
            events = self.redis.lrange(log_key, 0, -1)

        return [json.loads(e) for e in (events or [])]

    def replay_task(
        self,
        db: Session,
        task_id: str,
        preserve_retries: bool = False,
    ) -> Optional[Dict]:
        """Replay a task using original arguments.
        
        Creates a new task with the same arguments as the original.
        
        Args:
            db: Database session
            task_id: Original task ID
            preserve_retries: Whether to preserve retry count (default: reset to 0)
            
        Returns:
            New task dictionary or None if original not found
        """
        original_task = db.query(Task).filter(Task.task_id == task_id).first()

        if not original_task:
            return None

        # Create new task with same arguments
        new_task = Task(
            task_name=original_task.task_name,
            task_args=original_task.task_args,
            task_kwargs=original_task.task_kwargs,
            priority=original_task.priority,
            queue_name=original_task.queue_name,
            status="PENDING",
            retry_count=0 if not preserve_retries else original_task.retry_count,
            max_retries=original_task.max_retries,
            timeout_seconds=original_task.timeout_seconds,
        )

        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        # Log replay event
        self.log_execution_event(
            str(new_task.task_id),
            "replayed",
            {
                "original_task_id": str(original_task.task_id),
                "original_status": original_task.status,
            },
        )

        return {
            "task_id": str(new_task.task_id),
            "task_name": new_task.task_name,
            "status": new_task.status,
            "created_at": new_task.created_at.isoformat() if new_task.created_at else None,
        }

    def compare_tasks(
        self,
        db: Session,
        task_id1: str,
        task_id2: str,
    ) -> Optional[Dict]:
        """Compare two tasks to identify differences.
        
        Args:
            db: Database session
            task_id1: First task ID
            task_id2: Second task ID
            
        Returns:
            Comparison dictionary or None if either task not found
        """
        task1 = db.query(Task).filter(Task.task_id == task_id1).first()
        task2 = db.query(Task).filter(Task.task_id == task_id2).first()

        if not task1 or not task2:
            return None

        comparison = {
            "task1_id": str(task1.task_id),
            "task2_id": str(task2.task_id),
            "same_function": task1.task_name == task2.task_name,
            "same_args": task1.task_args == task2.task_args,
            "same_kwargs": task1.task_kwargs == task2.task_kwargs,
            "same_priority": task1.priority == task2.priority,
            "status_comparison": {
                "task1": task1.status,
                "task2": task2.status,
            },
            "timing": {
                "task1_duration": (
                    (task1.completed_at - task1.started_at).total_seconds()
                    if task1.completed_at and task1.started_at
                    else None
                ),
                "task2_duration": (
                    (task2.completed_at - task2.started_at).total_seconds()
                    if task2.completed_at and task2.started_at
                    else None
                ),
            },
            "retry_analysis": {
                "task1_retries": task1.retry_count,
                "task2_retries": task2.retry_count,
            },
            "error_comparison": {
                "task1_error": task1.error_message,
                "task2_error": task2.error_message,
            },
            "arguments": {
                "task1_args": task1.task_args,
                "task1_kwargs": task1.task_kwargs,
                "task2_args": task2.task_args,
                "task2_kwargs": task2.task_kwargs,
            },
        }

        return comparison

    def get_task_timeline(
        self,
        db: Session,
        task_id: str,
    ) -> Optional[Dict]:
        """Get timeline/execution trace for a task.
        
        Args:
            db: Database session
            task_id: Task ID
            
        Returns:
            Timeline dictionary or None
        """
        task = db.query(Task).filter(Task.task_id == task_id).first()

        if not task:
            return None

        # Get execution log events
        events = self.get_execution_log(str(task_id))

        timeline = {
            "task_id": str(task.task_id),
            "task_name": task.task_name,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "failed_at": task.failed_at.isoformat() if task.failed_at else None,
            "duration_seconds": (
                (task.completed_at - task.created_at).total_seconds()
                if task.completed_at and task.created_at
                else None
            ),
            "events": events,
            "retry_history": [
                {
                    "retry_count": task.retry_count,
                    "error": task.error_message,
                    "worker_id": str(task.worker_id) if task.worker_id else None,
                }
            ],
        }

        return timeline

    def validate_task_replay(
        self,
        db: Session,
        task_id: str,
    ) -> Dict:
        """Validate if a task can be safely replayed.
        
        Args:
            db: Database session
            task_id: Task ID
            
        Returns:
            Validation result dictionary
        """
        task = db.query(Task).filter(Task.task_id == task_id).first()

        if not task:
            return {"valid": False, "reason": "Task not found"}

        # Check if task is in a replayable state
        replayable_statuses = ["FAILED", "COMPLETED", "CANCELLED"]
        can_replay = task.status in replayable_statuses

        # Check if task has valid arguments
        has_valid_args = task.task_args is not None or task.task_kwargs is not None

        # Check retry limits
        can_retry = task.retry_count < task.max_retries

        validation = {
            "valid": can_replay and has_valid_args,
            "can_replay": can_replay,
            "status": task.status,
            "has_valid_args": has_valid_args,
            "can_retry": can_retry,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "reasons": [],
        }

        if not can_replay:
            validation["reasons"].append(f"Task status '{task.status}' not in replayable states")

        if not has_valid_args:
            validation["reasons"].append("Task has no valid arguments")

        return validation

    def test_dry_run(
        self,
        db: Session,
        task_name: str,
        task_args: list,
        task_kwargs: dict,
    ) -> Dict:
        """Create a test/dry-run task without execution.
        
        Args:
            db: Database session
            task_name: Task function name
            task_args: Task arguments
            task_kwargs: Task keyword arguments
            
        Returns:
            Dry-run task dictionary
        """
        test_task = Task(
            task_name=task_name,
            task_args=task_args,
            task_kwargs=task_kwargs,
            priority=1,
            status="PENDING",  # Will not be processed
            retry_count=0,
            max_retries=0,
            timeout_seconds=300,
        )

        db.add(test_task)
        db.commit()
        db.refresh(test_task)

        # Mark as test/dry-run
        self.log_execution_event(
            str(test_task.task_id),
            "dry_run",
            {"test_mode": True, "will_not_execute": True},
        )

        return {
            "task_id": str(test_task.task_id),
            "task_name": test_task.task_name,
            "task_args": test_task.task_args,
            "task_kwargs": test_task.task_kwargs,
            "status": test_task.status,
            "created_at": test_task.created_at.isoformat() if test_task.created_at else None,
            "note": "This is a dry-run task and will not be executed",
        }

    def get_similar_tasks(
        self,
        db: Session,
        task_id: str,
        limit: int = 10,
    ) -> List[Dict]:
        """Find similar tasks (same function, similar arguments).
        
        Args:
            db: Database session
            task_id: Reference task ID
            limit: Maximum number of similar tasks
            
        Returns:
            List of similar tasks
        """
        reference = db.query(Task).filter(Task.task_id == task_id).first()

        if not reference:
            return []

        # Find tasks with same function name
        similar = (
            db.query(Task)
            .filter(
                Task.task_name == reference.task_name,
                Task.task_id != task_id,
            )
            .order_by(Task.completed_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "task_id": str(t.task_id),
                "task_name": t.task_name,
                "status": t.status,
                "priority": t.priority,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "error_message": t.error_message,
                "args_match": t.task_args == reference.task_args,
                "kwargs_match": t.task_kwargs == reference.task_kwargs,
            }
            for t in similar
        ]

    def get_task_metrics_for_function(
        self,
        db: Session,
        task_name: str,
        limit: int = 100,
    ) -> Dict:
        """Get aggregate metrics for all executions of a function.
        
        Args:
            db: Database session
            task_name: Task function name
            limit: Maximum tasks to analyze
            
        Returns:
            Metrics dictionary
        """
        tasks = (
            db.query(Task)
            .filter(Task.task_name == task_name)
            .order_by(Task.completed_at.desc())
            .limit(limit)
            .all()
        )

        if not tasks:
            return {
                "task_name": task_name,
                "execution_count": 0,
                "metrics": None,
            }

        durations = []
        success_count = 0
        failed_count = 0
        retry_counts = []

        for task in tasks:
            if task.status == "COMPLETED":
                success_count += 1

            if task.status == "FAILED":
                failed_count += 1

            if task.completed_at and task.started_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                durations.append(duration)

            retry_counts.append(task.retry_count)

        metrics = {
            "task_name": task_name,
            "execution_count": len(tasks),
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": (success_count / len(tasks) * 100) if tasks else 0,
            "avg_duration_seconds": sum(durations) / len(durations) if durations else 0,
            "min_duration_seconds": min(durations) if durations else 0,
            "max_duration_seconds": max(durations) if durations else 0,
            "avg_retries": sum(retry_counts) / len(retry_counts) if retry_counts else 0,
            "max_retries_needed": max(retry_counts) if retry_counts else 0,
        }

        return metrics


# Global instance
_debugger: Optional[TaskDebugger] = None


def get_task_debugger() -> TaskDebugger:
    """Get global task debugger instance."""
    global _debugger
    if _debugger is None:
        _debugger = TaskDebugger()
    return _debugger
