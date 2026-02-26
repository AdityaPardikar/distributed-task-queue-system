"""
Centralized Security Configuration — TaskFlow
================================================
All security-related settings in one place: CORS policies, rate-limit tiers,
token policies, password rules, and allowed origins/hosts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import ClassVar

from src.config import get_settings

# ── Password Policy ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PasswordPolicy:
    """Enterprise password complexity requirements."""

    min_length: int = 10
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = True
    disallowed_patterns: tuple[str, ...] = ("password", "123456", "qwerty", "admin")

    def validate(self, password: str) -> list[str]:
        """Return a list of violation messages (empty = valid)."""
        errors: list[str] = []
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters")
        if len(password) > self.max_length:
            errors.append(f"Password must be at most {self.max_length} characters")
        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        if self.require_digit and not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")
        if self.require_special and not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
            errors.append("Password must contain at least one special character")
        lower = password.lower()
        for pattern in self.disallowed_patterns:
            if pattern in lower:
                errors.append(f"Password must not contain '{pattern}'")
        return errors


# ── Rate-Limit Tiers ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RateLimitTier:
    """A single rate-limit tier definition."""

    name: str
    requests_per_minute: int
    burst: int  # allowed burst above steady rate


@dataclass(frozen=True)
class RateLimitConfig:
    """Per-endpoint-class rate-limit configuration."""

    auth: RateLimitTier = field(default_factory=lambda: RateLimitTier("auth", 5, 2))
    read: RateLimitTier = field(default_factory=lambda: RateLimitTier("read", 100, 20))
    write: RateLimitTier = field(default_factory=lambda: RateLimitTier("write", 30, 10))
    analytics: RateLimitTier = field(default_factory=lambda: RateLimitTier("analytics", 10, 3))
    websocket_max_connections: int = 5
    global_per_ip: int = 1000

    # Path → tier mapping
    TIER_MAP: ClassVar[dict[str, str]] = {
        "/api/v1/auth/": "auth",
        "/api/v1/analytics/": "analytics",
        "/api/v1/tasks/export": "analytics",
        "/api/v1/campaigns/": "write",
        "/api/v1/tasks/": "write",
        "/api/v1/workers/": "write",
        "/api/v1/workflows/": "write",
        "/api/v1/templates/": "write",
    }

    def tier_for_path(self, method: str, path: str) -> RateLimitTier:
        """Resolve the correct rate-limit tier for a given request."""
        # Read methods bypass write limits
        if method.upper() == "GET":
            # Still apply special tiers for auth / analytics
            for prefix, tier_name in self.TIER_MAP.items():
                if path.startswith(prefix) and tier_name in ("auth", "analytics"):
                    return getattr(self, tier_name)
            return self.read

        for prefix, tier_name in self.TIER_MAP.items():
            if path.startswith(prefix):
                return getattr(self, tier_name)

        return self.read


# ── Token Policy ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TokenPolicy:
    """JWT token lifecycle policy."""

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    issuer: str = "taskflow"
    audience: str = "taskflow-api"
    rotate_refresh_on_use: bool = True
    max_active_sessions: int = 5


# ── Security Headers ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SecurityHeadersConfig:
    """HTTP security headers applied to every response."""

    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "1; mode=block"
    strict_transport_security: str = "max-age=31536000; includeSubDomains; preload"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "camera=(), microphone=(), geolocation=(), payment=()"
    content_security_policy: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "font-src 'self' data:; "
        "connect-src 'self' ws: wss:; "
        "frame-ancestors 'none'"
    )
    cross_origin_opener_policy: str = "same-origin"
    cross_origin_resource_policy: str = "same-origin"

    def as_dict(self) -> dict[str, str]:
        """Return headers as a {header-name: value} mapping."""
        return {
            "X-Content-Type-Options": self.x_content_type_options,
            "X-Frame-Options": self.x_frame_options,
            "X-XSS-Protection": self.x_xss_protection,
            "Strict-Transport-Security": self.strict_transport_security,
            "Referrer-Policy": self.referrer_policy,
            "Permissions-Policy": self.permissions_policy,
            "Content-Security-Policy": self.content_security_policy,
            "Cross-Origin-Opener-Policy": self.cross_origin_opener_policy,
            "Cross-Origin-Resource-Policy": self.cross_origin_resource_policy,
        }


# ── CORS Hardening ──────────────────────────────────────────────────────────


@dataclass
class CORSConfig:
    """CORS configuration with environment-aware defaults."""

    allow_credentials: bool = True
    allow_methods: tuple[str, ...] = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    allow_headers: tuple[str, ...] = (
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-User-ID",
        "Accept",
        "Origin",
    )
    expose_headers: tuple[str, ...] = (
        "X-Request-ID",
        "X-Response-Time",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    )
    max_age: int = 600  # preflight cache seconds

    @property
    def allow_origins(self) -> list[str]:
        settings = get_settings()
        return settings.cors_origins_list


# ── Aggregate Security Configuration ────────────────────────────────────────


class SecurityConfig:
    """Top-level singleton that holds all security sub-configs."""

    _instance: SecurityConfig | None = None

    def __new__(cls) -> SecurityConfig:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self.password_policy = PasswordPolicy()
        self.rate_limits = RateLimitConfig()
        self.token_policy = TokenPolicy()
        self.headers = SecurityHeadersConfig()
        self.cors = CORSConfig()

    # Convenience helpers
    @property
    def is_production(self) -> bool:
        return get_settings().is_production


def get_security_config() -> SecurityConfig:
    """Return the singleton security configuration."""
    return SecurityConfig()
