"""Add explicit lab ownership to capability CRUD records.

Revision ID: 20261124_0002
Revises: 20261124_0001

Additive only: two columns and one index. Legacy rows are backfilled from the
JSON payload when present, otherwise 0 (reserved orphan namespace).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261124_0002"
down_revision: str | None = "20261124_0001"


def upgrade() -> None:
    op.add_column(
        "capability_records",
        sa.Column("lab_id", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "capability_records",
        sa.Column(
            "owner_user_id", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
    )
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            UPDATE capability_records
            SET lab_id = COALESCE((payload ->> 'lab_id')::integer, 0),
                owner_user_id = COALESCE((payload ->> 'owner_user_id')::integer, 0)
            """
        )
    else:
        rows = bind.execute(
            sa.text("SELECT capability, record_id, payload FROM capability_records")
        ).mappings()
        import json

        for row in rows:
            try:
                payload = json.loads(row["payload"] or "{}")
            except (TypeError, ValueError):
                payload = {}
            bind.execute(
                sa.text(
                    "UPDATE capability_records "
                    "SET lab_id = :lab_id, owner_user_id = :owner_user_id "
                    "WHERE capability = :capability AND record_id = :record_id"
                ),
                {
                    "lab_id": int(payload.get("lab_id") or 0),
                    "owner_user_id": int(payload.get("owner_user_id") or 0),
                    "capability": row["capability"],
                    "record_id": row["record_id"],
                },
            )
    op.create_index(
        "ix_capability_records_lab_capability",
        "capability_records",
        ["lab_id", "capability", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_capability_records_lab_capability",
        table_name="capability_records",
    )
    op.drop_column("capability_records", "owner_user_id")
    op.drop_column("capability_records", "lab_id")
