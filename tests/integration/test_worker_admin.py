"""Integration tests for worker admin controls."""

import pytest
from datetime import datetime
from uuid import UUID, uuid4

from src.models import Worker, Task
from src.core.worker_controller import get_worker_controller


@pytest.fixture
def worker_controller():
    """Fixture providing worker controller."""
    return get_worker_controller()


@pytest.fixture
def test_worker(db):
    """Fixture creating a test worker."""
    worker = Worker(
        hostname="test-worker-1",
        capacity=5,
        current_load=0,
        status="ACTIVE",
        last_heartbeat=datetime.utcnow(),
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker


class TestWorkerPauseResume:
    """Test worker pause and resume operations."""

    def test_pause_worker(self, db, test_worker, worker_controller):
        """Test pausing a worker."""
        result = worker_controller.pause_worker(db, str(test_worker.worker_id))
        assert result is True

        worker = db.query(Worker).filter(Worker.worker_id == test_worker.worker_id).first()
        assert worker.status == "PAUSED"

    def test_pause_nonexistent_worker(self, db, worker_controller):
        """Test pausing a worker that doesn't exist."""
        fake_id = str(uuid4())
        result = worker_controller.pause_worker(db, fake_id)
        assert result is False

    def test_resume_worker(self, db, test_worker, worker_controller):
        """Test resuming a paused worker."""
        # First pause
        worker_controller.pause_worker(db, str(test_worker.worker_id))

        # Then resume
        result = worker_controller.resume_worker(db, str(test_worker.worker_id))
        assert result is True

        worker = db.query(Worker).filter(Worker.worker_id == test_worker.worker_id).first()
        assert worker.status == "ACTIVE"

    def test_resume_nonexistent_worker(self, db, worker_controller):
        """Test resuming a worker that doesn't exist."""
        fake_id = str(uuid4())
        result = worker_controller.resume_worker(db, fake_id)
        assert result is False


class TestWorkerDrain:
    """Test worker drain operation."""

    def test_drain_worker(self, db, test_worker, worker_controller):
        """Test draining a worker."""
        result = worker_controller.drain_worker(db, str(test_worker.worker_id))
        assert result is True

        worker = db.query(Worker).filter(Worker.worker_id == test_worker.worker_id).first()
        assert worker.status == "DRAINING"

    def test_is_worker_draining(self, db, test_worker, worker_controller):
        """Test checking if worker is draining."""
        assert worker_controller.is_worker_draining(str(test_worker.worker_id)) is False

        worker_controller.drain_worker(db, str(test_worker.worker_id))
        assert worker_controller.is_worker_draining(str(test_worker.worker_id)) is True

    def test_drain_nonexistent_worker(self, db, worker_controller):
        """Test draining a worker that doesn't exist."""
        fake_id = str(uuid4())
        result = worker_controller.drain_worker(db, fake_id)
        assert result is False


class TestWorkerCapacity:
    """Test worker capacity updates."""

    def test_update_worker_capacity(self, db, test_worker, worker_controller):
        """Test updating worker capacity."""
        new_capacity = 10
        result = worker_controller.update_worker_capacity(
            db, str(test_worker.worker_id), new_capacity
        )
        assert result is True

        worker = db.query(Worker).filter(Worker.worker_id == test_worker.worker_id).first()
        assert worker.capacity == new_capacity

    def test_update_capacity_invalid_value(self, db, test_worker, worker_controller):
        """Test updating capacity with invalid value."""
        result = worker_controller.update_worker_capacity(
            db, str(test_worker.worker_id), 0
        )
        assert result is False

    def test_update_capacity_nonexistent_worker(self, db, worker_controller):
        """Test updating capacity for nonexistent worker."""
        fake_id = str(uuid4())
        result = worker_controller.update_worker_capacity(db, fake_id, 10)
        assert result is False


class TestWorkerTimeout:
    """Test worker timeout configuration."""

    def test_update_worker_timeout(self, db, test_worker, worker_controller):
        """Test updating worker timeout."""
        timeout = 300
        result = worker_controller.update_worker_timeout(
            db, str(test_worker.worker_id), timeout
        )
        assert result is True

        # Check Redis stored config
        config = worker_controller.redis.hgetall(
            f"worker:config:{test_worker.worker_id}"
        )
        assert "timeout_seconds" in config
        assert config["timeout_seconds"] == str(timeout)

    def test_update_timeout_invalid_value(self, db, test_worker, worker_controller):
        """Test updating timeout with invalid value."""
        result = worker_controller.update_worker_timeout(
            db, str(test_worker.worker_id), 0
        )
        assert result is False

    def test_update_timeout_nonexistent_worker(self, db, worker_controller):
        """Test updating timeout for nonexistent worker."""
        fake_id = str(uuid4())
        result = worker_controller.update_worker_timeout(db, fake_id, 300)
        assert result is False


class TestWorkerStatus:
    """Test worker status retrieval."""

    def test_get_worker_status(self, db, test_worker, worker_controller):
        """Test getting worker status."""
        status = worker_controller.get_worker_status(db, str(test_worker.worker_id))

        assert status is not None
        assert status["worker_id"] == str(test_worker.worker_id)
        assert status["hostname"] == "test-worker-1"
        assert status["status"] == "ACTIVE"
        assert status["capacity"] == 5
        assert status["current_load"] == 0
        assert status["current_tasks"] == 0
        assert status["is_draining"] is False

    def test_get_status_nonexistent_worker(self, db, worker_controller):
        """Test getting status for nonexistent worker."""
        fake_id = str(uuid4())
        status = worker_controller.get_worker_status(db, fake_id)
        assert status is None

    def test_get_all_workers_status(self, db, worker_controller):
        """Test getting status for all workers."""
        # Create multiple workers
        for i in range(3):
            worker = Worker(
                hostname=f"test-worker-{i}",
                capacity=5,
                current_load=0,
                status="ACTIVE",
                last_heartbeat=datetime.utcnow(),
            )
            db.add(worker)
        db.commit()

        statuses = worker_controller.get_all_workers_status(db)
        assert len(statuses) >= 3
        assert all("worker_id" in s for s in statuses)
        assert all("status" in s for s in statuses)


class TestWorkerTermination:
    """Test worker termination."""

    def test_terminate_worker(self, db, test_worker, worker_controller):
        """Test terminating a worker."""
        result = worker_controller.terminate_worker(db, str(test_worker.worker_id))
        assert result is True

        worker = db.query(Worker).filter(Worker.worker_id == test_worker.worker_id).first()
        assert worker.status == "DEAD"

    def test_terminate_nonexistent_worker(self, db, worker_controller):
        """Test terminating a worker that doesn't exist."""
        fake_id = str(uuid4())
        result = worker_controller.terminate_worker(db, fake_id)
        assert result is False


class TestWorkerTaskHistory:
    """Test worker task history."""

    def test_get_task_history_empty(self, db, test_worker, worker_controller):
        """Test getting task history for worker with no tasks."""
        history = worker_controller.get_worker_task_history(
            db, str(test_worker.worker_id)
        )
        assert isinstance(history, list)
        assert len(history) == 0

    def test_get_task_history_with_tasks(self, db, test_worker, worker_controller):
        """Test getting task history with multiple tasks."""
        # Create tasks
        for i in range(5):
            task = Task(
                task_name=f"test_task_{i}",
                task_args=[],
                task_kwargs={},
                status="COMPLETED",
                priority=1,
                worker_id=test_worker.worker_id,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                retry_count=0,
            )
            db.add(task)
        db.commit()

        history = worker_controller.get_worker_task_history(
            db, str(test_worker.worker_id), limit=10
        )
        assert len(history) == 5
        assert all("task_id" in t for t in history)
        assert all("task_name" in t for t in history)
        assert all("status" in t for t in history)
        assert all("duration_seconds" in t for t in history)

    def test_get_task_history_limit(self, db, test_worker, worker_controller):
        """Test task history respects limit."""
        # Create 10 tasks
        for i in range(10):
            task = Task(
                task_name=f"test_task_{i}",
                task_args=[],
                task_kwargs={},
                status="COMPLETED",
                priority=1,
                worker_id=test_worker.worker_id,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                retry_count=0,
            )
            db.add(task)
        db.commit()

        history = worker_controller.get_worker_task_history(
            db, str(test_worker.worker_id), limit=5
        )
        assert len(history) == 5

    def test_task_history_includes_duration(self, db, test_worker, worker_controller):
        """Test that task history includes duration calculation."""
        from datetime import timedelta

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=30)

        task = Task(
            task_name="timed_task",
            task_args=[],
            task_kwargs={},
            status="COMPLETED",
            priority=1,
            worker_id=test_worker.worker_id,
            started_at=start_time,
            completed_at=end_time,
            retry_count=0,
        )
        db.add(task)
        db.commit()

        history = worker_controller.get_worker_task_history(
            db, str(test_worker.worker_id)
        )
        assert len(history) == 1
        assert history[0]["duration_seconds"] == 30


