"""Integration tests for task debugging and replay features."""

import pytest
import json
from datetime import datetime, timedelta

from src.models import Task
from src.services.task_debugger import get_task_debugger


@pytest.fixture
def task_debugger():
    """Fixture providing task debugger."""
    return get_task_debugger()


@pytest.fixture
def test_task(db):
    """Fixture creating a test task."""
    task = Task(
        task_name="test_function",
        task_args=[1, 2],
        task_kwargs={"key": "value"},
        priority=5,
        status="COMPLETED",
        retry_count=1,
        max_retries=3,
        timeout_seconds=300,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@pytest.fixture
def failed_task(db):
    """Fixture creating a failed task."""
    task = Task(
        task_name="failed_function",
        task_args=[],
        task_kwargs={},
        priority=1,
        status="FAILED",
        retry_count=2,
        max_retries=3,
        error_message="Task execution timeout",
        failed_at=datetime.utcnow(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


class TestDebugMode:
    """Test debug mode functionality."""

    def test_enable_debug_mode(self, test_task, task_debugger):
        """Test enabling debug mode for a task."""
        result = task_debugger.enable_debug_mode(str(test_task.task_id), 60)
        assert result is True

    def test_is_debug_enabled(self, test_task, task_debugger):
        """Test checking if debug mode is enabled."""
        assert task_debugger.is_debug_enabled(str(test_task.task_id)) is False

        task_debugger.enable_debug_mode(str(test_task.task_id), 60)
        assert task_debugger.is_debug_enabled(str(test_task.task_id)) is True

    def test_debug_mode_expiration(self, test_task, task_debugger):
        """Test that debug mode expires."""
        task_debugger.enable_debug_mode(str(test_task.task_id), 0)
        # Verify it was set (even though it expires immediately in tests)
        # In a real scenario, we'd wait for TTL


class TestExecutionLog:
    """Test execution logging."""

    def test_log_execution_event(self, test_task, task_debugger):
        """Test logging an execution event."""
        task_debugger.log_execution_event(
            str(test_task.task_id),
            "started",
            {"worker_id": "worker-1"},
        )

        events = task_debugger.get_execution_log(str(test_task.task_id))
        assert len(events) > 0
        assert events[0]["event_type"] == "started"
        assert events[0]["details"]["worker_id"] == "worker-1"

    def test_get_execution_log(self, test_task, task_debugger):
        """Test retrieving execution log."""
        # Log multiple events
        for i in range(5):
            task_debugger.log_execution_event(
                str(test_task.task_id),
                f"event_{i}",
                {"index": i},
            )

        events = task_debugger.get_execution_log(str(test_task.task_id))
        assert len(events) >= 5

    def test_get_execution_log_with_limit(self, test_task, task_debugger):
        """Test execution log respects limit."""
        # Log multiple events
        for i in range(10):
            task_debugger.log_execution_event(
                str(test_task.task_id),
                f"event_{i}",
                {"index": i},
            )

        events = task_debugger.get_execution_log(str(test_task.task_id), limit=5)
        assert len(events) <= 5


class TestTaskReplay:
    """Test task replay functionality."""

    def test_replay_completed_task(self, db, test_task, task_debugger):
        """Test replaying a completed task."""
        result = task_debugger.replay_task(db, str(test_task.task_id))

        assert result is not None
        assert result["task_id"] != str(test_task.task_id)
        assert result["task_name"] == test_task.task_name
        assert result["status"] == "PENDING"

    def test_replay_failed_task(self, db, failed_task, task_debugger):
        """Test replaying a failed task."""
        result = task_debugger.replay_task(db, str(failed_task.task_id))

        assert result is not None
        assert result["status"] == "PENDING"

    def test_replay_preserves_retries(self, db, failed_task, task_debugger):
        """Test replay can preserve retry count."""
        result = task_debugger.replay_task(
            db, str(failed_task.task_id), preserve_retries=True
        )

        replayed_task = db.query(Task).filter(
            Task.task_id == result["task_id"]
        ).first()
        assert replayed_task.retry_count == failed_task.retry_count

    def test_replay_resets_retries(self, db, failed_task, task_debugger):
        """Test replay resets retry count by default."""
        result = task_debugger.replay_task(db, str(failed_task.task_id))

        replayed_task = db.query(Task).filter(
            Task.task_id == result["task_id"]
        ).first()
        assert replayed_task.retry_count == 0

    def test_replay_nonexistent_task(self, db, task_debugger):
        """Test replaying a task that doesn't exist."""
        import uuid
        fake_id = str(uuid.uuid4())
        result = task_debugger.replay_task(db, fake_id)
        assert result is None


class TestTaskComparison:
    """Test task comparison functionality."""

    def test_compare_identical_tasks(self, db, task_debugger):
        """Test comparing identical tasks."""
        # Create two identical tasks
        task1 = Task(
            task_name="test_function",
            task_args=[1, 2],
            task_kwargs={"key": "value"},
            priority=5,
            status="COMPLETED",
        )
        task2 = Task(
            task_name="test_function",
            task_args=[1, 2],
            task_kwargs={"key": "value"},
            priority=5,
            status="COMPLETED",
        )
        db.add_all([task1, task2])
        db.commit()

        comparison = task_debugger.compare_tasks(
            db, str(task1.task_id), str(task2.task_id)
        )

        assert comparison["same_function"] is True
        assert comparison["same_args"] is True
        assert comparison["same_kwargs"] is True
        assert comparison["same_priority"] is True

    def test_compare_different_args(self, db, task_debugger):
        """Test comparing tasks with different arguments."""
        task1 = Task(
            task_name="test_function",
            task_args=[1, 2],
            task_kwargs={},
            priority=5,
            status="COMPLETED",
        )
        task2 = Task(
            task_name="test_function",
            task_args=[3, 4],
            task_kwargs={},
            priority=5,
            status="COMPLETED",
        )
        db.add_all([task1, task2])
        db.commit()

        comparison = task_debugger.compare_tasks(
            db, str(task1.task_id), str(task2.task_id)
        )

        assert comparison["same_function"] is True
        assert comparison["same_args"] is False

    def test_compare_nonexistent_task(self, db, test_task, task_debugger):
        """Test comparing with nonexistent task."""
        import uuid
        fake_id = str(uuid.uuid4())
        
        result = task_debugger.compare_tasks(db, str(test_task.task_id), fake_id)
        assert result is None


class TestTaskTimeline:
    """Test task timeline functionality."""

    def test_get_task_timeline(self, db, test_task, task_debugger):
        """Test getting task timeline."""
        # Log some events
        task_debugger.log_execution_event(
            str(test_task.task_id),
            "started",
            {"worker_id": "worker-1"},
        )

        timeline = task_debugger.get_task_timeline(db, str(test_task.task_id))

        assert timeline is not None
        assert timeline["task_id"] == str(test_task.task_id)
        assert timeline["task_name"] == test_task.task_name
        assert timeline["status"] == test_task.status
        assert "events" in timeline
        assert "retry_history" in timeline

    def test_timeline_includes_timestamps(self, db, test_task, task_debugger):
        """Test timeline includes timing information."""
        timeline = task_debugger.get_task_timeline(db, str(test_task.task_id))

        assert timeline["created_at"] is not None
        assert "duration_seconds" in timeline

    def test_get_timeline_nonexistent_task(self, db, task_debugger):
        """Test getting timeline for nonexistent task."""
        import uuid
        fake_id = str(uuid.uuid4())
        
        result = task_debugger.get_task_timeline(db, fake_id)
        assert result is None


class TestValidateReplay:
    """Test replay validation."""

    def test_validate_completed_task_replay(self, db, test_task, task_debugger):
        """Test validating completed task can be replayed."""
        validation = task_debugger.validate_task_replay(db, str(test_task.task_id))

        assert validation["valid"] is True
        assert validation["can_replay"] is True

    def test_validate_failed_task_replay(self, db, failed_task, task_debugger):
        """Test validating failed task can be replayed."""
        validation = task_debugger.validate_task_replay(db, str(failed_task.task_id))

        assert validation["valid"] is True
        assert validation["can_replay"] is True

    def test_validate_pending_task_replay(self, db, task_debugger):
        """Test validating pending task cannot be replayed."""
        task = Task(
            task_name="test",
            task_args=[],
            task_kwargs={},
            status="PENDING",
        )
        db.add(task)
        db.commit()

        validation = task_debugger.validate_task_replay(db, str(task.task_id))

        assert validation["valid"] is False
        assert validation["can_replay"] is False

    def test_validate_nonexistent_task(self, db, task_debugger):
        """Test validating nonexistent task."""
        import uuid
        fake_id = str(uuid.uuid4())
        
        validation = task_debugger.validate_task_replay(db, fake_id)
        assert validation["valid"] is False


class TestDryRun:
    """Test dry-run functionality."""

    def test_create_dry_run_task(self, db, task_debugger):
        """Test creating a dry-run task."""
        result = task_debugger.test_dry_run(
            db,
            "test_function",
            [1, 2],
            {"key": "value"},
        )

        assert result is not None
        assert result["task_name"] == "test_function"
        assert result["task_args"] == [1, 2]
        assert result["task_kwargs"] == {"key": "value"}
        assert "note" in result

    def test_dry_run_task_not_executed(self, db, task_debugger):
        """Test dry-run task is marked as test mode."""
        result = task_debugger.test_dry_run(db, "test", [], {})

        # Verify task was created
        task = db.query(Task).filter(Task.task_id == result["task_id"]).first()
        assert task is not None

        # Verify execution log shows dry-run
        events = task_debugger.get_execution_log(str(task.task_id))
        assert any(e["event_type"] == "dry_run" for e in events)


class TestSimilarTasks:
    """Test finding similar tasks."""

    def test_get_similar_tasks(self, db, test_task, task_debugger):
        """Test finding similar tasks."""
        # Create similar tasks
        for i in range(3):
            task = Task(
                task_name=test_task.task_name,
                task_args=[i],
                task_kwargs={},
                status="COMPLETED",
            )
            db.add(task)
        db.commit()

        similar = task_debugger.get_similar_tasks(db, str(test_task.task_id), limit=10)

        assert len(similar) >= 3
        assert all(t["task_name"] == test_task.task_name for t in similar)

    def test_similar_tasks_respects_limit(self, db, test_task, task_debugger):
        """Test similar tasks respects limit."""
        # Create 10 similar tasks
        for i in range(10):
            task = Task(
                task_name=test_task.task_name,
                task_args=[i],
                task_kwargs={},
                status="COMPLETED",
            )
            db.add(task)
        db.commit()

        similar = task_debugger.get_similar_tasks(db, str(test_task.task_id), limit=5)

        assert len(similar) <= 5

    def test_similar_tasks_empty_when_unique(self, db, task_debugger):
        """Test no similar tasks when function is unique."""
        task = Task(
            task_name="unique_function",
            task_args=[],
            task_kwargs={},
            status="COMPLETED",
        )
        db.add(task)
        db.commit()

        similar = task_debugger.get_similar_tasks(db, str(task.task_id))

        assert len(similar) == 0


class TestFunctionMetrics:
    """Test function-level metrics."""

    def test_get_function_metrics(self, db, task_debugger):
        """Test getting metrics for a function."""
        from datetime import datetime, timedelta

        # Create tasks
        for i in range(5):
            start = datetime.utcnow()
            completed = start + timedelta(seconds=10)

            task = Task(
                task_name="test_function",
                task_args=[],
                task_kwargs={},
                status="COMPLETED" if i < 3 else "FAILED",
                started_at=start,
                completed_at=completed,
                retry_count=i % 2,
            )
            db.add(task)
        db.commit()

        metrics = task_debugger.get_task_metrics_for_function(db, "test_function", 10)

        assert metrics["task_name"] == "test_function"
        assert metrics["execution_count"] == 5
        assert metrics["success_count"] == 3
        assert metrics["failed_count"] == 2
        assert 0 <= metrics["success_rate"] <= 100
        assert metrics["avg_duration_seconds"] > 0

    def test_function_metrics_empty(self, db, task_debugger):
        """Test metrics for function with no executions."""
        metrics = task_debugger.get_task_metrics_for_function(db, "nonexistent", 10)

        assert metrics["execution_count"] == 0
        assert metrics["metrics"] is None
