"""Add organization units, representatives and ownership records.

Revision ID: 20260814_0002
Revises: 20260814_0001
"""

from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa


revision = "20260814_0002"
down_revision = "20260814_0001"
branch_labels = None
depends_on = None


def _create_if_missing(name: str, columns: list[sa.Column], constraints: list[sa.Constraint]) -> None:
    if context.is_offline_mode():
        op.create_table(name, *columns, *constraints)
        return
    bind = op.get_bind()
    if name in sa.inspect(bind).get_table_names():
        return
    op.create_table(name, *columns, *constraints)


def upgrade() -> None:
    _create_if_missing(
        "niam_admin_units",
        [
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("unit_id", sa.String(length=100), nullable=False),
            sa.Column("department_id", sa.String(length=26), nullable=False),
            sa.Column("name_en", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=False),
            sa.Column("unit_type", sa.String(length=50), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        ],
        [
            sa.ForeignKeyConstraint(["department_id"], ["niam_admin_departments.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("uuid", name="uq_niam_admin_units_uuid"),
            sa.UniqueConstraint("unit_id", name="uq_niam_admin_units_unit_id"),
        ],
    )
    for column in ("department_id", "status", "unit_type"):
        op.create_index(f"ix_niam_admin_units_{column}", "niam_admin_units", [column])

    _create_if_missing(
        "niam_organization_representatives",
        [
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("organization_id", sa.String(length=26), nullable=False),
            sa.Column("account_id", sa.String(length=26), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("appointed_by", sa.String(length=26), nullable=True),
            sa.Column("appointment_reference", sa.String(length=255), nullable=True),
            sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        ],
        [
            sa.ForeignKeyConstraint(["organization_id"], ["niam_organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["account_id"], ["niam_accounts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["appointed_by"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("uuid", name="uq_niam_org_representatives_uuid"),
        ],
    )
    for column in ("organization_id", "account_id", "status"):
        op.create_index(f"ix_niam_org_representatives_{column}", "niam_organization_representatives", [column])

    _create_if_missing(
        "niam_organization_ownerships",
        [
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("organization_id", sa.String(length=26), nullable=False),
            sa.Column("account_id", sa.String(length=26), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("authority_reference", sa.String(length=255), nullable=True),
            sa.Column("confirmation_hash", sa.String(length=64), nullable=True),
            sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        ],
        [
            sa.ForeignKeyConstraint(["organization_id"], ["niam_organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["account_id"], ["niam_accounts.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("uuid", name="uq_niam_org_ownerships_uuid"),
        ],
    )
    for column in ("organization_id", "account_id", "status"):
        op.create_index(f"ix_niam_org_ownerships_{column}", "niam_organization_ownerships", [column])


def downgrade() -> None:
    tables = (
        "niam_organization_ownerships",
        "niam_organization_representatives",
        "niam_admin_units",
    )
    if context.is_offline_mode():
        for table in tables:
            op.drop_table(table)
        return
    bind = op.get_bind()
    for table in tables:
        if table not in sa.inspect(bind).get_table_names():
            continue
        for index in sa.inspect(bind).get_indexes(table):
            op.drop_index(index["name"], table_name=table)
        op.drop_table(table)
