"""Add email templates and campaign task mapping

Revision ID: 003
Revises: 002
Create Date: 2026-01-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration."""
    op.create_table(
        "email_templates",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("email_template_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("variables", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("campaign_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.campaign_id"], name="fk_email_template_campaign"),
    )
    op.create_index("idx_email_templates_campaign", "email_templates", ["campaign_id"])
    op.create_index("idx_email_templates_name", "email_templates", ["name"])

    op.create_table(
        "campaign_tasks",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("campaign_task_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.campaign_id"], name="fk_campaign_task_campaign"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"], name="fk_campaign_task_task"),
    )
    op.create_index("idx_campaign_task_campaign", "campaign_tasks", ["campaign_id"])
    op.create_index("idx_campaign_task_task", "campaign_tasks", ["task_id"])


def downgrade() -> None:
    """Revert migration."""
    op.drop_index("idx_campaign_task_task", table_name="campaign_tasks")
    op.drop_index("idx_campaign_task_campaign", table_name="campaign_tasks")
    op.drop_table("campaign_tasks")

    op.drop_index("idx_email_templates_name", table_name="email_templates")
    op.drop_index("idx_email_templates_campaign", table_name="email_templates")
    op.drop_table("email_templates")
