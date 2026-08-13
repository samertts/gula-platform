"""Create the durable cross-repository integration inbox.

Revision ID: 20260813_0005
Revises: 20260813_0004
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260813_0005"
down_revision = "20260813_0004"
branch_labels = None
depends_on = None

_TABLE = "integration_inbox_events"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE in inspector.get_table_names():
        return

    op.create_table(
        _TABLE,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(length=120), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("source_service", sa.String(length=80), nullable=False),
        sa.Column("tenant_id", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.String(length=160), nullable=False),
        sa.Column("correlation_id", sa.String(length=160), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("actor_id", sa.String(length=160), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending_review"),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("event_id", name="uq_integration_inbox_event_id"),
        sa.UniqueConstraint("idempotency_key", name="uq_integration_inbox_idempotency_key"),
    )
    for column in ("event_id", "event_type", "source_service", "tenant_id", "entity_id", "correlation_id", "idempotency_key", "status"):
        op.create_index(f"ix_integration_inbox_events_{column}", _TABLE, [column])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE not in inspector.get_table_names():
        return
    for column in ("status", "idempotency_key", "correlation_id", "entity_id", "tenant_id", "source_service", "event_type", "event_id"):
        op.drop_index(f"ix_integration_inbox_events_{column}", table_name=_TABLE)
    op.drop_table(_TABLE)
