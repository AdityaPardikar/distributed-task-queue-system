"""Integration test configuration.

Integration tests require running PostgreSQL and Redis services.
Tests are automatically skipped when services are unavailable.
"""

import pytest
import socket


def _is_service_available(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a network service is available."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False


def pytest_collection_modifyitems(config, items):
    """Skip integration tests when required services are not running."""
    pg_available = _is_service_available("localhost", 5432)
    redis_available = _is_service_available("localhost", 6379)

    if pg_available and redis_available:
        return  # All services available, run tests normally

    skip_reason = []
    if not pg_available:
        skip_reason.append("PostgreSQL (localhost:5432)")
    if not redis_available:
        skip_reason.append("Redis (localhost:6379)")

    reason = f"Integration tests require: {', '.join(skip_reason)}"
    skip_marker = pytest.mark.skip(reason=reason)

    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(skip_marker)
