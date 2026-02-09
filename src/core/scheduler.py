"""Task scheduler for cron-based and delayed task execution."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from croniter import croniter
from sqlalchemy.orm import Session

from src.core.broker import get_broker
from src.db.session import SessionLocal
from src.models import Task


class TaskScheduler:
    """
    Scheduler for handling delayed and recurring tasks.
    
    Features:
    - Cron-based recurring tasks
    - One-time scheduled tasks
    - Automatic task enqueueing when due
    """
    
    def __init__(self, poll_interval: int = 60):
        """
        Initialize the task scheduler.
        
        Args:
            poll_interval: How often to check for due tasks (seconds)
        """
        self.poll_interval = poll_interval
        self.running = False
        self.broker = get_broker()
    
    async def start(self):
        """Start the scheduler loop."""
        self.running = True
        while self.running:
            try:
                await self._check_and_enqueue_due_tasks()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                print(f"Error in scheduler loop: {e}")
                await asyncio.sleep(self.poll_interval)
    
    async def stop(self):
        """Stop the scheduler loop."""
        self.running = False
    
    def _check_and_enqueue_due_tasks(self):
        """
        Check for tasks that are due to be executed and enqueue them.
        
        Handles:
        - One-time scheduled tasks (scheduled_at in the past)
        - Recurring tasks (cron_expression specified)
        """
        db: Session = SessionLocal()
        try:
            now = datetime.utcnow()
            
            # Find tasks that are scheduled and due
            due_tasks = db.query(Task).filter(
                Task.status == "PENDING",
                Task.scheduled_at <= now
            ).all()
            
            for task in due_tasks:
                # Enqueue the task
                task.status = "QUEUED"
                task.started_at = now
                
                # Enqueue in Redis
                self.broker.enqueue_task(task)
                
                # If it's a recurring task, schedule the next occurrence
                if task.is_recurring and task.cron_expression:
                    next_run = self._calculate_next_run(task.cron_expression, now)
                    if next_run:
                        # Create a new task for the next occurrence
                        new_task = Task(
                            task_name=task.task_name,
                            task_args=task.task_args,
                            task_kwargs=task.task_kwargs,
                            priority=task.priority,
                            status="PENDING",
                            max_retries=task.max_retries,
                            timeout_seconds=task.timeout_seconds,
                            scheduled_at=next_run,
                            cron_expression=task.cron_expression,
                            is_recurring=True,
                            created_by=task.created_by
                        )
                        db.add(new_task)
                
                db.commit()
            
            if due_tasks:
                print(f"Enqueued {len(due_tasks)} due tasks")
        
        except Exception as e:
            db.rollback()
            print(f"Error checking due tasks: {e}")
            raise
        finally:
            db.close()
    
    def _calculate_next_run(self, cron_expression: str, base_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        Calculate the next run time based on a cron expression.
        
        Args:
            cron_expression: Cron expression (e.g., "0 */6 * * *")
            base_time: Base time to calculate from (defaults to now)
        
        Returns:
            Next run datetime or None if invalid
        """
        try:
            if not base_time:
                base_time = datetime.utcnow()
            
            cron = croniter(cron_expression, base_time)
            return cron.get_next(datetime)
        except Exception as e:
            print(f"Error parsing cron expression '{cron_expression}': {e}")
            return None
    
    def validate_cron_expression(self, cron_expression: str) -> bool:
        """
        Validate a cron expression.
        
        Args:
            cron_expression: Cron expression to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Standard cron uses 5 fields, reject 6-field expressions
            fields = cron_expression.strip().split()
            if len(fields) != 5:
                return False
            croniter(cron_expression)
            return True
        except Exception:
            return False
    
    def get_next_run_time(self, cron_expression: str, base_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        Get the next run time for a cron expression.
        
        Args:
            cron_expression: Cron expression
            base_time: Base time (defaults to now)
        
        Returns:
            Next run datetime or None
        """
        return self._calculate_next_run(cron_expression, base_time)


# Global scheduler instance
_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler


def start_scheduler_background():
    """Start the scheduler in the background."""
    scheduler = get_scheduler()
    asyncio.create_task(scheduler.start())
