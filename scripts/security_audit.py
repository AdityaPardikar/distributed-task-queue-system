#!/usr/bin/env python3
"""
Security Audit Script — TaskFlow
==================================
Automated security checker that scans for common vulnerabilities:
  1. Dependency CVEs (pip-audit / npm audit)
  2. Hardcoded secrets & credentials
  3. SQL injection patterns
  4. CORS misconfiguration
  5. Insecure default settings
  6. Security header completeness

Usage:
    python scripts/security_audit.py              # Full audit
    python scripts/security_audit.py --quick      # Quick scan (no dependency check)
    python scripts/security_audit.py --json       # JSON output
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

# Project root
ROOT = Path(__file__).resolve().parent.parent

# ── Data Classes ─────────────────────────────────────────────────────────────


@dataclass
class Finding:
    """A single security finding."""

    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    category: str
    message: str
    file: str = ""
    line: int = 0
    recommendation: str = ""


@dataclass
class AuditReport:
    """Aggregate audit report."""

    findings: list[Finding] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    warnings: int = 0

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)
        if finding.severity in ("CRITICAL", "HIGH"):
            self.failed += 1
        elif finding.severity in ("MEDIUM", "LOW"):
            self.warnings += 1
        else:
            self.passed += 1

    def add_pass(self, category: str, message: str) -> None:
        self.passed += 1
        self.findings.append(Finding("INFO", category, message))

    @property
    def score(self) -> str:
        total = self.passed + self.failed + self.warnings
        if total == 0:
            return "N/A"
        pct = (self.passed / total) * 100
        if pct >= 90:
            return f"A ({pct:.0f}%)"
        if pct >= 75:
            return f"B ({pct:.0f}%)"
        if pct >= 60:
            return f"C ({pct:.0f}%)"
        return f"F ({pct:.0f}%)"


# ── Scanning Functions ───────────────────────────────────────────────────────

SECRET_PATTERNS: list[tuple[str, str]] = [
    (r'(?i)(password|secret|token|api_key|apikey)\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded secret/credential"),
    (r"(?i)-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----", "Private key in source code"),
    (r"(?i)(aws_access_key_id|aws_secret_access_key)\s*=\s*\S+", "AWS credential"),
    (r"ghp_[A-Za-z0-9_]{36}", "GitHub personal access token"),
    (r"sk-[A-Za-z0-9]{48}", "OpenAI API key"),
    (r"(?i)bearer\s+[A-Za-z0-9\-_.]+", "Hardcoded bearer token"),
]

SQL_INJECTION_PATTERNS: list[tuple[str, str]] = [
    (r'f["\'].*\b(SELECT|INSERT|UPDATE|DELETE|DROP)\b.*{', "Possible SQL injection via f-string"),
    (r'["\'].*\b(SELECT|INSERT|UPDATE|DELETE)\b.*["\']\s*%\s*', "Possible SQL injection via % formatting"),
    (r'\.execute\(\s*f["\']', "Raw SQL execute with f-string interpolation"),
    (r"\.execute\(\s*[\"'].*\+\s*", "Raw SQL execute with string concatenation"),
]

SKIP_DIRS = {
    "__pycache__", "node_modules", ".git", ".venv", "venv",
    "dist", "build", "htmlcov", ".mypy_cache", ".pytest_cache",
    "coverage", ".egg-info", "taskflow.egg-info",
}

SKIP_FILES = {
    "security_audit.py",  # Don't flag ourselves
    "package-lock.json",
    "coverage-final.json",
}


def _scan_files(root: Path, extensions: tuple[str, ...] = (".py", ".ts", ".tsx", ".js", ".jsx", ".env", ".yml", ".yaml")):
    """Yield (path, line_no, line_text) for all project source files."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if fname in SKIP_FILES:
                continue
            if not any(fname.endswith(ext) for ext in extensions):
                continue
            fpath = Path(dirpath) / fname
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                yield fpath, i, line


def scan_hardcoded_secrets(report: AuditReport) -> None:
    """Scan for hardcoded secrets and credentials."""
    found = False
    for fpath, lineno, line in _scan_files(ROOT):
        # Skip comments
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        for pattern, desc in SECRET_PATTERNS:
            if re.search(pattern, line):
                # Allow obvious placeholders
                lower = line.lower()
                if any(p in lower for p in ("example", "placeholder", "change-in-production", "your-", "xxx", "changeme", "TODO")):
                    continue
                report.add(Finding(
                    "HIGH", "Hardcoded Secret", desc,
                    str(fpath.relative_to(ROOT)), lineno,
                    "Use environment variables or a secrets manager instead.",
                ))
                found = True
    if not found:
        report.add_pass("Hardcoded Secret", "No hardcoded secrets detected")


