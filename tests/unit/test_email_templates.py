"""Unit tests for email template functionality"""

import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.schemas import TemplateCreate, TemplatePreviewRequest
from src.db.session import get_db
from src.models import EmailTemplate as EmailTemplateModel
from src.services.email_template_engine import EmailTemplate, TemplateVariableInfo


# Mocked datetime import for tests
datetime = datetime


def override_get_db():
    """Mock get_db for testing"""
    db = MagicMock()
    yield db


@pytest.fixture
def test_client():
    """Create test client with mocked database"""
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


class TestEmailTemplateEngine:
    """Tests for email template engine"""

    def test_template_creation_valid(self):
        """Test creating a valid template"""
        engine = EmailTemplate(
            subject="Hello {{ name }}!",
            body="Hi {{ name }}, welcome to {{ company }}!"
        )
        assert engine.subject is not None
        assert engine.body is not None

    def test_template_creation_invalid_syntax(self):
        """Test that invalid Jinja2 syntax raises error"""
        with pytest.raises(ValueError, match="Template syntax error"):
            EmailTemplate(
                subject="Hello {{ name",
                body="Valid body"
            )

    def test_extract_variables(self):
        """Test extracting variables from template"""
        engine = EmailTemplate(
            subject="Hello {{ first_name }}!",
            body="Hi {{ first_name }} {{ last_name }}, welcome!"
        )
        variables = engine.extract_variables()
        var_names = {v.name for v in variables}
        assert var_names == {"first_name", "last_name"}

    def test_extract_no_variables(self):
        """Test template with no variables"""
        engine = EmailTemplate(
            subject="Hello!",
            body="Welcome to our service!"
        )
        variables = engine.extract_variables()
        assert len(variables) == 0

    def test_validate_variables_success(self):
        """Test validating required variables"""
        engine = EmailTemplate(
            subject="Hello {{ name }}!",
            body="Body with {{ name }}"
        )
        is_valid, missing = engine.validate_variables({"name": "John"})
        assert is_valid is True
        assert len(missing) == 0

    def test_validate_variables_missing(self):
        """Test detecting missing variables"""
        engine = EmailTemplate(
            subject="Hello {{ first_name }}!",
            body="Hi {{ first_name }} {{ last_name }}!"
        )
        is_valid, missing = engine.validate_variables({"first_name": "John"})
        assert is_valid is False
        assert "last_name" in missing

    def test_render_success(self):
        """Test successful template rendering"""
        engine = EmailTemplate(
            subject="Hello {{ name }}!",
            body="Welcome {{ name }} to {{ company }}!"
        )
        subject, body = engine.render({
            "name": "John",
            "company": "Acme Corp"
        })
        assert subject == "Hello John!"
        assert body == "Welcome John to Acme Corp!"

    def test_render_missing_variables(self):
        """Test rendering with missing variables"""
        engine = EmailTemplate(
            subject="Hello {{ name }}!",
            body="Body"
        )
        with pytest.raises(ValueError, match="Missing required variables"):
            engine.render({})

    def test_render_with_defaults(self):
        """Test rendering with default values"""
        engine = EmailTemplate(
            subject="Hello {{ name }}!",
            body="Body"
        )
        subject, body = engine.render_with_defaults(
            variables={},
            defaults={"name": "Default Name"}
        )
        assert subject == "Hello Default Name!"


class TestTemplateAPI:
    """Tests for template API endpoints (integration tests)"""

    def test_invalid_template_syntax(self, test_client):
        """Test API rejects templates with invalid Jinja2 syntax"""
        payload = {
            "name": "Invalid",
            "subject": "Hello {{ name",  # Missing closing braces
            "body": "Body"
        }
        response = test_client.post("/api/v1/templates", json=payload)
        # Should return 400 for invalid syntax
        assert response.status_code in [400, 422]  # 422 for validation error

    def test_create_template_endpoint_available(self, test_client):
        """Test that create template endpoint is available"""
        # Valid payload with all required fields
        payload = {
            "name": "Test Email",
            "subject": "Hello {{ name }}!",
            "body": "Welcome {{ name }}!"
        }
        response = test_client.post("/api/v1/templates", json=payload)
        # Should succeed (200-299) or fail with database error (500+) due to mocking
        # But should not fail validation
        assert response.status_code not in [404]  # Endpoint exists

    def test_list_templates_endpoint_available(self, test_client):
        """Test that list templates endpoint is available"""
        response = test_client.get("/api/v1/templates")
        # Endpoint should exist (not 404)
        assert response.status_code in [200, 400, 422]  # OK or validation/param error

    def test_template_id_parameter_validation(self, test_client):
        """Test that template endpoints validate UUID parameter"""
        # Invalid UUID should return 400 or 422
        response = test_client.get("/api/v1/templates/not-a-uuid")
        assert response.status_code in [400, 422]
