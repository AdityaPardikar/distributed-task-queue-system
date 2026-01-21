"""Integration tests for task dependencies and chains."""

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

    def schedule_task(self, task_id: str, scheduled_time: int):
        return True

    def add_task_dependency(self, parent_id: str, child_id: str):
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
    monkeypatch.setattr("src.api.routes.tasks.get_broker", lambda: broker)

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


def test_create_task_with_dependencies(client):
    # Create base task A
    resp_a = client.post(
        "/tasks",
        json={
            "task_name": "task_a",
            "priority": 5,
            "timeout_seconds": 120
        }
    )
    assert resp_a.status_code == 201
    task_a_id = resp_a.json()["task_id"]

    # Create dependent task B that depends on A
    resp_b = client.post(
        "/tasks",
        json={
            "task_name": "task_b",
            "priority": 5,
            "timeout_seconds": 120,
            "depends_on": [task_a_id]
        }
    )
    assert resp_b.status_code == 201
    task_b_id = resp_b.json()["task_id"]

    # Get dependencies for B
    dep_resp = client.get(f"/tasks/{task_b_id}/dependencies")
    assert dep_resp.status_code == 200
    data = dep_resp.json()
    assert data["total"] == 1
    assert data["dependencies"][0]["task_id"] == task_a_id

    # Get children for A
    children_resp = client.get(f"/tasks/{task_a_id}/children")
    assert children_resp.status_code == 200
    children = children_resp.json()
    assert children["total"] == 1
    assert children["children"][0]["task_id"] == task_b_id


def test_multiple_dependencies(client):
    # Create tasks X and Y
    resp_x = client.post(
        "/tasks",
        json={
            "task_name": "task_x",
            "priority": 5,
            "timeout_seconds": 120
        }
    )
    task_x_id = resp_x.json()["task_id"]

    resp_y = client.post(
        "/tasks",
        json={
            "task_name": "task_y",
            "priority": 5,
            "timeout_seconds": 120
        }
    )
    task_y_id = resp_y.json()["task_id"]

    # Task Z depends on both X and Y
    resp_z = client.post(
        "/tasks",
        json={
            "task_name": "task_z",
            "priority": 7,
            "timeout_seconds": 200,
            "depends_on": [task_x_id, task_y_id]
        }
    )
    task_z_id = resp_z.json()["task_id"]

    dep_resp = client.get(f"/tasks/{task_z_id}/dependencies")
    assert dep_resp.status_code == 200
    data = dep_resp.json()
    assert data["total"] == 2
    dep_ids = {item["task_id"] for item in data["dependencies"]}
    assert dep_ids == {task_x_id, task_y_id}

    # Children listing for X should include Z
    children_resp = client.get(f"/tasks/{task_x_id}/children")
    assert children_resp.status_code == 200
    assert any(c["task_id"] == task_z_id for c in children_resp.json()["children"])
