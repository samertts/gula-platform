"""Add national authorization expansion tables: tenants, permissions, roles, role_assignments, abac_policies, field_security, delegations, break_glass_sessions, authorization_audit

Revision ID: 20260722_0001
Revises: 20260720_0001_gap_closure_composite_indexes
Create Date: 2026-07-22

Tables:
  - tenants                      — Multi-tenant hierarchy (national, governorate, directorate, facility)
  - permissions                  — Canonical permission registry (1,284 permissions, 30 domains)
  - roles                        — Role catalog with hierarchy/inheritance (171 roles, 5 levels)
  - role_permissions             — Many-to-many role ↔ permission mapping
  - role_groups                  — Role groups/templates for bulk provisioning
  - role_group_members           — Many-to-many role_group ↔ role mapping
  - role_assignments             — User role assignments with scope (org/facility/dept)
  - abac_policies                — Attribute-based access control policies
  - field_security               — Field-level security configuration
  - delegations                  — Role delegation (temporary authority transfer)
  - break_glass_sessions         — Emergency access sessions
  - authorization_audit          — Immutable audit log for authorization decisions

Columns added to existing tables:
  - users: user_type, organization_id, facility_id, tenant_id, governorate_id,
           directorate_id, department_id, mfa_enabled, perm_version, preferences
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260722_0001"
down_revision: Union[str, None] = "20260720_0001"


def _has_table(name: str) -> bool:
    conn = op.get_bind()
    return conn.dialect.has_table(conn, name)


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    if not conn.dialect.has_table(conn, table):
        return False
    insp = sa.inspect(conn)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols


def _index_exists(name: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    try:
        indexes = insp.get_indexes("users")
        return any(i["name"] == name for i in indexes)
    except Exception:
        return False


def upgrade() -> None:
    # ── 1. tenants ────────────────────────────────────────────────────────────
    if not _has_table("tenants"):
        op.create_table(
            "tenants",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("tenant_id", sa.String(length=100), nullable=False),
            sa.Column("name_en", sa.String(length=200), nullable=False),
            sa.Column("name_ar", sa.String(length=200), nullable=False),
            sa.Column("domain", sa.String(length=200), nullable=True),
            sa.Column("tenant_type", sa.String(length=50), nullable=False, server_default=sa.text("'governorate'")),
            sa.Column("parent_tenant_id", sa.Integer(), nullable=True),
            sa.Column("phone", sa.String(length=30), nullable=True),
            sa.Column("address", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("max_users", sa.Integer(), nullable=True),
            sa.Column("feature_flags", sa.JSON(), nullable=True),
            sa.Column("settings", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("tenant_id"),
            sa.UniqueConstraint("domain"),
        )
        try:
            pass
        except Exception:
            pass
        # op.create_index("ix_tenants_tenant_id", "tenants", ["tenant_id"])
        try:
            pass
        except Exception:
            pass
        # op.create_index("ix_tenants_parent", "tenants", ["parent_tenant_id"])

    # ── 2. permissions ────────────────────────────────────────────────────────
    if not _has_table("permissions"):
        op.create_table(
            "permissions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("permission_id", sa.String(length=100), nullable=False),
            sa.Column("name_en", sa.String(length=200), nullable=False),
            sa.Column("name_ar", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("domain", sa.String(length=50), nullable=False),
            sa.Column("resource", sa.String(length=50), nullable=False),
            sa.Column("action", sa.String(length=50), nullable=False),
            sa.Column("risk_level", sa.String(length=20), nullable=False, server_default=sa.text("'low'")),
            sa.Column("is_sensitive", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("requires_mfa", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("requires_justification", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("is_audited", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("permission_id"),
        )
        try:
            pass
        except Exception:
            pass

    # ── 3. roles ──────────────────────────────────────────────────────────────
    if not _has_table("roles"):
        op.create_table(
            "roles",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("role_id", sa.String(length=100), nullable=False),
            sa.Column("name_en", sa.String(length=200), nullable=False),
            sa.Column("name_ar", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("level", sa.String(length=50), nullable=False, server_default=sa.text("'department'")),
            sa.Column("parent_role_id", sa.String(length=100), nullable=True),
            sa.Column("role_group_id", sa.String(length=100), nullable=True),
            sa.Column("is_temporary", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("is_delegatable", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("requires_mfa", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("max_duration_hours", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("version", sa.Integer(), nullable=True, server_default=sa.text("1")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("role_id"),
        )
        try:
            pass
        except Exception:
            pass
        # op.create_index("ix_roles_role_id", "roles", ["role_id"])
        try:
            pass
        except Exception:
            pass
        # op.create_index("ix_roles_parent", "roles", ["parent_role_id"])
        try:
            pass
        except Exception:
            pass
        # op.create_index("ix_roles_group", "roles", ["role_group_id"])

    # ── 4. role_permissions ───────────────────────────────────────────────────
    if not _has_table("role_permissions"):
        op.create_table(
            "role_permissions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("role_id", sa.String(length=100), sa.ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False),
            sa.Column("permission_id", sa.String(length=100), sa.ForeignKey("permissions.permission_id", ondelete="CASCADE"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    # ── 5. role_groups ────────────────────────────────────────────────────────
    if not _has_table("role_groups"):
        op.create_table(
            "role_groups",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("group_id", sa.String(length=100), nullable=False),
            sa.Column("name_en", sa.String(length=200), nullable=False),
            sa.Column("name_ar", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_template", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("group_id"),
        )

    # ── 6. role_group_members ─────────────────────────────────────────────────
    if not _has_table("role_group_members"):
        op.create_table(
            "role_group_members",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("group_id", sa.String(length=100), sa.ForeignKey("role_groups.group_id", ondelete="CASCADE"), nullable=False),
            sa.Column("role_id", sa.String(length=100), sa.ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    # ── 7. role_assignments ───────────────────────────────────────────────────
    if not _has_table("role_assignments"):
        op.create_table(
            "role_assignments",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("role_id", sa.String(length=100), sa.ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False),
            sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
            sa.Column("facility_id", sa.Integer(), sa.ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True),
            sa.Column("department_id", sa.Integer(), nullable=True),
            sa.Column("assigned_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_primary", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("is_delegated", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("delegation_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=True, server_default=sa.text("'active'")),
            sa.PrimaryKeyConstraint("id"),
        )
        try:
            pass
        except Exception:
            pass
        # op.create_index("ix_role_assignments_user", "role_assignments", ["user_id"])
        try:
            pass
        except Exception:
            pass
        # op.create_index("ix_role_assignments_role", "role_assignments", ["role_id"])
        try:
            pass
        except Exception:
            pass
        # op.create_index("ix_role_assignments_status", "role_assignments", ["status"])

    # ── 8. abac_policies ──────────────────────────────────────────────────────
    if not _has_table("abac_policies"):
        op.create_table(
            "abac_policies",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("policy_id", sa.String(length=100), nullable=False),
            sa.Column("name_en", sa.String(length=200), nullable=False),
            sa.Column("name_ar", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("version", sa.String(length=20), nullable=False, server_default=sa.text("'1.0.0'")),
            sa.Column("status", sa.String(length=20), nullable=True, server_default=sa.text("'draft'")),
            sa.Column("effect", sa.String(length=10), nullable=False, server_default=sa.text("'deny'")),
            sa.Column("priority", sa.Integer(), nullable=True, server_default=sa.text("100")),
            sa.Column("category", sa.String(length=50), nullable=True),
            sa.Column("target", sa.JSON(), nullable=True),
            sa.Column("conditions", sa.JSON(), nullable=True),
            sa.Column("obligations", sa.JSON(), nullable=True),
            sa.Column("validity_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("validity_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("signature", sa.String(length=255), nullable=True),
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("policy_id"),
        )

    # ── 9. field_security ─────────────────────────────────────────────────────
    if not _has_table("field_security"):
        op.create_table(
            "field_security",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("resource_type", sa.String(length=50), nullable=False),
            sa.Column("field_name", sa.String(length=100), nullable=False),
            sa.Column("default_level", sa.String(length=20), nullable=False, server_default=sa.text("'public'")),
            sa.Column("consent_required", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("encryption_required", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("masking_pattern", sa.String(length=100), nullable=True),
            sa.Column("audit_access", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("purpose_restricted", sa.JSON(), nullable=True),
            sa.Column("levels_by_role", sa.JSON(), nullable=True),
            sa.Column("levels_by_org_type", sa.JSON(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    # ── 10. delegations ───────────────────────────────────────────────────────
    if not _has_table("delegations"):
        op.create_table(
            "delegations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("delegator_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("delegate_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("role_id", sa.String(length=100), sa.ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False),
            sa.Column("delegation_type", sa.String(length=30), nullable=False),
            sa.Column("scope", sa.JSON(), nullable=True),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=True, server_default=sa.text("'active'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    # ── 11. break_glass_sessions ──────────────────────────────────────────────
    if not _has_table("break_glass_sessions"):
        op.create_table(
            "break_glass_sessions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("emergency_category", sa.String(length=50), nullable=False),
            sa.Column("justification", sa.Text(), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=True, server_default=sa.text("'active'")),
            sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("review_status", sa.String(length=20), nullable=True),
            sa.Column("review_notes", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    # ── 12. authorization_audit ───────────────────────────────────────────────
    if not _has_table("authorization_audit"):
        op.create_table(
            "authorization_audit",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("decision_id", sa.String(length=100), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("user_role", sa.String(length=100), nullable=True),
            sa.Column("action", sa.String(length=100), nullable=False),
            sa.Column("resource_type", sa.String(length=50), nullable=False),
            sa.Column("resource_id", sa.String(length=100), nullable=True),
            sa.Column("decision", sa.String(length=20), nullable=False),
            sa.Column("policies_applied", sa.JSON(), nullable=True),
            sa.Column("policy_engine", sa.String(length=20), nullable=True),
            sa.Column("context", sa.JSON(), nullable=True),
            sa.Column("risk_score", sa.Float(), nullable=True),
            sa.Column("justification", sa.Text(), nullable=True),
            sa.Column("is_emergency", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("delegation_id", sa.Integer(), sa.ForeignKey("delegations.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("decision_id"),
        )
        try:
            pass
        except Exception:
            pass
        # op.create_index("ix_authz_audit_user", "authorization_audit", ["user_id"])
        try:
            pass
        except Exception:
            pass
        # op.create_index("ix_authz_audit_action", "authorization_audit", ["action"])
        try:
            pass
        except Exception:
            pass
        # op.create_index("ix_authz_audit_resource", "authorization_audit", ["resource_id"])

    # ── 13. users — add authorization columns ─────────────────────────────────
    if not _has_column("users", "user_type"):
        op.add_column("users", sa.Column("user_type", sa.String(length=50), nullable=True))
        try:
            pass
        except Exception:
            pass
        # op.create_index("ix_users_user_type", "users", ["user_type"])
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("users", schema=None) as batch_op:
            if not _has_column("users", "organization_id"):
                batch_op.add_column(sa.Column("organization_id", sa.Integer(), nullable=True))
            if not _has_column("users", "tenant_id"):
                batch_op.add_column(sa.Column("tenant_id", sa.Integer(), nullable=True))
            if not _has_column("users", "facility_id"):
                batch_op.add_column(sa.Column("facility_id", sa.Integer(), nullable=True))
    else:
        if not _has_column("users", "organization_id"):
            op.add_column("users", sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True))
        if not _has_column("users", "tenant_id"):
            op.add_column("users", sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True))
        if not _has_column("users", "facility_id"):
            op.add_column("users", sa.Column("facility_id", sa.Integer(), sa.ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True))
    if not _has_column("users", "governorate_id"):
        op.add_column("users", sa.Column("governorate_id", sa.String(length=50), nullable=True))
        try:
            pass
        except Exception:
            pass
        # op.create_index("ix_users_governorate", "users", ["governorate_id"])
    if not _has_column("users", "directorate_id"):
        op.add_column("users", sa.Column("directorate_id", sa.String(length=50), nullable=True))
    if not _has_column("users", "department_id"):
        op.add_column("users", sa.Column("department_id", sa.String(length=100), nullable=True))
    if not _has_column("users", "mfa_enabled"):
        op.add_column("users", sa.Column("mfa_enabled", sa.Boolean(), nullable=True, server_default=sa.text("false")))
    if not _has_column("users", "perm_version"):
        op.add_column("users", sa.Column("perm_version", sa.Integer(), nullable=True, server_default=sa.text("1")))
    if not _has_column("users", "preferences"):
        op.add_column("users", sa.Column("preferences", sa.JSON(), nullable=True))

    # ── 14. organizations — add tenant_id FK if missing ────────────────────
    if _has_table("organizations"):
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("organizations", schema=None) as batch_op:
                if not _has_column("organizations", "tenant_id"):
                    batch_op.add_column(sa.Column("tenant_id", sa.Integer(), nullable=True))
        else:
            if not _has_column("organizations", "tenant_id"):
                op.add_column("organizations", sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True))
        if not _has_column("organizations", "governorate_id"):
            op.add_column("organizations", sa.Column("governorate_id", sa.String(length=50), nullable=True))
        if not _has_column("organizations", "directorate_id"):
            op.add_column("organizations", sa.Column("directorate_id", sa.String(length=50), nullable=True))
        if not _has_column("organizations", "contact_email"):
            op.add_column("organizations", sa.Column("contact_email", sa.String(length=200), nullable=True))
        if not _has_column("organizations", "contact_phone"):
            op.add_column("organizations", sa.Column("contact_phone", sa.String(length=30), nullable=True))
        if not _has_column("organizations", "address"):
            op.add_column("organizations", sa.Column("address", sa.Text(), nullable=True))
        if not _has_column("organizations", "metadata"):
            op.add_column("organizations", sa.Column("metadata", sa.JSON(), nullable=True))

    # ── 15. facilities — add tenant context columns if missing ─────────────
    if _has_table("facilities"):
        if not _has_column("facilities", "contact_email"):
            op.add_column("facilities", sa.Column("contact_email", sa.String(length=200), nullable=True))
        if not _has_column("facilities", "contact_phone"):
            op.add_column("facilities", sa.Column("contact_phone", sa.String(length=30), nullable=True))
        if not _has_column("facilities", "address"):
            op.add_column("facilities", sa.Column("address", sa.Text(), nullable=True))


def downgrade() -> None:
    # Drop new columns from users (reverse order)
    for col in ["preferences", "perm_version", "mfa_enabled", "department_id",
                 "directorate_id", "governorate_id", "facility_id", "tenant_id",
                 "organization_id", "user_type"]:
        if _has_column("users", col):
            op.drop_column("users", col)

    # Drop columns from organizations
    for col in ["metadata", "address", "contact_phone", "contact_email",
                 "directorate_id", "governorate_id", "tenant_id"]:
        if _has_column("organizations", col):
            op.drop_column("organizations", col)

    # Drop columns from facilities
    for col in ["address", "contact_phone", "contact_email"]:
        if _has_column("facilities", col):
            op.drop_column("facilities", col)

    # Drop new tables (reverse creation order)
    tables = [
        "authorization_audit",
        "break_glass_sessions",
        "delegations",
        "field_security",
        "abac_policies",
        "role_assignments",
        "role_group_members",
        "role_groups",
        "role_permissions",
        "roles",
        "permissions",
        "tenants",
    ]
    for table in tables:
        if _has_table(table):
            op.drop_table(table)
