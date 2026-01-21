"""Integration tests for workflows and batch operations."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.db.session import get_db
from src.models import Base, Task


class DummyBroker:
    def enqueue_task(self, task_id: str, priority: int = 5, task_data=None):
        return True


@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal


@pytest.fixture
def client(test_db, monkeypatch):
    engine, SessionLocal = test_db

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    broker = DummyBroker()
    monkeypatch.setattr("src.api.routes.workflows.get_broker", lambda: broker)
    monkeypatch.setattr("src.core.workflow_engine.get_broker", lambda: broker)

    yield client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def cleanup_db(test_db):
    engine, SessionLocal = test_db
    db = SessionLocal()
    yield
    db.query(Task).delete()
    db.commit()
    db.close()


def test_create_simple_workflow(client):
    """Test creating a workflow with sequential dependencies."""
    workflow = {
        "workflow_name": "test_pipeline",
        "tasks": [
            {"name": "task_a", "task_name": "step_a", "priority": 5},
            {"name": "task_b", "task_name": "step_b", "priority": 5},
            {"name": "task_c", "task_name": "step_c", "priority": 5},
        ],
        "dependencies": {
            "task_b": ["task_a"],
            "task_c": ["task_b"],
        },
    }

    response = client.post("/api/v1/workflows", json=workflow)
    assert response.status_code == 201
    data = response.json()
    assert data["workflow_name"] == "test_pipeline"
    assert data["total_tasks"] == 3
    assert len(data["task_ids"]) == 3


def test_create_parallel_workflow(client):
    """Test creating a workflow with parallel execution."""
    workflow = {
        "workflow_name": "parallel_pipeline",
        "tasks": [
            {"name": "fetch", "task_name": "fetch_data", "priority": 8},
            {"name": "process_a", "task_name": "process_chunk", "priority": 5},
            {"name": "process_b", "task_name": "process_chunk", "priority": 5},
            {"name": "aggregate", "task_name": "aggregate_results", "priority": 7},
        ],
        "dependencies": {
            "process_a": ["fetch"],
            "process_b": ["fetch"],
            "aggregate": ["process_a", "process_b"],
        },
    }

    response = client.post("/api/v1/workflows", json=workflow)
    assert response.status_code == 201
    data = response.json()
    assert data["total_tasks"] == 4


def test_workflow_invalid_dependency(client):
    """Test workflow creation fails with invalid dependency."""
    workflow = {
        "workflow_name": "bad_workflow",
        "tasks": [
            {"name": "task_a", "task_name": "step_a", "priority": 5},
        ],
        "dependencies": {
            "task_b": ["task_a"],  # task_b doesn't exist
        },
    }

    response = client.post("/api/v1/workflows", json=workflow)
    assert response.status_code == 400
    assert "not found in tasks" in response.json()["detail"]


def test_batch_create_tasks(client):
    """Test batch task creation."""
    batch = {
        "tasks": [
            {"name": f"task_{i}", "task_name": "batch_job", "priority": 5}
            for i in range(10)
        ]
    }

    response = client.post("/api/v1/workflows/batch", json=batch)
    assert response.status_code == 201
    data = response.json()
    assert data["total_created"] == 10
    assert len(data["task_ids"]) == 10


def test_workflow_no_dependencies(client):
    """Test workflow with no dependencies (all parallel)."""
    workflow = {
        "workflow_name": "parallel_only",
        "tasks": [
            {"name": f"task_{i}", "task_name": "independent", "priority": 5}
            for i in range(5)
        ],
    }

    response = client.post("/api/v1/workflows", json=workflow)
    assert response.status_code == 201
    data = response.json()
    assert data["total_tasks"] == 5
