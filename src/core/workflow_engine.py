"""Workflow engine for managing task workflows and batches."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from src.core.broker import get_broker
from src.models import Task


class WorkflowEngine:
    """Manages multi-task workflows with dependencies."""

    def __init__(self, db: Session):
        self.db = db
        self.broker = get_broker()

    def create_workflow(
        self,
        workflow_name: str,
        tasks: List[Dict[str, Any]],
        dependencies: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """Create a workflow with multiple tasks and dependencies.
        
        Args:
            workflow_name: Name of the workflow
            tasks: List of task definitions with name, args, kwargs, priority
            dependencies: Dict mapping task names to list of parent task names
            
        Returns:
            Dict with workflow_id and created task_ids
        """
        workflow_id = str(uuid4())
        task_map = {}  # Map task names to task objects
        created_tasks = []

        # First pass: create all tasks
        for task_def in tasks:
            db_task = Task(
                task_name=task_def.get("task_name", "workflow_task"),
                task_args=task_def.get("task_args", []),
                task_kwargs=task_def.get("task_kwargs", {}),
                priority=task_def.get("priority", 5),
                max_retries=task_def.get("max_retries", 5),
                timeout_seconds=task_def.get("timeout_seconds", 300),
                status="PENDING",
                depends_on=[],
            )
            self.db.add(db_task)
            self.db.flush()
            
            task_name = task_def.get("name", str(db_task.task_id))
            task_map[task_name] = db_task
            created_tasks.append(db_task)

        # Second pass: wire up dependencies
        if dependencies:
            for child_name, parent_names in dependencies.items():
                if child_name in task_map:
                    child_task = task_map[child_name]
                    child_task.depends_on = [
                        str(task_map[parent_name].task_id)
                        for parent_name in parent_names
                        if parent_name in task_map
                    ]

        self.db.commit()

        # Enqueue tasks without dependencies
        for task in created_tasks:
            if not task.depends_on:
                self.broker.enqueue_task(str(task.task_id), priority=task.priority)

        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "total_tasks": len(created_tasks),
            "task_ids": [str(t.task_id) for t in created_tasks],
        }

    def get_workflow_status(self, task_ids: List[str]) -> Dict[str, Any]:
        """Get status of all tasks in a workflow.
        
        Args:
            task_ids: List of task IDs in the workflow
            
        Returns:
            Dict with workflow status summary
        """
        tasks = self.db.query(Task).filter(Task.task_id.in_(task_ids)).all()
        
        status_counts = {
            "PENDING": 0,
            "RUNNING": 0,
            "COMPLETED": 0,
            "FAILED": 0,
            "CANCELLED": 0,
        }
        
        for task in tasks:
            status_counts[task.status] = status_counts.get(task.status, 0) + 1
        
        total = len(tasks)
        completed = status_counts["COMPLETED"]
        failed = status_counts["FAILED"]
        
        if total == completed:
            overall_status = "COMPLETED"
        elif failed > 0:
            overall_status = "FAILED"
        elif status_counts["RUNNING"] > 0:
            overall_status = "RUNNING"
        else:
            overall_status = "PENDING"
        
        return {
            "status": overall_status,
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "running": status_counts["RUNNING"],
            "pending": status_counts["PENDING"],
            "progress_percent": (completed / total * 100) if total > 0 else 0,
        }

    def batch_create_tasks(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Create multiple tasks in batch.
        
        Args:
            tasks: List of task definitions
            
        Returns:
            List of created task IDs
        """
        created_ids = []
        
        for task_def in tasks:
            db_task = Task(
                task_name=task_def.get("task_name", "batch_task"),
                task_args=task_def.get("task_args", []),
                task_kwargs=task_def.get("task_kwargs", {}),
                priority=task_def.get("priority", 5),
                max_retries=task_def.get("max_retries", 5),
                timeout_seconds=task_def.get("timeout_seconds", 300),
                status="PENDING",
            )
            self.db.add(db_task)
            self.db.flush()
            
            # Enqueue immediately
            self.broker.enqueue_task(str(db_task.task_id), priority=db_task.priority)
            created_ids.append(str(db_task.task_id))
        
        self.db.commit()
        return created_ids


def get_workflow_engine(db: Session) -> WorkflowEngine:
    """Get workflow engine instance."""
    return WorkflowEngine(db)
