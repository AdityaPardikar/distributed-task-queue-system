"""Integration tests for resilience and error handling."""

import pytest
from datetime import datetime
import time

from src.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
)
from src.resilience.graceful_degradation import (
    GracefulDegradation,
    DegradationStrategy,
    get_graceful_degradation,
)
from src.resilience.auto_recovery import (
    AutoRecoveryEngine,
    HealthChecker,
    RecoveryAction,
    get_auto_recovery_engine,
    get_health_checker,
)


@pytest.fixture
def circuit_breaker():
    """Fixture providing circuit breaker."""
    return CircuitBreaker(
        name="test_breaker",
        failure_threshold=3,
        recovery_timeout_seconds=5,
    )


@pytest.fixture
def degradation():
    """Fixture providing graceful degradation."""
    return get_graceful_degradation()


@pytest.fixture
def recovery_engine():
    """Fixture providing recovery engine."""
    return get_auto_recovery_engine()


@pytest.fixture
def health_checker():
    """Fixture providing health checker."""
    return get_health_checker()


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_circuit_starts_closed(self, circuit_breaker):
        """Test circuit breaker starts in closed state."""
        assert circuit_breaker.get_state() == CircuitState.CLOSED

    def test_successful_call_through_circuit(self, circuit_breaker):
        """Test successful call passes through."""
        def success_fn():
            return "success"

        result = circuit_breaker.call(success_fn)
        assert result == "success"
        assert circuit_breaker.get_state() == CircuitState.CLOSED

    def test_circuit_opens_after_failures(self, circuit_breaker):
        """Test circuit opens after threshold failures."""
        def failing_fn():
            raise ValueError("Test error")

        # Cause failures
        for _ in range(3):
            try:
                circuit_breaker.call(failing_fn)
            except ValueError:
                pass

        assert circuit_breaker.get_state() == CircuitState.OPEN

    def test_circuit_rejects_calls_when_open(self, circuit_breaker):
        """Test circuit rejects calls when open."""
        def failing_fn():
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(3):
            try:
                circuit_breaker.call(failing_fn)
            except ValueError:
                pass

        # Attempt call should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            circuit_breaker.call(failing_fn)

    def test_circuit_half_open_after_timeout(self, circuit_breaker):
        """Test circuit transitions to half-open after timeout."""
        def failing_fn():
            raise ValueError("Test error")

        # Open circuit
        for _ in range(3):
            try:
                circuit_breaker.call(failing_fn)
            except ValueError:
                pass

        assert circuit_breaker.get_state() == CircuitState.OPEN

        # Wait for recovery timeout (5 seconds)
        # In real scenario, we'd wait, but for tests we can force transition
        circuit_breaker.redis.delete(circuit_breaker.key_opened_at)

        # Next call should attempt half-open
        def success_fn():
            return "recovered"

        # Should attempt because timeout elapsed
        # Note: Half-open state transitions back on success
        result = circuit_breaker.call(success_fn)
        assert result == "recovered"
        assert circuit_breaker.get_state() == CircuitState.CLOSED

    def test_manual_reset(self, circuit_breaker):
        """Test manual reset of circuit breaker."""
        def failing_fn():
            raise ValueError("Test error")

        # Open circuit
        for _ in range(3):
            try:
                circuit_breaker.call(failing_fn)
            except ValueError:
                pass

        assert circuit_breaker.get_state() == CircuitState.OPEN

        # Reset
        circuit_breaker.reset()
        assert circuit_breaker.get_state() == CircuitState.CLOSED

    def test_get_status(self, circuit_breaker):
        """Test getting circuit breaker status."""
        status = circuit_breaker.get_status()

        assert status["name"] == "test_breaker"
        assert status["state"] == "CLOSED"
        assert status["failure_count"] == 0
        assert status["failure_threshold"] == 3


