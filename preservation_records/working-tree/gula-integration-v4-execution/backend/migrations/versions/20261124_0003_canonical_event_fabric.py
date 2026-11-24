"""Add canonical C09 fields to the durable outbox.

Revision ID: 20261124_0003
Revises: 20261124_0002

Additive only. Existing legacy rows are backfilled with stable synthetic
identifiers; no event payload is altered and no row is deleted.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261124_0003"
down_revision: str | None = "20261124_0002"


def upgrade() -> None:
    op.add_column("outbox_events", sa.Column("event_id", sa.String(length=120), nullable=True))
    op.add_column(
        "outbox_events",
        sa.Column(
            "schema_version", sa.Integer(), nullable=False, server_default=sa.text("1")
        ),
    )
    op.add_column(
        "outbox_events",
        sa.Column(
            "source_service",
            sa.String(length=80),
            nullable=False,
            server_default=sa.text("'gula-outbox'"),
        ),
    )
    op.add_column(
        "outbox_events",
        sa.Column(
            "tenant_id",
            sa.String(length=120),
            nullable=False,
            server_default=sa.text("'system'"),
        ),
    )
    op.add_column(
        "outbox_events",
        sa.Column(
            "actor_id",
            sa.String(length=160),
            nullable=False,
            server_default=sa.text("'system'"),
        ),
    )
    op.add_column(
        "outbox_events",
        sa.Column(
            "entity_id",
            sa.String(length=160),
            nullable=False,
            server_default=sa.text("'unknown'"),
        ),
    )
    op.add_column(
        "outbox_events",
        sa.Column(
            "correlation_id",
            sa.String(length=160),
            nullable=False,
            server_default=sa.text("'legacy-outbox'"),
        ),
    )
    op.add_column(
        "outbox_events",
        sa.Column(
            "idempotency_key",
            sa.String(length=200),
            nullable=False,
            server_default=sa.text("'legacy-outbox'"),
        ),
    )
    op.add_column("outbox_events", sa.Column("sequence", sa.Integer(), nullable=True))

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("UPDATE outbox_events SET event_id = 'legacy-' || id WHERE event_id IS NULL")
    else:
        rows = bind.execute(sa.text("SELECT id FROM outbox_events WHERE event_id IS NULL"))
        for row in rows:
            bind.execute(
                sa.text("UPDATE outbox_events SET event_id = :event_id WHERE id = :id"),
                {"event_id": f"legacy-{row[0]}", "id": row[0]},
            )

    op.alter_column("outbox_events", "event_id", nullable=False)
    op.create_unique_constraint("uq_outbox_events_event_id", "outbox_events", ["event_id"])
    op.create_index("ix_outbox_events_tenant_id", "outbox_events", ["tenant_id"], unique=False)
    op.create_index(
        "ix_outbox_events_correlation_id", "outbox_events", ["correlation_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_events_correlation_id", table_name="outbox_events")
    op.drop_index("ix_outbox_events_tenant_id", table_name="outbox_events")
    op.drop_constraint("uq_outbox_events_event_id", "outbox_events", type_="unique")
    for column in (
        "sequence",
        "idempotency_key",
        "correlation_id",
        "entity_id",
        "actor_id",
        "tenant_id",
        "source_service",
        "schema_version",
        "event_id",
    ):
        op.drop_column("outbox_events", column)
