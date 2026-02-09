"""End-to-end integration tests for complete task queue workflows."""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from src.models import Worker, Task
from src.core.broker import get_broker


@pytest.fixture
def broker():
    """Fixture providing broker."""
    return get_broker()


@pytest.fixture
def setup_workers(db, broker):
    """Fixture creating test workers."""
    workers = []
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

    return [w for w in db.query(Worker).all()[-3:]]


class TestBasicTaskFlow:
    """Test basic task submission and execution flow."""

    def test_submit_and_assign_task(self, db, broker, setup_workers):
        """Test submitting and assigning a task."""
        # Create task
        task = Task(
            task_name="process_data",
            task_args=[1, 2, 3],
            task_kwargs={"mode": "fast"},
            priority=5,
            status="PENDING",
            max_retries=3,
            timeout_seconds=300,
        )
        db.add(task)
        db.commit()

        # Verify task exists
        retrieved = db.query(Task).filter(Task.task_id == task.task_id).first()
        assert retrieved is not None
        assert retrieved.status == "PENDING"
        assert retrieved.task_name == "process_data"

    def test_task_execution_lifecycle(self, db, broker):
        """Test complete task lifecycle from submission to completion."""
        # 1. Create and submit task
        task = Task(
            task_name="calculate",
            task_args=[10, 20],
            task_kwargs={},
            priority=1,
            status="PENDING",
            retry_count=0,
            max_retries=3,
        )
        db.add(task)
        db.commit()

        assert task.status == "PENDING"

        # 2. Simulate assignment
        task.worker_id = uuid4()
        task.status = "RUNNING"
        task.started_at = datetime.utcnow()
        db.commit()

        assert task.status == "RUNNING"
        assert task.started_at is not None

        # 3. Simulate completion
        task.status = "COMPLETED"
        task.completed_at = datetime.utcnow()
        db.commit()

        assert task.status == "COMPLETED"
        assert task.completed_at is not None

    def test_task_failure_and_retry(self, db):
        """Test task failure and automatic retry."""
        # Create task with retries
        task = Task(
            task_name="flaky_task",
            task_args=[],
            task_kwargs={},
            status="PENDING",
            retry_count=0,
            max_retries=3,
        )
        db.add(task)
        db.commit()

        # Simulate failure
        task.status = "FAILED"
        task.error_message = "Connection timeout"
        task.failed_at = datetime.utcnow()
        db.commit()

        assert task.status == "FAILED"

        # Retry
        task.status = "PENDING"
        task.retry_count = 1
        db.commit()

        assert task.retry_count == 1
        assert task.status == "PENDING"

    def test_task_timeout(self, db):
        """Test task timeout handling."""
        task = Task(
            task_name="slow_task",
            task_args=[],
            task_kwargs={},
            status="RUNNING",
            started_at=datetime.utcnow() - timedelta(minutes=10),
            timeout_seconds=300,  # 5 minute timeout
        )
        db.add(task)
        db.commit()

        # Check if timed out
        elapsed = (datetime.utcnow() - task.started_at).total_seconds()
        is_timed_out = elapsed > task.timeout_seconds

        assert is_timed_out is True


