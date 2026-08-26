"""Add role hierarchy columns to lab_users.

Adds:
  - national_id_hash  VARCHAR(255) UNIQUE — HMAC-SHA256 of national ID
  - province_id       INTEGER             — province scope for province_admin
  - created_by        INTEGER FK          — who created this account

Revision ID: 20250322_0001
Revises    : (initial)
Create Date: 2025-03-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20250322_0001"
down_revision = "20250322_0000"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    """Return True if column already exists (idempotent migrations)."""
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

    bind = op.get_bind()
    if not _has_column("lab_users", "created_by"):
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("lab_users", recreate="always") as batch_op:
                batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
                batch_op.create_foreign_key(
                    "fk_lab_users_created_by",
                    "lab_users",
                    ["created_by"],
                    ["id"],
                    ondelete="SET NULL",
                )
        else:
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
    bind = op.get_bind()
    insp = inspect(bind)
    indexes = {i["name"] for i in insp.get_indexes("lab_users")}
    cols = {c["name"] for c in insp.get_columns("lab_users")}

    for index_name in ("ix_lab_users_province_id", "ix_lab_users_national_id_hash"):
        if index_name in indexes:
            op.drop_index(index_name, table_name="lab_users")

    if bind.dialect.name == "sqlite":
        if {"created_by", "province_id", "national_id_hash"}.intersection(cols):
            with op.batch_alter_table("lab_users", recreate="always") as batch_op:
                for foreign_key in insp.get_foreign_keys("lab_users"):
                    if "created_by" in (foreign_key.get("constrained_columns") or ()) and foreign_key.get("name"):
                        batch_op.drop_constraint(foreign_key["name"], type_="foreignkey")
                for column in ("created_by", "province_id", "national_id_hash"):
                    if column in cols:
                        batch_op.drop_column(column)
    else:
        for column in ("created_by", "province_id", "national_id_hash"):
            if column in cols:
                op.drop_column("lab_users", column)
