"""Outbox reliability metadata for retries, leases, replay, and integrity.

Prepared locally; not executed by this change set.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import context, op

revision = "20260817_0030"
down_revision = "20260816_0029"
branch_labels = None
depends_on = None


def _columns() -> set[str]:
    if context.is_offline_mode():
        return {"status", "event_type", "created_at"}
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns("outbox_events")} if inspector.has_table("outbox_events") else set()


def upgrade() -> None:
    existing = _columns()
    if not existing:
        return
    if "next_attempt_at" not in existing:
        op.add_column("outbox_events", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True))
    if "lease_until" not in existing:
        op.add_column("outbox_events", sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True))
    if "payload_hash" not in existing:
        op.add_column("outbox_events", sa.Column("payload_hash", sa.String(64), nullable=True))
    if "dead_letter_reason" not in existing:
        op.add_column("outbox_events", sa.Column("dead_letter_reason", sa.Text(), nullable=True))
    if "replayed_by" not in existing:
        op.add_column("outbox_events", sa.Column("replayed_by", sa.String(160), nullable=True))
    if "updated_at" not in existing:
        op.add_column("outbox_events", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    indexes = set() if context.is_offline_mode() else {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("outbox_events")}
    if "ix_outbox_events_status_next_attempt_created" not in indexes:
        op.create_index("ix_outbox_events_status_next_attempt_created", "outbox_events", ["status", "next_attempt_at", "created_at"])
    if "ix_outbox_events_type_status" not in indexes:
        op.create_index("ix_outbox_events_type_status", "outbox_events", ["event_type", "status"])


def downgrade() -> None:
    # Reliability metadata is retained by policy; rollback must not delete delivery history.
    return