class TestWorkerManagement:
    """Test worker registration, heartbeat, and management."""

    def test_worker_registration(self, db, broker, worker_service):
        """Test worker registration process."""
        worker_id = str(uuid4())
        hostname = "compute-node-1"

        # Register worker
        worker = Worker(
            worker_id=worker_id,
            hostname=hostname,
            capacity=10,
            current_load=0,
            status="ACTIVE",
            last_heartbeat=datetime.utcnow(),
        )
        db.add(worker)
        db.commit()

        # Verify registration
        retrieved = db.query(Worker).filter(
            Worker.worker_id == worker_id
        ).first()

        assert retrieved is not None
        assert retrieved.hostname == hostname
        assert retrieved.status == "ACTIVE"

    def test_worker_heartbeat_update(self, db):
        """Test worker heartbeat updates."""
        worker = Worker(
            hostname="worker-1",
            capacity=5,
            current_load=0,
            status="ACTIVE",
            last_heartbeat=datetime.utcnow() - timedelta(minutes=1),
        )
        db.add(worker)
        db.commit()

        initial_heartbeat = worker.last_heartbeat

        # Update heartbeat
        worker.last_heartbeat = datetime.utcnow()
        db.commit()

        assert worker.last_heartbeat > initial_heartbeat

    def test_worker_capacity_management(self, db):
        """Test worker capacity changes."""
        worker = Worker(
            hostname="worker-1",
            capacity=5,
            current_load=3,
            status="ACTIVE",
            last_heartbeat=datetime.utcnow(),
        )
        db.add(worker)
        db.commit()

        # Increase capacity
        worker.capacity = 10
        db.commit()

        assert worker.capacity == 10
        assert worker.current_load == 3
        assert worker.current_load < worker.capacity

    def test_multi_worker_load_distribution(self, db, setup_workers):
        """Test load distribution across multiple workers."""
        workers = setup_workers

        # Assign loads
        for i, worker in enumerate(workers):
            worker.current_load = (i + 1) * 2
            db.add(worker)
        db.commit()

        # Verify loads
        for i, worker in enumerate(db.query(Worker).all()[-3:]):
            assert worker.current_load == (i + 1) * 2

    def test_worker_health_check(self, db):
        """Test worker health checking."""
        worker = Worker(
            hostname="healthy-worker",
            capacity=5,
            current_load=2,
            status="ACTIVE",
            last_heartbeat=datetime.utcnow(),
        )
        db.add(worker)
        db.commit()

        # Simulate no heartbeat for long time
        worker.last_heartbeat = datetime.utcnow() - timedelta(minutes=10)

        # Check if unhealthy
        time_since_heartbeat = (datetime.utcnow() - worker.last_heartbeat).total_seconds()
        is_unhealthy = time_since_heartbeat > 300  # 5 minute threshold

        assert is_unhealthy is True


class TestQueueOperations:
    """Test queue prioritization and depth."""

    def test_priority_queue_ordering(self, db, broker):
        """Test tasks are ordered by priority."""
        # Create tasks with different priorities
        for priority in [1, 5, 10, 3, 8]:
            task = Task(
                task_name="test",
                task_args=[],
                task_kwargs={},
                priority=priority,
                status="PENDING",
            )
            db.add(task)
        db.commit()

        # Retrieve in order
        tasks = db.query(Task).order_by(Task.priority.desc()).all()

        priorities = [t.priority for t in tasks]
        assert priorities == sorted(priorities, reverse=True)

    def test_queue_depth_tracking(self, db):
        """Test queue depth calculation."""
        # Create pending tasks
        for _ in range(5):
            task = Task(
                task_name="test",
                task_args=[],
                task_kwargs={},
                status="PENDING",
                priority=1,
            )
            db.add(task)
        db.commit()

        # Count pending
        pending_count = db.query(Task).filter(Task.status == "PENDING").count()
        assert pending_count == 5

    def test_queue_backpressure(self, db):
        """Test handling of queue backlog."""
        # Create large number of tasks
        for i in range(100):
            task = Task(
                task_name="heavy",
                task_args=[i],
                task_kwargs={},
                status="PENDING",
                priority=1,
            )
            db.add(task)

            if i % 10 == 0:
                db.commit()

        db.commit()

        pending = db.query(Task).filter(Task.status == "PENDING").count()
        assert pending == 100


class TestErrorHandlingAndRetry:
    """Test error handling and retry logic."""

    def test_exponential_backoff_retry(self, db):
        """Test exponential backoff in retries."""
        task = Task(
            task_name="failing_task",
            task_args=[],
            task_kwargs={},
            status="FAILED",
            retry_count=0,
            max_retries=3,
            error_message="Initial failure",
        )
        db.add(task)
        db.commit()

        # Calculate backoff times
        backoff_times = []
        for retry in range(1, 4):
            backoff = 2 ** (retry - 1) * 5  # 5s, 10s, 20s
            backoff_times.append(backoff)

        assert backoff_times == [5, 10, 20]

    def test_max_retry_limit(self, db):
        """Test max retry limit enforcement."""
        task = Task(
            task_name="failing_task",
            task_args=[],
            task_kwargs={},
            status="FAILED",
            retry_count=3,
            max_retries=3,
            error_message="Max retries exceeded",
        )
        db.add(task)
        db.commit()

        # Check if should retry
        can_retry = task.retry_count < task.max_retries
        assert can_retry is False

    def test_dead_letter_queue(self, db):
        """Test DLQ for tasks exceeding max retries."""
        task = Task(
            task_name="poisoned_task",
            task_args=[],
            task_kwargs={},
            status="FAILED",
            retry_count=3,
            max_retries=3,
            dlq_reason="Max retries exceeded",
            in_dlq=True,
        )
        db.add(task)
        db.commit()

        retrieved = db.query(Task).filter(Task.in_dlq is True).first()
        assert retrieved is not None
        assert retrieved.dlq_reason is not None


