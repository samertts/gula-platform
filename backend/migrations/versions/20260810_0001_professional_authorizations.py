"""Wave A (A4): National professional authorization — separable operational
authorization records derived from verified registry entries.

Each authorization carries its own scope (national/directorate/facility),
duration, and lifecycle (active/suspended/revoked/expired), keeping the
identity layer (registry entry) separable from the privilege layer
(authorization).

Revision ID: 20260810_0001
Revises: 20260806_0001
Create Date: 2026-08-10
"""

import sqlalchemy as sa
from alembic import op

revision = "20260810_0001"
down_revision = "20260806_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "niam_professional_authorizations",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("authorization_id", sa.String(length=100), nullable=False),
        sa.Column("registry_id", sa.String(length=26), nullable=False),
        sa.Column("person_id", sa.String(length=26), nullable=False),
        sa.Column("profession", sa.String(length=50), nullable=False),
        sa.Column("scope_type", sa.String(length=30), nullable=False),
        sa.Column("scope_id", sa.String(length=26), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("status_reason", sa.Text(), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("granted_by", sa.String(length=100), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["niam_persons.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["registry_id"],
            ["niam_professional_registry.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_niam_professional_authorizations_uuid",
        "niam_professional_authorizations",
        ["uuid"],
        unique=True,
    )
    op.create_index(
        "ix_niam_professional_authorizations_authorization_id",
        "niam_professional_authorizations",
        ["authorization_id"],
        unique=True,
    )
    op.create_index(
        "ix_niam_professional_authorizations_registry_id",
        "niam_professional_authorizations",
        ["registry_id"],
    )
    op.create_index(
        "ix_niam_professional_authorizations_person_id",
        "niam_professional_authorizations",
        ["person_id"],
    )
    op.create_index(
        "ix_niam_professional_authorizations_profession",
        "niam_professional_authorizations",
        ["profession"],
    )
    op.create_index(
        "ix_niam_professional_authorizations_scope_type",
        "niam_professional_authorizations",
        ["scope_type"],
    )
    op.create_index(
        "ix_niam_professional_authorizations_scope_id",
        "niam_professional_authorizations",
        ["scope_id"],
    )
    op.create_index(
        "ix_niam_professional_authorizations_status",
        "niam_professional_authorizations",
        ["status"],
    )


def downgrade() -> None:
    op.drop_table("niam_professional_authorizations")
