"""Integration tests for observability features (metrics, logging, tracing)."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_prometheus_metrics_endpoint():
    """Test Prometheus scrape endpoint returns metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    # Check for some expected metric names
    assert b"tasks_submitted_total" in response.content
    assert b"queue_depth" in response.content
    assert b"http_request_duration_seconds" in response.content


def test_api_metrics_endpoint():
    """Test API metrics endpoint returns JSON."""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "tasks_total" in data
    assert "workers_active" in data
    assert "queue_depth" in data


def test_health_endpoint():
    """Test basic health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_ready_endpoint():
    """Test readiness check."""
    response = client.get("/ready")
    assert response.status_code in [200, 503]
    data = response.json()
    assert data["status"] in ["ready", "not_ready"]


def test_worker_health_status():
    """Test worker health status endpoint."""
    response = client.get("/workers/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "total_workers" in data
    assert "active_workers" in data


def test_request_id_header():
    """Test that request ID is added to response headers."""
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
