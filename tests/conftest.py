"""Pytest configuration and fixtures"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import Base


@pytest.fixture(scope="session")
def test_db():
    """Create test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@pytest.fixture(scope="function")
def db(test_db):
    """Get database session for test"""
    test_db.begin_nested()
    yield test_db
    test_db.rollback()


@pytest.fixture
def client():
    """Get test client"""
    from fastapi.testclient import TestClient

    from src.api.main import app

    return TestClient(app)


@pytest.mark.asyncio
async def test_app_startup(client):
    """Test app startup"""
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
