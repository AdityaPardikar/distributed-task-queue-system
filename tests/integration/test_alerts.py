"""Integration tests for alert system."""

import pytest
from datetime import datetime, timedelta
from fastapi import status
from fastapi.testclient import TestClient

from src.api.main import app
from src.alerts.engine import AlertEngine, AlertType, AlertSeverity
from src.models import Task, Worker, Alert
from src.db.session import SessionLocal

client = TestClient(app)


class TestAlertEngine:
    """Test alert engine evaluation and firing."""

    def test_alert_engine_initialization(self):
        """Test alert engine can be initialized."""
        engine = AlertEngine()
        assert engine is not None

    def test_evaluate_no_active_workers(self):
        """Test detection of no active workers."""
        db = SessionLocal()
        engine = AlertEngine()
        
        result = engine.evaluate_no_active_workers(db)
        assert isinstance(result, bool)
        
        db.close()

    def test_evaluate_high_queue_depth(self):
        """Test detection of high queue depth."""
        db = SessionLocal()
        engine = AlertEngine()
        
        result = engine.evaluate_high_queue_depth(db, threshold=1000)
        assert isinstance(result, bool)
        
        db.close()

    def test_fire_alert(self):
        """Test firing an alert."""
        engine = AlertEngine()
        
        alert = engine.fire_alert(
            AlertType.NO_ACTIVE_WORKERS,
            AlertSeverity.CRITICAL,
            "Test alert description",
            metadata={"test": "data"},
        )
        
        assert alert
        assert alert["type"] == AlertType.NO_ACTIVE_WORKERS.value
        assert alert["severity"] == AlertSeverity.CRITICAL.value

    def test_alert_cooldown(self):
        """Test alert cooldown prevents duplicate firing."""
        engine = AlertEngine()
        
        # Fire first alert
        alert1 = engine.fire_alert(
            AlertType.NO_ACTIVE_WORKERS,
            AlertSeverity.CRITICAL,
            "First alert",
        )
        assert alert1
        
        # Try to fire same alert type immediately
        alert2 = engine.fire_alert(
            AlertType.NO_ACTIVE_WORKERS,
            AlertSeverity.CRITICAL,
            "Second alert",
        )
        
        # Should be empty due to cooldown
        assert not alert2


class TestAlertAPI:
    """Test alert API endpoints."""

    def test_get_active_alerts(self):
        """Test getting active alerts."""
        response = client.get("/api/v1/alerts")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)

    def test_get_alert_history(self):
        """Test getting alert history."""
        response = client.get("/api/v1/alerts/history?hours=24&limit=100")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)

    def test_get_alert_statistics(self):
        """Test getting alert statistics."""
        response = client.get("/api/v1/alerts/stats")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_alerts" in data
        assert "active_alerts" in data
        assert "acknowledged_alerts" in data
        assert "by_severity" in data
        assert "active_by_type" in data

    def test_evaluate_alert_rules(self):
        """Test manual alert rule evaluation."""
        response = client.post("/api/v1/alerts/evaluate")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "evaluated" in data
        assert data["evaluated"] is True
        assert "alerts_fired" in data

    def test_acknowledge_alert(self):
        """Test acknowledging an alert."""
        db = SessionLocal()
        
        # Create test alert
        alert = Alert(
            alert_type="TEST_ALERT",
            severity="INFO",
            description="Test alert",
            acknowledged=False,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        alert_id = str(alert.alert_id)
        
        # Acknowledge alert via API
        response = client.post(f"/api/v1/alerts/{alert_id}/acknowledge")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["acknowledged"] is True
        assert data["acknowledged_at"] is not None
        
        db.close()

    def test_get_alerts_filtered_by_acknowledged(self):
        """Test filtering alerts by acknowledged status."""
        # Get unacknowledged alerts
        response = client.get("/api/v1/alerts?acknowledged=false")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)

    def test_alert_history_time_range(self):
        """Test alert history with different time ranges."""
        # 6 hours
        response = client.get("/api/v1/alerts/history?hours=6")
        assert response.status_code == status.HTTP_200_OK
        
        # 7 days
        response = client.get("/api/v1/alerts/history?hours=168")
        assert response.status_code == status.HTTP_200_OK

    def test_alert_history_limit(self):
        """Test alert history with different limits."""
        response = client.get("/api/v1/alerts/history?limit=50")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 50
        
        response = client.get("/api/v1/alerts/history?limit=500")
        assert response.status_code == status.HTTP_200_OK