class TestGracefulDegradation:
    """Test graceful degradation."""

    def test_mark_service_degraded(self, degradation):
        """Test marking a service as degraded."""
        result = degradation.mark_service_degraded(
            "database",
            DegradationStrategy.RETURN_CACHED,
            300,
        )
        assert result is True

    def test_is_service_degraded(self, degradation):
        """Test checking if service is degraded."""
        assert degradation.is_service_degraded("database") is False

        degradation.mark_service_degraded(
            "database",
            DegradationStrategy.RETURN_CACHED,
        )

        assert degradation.is_service_degraded("database") is True

    def test_get_degradation_strategy(self, degradation):
        """Test getting degradation strategy."""
        degradation.mark_service_degraded(
            "api",
            DegradationStrategy.QUEUE_TO_FALLBACK,
        )

        strategy = degradation.get_degradation_strategy("api")
        assert strategy == DegradationStrategy.QUEUE_TO_FALLBACK

    def test_throughput_limit(self, degradation):
        """Test throughput limiting during degradation."""
        degradation.set_throughput_limit(100, 300)

        limit = degradation.get_throughput_limit()
        assert limit == 100

    def test_cache_result(self, degradation):
        """Test caching result for fallback."""
        test_data = {"user_id": 123, "name": "Test"}

        degradation.cache_result("user:123", test_data, 3600)
        cached = degradation.get_cached_result("user:123")

        assert cached == test_data

    def test_clear_degradation(self, degradation):
        """Test clearing degradation state."""
        degradation.mark_service_degraded(
            "cache",
            DegradationStrategy.SKIP_ENRICHMENT,
        )

        assert degradation.is_service_degraded("cache") is True

        degradation.clear_degradation("cache")
        assert degradation.is_service_degraded("cache") is False

    def test_get_all_degraded_services(self, degradation):
        """Test getting all degraded services."""
        degradation.mark_service_degraded("db", DegradationStrategy.RETURN_CACHED)
        degradation.mark_service_degraded("api", DegradationStrategy.SKIP_ENRICHMENT)

        services = degradation.get_all_degraded_services()

        assert "db" in services
        assert "api" in services
        assert services["db"]["strategy"] == "return_cached"
        assert services["api"]["strategy"] == "skip_enrichment"


class TestAutoRecovery:
    """Test auto-recovery mechanisms."""

    def test_register_recovery_action(self, recovery_engine):
        """Test registering a recovery action."""
        def dummy_action(context):
            pass

        action = RecoveryAction(
            name="restart_service",
            action=dummy_action,
            max_attempts=3,
            backoff_seconds=5,
        )

        result = recovery_engine.register_recovery_action("web_service", action)
        assert result is True

    def test_attempt_recovery_success(self, recovery_engine):
        """Test successful recovery attempt."""
        call_count = 0

        def recovery_action(context):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Failed on first attempt")

        action = RecoveryAction(
            name="reconnect",
            action=recovery_action,
            max_attempts=3,
            backoff_seconds=0.1,
        )

        result = recovery_engine.attempt_recovery("database", action)

        assert result["success"] is True
        assert result["attempt"] == 2
        assert call_count == 2

    def test_attempt_recovery_failure(self, recovery_engine):
        """Test failed recovery attempt."""
        def failing_action(context):
            raise Exception("Persistent failure")

        action = RecoveryAction(
            name="reconnect",
            action=failing_action,
            max_attempts=2,
            backoff_seconds=0.01,
        )

        result = recovery_engine.attempt_recovery("database", action)

        assert result["success"] is False
        assert result["attempt"] == 2
        assert result["error"] is not None

    def test_recovery_history(self, recovery_engine):
        """Test recovery action history."""
        def dummy_action(context):
            pass

        action = RecoveryAction("test_action", dummy_action)

        recovery_engine.attempt_recovery("service_a", action)
        recovery_engine.attempt_recovery("service_b", action)

        history = recovery_engine.get_recovery_history(limit=10)
        assert len(history) >= 2

    def test_recovery_status(self, recovery_engine):
        """Test getting recovery status."""
        def dummy_action(context):
            pass

        action = RecoveryAction("restart", dummy_action)
        recovery_engine.register_recovery_action("worker", action)
        recovery_engine.attempt_recovery("worker", action)

        status = recovery_engine.get_recovery_status("worker")

        assert status["component"] == "worker"
        assert status["action_name"] == "restart"
        assert status["max_attempts"] == 3


