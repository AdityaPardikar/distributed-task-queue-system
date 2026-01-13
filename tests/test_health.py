"""Health check tests"""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_info_endpoint(client):
    """Test info endpoint"""
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
