"""Add email recipients table for campaign management

Revision ID: 004
Revises: 003
Create Date: 2026-01-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration - create email_recipients table."""
    op.create_table(
        "email_recipients",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("recipient_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("personalization", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("task_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("bounce_reason", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.campaign_id"], name="fk_email_recipient_campaign"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"], name="fk_email_recipient_task"),
    )
    op.create_index("idx_email_campaign_status", "email_recipients", ["campaign_id", "status"])


def downgrade() -> None:
    """Revert migration - drop email_recipients table."""
    op.drop_index("idx_email_campaign_status", table_name="email_recipients")
    op.drop_table("email_recipients")
