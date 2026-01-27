"""Initial schema with tasks, workers, campaigns, and monitoring

Revision ID: 001
Revises: None
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration."""
    # Create workers table FIRST (no FK dependencies)
    op.create_table(
        "workers",
        sa.Column("worker_id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("current_load", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_heartbeat", sa.DateTime(), nullable=True),
        sa.Column("worker_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_workers_heartbeat", "workers", ["last_heartbeat"])

    # Create campaigns table (no FK dependencies)
    op.create_table(
        "campaigns",
        sa.Column("campaign_id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("variables", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_campaigns_status", "campaigns", ["status"])
    op.create_index("idx_campaigns_scheduled_at", "campaigns", ["scheduled_at"])

    # Create tasks table (after workers)
    op.create_table(
        "tasks",
        sa.Column("task_id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("handler", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("result", sa.JSON(), nullable=True, server_default=sa.text("'{}'::json")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("parent_task_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("worker_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["parent_task_id"], ["tasks.task_id"], name="fk_task_parent"),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.worker_id"], name="fk_task_worker"),
    )
    op.create_index("idx_tasks_status", "tasks", ["status"])
    op.create_index("idx_tasks_priority", "tasks", ["priority"])
    op.create_index("idx_tasks_scheduled_at", "tasks", ["scheduled_at"])
    op.create_index("idx_tasks_created_at", "tasks", ["created_at"])

    # Create task_results table
    op.create_table(
        "task_results",
        sa.Column("result_id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("task_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("execution_time_ms", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"], name="fk_result_task"),
    )
    op.create_index("idx_task_results_task_id", "task_results", ["task_id"])

    # Create task_logs table
    op.create_table(
        "task_logs",
        sa.Column("log_id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("task_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False, server_default="INFO"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("log_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"], name="fk_log_task"),
    )
    op.create_index("idx_task_logs_task_id", "task_logs", ["task_id", "created_at"])

    # Create task_executions table
    op.create_table(
        "task_executions",
        sa.Column("execution_id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("task_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("worker_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"], name="fk_execution_task"),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.worker_id"], name="fk_execution_worker"),
    )
    op.create_index("idx_task_executions_task_id", "task_executions", ["task_id"])

    # Create campaigns table
    op.create_table(
        "campaigns",
        sa.Column("campaign_id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("variables", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_campaigns_status", "campaigns", ["status"])
    op.create_index("idx_campaigns_scheduled_at", "campaigns", ["scheduled_at"])

    # Create alerts table
    op.create_table(
        "alerts",
        sa.Column("alert_id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("alert_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("alert_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("acknowledged", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_alert_type", "alerts", ["alert_type"])


def downgrade() -> None:
    """Revert migration."""
    op.drop_index("idx_alert_type", table_name="alerts")
    op.drop_table("alerts")

    op.drop_index("idx_campaigns_scheduled_at", table_name="campaigns")
    op.drop_index("idx_campaigns_status", table_name="campaigns")
    op.drop_table("campaigns")

    op.drop_index("idx_task_executions_task_id", table_name="task_executions")
    op.drop_table("task_executions")

    op.drop_index("idx_task_logs_task_id", table_name="task_logs")
    op.drop_table("task_logs")

    op.drop_index("idx_task_results_task_id", table_name="task_results")
    op.drop_table("task_results")

    op.drop_index("idx_workers_heartbeat", table_name="workers")
    op.drop_table("workers")

    op.drop_index("idx_tasks_created_at", table_name="tasks")
    op.drop_index("idx_tasks_scheduled_at", table_name="tasks")
    op.drop_index("idx_tasks_priority", table_name="tasks")
    op.drop_index("idx_tasks_status", table_name="tasks")
    op.drop_table("tasks")