def scan_sql_injection(report: AuditReport) -> None:
    """Scan for potential SQL injection patterns."""
    found = False
    for fpath, lineno, line in _scan_files(ROOT, (".py",)):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for pattern, desc in SQL_INJECTION_PATTERNS:
            if re.search(pattern, line):
                report.add(Finding(
                    "CRITICAL", "SQL Injection", desc,
                    str(fpath.relative_to(ROOT)), lineno,
                    "Use parameterized queries or SQLAlchemy ORM instead.",
                ))
                found = True
    if not found:
        report.add_pass("SQL Injection", "No SQL injection patterns detected")


def scan_cors_config(report: AuditReport) -> None:
    """Check CORS configuration for overly permissive origins."""
    settings_path = ROOT / "src" / "config" / "settings.py"
    if not settings_path.exists():
        report.add(Finding("MEDIUM", "CORS", "Settings file not found", "src/config/settings.py"))
        return

    text = settings_path.read_text(encoding="utf-8")

    # Check for wildcard origins
    if 'CORS_ORIGINS: str = "*"' in text or '"*"' in text:
        report.add(Finding(
            "HIGH", "CORS", "Wildcard (*) CORS origin detected",
            "src/config/settings.py", 0,
            "Restrict CORS_ORIGINS to specific domains in production.",
        ))
    else:
        report.add_pass("CORS", "CORS origins are not wildcard")

    # Check allow_methods = ["*"]
    main_path = ROOT / "src" / "api" / "main.py"
    if main_path.exists():
        main_text = main_path.read_text(encoding="utf-8")
        if 'allow_methods=["*"]' in main_text:
            report.add(Finding(
                "MEDIUM", "CORS", "allow_methods=['*'] allows all HTTP methods",
                "src/api/main.py", 0,
                "Restrict to specific methods: GET, POST, PUT, PATCH, DELETE, OPTIONS.",
            ))
        if 'allow_headers=["*"]' in main_text:
            report.add(Finding(
                "MEDIUM", "CORS", "allow_headers=['*'] allows all headers",
                "src/api/main.py", 0,
                "Restrict to specific headers: Authorization, Content-Type, etc.",
            ))


def scan_security_headers(report: AuditReport) -> None:
    """Verify security headers middleware is in place."""
    security_path = ROOT / "src" / "api" / "security.py"
    if security_path.exists():
        text = security_path.read_text(encoding="utf-8")
        headers_to_check = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "Referrer-Policy",
        ]
        for header in headers_to_check:
            if header in text:
                report.add_pass("Security Headers", f"{header} is configured")
            else:
                report.add(Finding(
                    "MEDIUM", "Security Headers", f"Missing {header} header",
                    "src/api/security.py", 0,
                    f"Add {header} to the security headers middleware.",
                ))
    else:
        report.add(Finding(
            "HIGH", "Security Headers", "Security headers middleware not found",
            "src/api/security.py", 0,
            "Create src/api/security.py with SecurityHeadersMiddleware.",
        ))


def scan_insecure_defaults(report: AuditReport) -> None:
    """Check for insecure default values in configuration."""
    settings_path = ROOT / "src" / "config" / "settings.py"
    if not settings_path.exists():
        return

    text = settings_path.read_text(encoding="utf-8")

    # DEBUG should be False in production defaults
    if 'DEBUG: bool = True' in text:
        report.add(Finding(
            "MEDIUM", "Config", "DEBUG defaults to True — ensure it is False in production",
            "src/config/settings.py", 0,
            "Set DEBUG=False in .env for production deployments.",
        ))

    # Default secret key
    if "your-secret-key" in text or "changeme" in text.lower():
        report.add(Finding(
            "HIGH", "Config", "Default SECRET_KEY detected in settings",
            "src/config/settings.py", 0,
            "Generate a strong random SECRET_KEY for production.",
        ))
    else:
        report.add_pass("Config", "No default SECRET_KEY placeholder found")

    # Check JWT expiration isn't too long
    if "JWT_EXPIRATION_HOURS: int = 24" in text:
        report.add(Finding(
            "LOW", "Config", "JWT access token expires in 24 hours — consider reducing to 1-4 hours",
            "src/config/settings.py", 0,
            "Reduce JWT_EXPIRATION_HOURS for better security.",
        ))


def scan_env_files(report: AuditReport) -> None:
    """Check that .env files are not committed (should be gitignored)."""
    gitignore = ROOT / ".gitignore"
    if gitignore.exists():
        text = gitignore.read_text(encoding="utf-8")
        if ".env" in text:
            report.add_pass("Environment", ".env is in .gitignore")
        else:
            report.add(Finding(
                "HIGH", "Environment", ".env is NOT in .gitignore",
                ".gitignore", 0,
                "Add .env to .gitignore to prevent committing secrets.",
            ))
    else:
        report.add(Finding(
            "MEDIUM", "Environment", "No .gitignore file found",
            "", 0,
            "Create a .gitignore file including .env patterns.",
        ))


