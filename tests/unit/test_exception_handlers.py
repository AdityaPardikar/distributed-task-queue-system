"""Tests for global exception handlers registered in main.py"""

import pytest
from fastapi import APIRouter, HTTPException
from fastapi.testclient import TestClient


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #


def _add_test_routes(app):
    """Attach ephemeral routes used only by these tests."""
    router = APIRouter(prefix="/test-exc")

    @router.get("/http-error")
    async def raise_http():
        raise HTTPException(status_code=404, detail="Not found – test")

    @router.get("/unhandled-error")
    async def raise_unhandled():
        raise RuntimeError("Boom – test")

    @router.post("/validation-error")
    async def require_body(payload: dict):
        return payload

    app.include_router(router)


# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #


@pytest.fixture()
def exc_client(db):
    """Test client that also has the ephemeral error routes."""
    from src.api.main import app
    from src.db.session import get_db

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    _add_test_routes(app)

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


# ------------------------------------------------------------------ #
# Tests                                                                #
# ------------------------------------------------------------------ #


class TestHTTPExceptionHandler:
    def test_returns_json_envelope(self, exc_client):
        r = exc_client.get("/test-exc/http-error")
        assert r.status_code == 404
        body = r.json()
        assert body["error"] is True
        assert body["status_code"] == 404
        assert "Not found" in body["detail"]

    def test_404_missing_route(self, exc_client):
        r = exc_client.get("/this-route-does-not-exist-99")
        assert r.status_code == 404
        body = r.json()
        # FastAPI default 404 still returns JSON; our handler wraps it
        assert r.headers["content-type"].startswith("application/json")


class TestValidationExceptionHandler:
    def test_missing_body_returns_422(self, exc_client):
        # POST without a JSON body → RequestValidationError
        r = exc_client.post("/test-exc/validation-error", content="not-json")
        assert r.status_code == 422
        body = r.json()
        assert body["error"] is True
        assert body["status_code"] == 422
        assert "errors" in body


class TestUnhandledExceptionHandler:
    def test_returns_500_json_envelope(self, exc_client):
        r = exc_client.get("/test-exc/unhandled-error")
        assert r.status_code == 500
        body = r.json()
        assert body["error"] is True
        assert body["status_code"] == 500
        assert "Internal server error" in body["detail"]
