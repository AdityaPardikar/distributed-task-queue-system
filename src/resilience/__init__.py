"""Resilience and recovery module for error handling."""

from .circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerOpenError
from .graceful_degradation import GracefulDegradation, DegradationStrategy, get_graceful_degradation
from .auto_recovery import (
    AutoRecoveryEngine,
    RecoveryAction,
    HealthChecker,
    get_auto_recovery_engine,
    get_health_checker,
)

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerOpenError",
    "GracefulDegradation",
    "DegradationStrategy",
    "get_graceful_degradation",
    "AutoRecoveryEngine",
    "RecoveryAction",
    "HealthChecker",
    "get_auto_recovery_engine",
    "get_health_checker",
]
