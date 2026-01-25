"""Auto-recovery mechanisms for resilience."""

from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, Any

from src.cache.client import RedisClient, get_redis_client


class RecoveryAction:
    """Represents an action to attempt recovery."""

    def __init__(
        self,
        name: str,
        action: Callable,
        max_attempts: int = 3,
        backoff_seconds: int = 5,
    ):
        """Initialize recovery action.
        
        Args:
            name: Action name
            action: Callable to execute
            max_attempts: Maximum retry attempts
            backoff_seconds: Initial backoff delay
        """
        self.name = name
        self.action = action
        self.max_attempts = max_attempts
        self.backoff_seconds = backoff_seconds


class AutoRecoveryEngine:
    """Handles automatic recovery from failures."""

    def __init__(self, redis_client: Optional[RedisClient] = None):
        """Initialize auto-recovery engine.
        
        Args:
            redis_client: Redis client for state tracking
        """
        self.redis = redis_client or get_redis_client()
        self.key_recovery_prefix = "recovery"
        self.key_action_history = "recovery:history"

    def register_recovery_action(
        self,
        component: str,
        action: RecoveryAction,
    ) -> bool:
        """Register a recovery action for a component.
        
        Args:
            component: Component name
            action: Recovery action
            
        Returns:
            True if registered
        """
        key = f"{self.key_recovery_prefix}:{component}"
        self.redis.hset(
            key,
            "name",
            action.name,
        )
        self.redis.hset(
            key,
            "max_attempts",
            str(action.max_attempts),
        )
        self.redis.hset(
            key,
            "backoff_seconds",
            str(action.backoff_seconds),
        )
        return True

    def attempt_recovery(
        self,
        component: str,
        action: RecoveryAction,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Attempt to recover a component.
        
        Args:
            component: Component name
            action: Recovery action to execute
            context: Additional context for recovery
            
        Returns:
            Recovery result dictionary
        """
        result = {
            "component": component,
            "action": action.name,
            "success": False,
            "attempt": 0,
            "error": None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        attempt = 0
        delay = action.backoff_seconds

        while attempt < action.max_attempts:
            attempt += 1
            result["attempt"] = attempt

            try:
                action.action(context or {})
                result["success"] = True
                self._log_recovery(component, action.name, True, attempt)
                return result

            except Exception as e:
                result["error"] = str(e)
                if attempt < action.max_attempts:
                    import time
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff

                self._log_recovery(component, action.name, False, attempt)

        return result

    def _log_recovery(
        self,
        component: str,
        action_name: str,
        success: bool,
        attempt: int,
    ) -> None:
        """Log recovery attempt.
        
        Args:
            component: Component name
            action_name: Action name
            success: Whether attempt succeeded
            attempt: Attempt number
        """
        import json
        entry = {
            "component": component,
            "action": action_name,
            "success": success,
            "attempt": attempt,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self.redis.rpush(
            self.key_action_history,
            json.dumps(entry),
        )
        # Keep last 1000 entries
        self.redis.ltrim(self.key_action_history, -1000, -1)

    def get_recovery_history(
        self,
        component: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """Get recovery attempt history.
        
        Args:
            component: Component to filter (optional)
            limit: Maximum entries to return
            
        Returns:
            List of recovery entries
        """
        import json
        entries = self.redis.lrange(
            self.key_action_history,
            -limit,
            -1,
        )

        history = [json.loads(e) for e in (entries or [])]

        if component:
            history = [e for e in history if e["component"] == component]

        return history

    def get_recovery_status(self, component: str) -> Dict[str, Any]:
        """Get recovery status for a component.
        
        Args:
            component: Component name
            
        Returns:
            Recovery status dictionary
        """
        key = f"{self.key_recovery_prefix}:{component}"
        data = self.redis.hgetall(key)

        if not data:
            return {"component": component, "status": "no_recovery_registered"}

        history = self.get_recovery_history(component, limit=10)
        recent_success = any(e["success"] for e in history[-5:]) if history else False

        return {
            "component": component,
            "action_name": data.get("name"),
            "max_attempts": int(data.get("max_attempts", 0)),
            "backoff_seconds": int(data.get("backoff_seconds", 0)),
            "recent_success": recent_success,
            "recent_history": history[-5:],
        }


class HealthChecker:
    """Monitor component health and trigger recovery."""

    def __init__(self, redis_client: Optional[RedisClient] = None):
        """Initialize health checker.
        
        Args:
            redis_client: Redis client
        """
        self.redis = redis_client or get_redis_client()
        self.key_health_prefix = "health"
        self.key_checks_prefix = "health:checks"

    def check_health(
        self,
        component: str,
        check_fn: Callable[[], bool],
    ) -> bool:
        """Check if a component is healthy.
        
        Args:
            component: Component name
            check_fn: Function that returns True if healthy
            
        Returns:
            True if healthy
        """
        try:
            is_healthy = check_fn()
            self._record_check(component, is_healthy)
            return is_healthy

        except Exception as e:
            self._record_check(component, False, str(e))
            return False

    def _record_check(
        self,
        component: str,
        healthy: bool,
        error: Optional[str] = None,
    ) -> None:
        """Record a health check result.
        
        Args:
            component: Component name
            healthy: Whether check passed
            error: Error message if unhealthy
        """
        import json
        check_entry = {
            "component": component,
            "healthy": healthy,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.redis.rpush(
            f"{self.key_checks_prefix}:{component}",
            json.dumps(check_entry),
        )

        # Keep last 100 checks per component
        self.redis.ltrim(f"{self.key_checks_prefix}:{component}", -100, -1)

        # Update latest status
        status_key = f"{self.key_health_prefix}:{component}"
        self.redis.set(status_key, "healthy" if healthy else "unhealthy")
        self.redis.expire(status_key, 3600)

    def get_component_health(self, component: str) -> Dict[str, Any]:
        """Get health status for a component.
        
        Args:
            component: Component name
            
        Returns:
            Health status dictionary
        """
        import json
        status_key = f"{self.key_health_prefix}:{component}"
        status = self.redis.get(status_key) or "unknown"

        checks = self.redis.lrange(
            f"{self.key_checks_prefix}:{component}",
            -10,
            -1,
        )

        recent_checks = [json.loads(c) for c in (checks or [])]

        # Calculate success rate
        if recent_checks:
            success_count = sum(1 for c in recent_checks if c["healthy"])
            success_rate = (success_count / len(recent_checks)) * 100
        else:
            success_rate = 0.0

        return {
            "component": component,
            "status": status,
            "success_rate": success_rate,
            "recent_checks": recent_checks[-5:],
        }

    def get_all_health_status(self) -> Dict[str, Any]:
        """Get health status for all components.
        
        Returns:
            Dictionary of all component health statuses
        """
        all_status = {}

        # Scan for all health keys
        keys = self.redis.scan_keys(f"{self.key_health_prefix}:*")

        for key in (keys or []):
            component = key.split(":")[-1]
            all_status[component] = self.get_component_health(component)

        return all_status


# Global instances
_recovery_engine: Optional[AutoRecoveryEngine] = None
_health_checker: Optional[HealthChecker] = None


def get_auto_recovery_engine() -> AutoRecoveryEngine:
    """Get global auto-recovery engine instance."""
    global _recovery_engine
    if _recovery_engine is None:
        _recovery_engine = AutoRecoveryEngine()
    return _recovery_engine


def get_health_checker() -> HealthChecker:
    """Get global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
