"""Locust load testing configuration for TaskFlow API.

Run with: locust -f tests/load/locustfile.py --host http://localhost:8000
"""

import random
import string

from locust import HttpUser, task, between, tag


def random_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


class TaskFlowUser(HttpUser):
    """Simulates a typical TaskFlow user."""

    wait_time = between(0.5, 2)
    token: str = ""

    def on_start(self):
        """Login at the start of each user session."""
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token", "")

    @property
    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(10)
    @tag("read", "tasks")
    def list_tasks(self):
        """List tasks with pagination."""
        page = random.randint(1, 5)
        self.client.get(
            f"/api/v1/tasks?page={page}&page_size=20",
            headers=self.auth_headers,
            name="/api/v1/tasks",
        )

    @task(5)
    @tag("write", "tasks")
    def create_task(self):
        """Create a new task."""
        self.client.post(
            "/api/v1/tasks",
            json={
                "task_name": f"load_test_{random_string()}",
                "priority": random.randint(1, 10),
                "task_args": {"key": random_string()},
            },
            headers=self.auth_headers,
            name="/api/v1/tasks [POST]",
        )

    @task(8)
    @tag("read", "dashboard")
    def get_dashboard(self):
        """Fetch dashboard data."""
        self.client.get(
            "/api/v1/dashboard/summary",
            headers=self.auth_headers,
            name="/api/v1/dashboard/summary",
        )

    @task(3)
    @tag("read", "analytics")
    def get_analytics(self):
        """Fetch analytics."""
        self.client.get(
            "/api/v1/analytics/summary",
            headers=self.auth_headers,
            name="/api/v1/analytics/summary",
        )

    @task(6)
    @tag("read", "workers")
    def list_workers(self):
        """List workers."""
        self.client.get(
            "/api/v1/workers",
            headers=self.auth_headers,
            name="/api/v1/workers",
        )

    @task(2)
    @tag("read", "metrics")
    def get_metrics(self):
        """Fetch metrics."""
        self.client.get(
            "/api/v1/metrics/summary",
            headers=self.auth_headers,
            name="/api/v1/metrics/summary",
        )

    @task(15)
    @tag("read", "health")
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health", name="/health")

    @task(4)
    @tag("read", "search")
    def search_tasks(self):
        """Search for tasks."""
        self.client.get(
            f"/api/v1/search/tasks?q={random_string(4)}",
            headers=self.auth_headers,
            name="/api/v1/search/tasks",
        )

    @task(3)
    @tag("read", "performance")
    def get_performance_stats(self):
        """Performance monitoring."""
        self.client.get(
            "/api/v1/performance/stats",
            headers=self.auth_headers,
            name="/api/v1/performance/stats",
        )


class AdminUser(HttpUser):
    """Simulates an admin performing heavier operations."""

    wait_time = between(2, 5)
    weight = 1  # 1 admin per 3 regular users
    token: str = ""

    def on_start(self):
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token", "")

    @property
    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(3)
    @tag("admin", "performance")
    def check_database_health(self):
        self.client.get(
            "/api/v1/performance/database/info",
            headers=self.auth_headers,
            name="/api/v1/performance/database/info",
        )

    @task(2)
    @tag("admin", "performance")
    def check_endpoints(self):
        self.client.get(
            "/api/v1/performance/endpoints",
            headers=self.auth_headers,
            name="/api/v1/performance/endpoints",
        )

    @task(1)
    @tag("admin", "campaigns")
    def list_campaigns(self):
        self.client.get(
            "/api/v1/campaigns",
            headers=self.auth_headers,
            name="/api/v1/campaigns",
        )
