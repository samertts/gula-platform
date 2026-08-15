"""Persist verification attempt and lock metadata.

Revision ID: 20260815_0024
Revises: 20260815_0023
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260815_0024"
down_revision = "20260815_0023"
branch_labels = None
depends_on = None

_COLUMNS = (
    ("verification_attempts", sa.Integer(), 0, False),
    ("verification_locked_at", sa.DateTime(timezone=True), None, True),
    ("verification_failure_reason_code", sa.String(length=100), None, True),
)


def _has_table(table: str) -> bool:
    return bool(sa.inspect(op.get_bind()).has_table(table))


def _columns(table: str) -> set[str]:
    if not _has_table(table):
        return set()
    return {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    table = "niam_account_creation_requests"
    if not _has_table(table):
        return
    existing = _columns(table)
    for name, column_type, default, nullable in _COLUMNS:
        if name in existing:
            continue
        server_default = sa.text(str(default)) if default is not None else None
        op.add_column(
            table,
            sa.Column(
                name,
                column_type,
                nullable=nullable,
                server_default=server_default,
            ),
        )


def downgrade() -> None:
    table = "niam_account_creation_requests"
    if not _has_table(table):
        return
    existing = _columns(table)
    for name, _, _, _ in reversed(_COLUMNS):
        if name in existing:
            op.drop_column(table, name)
