#!/usr/bin/env python3
"""
TaskFlow — Environment Validation Script
=========================================
Validates that all required environment variables are set and that
critical services (PostgreSQL, Redis) are reachable.

Usage:
    python scripts/validate_env.py          # Check current environment
    python scripts/validate_env.py --strict # Fail on warnings too
"""

import os
import sys
from pathlib import Path

# ── Colour helpers (works on most terminals) ─────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"  {GREEN}✓{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}⚠{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"  {RED}✗{RESET} {msg}")


# ── Required variables (name → description) ─────────────────────────────────
REQUIRED_VARS: dict[str, str] = {
    "SECRET_KEY": "Application secret key for signing tokens",
    "DATABASE_URL": "PostgreSQL connection string",
    "REDIS_URL": "Redis connection string",
}

RECOMMENDED_VARS: dict[str, str] = {
    "APP_ENV": "Application environment (development/staging/production)",
    "JWT_ALGORITHM": "JWT signing algorithm",
    "JWT_EXPIRATION_HOURS": "JWT token lifetime",
    "LOG_LEVEL": "Logging verbosity",
    "CORS_ORIGINS": "Allowed CORS origins",
    "ALLOWED_HOSTS": "Trusted host names",
}

PRODUCTION_REQUIRED: dict[str, str] = {
    "REDIS_PASSWORD": "Redis authentication password",
    "DB_PASSWORD": "Database password for Docker",
    "SMTP_HOST": "SMTP server for email delivery",
}

# ── Dangerous defaults that must be changed in production ────────────────────
DANGEROUS_DEFAULTS = {
    "SECRET_KEY": [
        "your-secret-key-change-in-production",
        "change-me-to-a-random-64-char-string",
        "dev-secret-key-change-in-production",
        "your-secret-key-here-change-in-production",
    ],
    "DB_PASSWORD": ["postgres", "password", "taskflow"],
    "REDIS_PASSWORD": [""],
}


def load_dotenv_file() -> dict[str, str]:
    """Load .env file manually (no dependency on python-dotenv)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    loaded: dict[str, str] = {}

    if not env_path.exists():
        warn(f".env file not found at {env_path}")
        warn("Create one with:  cp .env.example .env")
        return loaded

    ok(f"Found .env at {env_path}")

    with open(env_path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Remove surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            loaded[key] = value
            # Also set in os.environ so connectivity checks can use them
            if key not in os.environ:
                os.environ[key] = value

    return loaded


def get_var(name: str, loaded: dict[str, str]) -> str | None:
    """Get variable from os.environ first, then .env file."""
    return os.environ.get(name) or loaded.get(name)


def check_required(loaded: dict[str, str]) -> int:
    """Check that all required vars are present. Returns error count."""
    errors = 0
    print(f"\n{BOLD}Required Variables{RESET}")

    for var, desc in REQUIRED_VARS.items():
        val = get_var(var, loaded)
        if val:
            ok(f"{var} — set")
        else:
            fail(f"{var} — MISSING ({desc})")
            errors += 1

    return errors


def check_recommended(loaded: dict[str, str]) -> int:
    """Check recommended vars. Returns warning count."""
    warnings = 0
    print(f"\n{BOLD}Recommended Variables{RESET}")

    for var, desc in RECOMMENDED_VARS.items():
        val = get_var(var, loaded)
        if val:
            ok(f"{var} = {val}")
        else:
            warn(f"{var} — not set, using default ({desc})")
            warnings += 1

    return warnings


def check_production_security(loaded: dict[str, str]) -> int:
    """Check for dangerous default values. Returns error count."""
    app_env = get_var("APP_ENV", loaded) or "development"
    is_prod = app_env in ("production", "staging")

    print(f"\n{BOLD}Security Checks{RESET} (APP_ENV={app_env})")

    errors = 0

    # Check dangerous defaults
    for var, defaults in DANGEROUS_DEFAULTS.items():
        val = get_var(var, loaded)
        if val and val in defaults:
            if is_prod:
                fail(f"{var} is set to a dangerous default — CHANGE IT for production!")
                errors += 1
            else:
                warn(f"{var} is using a default value — change before deploying")

    # Check DEBUG in production
    debug_val = get_var("DEBUG", loaded)
    if is_prod and debug_val and debug_val.lower() in ("true", "1", "yes"):
        fail("DEBUG=True in production — this exposes sensitive information!")
        errors += 1

    # Production-required vars
    if is_prod:
        for var, desc in PRODUCTION_REQUIRED.items():
            val = get_var(var, loaded)
            if not val or val.strip() == "":
                fail(f"{var} — required in production ({desc})")
                errors += 1
            else:
                ok(f"{var} — set")

    if errors == 0:
        ok("No security issues detected")

    return errors


def check_database_connectivity(loaded: dict[str, str]) -> int:
    """Test PostgreSQL connection."""
    print(f"\n{BOLD}Database Connectivity{RESET}")
    db_url = get_var("DATABASE_URL", loaded)
    if not db_url:
        warn("DATABASE_URL not set — skipping connectivity check")
        return 0

    if db_url.startswith("sqlite"):
        ok(f"Using SQLite: {db_url}")
        return 0

    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(db_url, pool_pre_ping=True, pool_size=1)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        ok(f"PostgreSQL connection successful")
        engine.dispose()
        return 0
    except ImportError:
        warn("sqlalchemy not installed — skipping DB connectivity check")
        return 0
    except Exception as e:
        fail(f"PostgreSQL connection failed: {e}")
        return 1


def check_redis_connectivity(loaded: dict[str, str]) -> int:
    """Test Redis connection."""
    print(f"\n{BOLD}Redis Connectivity{RESET}")
    redis_url = get_var("REDIS_URL", loaded)
    if not redis_url:
        warn("REDIS_URL not set — skipping connectivity check")
        return 0

    try:
        import redis as redis_lib

        client = redis_lib.from_url(redis_url, socket_timeout=5)
        client.ping()
        ok("Redis connection successful")
        info = client.info("server")
        ok(f"Redis version: {info.get('redis_version', 'unknown')}")
        client.close()
        return 0
    except ImportError:
        warn("redis package not installed — skipping Redis connectivity check")
        return 0
    except Exception as e:
        fail(f"Redis connection failed: {e}")
        return 1


def main() -> None:
    strict = "--strict" in sys.argv

    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  TaskFlow — Environment Validation{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")

    loaded = load_dotenv_file()

    errors = 0
    warnings = 0

    errors += check_required(loaded)
    warnings += check_recommended(loaded)
    errors += check_production_security(loaded)
    errors += check_database_connectivity(loaded)
    errors += check_redis_connectivity(loaded)

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n{BOLD}{'─' * 60}{RESET}")
    if errors > 0:
        print(f"{RED}{BOLD}  FAILED{RESET} — {errors} error(s), {warnings} warning(s)")
        print(f"  Fix the errors above and re-run this script.")
        sys.exit(1)
    elif strict and warnings > 0:
        print(f"{YELLOW}{BOLD}  WARNINGS{RESET} — {warnings} warning(s) (strict mode)")
        print(f"  Fix warnings or re-run without --strict.")
        sys.exit(1)
    else:
        print(f"{GREEN}{BOLD}  PASSED{RESET} — environment is valid ({warnings} warning(s))")
        sys.exit(0)


if __name__ == "__main__":
    main()
