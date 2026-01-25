"""Circuit breaker pattern implementation for resilience."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional, Any

from src.cache.client import RedisClient, get_redis_client


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"        # Normal operation
    OPEN = "OPEN"            # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreaker:
    """Circuit breaker for protecting failing services."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
        expected_exception: type = Exception,
        redis_client: Optional[RedisClient] = None,
    ):
        """Initialize circuit breaker.
        
        Args:
            name: Circuit breaker identifier
            failure_threshold: Failures before opening circuit
            recovery_timeout_seconds: Time before trying to recover
            expected_exception: Exception type to catch
            redis_client: Redis client for state persistence
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.expected_exception = expected_exception
        self.redis = redis_client or get_redis_client()

        self.key_state = f"circuit_breaker:{name}:state"
        self.key_count = f"circuit_breaker:{name}:failure_count"
        self.key_last_failure = f"circuit_breaker:{name}:last_failure"
        self.key_opened_at = f"circuit_breaker:{name}:opened_at"

    def call(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Expected exception from function
        """
        state = self.get_state()

        if state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise

    def get_state(self) -> CircuitState:
        """Get current circuit state.
        
        Returns:
            Current state
        """
        state_str = self.redis.get(self.key_state)
        if state_str:
            return CircuitState(state_str)
        return CircuitState.CLOSED

    def _on_success(self) -> None:
        """Handle successful call."""
        self.redis.delete(self.key_count)
        self.redis.delete(self.key_last_failure)
        self.redis.set(self.key_state, CircuitState.CLOSED.value)

    def _on_failure(self) -> None:
        """Handle failed call."""
        count = self.redis.incr(self.key_count)
        self.redis.set(self.key_last_failure, datetime.utcnow().isoformat())

        if count >= self.failure_threshold:
            self._transition_to_open()

    def _transition_to_open(self) -> None:
        """Transition to open state."""
        self.redis.set(self.key_state, CircuitState.OPEN.value)
        self.redis.set(self.key_opened_at, datetime.utcnow().isoformat())

    def _transition_to_half_open(self) -> None:
        """Transition to half-open state."""
        self.redis.set(self.key_state, CircuitState.HALF_OPEN.value)

    def _should_attempt_reset(self) -> bool:
        """Check if recovery timeout has elapsed.
        
        Returns:
            True if should attempt reset
        """
        opened_at_str = self.redis.get(self.key_opened_at)
        if not opened_at_str:
            return True

        opened_at = datetime.fromisoformat(opened_at_str)
        elapsed = (datetime.utcnow() - opened_at).total_seconds()
        return elapsed >= self.recovery_timeout_seconds

    def reset(self) -> None:
        """Manually reset circuit breaker."""
        self.redis.delete(self.key_state)
        self.redis.delete(self.key_count)
        self.redis.delete(self.key_last_failure)
        self.redis.delete(self.key_opened_at)

    def get_status(self) -> dict:
        """Get circuit breaker status.
        
        Returns:
            Status dictionary
        """
        state = self.get_state()
        count = self.redis.get(self.key_count) or 0
        last_failure = self.redis.get(self.key_last_failure)
        opened_at = self.redis.get(self.key_opened_at)

        return {
            "name": self.name,
            "state": state.value,
            "failure_count": int(count),
            "failure_threshold": self.failure_threshold,
            "last_failure": last_failure,
            "opened_at": opened_at,
            "recovery_timeout_seconds": self.recovery_timeout_seconds,
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass
