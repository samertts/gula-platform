"""Wave A (PRG-05/PRG-09) - real persistence for generated capability CRUD.

Revision ID: 20261124_0001
Revises: 20261119_0003

Additive only. Creates one namespaced table used by the eight generated
capability CRUD routers that previously returned static empty responses.
No existing table, column, constraint or data is modified.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261124_0001"
down_revision: str | None = "20261119_0003"

_PAYLOAD_JSON = postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "capability_records",
        sa.Column("capability", sa.String(length=80), nullable=False),
        sa.Column("record_id", sa.String(length=120), nullable=False),
        sa.Column("payload", _PAYLOAD_JSON, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("capability", "record_id", name="pk_capability_records"),
    )
    op.create_index(
        "ix_capability_records_capability_created_at",
        "capability_records",
        ["capability", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_capability_records_capability_created_at",
        table_name="capability_records",
    )
    op.drop_table("capability_records")
