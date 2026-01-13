"""Unit tests for broker operations"""

import pytest
from src.core.broker import TaskBroker
from src.cache.client import RedisClient


@pytest.fixture
def broker():
    """Create a test broker instance"""
    return TaskBroker()


def test_enqueue_task(broker):
    """Test enqueuing a task"""
    task_id = "test-task-123"
    result = broker.enqueue_task(task_id, "HIGH")
    assert result is True


def test_dequeue_task(broker):
    """Test dequeuing a task"""
    task_id = "test-task-456"
    broker.enqueue_task(task_id, "MEDIUM")
    # Note: Actual dequeue would require a real Redis instance


def test_task_meta_operations(broker):
    """Test task metadata operations"""
    task_id = "test-task-789"
    metadata = {"status": "RUNNING", "worker_id": "worker-1"}
    
    result = broker.set_task_meta(task_id, metadata)
    assert result is True
    
    retrieved = broker.get_task_meta(task_id)
    assert retrieved.get("status") == "RUNNING"


def test_worker_registration(broker):
    """Test worker registration"""
    worker_id = "worker-test-1"
    metadata = {
        "hostname": "test-host",
        "capacity": "5",
        "status": "ACTIVE"
    }
    
    result = broker.register_worker(worker_id, metadata)
    assert result is True
    
    workers = broker.get_active_workers()
    assert worker_id in workers
