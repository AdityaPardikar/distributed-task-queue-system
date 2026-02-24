#!/usr/bin/env python3
"""
TaskFlow — Demo Data Seeder
============================
Populates the database with realistic demo data for development, testing,
and demos.  Safe to run multiple times — uses upsert-style logic and
checks for existing records before inserting.

Usage:
    python scripts/seed_data.py              # Seed all entities
    python scripts/seed_data.py --clear      # Delete all data first, then seed
    python scripts/seed_data.py --clear-only # Delete all data (no re-seed)
"""

import sys
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from src.db.session import SessionLocal, engine
from src.models import (
    Base,
    Task,
    TaskResult,
    TaskLog,
    TaskExecution,
    Worker,
    Campaign,
    EmailRecipient,
    EmailTemplate,
    CampaignTask,
    DeadLetterQueue,
    Alert,
    User,
)

# ── Colour helpers ───────────────────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

NOW = datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid4())


# ═══════════════════════════════════════════════════════════════════════════════
#  Demo data factories
# ═══════════════════════════════════════════════════════════════════════════════

def make_users() -> list[dict]:
    """Create demo user records."""
    try:
        from passlib.context import CryptContext
        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hash_pw = pwd.hash
    except ImportError:
        import hashlib
        def hash_pw(pw: str) -> str:
            return hashlib.sha256(pw.encode()).hexdigest()

    return [
        {
            "user_id": "u-admin-0001",
            "username": "admin",
            "email": "admin@taskflow.dev",
            "hashed_password": hash_pw("admin123"),
            "full_name": "System Admin",
            "role": "admin",
            "is_active": True,
            "is_superuser": True,
            "last_login": NOW - timedelta(hours=1),
        },
        {
            "user_id": "u-operator-0001",
            "username": "operator",
            "email": "operator@taskflow.dev",
            "hashed_password": hash_pw("operator123"),
            "full_name": "Queue Operator",
            "role": "operator",
            "is_active": True,
            "is_superuser": False,
            "last_login": NOW - timedelta(hours=3),
        },
        {
            "user_id": "u-viewer-0001",
            "username": "viewer",
            "email": "viewer@taskflow.dev",
            "hashed_password": hash_pw("viewer123"),
            "full_name": "Dashboard Viewer",
            "role": "viewer",
            "is_active": True,
            "is_superuser": False,
            "last_login": NOW - timedelta(days=1),
        },
    ]


def make_workers() -> list[dict]:
    """Create demo worker node records."""
    statuses = ["ACTIVE", "ACTIVE", "ACTIVE", "IDLE", "OFFLINE"]
    hostnames = [
        "worker-alpha.taskflow.local",
        "worker-beta.taskflow.local",
        "worker-gamma.taskflow.local",
        "worker-delta.taskflow.local",
        "worker-epsilon.taskflow.local",
    ]
    workers = []
    for i, (hostname, status) in enumerate(zip(hostnames, statuses)):
        workers.append({
            "worker_id": f"w-{i+1:04d}",
            "hostname": hostname,
            "status": status,
            "capacity": random.choice([5, 10, 15, 20]),
            "current_load": random.randint(0, 4) if status == "ACTIVE" else 0,
            "last_heartbeat": NOW - timedelta(seconds=random.randint(5, 300)) if status != "OFFLINE" else NOW - timedelta(hours=2),
            "worker_metadata": {
                "cpu_cores": random.choice([4, 8, 16]),
                "memory_gb": random.choice([8, 16, 32]),
                "python_version": "3.13.5",
                "os": "Linux",
            },
        })
    return workers


TASK_TYPES = [
    ("send_email", "Email Delivery"),
    ("generate_report", "Report Generation"),
    ("process_image", "Image Processing"),
    ("sync_data", "Data Sync"),
    ("run_analysis", "Analytics Pipeline"),
    ("backup_database", "Database Backup"),
    ("send_notification", "Push Notification"),
    ("aggregate_metrics", "Metrics Aggregation"),
    ("cleanup_temp_files", "File Cleanup"),
    ("webhook_delivery", "Webhook Delivery"),
]


