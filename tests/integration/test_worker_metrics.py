"""Integration tests for worker metrics tracking."""

import time

import pytest

from src.monitoring.worker_metrics import WorkerMetricsTracker


class TestWorkerMetrics:
    """Test worker performance metrics tracking."""

    @pytest.fixture
    def tracker(self):
        """Create a worker metrics tracker instance."""
        return WorkerMetricsTracker()

    def test_record_worker_start(self, tracker):
        """Test recording worker start."""
        worker_id = "test-worker-1"
        
        tracker.record_worker_start(worker_id)
        
        metrics = tracker.get_worker_metrics(worker_id)
        assert metrics["worker_id"] == worker_id
        assert metrics["restart_count"] == 1
        assert metrics["uptime_seconds"] >= 0

    def test_record_task_lifecycle(self, tracker):
        """Test recording complete task lifecycle."""
        worker_id = "test-worker-2"
        task_id = "task-123"
        task_name = "test_task"
        
        # Start worker
        tracker.record_worker_start(worker_id)
        
        # Start task
        tracker.record_task_start(worker_id, task_id, task_name)
        
        # Complete task
        time.sleep(0.1)  # Simulate task execution
        tracker.record_task_complete(
            worker_id, task_id, task_name, duration_seconds=0.1, success=True
        )
        
        # Check metrics
        metrics = tracker.get_worker_metrics(worker_id)
        assert metrics["total_tasks"] == 1
        assert metrics["total_errors"] == 0
        assert metrics["avg_duration_seconds"] > 0

    def test_record_task_failure(self, tracker):
        """Test recording task failure."""
        worker_id = "test-worker-3"
        task_id = "task-456"
        task_name = "failing_task"
        
        tracker.record_worker_start(worker_id)
        tracker.record_task_start(worker_id, task_id, task_name)
        tracker.record_task_complete(
            worker_id, task_id, task_name, duration_seconds=0.5, success=False
        )
        
        metrics = tracker.get_worker_metrics(worker_id)
        assert metrics["total_errors"] == 1
        assert metrics["error_rate"] == 1.0  # 100% error rate with 1 task

    def test_get_worker_task_history(self, tracker):
        """Test retrieving worker task history."""
        worker_id = "test-worker-4"
        
        tracker.record_worker_start(worker_id)
        
        # Record multiple tasks
        for i in range(5):
            task_id = f"task-{i}"
            tracker.record_task_start(worker_id, task_id, "test_task")
            tracker.record_task_complete(
                worker_id, task_id, "test_task", duration_seconds=0.1
            )
        
        history = tracker.get_worker_task_history(worker_id, limit=10)
        assert len(history) >= 5  # At least 5 entries (start + complete for each)

    def test_compare_workers(self, tracker):
        """Test comparing performance across multiple workers."""
        # Create multiple workers
        for i in range(3):
            worker_id = f"worker-{i}"
            tracker.record_worker_start(worker_id)
            
            # Record different number of tasks per worker
            for j in range((i + 1) * 2):
                task_id = f"task-{i}-{j}"
                tracker.record_task_start(worker_id, task_id, "test_task")
                tracker.record_task_complete(
                    worker_id, task_id, "test_task", duration_seconds=0.1 + i * 0.05
                )
        
        comparison = tracker.compare_workers()
        assert comparison["total_workers"] == 3
        assert comparison["aggregate"]["total_tasks"] == 12  # 2 + 4 + 6
        assert "best_performer" in comparison
        assert "slowest_worker" in comparison

    def test_heartbeat_recording(self, tracker):
        """Test worker heartbeat recording."""
        worker_id = "test-worker-5"
        
        tracker.record_worker_start(worker_id)
        time.sleep(0.1)
        tracker.record_heartbeat(worker_id)
        
        metrics = tracker.get_worker_metrics(worker_id)
        assert metrics["last_heartbeat"] is not None

    def test_restart_count_increments(self, tracker):
        """Test that restart count increments on multiple starts."""
        worker_id = "test-worker-6"
        
        tracker.record_worker_start(worker_id)
        metrics1 = tracker.get_worker_metrics(worker_id)
        assert metrics1["restart_count"] == 1
        
        tracker.record_worker_start(worker_id)
        metrics2 = tracker.get_worker_metrics(worker_id)
        assert metrics2["restart_count"] == 2

    def test_empty_metrics_for_nonexistent_worker(self, tracker):
        """Test that empty metrics are returned for non-existent worker."""
        metrics = tracker.get_worker_metrics("nonexistent-worker")
        assert metrics == {}

    def test_get_all_workers_metrics(self, tracker):
        """Test retrieving metrics for all workers."""
        # Create multiple workers
        for i in range(3):
            worker_id = f"multi-worker-{i}"
            tracker.record_worker_start(worker_id)
            tracker.record_task_start(worker_id, f"task-{i}", "test")
            tracker.record_task_complete(worker_id, f"task-{i}", "test", 0.1)
        
        all_metrics = tracker.get_all_workers_metrics()
        assert len(all_metrics) >= 3
        assert all(m["total_tasks"] >= 1 for m in all_metrics)
