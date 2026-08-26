"""Bind machine identities to a laboratory for cross-facility interop.

Legacy service accounts remain nullable and continue to work for existing
administrative APIs. PIXm/MHD endpoints reject unbound accounts explicitly.
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0001"
down_revision: str | None = "20260814_0010"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table(table):
        return False
    return column in {item["name"] for item in sa.inspect(bind).get_columns(table)}


def _has_lab_foreign_key() -> bool:
    bind = op.get_bind()
    return any(
        foreign_key.get("referred_table") == "labs"
        and foreign_key.get("constrained_columns") == ["lab_id"]
        for foreign_key in sa.inspect(bind).get_foreign_keys("service_accounts")
    )


def upgrade() -> None:
    bind = op.get_bind()
    has_column = _has_column("service_accounts", "lab_id")
    has_foreign_key = _has_lab_foreign_key()
    if bind.dialect.name == "sqlite":
        if not has_column or not has_foreign_key:
            with op.batch_alter_table("service_accounts", recreate="always") as batch_op:
                if not has_column:
                    batch_op.add_column(sa.Column("lab_id", sa.Integer(), nullable=True))
                if not has_foreign_key:
                    batch_op.create_foreign_key(
                        "fk_service_accounts_lab_id",
                        "labs",
                        ["lab_id"],
                        ["id"],
                        ondelete="SET NULL",
                    )
    elif not has_column:
        op.add_column(
            "service_accounts",
            sa.Column(
                "lab_id",
                sa.Integer(),
                sa.ForeignKey("labs.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
    elif not has_foreign_key:
        op.create_foreign_key(
            "fk_service_accounts_lab_id",
            "service_accounts",
            "labs",
            ["lab_id"],
            ["id"],
            ondelete="SET NULL",
        )
    indexes = {item["name"] for item in sa.inspect(bind).get_indexes("service_accounts")}
    if "ix_service_accounts_lab_id" not in indexes:
        op.create_index("ix_service_accounts_lab_id", "service_accounts", ["lab_id"])


def downgrade() -> None:
    bind = op.get_bind()
    indexes = {item["name"] for item in sa.inspect(bind).get_indexes("service_accounts")}
    if "ix_service_accounts_lab_id" in indexes:
        op.drop_index("ix_service_accounts_lab_id", table_name="service_accounts")
    if _has_column("service_accounts", "lab_id"):
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("service_accounts", recreate="always") as batch_op:
                batch_op.drop_column("lab_id")
        else:
            op.drop_column("service_accounts", "lab_id")
