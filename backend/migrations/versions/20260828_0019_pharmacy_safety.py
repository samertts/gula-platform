"""Additive pharmacy recall event ledger.

Revision ID: 20260828_0019
Revises: 20260828_0018
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260828_0019"
down_revision: str | None = "20260828_0018"
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if _table_exists("core_prescriptions"):
        inspector = sa.inspect(op.get_bind())
        columns = {column["name"] for column in inspector.get_columns("core_prescriptions")}
        if "controlled_policy_approved_by_account_id" not in columns:
            op.add_column("core_prescriptions", sa.Column("controlled_policy_approved_by_account_id", sa.String(26), nullable=True))
            op.create_foreign_key("fk_core_prescription_policy_approver", "core_prescriptions", "niam_accounts", ["controlled_policy_approved_by_account_id"], ["id"], ondelete="SET NULL")
        if "controlled_policy_approved_at" not in columns:
            op.add_column("core_prescriptions", sa.Column("controlled_policy_approved_at", sa.DateTime(timezone=True), nullable=True))
        if "controlled_policy_reason" not in columns:
            op.add_column("core_prescriptions", sa.Column("controlled_policy_reason", sa.String(500), nullable=True))
        if "controlled_policy_evidence" not in columns:
            op.add_column("core_prescriptions", sa.Column("controlled_policy_evidence", sa.JSON(), nullable=True))
        constraints = {item.get("name") for item in inspector.get_check_constraints("core_prescriptions")}
        if "ck_core_prescription_controlled_policy" in constraints:
            op.drop_constraint("ck_core_prescription_controlled_policy", "core_prescriptions", type_="check")
        op.create_check_constraint("ck_core_prescription_controlled_policy", "core_prescriptions", "controlled_policy_status IN ('NOT_CONTROLLED','PENDING_POLICY_REVIEW','APPROVED_BY_POLICY','REJECTED_BY_POLICY')")

    if _table_exists("core_medication_batches"):
        batch_inspector = sa.inspect(op.get_bind())
        batch_columns = {column["name"] for column in batch_inspector.get_columns("core_medication_batches")}
        if "version" not in batch_columns:
            op.add_column("core_medication_batches", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
        batch_constraints = {item.get("name") for item in batch_inspector.get_check_constraints("core_medication_batches")}
        if "ck_core_medication_batch_version_positive" not in batch_constraints:
            op.create_check_constraint("ck_core_medication_batch_version_positive", "core_medication_batches", "version > 0")

    if not _table_exists("core_medication_recalls"):
        op.create_table(
            "core_medication_recalls",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("batch_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("workspace_id", sa.String(26), nullable=False),
            sa.Column("recall_reference", sa.String(120), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="OPEN"),
            sa.Column("created_by_account_id", sa.String(26), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["batch_id"], ["core_medication_batches.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["created_by_account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
            sa.UniqueConstraint("recall_reference", name="uq_core_medication_recall_reference"),
            sa.UniqueConstraint("batch_id", "status", name="uq_core_medication_recall_batch_status"),
            sa.CheckConstraint("status IN ('OPEN','CLEARED')", name="ck_core_medication_recall_status"),
        )
    inspector = sa.inspect(op.get_bind())
    if not any(item["name"] == "ix_core_medication_recall_scope_status" for item in inspector.get_indexes("core_medication_recalls")):
        op.create_index("ix_core_medication_recall_scope_status", "core_medication_recalls", ["organization_id", "facility_id", "workspace_id", "status", "created_at"])


def downgrade() -> None:
    if _table_exists("core_medication_recalls"):
        op.drop_table("core_medication_recalls")
    if _table_exists("core_medication_batches"):
        batch_inspector = sa.inspect(op.get_bind())
        batch_columns = {column["name"] for column in batch_inspector.get_columns("core_medication_batches")}
        batch_constraints = {item.get("name") for item in batch_inspector.get_check_constraints("core_medication_batches")}
        if "ck_core_medication_batch_version_positive" in batch_constraints:
            op.drop_constraint("ck_core_medication_batch_version_positive", "core_medication_batches", type_="check")
        if "version" in batch_columns:
            op.drop_column("core_medication_batches", "version")
    if _table_exists("core_prescriptions"):
        inspector = sa.inspect(op.get_bind())
        constraints = {item.get("name") for item in inspector.get_check_constraints("core_prescriptions")}
        if "ck_core_prescription_controlled_policy" in constraints:
            op.drop_constraint("ck_core_prescription_controlled_policy", "core_prescriptions", type_="check")
        op.create_check_constraint("ck_core_prescription_controlled_policy", "core_prescriptions", "controlled_policy_status IN ('NOT_CONTROLLED','PENDING_POLICY_REVIEW','REJECTED_BY_POLICY')")
        columns = {column["name"] for column in inspector.get_columns("core_prescriptions")}
        if "controlled_policy_evidence" in columns:
            op.drop_column("core_prescriptions", "controlled_policy_evidence")
        if "controlled_policy_reason" in columns:
            op.drop_column("core_prescriptions", "controlled_policy_reason")
        if "controlled_policy_approved_at" in columns:
            op.drop_column("core_prescriptions", "controlled_policy_approved_at")
        if "controlled_policy_approved_by_account_id" in columns:
            op.drop_constraint("fk_core_prescription_policy_approver", "core_prescriptions", type_="foreignkey")
            op.drop_column("core_prescriptions", "controlled_policy_approved_by_account_id")
