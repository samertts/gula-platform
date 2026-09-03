"""Institution-scoped drug substitution rules and approval requests."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260815_0023"
down_revision: str | None = "20260815_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("pharmacy_drug_substitution_rules"):
        op.create_table(
            "pharmacy_drug_substitution_rules",
            sa.Column("id", sa.String(26), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("original_drug_catalog_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"), nullable=False),
            sa.Column("alternative_drug_catalog_id", sa.Integer(), sa.ForeignKey("pharmacy_drug_catalog.id", ondelete="CASCADE"), nullable=False),
            sa.Column("equivalence_type", sa.String(32), nullable=False, server_default="generic"),
            sa.Column("approval_level", sa.String(32), nullable=False, server_default="pharmacist"),
            sa.Column("requires_patient_consent", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "original_drug_catalog_id", "alternative_drug_catalog_id", name="uq_pharmacy_substitution_rule_pair"),
            sa.CheckConstraint("original_drug_catalog_id <> alternative_drug_catalog_id", name="ck_pharmacy_substitution_rule_distinct_drugs"),
        )
        op.create_index("ix_pharmacy_substitution_rule_original", "pharmacy_drug_substitution_rules", ["lab_id", "original_drug_catalog_id"])
        op.create_index("ix_pharmacy_substitution_rule_alternative", "pharmacy_drug_substitution_rules", ["lab_id", "alternative_drug_catalog_id"])
        op.create_index("ix_pharmacy_substitution_rule_active", "pharmacy_drug_substitution_rules", ["lab_id", "is_active"])

    if not _table_exists("pharmacy_drug_substitution_requests"):
        op.create_table(
            "pharmacy_drug_substitution_requests",
            sa.Column("id", sa.String(26), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("rule_id", sa.String(26), sa.ForeignKey("pharmacy_drug_substitution_rules.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("original_drug_catalog_id", sa.String(26), nullable=False),
            sa.Column("alternative_drug_catalog_id", sa.String(26), nullable=False),
            sa.Column("prescription_id", sa.String(26), nullable=True),
            sa.Column("patient_id", sa.String(26), nullable=True),
            sa.Column("citizen_id", sa.String(26), nullable=True),
            sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
            sa.Column("reason", sa.String(500), nullable=False),
            sa.Column("approval_level", sa.String(32), nullable=False, server_default="pharmacist"),
            sa.Column("approved_by", sa.String(26), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("patient_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("patient_notified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("consumed_sale_id", sa.String(26), sa.ForeignKey("pharmacy_sales.id", ondelete="SET NULL"), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("quantity > 0", name="ck_pharmacy_substitution_request_quantity_positive"),
            sa.CheckConstraint("status IN ('pending', 'approved', 'rejected', 'consumed')", name="ck_pharmacy_substitution_request_status"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_pharmacy_substitution_request_rule", "pharmacy_drug_substitution_requests", ["lab_id", "rule_id"])
        op.create_index("ix_pharmacy_substitution_request_status", "pharmacy_drug_substitution_requests", ["lab_id", "status"])
        op.create_index("ix_pharmacy_substitution_request_patient", "pharmacy_drug_substitution_requests", ["lab_id", "patient_id"])
        op.create_index("ix_pharmacy_substitution_request_sale", "pharmacy_drug_substitution_requests", ["lab_id", "consumed_sale_id"])


def downgrade() -> None:
    if _table_exists("pharmacy_drug_substitution_requests"):
        op.drop_index("ix_pharmacy_substitution_request_sale", table_name="pharmacy_drug_substitution_requests")
        op.drop_index("ix_pharmacy_substitution_request_patient", table_name="pharmacy_drug_substitution_requests")
        op.drop_index("ix_pharmacy_substitution_request_status", table_name="pharmacy_drug_substitution_requests")
        op.drop_index("ix_pharmacy_substitution_request_rule", table_name="pharmacy_drug_substitution_requests")
        op.drop_table("pharmacy_drug_substitution_requests")
    if _table_exists("pharmacy_drug_substitution_rules"):
        op.drop_index("ix_pharmacy_substitution_rule_active", table_name="pharmacy_drug_substitution_rules")
        op.drop_index("ix_pharmacy_substitution_rule_alternative", table_name="pharmacy_drug_substitution_rules")
        op.drop_index("ix_pharmacy_substitution_rule_original", table_name="pharmacy_drug_substitution_rules")
        op.drop_table("pharmacy_drug_substitution_rules")