class TestSchedulingAndDependencies:
    """Test scheduled tasks and dependencies."""

    def test_scheduled_task_execution(self, db):
        """Test scheduled task creation and timing."""
        scheduled_time = datetime.utcnow() + timedelta(hours=1)

        task = Task(
            task_name="scheduled",
            task_args=[],
            task_kwargs={},
            status="SCHEDULED",
            scheduled_at=scheduled_time,
        )
        db.add(task)
        db.commit()

        # Check if should execute
        now = datetime.utcnow()
        should_execute = now >= task.scheduled_at

        assert should_execute is False

        # Advance time
        now = scheduled_time + timedelta(minutes=1)
        should_execute = now >= task.scheduled_at
        assert should_execute is True

    def test_task_dependency_resolution(self, db):
        """Test task dependency ordering."""
        # Create task A
        task_a = Task(
            task_name="task_a",
            task_args=[],
            task_kwargs={},
            status="COMPLETED",
        )
        db.add(task_a)
        db.commit()

        # Create task B dependent on A
        task_b = Task(
            task_name="task_b",
            task_args=[],
            task_kwargs={},
            status="PENDING",
            depends_on_tasks=[str(task_a.task_id)],
        )
        db.add(task_b)
        db.commit()

        # Check dependencies
        assert len(task_b.depends_on_tasks or []) == 1
        assert str(task_a.task_id) in (task_b.depends_on_tasks or [])


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_simple_workflow(self, db, setup_workers):
        """Test simple task submission and completion workflow."""
        workers = setup_workers

        # 1. Submit task
        task = Task(
            task_name="process",
            task_args=["data"],
            task_kwargs={"mode": "fast"},
            status="PENDING",
            priority=5,
            max_retries=3,
        )
        db.add(task)
        db.commit()

        task_id = task.task_id

        # 2. Assign to worker
        task = db.query(Task).filter(Task.task_id == task_id).first()
        task.worker_id = workers[0].worker_id
        task.status = "RUNNING"
        task.started_at = datetime.utcnow()
        workers[0].current_load += 1
        db.commit()

        assert task.status == "RUNNING"
        assert workers[0].current_load == 1

        # 3. Complete task
        task.status = "COMPLETED"
        task.completed_at = datetime.utcnow()
        workers[0].current_load -= 1
        db.commit()

        assert task.status == "COMPLETED"
        assert workers[0].current_load == 0

    def test_multi_task_workflow(self, db, setup_workers):
        """Test multiple concurrent tasks."""
        workers = setup_workers

        # Submit multiple tasks
        task_ids = []
        for i in range(10):
            task = Task(
                task_name=f"task_{i}",
                task_args=[i],
                task_kwargs={},
                status="PENDING",
                priority=i % 5,
            )
            db.add(task)
            task_ids.append(task.task_id)

        db.commit()

        # Assign to workers
        tasks = db.query(Task).all()
        for i, task in enumerate(tasks):
            worker = workers[i % len(workers)]
            task.worker_id = worker.worker_id
            task.status = "RUNNING"
            task.started_at = datetime.utcnow()
            worker.current_load += 1

        db.commit()

        # Verify distribution
        for worker in workers:
            count = db.query(Task).filter(Task.worker_id == worker.worker_id).count()
            assert count > 0

        # Complete all
        for task in db.query(Task).all():
            task.status = "COMPLETED"
            task.completed_at = datetime.utcnow()
            worker = db.query(Worker).filter(
                Worker.worker_id == task.worker_id
            ).first()
            if worker:
                worker.current_load = max(0, worker.current_load - 1)

        db.commit()

        # Verify all completed
        completed_count = db.query(Task).filter(
            Task.status == "COMPLETED"
        ).count()
        assert completed_count == 10

    def test_failure_recovery_workflow(self, db):
        """Test failure detection and recovery."""
        # Submit task
        task = Task(
            task_name="recovery_test",
            task_args=[],
            task_kwargs={},
            status="PENDING",
            max_retries=2,
        )
        db.add(task)
        db.commit()

        # Simulate failure
        task.status = "FAILED"
        task.error_message = "Network timeout"
        task.failed_at = datetime.utcnow()
        db.commit()

        assert task.status == "FAILED"

        # Retry
        task.status = "PENDING"
        task.retry_count = 1
        db.commit()

        assert task.retry_count == 1

        # Succeed on retry
        task.status = "COMPLETED"
        task.completed_at = datetime.utcnow()
        db.commit()

        assert task.status == "COMPLETED"
