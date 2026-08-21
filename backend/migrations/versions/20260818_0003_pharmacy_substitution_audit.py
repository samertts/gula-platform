"""Add auditable metadata for prescription-item substitution.

Revision ID: 20260818_0003
Revises: 20260818_0002
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.engine import Inspector

revision: str = "20260818_0003"
down_revision: str | None = "20260818_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS: tuple[tuple[str, sa.types.TypeEngine], ...] = (
    ("substituted_from_drug_id", sa.String(length=26)),
    ("substitution_reason", sa.String(length=500)),
    ("substituted_by", sa.String(length=26)),
    ("substituted_at", sa.DateTime(timezone=True)),
)


def _inspector() -> Inspector:
    return cast(Inspector, inspect(op.get_bind()))


def _has_column(table: str, name: str) -> bool:
    return name in {column["name"] for column in _inspector().get_columns(table)}


def _has_index(table: str, name: str) -> bool:
    return any(index["name"] == name for index in _inspector().get_indexes(table))


def upgrade() -> None:
    for name, column_type in _COLUMNS:
        if not _has_column("pharmacy_prescription_items", name):
            op.add_column("pharmacy_prescription_items", sa.Column(name, column_type, nullable=True))
    if not _has_index("pharmacy_prescription_items", "ix_pharmacy_rx_item_substituted_from"):
        op.create_index(
            "ix_pharmacy_rx_item_substituted_from",
            "pharmacy_prescription_items",
            ["substituted_from_drug_id"],
        )


def downgrade() -> None:
    if _has_index("pharmacy_prescription_items", "ix_pharmacy_rx_item_substituted_from"):
        op.drop_index("ix_pharmacy_rx_item_substituted_from", table_name="pharmacy_prescription_items")
    for name, _column_type in reversed(_COLUMNS):
        if _has_column("pharmacy_prescription_items", name):
            op.drop_column("pharmacy_prescription_items", name)
