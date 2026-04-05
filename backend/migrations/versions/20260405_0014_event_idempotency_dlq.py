"""Event idempotency + Dead Letter Queue tables.

New tables:
  processed_events — prevents duplicate event processing (idempotency guard)
  dlq_events       — dead letter queue for repeatedly-failing events

These two tables harden the Transactional Outbox pattern already in place.
The processed_events table provides at-exactly-once semantics for consumers
by recording every event_id that has been successfully processed.

The dlq_events table captures events that exceed MAX_DLQ_ATTEMPTS (5).
Operations staff can replay or discard DLQ events from the admin panel.

All DDL is idempotent — safe to run on existing databases.

Revision ID : 20260405_0014
Revises     : 20260402_0013
Create Date : 2026-04-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision      = "20260405_0014"
down_revision = "20260402_0013"
branch_labels = None
depends_on    = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _index_exists(index_name: str, table_name: str) -> bool:
    insp = inspect(op.get_bind())
    return any(
        idx["name"] == index_name
        for idx in insp.get_indexes(table_name)
    )


def upgrade() -> None:
    # ── processed_events ──────────────────────────────────────────────────────
    if not _table_exists("processed_events"):
        op.create_table(
            "processed_events",
            sa.Column("id",           sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("event_id",     sa.String(100),  nullable=False),
            sa.Column("consumer",     sa.String(100),  nullable=False, server_default="default"),
            sa.Column("event_type",   sa.String(100),  nullable=True),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("notes",        sa.Text(),        nullable=True),
            sa.UniqueConstraint("event_id", "consumer",
                                name="uq_processed_event_id_consumer"),
        )
        op.create_index("ix_processed_events_event_id",    "processed_events", ["event_id"])
        op.create_index("ix_processed_events_processed_at","processed_events", ["processed_at"])

    # ── dlq_events ────────────────────────────────────────────────────────────
    if not _table_exists("dlq_events"):
        op.create_table(
            "dlq_events",
            sa.Column("id",          sa.Integer(),   primary_key=True, autoincrement=True),
            sa.Column("original_id", sa.Integer(),   nullable=True),
            sa.Column("event_type",  sa.String(100), nullable=False),
            sa.Column("payload",     sa.Text(),       nullable=False),
            sa.Column("attempts",    sa.Integer(),   nullable=False, server_default="0"),
            sa.Column("last_error",  sa.Text(),       nullable=True),
            sa.Column("consumer",    sa.String(100), nullable=True),
            sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolved_by", sa.String(100), nullable=True),
            sa.Column("resolution",  sa.Text(),       nullable=True),
        )
        op.create_index("ix_dlq_events_original_id", "dlq_events", ["original_id"])
        op.create_index("ix_dlq_events_event_type",  "dlq_events", ["event_type"])
        op.create_index("ix_dlq_events_created_at",  "dlq_events", ["created_at"])


def downgrade() -> None:
    if _table_exists("dlq_events"):
        op.drop_table("dlq_events")
    if _table_exists("processed_events"):
        op.drop_table("processed_events")
