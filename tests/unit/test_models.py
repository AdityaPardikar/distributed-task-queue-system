"""Unit tests for models"""

import pytest
from datetime import datetime
from src.models import Task, Worker, Campaign


def test_task_creation():
    """Test Task model creation"""
    task = Task(
        task_name="send_email",
        task_kwargs={"email": "test@example.com"},
        priority=5,
        status="PENDING"
    )
    assert task.task_name == "send_email"
    assert task.priority == 5
    assert task.status == "PENDING"


def test_worker_creation():
    """Test Worker model creation"""
    worker = Worker(
        hostname="worker-1",
        status="ACTIVE",
        capacity=5
    )
    assert worker.hostname == "worker-1"
    assert worker.capacity == 5
    assert worker.status == "ACTIVE"


def test_campaign_creation():
    """Test Campaign model creation"""
    campaign = Campaign(
        name="Welcome Campaign",
        template_subject="Welcome {{name}}",
        template_body="Hello {{name}}!",
        status="DRAFT"
    )
    assert campaign.name == "Welcome Campaign"
    assert campaign.status == "DRAFT"
