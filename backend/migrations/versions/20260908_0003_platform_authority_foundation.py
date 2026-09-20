"""Add NIAM Platform Authority assignment foundation (Phase 10).

Revision ID: 20260908_0003
Revises: 20260908_0001

Adds niam_platform_authority_assignments only. No role, permission, or
initial operator is seeded -- see
docs/security/NIAM_PLATFORM_AUTHORITY_ARCHITECTURE.md Section 13 step 2
and Section 7 (bootstrap is an explicit, separate, not-yet-authorized step).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260908_0003"
down_revision = "20260908_0001"
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

    if "niam_platform_authority_assignments" not in tables:
        op.create_table(
            "niam_platform_authority_assignments",
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("identity_id", sa.String(length=26), nullable=False),
            sa.Column("capability", sa.String(length=80), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
            sa.Column("granted_by", sa.String(length=26), nullable=True),
            sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_by", sa.String(length=26), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revocation_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["identity_id"], ["niam_identities.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["granted_by"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["revoked_by"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("uuid", name="uq_niam_platform_authority_assignments_uuid"),
        )
        for column in ("identity_id", "capability", "status"):
            op.create_index(
                f"ix_niam_platform_authority_assignments_{column}",
                "niam_platform_authority_assignments",
                [column],
            )
        # At most one ACTIVE assignment per (identity, capability): a
        # check-then-insert grant can otherwise race (two concurrent grants
        # both observe "no active row" and both insert). Scoped to active
        # rows only (Postgres partial index, precedent:
        # 20260329_0012_lab_result_version_citizen_indexes.py) rather than a
        # blanket unique constraint, because revocation is terminal for a
        # row (mirrors niam_role_assignments' revoked -> {} rule) and a
        # capability must remain re-grantable after a prior revocation.
        op.create_index(
            "uq_niam_platform_authority_active_capability",
            "niam_platform_authority_assignments",
            ["identity_id", "capability"],
            unique=True,
            postgresql_where=sa.text("status = 'active'"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "niam_platform_authority_assignments" in inspector.get_table_names():
        _drop_table_indexes("niam_platform_authority_assignments")
        op.drop_table("niam_platform_authority_assignments")
