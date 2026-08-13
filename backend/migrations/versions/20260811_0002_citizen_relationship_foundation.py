"""Citizen relationship foundation.

The legacy user/patient tables are deployment-specific. The core relationship
record is therefore created independently, while foreign keys to legacy tables
are added only when those tables exist in the target database.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260811_0002"
down_revision: Union[str, None] = "20260811_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "niam_citizen_relationships"


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return bind.dialect.has_table(bind, name)


def upgrade() -> None:
    if not _has_table(_TABLE):
        op.create_table(
            _TABLE,
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
            sa.ForeignKeyConstraint(["verified_by_account_id"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )

        for constraint_name, column, target_table in (
            ("fk_citizen_relationship_user", "legacy_user_id", "users"),
            ("fk_citizen_relationship_lab_user", "legacy_lab_user_id", "lab_users"),
            ("fk_citizen_relationship_citizen", "citizen_id", "national_citizens"),
            ("fk_citizen_relationship_patient", "patient_id", "national_patients"),
        ):
            if _has_table(target_table):
                op.create_foreign_key(
                    constraint_name,
                    _TABLE,
                    target_table,
                    [column],
                    ["id"],
                    ondelete="RESTRICT",
                )

        indexes = (
            ("ix_niam_citizen_relationships_source_kind", ["source_kind"]),
            ("ix_niam_citizen_relationships_canonical_account_id", ["canonical_account_id"]),
            ("ix_niam_citizen_relationships_legacy_user_id", ["legacy_user_id"]),
            ("ix_niam_citizen_relationships_legacy_lab_user_id", ["legacy_lab_user_id"]),
            ("ix_niam_citizen_relationships_citizen_id", ["citizen_id"]),
            ("ix_niam_citizen_relationships_patient_id", ["patient_id"]),
            ("ix_niam_citizen_relationships_relationship_type", ["relationship_type"]),
            ("ix_niam_citizen_relationships_status", ["status"]),
            ("ix_citizen_relationship_access", ["citizen_id", "status", "relationship_type"]),
            ("ix_citizen_relationship_expiry", ["status", "expires_at"]),
        )
        for index_name, columns in indexes:
            op.create_index(index_name, _TABLE, columns)


def downgrade() -> None:
    if not _has_table(_TABLE):
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for constraint_name in (
        "fk_citizen_relationship_patient",
        "fk_citizen_relationship_citizen",
        "fk_citizen_relationship_lab_user",
        "fk_citizen_relationship_user",
    ):
        if constraint_name in {c["name"] for c in inspector.get_foreign_keys(_TABLE)}:
            op.drop_constraint(constraint_name, _TABLE, type_="foreignkey")

    for index_name in (
        "ix_citizen_relationship_expiry",
        "ix_citizen_relationship_access",
        "ix_niam_citizen_relationships_status",
        "ix_niam_citizen_relationships_relationship_type",
        "ix_niam_citizen_relationships_patient_id",
        "ix_niam_citizen_relationships_citizen_id",
        "ix_niam_citizen_relationships_legacy_lab_user_id",
        "ix_niam_citizen_relationships_legacy_user_id",
        "ix_niam_citizen_relationships_canonical_account_id",
        "ix_niam_citizen_relationships_source_kind",
    ):
        if index_name in {i["name"] for i in inspector.get_indexes(_TABLE)}:
            op.drop_index(index_name, table_name=_TABLE)
    op.drop_table(_TABLE)