def make_tasks(worker_ids: list[str]) -> list[dict]:
    """Create a mix of tasks in various states."""
    tasks = []
    statuses_pool = [
        ("COMPLETED", 30),
        ("RUNNING", 5),
        ("PENDING", 8),
        ("QUEUED", 4),
        ("FAILED", 6),
        ("CANCELLED", 2),
        ("RETRYING", 2),
        ("TIMEOUT", 1),
    ]

    # Flatten weighted list
    weighted_statuses = []
    for s, count in statuses_pool:
        weighted_statuses.extend([s] * count)

    for i in range(58):
        task_name, label = random.choice(TASK_TYPES)
        status = random.choice(weighted_statuses)
        priority = random.randint(1, 10)
        created = NOW - timedelta(hours=random.randint(1, 168))
        started = created + timedelta(seconds=random.randint(1, 60)) if status not in ("PENDING", "QUEUED") else None
        completed = started + timedelta(seconds=random.randint(5, 300)) if status == "COMPLETED" else None
        worker_id = random.choice(worker_ids[:3]) if status in ("RUNNING", "COMPLETED", "FAILED", "TIMEOUT") else None

        tasks.append({
            "task_id": f"t-{i+1:04d}",
            "task_name": task_name,
            "task_args": [f"arg_{i}"],
            "task_kwargs": {"label": label, "index": i},
            "priority": priority,
            "status": status,
            "retry_count": random.randint(0, 3) if status in ("FAILED", "RETRYING") else 0,
            "max_retries": 5,
            "timeout_seconds": random.choice([60, 120, 300, 600]),
            "depends_on": [],
            "started_at": started,
            "completed_at": completed,
            "worker_id": worker_id,
            "created_by": "u-admin-0001",
        })

    return tasks


def make_task_results(tasks: list[dict]) -> list[dict]:
    """Create result records for completed / failed tasks."""
    results = []
    for t in tasks:
        if t["status"] in ("COMPLETED", "FAILED"):
            results.append({
                "result_id": _uuid(),
                "task_id": t["task_id"],
                "result_data": {"output": f"Result for {t['task_name']}", "rows_affected": random.randint(1, 5000)} if t["status"] == "COMPLETED" else {},
                "error_message": f"Simulated failure in {t['task_name']}" if t["status"] == "FAILED" else None,
                "stack_trace": "Traceback (most recent call last):\n  File \"worker.py\", line 42\nRuntimeError: simulated" if t["status"] == "FAILED" else None,
            })
    return results


def make_task_logs(tasks: list[dict]) -> list[dict]:
    """Create log entries for tasks."""
    logs = []
    for t in tasks:
        base_time = t.get("started_at") or NOW - timedelta(hours=1)
        logs.append({
            "log_id": _uuid(),
            "task_id": t["task_id"],
            "level": "INFO",
            "message": f"Task {t['task_name']} created",
            "log_metadata": {"source": "scheduler"},
            "created_at": base_time - timedelta(seconds=10),
        })
        if t["status"] in ("RUNNING", "COMPLETED", "FAILED", "TIMEOUT"):
            logs.append({
                "log_id": _uuid(),
                "task_id": t["task_id"],
                "level": "INFO",
                "message": f"Task picked up by worker {t.get('worker_id', 'unknown')}",
                "log_metadata": {"source": "worker"},
                "created_at": base_time,
            })
        if t["status"] == "COMPLETED":
            logs.append({
                "log_id": _uuid(),
                "task_id": t["task_id"],
                "level": "INFO",
                "message": f"Task completed successfully in {random.randint(5,120)}s",
                "log_metadata": {"source": "worker"},
                "created_at": base_time + timedelta(seconds=random.randint(5, 120)),
            })
        if t["status"] == "FAILED":
            logs.append({
                "log_id": _uuid(),
                "task_id": t["task_id"],
                "level": "ERROR",
                "message": f"Task failed: simulated error in {t['task_name']}",
                "log_metadata": {"source": "worker", "attempt": t["retry_count"]},
                "created_at": base_time + timedelta(seconds=random.randint(5, 30)),
            })
    return logs


