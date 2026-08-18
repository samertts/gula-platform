"""Bind machine identities to a laboratory for cross-facility interop.

Legacy service accounts remain nullable and continue to work for existing
administrative APIs. PIXm/MHD endpoints reject unbound accounts explicitly.
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import context, op

revision: str = "20260815_0001"
down_revision: Union[str, None] = "20260814_0010"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    if context.is_offline_mode():
        return False
    bind = op.get_bind()
    if not sa.inspect(bind).has_table(table):
        return False
    return column in {item["name"] for item in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    if context.is_offline_mode():
        op.add_column("service_accounts", sa.Column("lab_id", sa.Integer(), nullable=True))
        op.create_index("ix_service_accounts_lab_id", "service_accounts", ["lab_id"])
        return
    if not _has_column("service_accounts", "lab_id"):
        column = sa.Column(
            "lab_id",
            sa.Integer(),
            sa.ForeignKey("labs.id", name="fk_service_accounts_lab_id", ondelete="SET NULL"),
            nullable=True,
        )
        if op.get_bind().dialect.name == "sqlite":
            with op.batch_alter_table("service_accounts", recreate="always") as batch_op:
                batch_op.add_column(column)
        else:
            op.add_column("service_accounts", column)
    bind = op.get_bind()
    indexes = {item["name"] for item in sa.inspect(bind).get_indexes("service_accounts")}
    if "ix_service_accounts_lab_id" not in indexes:
        op.create_index("ix_service_accounts_lab_id", "service_accounts", ["lab_id"])


def downgrade() -> None:
    if context.is_offline_mode():
        op.drop_index("ix_service_accounts_lab_id", table_name="service_accounts")
        op.drop_column("service_accounts", "lab_id")
        return
    bind = op.get_bind()
    indexes = {item["name"] for item in sa.inspect(bind).get_indexes("service_accounts")}
    if "ix_service_accounts_lab_id" in indexes:
        op.drop_index("ix_service_accounts_lab_id", table_name="service_accounts")
    if _has_column("service_accounts", "lab_id"):
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("service_accounts", recreate="always") as batch_op:
                batch_op.drop_constraint("fk_service_accounts_lab_id", type_="foreignkey")
                batch_op.drop_column("lab_id")
        else:
            op.drop_column("service_accounts", "lab_id")
