"""Add tenant-scoped device gateway outbox.

Revision ID: 20260815_0017
Revises: 20260815_0016
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260815_0017"
down_revision = "20260815_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "device_outbox_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("gateway_ref", sa.String(length=160), nullable=True),
        sa.Column("event_type", sa.String(length=96), nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False, server_default="device_event"),
        sa.Column("aggregate_id", sa.Integer(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("correlation_id", sa.String(length=96), nullable=False),
        sa.Column("payload_safe", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("simulation_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lab_id", "idempotency_key", name="uq_device_outbox_lab_idempotency"),
    )
    op.create_index(
        "ix_device_outbox_lab_status_next",
        "device_outbox_messages",
        ["lab_id", "status", "next_attempt_at"],
    )
    op.create_index(
        "ix_device_outbox_gateway_status",
        "device_outbox_messages",
        ["gateway_ref", "status", "next_attempt_at"],
    )
    op.create_index(
        "ix_device_outbox_created",
        "device_outbox_messages",
        ["lab_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_device_outbox_created", table_name="device_outbox_messages")
    op.drop_index("ix_device_outbox_gateway_status", table_name="device_outbox_messages")
    op.drop_index("ix_device_outbox_lab_status_next", table_name="device_outbox_messages")
    op.drop_table("device_outbox_messages")
