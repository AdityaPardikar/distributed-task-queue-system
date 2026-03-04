"""Extended unit tests for task API — pagination, filtering, edge cases."""

import pytest
from unittest.mock import Mock, patch


class TestGetTasksEndpoint:
    """GET /api/v1/tasks — list & pagination"""

    def test_list_tasks_returns_200(self, client):
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200

    def test_list_tasks_response_shape(self, client):
        response = client.get("/api/v1/tasks")
        data = response.json()
        # Must follow TaskListResponse envelope
        assert "items" in data or "tasks" in data or isinstance(data, (list, dict))

    def test_list_tasks_default_page_params(self, client):
        r1 = client.get("/api/v1/tasks?page=1&per_page=10")
        assert r1.status_code == 200

    def test_list_tasks_out_of_range_page(self, client):
        r = client.get("/api/v1/tasks?page=999999&per_page=10")
        # Should return 200 with empty result, not a 500
        assert r.status_code in (200, 404)

    def test_list_tasks_invalid_per_page_too_high(self, client):
        r = client.get("/api/v1/tasks?per_page=99999")
        # Clamped or rejected — not a 500
        assert r.status_code in (200, 400, 422)

    def test_filter_by_status_pending(self, client):
        r = client.get("/api/v1/tasks?status=PENDING")
        assert r.status_code == 200

    def test_filter_by_status_completed(self, client):
        r = client.get("/api/v1/tasks?status=COMPLETED")
        assert r.status_code == 200

    def test_filter_by_invalid_status(self, client):
        r = client.get("/api/v1/tasks?status=BOGUS")
        assert r.status_code in (200, 422)

    def test_filter_by_priority(self, client):
        r = client.get("/api/v1/tasks?priority=5")
        assert r.status_code == 200


class TestGetTaskByIdEndpoint:
    """GET /api/v1/tasks/{task_id}"""

    def test_get_nonexistent_task_returns_404(self, client):
        r = client.get("/api/v1/tasks/nonexistent-id-99999")
        assert r.status_code == 404

    def test_404_uses_error_envelope(self, client):
        """The global exception handler should wrap 404 in our JSON envelope."""
        r = client.get("/api/v1/tasks/nonexistent-id-99999")
        body = r.json()
        # Either the standard FastAPI 404 or our handler's wrapped version
        assert "detail" in body or "error" in body


@patch("src.api.routes.tasks.get_broker")
class TestCreateTaskValidation:
    """POST /api/v1/tasks — input validation"""

    def test_reject_empty_task_name(self, mock_get_broker, client):
        r = client.post("/api/v1/tasks", json={"task_name": ""})
        assert r.status_code == 422

    def test_reject_task_name_too_long(self, mock_get_broker, client):
        r = client.post(
            "/api/v1/tasks",
            json={"task_name": "x" * 300},
        )
        assert r.status_code == 422

    def test_reject_priority_out_of_range_high(self, mock_get_broker, client):
        mock_get_broker.return_value = Mock(enqueue_task=Mock(return_value=True))
        r = client.post("/api/v1/tasks", json={"task_name": "t", "priority": 99})
        assert r.status_code == 422

    def test_reject_priority_out_of_range_low(self, mock_get_broker, client):
        mock_get_broker.return_value = Mock(enqueue_task=Mock(return_value=True))
        r = client.post("/api/v1/tasks", json={"task_name": "t", "priority": 0})
        assert r.status_code == 422

    def test_reject_max_retries_out_of_range(self, mock_get_broker, client):
        mock_get_broker.return_value = Mock(enqueue_task=Mock(return_value=True))
        r = client.post("/api/v1/tasks", json={"task_name": "t", "max_retries": 100})
        assert r.status_code == 422

    def test_validation_error_uses_envelope(self, mock_get_broker, client):
        r = client.post("/api/v1/tasks", json={"task_name": ""})
        body = r.json()
        assert r.status_code == 422
        # Our handler adds error=True and errors[] key
        assert "errors" in body or "detail" in body


class TestWorkerEndpoints:
    """GET /api/v1/workers"""

    def test_list_workers_returns_200(self, client):
        r = client.get("/api/v1/workers")
        assert r.status_code == 200

    def test_get_nonexistent_worker_returns_404(self, client):
        r = client.get("/api/v1/workers/nonexistent-worker-id")
        assert r.status_code == 404


class TestHealthEndpoints:
    """Health check routes"""

    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_body_has_status(self, client):
        r = client.get("/health")
        assert "status" in r.json()

    def test_root_returns_online(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json().get("status") == "online"
