"""Add password-reset fields to platform users.

Revision ID: 20260815_0022
Revises: 20260815_0021
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260815_0022"
down_revision = "20260815_0021"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    if not conn.dialect.has_table(conn, table):
        return False
    return column in {item["name"] for item in sa.inspect(conn).get_columns(table)}


def upgrade() -> None:
    if not _has_column("users", "reset_token"):
        op.add_column(
            "users",
            sa.Column("reset_token", sa.String(length=255), nullable=True),
        )
        op.create_index("ix_users_reset_token", "users", ["reset_token"])
    if not _has_column("users", "reset_token_expires"):
        op.add_column(
            "users",
            sa.Column("reset_token_expires", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    if _has_column("users", "reset_token_expires"):
        op.drop_column("users", "reset_token_expires")
    if _has_column("users", "reset_token"):
        op.drop_index("ix_users_reset_token", table_name="users")
        op.drop_column("users", "reset_token")
