"""Add explicit facility scope to outbox events.

Prepared locally; not executed by this change set.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import context, op

revision = "20260817_0032"
down_revision = "20260817_0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if context.is_offline_mode():
        op.add_column("outbox_events", sa.Column("lab_id", sa.Integer(), nullable=True))
        op.create_index("ix_outbox_events_lab_id", "outbox_events", ["lab_id"])
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("outbox_events"):
        return
    columns = {item["name"] for item in inspector.get_columns("outbox_events")}
    if "lab_id" not in columns:
        op.add_column("outbox_events", sa.Column("lab_id", sa.Integer(), nullable=True))
    indexes = {item["name"] for item in inspector.get_indexes("outbox_events")}
    if "ix_outbox_events_lab_id" not in indexes:
        op.create_index("ix_outbox_events_lab_id", "outbox_events", ["lab_id"])


def downgrade() -> None:
    if context.is_offline_mode():
        op.drop_index("ix_outbox_events_lab_id", table_name="outbox_events")
        op.drop_column("outbox_events", "lab_id")
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("outbox_events"):
        return
    indexes = {item["name"] for item in inspector.get_indexes("outbox_events")}
    if "ix_outbox_events_lab_id" in indexes:
        op.drop_index("ix_outbox_events_lab_id", table_name="outbox_events")
    columns = {item["name"] for item in inspector.get_columns("outbox_events")}
    if "lab_id" in columns:
        op.drop_column("outbox_events", "lab_id")