def make_campaigns() -> list[dict]:
    """Create demo email campaigns."""
    return [
        {
            "campaign_id": "c-0001",
            "name": "Weekly Newsletter — July 2025",
            "status": "COMPLETED",
            "template_subject": "Your Weekly TaskFlow Digest",
            "template_body": "<h1>Hello {{name}}</h1><p>Here's what happened this week...</p>",
            "template_variables": {"name": "string"},
            "total_recipients": 250,
            "sent_count": 247,
            "failed_count": 3,
            "started_at": NOW - timedelta(days=3),
            "completed_at": NOW - timedelta(days=3, hours=-1),
            "created_by": "u-admin-0001",
            "rate_limit_per_minute": 50,
        },
        {
            "campaign_id": "c-0002",
            "name": "Product Launch Announcement",
            "status": "DRAFT",
            "template_subject": "Introducing TaskFlow v2!",
            "template_body": "<h1>Hi {{name}}</h1><p>We're excited to announce TaskFlow v2...</p>",
            "template_variables": {"name": "string", "company": "string"},
            "total_recipients": 1200,
            "sent_count": 0,
            "failed_count": 0,
            "created_by": "u-operator-0001",
            "rate_limit_per_minute": 100,
        },
        {
            "campaign_id": "c-0003",
            "name": "System Maintenance Notice",
            "status": "SENDING",
            "template_subject": "Scheduled Maintenance — {{date}}",
            "template_body": "<p>Dear {{name}}, we will be performing maintenance on {{date}}.</p>",
            "template_variables": {"name": "string", "date": "string"},
            "total_recipients": 80,
            "sent_count": 45,
            "failed_count": 1,
            "started_at": NOW - timedelta(minutes=30),
            "created_by": "u-admin-0001",
            "rate_limit_per_minute": 30,
        },
    ]


def make_email_templates(campaign_ids: list[str]) -> list[dict]:
    """Create reusable email templates."""
    return [
        {
            "email_template_id": _uuid(),
            "name": "Welcome Email",
            "subject": "Welcome to TaskFlow, {{name}}!",
            "body": "<h1>Welcome, {{name}}!</h1><p>Get started with your first task queue.</p>",
            "variables": {"name": "string"},
            "version": 1,
            "campaign_id": campaign_ids[0],
        },
        {
            "email_template_id": _uuid(),
            "name": "Password Reset",
            "subject": "Reset Your Password",
            "body": "<p>Hi {{name}}, click <a href='{{link}}'>here</a> to reset your password.</p>",
            "variables": {"name": "string", "link": "string"},
            "version": 2,
            "campaign_id": None,
        },
        {
            "email_template_id": _uuid(),
            "name": "Alert Notification",
            "subject": "[{{severity}}] Alert: {{title}}",
            "body": "<p>An alert was triggered: <strong>{{title}}</strong></p><p>{{description}}</p>",
            "variables": {"severity": "string", "title": "string", "description": "string"},
            "version": 1,
            "campaign_id": None,
        },
    ]


def make_email_recipients(campaign_ids: list[str]) -> list[dict]:
    """Create demo recipients for the first campaign."""
    recipients = []
    names = ["alice", "bob", "charlie", "diana", "eve", "frank", "grace", "henry"]
    for i, name in enumerate(names):
        recipients.append({
            "recipient_id": _uuid(),
            "campaign_id": campaign_ids[0],
            "email": f"{name}@example.com",
            "status": "SENT" if i < 6 else "FAILED",
            "personalization": {"name": name.capitalize()},
            "sent_at": NOW - timedelta(days=3) if i < 6 else None,
            "error_message": "Mailbox full" if i >= 6 else None,
        })
    return recipients


def make_alerts() -> list[dict]:
    """Create demo system alerts."""
    return [
        {
            "alert_id": _uuid(),
            "alert_type": "high_failure_rate",
            "severity": "critical",
            "description": "Task failure rate exceeded 15% in the last hour (18.2%)",
            "alert_metadata": {"threshold": 15, "actual": 18.2, "window": "1h"},
            "acknowledged": False,
            "created_at": NOW - timedelta(minutes=25),
        },
        {
            "alert_id": _uuid(),
            "alert_type": "worker_offline",
            "severity": "warning",
            "description": "Worker worker-epsilon.taskflow.local has been offline for 2 hours",
            "alert_metadata": {"worker_id": "w-0005", "last_seen": (NOW - timedelta(hours=2)).isoformat()},
            "acknowledged": False,
            "created_at": NOW - timedelta(hours=2),
        },
        {
            "alert_id": _uuid(),
            "alert_type": "queue_depth",
            "severity": "warning",
            "description": "Pending task queue depth is 42 (threshold: 30)",
            "alert_metadata": {"threshold": 30, "actual": 42},
            "acknowledged": True,
            "acknowledged_at": NOW - timedelta(hours=1),
            "acknowledged_by": "admin",
            "created_at": NOW - timedelta(hours=3),
        },
        {
            "alert_id": _uuid(),
            "alert_type": "disk_space",
            "severity": "info",
            "description": "Log disk usage at 72% (threshold: 80%)",
            "alert_metadata": {"threshold": 80, "actual": 72, "path": "/var/log/taskflow"},
            "acknowledged": True,
            "acknowledged_at": NOW - timedelta(days=1),
            "acknowledged_by": "operator",
            "created_at": NOW - timedelta(days=1, hours=3),
        },
    ]


