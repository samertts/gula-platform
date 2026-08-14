"""Add demo-safe billing and insurance projection tables.

Revision ID: 20260814_0009
Revises: 20260814_0008
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260814_0009"
down_revision = "20260814_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "billing_invoices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("encounter_ref", sa.String(length=128), nullable=False),
        sa.Column("invoice_number", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="IQD"),
        sa.Column("gross_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("covered_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("patient_due", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("claim_reference", sa.String(length=128), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("due_at", sa.Date(), nullable=True),
        sa.Column("issued_at", sa.Date(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("lab_id", "invoice_number", name="uq_billing_invoice_lab_number"),
        sa.UniqueConstraint("lab_id", "idempotency_key", name="uq_billing_invoice_lab_idempotency"),
        sa.CheckConstraint("gross_amount >= 0", name="ck_billing_invoice_gross_non_negative"),
        sa.CheckConstraint("covered_amount >= 0", name="ck_billing_invoice_covered_non_negative"),
        sa.CheckConstraint("patient_due >= 0", name="ck_billing_invoice_due_non_negative"),
    )
    op.create_index("ix_billing_invoices_lab_status", "billing_invoices", ["lab_id", "status"])
    op.create_index("ix_billing_invoices_lab_patient", "billing_invoices", ["lab_id", "patient_id"])
    op.create_index("ix_billing_invoices_status", "billing_invoices", ["status"])
    op.create_index("ix_billing_invoices_claim_reference", "billing_invoices", ["claim_reference"])
    op.create_index("ix_billing_invoices_created_at", "billing_invoices", ["created_at"])

    op.create_table(
        "billing_invoice_lines",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("service_code", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("line_amount", sa.Numeric(14, 2), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["billing_invoices.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("invoice_id", "line_number", name="uq_billing_invoice_line_number"),
        sa.CheckConstraint("quantity > 0", name="ck_billing_invoice_line_quantity_positive"),
        sa.CheckConstraint("unit_amount >= 0", name="ck_billing_invoice_line_unit_non_negative"),
        sa.CheckConstraint("line_amount >= 0", name="ck_billing_invoice_line_amount_non_negative"),
    )
    op.create_index("ix_billing_invoice_lines_invoice_id", "billing_invoice_lines", ["invoice_id"])

    op.create_table(
        "insurance_coverages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("payer", sa.String(length=255), nullable=False),
        sa.Column("plan", sa.String(length=255), nullable=False),
        sa.Column("member_id", sa.String(length=128), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False, server_default="needs_verification"),
        sa.Column("verification", sa.String(length=512), nullable=False, server_default="لم يُتحقق"),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("lab_id", "member_id", name="uq_insurance_coverage_lab_member"),
    )
    op.create_index("ix_insurance_coverages_lab_patient", "insurance_coverages", ["lab_id", "patient_id"])
    op.create_index("ix_insurance_coverages_lab_state", "insurance_coverages", ["lab_id", "state"])

    op.create_table(
        "billing_payments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="IQD"),
        sa.Column("method", sa.String(length=64), nullable=False, server_default="synthetic_settlement"),
        sa.Column("reference", sa.String(length=128), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False, server_default="patient_payment"),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invoice_id"], ["billing_invoices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("lab_id", "reference", name="uq_billing_payment_lab_reference"),
        sa.CheckConstraint("amount > 0", name="ck_billing_payment_amount_positive"),
    )
    op.create_index("ix_billing_payments_invoice_id", "billing_payments", ["invoice_id"])
    op.create_index("ix_billing_payments_lab_created", "billing_payments", ["lab_id", "created_at"])
    op.create_index("ix_billing_payments_created_at", "billing_payments", ["created_at"])

    op.create_table(
        "billing_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("safe_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_billing_audit_lab_created", "billing_audit_events", ["lab_id", "created_at"])
    op.create_index("ix_billing_audit_entity", "billing_audit_events", ["entity_type", "entity_id"])
    op.create_index("ix_billing_audit_events_created_at", "billing_audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_billing_audit_events_created_at", table_name="billing_audit_events")
    op.drop_index("ix_billing_audit_entity", table_name="billing_audit_events")
    op.drop_index("ix_billing_audit_lab_created", table_name="billing_audit_events")
    op.drop_table("billing_audit_events")
    op.drop_index("ix_billing_payments_created_at", table_name="billing_payments")
    op.drop_index("ix_billing_payments_lab_created", table_name="billing_payments")
    op.drop_index("ix_billing_payments_invoice_id", table_name="billing_payments")
    op.drop_table("billing_payments")
    op.drop_index("ix_insurance_coverages_lab_state", table_name="insurance_coverages")
    op.drop_index("ix_insurance_coverages_lab_patient", table_name="insurance_coverages")
    op.drop_table("insurance_coverages")
    op.drop_index("ix_billing_invoice_lines_invoice_id", table_name="billing_invoice_lines")
    op.drop_table("billing_invoice_lines")
    op.drop_index("ix_billing_invoices_created_at", table_name="billing_invoices")
    op.drop_index("ix_billing_invoices_claim_reference", table_name="billing_invoices")
    op.drop_index("ix_billing_invoices_status", table_name="billing_invoices")
    op.drop_index("ix_billing_invoices_lab_patient", table_name="billing_invoices")
    op.drop_index("ix_billing_invoices_lab_status", table_name="billing_invoices")
    op.drop_table("billing_invoices")
