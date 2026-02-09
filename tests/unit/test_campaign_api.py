"""Unit tests for campaign API endpoints."""

import os
import pytest

# Set test environment before importing app
os.environ["APP_ENV"] = "test"

from src.api.schemas import CampaignCreate
from src.models import Base


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
