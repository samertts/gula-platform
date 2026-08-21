"""Add durable clinical review fields to lab_results.

Revision ID: 20260818_0005
Revises: 20260818_0004
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.engine import Inspector

revision: str = "20260818_0005"
down_revision: str | None = "20260818_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS: tuple[tuple[str, sa.types.TypeEngine], ...] = (
    ("review_status", sa.String(length=24)),
    ("reviewed_by", sa.String(length=26)),
    ("reviewed_at", sa.DateTime(timezone=True)),
    ("review_note", sa.String(length=1000)),
)


def _inspector() -> Inspector:
    return cast(Inspector, inspect(op.get_bind()))


def _has_column(table: str, name: str) -> bool:
    return name in {column["name"] for column in _inspector().get_columns(table)}


def _has_index(table: str, name: str) -> bool:
    return any(index["name"] == name for index in _inspector().get_indexes(table))


def upgrade() -> None:
    for name, column_type in _COLUMNS:
        if not _has_column("lab_results", name):
            kwargs: dict[str, object] = {"nullable": name == "review_status"}
            if name == "review_status":
                kwargs["nullable"] = False
                kwargs["server_default"] = "UNREVIEWED"
            op.add_column("lab_results", sa.Column(name, column_type, **kwargs))
    if not _has_index("lab_results", "ix_lab_results_review_status"):
        op.create_index("ix_lab_results_review_status", "lab_results", ["review_status"])
    if not _has_index("lab_results", "ix_lab_results_reviewed_by"):
        op.create_index("ix_lab_results_reviewed_by", "lab_results", ["reviewed_by"])


def downgrade() -> None:
    for name in ("ix_lab_results_reviewed_by", "ix_lab_results_review_status"):
        if _has_index("lab_results", name):
            op.drop_index(name, table_name="lab_results")
    for name, _column_type in reversed(_COLUMNS):
        if _has_column("lab_results", name):
            op.drop_column("lab_results", name)
