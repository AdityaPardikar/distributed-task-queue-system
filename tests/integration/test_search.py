"""Integration tests for task search and filtering."""

import pytest
from datetime import datetime, timedelta
from fastapi import status
from fastapi.testclient import TestClient

from src.api.main import app
from src.models import Task
from src.db.session import SessionLocal
from src.services.task_search import TaskFilter, FilterPreset

client = TestClient(app)


class TestTaskSearch:
    """Test task search and filtering functionality."""

    def test_simple_search(self):
        """Test simple task search."""
        response = client.get("/api/v1/search/tasks?status=PENDING")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "page" in data

    def test_search_with_pagination(self):
        """Test search with pagination."""
        response = client.get("/api/v1/search/tasks?limit=50&offset=0")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["limit"] == 50
        assert data["offset"] == 0
        assert data["page"] == 1

    def test_search_with_multiple_filters(self):
        """Test search with multiple filter criteria."""
        response = client.get(
            "/api/v1/search/tasks?status=COMPLETED&priority=5&limit=100"
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        for task in data["tasks"]:
            if data["total"] > 0:
                assert task["status"] in ["COMPLETED", None]  # May be filtered

    def test_search_with_date_range(self):
        """Test search with date range filters."""
        now = datetime.utcnow()
        before = (now - timedelta(days=7)).isoformat()
        after = now.isoformat()
        
        response = client.get(
            f"/api/v1/search/tasks?created_before={after}&created_after={before}"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_fulltext_search(self):
        """Test full-text search functionality."""
        response = client.get("/api/v1/search/tasks?search=email")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data["tasks"], list)

    def test_search_ordering(self):
        """Test search result ordering."""
        response1 = client.get("/api/v1/search/tasks?order_by=created_at&order_desc=true")
        assert response1.status_code == status.HTTP_200_OK
        
        response2 = client.get("/api/v1/search/tasks?order_by=created_at&order_desc=false")
        assert response2.status_code == status.HTTP_200_OK

    def test_get_filter_presets(self):
        """Test getting available filter presets."""
        response = client.get("/api/v1/search/presets")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "presets" in data
        assert isinstance(data["presets"], list)
        assert len(data["presets"]) > 0

    def test_apply_filter_preset(self):
        """Test applying a filter preset."""
        response = client.get("/api/v1/search/presets/failed_today")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "tasks" in data
        assert "total" in data

    def test_apply_invalid_preset(self):
        """Test applying non-existent preset."""
        response = client.get("/api/v1/search/presets/nonexistent_preset")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["total"] == 0

    def test_export_to_csv(self):
        """Test exporting tasks as CSV."""
        response = client.get("/api/v1/search/tasks/export/csv")
        assert response.status_code == status.HTTP_200_OK
        
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "Content-Disposition" in response.headers

    def test_bulk_retry_action(self):
        """Test bulk retry action on filtered tasks."""
        response = client.post(
            "/api/v1/search/tasks/bulk-action?action=retry&status=FAILED"
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["action"] == "retry"
        assert "affected_tasks" in data

    def test_bulk_cancel_action(self):
        """Test bulk cancel action on filtered tasks."""
        response = client.post(
            "/api/v1/search/tasks/bulk-action?action=cancel&status=PENDING"
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["action"] == "cancel"

    def test_bulk_priority_boost_action(self):
        """Test bulk priority boost action."""
        response = client.post(
            "/api/v1/search/tasks/bulk-action?action=priority_boost&new_priority=9"
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["action"] == "priority_boost"

    def test_invalid_query_parameters(self):
        """Test with invalid query parameters."""
        response = client.get("/api/v1/search/tasks?priority=11")  # Invalid priority
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        response = client.get("/api/v1/search/tasks?limit=10001")  # Exceeds max
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_result_structure(self):
        """Test that search results have correct structure."""
        response = client.get("/api/v1/search/tasks?limit=1")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        if data["tasks"]:
            task = data["tasks"][0]
            assert "task_id" in task
            assert "task_name" in task
            assert "status" in task
            assert "priority" in task
            assert "created_at" in task


class TestTaskFilterService:
    """Test TaskFilter service class."""

    def test_build_filters(self):
        """Test building filter conditions."""
        filters = TaskFilter.build_filters(
            status="COMPLETED",
            priority=5,
        )
        
        assert len(filters) > 0

    def test_search_with_filters(self):
        """Test search with filters service method."""
        db = SessionLocal()
        
        tasks, total = TaskFilter.search_with_filters(
            db,
            status="PENDING",
            limit=10,
            offset=0,
        )
        
        assert isinstance(tasks, list)
        assert isinstance(total, int)
        
        db.close()

    def test_filter_presets_exist(self):
        """Test that filter presets are available."""
        presets = TaskFilter.get_filter_presets()
        
        assert len(presets) > 0
        assert "failed_today" in presets
        assert "high_priority_pending" in presets

    def test_full_text_search(self):
        """Test full-text search."""
        db = SessionLocal()
        
        tasks = TaskFilter.full_text_search(
            db,
            query="test",
            limit=10,
        )
        
        assert isinstance(tasks, list)
        
        db.close()

    def test_export_to_csv(self):
        """Test CSV export functionality."""
        db = SessionLocal()
        
        tasks = db.query(Task).limit(5).all()
        csv_content = TaskFilter.export_to_csv(tasks)
        
        assert isinstance(csv_content, str)
        assert "task_id" in csv_content
        assert "task_name" in csv_content
        
        db.close()
