"""Unit tests for task API endpoints."""

import json
import os
from datetime import datetime
from uuid import uuid4

import pytest
from unittest.mock import Mock, patch

# Set test environment before importing app
os.environ["APP_ENV"] ="test"

from src.models import Base, Task


class TestCreateTaskEndpoint:
    """Test POST /api/v1/tasks endpoint"""

    @patch('src.api.routes.tasks.get_broker')
    def test_create_task_success(self, mock_get_broker, client):
        """Test successful task creation"""
        # Mock broker
        mock_broker = Mock()
        mock_broker.enqueue_task = Mock(return_value=True)
        mock_get_broker.return_value = mock_broker
        
        payload = {
            "task_name": "send_email",
            "task_kwargs": {
                "to": "user@example.com",
                "subject": "Test",
                "body": "Hello"
            },
            "priority": 8,
            "max_retries": 3,
            "timeout_seconds": 60
        }
        
        response = client.post("/api/v1/tasks", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data
        assert data["task_name"] == "send_email"
        assert data["priority"] == 8
        assert data["status"] == "PENDING"

    @patch('src.api.routes.tasks.get_broker')
    def test_create_task_with_minimal_fields(self, mock_get_broker, client):
        """Test task creation with only required fields"""
        mock_broker = Mock()
        mock_broker.enqueue_task = Mock(return_value=True)
        mock_get_broker.return_value = mock_broker
        
        payload = {
            "task_name": "process_data"
        }
        
        response = client.post("/api/v1/tasks", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["task_name"] == "process_data"
        assert data["priority"] == 5  # Default priority
        assert data["max_retries"] == 5  # Default retries

    def test_create_task_invalid_priority(self, client):
        """Test task creation with invalid priority"""
        payload = {
            "task_name": "test_task",
            "priority": 15  # Out of range (1-10)
        }
        
        response = client.post("/api/v1/tasks", json=payload)
        
        # Should return validation error
        assert response.status_code == 422

    def test_create_task_missing_task_name(self, client):
        """Test task creation without task name"""
        payload = {
            "priority": 5
        }
        
        response = client.post("/api/v1/tasks", json=payload)
        
        assert response.status_code == 422
        assert "task_name" in response.text.lower()

    def test_create_task_empty_task_name(self, client):
        """Test task creation with empty task name"""
        payload = {
            "task_name": "   "  # Whitespace only
        }
        
        response = client.post("/api/v1/tasks", json=payload)
        
        assert response.status_code == 422

    @patch('src.api.routes.tasks.get_broker')
    def test_create_task_with_scheduled_time(self, mock_get_broker, client):
        """Test creating scheduled task"""
        mock_broker = Mock()
        mock_broker.schedule_task = Mock(return_value=True)
        mock_get_broker.return_value = mock_broker
        
        future_time = "2026-12-31T23:59:59"
        payload = {
            "task_name": "scheduled_task",
            "scheduled_at": future_time,
            "priority": 7
        }
        
        response = client.post("/api/v1/tasks", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["scheduled_at"] is not None
        # Should call schedule_task, not enqueue_task
        mock_broker.schedule_task.assert_called_once()

    @patch('src.api.routes.tasks.get_broker')
    def test_create_task_with_complex_payload(self, mock_get_broker, client):
        """Test task with complex nested payload"""
        mock_broker = Mock()
        mock_broker.enqueue_task = Mock(return_value=True)
        mock_get_broker.return_value = mock_broker
        
        payload = {
            "task_name": "complex_task",
            "task_kwargs": {
                "nested": {
                    "level1": {
                        "level2": {
                            "value": 123,
                            "list": [1, 2, 3],
                            "flag": True
                        }
                    }
                },
                "array": ["a", "b", "c"]
            },
            "priority": 6
        }
        
        response = client.post("/api/v1/tasks", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["task_name"] == "complex_task"

    @patch('src.api.routes.tasks.get_broker')
    def test_create_task_broker_enqueue_fails(self, mock_get_broker, client):
        """Test handling of broker enqueue failure"""
        mock_broker = Mock()
        mock_broker.enqueue_task = Mock(return_value=False)
        mock_get_broker.return_value = mock_broker
        
        payload = {
            "task_name": "failing_task",
            "priority": 5
        }
        
        response = client.post("/api/v1/tasks", json=payload)
        
        # Should return 500 error
        assert response.status_code == 500
        assert "enqueue" in response.text.lower()

    @patch('src.api.routes.tasks.get_broker')
    def test_create_task_with_parent_task_id(self, mock_get_broker, client, db):
        """Test creating child task with parent dependency"""
        # Create parent task first
        parent_task = Task(
            task_name="parent_task",
            priority=5,
            status="PENDING"
        )
        db.add(parent_task)
        db.commit()
        
        mock_broker = Mock()
        mock_broker.enqueue_task = Mock(return_value=True)
        mock_get_broker.return_value = mock_broker
        
        payload = {
            "task_name": "child_task",
            "parent_task_id": str(parent_task.task_id),
            "priority": 5
        }
        
        response = client.post("/api/v1/tasks", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["task_name"] == "child_task"


class TestTaskValidation:
    """Test task schema validation"""

    def test_priority_range_validation(self, client):
        """Test priority must be between 1 and 10"""
        # Test below range
        response = client.post("/api/v1/tasks", json={
            "task_name": "test",
            "priority": 0
        })
        assert response.status_code == 422
        
        # Test above range
        response = client.post("/api/v1/tasks", json={
            "task_name": "test",
            "priority": 11
        })
        assert response.status_code == 422

    def test_max_retries_validation(self, client):
        """Test max_retries must be between 0 and 10"""
        response = client.post("/api/v1/tasks", json={
            "task_name": "test",
            "max_retries": 15
        })
        assert response.status_code == 422

    def test_timeout_validation(self, client):
        """Test timeout must be between 1 and 3600"""
        response = client.post("/api/v1/tasks", json={
            "task_name": "test",
            "timeout_seconds": 5000
        })
        assert response.status_code == 422

    def test_task_kwargs_must_be_dict(self, client):
        """Test task_kwargs must be a dictionary"""
        response = client.post("/api/v1/tasks", json={
            "task_name": "test",
            "task_kwargs": "not a dict"
        })
        assert response.status_code == 422
