"""Integration tests for dashboard API endpoints."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.api.main import app
from src.models import Task, Worker

client = TestClient(app)


class TestDashboardAPI:
    """Test dashboard API endpoints."""

    def test_get_system_stats(self):
        """Test getting system statistics."""
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_tasks" in data
        assert "active_workers" in data
        assert "queue_depth_high" in data
        assert "system_cpu_percent" in data
        assert "system_memory_percent" in data
        assert "timestamp" in data

    def test_get_workers_grid(self):
        """Test getting worker grid information."""
        response = client.get("/api/v1/dashboard/workers")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        
        # If workers exist, verify structure
        if data:
            worker = data[0]
            assert "worker_id" in worker
            assert "hostname" in worker
            assert "status" in worker
            assert "capacity" in worker
            assert "task_rate_per_minute" in worker

    def test_get_recent_tasks(self):
        """Test getting recent tasks."""
        response = client.get("/api/v1/dashboard/recent-tasks?limit=50")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        
        # If tasks exist, verify structure
        if data:
            task = data[0]
            assert "task_id" in task
            assert "task_name" in task
            assert "status" in task
            assert "priority" in task
            assert "created_at" in task

    def test_get_queue_depth(self):
        """Test getting queue depth metrics."""
        response = client.get("/api/v1/dashboard/queue-depth")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "high_priority_depth" in data
        assert "medium_priority_depth" in data
        assert "low_priority_depth" in data
        assert "total_depth" in data
        assert "oldest_task_age_seconds" in data or data["oldest_task_age_seconds"] is None
        assert "avg_wait_time_seconds" in data or data["avg_wait_time_seconds"] is None

    def test_get_hourly_stats(self):
        """Test getting hourly statistics."""
        response = client.get("/api/v1/dashboard/hourly-stats?hours=12")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        
        # If stats exist, verify structure
        if data:
            stat = data[0]
            assert "hour" in stat
            assert "submitted" in stat
            assert "completed" in stat
            assert "failed" in stat

    def test_get_daily_stats(self):
        """Test getting daily statistics."""
        response = client.get("/api/v1/dashboard/daily-stats?days=3")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        
        # If stats exist, verify structure
        if data:
            stat = data[0]
            assert "day" in stat
            assert "submitted" in stat
            assert "completed" in stat
            assert "failed" in stat
            assert "avg_duration_seconds" in stat

    def test_dashboard_stats_with_no_data(self):
        """Test dashboard endpoints with empty database."""
        # This should still return valid responses with zero values
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["total_tasks"] >= 0
        assert data["active_workers"] >= 0

    def test_recent_tasks_limit_parameter(self):
        """Test recent tasks with different limit values."""
        # Test with small limit
        response = client.get("/api/v1/dashboard/recent-tasks?limit=5")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 5
        
        # Test with large limit
        response = client.get("/api/v1/dashboard/recent-tasks?limit=1000")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 1000

    def test_hourly_stats_time_range(self):
        """Test hourly stats with different time ranges."""
        # Test 6 hours
        response = client.get("/api/v1/dashboard/hourly-stats?hours=6")
        assert response.status_code == status.HTTP_200_OK
        
        # Test 48 hours
        response = client.get("/api/v1/dashboard/hourly-stats?hours=48")
        assert response.status_code == status.HTTP_200_OK

    def test_daily_stats_time_range(self):
        """Test daily stats with different time ranges."""
        # Test 7 days
        response = client.get("/api/v1/dashboard/daily-stats?days=7")
        assert response.status_code == status.HTTP_200_OK
        
        # Test 30 days
        response = client.get("/api/v1/dashboard/daily-stats?days=30")
        assert response.status_code == status.HTTP_200_OK
