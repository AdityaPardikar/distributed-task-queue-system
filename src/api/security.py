"""
Security Headers Middleware — TaskFlow
=======================================
Adds production-grade HTTP security headers to every response.
Includes optional per-endpoint rate limiting with tiered limits.
"""

from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from src.cache.client import get_redis_client
from src.config import get_settings
from src.config.security import get_security_config

settings = get_settings()
security = get_security_config()

# ── Security Headers Middleware (ASGI) ───────────────────────────────────────


class SecurityHeadersMiddleware:
    """
    ASGI middleware that attaches security headers to every HTTP response.

    Usage in FastAPI::

        app.add_middleware(SecurityHeadersMiddleware)
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.headers = security.headers.as_dict()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def _send_with_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for name, value in self.headers.items():
                    headers.append((name.lower().encode(), value.encode()))

                # Remove Server header (information disclosure)
                headers = [
                    (k, v) for k, v in headers if k != b"server"
                ]

                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, _send_with_headers)


# ── Enhanced Rate Limiter (per-endpoint tiered) ─────────────────────────────


async def tiered_rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """
    Enhanced rate limiter that applies different limits based on endpoint tier.

    Tiers (defined in SecurityConfig.rate_limits):
      - auth:      5 req/min   (brute-force protection)
      - read:    100 req/min   (standard GETs)
      - write:    30 req/min   (mutating operations)
      - analytics: 10 req/min  (heavy queries / exports)

    Returns X-RateLimit-* headers on every response for client visibility.
    """
    if not settings.RATE_LIMIT_ENABLED:
        return await call_next(request)

    # Skip rate limiting for health checks and metrics
    path = request.url.path
    if path in ("/health", "/healthz", "/metrics", "/"):
        return await call_next(request)

    redis = get_redis_client()
    rate_cfg = security.rate_limits
    tier = rate_cfg.tier_for_path(request.method, path)

    # Identify caller
    user_id = request.headers.get(
        "X-User-ID",
        request.client.host if request.client else "unknown",
    )

    # Per-tier key
    key = f"rl:{tier.name}:{user_id}"
    window = 60  # 1-minute sliding window

    try:
        current_raw = redis.get(key)
        current = int(current_raw) if current_raw is not None else 0

        if current >= tier.requests_per_minute + tier.burst:
            # Calculate retry-after from TTL
            ttl = redis.ttl(key)
            retry_after = max(ttl if ttl and ttl > 0 else window, 1)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "tier": tier.name,
                    "limit": tier.requests_per_minute,
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(tier.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )

        if current == 0:
            redis.set(key, 1, ttl=window)
        else:
            redis.incr(key)

        remaining = max(tier.requests_per_minute - (current + 1), 0)
    except Exception:
        # If Redis is down, fail open (allow the request)
        remaining = tier.requests_per_minute

    response = await call_next(request)

    # Attach rate-limit info headers
    response.headers["X-RateLimit-Limit"] = str(tier.requests_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Tier"] = tier.name
    return response


# ── Login Attempt Throttle ──────────────────────────────────────────────────

_LOGIN_WINDOW = 900  # 15-minute window
_LOGIN_MAX_ATTEMPTS = 10  # lock after 10 failed attempts in that window
_LOCKOUT_DURATION = 900  # 15-minute lockout


async def check_login_throttle(identifier: str) -> tuple[bool, int]:
    """
    Check whether a login attempt should be throttled.

    Returns:
        (is_allowed, remaining_attempts)
    """
    redis = get_redis_client()
    key = f"login_throttle:{identifier}"

    try:
        current_raw = redis.get(key)
        current = int(current_raw) if current_raw is not None else 0

        if current >= _LOGIN_MAX_ATTEMPTS:
            ttl = redis.ttl(key)
            return False, 0

        if current == 0:
            redis.set(key, 1, ttl=_LOGIN_WINDOW)
        else:
            redis.incr(key)

        return True, _LOGIN_MAX_ATTEMPTS - (current + 1)
    except Exception:
        # Fail open if Redis is unavailable
        return True, _LOGIN_MAX_ATTEMPTS


async def record_failed_login(identifier: str) -> None:
    """Record a failed login attempt (increments the throttle counter)."""
    redis = get_redis_client()
    key = f"login_throttle:{identifier}"
    try:
        current_raw = redis.get(key)
        if current_raw is None:
            redis.set(key, 1, ttl=_LOGIN_WINDOW)
        else:
            redis.incr(key)
    except Exception:
        pass


async def clear_login_throttle(identifier: str) -> None:
    """Clear throttle counter on successful login."""
    redis = get_redis_client()
    key = f"login_throttle:{identifier}"
    try:
        redis.delete(key)
    except Exception:
        pass


# ── IP Blocklist Checker ────────────────────────────────────────────────────


async def is_ip_blocked(ip: str) -> bool:
    """Check if an IP is in the Redis blocklist."""
    redis = get_redis_client()
    try:
        return redis.get(f"blocked_ip:{ip}") is not None
    except Exception:
        return False


async def block_ip(ip: str, duration_seconds: int = 3600, reason: str = "") -> None:
    """Block an IP for a given duration."""
    redis = get_redis_client()
    try:
        redis.set(f"blocked_ip:{ip}", reason or "blocked", ttl=duration_seconds)
    except Exception:
        pass
