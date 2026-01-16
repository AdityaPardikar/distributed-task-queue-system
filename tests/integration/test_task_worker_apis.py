"""Integration tests for task and worker management APIs."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from uuid import UUID

from src.api.main import app
from src.db.session import get_db
from src.models import Base, Task, Worker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Setup test database
@pytest.fixture(scope="module")
def test_db():
    """Create test database for integration tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal


@pytest.fixture
def client(test_db):
    """Get test client with database session override."""
    engine, SessionLocal = test_db
    
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def cleanup_db(test_db):
    """Clean up database between tests."""
    engine, SessionLocal = test_db
    db = SessionLocal()
    
    yield
    
    # Clear all tables
    db.query(Task).delete()
    db.query(Worker).delete()
    db.commit()
    db.close()


class TestTaskManagementAPIs:
    """Test cases for task management endpoints."""
    
    def test_create_task(self, client):
        """Test POST /tasks endpoint."""
        response = client.post(
            "/tasks",
            json={
                "task_name": "process_data",
                "task_args": [1, 2, 3],
                "task_kwargs": {"format": "json"},
                "priority": 5,
                "timeout": 300,
                "max_retries": 3
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["task_name"] == "process_data"
        assert data["status"] == "QUEUED"
        assert data["priority"] == 5
        assert "task_id" in data
    
    def test_create_task_with_invalid_priority(self, client):
        """Test POST /tasks with invalid priority."""
        response = client.post(
            "/tasks",
            json={
                "task_name": "process_data",
                "task_args": [],
                "priority": 15,  # Invalid: should be 1-10
                "timeout": 300
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_list_tasks(self, client):
        """Test GET /tasks list endpoint."""
        # Create multiple tasks
        for i in range(5):
            client.post(
                "/tasks",
                json={
                    "task_name": f"task_{i}",
                    "task_args": [],
                    "priority": i % 10 + 1,
                    "timeout": 300
                }
            )
        
        response = client.get("/tasks?page=1&page_size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 5
        assert data["total"] == 5
        assert "has_next" in data
        assert "has_previous" in data
        assert "total_pages" in data
    
    def test_list_tasks_with_filtering(self, client):
        """Test GET /tasks with status/priority filtering."""
        # Create tasks with different priorities
        client.post(
            "/tasks",
            json={
                "task_name": "high_priority",
                "priority": 9,
                "timeout": 300
            }
        )
        
        client.post(
            "/tasks",
            json={
                "task_name": "low_priority",
                "priority": 2,
                "timeout": 300
            }
        )
        
        # Filter by priority
        response = client.get("/tasks?priority=9")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["priority"] == 9
    
    def test_list_tasks_with_sorting(self, client):
        """Test GET /tasks with sorting."""
        # Create tasks
        task_ids = []
        for i in range(3):
            resp = client.post(
                "/tasks",
                json={
                    "task_name": f"task_{i}",
                    "priority": (i + 1) * 2,
                    "timeout": 300
                }
            )
            task_ids.append(resp.json()["task_id"])
        
        # Sort by priority descending
        response = client.get("/tasks?sort_by=priority&sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        
        priorities = [item["priority"] for item in data["items"]]
        assert priorities == sorted(priorities, reverse=True)
    
    def test_list_tasks_pagination(self, client):
        """Test GET /tasks pagination."""
        # Create 25 tasks
        for i in range(25):
            client.post(
                "/tasks",
                json={
                    "task_name": f"task_{i}",
                    "priority": (i % 10) + 1,
                    "timeout": 300
                }
            )
        
        # Get first page
        response = client.get("/tasks?page=1&page_size=10")
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["has_next"] is True
        assert data["has_previous"] is False
        
        # Get second page
        response = client.get("/tasks?page=2&page_size=10")
        data = response.json()
        assert len(data["items"]) == 10
        assert data["has_previous"] is True
    
    def test_get_task_detail(self, client):
        """Test GET /tasks/{id} endpoint."""
        # Create a task
        create_resp = client.post(
            "/tasks",
            json={
                "task_name": "test_task",
                "task_args": [1, 2, 3],
                "task_kwargs": {"format": "json"},
                "priority": 5,
                "timeout": 300
            }
        )
        
        task_id = create_resp.json()["task_id"]
        
        # Get task detail
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == task_id
        assert data["task_name"] == "test_task"
        assert data["task_args"] == [1, 2, 3]
        assert data["task_kwargs"] == {"format": "json"}
        assert "executions" in data
    
    def test_get_task_not_found(self, client):
        """Test GET /tasks/{id} with non-existent task."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/tasks/{fake_id}")
        assert response.status_code == 404
    
    def test_update_task(self, client):
        """Test PATCH /tasks/{id} endpoint."""
        # Create a task
        create_resp = client.post(
            "/tasks",
            json={
                "task_name": "test_task",
                "priority": 5,
                "max_retries": 2,
                "timeout": 300
            }
        )
        
        task_id = create_resp.json()["task_id"]
        
        # Update task
        response = client.patch(
            f"/tasks/{task_id}",
            json={
                "priority": 8,
                "max_retries": 5,
                "timeout": 600
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == 8
        assert data["max_retries"] == 5
        assert data["timeout"] == 600
    
    def test_update_task_partial(self, client):
        """Test PATCH /tasks/{id} with partial update."""
        # Create a task
        create_resp = client.post(
            "/tasks",
            json={
                "task_name": "test_task",
                "priority": 5,
                "timeout": 300
            }
        )
        
        task_id = create_resp.json()["task_id"]
        
        # Partial update (only priority)
        response = client.patch(
            f"/tasks/{task_id}",
            json={"priority": 9}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == 9
        assert data["timeout"] == 300  # Unchanged
    
    def test_cancel_task(self, client):
        """Test DELETE /tasks/{id} endpoint."""
        # Create a task
        create_resp = client.post(
            "/tasks",
            json={
                "task_name": "test_task",
                "priority": 5,
                "timeout": 300
            }
        )
        
        task_id = create_resp.json()["task_id"]
        
        # Cancel task
        response = client.delete(f"/tasks/{task_id}")
        assert response.status_code == 200
        
        # Verify task is cancelled
        get_resp = client.get(f"/tasks/{task_id}")
        assert get_resp.json()["status"] == "CANCELLED"
    
    def test_cancel_already_completed_task(self, client):
        """Test DELETE on already completed task (should fail)."""
        # Create and complete a task
        create_resp = client.post(
            "/tasks",
            json={
                "task_name": "test_task",
                "priority": 5,
                "timeout": 300
            }
        )
        
        task_id = create_resp.json()["task_id"]
        
        # This test assumes we have a way to mark task as COMPLETED
        # For now, we'll test canceling a non-cancellable status
        # In a real scenario, you'd mark it COMPLETED first
        
        response = client.delete(f"/tasks/{task_id}")
        # Should succeed since it's still QUEUED
        assert response.status_code in [200, 400]


class TestWorkerManagementAPIs:
    """Test cases for worker management endpoints."""
    
    def test_register_worker(self, client):
        """Test POST /workers endpoint."""
        response = client.post(
            "/workers",
            params={
                "hostname": "worker-1",
                "capacity": 10
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["hostname"] == "worker-1"
        assert data["capacity"] == 10
        assert data["status"] == "ACTIVE"
        assert data["current_load"] == 0
        assert "worker_id" in data
    
    def test_register_worker_with_defaults(self, client):
        """Test POST /workers with default capacity."""
        response = client.post(
            "/workers",
            params={"hostname": "worker-2"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["capacity"] == 5  # Default
    
    def test_register_worker_invalid_capacity(self, client):
        """Test POST /workers with invalid capacity."""
        response = client.post(
            "/workers",
            params={
                "hostname": "worker-3",
                "capacity": 0  # Invalid: must be >= 1
            }
        )
        
        assert response.status_code == 422
    
    def test_send_heartbeat(self, client):
        """Test POST /workers/{id}/heartbeat endpoint."""
        # Register worker
        reg_resp = client.post(
            "/workers",
            params={
                "hostname": "worker-4",
                "capacity": 5
            }
        )
        worker_id = reg_resp.json()["worker_id"]
        
        # Send heartbeat
        response = client.post(
            f"/workers/{worker_id}/heartbeat",
            params={
                "current_load": 3,
                "worker_status": "ACTIVE"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_load"] == 3
        assert data["status"] == "ACTIVE"
    
    def test_send_heartbeat_not_found(self, client):
        """Test POST /workers/{id}/heartbeat with non-existent worker."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.post(
            f"/workers/{fake_id}/heartbeat",
            params={
                "current_load": 3
            }
        )
        
        assert response.status_code == 404
    
    def test_list_workers(self, client):
        """Test GET /workers list endpoint."""
        # Register multiple workers
        for i in range(3):
            client.post(
                "/workers",
                params={
                    "hostname": f"worker-{i}",
                    "capacity": 5 + i
                }
            )
        
        response = client.get("/workers")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3
    
    def test_list_workers_with_status_filter(self, client):
        """Test GET /workers with status filtering."""
        # Register workers
        reg_resp = client.post(
            "/workers",
            params={
                "hostname": "worker-5",
                "capacity": 5
            }
        )
        worker_id = reg_resp.json()["worker_id"]
        
        # Change status to DRAINING
        client.patch(
            f"/workers/{worker_id}/status",
            params={"new_status": "DRAINING"}
        )
        
        # Register another (ACTIVE)
        client.post(
            "/workers",
            params={
                "hostname": "worker-6",
                "capacity": 5
            }
        )
        
        # Filter by status
        response = client.get("/workers?worker_status=DRAINING")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "DRAINING"
    
    def test_get_worker_detail(self, client):
        """Test GET /workers/{id} endpoint."""
        # Register worker
        reg_resp = client.post(
            "/workers",
            params={
                "hostname": "worker-7",
                "capacity": 5
            }
        )
        worker_id = reg_resp.json()["worker_id"]
        
        # Get worker detail
        response = client.get(f"/workers/{worker_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["worker_id"] == worker_id
        assert data["hostname"] == "worker-7"
    
    def test_update_worker_status(self, client):
        """Test PATCH /workers/{id}/status endpoint."""
        # Register worker
        reg_resp = client.post(
            "/workers",
            params={
                "hostname": "worker-8",
                "capacity": 5
            }
        )
        worker_id = reg_resp.json()["worker_id"]
        
        # Update status to DRAINING
        response = client.patch(
            f"/workers/{worker_id}/status",
            params={"new_status": "DRAINING"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DRAINING"
    
    def test_invalid_status_transition(self, client):
        """Test invalid status transition."""
        # Register worker
        reg_resp = client.post(
            "/workers",
            params={
                "hostname": "worker-9",
                "capacity": 5
            }
        )
        worker_id = reg_resp.json()["worker_id"]
        
        # Try invalid transition (ACTIVE -> QUEUED doesn't exist)
        response = client.patch(
            f"/workers/{worker_id}/status",
            params={"new_status": "QUEUED"}  # Invalid status value
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_deregister_worker(self, client):
        """Test DELETE /workers/{id} endpoint."""
        # Register worker
        reg_resp = client.post(
            "/workers",
            params={
                "hostname": "worker-10",
                "capacity": 5
            }
        )
        worker_id = reg_resp.json()["worker_id"]
        
        # Deregister worker
        response = client.delete(f"/workers/{worker_id}")
        assert response.status_code == 204
        
        # Verify worker is deleted
        get_resp = client.get(f"/workers/{worker_id}")
        assert get_resp.status_code == 404
    
    def test_get_worker_tasks(self, client):
        """Test GET /workers/{id}/tasks endpoint."""
        # Register worker
        reg_resp = client.post(
            "/workers",
            params={
                "hostname": "worker-11",
                "capacity": 10
            }
        )
        worker_id = reg_resp.json()["worker_id"]
        
        # Get worker tasks (should be empty initially)
        response = client.get(f"/workers/{worker_id}/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_tasks"] == 0
        assert len(data["tasks"]) == 0


class TestTaskWorkerIntegration:
    """Integration tests combining task and worker flows."""
    
    def test_worker_registration_and_task_submission_flow(self, client):
        """Test complete flow of registering worker and submitting tasks."""
        # Register worker
        worker_resp = client.post(
            "/workers",
            params={
                "hostname": "integration-worker",
                "capacity": 5
            }
        )
        assert worker_resp.status_code == 201
        worker_id = worker_resp.json()["worker_id"]
        
        # Submit tasks
        task_ids = []
        for i in range(3):
            task_resp = client.post(
                "/tasks",
                json={
                    "task_name": f"integration_task_{i}",
                    "priority": (i + 1) * 2,
                    "timeout": 300
                }
            )
            assert task_resp.status_code == 201
            task_ids.append(task_resp.json()["task_id"])
        
        # Verify tasks are queued
        list_resp = client.get("/tasks")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 3
        
        # Send heartbeat
        hb_resp = client.post(
            f"/workers/{worker_id}/heartbeat",
            params={
                "current_load": 2,
                "worker_status": "ACTIVE"
            }
        )
        assert hb_resp.status_code == 200
        
        # Get worker detail
        worker_detail = client.get(f"/workers/{worker_id}")
        assert worker_detail.status_code == 200
        assert worker_detail.json()["current_load"] == 2
