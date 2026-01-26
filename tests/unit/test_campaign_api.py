"""Unit tests for campaign API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.api.schemas import CampaignCreate
from src.db.session import get_db
from src.models import Base


TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _override_get_db(test_db):
    def _override():
        try:
            yield test_db
        finally:
            pass

    return _override


@pytest.fixture
def test_db():
    """Create test database."""
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(test_db):
    """Create test client with DB override."""
    app.dependency_overrides[get_db] = _override_get_db(test_db)
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_campaign_success(client):
    """POST /api/v1/campaigns creates a campaign."""
    payload = {
        "name": "Welcome Campaign",
        "template_subject": "Welcome {{name}}",
        "template_body": "Hello {{name}}!",
        "template_variables": {"name": "Friend"},
        "rate_limit_per_minute": 150,
    }

    response = client.post("/api/v1/campaigns", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Welcome Campaign"
    assert data["status"] == "DRAFT"
    assert data["template_subject"] == "Welcome {{name}}"
    assert data["rate_limit_per_minute"] == 150


def test_list_campaigns_returns_items(client):
    """GET /api/v1/campaigns returns created campaigns."""
    for idx in range(2):
        payload = CampaignCreate(
            name=f"Campaign {idx}",
            template_subject="Subject",
            template_body="Body",
            template_variables={},
        ).model_dump()
        client.post("/api/v1/campaigns", json=payload)

    response = client.get("/api/v1/campaigns?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


def test_update_campaign_status(client):
    """PATCH /api/v1/campaigns/{id} updates fields."""
    create_resp = client.post(
        "/api/v1/campaigns",
        json={
            "name": "Campaign to Update",
            "template_subject": "Subject",
            "template_body": "Body",
            "template_variables": {},
        },
    )
    campaign_id = create_resp.json()["campaign_id"]

    patch_resp = client.patch(
        f"/api/v1/campaigns/{campaign_id}",
        json={"status": "SCHEDULED", "rate_limit_per_minute": 200},
    )

    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["status"] == "SCHEDULED"
    assert updated["rate_limit_per_minute"] == 200
