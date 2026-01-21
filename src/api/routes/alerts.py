"""Alerts API routes."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.alerts.engine import get_alert_engine, AlertType, AlertSeverity
from src.db.session import get_db
from src.models import Alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertResponse(BaseModel):
    """Alert response schema."""
    alert_id: str
    alert_type: str
    severity: str
    description: str
    metadata: dict
    acknowledged: bool
    created_at: datetime
    acknowledged_at: datetime | None


class AlertCreate(BaseModel):
    """Create alert request."""
    alert_type: str
    severity: str
    description: str
    metadata: dict = {}


@router.get("", response_model=List[AlertResponse])
async def get_active_alerts(
    db: Session = Depends(get_db),
    acknowledged: bool = Query(False),
):
    """Get active alerts, optionally filtered by acknowledged status."""
    query = db.query(Alert)
    
    if not acknowledged:
        query = query.filter(Alert.acknowledged == False)
    
    alerts = query.order_by(Alert.created_at.desc()).all()
    
    return [
        AlertResponse(
            alert_id=str(a.alert_id),
            alert_type=a.alert_type,
            severity=a.severity,
            description=a.description,
            metadata=a.metadata,
            acknowledged=a.acknowledged,
            created_at=a.created_at,
            acknowledged_at=a.acknowledged_at,
        )
        for a in alerts
    ]


@router.get("/history")
async def get_alert_history(
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get alert history for specified time period."""
    from datetime import timedelta
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    alerts = (
        db.query(Alert)
        .filter(Alert.created_at >= cutoff)
        .order_by(Alert.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "alert_id": str(a.alert_id),
            "alert_type": a.alert_type,
            "severity": a.severity,
            "description": a.description,
            "created_at": a.created_at,
            "acknowledged": a.acknowledged,
        }
        for a in alerts
    ]


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
):
    """Mark an alert as acknowledged."""
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    
    if not alert:
        return {"error": "Alert not found"}
    
    alert.acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    
    return {
        "alert_id": str(alert.alert_id),
        "acknowledged": True,
        "acknowledged_at": alert.acknowledged_at,
    }


@router.get("/stats")
async def get_alert_statistics(db: Session = Depends(get_db)):
    """Get alert statistics and summary."""
    all_alerts = db.query(Alert).all()
    active_alerts = db.query(Alert).filter(Alert.acknowledged == False).all()
    
    # Group by severity
    severity_counts = {}
    for alert in all_alerts:
        severity = alert.severity
        if severity not in severity_counts:
            severity_counts[severity] = 0
        severity_counts[severity] += 1
    
    # Group by type
    type_counts = {}
    for alert in active_alerts:
        alert_type = alert.alert_type
        if alert_type not in type_counts:
            type_counts[alert_type] = 0
        type_counts[alert_type] += 1
    
    return {
        "total_alerts": len(all_alerts),
        "active_alerts": len(active_alerts),
        "acknowledged_alerts": len(all_alerts) - len(active_alerts),
        "by_severity": severity_counts,
        "active_by_type": type_counts,
    }


@router.post("/evaluate")
async def evaluate_alert_rules(db: Session = Depends(get_db)):
    """Manually evaluate all alert rules."""
    engine = get_alert_engine()
    fired_alerts = engine.evaluate_all_rules(db)
    
    # Store fired alerts in database
    for alert_data in fired_alerts:
        alert = Alert(
            alert_type=alert_data["type"],
            severity=alert_data["severity"],
            description=alert_data["description"],
            metadata=alert_data.get("metadata", {}),
        )
        db.add(alert)
    
    db.commit()
    
    return {
        "evaluated": True,
        "alerts_fired": len(fired_alerts),
        "details": fired_alerts,
    }
