"""B5 — canonical NIAM delegation input to the single authorization authority

Revision ID: 20261119_0002
Revises: 20261119_0001

Creates ``niam_delegations`` — an additive, scoped, revocable, time-bounded,
depth-limited delegation record consumed by the canonical
``RolePermissionService.effective_permissions``. No existing table or column is
altered, no role/permission catalog entry is created, and no data is migrated.

Owner directive GULA-MASTER-AUTH-2026-11-19 §5/B5 (AUD-SEC-008).
Fully reversible: ``downgrade`` drops only this table.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20261119_0002"
down_revision: str | None = "20261119_0001"


def _has_table(name: str) -> bool:
    conn = op.get_bind()
    return conn.dialect.has_table(conn, name)


def upgrade() -> None:
    if _has_table("niam_delegations"):
        return
    op.create_table(
        "niam_delegations",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("uuid", sa.String(36), nullable=False),
        sa.Column("delegator_account_id", sa.String(26), nullable=False),
        sa.Column("delegate_account_id", sa.String(26), nullable=False),
        sa.Column("role_id", sa.String(26), nullable=False),
        sa.Column("organization_id", sa.String(26), nullable=False),
        sa.Column("facility_id", sa.String(26), nullable=True),
        sa.Column("department_id", sa.String(26), nullable=True),
        sa.Column("unit_id", sa.String(26), nullable=True),
        sa.Column("workspace_id", sa.String(26), nullable=True),
        sa.Column("scope_type", sa.String(30), nullable=False),
        sa.Column("permission_keys", sa.JSON(), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'active'")),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by", sa.String(26), nullable=True),
        sa.Column("revocation_reason", sa.String(500), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.CheckConstraint("depth >= 1 AND depth <= 3", name="ck_niam_delegations_depth"),
        sa.ForeignKeyConstraint(["delegator_account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["delegate_account_id"], ["niam_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["niam_roles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["niam_organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("uuid", name="uq_niam_delegations_uuid"),
    )
    for column in (
        "uuid", "delegator_account_id", "delegate_account_id", "role_id",
        "organization_id", "facility_id", "department_id", "unit_id",
        "workspace_id", "expires_at", "status",
    ):
        op.create_index(
            f"ix_niam_delegations_{column}", "niam_delegations", [column], unique=False
        )
    # Composite indexes align with the ORM model declarations in
    # app/identity/models/delegation.py (avoids new autogenerate drift).
    op.create_index(
        "ix_niam_delegations_delegate",
        "niam_delegations",
        ["delegate_account_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_niam_delegations_role",
        "niam_delegations",
        ["role_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    if not _has_table("niam_delegations"):
        return
    op.drop_index("ix_niam_delegations_role", table_name="niam_delegations")
    op.drop_index("ix_niam_delegations_delegate", table_name="niam_delegations")
    for column in (
        "uuid", "delegator_account_id", "delegate_account_id", "role_id",
        "organization_id", "facility_id", "department_id", "unit_id",
        "workspace_id", "expires_at", "status",
    ):
        op.drop_index(f"ix_niam_delegations_{column}", table_name="niam_delegations")
    op.drop_table("niam_delegations")