class TestWorkerControllerIntegration:
    """Integration tests for worker controller workflows."""

    def test_pause_pause_resume_workflow(self, db, test_worker, worker_controller):
        """Test pausing and resuming workflow."""
        # Start with active worker
        assert test_worker.status == "ACTIVE"

        # Pause
        worker_controller.pause_worker(db, str(test_worker.worker_id))
        worker = db.query(Worker).filter(Worker.worker_id == test_worker.worker_id).first()
        assert worker.status == "PAUSED"

        # Pause again (should work)
        result = worker_controller.pause_worker(db, str(test_worker.worker_id))
        assert result is True

        # Resume
        worker_controller.resume_worker(db, str(test_worker.worker_id))
        worker = db.query(Worker).filter(Worker.worker_id == test_worker.worker_id).first()
        assert worker.status == "ACTIVE"

    def test_multiple_capacity_updates(self, db, test_worker, worker_controller):
        """Test multiple capacity updates."""
        capacities = [10, 20, 15, 5]

        for capacity in capacities:
            result = worker_controller.update_worker_capacity(
                db, str(test_worker.worker_id), capacity
            )
            assert result is True

            worker = db.query(Worker).filter(
                Worker.worker_id == test_worker.worker_id
            ).first()
            assert worker.capacity == capacity

    def test_drain_workflow(self, db, test_worker, worker_controller):
        """Test drain workflow with status tracking."""
        # Start active
        assert test_worker.status == "ACTIVE"
        assert worker_controller.is_worker_draining(str(test_worker.worker_id)) is False

        # Start drain
        result = worker_controller.drain_worker(db, str(test_worker.worker_id))
        assert result is True

        worker = db.query(Worker).filter(Worker.worker_id == test_worker.worker_id).first()
        assert worker.status == "DRAINING"
        assert worker_controller.is_worker_draining(str(test_worker.worker_id)) is True
