"""Alert system for monitoring threshold violations."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.cache.client import RedisClient, get_redis_client
from src.models import Task, Worker


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertType(str, Enum):
    """Types of alerts."""
    NO_ACTIVE_WORKERS = "NO_ACTIVE_WORKERS"
    HIGH_QUEUE_DEPTH = "HIGH_QUEUE_DEPTH"
    HIGH_FAILURE_RATE = "HIGH_FAILURE_RATE"
    WORKER_DOWN = "WORKER_DOWN"
    TASK_TIMEOUT = "TASK_TIMEOUT"
    LOW_WORKER_HEARTBEAT = "LOW_WORKER_HEARTBEAT"


class AlertRule:
    """Represents an alert rule with threshold and condition."""

    def __init__(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        description: str,
        condition_check,
        cooldown_minutes: int = 5,
    ):
        """Initialize alert rule.
        
        Args:
            alert_type: Type of alert
            severity: Alert severity level
            description: Human-readable description
            condition_check: Callable that returns True if alert should fire
            cooldown_minutes: Minutes to wait before triggering same alert again
        """
        self.alert_type = alert_type
        self.severity = severity
        self.description = description
        self.condition_check = condition_check
        self.cooldown_minutes = cooldown_minutes


class AlertEngine:
    """Engine for evaluating alert rules and managing alert state."""

    ALERTS_KEY = "alerts:active"
    ALERT_HISTORY_KEY = "alerts:history"
    ALERT_COOLDOWN_KEY = "alerts:cooldown"
    ALERT_RETENTION = 604800  # 7 days in seconds

    def __init__(self, redis_client: Optional[RedisClient] = None):
        """Initialize alert engine."""
        self.redis = redis_client or get_redis_client()

    def _get_cooldown_key(self, alert_type: AlertType) -> str:
        """Get Redis key for alert cooldown."""
        return f"{self.ALERT_COOLDOWN_KEY}:{alert_type.value}"

    def _should_fire_alert(self, alert_type: AlertType) -> bool:
        """Check if alert is not in cooldown period."""
        cooldown_key = self._get_cooldown_key(alert_type)
        return self.redis.get(cooldown_key) is None

    def _set_alert_cooldown(self, alert_type: AlertType, cooldown_minutes: int = 5):
        """Set cooldown period for alert."""
        cooldown_key = self._get_cooldown_key(alert_type)
        self.redis.set(cooldown_key, "1", ttl=cooldown_minutes * 60)

    def evaluate_no_active_workers(self, db: Session) -> bool:
        """Check if there are no active workers."""
        active_count = db.query(Worker).filter(Worker.status == "ACTIVE").count()
        return active_count == 0

    def evaluate_high_queue_depth(
        self,
        db: Session,
        threshold: int = 1000,
    ) -> bool:
        """Check if queue depth exceeds threshold."""
        pending_count = db.query(Task).filter(Task.status == "PENDING").count()
        return pending_count > threshold

    def evaluate_high_failure_rate(
        self,
        db: Session,
        hours: int = 1,
        threshold: float = 0.5,  # 50% failure rate
    ) -> bool:
        """Check if failure rate exceeds threshold in recent period."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        recent_tasks = db.query(Task).filter(
            Task.completed_at >= cutoff,
        ).all()
        
        if not recent_tasks:
            return False
        
        failed = sum(1 for t in recent_tasks if t.status == "FAILED")
        failure_rate = failed / len(recent_tasks)
        
        return failure_rate > threshold

    def evaluate_worker_down(self, db: Session, heartbeat_timeout_seconds: int = 300) -> bool:
        """Check if any worker has missed heartbeat."""
        timeout = datetime.utcnow() - timedelta(seconds=heartbeat_timeout_seconds)
        
        dead_workers = db.query(Worker).filter(
            Worker.status == "ACTIVE",
            Worker.last_heartbeat < timeout,
        ).count()
        
        return dead_workers > 0

    def evaluate_low_heartbeat_frequency(
        self,
        db: Session,
        expected_interval_seconds: int = 60,
    ) -> bool:
        """Check if workers are heartbeating infrequently."""
        threshold = datetime.utcnow() - timedelta(seconds=expected_interval_seconds * 2)
        
        stale_workers = db.query(Worker).filter(
            Worker.status == "ACTIVE",
            Worker.last_heartbeat < threshold,
        ).count()
        
        return stale_workers > 0

    def fire_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        description: str,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Create and store an alert."""
        if not self._should_fire_alert(alert_type):
            return {}
        
        alert = {
            "id": f"{alert_type.value}:{int(datetime.utcnow().timestamp())}",
            "type": alert_type.value,
            "severity": severity.value,
            "description": description,
            "timestamp": datetime.utcnow().isoformat(),
            "acknowledged": False,
            "metadata": metadata or {},
        }
        
        # Add to active alerts
        self.redis.rpush(self.ALERTS_KEY, alert)
        
        # Add to history
        self.redis.rpush(self.ALERT_HISTORY_KEY, alert)
        self.redis.expire(self.ALERT_HISTORY_KEY, self.ALERT_RETENTION)
        
        # Set cooldown
        rule = self._get_default_rules().get(alert_type)
        if rule:
            self._set_alert_cooldown(alert_type, rule.cooldown_minutes)
        
        return alert

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark alert as acknowledged."""
        alerts = self.redis.lrange(self.ALERTS_KEY, 0, -1)
        
        for i, alert in enumerate(alerts):
            if alert.get("id") == alert_id:
                alert["acknowledged"] = True
                self.redis.lset(self.ALERTS_KEY, i, alert)
                return True
        
        return False

    def get_active_alerts(self) -> List[Dict]:
        """Get all active (non-acknowledged) alerts."""
        alerts = self.redis.lrange(self.ALERTS_KEY, 0, -1)
        return [a for a in alerts if not a.get("acknowledged", False)]

    def get_all_alerts(self, limit: int = 100) -> List[Dict]:
        """Get all alerts including acknowledged ones."""
        alerts = self.redis.lrange(self.ALERTS_KEY, 0, limit - 1)
        return alerts

    def get_alert_history(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """Get alert history for specified time period."""
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        history = self.redis.lrange(self.ALERT_HISTORY_KEY, 0, limit - 1)
        
        # Filter by time
        filtered = [
            a for a in history
            if a.get("timestamp", "") >= cutoff
        ]
        
        return filtered

    def clear_acknowledged_alerts(self) -> int:
        """Remove acknowledged alerts from active list."""
        alerts = self.redis.lrange(self.ALERTS_KEY, 0, -1)
        active_alerts = [a for a in alerts if not a.get("acknowledged", False)]
        
        # Clear and repopulate
        self.redis.delete(self.ALERTS_KEY)
        for alert in active_alerts:
            self.redis.rpush(self.ALERTS_KEY, alert)
        
        return len(alerts) - len(active_alerts)

    def _get_default_rules(self) -> Dict[AlertType, AlertRule]:
        """Get default alert rules."""
        return {
            AlertType.NO_ACTIVE_WORKERS: AlertRule(
                AlertType.NO_ACTIVE_WORKERS,
                AlertSeverity.CRITICAL,
                "No active workers detected",
                self.evaluate_no_active_workers,
                cooldown_minutes=2,
            ),
            AlertType.HIGH_QUEUE_DEPTH: AlertRule(
                AlertType.HIGH_QUEUE_DEPTH,
                AlertSeverity.WARNING,
                "Queue depth exceeds 1000 tasks",
                lambda db: self.evaluate_high_queue_depth(db, 1000),
                cooldown_minutes=10,
            ),
            AlertType.HIGH_FAILURE_RATE: AlertRule(
                AlertType.HIGH_FAILURE_RATE,
                AlertSeverity.CRITICAL,
                "Failure rate exceeds 50% in last hour",
                lambda db: self.evaluate_high_failure_rate(db, 1, 0.5),
                cooldown_minutes=15,
            ),
            AlertType.WORKER_DOWN: AlertRule(
                AlertType.WORKER_DOWN,
                AlertSeverity.CRITICAL,
                "Worker heartbeat timeout detected",
                lambda db: self.evaluate_worker_down(db),
                cooldown_minutes=5,
            ),
            AlertType.LOW_WORKER_HEARTBEAT: AlertRule(
                AlertType.LOW_WORKER_HEARTBEAT,
                AlertSeverity.WARNING,
                "Worker heartbeat frequency is low",
                lambda db: self.evaluate_low_heartbeat_frequency(db),
                cooldown_minutes=20,
            ),
        }

    def evaluate_all_rules(self, db: Session) -> List[Dict]:
        """Evaluate all alert rules and fire alerts for violations."""
        fired_alerts = []
        rules = self._get_default_rules()
        
        for alert_type, rule in rules.items():
            try:
                if rule.condition_check(db):
                    alert = self.fire_alert(
                        alert_type,
                        rule.severity,
                        rule.description,
                    )
                    if alert:
                        fired_alerts.append(alert)
            except Exception as e:
                # Log error but continue evaluating other rules
                print(f"Error evaluating rule {alert_type}: {e}")
        
        return fired_alerts


# Global instance
_engine: Optional[AlertEngine] = None


def get_alert_engine() -> AlertEngine:
    """Get global alert engine instance."""
    global _engine
    if _engine is None:
        _engine = AlertEngine()
    return _engine
