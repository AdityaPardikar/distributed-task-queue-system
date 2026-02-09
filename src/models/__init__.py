"""Database models for TaskFlow"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import JSON, UUID, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from .task_status import TaskStatus, is_valid_transition, is_terminal_status, get_valid_next_statuses


class Base(DeclarativeBase):
    """Base class for all database models"""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Task(Base):
    """Task model for job queue"""

    __tablename__ = "tasks"

    task_id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uuid4)
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_args: Mapped[dict] = mapped_column(JSON, default=dict)
    task_kwargs: Mapped[dict] = mapped_column(JSON, default=dict)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=5)
    retry_strategy: Mapped[str] = mapped_column(String(50), default="exponential")
    backoff_base_seconds: Mapped[int] = mapped_column(Integer, default=2)
    max_backoff_seconds: Mapped[int] = mapped_column(Integer, default=3600)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300)
    depends_on: Mapped[list] = mapped_column(JSON, default=list)
    parent_task_id: Mapped[Optional[str]] = mapped_column(UUID, ForeignKey("tasks.task_id"))
    campaign_id: Mapped[Optional[str]] = mapped_column(UUID, ForeignKey("campaigns.campaign_id"))
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100))
    is_recurring: Mapped[bool] = mapped_column(Integer, default=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    worker_id: Mapped[Optional[str]] = mapped_column(UUID, ForeignKey("workers.worker_id"))
    created_by: Mapped[Optional[str]] = mapped_column(UUID)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("priority >= 1 AND priority <= 10", name="check_priority_range"),
        Index("idx_status_priority", "status", "priority"),
        Index("idx_scheduled_at", "scheduled_at"),
        Index("idx_campaign_id", "campaign_id"),
        Index("idx_created_at", "created_at"),
        Index("idx_worker_id", "worker_id"),
    )

    # Relationships
    campaign: Mapped[Optional["Campaign"]] = relationship("Campaign", back_populates="tasks")
    worker: Mapped[Optional["Worker"]] = relationship("Worker", back_populates="tasks")
    result: Mapped[Optional["TaskResult"]] = relationship("TaskResult", back_populates="task", uselist=False)
    logs: Mapped[list["TaskLog"]] = relationship("TaskLog", back_populates="task")
    executions: Mapped[list["TaskExecution"]] = relationship("TaskExecution", back_populates="task")
    children: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="parent",
        foreign_keys=[parent_task_id]
    )
    parent: Mapped[Optional["Task"]] = relationship(
        "Task", 
        back_populates="children",
        remote_side=[task_id]
    )


class TaskResult(Base):
    """Task execution result"""

    __tablename__ = "task_results"

    result_id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uuid4)
    task_id: Mapped[str] = mapped_column(UUID, ForeignKey("tasks.task_id"), unique=True)
    result_data: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("idx_task_result_id", "task_id"),)

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="result")


class TaskLog(Base):
    """Task execution logs"""

    __tablename__ = "task_logs"

    log_id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uuid4)
    task_id: Mapped[str] = mapped_column(UUID, ForeignKey("tasks.task_id"))
    level: Mapped[str] = mapped_column(String(20), default="INFO")
    message: Mapped[str] = mapped_column(Text)
    log_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("idx_task_logs_task_id", "task_id", "created_at"),)

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="logs")


class TaskExecution(Base):
    """Task execution details"""

    __tablename__ = "task_executions"

    execution_id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uuid4)
    task_id: Mapped[str] = mapped_column(UUID, ForeignKey("tasks.task_id"))
    worker_id: Mapped[str] = mapped_column(UUID, ForeignKey("workers.worker_id"))
    attempt_number: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50))
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        Index("idx_task_execution_task_id", "task_id"),
        Index("idx_task_execution_worker_id", "worker_id"),
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="executions")
    worker: Mapped["Worker"] = relationship("Worker", back_populates="executions")


class Worker(Base):
    """Worker node information"""

    __tablename__ = "workers"

    worker_id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uuid4)
    hostname: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    capacity: Mapped[int] = mapped_column(Integer, default=5)
    current_load: Mapped[int] = mapped_column(Integer, default=0)
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime)
    worker_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("idx_workers_heartbeat", "last_heartbeat"),)

    # Relationships
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="worker")
    executions: Mapped[list["TaskExecution"]] = relationship("TaskExecution", back_populates="worker")


class Campaign(Base):
    """Email campaign"""

    __tablename__ = "campaigns"

    campaign_id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="DRAFT")
    template_subject: Mapped[str] = mapped_column(String(255))
    template_body: Mapped[str] = mapped_column(Text)
    template_variables: Mapped[dict] = mapped_column(JSON, default=dict)
    total_recipients: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_by: Mapped[Optional[str]] = mapped_column(UUID)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=100)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("idx_campaign_status", "status"),)

    # Relationships
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="campaign")
    recipients: Mapped[list["EmailRecipient"]] = relationship("EmailRecipient", back_populates="campaign")
    campaign_tasks: Mapped[list["CampaignTask"]] = relationship("CampaignTask", back_populates="campaign")
    email_templates: Mapped[list["EmailTemplate"]] = relationship("EmailTemplate", back_populates="campaign")


class EmailRecipient(Base):
    """Email recipient for campaigns"""

    __tablename__ = "email_recipients"

    recipient_id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uuid4)
    campaign_id: Mapped[str] = mapped_column(UUID, ForeignKey("campaigns.campaign_id"))
    email: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    personalization: Mapped[dict] = mapped_column(JSON, default=dict)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    task_id: Mapped[Optional[str]] = mapped_column(UUID, ForeignKey("tasks.task_id"))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    bounce_reason: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("idx_email_campaign_status", "campaign_id", "status"),)

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="recipients")


class EmailTemplate(Base):
    """Reusable email template for campaigns."""

    __tablename__ = "email_templates"

    email_template_id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    variables: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    campaign_id: Mapped[Optional[str]] = mapped_column(UUID, ForeignKey("campaigns.campaign_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_email_templates_campaign", "campaign_id"),
        Index("idx_email_templates_name", "name"),
    )

    campaign: Mapped[Optional["Campaign"]] = relationship("Campaign", back_populates="email_templates")


class CampaignTask(Base):
    """Links campaigns to tasks for tracking."""

    __tablename__ = "campaign_tasks"

    campaign_task_id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uuid4)
    campaign_id: Mapped[str] = mapped_column(UUID, ForeignKey("campaigns.campaign_id"))
    task_id: Mapped[str] = mapped_column(UUID, ForeignKey("tasks.task_id"))
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_campaign_task_campaign", "campaign_id"),
        Index("idx_campaign_task_task", "task_id"),
    )

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="campaign_tasks")
    task: Mapped["Task"] = relationship("Task")


class DeadLetterQueue(Base):
    """Dead letter queue for failed tasks"""

    __tablename__ = "dead_letter_queue"

    dlq_id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uuid4)
    task_id: Mapped[str] = mapped_column(UUID, ForeignKey("tasks.task_id"))
    task_data: Mapped[dict] = mapped_column(JSON)
    failure_reason: Mapped[str] = mapped_column(Text)
    total_attempts: Mapped[int] = mapped_column(Integer)
    requeued_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("idx_dlq_task_id", "task_id"),)


class Alert(Base):
    """System alerts for threshold violations."""

    __tablename__ = "alerts"

    alert_id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uuid4)
    alert_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    alert_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    acknowledged: Mapped[bool] = mapped_column(Integer, default=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_alert_type", "alert_type"),
        Index("idx_alert_severity", "severity"),
        Index("idx_alert_acknowledged", "acknowledged"),
        Index("idx_alert_created_at", "created_at"),
    )


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="viewer")  # admin, operator, viewer
    is_active: Mapped[bool] = mapped_column(Integer, default=True)
    is_superuser: Mapped[bool] = mapped_column(Integer, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_user_username", "username"),
        Index("idx_user_email", "email"),
        Index("idx_user_role", "role"),
        CheckConstraint("role IN ('admin', 'operator', 'viewer')", name="check_user_role"),
    )
