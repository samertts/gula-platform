"""Add canonical membership, invitation and application relationships.

Revision ID: 20260814_0004
Revises: 20260814_0003
"""

from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa


revision = "20260814_0004"
down_revision = "20260814_0003"
branch_labels = None
depends_on = None


def _drop_table_indexes(table_name: str) -> None:
    if context.is_offline_mode():
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    unique_constraints = {
        item["name"]
        for item in inspector.get_unique_constraints(table_name)
        if item.get("name")
    }
    for index in inspector.get_indexes(table_name):
        if index["name"] not in unique_constraints:
            op.drop_index(index["name"], table_name=table_name)


def upgrade() -> None:
    if context.is_offline_mode():
        tables = set()
    else:
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        tables = set(inspector.get_table_names())

    if "niam_memberships" not in tables:
        op.create_table(
            "niam_memberships",
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("membership_key", sa.String(length=768), nullable=False),
            sa.Column("account_id", sa.String(length=26), nullable=False),
            sa.Column("identity_id", sa.String(length=26), nullable=True),
            sa.Column("organization_id", sa.String(length=26), nullable=False),
            sa.Column("facility_id", sa.String(length=26), nullable=True),
            sa.Column("department_id", sa.String(length=26), nullable=True),
            sa.Column("unit_id", sa.String(length=26), nullable=True),
            sa.Column("workspace_id", sa.String(length=26), nullable=True),
            sa.Column("relationship_type", sa.String(length=50), nullable=False),
            sa.Column("scope_type", sa.String(length=30), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
            sa.Column("source", sa.String(length=50), nullable=False),
            sa.Column("created_by", sa.String(length=26), nullable=True),
            sa.Column("activated_by", sa.String(length=26), nullable=True),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revocation_reason", sa.Text(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["account_id"], ["niam_accounts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["identity_id"], ["niam_identities.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["organization_id"], ["niam_organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["facility_id"], ["niam_admin_facilities.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["department_id"], ["niam_admin_departments.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["unit_id"], ["niam_admin_units.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["activated_by"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("uuid", name="uq_niam_memberships_uuid"),
            sa.UniqueConstraint("membership_key", name="uq_niam_memberships_key"),
        )
        for column in ("account_id", "organization_id", "facility_id", "department_id", "unit_id", "workspace_id", "relationship_type", "scope_type", "status", "expires_at", "is_active"):
            op.create_index(f"ix_niam_memberships_{column}", "niam_memberships", [column])

    if "niam_membership_invitations" not in tables:
        op.create_table(
            "niam_membership_invitations",
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("invitation_key", sa.String(length=768), nullable=False),
            sa.Column("token_hash", sa.String(length=128), nullable=False),
            sa.Column("recipient_account_id", sa.String(length=26), nullable=True),
            sa.Column("organization_id", sa.String(length=26), nullable=False),
            sa.Column("facility_id", sa.String(length=26), nullable=True),
            sa.Column("department_id", sa.String(length=26), nullable=True),
            sa.Column("unit_id", sa.String(length=26), nullable=True),
            sa.Column("workspace_id", sa.String(length=26), nullable=True),
            sa.Column("relationship_type", sa.String(length=50), nullable=False),
            sa.Column("scope_type", sa.String(length=30), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
            sa.Column("membership_id", sa.String(length=26), nullable=True),
            sa.Column("created_by", sa.String(length=26), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["recipient_account_id"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["organization_id"], ["niam_organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["facility_id"], ["niam_admin_facilities.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["department_id"], ["niam_admin_departments.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["unit_id"], ["niam_admin_units.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["membership_id"], ["niam_memberships.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("uuid", name="uq_niam_membership_invitations_uuid"),
            sa.UniqueConstraint("invitation_key", name="uq_niam_membership_invitations_key"),
            sa.UniqueConstraint("token_hash", name="uq_niam_membership_invitations_token_hash"),
        )
        for column in ("recipient_account_id", "organization_id", "status", "expires_at"):
            op.create_index(f"ix_niam_membership_invitations_{column}", "niam_membership_invitations", [column])

    if "niam_membership_applications" not in tables:
        op.create_table(
            "niam_membership_applications",
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("application_key", sa.String(length=768), nullable=False),
            sa.Column("account_id", sa.String(length=26), nullable=False),
            sa.Column("identity_id", sa.String(length=26), nullable=True),
            sa.Column("organization_id", sa.String(length=26), nullable=False),
            sa.Column("facility_id", sa.String(length=26), nullable=True),
            sa.Column("department_id", sa.String(length=26), nullable=True),
            sa.Column("unit_id", sa.String(length=26), nullable=True),
            sa.Column("workspace_id", sa.String(length=26), nullable=True),
            sa.Column("relationship_type", sa.String(length=50), nullable=False),
            sa.Column("scope_type", sa.String(length=30), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reviewed_by", sa.String(length=26), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rejection_reason", sa.Text(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["account_id"], ["niam_accounts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["identity_id"], ["niam_identities.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["organization_id"], ["niam_organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["facility_id"], ["niam_admin_facilities.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["department_id"], ["niam_admin_departments.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["unit_id"], ["niam_admin_units.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["reviewed_by"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("uuid", name="uq_niam_membership_applications_uuid"),
            sa.UniqueConstraint("application_key", name="uq_niam_membership_applications_key"),
        )
        for column in ("account_id", "organization_id", "status"):
            op.create_index(f"ix_niam_membership_applications_{column}", "niam_membership_applications", [column])


def downgrade() -> None:
    if context.is_offline_mode():
        for table_name in ("niam_membership_applications", "niam_membership_invitations", "niam_memberships"):
            op.drop_table(table_name)
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table_name in ("niam_membership_applications", "niam_membership_invitations", "niam_memberships"):
        if table_name in inspector.get_table_names():
            _drop_table_indexes(table_name)
            op.drop_table(table_name)
