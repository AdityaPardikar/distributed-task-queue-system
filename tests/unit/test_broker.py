"""Unit tests for broker operations and priority queue logic"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.core.broker import TaskBroker
from src.cache.client import RedisClient


@pytest.fixture
def mock_redis():
    """Create mock Redis client"""
    redis = Mock(spec=RedisClient)
    redis.rpush = Mock(return_value=1)
    redis.blpop = Mock(return_value=None)
    redis.hset = Mock(return_value=1)
    redis.hgetall = Mock(return_value={})
    redis.sadd = Mock(return_value=1)
    redis.smembers = Mock(return_value=set())
    return redis


@pytest.fixture
def broker(mock_redis):
    """Create a test broker instance with mock Redis"""
    return TaskBroker(redis_client=mock_redis)


class TestPriorityQueueLogic:
    """Test priority queue operations"""

    def test_enqueue_high_priority_task(self, broker, mock_redis):
        """Test enqueueing high priority task (8-10)"""
        task_id = "task-high-priority"
        priority = 10
        
        result = broker.enqueue_task(task_id, priority=priority)
        
        assert result is True
        mock_redis.rpush.assert_called()
        call_args = mock_redis.rpush.call_args[0]
        assert "HIGH" in call_args[0]

    def test_enqueue_medium_priority_task(self, broker, mock_redis):
        """Test enqueueing medium priority task (4-7)"""
        task_id = "task-medium"
        priority = 5
        
        result = broker.enqueue_task(task_id, priority=priority)
        
        assert result is True
        call_args = mock_redis.rpush.call_args[0]
        assert "MEDIUM" in call_args[0]

    def test_enqueue_low_priority_task(self, broker, mock_redis):
        """Test enqueueing low priority task (1-3)"""
        task_id = "task-low"
        priority = 2
        
        result = broker.enqueue_task(task_id, priority=priority)
        
        assert result is True
        call_args = mock_redis.rpush.call_args[0]
        assert "LOW" in call_args[0]

    def test_invalid_priority_defaults_to_medium(self, broker, mock_redis):
        """Test that invalid priority defaults to medium"""
        task_id = "task-invalid"
        priority = 15  # Out of range
        
        broker.enqueue_task(task_id, priority=priority)
        
        call_args = mock_redis.rpush.call_args[0]
        assert "MEDIUM" in call_args[0]

    def test_enqueue_with_metadata(self, broker, mock_redis):
        """Test enqueueing task with metadata"""
        task_id = "task-meta"
        priority = 7
        task_data = {
            "task_name": "send_email",
            "status": "PENDING"
        }
        
        result = broker.enqueue_task(task_id, priority=priority, task_data=task_data)
        
        assert result is True
        mock_redis.hset.assert_called()

    def test_dequeue_checks_priority_order(self, broker, mock_redis):
        """Test that dequeue checks HIGH, then MEDIUM, then LOW"""
        mock_redis.blpop = Mock(side_effect=[
            None,  # HIGH empty
            None,  # MEDIUM empty
            ("queue:LOW", "task-low")  # LOW has task
        ])
        
        task_id = broker.dequeue_task()
        
        assert task_id == "task-low"
        assert mock_redis.blpop.call_count == 3


class TestTaskMetadataOperations:
    """Test task metadata operations"""

    def test_set_task_metadata_with_dict(self, broker, mock_redis):
        """Test storing metadata with dict/list values"""
        task_id = "task-meta"
        metadata = {
            "status": "PENDING",
            "payload": {"key": "value"},
            "tags": [1, 2, 3]
        }
        
        broker.set_task_metadata(task_id, metadata)
        
        mock_redis.hset.assert_called_once()
        stored_data = mock_redis.hset.call_args[0][1]
        # Complex types should be JSON strings
        assert isinstance(stored_data["payload"], str)
        assert isinstance(stored_data["tags"], str)

    def test_get_task_metadata_deserializes_payload(self, broker, mock_redis):
        """Test retrieving and deserializing metadata"""
        task_id = "task-get"
        mock_data = {
            "status": "RUNNING",
            "payload": json.dumps({"email": "test@example.com"})
        }
        mock_redis.hgetall = Mock(return_value=mock_data)
        
        metadata = broker.get_task_metadata(task_id)
        
        assert metadata["status"] == "RUNNING"
        assert isinstance(metadata["payload"], dict)
        assert metadata["payload"]["email"] == "test@example.com"

    def test_update_task_status(self, broker, mock_redis):
        """Test updating task status"""
        task_id = "task-status"
        new_status = "COMPLETED"
        
        result = broker.update_task_status(task_id, new_status)
        
        assert result is True
        mock_redis.hset.assert_called()
        update_data = mock_redis.hset.call_args[0][1]
        assert update_data["status"] == new_status

    def test_update_task_status_with_extra_fields(self, broker, mock_redis):
        """Test updating status with additional fields"""
        task_id = "task-extra"
        
        result = broker.update_task_status(
            task_id,
            "COMPLETED",
            completed_at="2026-01-14T12:00:00",
            result="success"
        )
        
        assert result is True
        update_data = mock_redis.hset.call_args[0][1]
        assert update_data["status"] == "COMPLETED"
        assert "completed_at" in update_data
        assert "result" in update_data


class TestWorkerOperations:
    """Test worker registration and management"""

    def test_register_worker(self, broker, mock_redis):
        """Test worker registration"""
        worker_id = "worker-1"
        metadata = {
            "hostname": "test-host",
            "capacity": "5",
            "status": "ACTIVE"
        }
        
        result = broker.register_worker(worker_id, metadata)
        
        assert result is True
        mock_redis.sadd.assert_called()  # Added to registry
        mock_redis.hset.assert_called()  # Stored metadata
    
    workers = broker.get_active_workers()
    assert worker_id in workers
