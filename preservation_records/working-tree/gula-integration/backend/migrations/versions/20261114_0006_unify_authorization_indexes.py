"""Unify authorization indexes omitted by origin/main.

Revision ID: 20261114_0006
Revises: 20261114_0005
Create Date: 2026-11-14

origin/main comments out the explicit index creation in
20260722_0001_authorization_expansion (leaving an unused `_index_exists`
helper). The local lineage created them. Restore the local behaviour with
idempotent CREATE INDEX IF NOT EXISTS, matching the local revision exactly.
"""

from __future__ import annotations

from alembic import op

revision = "20261114_0006"
down_revision = "20261114_0005"
branch_labels = None
depends_on = None

_INDEXES = (
    ("ix_tenants_tenant_id", "tenants", "tenant_id"),
    ("ix_tenants_parent", "tenants", "parent_tenant_id"),
    ("ix_roles_parent", "roles", "parent_role_id"),
    ("ix_roles_group", "roles", "role_group_id"),
    ("ix_role_assignments_user", "role_assignments", "user_id"),
    ("ix_role_assignments_role", "role_assignments", "role_id"),
    ("ix_role_assignments_status", "role_assignments", "status"),
    ("ix_authz_audit_user", "authorization_audit", "user_id"),
    ("ix_authz_audit_action", "authorization_audit", "action"),
    ("ix_authz_audit_resource", "authorization_audit", "resource_id"),
    ("ix_users_user_type", "users", "user_type"),
    ("ix_users_organization", "users", "organization_id"),
    ("ix_users_tenant", "users", "tenant_id"),
    ("ix_users_governorate", "users", "governorate_id"),
    ("ix_organizations_tenant", "organizations", "tenant_id"),
)


def upgrade() -> None:
    for name, table, column in _INDEXES:
        op.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({column})")


def downgrade() -> None:
    for name, _table, _column in _INDEXES:
        op.execute(f"DROP INDEX IF EXISTS {name}")