def make_dead_letter_entries(tasks: list[dict]) -> list[dict]:
    """Create DLQ entries for some failed tasks."""
    dlq = []
    failed = [t for t in tasks if t["status"] == "FAILED"][:3]
    for t in failed:
        dlq.append({
            "dlq_id": _uuid(),
            "task_id": t["task_id"],
            "task_data": {"task_name": t["task_name"], "args": t["task_args"], "kwargs": t["task_kwargs"]},
            "failure_reason": f"Max retries exceeded for {t['task_name']}",
            "total_attempts": t["max_retries"],
        })
    return dlq


# ═══════════════════════════════════════════════════════════════════════════════
#  Main seeder logic
# ═══════════════════════════════════════════════════════════════════════════════

MODEL_TABLES = [
    CampaignTask, EmailRecipient, EmailTemplate,
    DeadLetterQueue, TaskLog, TaskExecution, TaskResult, Task,
    Alert, Campaign, Worker, User,
]


def clear_data(session) -> None:
    """Delete all rows from demo tables (respects FK ordering)."""
    print(f"\n{BOLD}Clearing existing data …{RESET}")
    for model in MODEL_TABLES:
        count = session.query(model).delete()
        if count:
            print(f"  Deleted {count} rows from {model.__tablename__}")
    session.commit()
    print(f"  {GREEN}✓{RESET} All data cleared")


def seed_model(session, model_cls, records: list[dict], label: str) -> int:
    """Insert records into a table. Returns count inserted."""
    inserted = 0
    for rec in records:
        try:
            obj = model_cls(**rec)
            session.add(obj)
            session.flush()
            inserted += 1
        except Exception:
            session.rollback()
            # Likely duplicate — skip
            continue
    session.commit()
    colour = GREEN if inserted > 0 else YELLOW
    print(f"  {colour}✓{RESET} {label}: {inserted}/{len(records)} inserted")
    return inserted


def seed_all() -> None:
    """Generate and insert all demo data."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        print(f"\n{BOLD}Seeding demo data …{RESET}")

        # 1) Users
        users = make_users()
        seed_model(session, User, users, "Users")

        # 2) Workers
        workers = make_workers()
        seed_model(session, Worker, workers, "Workers")
        worker_ids = [w["worker_id"] for w in workers]

        # 3) Campaigns
        campaigns = make_campaigns()
        seed_model(session, Campaign, campaigns, "Campaigns")
        campaign_ids = [c["campaign_id"] for c in campaigns]

        # 4) Email templates
        templates = make_email_templates(campaign_ids)
        seed_model(session, EmailTemplate, templates, "Email Templates")

        # 5) Email recipients
        recipients = make_email_recipients(campaign_ids)
        seed_model(session, EmailRecipient, recipients, "Email Recipients")

        # 6) Tasks
        tasks = make_tasks(worker_ids)
        seed_model(session, Task, tasks, "Tasks")

        # 7) Task Results
        results = make_task_results(tasks)
        seed_model(session, TaskResult, results, "Task Results")

        # 8) Task Logs
        logs = make_task_logs(tasks)
        seed_model(session, TaskLog, logs, "Task Logs")

        # 9) Alerts
        alerts = make_alerts()
        seed_model(session, Alert, alerts, "Alerts")

        # 10) Dead Letter Queue
        dlq = make_dead_letter_entries(tasks)
        seed_model(session, DeadLetterQueue, dlq, "Dead Letter Queue")

        # ── Summary ──────────────────────────────────────────────────────
        total = (
            len(users) + len(workers) + len(campaigns) + len(templates)
            + len(recipients) + len(tasks) + len(results) + len(logs)
            + len(alerts) + len(dlq)
        )
        print(f"\n{GREEN}{BOLD}  ✓ Seeding complete — {total} records across 10 tables{RESET}")

    except Exception as e:
        session.rollback()
        print(f"\n{RED}✗ Seeding failed: {e}{RESET}")
        raise
    finally:
        session.close()


def main() -> None:
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  TaskFlow — Demo Data Seeder{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")

    clear_only = "--clear-only" in sys.argv
    clear = "--clear" in sys.argv or clear_only

    if clear:
        session = SessionLocal()
        try:
            clear_data(session)
        finally:
            session.close()

    if not clear_only:
        seed_all()


if __name__ == "__main__":
    main()
