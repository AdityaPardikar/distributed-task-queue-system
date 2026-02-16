"""Configuration validation and management.

Validates application configuration on startup, checks for required
secrets, validates database connectivity, and provides config diagnostics.
"""

import os
import re
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a single config validation check."""

    check_name: str
    passed: bool
    message: str
    severity: str = "error"  # error, warning, info
    value: Optional[str] = None


@dataclass
class ConfigValidationReport:
    """Full configuration validation report."""

    valid: bool
    results: list[ValidationResult] = field(default_factory=list)
    errors: int = 0
    warnings: int = 0

    def add(self, result: ValidationResult):
        self.results.append(result)
        if not result.passed:
            if result.severity == "error":
                self.errors += 1
                self.valid = False
            elif result.severity == "warning":
                self.warnings += 1

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "checks": [
                {
                    "check": r.check_name,
                    "passed": r.passed,
                    "message": r.message,
                    "severity": r.severity,
                }
                for r in self.results
            ],
        }


class ConfigValidator:
    """Validates application configuration."""

    REQUIRED_ENV_VARS = [
        "DATABASE_URL",
    ]

    RECOMMENDED_ENV_VARS = [
        "SECRET_KEY",
        "REDIS_URL",
        "LOG_LEVEL",
    ]

    SECRET_PATTERNS = [
        ("DATABASE_URL", r"password"),
        ("SECRET_KEY", r".+"),
        ("REDIS_URL", r"password"),
    ]

    WEAK_SECRET_PATTERNS = [
        r"^password$",
        r"^secret$",
        r"^123456",
        r"^admin$",
        r"^changeme$",
        r"^default$",
    ]

    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file
        self._env_vars: dict[str, str] = {}
        if env_file and os.path.exists(env_file):
            self._load_env_file(env_file)

    def _load_env_file(self, filepath: str):
        """Load .env file variables."""
        try:
            with open(filepath) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        self._env_vars[key.strip()] = value.strip().strip('"').strip("'")
        except Exception as e:
            logger.warning("Failed to load .env file: %s", e)

    def validate_all(self) -> ConfigValidationReport:
        """Run all configuration validations."""
        report = ConfigValidationReport(valid=True)

        self._check_required_env_vars(report)
        self._check_recommended_env_vars(report)
        self._check_database_url(report)
        self._check_secret_key(report)
        self._check_redis_url(report)
        self._check_cors_settings(report)
        self._check_log_level(report)
        self._check_port_settings(report)
        self._check_weak_secrets(report)

        return report

    def _get_var(self, name: str) -> Optional[str]:
        """Get config variable from env or .env file."""
        return os.environ.get(name) or self._env_vars.get(name)

    def _check_required_env_vars(self, report: ConfigValidationReport):
        """Check that required environment variables are set."""
        for var in self.REQUIRED_ENV_VARS:
            value = self._get_var(var)
            if value:
                report.add(ValidationResult(
                    check_name=f"required_var_{var}",
                    passed=True,
                    message=f"Required variable {var} is set",
                    severity="error",
                ))
            else:
                report.add(ValidationResult(
                    check_name=f"required_var_{var}",
                    passed=False,
                    message=f"Required variable {var} is not set",
                    severity="error",
                ))

    def _check_recommended_env_vars(self, report: ConfigValidationReport):
        """Check recommended environment variables."""
        for var in self.RECOMMENDED_ENV_VARS:
            value = self._get_var(var)
            if value:
                report.add(ValidationResult(
                    check_name=f"recommended_var_{var}",
                    passed=True,
                    message=f"Recommended variable {var} is set",
                    severity="info",
                ))
            else:
                report.add(ValidationResult(
                    check_name=f"recommended_var_{var}",
                    passed=False,
                    message=f"Recommended variable {var} is not set",
                    severity="warning",
                ))

    def _check_database_url(self, report: ConfigValidationReport):
        """Validate DATABASE_URL format."""
        db_url = self._get_var("DATABASE_URL")
        if not db_url:
            return

        valid_prefixes = ("postgresql://", "sqlite:///", "mysql://", "postgresql+asyncpg://")
        if any(db_url.startswith(p) for p in valid_prefixes):
            report.add(ValidationResult(
                check_name="database_url_format",
                passed=True,
                message="DATABASE_URL has valid format",
            ))

            # Check for production readiness
            if db_url.startswith("sqlite"):
                report.add(ValidationResult(
                    check_name="database_production",
                    passed=False,
                    message="SQLite is not recommended for production",
                    severity="warning",
                ))
            elif "localhost" in db_url or "127.0.0.1" in db_url:
                report.add(ValidationResult(
                    check_name="database_production",
                    passed=True,
                    message="Database URL points to localhost (check for production)",
                    severity="info",
                ))
        else:
            report.add(ValidationResult(
                check_name="database_url_format",
                passed=False,
                message=f"DATABASE_URL has unexpected format: {db_url[:20]}...",
                severity="error",
            ))

    def _check_secret_key(self, report: ConfigValidationReport):
        """Validate SECRET_KEY strength."""
        secret = self._get_var("SECRET_KEY")
        if not secret:
            report.add(ValidationResult(
                check_name="secret_key_present",
                passed=False,
                message="SECRET_KEY not set, using default (insecure)",
                severity="warning",
            ))
            return

        if len(secret) < 32:
            report.add(ValidationResult(
                check_name="secret_key_length",
                passed=False,
                message=f"SECRET_KEY is too short ({len(secret)} chars, recommend 32+)",
                severity="warning",
            ))
        else:
            report.add(ValidationResult(
                check_name="secret_key_length",
                passed=True,
                message="SECRET_KEY has adequate length",
            ))

    def _check_redis_url(self, report: ConfigValidationReport):
        """Check Redis configuration."""
        redis_url = self._get_var("REDIS_URL")
        if redis_url:
            if redis_url.startswith("redis://") or redis_url.startswith("rediss://"):
                report.add(ValidationResult(
                    check_name="redis_url_format",
                    passed=True,
                    message="REDIS_URL has valid format",
                ))
            else:
                report.add(ValidationResult(
                    check_name="redis_url_format",
                    passed=False,
                    message="REDIS_URL has unexpected format",
                    severity="warning",
                ))

    def _check_cors_settings(self, report: ConfigValidationReport):
        """Check CORS configuration."""
        cors_origins = self._get_var("CORS_ORIGINS")
        if cors_origins:
            if "*" in cors_origins:
                report.add(ValidationResult(
                    check_name="cors_wildcard",
                    passed=False,
                    message="CORS allows all origins (*) - insecure for production",
                    severity="warning",
                ))
            else:
                report.add(ValidationResult(
                    check_name="cors_origins",
                    passed=True,
                    message="CORS origins are restricted",
                ))

    def _check_log_level(self, report: ConfigValidationReport):
        """Validate LOG_LEVEL setting."""
        log_level = self._get_var("LOG_LEVEL")
        valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if log_level:
            if log_level.upper() in valid_levels:
                report.add(ValidationResult(
                    check_name="log_level",
                    passed=True,
                    message=f"LOG_LEVEL is valid: {log_level.upper()}",
                ))
                if log_level.upper() == "DEBUG":
                    report.add(ValidationResult(
                        check_name="log_level_production",
                        passed=False,
                        message="DEBUG log level should not be used in production",
                        severity="warning",
                    ))
            else:
                report.add(ValidationResult(
                    check_name="log_level",
                    passed=False,
                    message=f"Invalid LOG_LEVEL: {log_level}. Valid: {valid_levels}",
                    severity="warning",
                ))

    def _check_port_settings(self, report: ConfigValidationReport):
        """Validate port configuration."""
        port = self._get_var("PORT") or self._get_var("API_PORT")
        if port:
            try:
                port_int = int(port)
                if 1 <= port_int <= 65535:
                    report.add(ValidationResult(
                        check_name="port_valid",
                        passed=True,
                        message=f"Port {port_int} is valid",
                    ))
                else:
                    report.add(ValidationResult(
                        check_name="port_valid",
                        passed=False,
                        message=f"Port {port_int} is out of range (1-65535)",
                        severity="error",
                    ))
            except ValueError:
                report.add(ValidationResult(
                    check_name="port_valid",
                    passed=False,
                    message=f"Port '{port}' is not a valid number",
                    severity="error",
                ))

    def _check_weak_secrets(self, report: ConfigValidationReport):
        """Check for weak/default passwords in configuration."""
        for var_name in ("SECRET_KEY", "DATABASE_URL", "REDIS_URL"):
            value = self._get_var(var_name)
            if not value:
                continue

            for pattern in self.WEAK_SECRET_PATTERNS:
                # Extract password portion from URLs
                if "://" in value:
                    match = re.search(r":([^:@]+)@", value)
                    if match and re.match(pattern, match.group(1), re.IGNORECASE):
                        report.add(ValidationResult(
                            check_name=f"weak_secret_{var_name}",
                            passed=False,
                            message=f"{var_name} contains a weak/default password",
                            severity="warning",
                        ))
                        break
                elif re.match(pattern, value, re.IGNORECASE):
                    report.add(ValidationResult(
                        check_name=f"weak_secret_{var_name}",
                        passed=False,
                        message=f"{var_name} value appears to be a weak/default secret",
                        severity="warning",
                    ))
                    break

    def get_current_config(self) -> dict:
        """Get current configuration summary (values masked)."""
        config = {}
        all_vars = set(self.REQUIRED_ENV_VARS + self.RECOMMENDED_ENV_VARS)
        all_vars.update(["CORS_ORIGINS", "PORT", "API_PORT", "DEBUG", "ENVIRONMENT"])

        for var in sorted(all_vars):
            value = self._get_var(var)
            if value:
                # Mask sensitive values
                if any(s in var.upper() for s in ("SECRET", "PASSWORD", "KEY", "TOKEN")):
                    config[var] = f"***set*** ({len(value)} chars)"
                elif "URL" in var.upper() and "://" in value:
                    # Mask password in URLs
                    config[var] = re.sub(r":([^:@]+)@", ":***@", value)
                else:
                    config[var] = value
            else:
                config[var] = None

        return config
