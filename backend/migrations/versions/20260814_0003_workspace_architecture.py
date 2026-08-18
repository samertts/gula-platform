"""Add canonical workspace architecture and server-authoritative contexts.

Revision ID: 20260814_0003
Revises: 20260814_0002
"""

from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa


revision = "20260814_0003"
down_revision = "20260814_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if context.is_offline_mode():
        tables = set()
    else:
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        tables = set(inspector.get_table_names())

    if "niam_workspaces" not in tables:
        op.create_table(
            "niam_workspaces",
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("workspace_key", sa.String(length=255), nullable=False),
            sa.Column("workspace_type", sa.String(length=30), nullable=False),
            sa.Column("name", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="provisioning"),
            sa.Column("owner_account_id", sa.String(length=26), nullable=True),
            sa.Column("organization_id", sa.String(length=26), nullable=True),
            sa.Column("facility_id", sa.String(length=26), nullable=True),
            sa.Column("department_id", sa.String(length=26), nullable=True),
            sa.Column("professional_type", sa.String(length=60), nullable=True),
            sa.Column("provisioned_by", sa.String(length=26), nullable=True),
            sa.Column("is_personal", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["owner_account_id"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["organization_id"], ["niam_organizations.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["provisioned_by"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("uuid", name="uq_niam_workspaces_uuid"),
            sa.UniqueConstraint("workspace_key", name="uq_niam_workspaces_key"),
        )
        for column in (
            "workspace_type",
            "status",
            "owner_account_id",
            "organization_id",
            "facility_id",
            "department_id",
            "professional_type",
            "is_personal",
        ):
            op.create_index(f"ix_niam_workspaces_{column}", "niam_workspaces", [column])

    if "niam_workspace_contexts" not in tables:
        op.create_table(
            "niam_workspace_contexts",
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("session_id", sa.String(length=26), nullable=False),
            sa.Column("account_id", sa.String(length=26), nullable=False),
            sa.Column("identity_id", sa.String(length=26), nullable=False),
            sa.Column("workspace_id", sa.String(length=26), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["session_id"], ["niam_sessions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["account_id"], ["niam_accounts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["identity_id"], ["niam_identities.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("session_id", name="uq_niam_workspace_context_session"),
        )
        for column in ("account_id", "identity_id", "workspace_id", "is_active"):
            op.create_index(f"ix_niam_workspace_contexts_{column}", "niam_workspace_contexts", [column])


def downgrade() -> None:
    if context.is_offline_mode():
        op.drop_table("niam_workspace_contexts")
        op.drop_table("niam_workspaces")
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "niam_workspace_contexts" in inspector.get_table_names():
        unique_constraints = {
            item["name"]
            for item in inspector.get_unique_constraints("niam_workspace_contexts")
            if item.get("name")
        }
        for index in inspector.get_indexes("niam_workspace_contexts"):
            if index["name"] not in unique_constraints:
                op.drop_index(index["name"], table_name="niam_workspace_contexts")
        op.drop_table("niam_workspace_contexts")
    if "niam_workspaces" in inspector.get_table_names():
        unique_constraints = {
            item["name"]
            for item in inspector.get_unique_constraints("niam_workspaces")
            if item.get("name")
        }
        for index in inspector.get_indexes("niam_workspaces"):
            if index["name"] not in unique_constraints:
                op.drop_index(index["name"], table_name="niam_workspaces")
        op.drop_table("niam_workspaces")
