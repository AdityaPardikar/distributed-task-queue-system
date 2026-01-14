"""Add status enum validation and indexes

Revision ID: 002
Revises: 001
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration."""
    # Add check constraint for valid status values
    op.create_check_constraint(
        "check_task_status_valid",
        "tasks",
        "status IN ('PENDING', 'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'RETRYING', 'TIMEOUT')"
    )
    
    # Add check constraint for worker status
    op.create_check_constraint(
        "check_worker_status_valid",
        "workers",
        "status IN ('ACTIVE', 'INACTIVE', 'OFFLINE', 'MAINTENANCE')"
    )
    
    # Add check constraint for campaign status
    op.create_check_constraint(
        "check_campaign_status_valid",
        "campaigns",
        "status IN ('DRAFT', 'SCHEDULED', 'RUNNING', 'PAUSED', 'COMPLETED', 'CANCELLED')"
    )
    
    # Add index for task status filtering
    op.create_index(
        "idx_tasks_status",
        "tasks",
        ["status"],
    )
    
    # Add composite index for common queries
    op.create_index(
        "idx_tasks_status_created",
        "tasks",
        ["status", "created_at"],
    )
    
    # Add index for timestamp queries
    op.create_index(
        "idx_tasks_started_at",
        "tasks",
        ["started_at"],
    )
    
    op.create_index(
        "idx_tasks_completed_at",
        "tasks",
        ["completed_at"],
    )


def downgrade() -> None:
    """Revert migration."""
    op.drop_index("idx_tasks_completed_at", table_name="tasks")
    op.drop_index("idx_tasks_started_at", table_name="tasks")
    op.drop_index("idx_tasks_status_created", table_name="tasks")
    op.drop_index("idx_tasks_status", table_name="tasks")
    
    op.drop_constraint("check_campaign_status_valid", "campaigns", type_="check")
    op.drop_constraint("check_worker_status_valid", "workers", type_="check")
    op.drop_constraint("check_task_status_valid", "tasks", type_="check")
