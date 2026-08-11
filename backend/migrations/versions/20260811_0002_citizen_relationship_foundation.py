"""Add explicit account-to-citizen relationship foundation.

Revision ID: 20260811_0002
Revises: 20260811_0001
Create Date: 2026-08-11

This migration is additive only. It does not backfill phone/national-ID
matches, create relationships, enable dual-write, or modify legacy tables.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260811_0002"
down_revision: Union[str, None] = "20260811_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "niam_citizen_relationships",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_kind", sa.String(length=30), nullable=False),
        sa.Column("canonical_account_id", sa.String(length=26), nullable=True),
        sa.Column("legacy_user_id", sa.Integer(), nullable=True),
        sa.Column("legacy_lab_user_id", sa.Integer(), nullable=True),
        sa.Column("citizen_id", sa.String(length=26), nullable=False),
        sa.Column("patient_id", sa.String(length=26), nullable=True),
        sa.Column("relationship_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("purpose", sa.String(length=100), nullable=False, server_default="citizen_workspace"),
        sa.Column("scope", sa.JSON(), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by_account_id", sa.String(length=26), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(length=255), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.CheckConstraint(
            "canonical_account_id IS NOT NULL OR legacy_user_id IS NOT NULL OR legacy_lab_user_id IS NOT NULL",
            name="ck_citizen_relationship_has_source",
        ),
        sa.CheckConstraint(
            "(source_kind = 'canonical_account' AND canonical_account_id IS NOT NULL AND legacy_user_id IS NULL AND legacy_lab_user_id IS NULL) OR "
            "(source_kind = 'legacy_user' AND legacy_user_id IS NOT NULL AND canonical_account_id IS NULL AND legacy_lab_user_id IS NULL) OR "
            "(source_kind = 'legacy_lab_user' AND legacy_lab_user_id IS NOT NULL AND canonical_account_id IS NULL AND legacy_user_id IS NULL)",
            name="ck_citizen_relationship_source_matches_kind",
        ),
        sa.ForeignKeyConstraint(["canonical_account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["legacy_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["legacy_lab_user_id"], ["lab_users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["citizen_id"], ["national_citizens.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["patient_id"], ["national_patients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["verified_by_account_id"], ["niam_accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_citizen_relationships_source_kind", "niam_citizen_relationships", ["source_kind"])
    op.create_index("ix_niam_citizen_relationships_canonical_account_id", "niam_citizen_relationships", ["canonical_account_id"])
    op.create_index("ix_niam_citizen_relationships_legacy_user_id", "niam_citizen_relationships", ["legacy_user_id"])
    op.create_index("ix_niam_citizen_relationships_legacy_lab_user_id", "niam_citizen_relationships", ["legacy_lab_user_id"])
    op.create_index("ix_niam_citizen_relationships_citizen_id", "niam_citizen_relationships", ["citizen_id"])
    op.create_index("ix_niam_citizen_relationships_patient_id", "niam_citizen_relationships", ["patient_id"])
    op.create_index("ix_niam_citizen_relationships_relationship_type", "niam_citizen_relationships", ["relationship_type"])
    op.create_index("ix_niam_citizen_relationships_status", "niam_citizen_relationships", ["status"])
    op.create_index(
        "ix_citizen_relationship_access",
        "niam_citizen_relationships",
        ["citizen_id", "status", "relationship_type"],
    )
    op.create_index("ix_citizen_relationship_expiry", "niam_citizen_relationships", ["status", "expires_at"])


def downgrade() -> None:
    op.drop_index("ix_citizen_relationship_expiry", table_name="niam_citizen_relationships")
    op.drop_index("ix_citizen_relationship_access", table_name="niam_citizen_relationships")
    op.drop_index("ix_niam_citizen_relationships_status", table_name="niam_citizen_relationships")
    op.drop_index("ix_niam_citizen_relationships_relationship_type", table_name="niam_citizen_relationships")
    op.drop_index("ix_niam_citizen_relationships_patient_id", table_name="niam_citizen_relationships")
    op.drop_index("ix_niam_citizen_relationships_citizen_id", table_name="niam_citizen_relationships")
    op.drop_index("ix_niam_citizen_relationships_legacy_lab_user_id", table_name="niam_citizen_relationships")
    op.drop_index("ix_niam_citizen_relationships_legacy_user_id", table_name="niam_citizen_relationships")
    op.drop_index("ix_niam_citizen_relationships_canonical_account_id", table_name="niam_citizen_relationships")
    op.drop_index("ix_niam_citizen_relationships_source_kind", table_name="niam_citizen_relationships")
    op.drop_table("niam_citizen_relationships")
