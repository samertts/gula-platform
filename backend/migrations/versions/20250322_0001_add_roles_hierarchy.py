"""Add role hierarchy columns to lab_users.

Adds:
  - national_id_hash  VARCHAR(255) UNIQUE — HMAC-SHA256 of national ID
  - province_id       INTEGER             — province scope for province_admin
  - created_by        INTEGER FK          — who created this account

Revision ID: 20250322_0001
Revises    : (initial)
Create Date: 2025-03-22
"""

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20250322_0001"
down_revision = "20250322_0000"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    """Return True if column already exists (idempotent migrations)."""
    if context.is_offline_mode():
        return False
    bind = op.get_bind()
    insp = inspect(bind)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols


def upgrade() -> None:
    if not _has_column("lab_users", "national_id_hash"):
        op.add_column(
            "lab_users",
            sa.Column("national_id_hash", sa.String(255), nullable=True),
        )
        op.create_index(
            "ix_lab_users_national_id_hash",
            "lab_users",
            ["national_id_hash"],
            unique=True,
        )

    if not _has_column("lab_users", "province_id"):
        op.add_column(
            "lab_users",
            sa.Column("province_id", sa.Integer(), nullable=True),
        )
        op.create_index(
            "ix_lab_users_province_id",
            "lab_users",
            ["province_id"],
            unique=False,
        )

    if not _has_column("lab_users", "created_by"):
        op.add_column(
            "lab_users",
            sa.Column(
                "created_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )


def downgrade() -> None:
    if context.is_offline_mode():
        op.drop_column("lab_users", "created_by")
        op.drop_index("ix_lab_users_province_id", table_name="lab_users")
        op.drop_column("lab_users", "province_id")
        op.drop_index("ix_lab_users_national_id_hash", table_name="lab_users")
        op.drop_column("lab_users", "national_id_hash")
        return
    bind = op.get_bind()
    insp = inspect(bind)
    indexes = {i["name"] for i in insp.get_indexes("lab_users")}
    cols = [c["name"] for c in insp.get_columns("lab_users")]

    if "created_by" in cols:
        op.drop_column("lab_users", "created_by")

    if "ix_lab_users_province_id" in indexes:
        op.drop_index("ix_lab_users_province_id", table_name="lab_users")
    if "province_id" in cols:
        op.drop_column("lab_users", "province_id")

    if "ix_lab_users_national_id_hash" in indexes:
        op.drop_index("ix_lab_users_national_id_hash", table_name="lab_users")
    if "national_id_hash" in cols:
        op.drop_column("lab_users", "national_id_hash")
