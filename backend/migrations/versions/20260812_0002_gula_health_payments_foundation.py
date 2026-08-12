"""GULA Health Payments Foundation (P0).

Revision ID: 20260812_0002
Revises: 20260812_0001
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260812_0002"
down_revision = "20260812_0001"
branch_labels = None
depends_on = None

MONEY = sa.Numeric(18, 2)


def upgrade() -> None:
    op.create_table(
        "pay_invoices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("patient_reference", sa.String(128), nullable=True),
        sa.Column("invoice_number", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IQD"),
        sa.Column("total_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("paid_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("refunded_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("institution_id", "invoice_number", name="uq_pay_invoice_number"),
        sa.CheckConstraint("total_amount >= 0", name="ck_pay_invoice_total_non_negative"),
        sa.CheckConstraint("paid_amount >= 0", name="ck_pay_invoice_paid_non_negative"),
        sa.CheckConstraint("refunded_amount >= 0", name="ck_pay_invoice_refunded_non_negative"),
    )
    op.create_index("ix_pay_invoices_institution_id", "pay_invoices", ["institution_id"])
    op.create_index("ix_pay_invoices_patient_reference", "pay_invoices", ["patient_reference"])
    op.create_index("ix_pay_invoices_status", "pay_invoices", ["status"])

    op.create_table(
        "pay_invoice_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("pay_invoices.id"), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("service_reference", sa.String(128), nullable=True),
        sa.Column("description", sa.String(512), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_amount", MONEY, nullable=False),
        sa.Column("line_amount", MONEY, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("invoice_id", "line_number", name="uq_pay_invoice_line_number"),
        sa.CheckConstraint("quantity > 0", name="ck_pay_invoice_line_quantity_positive"),
        sa.CheckConstraint("unit_amount >= 0", name="ck_pay_invoice_line_unit_non_negative"),
        sa.CheckConstraint("line_amount >= 0", name="ck_pay_invoice_line_total_non_negative"),
    )
    op.create_index("ix_pay_invoice_lines_invoice_id", "pay_invoice_lines", ["invoice_id"])

    op.create_table(
        "pay_payment_intents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("pay_invoices.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IQD"),
        sa.Column("method", sa.String(32), nullable=False, server_default="CASH"),
        sa.Column("status", sa.String(32), nullable=False, server_default="CREATED"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_reference", sa.String(128), nullable=True, unique=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("institution_id", "idempotency_key", name="uq_pay_intent_idempotency"),
        sa.CheckConstraint("amount > 0", name="ck_pay_intent_amount_positive"),
    )
    op.create_index("ix_pay_payment_intents_institution_id", "pay_payment_intents", ["institution_id"])
    op.create_index("ix_pay_payment_intents_invoice_id", "pay_payment_intents", ["invoice_id"])
    op.create_index("ix_pay_payment_intents_status", "pay_payment_intents", ["status"])

    op.create_table(
        "pay_cash_shifts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("cashier_user_id", sa.Integer(), nullable=False),
        sa.Column("terminal_reference", sa.String(128), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IQD"),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("opening_float", MONEY, nullable=False, server_default="0"),
        sa.Column("expected_closing", MONEY, nullable=True),
        sa.Column("actual_closing", MONEY, nullable=True),
        sa.Column("variance_amount", MONEY, nullable=True),
        sa.Column("variance_reason", sa.String(512), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.CheckConstraint("opening_float >= 0", name="ck_pay_cash_shift_opening_non_negative"),
    )
    op.create_index("ix_pay_cash_shifts_institution_id", "pay_cash_shifts", ["institution_id"])
    op.create_index("ix_pay_cash_shifts_cashier_user_id", "pay_cash_shifts", ["cashier_user_id"])
    op.create_index("ix_pay_cash_shifts_status", "pay_cash_shifts", ["status"])

    op.create_table(
        "pay_payment_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("intent_id", sa.String(36), sa.ForeignKey("pay_payment_intents.id"), nullable=False),
        sa.Column("cash_shift_id", sa.String(36), sa.ForeignKey("pay_cash_shifts.id"), nullable=True),
        sa.Column("provider_code", sa.String(64), nullable=False, server_default="cashier"),
        sa.Column("provider_transaction_id", sa.String(128), nullable=True),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IQD"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(64), nullable=True),
        sa.Column("failure_reason", sa.String(512), nullable=True),
        sa.Column("safe_provider_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("provider_code", "provider_transaction_id", name="uq_pay_provider_transaction"),
        sa.CheckConstraint("amount > 0", name="ck_pay_attempt_amount_positive"),
    )
    op.create_index("ix_pay_payment_attempts_intent_id", "pay_payment_attempts", ["intent_id"])
    op.create_index("ix_pay_payment_attempts_cash_shift_id", "pay_payment_attempts", ["cash_shift_id"])
    op.create_index("ix_pay_payment_attempts_status", "pay_payment_attempts", ["status"])

    op.create_table(
        "pay_providers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("provider_type", sa.String(32), nullable=False),
        sa.Column("environment", sa.String(16), nullable=False, server_default="sandbox"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING_REVIEW"),
        sa.Column("supports_refund", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("supports_reconciliation", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "pay_ledger_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("account_type", sa.String(32), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IQD"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("institution_id", "code", name="uq_pay_ledger_account_code"),
    )
    op.create_index("ix_pay_ledger_accounts_institution_id", "pay_ledger_accounts", ["institution_id"])

    op.create_table(
        "pay_ledger_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("reference_type", sa.String(64), nullable=False),
        sa.Column("reference_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="POSTED"),
        sa.Column("reversal_of_entry_id", sa.String(36), sa.ForeignKey("pay_ledger_entries.id"), nullable=True),
        sa.Column("description", sa.String(512), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("posted_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_pay_ledger_entries_institution_id", "pay_ledger_entries", ["institution_id"])

    op.create_table(
        "pay_ledger_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entry_id", sa.String(36), sa.ForeignKey("pay_ledger_entries.id"), nullable=False),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("pay_ledger_accounts.id"), nullable=False),
        sa.Column("debit_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("credit_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IQD"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("debit_amount >= 0", name="ck_pay_ledger_line_debit_non_negative"),
        sa.CheckConstraint("credit_amount >= 0", name="ck_pay_ledger_line_credit_non_negative"),
        sa.CheckConstraint(
            "(debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0)",
            name="ck_pay_ledger_line_one_sided",
        ),
    )
    op.create_index("ix_pay_ledger_lines_entry_id", "pay_ledger_lines", ["entry_id"])
    op.create_index("ix_pay_ledger_lines_account_id", "pay_ledger_lines", ["account_id"])

    op.create_table(
        "pay_refunds",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("pay_invoices.id"), nullable=False),
        sa.Column("payment_intent_id", sa.String(36), sa.ForeignKey("pay_payment_intents.id"), nullable=False),
        sa.Column("cash_shift_id", sa.String(36), sa.ForeignKey("pay_cash_shifts.id"), nullable=True),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IQD"),
        sa.Column("reason", sa.String(512), nullable=False),
        sa.Column("external_reference", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="REQUESTED"),
        sa.Column("requested_by", sa.Integer(), nullable=False),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0", name="ck_pay_refund_amount_positive"),
    )
    op.create_index("ix_pay_refunds_institution_id", "pay_refunds", ["institution_id"])
    op.create_index("ix_pay_refunds_invoice_id", "pay_refunds", ["invoice_id"])
    op.create_index("ix_pay_refunds_payment_intent_id", "pay_refunds", ["payment_intent_id"])
    op.create_index("ix_pay_refunds_cash_shift_id", "pay_refunds", ["cash_shift_id"])
    op.create_index("ix_pay_refunds_status", "pay_refunds", ["status"])

    op.create_table(
        "pay_reconciliation_cases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_reference", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("expected_amount", MONEY, nullable=False),
        sa.Column("observed_amount", MONEY, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IQD"),
        sa.Column("discrepancy_reason", sa.String(512), nullable=False),
        sa.Column("resolved_by", sa.Integer(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_pay_reconciliation_cases_institution_id", "pay_reconciliation_cases", ["institution_id"])
    op.create_index("ix_pay_reconciliation_cases_source_reference", "pay_reconciliation_cases", ["source_reference"])
    op.create_index("ix_pay_reconciliation_cases_status", "pay_reconciliation_cases", ["status"])

    op.create_table(
        "pay_audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("request_id", sa.String(128), nullable=True),
        sa.Column("safe_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_pay_audit_events_institution_id", "pay_audit_events", ["institution_id"])
    op.create_index("ix_pay_audit_entity", "pay_audit_events", ["entity_type", "entity_id"])


def downgrade() -> None:
    for table in (
        "pay_audit_events",
        "pay_reconciliation_cases",
        "pay_refunds",
        "pay_ledger_lines",
        "pay_ledger_entries",
        "pay_ledger_accounts",
        "pay_providers",
        "pay_payment_attempts",
        "pay_cash_shifts",
        "pay_payment_intents",
        "pay_invoice_lines",
        "pay_invoices",
    ):
        op.drop_table(table)