class TestHealthChecker:
    """Test health checking."""

    def test_check_healthy_component(self, health_checker):
        """Test checking healthy component."""
        def health_check():
            return True

        is_healthy = health_checker.check_health("api", health_check)
        assert is_healthy is True

    def test_check_unhealthy_component(self, health_checker):
        """Test checking unhealthy component."""
        def health_check():
            return False

        is_healthy = health_checker.check_health("database", health_check)
        assert is_healthy is False

    def test_health_check_exception(self, health_checker):
        """Test health check with exception."""
        def health_check():
            raise Exception("Connection failed")

        is_healthy = health_checker.check_health("external_api", health_check)
        assert is_healthy is False

    def test_get_component_health(self, health_checker):
        """Test getting component health status."""
        def health_check():
            return True

        for _ in range(5):
            health_checker.check_health("service", health_check)

        status = health_checker.get_component_health("service")

        assert status["component"] == "service"
        assert status["status"] == "healthy"
        assert status["success_rate"] == 100.0

    def test_health_success_rate(self, health_checker):
        """Test calculating success rate."""
        check_results = [True, True, False, True, False]

        for result in check_results:
            def health_check():
                return result
            health_checker.check_health("intermittent", health_check)

        status = health_checker.get_component_health("intermittent")

        # 3 successes out of 5 = 60%
        assert status["success_rate"] == 60.0

    def test_get_all_health_status(self, health_checker):
        """Test getting all component health statuses."""
        def healthy():
            return True

        def unhealthy():
            return False

        health_checker.check_health("service_a", healthy)
        health_checker.check_health("service_b", unhealthy)

        all_status = health_checker.get_all_health_status()

        assert "service_a" in all_status
        assert "service_b" in all_status
        assert all_status["service_a"]["status"] == "healthy"
        assert all_status["service_b"]["status"] == "unhealthy"


class TestResilienceIntegration:
    """Integration tests combining resilience patterns."""

    def test_circuit_breaker_with_recovery(self, circuit_breaker, recovery_engine):
        """Test circuit breaker with auto-recovery."""
        failure_count = 0

        def failing_fn():
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 3:
                raise ValueError("Service unavailable")
            return "recovered"

        # Trigger failures to open circuit
        for _ in range(3):
            try:
                circuit_breaker.call(failing_fn)
            except ValueError:
                pass

        assert circuit_breaker.get_state() == CircuitState.OPEN

        # Define recovery action
        def recover_service(context):
            # Simulate recovery
            pass

        action = RecoveryAction("restart", recover_service)
        recovery_engine.attempt_recovery("service", action)

        # Reset circuit manually (as if recovery succeeded)
        circuit_breaker.reset()
        assert circuit_breaker.get_state() == CircuitState.CLOSED

    def test_graceful_degradation_workflow(self, degradation):
        """Test complete graceful degradation workflow."""
        # Cache some data before degradation
        data = {"query": "SELECT * FROM users", "result": [1, 2, 3]}
        degradation.cache_result("query:users", data)

        # Mark service as degraded
        degradation.mark_service_degraded(
            "database",
            DegradationStrategy.RETURN_CACHED,
        )

        # Check if degraded
        assert degradation.is_service_degraded("database") is True

        # Get cached result
        cached = degradation.get_cached_result("query:users")
        assert cached == data

        # Clear degradation
        degradation.clear_degradation("database")
        assert degradation.is_service_degraded("database") is False
