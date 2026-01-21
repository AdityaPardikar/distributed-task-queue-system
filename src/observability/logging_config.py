"""Structured logging configuration using structlog."""

import logging
import sys
from typing import Any, Mapping

import structlog

DEFAULT_LOG_LEVEL = "INFO"


def configure_logging(log_level: str = DEFAULT_LOG_LEVEL, log_format: str = "json") -> None:
    """Configure structlog and stdlib logging.

    Args:
        log_level: Log level name (e.g., INFO, DEBUG)
        log_format: Either "json" or "console".
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if log_format == "console":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(level=level, handlers=[logging.StreamHandler(sys.stdout)])


def add_request_context(request_id: str, path: str, method: str, client: str | None) -> None:
    """Inject request context into structlog contextvars."""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        path=path,
        method=method,
        client=client,
    )


def bind_extra(**kwargs: Any) -> Mapping[str, Any]:
    """Bind extra fields to current context and return them."""
    structlog.contextvars.bind_contextvars(**kwargs)
    return kwargs