def scan_dependencies(report: AuditReport, quick: bool = False) -> None:
    """Run pip-audit and npm audit for known CVEs."""
    if quick:
        report.add_pass("Dependencies", "Skipped (--quick mode)")
        return

    # pip-audit
    req_file = ROOT / "requirements.txt"
    if req_file.exists():
        try:
            result = subprocess.run(
                ["pip-audit", "-r", str(req_file), "--format", "json"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                report.add_pass("Dependencies", "pip-audit: no known vulnerabilities")
            else:
                try:
                    vulns = json.loads(result.stdout)
                    for v in vulns.get("dependencies", []):
                        for vuln in v.get("vulns", []):
                            report.add(Finding(
                                "HIGH", "Dependency CVE",
                                f"{v['name']}=={v['version']}: {vuln.get('id', 'unknown')} — {vuln.get('description', '')[:120]}",
                                "requirements.txt", 0,
                                f"Upgrade {v['name']} to a patched version.",
                            ))
                except (json.JSONDecodeError, KeyError):
                    report.add(Finding(
                        "MEDIUM", "Dependencies",
                        f"pip-audit reported issues: {result.stderr[:200]}",
                        "requirements.txt",
                    ))
        except FileNotFoundError:
            report.add(Finding(
                "LOW", "Dependencies", "pip-audit not installed — install with: pip install pip-audit",
                recommendation="pip install pip-audit",
            ))
        except subprocess.TimeoutExpired:
            report.add(Finding("LOW", "Dependencies", "pip-audit timed out"))

    # npm audit
    pkg_json = ROOT / "frontend" / "package.json"
    if pkg_json.exists():
        try:
            result = subprocess.run(
                ["npm", "audit", "--json", "--audit-level=high"],
                capture_output=True, text=True, timeout=120,
                cwd=str(ROOT / "frontend"),
            )
            if result.returncode == 0:
                report.add_pass("Dependencies", "npm audit: no high/critical vulnerabilities")
            else:
                try:
                    audit = json.loads(result.stdout)
                    total = audit.get("metadata", {}).get("vulnerabilities", {})
                    high = total.get("high", 0)
                    critical = total.get("critical", 0)
                    if high + critical > 0:
                        report.add(Finding(
                            "HIGH", "Dependency CVE",
                            f"npm audit: {critical} critical, {high} high vulnerabilities",
                            "frontend/package.json", 0,
                            "Run: cd frontend && npm audit fix",
                        ))
                    else:
                        report.add_pass("Dependencies", "npm audit: no high/critical vulnerabilities")
                except (json.JSONDecodeError, KeyError):
                    pass
        except FileNotFoundError:
            report.add(Finding("INFO", "Dependencies", "npm not found — skipping frontend audit"))
        except subprocess.TimeoutExpired:
            report.add(Finding("LOW", "Dependencies", "npm audit timed out"))


# ── Report Rendering ─────────────────────────────────────────────────────────

SEVERITY_COLORS = {
    "CRITICAL": "\033[91m",  # Red
    "HIGH": "\033[93m",      # Yellow
    "MEDIUM": "\033[33m",    # Orange
    "LOW": "\033[36m",       # Cyan
    "INFO": "\033[32m",      # Green
}
RESET = "\033[0m"


def print_report(report: AuditReport) -> None:
    """Pretty-print the audit report to stdout."""
    print("\n" + "=" * 72)
    print("  TASKFLOW SECURITY AUDIT REPORT")
    print("=" * 72)

    # Group by category
    categories: dict[str, list[Finding]] = {}
    for f in report.findings:
        categories.setdefault(f.category, []).append(f)

    for cat, findings in sorted(categories.items()):
        print(f"\n  [{cat}]")
        for f in findings:
            color = SEVERITY_COLORS.get(f.severity, "")
            icon = "PASS" if f.severity == "INFO" else f.severity
            loc = ""
            if f.file:
                loc = f"  {f.file}"
                if f.line:
                    loc += f":{f.line}"
            print(f"    {color}[{icon:>8}]{RESET} {f.message}{loc}")
            if f.recommendation and f.severity != "INFO":
                print(f"             -> {f.recommendation}")

    print("\n" + "-" * 72)
    print(f"  Score: {report.score}")
    print(f"  Passed: {report.passed}  |  Warnings: {report.warnings}  |  Failed: {report.failed}")
    print("=" * 72 + "\n")


def json_report(report: AuditReport) -> str:
    """Return the audit report as JSON."""
    return json.dumps({
        "score": report.score,
        "passed": report.passed,
        "warnings": report.warnings,
        "failed": report.failed,
        "findings": [asdict(f) for f in report.findings],
    }, indent=2)


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="TaskFlow Security Audit")
    parser.add_argument("--quick", action="store_true", help="Skip dependency scanning")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output as JSON")
    args = parser.parse_args()

    report = AuditReport()

    print("Running security audit..." if not args.json_output else "", file=sys.stderr)

    scan_hardcoded_secrets(report)
    scan_sql_injection(report)
    scan_cors_config(report)
    scan_security_headers(report)
    scan_insecure_defaults(report)
    scan_env_files(report)
    scan_dependencies(report, quick=args.quick)

    if args.json_output:
        print(json_report(report))
    else:
        print_report(report)

    # Exit with non-zero if any critical/high findings
    return 1 if report.failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
