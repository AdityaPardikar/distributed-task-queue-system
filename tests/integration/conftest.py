"""Integration test configuration.

Provides shared fixtures for integration tests:
  • In-memory SQLite database with proper test isolation per function.
  • Redis mock via ``fakeredis`` when Redis is unavailable.
  • FastAPI ``TestClient`` pre-configured with DB + Redis overrides.
  • Automatic service-availability detection — tests that truly need
    a live Postgres / Redis are skipped when those services are down,
    but all *database-only* tests can still run via SQLite.

Usage
-----
Tests that import ``client`` or ``db`` from this conftest automatically
get a clean, isolated environment.
"""

from __future__ import annotations

import os
import socket
from datetime import datetime, timezone
from typing import Generator
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure test environment
os.environ.setdefault("APP_ENV", "test")

from src.models import Base, Task, Worker, Campaign  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Service availability helpers
# ─────────────────────────────────────────────────────────────────────────────

def _is_service_available(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a network service is reachable."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False


_PG_AVAILABLE = _is_service_available("localhost", 5432)
_REDIS_AVAILABLE = _is_service_available("localhost", 6379)


def pytest_collection_modifyitems(config, items):
    """Skip integration tests that need live services when unavailable.

    Tests are only skipped if they carry the ``@pytest.mark.requires_postgres``
    or ``@pytest.mark.requires_redis`` markers *and* the service isn't running.
    All other integration tests run against the in-memory SQLite DB.
    """
    for item in items:
        if "integration" not in str(item.fspath):
            continue

        if "requires_postgres" in [m.name for m in item.iter_markers()] and not _PG_AVAILABLE:
            item.add_marker(pytest.mark.skip(reason="PostgreSQL not available on localhost:5432"))

        if "requires_redis" in [m.name for m in item.iter_markers()] and not _REDIS_AVAILABLE:
            item.add_marker(pytest.mark.skip(reason="Redis not available on localhost:6379"))


# ─────────────────────────────────────────────────────────────────────────────
# Database fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def integration_engine():
    """Create a session-scoped in-memory SQLite engine.

    ``StaticPool`` ensures a single connection is shared across threads
    (SQLite limitation with ``:memory:``).  Foreign-key enforcement is
    turned on via a ``connect`` event.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session")
def IntegrationSessionFactory(integration_engine):
    """Session-scoped sessionmaker bound to the test engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=integration_engine)


@pytest.fixture()
def db(IntegrationSessionFactory) -> Generator[Session, None, None]:
    """Function-scoped DB session with automatic rollback for isolation."""
    session: Session = IntegrationSessionFactory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ─────────────────────────────────────────────────────────────────────────────
# Redis mock fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def mock_redis():
    """Provide a lightweight in-process Redis mock.

    If ``fakeredis`` is installed it will be used for high-fidelity
    simulation; otherwise a ``MagicMock`` is returned so tests that
    don't exercise Redis deeply still pass.
    """
    try:
        import fakeredis
        server = fakeredis.FakeServer()
        client = fakeredis.FakeStrictRedis(server=server, decode_responses=True)
        yield client
        client.flushall()
    except ImportError:
        mock = MagicMock()
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = 1
        mock.hgetall.return_value = {}
        mock.hset.return_value = 1
        mock.rpush.return_value = 1
        mock.llen.return_value = 0
        mock.blpop.return_value = None
        mock.sadd.return_value = 1
        mock.smembers.return_value = set()
        mock.exists.return_value = 0
        mock.expire.return_value = True
        mock.incr.return_value = 1
        mock.pipeline.return_value = mock  # pipeline returns self
        mock.execute.return_value = []
        yield mock


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI TestClient fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def client(db, mock_redis) -> Generator[TestClient, None, None]:
    """Pre-configured ``TestClient`` with DB and Redis overrides."""
    from src.api.main import app
    from src.db.session import get_db

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    with patch("src.cache.client.get_redis_client", return_value=mock_redis):
        with TestClient(app, raise_server_exceptions=False) as tc:
            yield tc

    app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Test data factories
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def sample_workers(db) -> list[Worker]:
    """Create 3 test workers and commit them."""
    workers: list[Worker] = []
    for i in range(3):
        w = Worker(
            hostname=f"integration-worker-{i}",
            capacity=10,
            current_load=0,
            status="ACTIVE",
            last_heartbeat=datetime.now(timezone.utc),
        )
        db.add(w)
        workers.append(w)
    db.commit()
    for w in workers:
        db.refresh(w)
    return workers


@pytest.fixture()
def sample_tasks(db) -> list[Task]:
    """Create a set of tasks with mixed statuses."""
    statuses = ["PENDING", "RUNNING", "COMPLETED", "FAILED"]
    priorities = [1, 3, 5, 8]
    tasks: list[Task] = []
    for i, (st, pr) in enumerate(zip(statuses, priorities)):
        t = Task(
            task_name=f"integration-task-{i}",
            task_args=[i],
            task_kwargs={"index": i},
            priority=pr,
            status=st,
            max_retries=3,
            timeout_seconds=120,
        )
        db.add(t)
        tasks.append(t)
    db.commit()
    for t in tasks:
        db.refresh(t)
    return tasks
