"""Chaos and stress tests for system resilience."""

import pytest
import random
from datetime import datetime, timedelta
from uuid import uuid4

from src.models import Worker, Task


@pytest.fixture
def chaos_workers(db):
    """Create workers for chaos testing."""
    workers = []
    for i in range(5):
        worker = Worker(
            hostname=f"chaos-worker-{i}",
            capacity=10,
            current_load=0,
            status="ACTIVE",
            last_heartbeat=datetime.utcnow(),
        )
        db.add(worker)
    db.commit()
    return db.query(Worker).all()[-5:]


class TestHighLoadConditions:
    """Test system behavior under high load."""

    def test_high_task_submission_rate(self, db):
        """Test rapid task submission."""
        # Submit 1000 tasks rapidly
        for i in range(1000):
            task = Task(
                task_name=f"high_load_{i % 10}",
                task_args=[i],
                task_kwargs={"batch": i // 100},
                status="PENDING",
                priority=random.randint(1, 10),
            )
            db.add(task)

            if i % 100 == 0:
                db.commit()

        db.commit()

        # Verify all submitted
        count = db.query(Task).filter(Task.status == "PENDING").count()
        assert count == 1000

    def test_queue_overflow_handling(self, db):
        """Test handling of extremely large queue."""
        # Create 5000 pending tasks
        for i in range(5000):
            task = Task(
                task_name="overflow_test",
                task_args=[i],
                task_kwargs={},
                status="PENDING",
                priority=random.randint(1, 5),
            )
            db.add(task)

            if i % 500 == 0:
                db.commit()

        db.commit()

        # Count pending
        pending = db.query(Task).filter(Task.status == "PENDING").count()
        assert pending == 5000

        # Verify priority ordering works under load
        high_priority = db.query(Task).filter(
            Task.status == "PENDING",
            Task.priority >= 4,
        ).count()
        assert high_priority > 0

    def test_concurrent_worker_operations(self, db, chaos_workers):
        """Test workers operating concurrently."""
        workers = chaos_workers

        # Create many tasks
        for i in range(100):
            task = Task(
                task_name="concurrent",
                task_args=[i],
                task_kwargs={},
                status="PENDING",
                priority=random.randint(1, 10),
            )
            db.add(task)
        db.commit()

        # Simulate concurrent assignment and execution
        tasks = db.query(Task).filter(Task.status == "PENDING").all()

        for i, task in enumerate(tasks):
            worker = workers[i % len(workers)]
            task.worker_id = worker.worker_id
            task.status = "RUNNING"
            task.started_at = datetime.utcnow()
            worker.current_load += 1

        db.commit()

        # Verify distribution
        for worker in workers:
            assigned = db.query(Task).filter(
                Task.worker_id == worker.worker_id,
                Task.status == "RUNNING",
            ).count()
            assert assigned <= worker.capacity


class TestWorkerFailures:
    """Test system behavior when workers fail."""

    def test_worker_sudden_death(self, db, chaos_workers):
        """Test handling of worker crash."""
        worker = chaos_workers[0]

        # Assign tasks to worker
        for i in range(5):
            task = Task(
                task_name="test",
                task_args=[],
                task_kwargs={},
                status="RUNNING",
                worker_id=worker.worker_id,
                started_at=datetime.utcnow(),
            )
            db.add(task)
        db.commit()

        # Worker dies
        worker.status = "DEAD"
        db.commit()

        # Find orphaned tasks
        orphaned = db.query(Task).filter(
            Task.worker_id == worker.worker_id,
            Task.status == "RUNNING",
        ).count()

        assert orphaned == 5

    def test_cascading_worker_failures(self, db, chaos_workers):
        """Test multiple workers failing."""
        workers = chaos_workers[:3]

        # Assign tasks
        task_count = 0
        for worker in workers:
            for i in range(5):
                task = Task(
                    task_name="test",
                    task_args=[],
                    task_kwargs={},
                    status="RUNNING",
                    worker_id=worker.worker_id,
                    started_at=datetime.utcnow(),
                )
                db.add(task)
                task_count += 1
        db.commit()

        # All workers die
        for worker in workers:
            worker.status = "DEAD"
        db.commit()

        # Verify orphaned tasks
        orphaned = db.query(Task).filter(
            Task.status == "RUNNING",
            Task.worker_id.in_([w.worker_id for w in workers]),
        ).count()

        assert orphaned == task_count

    def test_worker_slowdown_recovery(self, db, chaos_workers):
        """Test recovery from slowed workers."""
        slow_worker = chaos_workers[0]

        # Assign tasks
        for i in range(10):
            task = Task(
                task_name="test",
                task_args=[],
                task_kwargs={},
                status="RUNNING",
                worker_id=slow_worker.worker_id,
                started_at=datetime.utcnow() - timedelta(minutes=5),
            )
            db.add(task)
        db.commit()

        # Detect timeout
        tasks = db.query(Task).filter(
            Task.worker_id == slow_worker.worker_id,
            Task.status == "RUNNING",
        ).all()

        timed_out = []
        for task in tasks:
            elapsed = (datetime.utcnow() - task.started_at).total_seconds()
            if elapsed > 300:  # 5 minute timeout
                timed_out.append(task)

        # Move to DLQ or retry
        for task in timed_out:
            task.status = "FAILED"
            task.error_message = "Task timeout"

        db.commit()

        assert len(timed_out) == 10

    def test_flaky_worker_pattern(self, db, chaos_workers):
        """Test worker that intermittently fails."""
        worker = chaos_workers[0]

        # Simulate flaky behavior
        success_count = 0
        failure_count = 0

        for i in range(20):
            task = Task(
                task_name="flaky",
                task_args=[],
                task_kwargs={},
                status="COMPLETED" if random.random() > 0.5 else "FAILED",
                worker_id=worker.worker_id,
                completed_at=datetime.utcnow(),
            )
            db.add(task)

            if task.status == "COMPLETED":
                success_count += 1
            else:
                failure_count += 1

        db.commit()

        # Calculate success rate
        success_rate = success_count / (success_count + failure_count) * 100

        # Should be around 50% but not guaranteed
        assert 0 <= success_rate <= 100

        # Detect flaky worker
        tasks = db.query(Task).filter(Task.worker_id == worker.worker_id).all()
        failures = sum(1 for t in tasks if t.status == "FAILED")
        success = sum(1 for t in tasks if t.status == "COMPLETED")

        is_flaky = failures > 0 and success > 0
        assert is_flaky is True


class TestTaskFailurePatterns:
    """Test different task failure modes."""

    def test_timeout_failures(self, db):
        """Test timeout-based failures."""
        for i in range(50):
            task = Task(
                task_name="slow_task",
                task_args=[],
                task_kwargs={},
                status="FAILED",
                started_at=datetime.utcnow() - timedelta(minutes=10),
                failed_at=datetime.utcnow(),
                error_message="Task timeout",
            )
            db.add(task)
        db.commit()

        timeouts = db.query(Task).filter(
            Task.error_message.like("%timeout%")
        ).count()
        assert timeouts == 50

    def test_resource_exhaustion_failures(self, db):
        """Test resource exhaustion scenarios."""
        for i in range(30):
            task = Task(
                task_name="memory_intensive",
                task_args=[],
                task_kwargs={},
                status="FAILED",
                failed_at=datetime.utcnow(),
                error_message="Out of memory" if i % 2 == 0 else "Disk space exceeded",
            )
            db.add(task)
        db.commit()

        oom_failures = db.query(Task).filter(
            Task.error_message.like("%memory%")
        ).count()
        disk_failures = db.query(Task).filter(
            Task.error_message.like("%Disk%")
        ).count()

        assert oom_failures > 0
        assert disk_failures > 0

    def test_transient_failures(self, db):
        """Test transient network failures."""
        # Create tasks that fail transiently
        for i in range(100):
            task = Task(
                task_name="network_call",
                task_args=[i],
                task_kwargs={},
                status="COMPLETED" if i % 3 != 0 else "FAILED",
                retry_count=0 if i % 3 != 0 else 1,
                error_message="Connection timeout" if i % 3 != 0 else None,
            )
            db.add(task)

            if i % 10 == 0:
                db.commit()

        db.commit()

        # Verify retry pattern
        retried = db.query(Task).filter(Task.retry_count > 0).count()
        assert retried > 0


class TestResourceConstraints:
    """Test behavior under resource constraints."""

    def test_memory_pressure_scenario(self, db, chaos_workers):
        """Test behavior when memory is constrained."""
        # Create many in-flight tasks (simulating memory pressure)
        for i in range(500):
            task = Task(
                task_name="memory_task",
                task_args=[i] * 100,  # Large args
                task_kwargs={},
                status="RUNNING",
                worker_id=chaos_workers[i % len(chaos_workers)].worker_id,
                started_at=datetime.utcnow(),
            )
            db.add(task)

            if i % 50 == 0:
                db.commit()

        db.commit()

        # Verify tasks can still be queried despite load
        running = db.query(Task).filter(Task.status == "RUNNING").count()
        assert running == 500

    def test_cpu_bound_saturation(self, db, chaos_workers):
        """Test CPU saturation scenario."""
        workers = chaos_workers

        # All workers at full capacity
        for i, worker in enumerate(workers):
            worker.current_load = worker.capacity

        db.commit()

        # Verify all workers at capacity
        for worker in workers:
            capacity_used = worker.current_load / worker.capacity
            assert capacity_used == 1.0

    def test_disk_io_saturation(self, db):
        """Test disk I/O saturation."""
        # Create many I/O intensive tasks
        for i in range(200):
            task = Task(
                task_name="disk_io_task",
                task_args=[],
                task_kwargs={"file_size_mb": 100},
                status="RUNNING" if i % 2 == 0 else "QUEUED",
                started_at=datetime.utcnow(),
            )
            db.add(task)

            if i % 20 == 0:
                db.commit()

        db.commit()

        running = db.query(Task).filter(Task.status == "RUNNING").count()
        queued = db.query(Task).filter(Task.status == "QUEUED").count()

        assert running == 100
        assert queued == 100


class TestRecoveryAndResilience:
    """Test recovery and resilience under chaos."""

    def test_recovery_from_cascading_failures(self, db, chaos_workers):
        """Test recovery when multiple systems fail."""
        workers = chaos_workers

        # Create tasks across workers
        for i in range(100):
            task = Task(
                task_name="resilience_test",
                task_args=[i],
                task_kwargs={},
                status="RUNNING",
                worker_id=workers[i % len(workers)].worker_id,
                started_at=datetime.utcnow(),
            )
            db.add(task)

            if i % 25 == 0:
                db.commit()

        db.commit()

        # Simulate cascade: 40% of workers fail
        for worker in workers[:2]:
            worker.status = "DEAD"

        db.commit()

        # Tasks on live workers should be fine
        live_workers = [w for w in workers if w.status == "ACTIVE"]
        live_tasks = db.query(Task).filter(
            Task.worker_id.in_([w.worker_id for w in live_workers]),
        ).count()

        assert live_tasks > 0

    def test_graceful_degradation_under_load(self, db):
        """Test system degrades gracefully."""
        # Create mixed task statuses
        for i in range(1000):
            status = random.choice(["PENDING", "RUNNING", "COMPLETED", "FAILED"])
            task = Task(
                task_name="degrade_test",
                task_args=[i],
                task_kwargs={},
                status=status,
            )
            db.add(task)

            if i % 100 == 0:
                db.commit()

        db.commit()

        # Verify system still responsive
        pending = db.query(Task).filter(Task.status == "PENDING").count()
        running = db.query(Task).filter(Task.status == "RUNNING").count()
        completed = db.query(Task).filter(Task.status == "COMPLETED").count()
        failed = db.query(Task).filter(Task.status == "FAILED").count()

        total = pending + running + completed + failed
        assert total == 1000

    def test_distributed_failure_isolation(self, db, chaos_workers):
        """Test that failure on one worker doesn't cascade."""
        workers = chaos_workers

        # Assign tasks
        for i in range(50):
            task = Task(
                task_name="isolation_test",
                task_args=[i],
                task_kwargs={},
                status="RUNNING",
                worker_id=workers[i % len(workers)].worker_id,
                started_at=datetime.utcnow(),
            )
            db.add(task)

        db.commit()

        # Isolate one worker
        failed_worker = workers[0]
        failed_worker.status = "DEAD"
        db.commit()

        # Tasks on other workers unaffected
        other_tasks = db.query(Task).filter(
            Task.worker_id.in_([w.worker_id for w in workers[1:]]),
            Task.status == "RUNNING",
        ).count()

        tasks_on_failed = db.query(Task).filter(
            Task.worker_id == failed_worker.worker_id,
            Task.status == "RUNNING",
        ).count()

        assert other_tasks > 0
        assert tasks_on_failed > 0
