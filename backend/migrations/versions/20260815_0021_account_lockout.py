"""Add account-level brute-force lockout state.

Revision ID: 20260815_0021
Revises: 20260815_0020
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260815_0021"
down_revision = "20260815_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lab_users",
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "lab_users",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
    op.drop_column("lab_users", "locked_until")
    op.drop_column("lab_users", "failed_login_attempts")
