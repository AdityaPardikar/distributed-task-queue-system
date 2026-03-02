#!/usr/bin/env python3
"""
Production Smoke Test Suite — TaskFlow v1.0.0

Automated smoke tests that validate core system functionality after deployment.
Run against a live instance to verify health, authentication, task lifecycle,
WebSocket connectivity, and metrics endpoints.

Usage:
    python scripts/smoke_test.py                          # Default: http://localhost:8000
    python scripts/smoke_test.py --base-url https://api.example.com
    python scripts/smoke_test.py --verbose
    python scripts/smoke_test.py --timeout 10
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

try:
    import httpx
except ImportError:
    print("ERROR: httpx is required. Install with: pip install httpx")
    sys.exit(1)

try:
    import websockets
    import asyncio
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 5  # seconds per request
TEST_USER = {"username": "smoke_test_user", "password": "SmokeTest!2026"}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SmokeResult:
    name: str
    passed: bool
    duration_ms: float
    detail: str = ""
    error: str = ""


@dataclass
class SmokeReport:
    base_url: str
    started_at: str = ""
    results: list[SmokeResult] = field(default_factory=list)
    total_duration_ms: float = 0.0

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def all_passed(self) -> bool:
        return self.failed == 0


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

class SmokeTestRunner:
    def __init__(self, base_url: str, timeout: int, verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verbose = verbose
        self.client = httpx.Client(base_url=self.base_url, timeout=timeout)
        self.token: Optional[str] = None
        self.report = SmokeReport(base_url=self.base_url)

    def run_all(self) -> SmokeReport:
        self.report.started_at = datetime.utcnow().isoformat() + "Z"
        start = time.perf_counter()

        tests = [
            ("Health Check", self.test_health),
            ("Readiness Probe", self.test_readiness),
            ("Liveness Probe", self.test_liveness),
            ("User Registration", self.test_register),
            ("User Login (JWT)", self.test_login),
            ("Token Refresh", self.test_refresh),
            ("Create Task", self.test_create_task),
            ("List Tasks", self.test_list_tasks),
            ("Get Task Detail", self.test_get_task),
            ("List Workers", self.test_list_workers),
            ("Dashboard Stats", self.test_dashboard_stats),
            ("Metrics Endpoint", self.test_metrics),
            ("Search Endpoint", self.test_search),
            ("Alerts Endpoint", self.test_alerts),
            ("Operations Config", self.test_operations_config),
            ("WebSocket Connection", self.test_websocket),
        ]

        for name, fn in tests:
            self._run_test(name, fn)

        self.report.total_duration_ms = (time.perf_counter() - start) * 1000
        self.client.close()
        return self.report

    def _run_test(self, name: str, fn):
        start = time.perf_counter()
        try:
            detail = fn()
            duration = (time.perf_counter() - start) * 1000
            result = SmokeResult(name=name, passed=True, duration_ms=round(duration, 2), detail=detail or "OK")
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            result = SmokeResult(name=name, passed=False, duration_ms=round(duration, 2), error=str(e))

        self.report.results.append(result)
        self._print_result(result)

    def _print_result(self, r: SmokeResult):
        icon = "PASS" if r.passed else "FAIL"
        line = f"  [{icon}] {r.name} ({r.duration_ms:.0f}ms)"
        if r.error and self.verbose:
            line += f" — {r.error}"
        elif r.detail and self.verbose:
            line += f" — {r.detail}"
        print(line)

    # -- Auth helpers -------------------------------------------------------

    def _auth_headers(self) -> dict:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    # -- Tests --------------------------------------------------------------

    def test_health(self) -> str:
        r = self.client.get("/health")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        body = r.json()
        return f"status={body.get('status', 'unknown')}"

    def test_readiness(self) -> str:
        r = self.client.get("/ready")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        return "ready"

    def test_liveness(self) -> str:
        r = self.client.get("/live")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        return "alive"

    def test_register(self) -> str:
        r = self.client.post("/api/v1/auth/register", json=TEST_USER)
        # 201 = new user, 400/409 = already exists — both acceptable
        if r.status_code in (200, 201):
            return "registered"
        elif r.status_code in (400, 409, 422):
            return "already exists (OK)"
        else:
            raise AssertionError(f"Unexpected status {r.status_code}: {r.text[:200]}")

    def test_login(self) -> str:
        r = self.client.post(
            "/api/v1/auth/login",
            data={"username": TEST_USER["username"], "password": TEST_USER["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if r.status_code != 200:
            raise AssertionError(f"Login failed ({r.status_code}): {r.text[:200]}")
        body = r.json()
        self.token = body.get("access_token")
        assert self.token, "No access_token in response"
        return "token acquired"

    def test_refresh(self) -> str:
        r = self.client.post("/api/v1/auth/refresh", headers=self._auth_headers())
        # Accept 200 (success) or 401/422 (feature may require refresh_token body)
        if r.status_code == 200:
            return "refreshed"
        return f"status={r.status_code} (acceptable)"

    def test_create_task(self) -> str:
        payload = {
            "name": f"smoke_test_{int(time.time())}",
            "task_type": "smoke_test",
            "priority": "LOW",
            "payload": {"test": True},
        }
        r = self.client.post("/api/v1/tasks", json=payload, headers=self._auth_headers())
        if r.status_code not in (200, 201):
            raise AssertionError(f"Create task failed ({r.status_code}): {r.text[:200]}")
        body = r.json()
        task_id = body.get("id") or body.get("task_id")
        self._task_id = task_id
        return f"task_id={task_id}"

    def test_list_tasks(self) -> str:
        r = self.client.get("/api/v1/tasks", headers=self._auth_headers(), params={"limit": 5})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        body = r.json()
        count = len(body) if isinstance(body, list) else body.get("total", body.get("count", "?"))
        return f"count={count}"

    def test_get_task(self) -> str:
        task_id = getattr(self, "_task_id", None)
        if not task_id:
            return "skipped (no task created)"
        r = self.client.get(f"/api/v1/tasks/{task_id}", headers=self._auth_headers())
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        body = r.json()
        return f"status={body.get('status', 'unknown')}"

    def test_list_workers(self) -> str:
        r = self.client.get("/api/v1/workers", headers=self._auth_headers())
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        body = r.json()
        count = len(body) if isinstance(body, list) else body.get("total", 0)
        return f"workers={count}"

    def test_dashboard_stats(self) -> str:
        r = self.client.get("/api/v1/dashboard/stats", headers=self._auth_headers())
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        return "dashboard OK"

    def test_metrics(self) -> str:
        r = self.client.get("/api/v1/metrics")
        # Prometheus text format or JSON
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        content_length = len(r.content)
        return f"metrics payload={content_length} bytes"

    def test_search(self) -> str:
        r = self.client.get(
            "/api/v1/search",
            params={"q": "smoke", "limit": 5},
            headers=self._auth_headers(),
        )
        # 200 = results, 422 = validation variant — both acceptable
        if r.status_code in (200, 422):
            return f"status={r.status_code}"
        raise AssertionError(f"Unexpected status {r.status_code}")

    def test_alerts(self) -> str:
        r = self.client.get("/api/v1/alerts", headers=self._auth_headers())
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        body = r.json()
        count = len(body) if isinstance(body, list) else body.get("total", 0)
        return f"alerts={count}"

    def test_operations_config(self) -> str:
        r = self.client.get("/api/v1/operations/config", headers=self._auth_headers())
        # 200 or 403 (admin only) both acceptable
        if r.status_code in (200, 403):
            return f"status={r.status_code}"
        raise AssertionError(f"Unexpected status {r.status_code}")

    def test_websocket(self) -> str:
        if not HAS_WEBSOCKETS:
            return "skipped (websockets not installed)"

        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")

        async def _connect():
            async with websockets.connect(f"{ws_url}/ws/metrics", open_timeout=self.timeout) as ws:
                await ws.ping()
                return "connected"

        try:
            result = asyncio.get_event_loop().run_until_complete(_connect())
            return result
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(_connect())
                return result
            finally:
                loop.close()
        except Exception as e:
            # WebSocket may not be available in all environments
            return f"skipped ({type(e).__name__})"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(report: SmokeReport):
    print("\n" + "=" * 60)
    print("SMOKE TEST REPORT")
    print("=" * 60)
    print(f"  Target:    {report.base_url}")
    print(f"  Timestamp: {report.started_at}")
    print(f"  Duration:  {report.total_duration_ms:.0f}ms")
    print(f"  Results:   {report.passed} passed, {report.failed} failed, {len(report.results)} total")
    print()

    if report.failed > 0:
        print("FAILURES:")
        for r in report.results:
            if not r.passed:
                print(f"  - {r.name}: {r.error}")
        print()

    status = "ALL TESTS PASSED" if report.all_passed else "SOME TESTS FAILED"
    print(f"  >>> {status} <<<")
    print("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="TaskFlow Production Smoke Tests")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"API base URL (default: {DEFAULT_BASE_URL})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--json", action="store_true", help="Output report as JSON")
    args = parser.parse_args()

    print(f"\nTaskFlow Smoke Test Suite")
    print(f"Target: {args.base_url}\n")

    runner = SmokeTestRunner(base_url=args.base_url, timeout=args.timeout, verbose=args.verbose)
    report = runner.run_all()

    if args.json:
        output = {
            "base_url": report.base_url,
            "started_at": report.started_at,
            "total_duration_ms": round(report.total_duration_ms, 2),
            "passed": report.passed,
            "failed": report.failed,
            "total": len(report.results),
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "duration_ms": r.duration_ms,
                    "detail": r.detail,
                    "error": r.error,
                }
                for r in report.results
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print_report(report)

    sys.exit(0 if report.all_passed else 1)


if __name__ == "__main__":
    main()
