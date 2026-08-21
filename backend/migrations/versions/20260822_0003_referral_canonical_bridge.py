"""Add nullable legacy-to-canonical referral bridge columns.

Revision ID: 20260822_0003
Revises: 20260822_0002
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Inspector

revision: str = "20260822_0003"
down_revision: str = "20260822_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BRIDGES = (
    ("national_referrals", "ix_national_referrals_canonical", "canonical_referral_id"),
    ("ins_referrals", "ix_ins_referrals_canonical", "canonical_referral_id"),
)


def _inspector() -> Inspector:
    return cast(Inspector, sa.inspect(op.get_bind()))


def _table_exists(table: str) -> bool:
    return table in set(_inspector().get_table_names())


def _column_exists(table: str, column: str) -> bool:
    return column in {item["name"] for item in _inspector().get_columns(table)}


def _index_exists(table: str, index_name: str) -> bool:
    return index_name in {item["name"] for item in _inspector().get_indexes(table)}


def upgrade() -> None:
    for table, index_name, column in _BRIDGES:
        if not _table_exists(table):
            continue
        if not _column_exists(table, column):
            op.add_column(table, sa.Column(column, sa.String(length=26), nullable=True))
        if not _index_exists(table, index_name):
            op.create_index(index_name, table, [column], unique=False)


def downgrade() -> None:
    # Additive-only policy: do not remove bridge data or columns in production.
    return None
