"""Add generic clinician ownership to the existing nursing workflow bridge.

Revision ID: 20260818_0004
Revises: 20260818_0003
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260818_0004"
down_revision: str | None = "20260818_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table: str, name: str) -> bool:
    return name in {column["name"] for column in inspect(op.get_bind()).get_columns(table)}


def _has_index(table: str, name: str) -> bool:
    return any(index["name"] == name for index in inspect(op.get_bind()).get_indexes(table))


def upgrade() -> None:
    for table in ("nursing_shifts", "nursing_patient_assignments"):
        if not _has_column(table, "clinician_user_id"):
            op.add_column(
                table,
                sa.Column(
                    "clinician_user_id",
                    sa.String(length=26),
                    sa.ForeignKey("lab_users.id", ondelete="SET NULL" if table == "nursing_shifts" else "CASCADE"),
                    nullable=True,
                ),
            )
        index_name = "ix_nursing_shifts_clinician_user" if table == "nursing_shifts" else "ix_nursing_assignments_clinician_user"
        if not _has_index(table, index_name):
            op.create_index(index_name, table, ["clinician_user_id"])


def downgrade() -> None:
    for table, index_name in (
        ("nursing_patient_assignments", "ix_nursing_assignments_clinician_user"),
        ("nursing_shifts", "ix_nursing_shifts_clinician_user"),
    ):
        if _has_index(table, index_name):
            op.drop_index(index_name, table_name=table)
        if _has_column(table, "clinician_user_id"):
            op.drop_column(table, "clinician_user_id")
