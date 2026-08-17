"""Add operational patient-flow state and timestamps to encounters.

Revision ID: 20260817_0024
Revises: 20260817_0023
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

revision: str = "20260817_0024"
down_revision: str | None = "20260817_0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = {
    "flow_state": sa.String(length=30),
    "hospital_id": sa.Integer(),
    "idempotency_key": sa.String(length=64),
    "arrival_at": sa.DateTime(timezone=True),
    "triage_at": sa.DateTime(timezone=True),
    "admission_at": sa.DateTime(timezone=True),
    "discharge_at": sa.DateTime(timezone=True),
}


def _column_exists(column: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(item["name"] == column for item in inspector.get_columns("national_encounters"))


def _index_exists(index_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(item["name"] == index_name for item in inspector.get_indexes("national_encounters"))


def upgrade() -> None:
    for name, column_type in _COLUMNS.items():
        if not _column_exists(name):
            op.add_column(
                "national_encounters",
                sa.Column(
                    name,
                    column_type,
                    nullable=False if name == "flow_state" else True,
                    server_default="planned" if name == "flow_state" else None,
                ),
            )
    op.execute(text("UPDATE national_encounters SET flow_state = 'planned' WHERE flow_state IS NULL"))
    if not _index_exists("ix_national_encounters_flow_state"):
        op.create_index(
            "ix_national_encounters_flow_state",
            "national_encounters",
            ["flow_state"],
        )
    if not _index_exists("ix_national_encounters_hospital_flow"):
        op.create_index(
            "ix_national_encounters_hospital_flow",
            "national_encounters",
            ["hospital_id", "flow_state"],
        )
    if not _index_exists("ix_national_encounters_idempotency"):
        op.create_index(
            "ix_national_encounters_idempotency",
            "national_encounters",
            ["lab_id", "hospital_id", "idempotency_key"],
            unique=True,
        )


def downgrade() -> None:
    if _index_exists("ix_national_encounters_idempotency"):
        op.drop_index("ix_national_encounters_idempotency", table_name="national_encounters")
    if _index_exists("ix_national_encounters_hospital_flow"):
        op.drop_index("ix_national_encounters_hospital_flow", table_name="national_encounters")
    if _index_exists("ix_national_encounters_flow_state"):
        op.drop_index("ix_national_encounters_flow_state", table_name="national_encounters")
    for name in reversed(tuple(_COLUMNS)):
        if _column_exists(name):
            op.drop_column("national_encounters", name)
