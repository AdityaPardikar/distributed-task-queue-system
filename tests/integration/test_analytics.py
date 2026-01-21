"""Integration tests for analytics endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi import status
from fastapi.testclient import TestClient

from src.api.main import app
from src.models import Task
from src.db.session import SessionLocal

client = TestClient(app)


class TestAnalyticsAPI:
    """Test analytics API endpoints."""

    def test_get_completion_rate_trend(self):
        """Test getting completion rate trends."""
        response = client.get("/api/v1/analytics/completion-rate-trend?hours=24&interval_minutes=60")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        
        if data:
            trend = data[0]
            assert "timestamp" in trend
            assert "completed" in trend
            assert "failed" in trend
            assert "rate" in trend
            assert 0.0 <= trend["rate"] <= 1.0

    def test_get_wait_time_trend(self):
        """Test getting wait time trends."""
        response = client.get("/api/v1/analytics/wait-time-trend?hours=24&interval_minutes=60")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        
        if data:
            trend = data[0]
            assert "timestamp" in trend
            assert "min_wait" in trend
            assert "max_wait" in trend
            assert "avg_wait" in trend

    def test_get_peak_loads(self):
        """Test getting peak load times."""
        response = client.get("/api/v1/analytics/peak-loads?hours=24&interval_minutes=60&top_n=5")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
        
        if data:
            peak = data[0]
            assert "timestamp" in peak
            assert "submitted" in peak
            assert peak["submitted"] >= 0

    def test_get_task_distribution(self):
        """Test getting task type distribution."""
        response = client.get("/api/v1/analytics/task-distribution?hours=24")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        
        if data:
            dist = data[0]
            assert "task_name" in dist
            assert "total" in dist
            assert "completed" in dist
            assert "failed" in dist
            assert "pending" in dist
            assert "percentage" in dist

    def test_get_failure_patterns(self):
        """Test getting failure patterns."""
        response = client.get("/api/v1/analytics/failure-patterns?hours=24&limit=10")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
        
        if data:
            pattern = data[0]
            assert "task_name" in pattern
            assert "error" in pattern
            assert "count" in pattern
            assert pattern["count"] > 0

    def test_get_retry_success_rate(self):
        """Test getting retry success rates."""
        response = client.get("/api/v1/analytics/retry-success-rate?hours=24")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, dict)
        
        # Each value should be a dict with retry stats
        for task_name, stats in data.items():
            assert "task_name" in stats
            assert "total_retries" in stats
            assert "successful_after_retry" in stats
            assert "failed_after_retry" in stats
            assert "success_rate" in stats
            assert "avg_retries" in stats

    def test_get_performance_summary(self):
        """Test getting performance summary."""
        response = client.get("/api/v1/analytics/performance-summary")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_tasks" in data
        assert "completion_rate" in data
        assert "failure_rate" in data
        assert "avg_execution_time" in data
        assert "avg_wait_time" in data
        assert "total_retries" in data
        
        # Validate ranges
        assert data["completion_rate"] >= 0
        assert data["failure_rate"] >= 0
        assert data["total_retries"] >= 0

    def test_analytics_with_query_parameters(self):
        """Test analytics endpoints with various query parameters."""
        # Test different hour ranges
        response = client.get("/api/v1/analytics/completion-rate-trend?hours=6")
        assert response.status_code == status.HTTP_200_OK
        
        response = client.get("/api/v1/analytics/completion-rate-trend?hours=168")  # 1 week
        assert response.status_code == status.HTTP_200_OK
        
        # Test different intervals
        response = client.get("/api/v1/analytics/completion-rate-trend?interval_minutes=30")
        assert response.status_code == status.HTTP_200_OK
        
        response = client.get("/api/v1/analytics/completion-rate-trend?interval_minutes=120")
        assert response.status_code == status.HTTP_200_OK

    def test_analytics_invalid_parameters(self):
        """Test analytics endpoints with invalid parameters."""
        # Test out-of-range hours
        response = client.get("/api/v1/analytics/completion-rate-trend?hours=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test out-of-range interval
        response = client.get("/api/v1/analytics/completion-rate-trend?interval_minutes=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_analytics_empty_database(self):
        """Test analytics with empty or minimal data."""
        # Should return empty lists or zero values without errors
        response = client.get("/api/v1/analytics/peak-loads?hours=1&top_n=5")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
