"""Persist refresh-token lineage for session replay detection.

Revision ID: 20260815_0025
Revises: 20260815_0024
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260815_0025"
down_revision = "20260815_0024"
branch_labels = None
depends_on = None

_COLUMNS = (
    ("refresh_family_id", sa.String(length=36), True),
    ("refresh_replaced_by_jti", sa.String(length=128), True),
)


def _has_table(table: str) -> bool:
    return bool(sa.inspect(op.get_bind()).has_table(table))


def _columns(table: str) -> set[str]:
    if not _has_table(table):
        return set()
    return {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    table = "niam_sessions"
    if not _has_table(table):
        return
    existing = _columns(table)
    for name, column_type, nullable in _COLUMNS:
        if name not in existing:
            op.add_column(table, sa.Column(name, column_type, nullable=nullable))
    refreshed = _columns(table)
    if "refresh_family_id" in refreshed:
        op.create_index(
            "ix_niam_sessions_refresh_family_id",
            table,
            ["refresh_family_id"],
            unique=False,
            if_not_exists=True,
        )
    if "refresh_replaced_by_jti" in refreshed:
        op.create_index(
            "ix_niam_sessions_refresh_replaced_by_jti",
            table,
            ["refresh_replaced_by_jti"],
            unique=False,
            if_not_exists=True,
        )


def downgrade() -> None:
    table = "niam_sessions"
    if not _has_table(table):
        return
    existing = _columns(table)
    for index_name in (
        "ix_niam_sessions_refresh_replaced_by_jti",
        "ix_niam_sessions_refresh_family_id",
    ):
        op.drop_index(index_name, table_name=table, if_exists=True)
    for name, _, _ in reversed(_COLUMNS):
        if name in existing:
            op.drop_column(table, name)
