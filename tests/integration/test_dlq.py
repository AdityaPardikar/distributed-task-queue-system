"""Integration tests for Dead Letter Queue operations."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.db.session import get_db
from src.models import Base, Task


class FakeBroker:
    """In-memory fake broker for testing DLQ endpoints."""

    def __init__(self):
        self.dlq = {}
        self.queue = []

    # No-op enqueue just records the task id
    def enqueue_task(self, task_id: str, priority: int = 5, task_data=None):
        self.queue.append(task_id)
        return True

    def schedule_task(self, task_id: str, scheduled_time: int):
        return True

    def move_to_dlq(self, task_id: str, failure_reason: str, task_data=None):
        self.dlq[task_id] = {
            "failure_reason": failure_reason,
            "task_id": task_id,
            "task_data": task_data or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        return True

    def list_dlq(self, start: int = 0, stop: int = -1):
        items = list(self.dlq.values())
        if stop != -1:
            return items[start:stop]
        return items[start:]

    def get_dlq_meta(self, task_id: str):
        return self.dlq.get(task_id)

    def remove_from_dlq(self, task_id: str):
        self.dlq.pop(task_id, None)
        return True


@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal


@pytest.fixture
def fake_broker(monkeypatch):
    broker = FakeBroker()
    monkeypatch.setattr("src.api.routes.tasks.get_broker", lambda: broker)
    return broker


@pytest.fixture
def client(test_db, fake_broker):
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
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def cleanup_db(test_db):
    engine, SessionLocal = test_db
    db = SessionLocal()
    yield
    db.query(Task).delete()
    db.commit()
    db.close()


def test_dlq_list_and_move(client, fake_broker):
    # Create a task
    resp = client.post(
        "/tasks",
        json={
            "task_name": "process_data",
            "priority": 5,
            "timeout_seconds": 120
        }
    )
    assert resp.status_code == 201
    task_id = resp.json()["task_id"]

    # Move to DLQ via broker
    fake_broker.move_to_dlq(task_id, "Max retries exceeded", {"task_name": "process_data"})

    # List DLQ
    dlq_resp = client.get("/tasks/dlq")
    assert dlq_resp.status_code == 200
    payload = dlq_resp.json()
    assert payload["total"] == 1
    assert payload["items"][0]["task_id"] == task_id


def test_dlq_retry(client, fake_broker):
    # Create a task
    resp = client.post(
        "/tasks",
        json={
            "task_name": "send_email",
            "priority": 7,
            "timeout_seconds": 60
        }
    )
    task_id = resp.json()["task_id"]

    fake_broker.move_to_dlq(task_id, "Failed after retries", {"task_name": "send_email"})

    retry_resp = client.post(f"/tasks/dlq/{task_id}/retry")
    assert retry_resp.status_code == 200
    data = retry_resp.json()
    assert data["task_id"] == task_id
    assert data["status"] == "PENDING"
    # Ensure removed from DLQ
    dlq_resp = client.get("/tasks/dlq")
    assert dlq_resp.json()["total"] == 0


def test_dlq_discard(client, fake_broker):
    resp = client.post(
        "/tasks",
        json={
            "task_name": "cleanup",
            "priority": 3,
            "timeout_seconds": 45
        }
    )
    task_id = resp.json()["task_id"]

    fake_broker.move_to_dlq(task_id, "Permanent failure")

    discard_resp = client.post(f"/tasks/dlq/{task_id}/discard")
    assert discard_resp.status_code == 204

    # Ensure no entries
    dlq_resp = client.get("/tasks/dlq")
    assert dlq_resp.json()["total"] == 0
