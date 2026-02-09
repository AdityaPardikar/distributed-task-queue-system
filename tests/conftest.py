"""Pytest configuration and fixtures"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Set test environment
os.environ["APP_ENV"] = "test"

# Import all models so they're registered with Base.metadata
from src.models import (
    Base,
    Task,
   Worker,
    Campaign,
    TaskResult,
    TaskLog,
    TaskExecution,
    EmailRecipient,
    EmailTemplate,
    CampaignTask,
    DeadLetterQueue,
    Alert,
)


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine""" 
    # Use StaticPool to share one connection across all threads/tests
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session")
def TestSessionLocal(test_engine):
    """Create session factory for test database"""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db(TestSessionLocal):
    """Get database session for test"""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db):
    """Get test client with overridden database dependency"""
    from fastapi.testclient import TestClient

    from src.api.main import app
    from src.db.session import get_db

    # Override the get_db dependency to use test database
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_app_startup(client):
    """Test app startup"""
    response = client.get("/health")
    assert response.status_code == 200
