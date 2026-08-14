"""Add role, permission and scoped role assignment engine.

Revision ID: 20260814_0005
Revises: 20260814_0004
"""

from __future__ import annotations

from datetime import UTC, datetime

from alembic import op
import sqlalchemy as sa


revision = "20260814_0005"
down_revision = "20260814_0004"
branch_labels = None
depends_on = None


def _drop_table_indexes(table_name: str) -> None:
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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    now = datetime.now(UTC)

    if "niam_roles" not in tables:
        op.create_table(
            "niam_roles",
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("role_key", sa.String(length=120), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("name_ar", sa.String(length=200), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("scope_type", sa.String(length=30), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
            sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("uuid", name="uq_niam_roles_uuid"),
            sa.UniqueConstraint("role_key", name="uq_niam_roles_key"),
        )
        for column in ("role_key", "scope_type", "status"):
            op.create_index(f"ix_niam_roles_{column}", "niam_roles", [column])

    if "niam_permissions" not in tables:
        op.create_table(
            "niam_permissions",
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("permission_key", sa.String(length=160), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("name_ar", sa.String(length=200), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("resource", sa.String(length=120), nullable=False),
            sa.Column("action", sa.String(length=80), nullable=False),
            sa.Column("sensitivity", sa.String(length=30), nullable=False, server_default="medium"),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("uuid", name="uq_niam_permissions_uuid"),
            sa.UniqueConstraint("permission_key", name="uq_niam_permissions_key"),
        )
        for column in ("permission_key", "resource", "action", "status"):
            op.create_index(f"ix_niam_permissions_{column}", "niam_permissions", [column])

    if "niam_role_permissions" not in tables:
        op.create_table(
            "niam_role_permissions",
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("role_id", sa.String(length=26), nullable=False),
            sa.Column("permission_id", sa.String(length=26), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
            sa.Column("created_by", sa.String(length=26), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["role_id"], ["niam_roles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["permission_id"], ["niam_permissions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("role_id", "permission_id", name="uq_niam_role_permissions_relation"),
        )
        for column in ("role_id", "permission_id", "status"):
            op.create_index(f"ix_niam_role_permissions_{column}", "niam_role_permissions", [column])

    if "niam_role_assignments" not in tables:
        op.create_table(
            "niam_role_assignments",
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("assignment_key", sa.String(length=768), nullable=False),
            sa.Column("account_id", sa.String(length=26), nullable=False),
            sa.Column("membership_id", sa.String(length=26), nullable=False),
            sa.Column("role_id", sa.String(length=26), nullable=False),
            sa.Column("organization_id", sa.String(length=26), nullable=False),
            sa.Column("facility_id", sa.String(length=26), nullable=True),
            sa.Column("department_id", sa.String(length=26), nullable=True),
            sa.Column("unit_id", sa.String(length=26), nullable=True),
            sa.Column("workspace_id", sa.String(length=26), nullable=True),
            sa.Column("scope_type", sa.String(length=30), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
            sa.Column("assigned_by", sa.String(length=26), nullable=True),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revocation_reason", sa.Text(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["account_id"], ["niam_accounts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["membership_id"], ["niam_memberships.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["role_id"], ["niam_roles.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["organization_id"], ["niam_organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["facility_id"], ["niam_admin_facilities.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["department_id"], ["niam_admin_departments.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["unit_id"], ["niam_admin_units.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["assigned_by"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("uuid", name="uq_niam_role_assignments_uuid"),
            sa.UniqueConstraint("assignment_key", name="uq_niam_role_assignments_key"),
        )
        for column in ("account_id", "membership_id", "role_id", "organization_id", "scope_type", "status", "expires_at"):
            op.create_index(f"ix_niam_role_assignments_{column}", "niam_role_assignments", [column])

    # Minimal least-privilege catalog. No platform-wide or clinical write grants are seeded here.
    roles = sa.table(
        "niam_roles",
        sa.column("id", sa.String),
        sa.column("uuid", sa.String),
        sa.column("role_key", sa.String),
        sa.column("name", sa.String),
        sa.column("name_ar", sa.String),
        sa.column("description", sa.Text),
        sa.column("scope_type", sa.String),
        sa.column("status", sa.String),
        sa.column("is_system", sa.Boolean),
        sa.column("version", sa.Integer),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    permissions = sa.table(
        "niam_permissions",
        sa.column("id", sa.String),
        sa.column("uuid", sa.String),
        sa.column("permission_key", sa.String),
        sa.column("name", sa.String),
        sa.column("name_ar", sa.String),
        sa.column("description", sa.Text),
        sa.column("resource", sa.String),
        sa.column("action", sa.String),
        sa.column("sensitivity", sa.String),
        sa.column("status", sa.String),
        sa.column("version", sa.Integer),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    role_permissions = sa.table(
        "niam_role_permissions",
        sa.column("id", sa.String),
        sa.column("role_id", sa.String),
        sa.column("permission_id", sa.String),
        sa.column("status", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    role_rows = [
        {"id": "R7ORGVIEWER0000000000000001", "uuid": "r7-org-viewer-0000000000000001", "role_key": "organization_viewer", "name": "Organization Viewer", "name_ar": "قارئ المنظمة", "description": "Read-only organization membership context.", "scope_type": "organization", "status": "active", "is_system": True, "version": 1, "created_at": now, "updated_at": now},
        {"id": "R7ORGMANAGER0000000000000001", "uuid": "r7-org-manager-000000000000001", "role_key": "organization_manager", "name": "Organization Manager", "name_ar": "مدير المنظمة", "description": "Manage scoped memberships and roles within an organization.", "scope_type": "organization", "status": "active", "is_system": True, "version": 1, "created_at": now, "updated_at": now},
    ]
    permission_rows = [
        {"id": "P7MEMBERREAD0000000000000001", "uuid": "p7-membership-read-00000001", "permission_key": "membership.read", "name": "Read Membership", "name_ar": "قراءة العضوية", "description": "Read effective memberships in context.", "resource": "membership", "action": "read", "sensitivity": "medium", "status": "active", "version": 1, "created_at": now, "updated_at": now},
        {"id": "P7MEMBERINVITE000000000000001", "uuid": "p7-membership-invite-0000001", "permission_key": "membership.invite", "name": "Invite Membership", "name_ar": "دعوة عضو", "description": "Create scoped membership invitations.", "resource": "membership", "action": "invite", "sensitivity": "high", "status": "active", "version": 1, "created_at": now, "updated_at": now},
        {"id": "P7MEMBERREVOKE00000000000001", "uuid": "p7-membership-revoke-00000001", "permission_key": "membership.revoke", "name": "Revoke Membership", "name_ar": "إلغاء العضوية", "description": "Revoke scoped memberships.", "resource": "membership", "action": "revoke", "sensitivity": "high", "status": "active", "version": 1, "created_at": now, "updated_at": now},
        {"id": "P7ROLEASSIGN0000000000000001", "uuid": "p7-role-assign-00000000000001", "permission_key": "role.assign", "name": "Assign Role", "name_ar": "إسناد دور", "description": "Assign a catalog role within an authorized scope.", "resource": "role", "action": "assign", "sensitivity": "critical", "status": "active", "version": 1, "created_at": now, "updated_at": now},
        {"id": "P7WORKSPACEREAD0000000000001", "uuid": "p7-workspace-read-00000001", "permission_key": "workspace.read", "name": "Read Workspace", "name_ar": "قراءة مساحة العمل", "description": "Read server-reflected workspace context.", "resource": "workspace", "action": "read", "sensitivity": "medium", "status": "active", "version": 1, "created_at": now, "updated_at": now},
        {"id": "P7AUDITREAD0000000000000001", "uuid": "p7-audit-read-00000001", "permission_key": "audit.read", "name": "Read Audit", "name_ar": "قراءة التدقيق", "description": "Read authorized organization audit records.", "resource": "audit", "action": "read", "sensitivity": "critical", "status": "active", "version": 1, "created_at": now, "updated_at": now},
    ]
    op.bulk_insert(roles, role_rows)
    op.bulk_insert(permissions, permission_rows)
    op.bulk_insert(
        role_permissions,
        [
            {"id": "RP7VIEWERREAD00000000000001", "role_id": role_rows[0]["id"], "permission_id": permission_rows[0]["id"], "status": "active", "created_at": now, "updated_at": now},
            {"id": "RP7VIEWERWORKSPACE000000001", "role_id": role_rows[0]["id"], "permission_id": permission_rows[4]["id"], "status": "active", "created_at": now, "updated_at": now},
            {"id": "RP7MANAGERREAD00000000000001", "role_id": role_rows[1]["id"], "permission_id": permission_rows[0]["id"], "status": "active", "created_at": now, "updated_at": now},
            {"id": "RP7MANAGERINVITE000000000001", "role_id": role_rows[1]["id"], "permission_id": permission_rows[1]["id"], "status": "active", "created_at": now, "updated_at": now},
            {"id": "RP7MANAGERREVOKE00000000001", "role_id": role_rows[1]["id"], "permission_id": permission_rows[2]["id"], "status": "active", "created_at": now, "updated_at": now},
            {"id": "RP7MANAGERASSIGN000000000001", "role_id": role_rows[1]["id"], "permission_id": permission_rows[3]["id"], "status": "active", "created_at": now, "updated_at": now},
            {"id": "RP7MANAGERAUDIT0000000000001", "role_id": role_rows[1]["id"], "permission_id": permission_rows[5]["id"], "status": "active", "created_at": now, "updated_at": now},
        ],
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table_name in ("niam_role_assignments", "niam_role_permissions", "niam_permissions", "niam_roles"):
        if table_name in inspector.get_table_names():
            _drop_table_indexes(table_name)
            op.drop_table(table_name)
