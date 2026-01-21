"""Dependency resolver for task chains."""

from typing import List, Optional, Set

from sqlalchemy.orm import Session

from src.models import Task


class DependencyResolver:
    """Resolves task dependencies and triggers child tasks when dependencies complete."""

    def __init__(self, db: Session):
        self.db = db

    def check_dependencies_complete(self, task_id: str) -> tuple[bool, List[str]]:
        """Check if all dependencies for a task are complete.
        
        Returns:
            Tuple of (all_complete, failed_dependencies)
        """
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if not task or not task.depends_on:
            return True, []

        failed_deps = []
        for dep_id in task.depends_on:
            dep_task = self.db.query(Task).filter(Task.task_id == dep_id).first()
            if not dep_task:
                failed_deps.append(dep_id)
            elif dep_task.status == "FAILED":
                failed_deps.append(dep_id)
            elif dep_task.status != "COMPLETED":
                return False, []

        return len(failed_deps) == 0, failed_deps

    def get_ready_children(self, parent_id: str) -> List[Task]:
        """Get child tasks that are ready to run after parent completes.
        
        Args:
            parent_id: ID of completed parent task
            
        Returns:
            List of child tasks ready to be enqueued
        """
        # Find all tasks that depend on this parent
        all_tasks = self.db.query(Task).filter(Task.status == "PENDING").all()
        ready_children = []

        for task in all_tasks:
            if task.depends_on and str(parent_id) in task.depends_on:
                # Check if all dependencies are complete
                all_complete, failed = self.check_dependencies_complete(str(task.task_id))
                if all_complete:
                    ready_children.append(task)
                elif failed:
                    # Mark task as failed if any dependency failed
                    task.status = "FAILED"
                    task.error_message = f"Dependencies failed: {', '.join(failed)}"
                    self.db.commit()

        return ready_children

    def mark_children_as_failed(self, parent_id: str) -> int:
        """Mark all dependent tasks as failed when parent fails.
        
        Returns:
            Number of children marked as failed
        """
        all_tasks = self.db.query(Task).filter(Task.status == "PENDING").all()
        failed_count = 0

        for task in all_tasks:
            if task.depends_on and str(parent_id) in task.depends_on:
                task.status = "FAILED"
                task.error_message = f"Parent task {parent_id} failed"
                failed_count += 1

        if failed_count > 0:
            self.db.commit()

        return failed_count

    def has_circular_dependency(self, task_id: str, visited: Optional[Set[str]] = None) -> bool:
        """Check if adding dependencies would create a circular dependency.
        
        Args:
            task_id: Task to check
            visited: Set of already visited task IDs
            
        Returns:
            True if circular dependency detected
        """
        if visited is None:
            visited = set()

        if task_id in visited:
            return True

        visited.add(task_id)

        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if not task or not task.depends_on:
            return False

        for dep_id in task.depends_on:
            if self.has_circular_dependency(dep_id, visited.copy()):
                return True

        return False


def get_dependency_resolver(db: Session) -> DependencyResolver:
    """Get a dependency resolver instance."""
    return DependencyResolver(db)
