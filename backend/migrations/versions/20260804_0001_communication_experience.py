"""PROGRAM-COMM-003: User Communication Experience tables

Revision ID: 20260804_0001
Revises: 20260802_0002
Create Date: 2026-08-04

Adds the unified user inbox (``comm_notifications``), append-only
notification history (``comm_notification_events``) and per-user
communication preferences (``comm_user_preferences``). All tables are
additive — no existing table or column is touched; deletion is soft.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260804_0001"
down_revision = "20260802_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comm_notifications",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("category", sa.String(40), nullable=False, server_default="system"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("title", sa.String(255), nullable=False, server_default=""),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("data", sa.Text(), nullable=True),
        sa.Column("state", sa.String(20), nullable=False, server_default="unread"),
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("group_key", sa.String(100), nullable=True),
        sa.Column("delivery_id", sa.String(64), nullable=True),
        sa.Column("template_id", sa.String(100), nullable=True),
        sa.Column("locale", sa.String(10), nullable=False, server_default="ar"),
        sa.Column("external_status", sa.String(40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_comm_notifications_user_id", "comm_notifications", ["user_id"])
    op.create_index(
        "ix_comm_notifications_user_state", "comm_notifications", ["user_id", "state"]
    )
    op.create_index(
        "ix_comm_notifications_user_category",
        "comm_notifications",
        ["user_id", "category"],
    )
    op.create_index(
        "ix_comm_notifications_user_priority",
        "comm_notifications",
        ["user_id", "priority"],
    )
    op.create_index(
        "ix_comm_notifications_user_group", "comm_notifications", ["user_id", "group_key"]
    )
    op.create_index("ix_comm_notifications_state", "comm_notifications", ["state"])
    op.create_index("ix_comm_notifications_created_at", "comm_notifications", ["created_at"])
    op.create_index("ix_comm_notifications_delivery_id", "comm_notifications", ["delivery_id"])

    op.create_table(
        "comm_notification_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("notification_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("channel", sa.String(40), nullable=True),
        sa.Column("provider", sa.String(40), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_comm_notification_events_notification_id",
        "comm_notification_events",
        ["notification_id"],
    )
    op.create_index(
        "ix_comm_notification_events_created_at",
        "comm_notification_events",
        ["created_at"],
    )
    op.create_index(
        "ix_comm_notification_events_nid_created",
        "comm_notification_events",
        ["notification_id", "created_at"],
    )
    op.create_foreign_key(
        "fk_comm_notification_events_notification_id",
        "comm_notification_events",
        "comm_notifications",
        ["notification_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_table(
        "comm_user_preferences",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("preferences", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("comm_user_preferences")
    op.drop_table("comm_notification_events")
    op.drop_table("comm_notifications")
