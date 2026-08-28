"""Additive canonical finance/insurance core over legacy projections.

Revision ID: 20260828_0017
Revises: 20260828_0016
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260828_0017"
down_revision: str | None = "20260828_0016"
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table)


def _index_exists(name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(name == item["name"] for table in inspector.get_table_names() for item in inspector.get_indexes(table))


def _create_index(name: str, table: str, *columns: str) -> None:
    if not _index_exists(name) and _table_exists(table):
        op.create_index(name, table, list(columns))


def upgrade() -> None:
    if not _table_exists("core_financial_command_receipts"):
        op.create_table(
            "core_financial_command_receipts",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("actor_account_id", sa.String(26), nullable=False),
            sa.Column("operation", sa.String(100), nullable=False),
            sa.Column("idempotency_key", sa.String(128), nullable=False),
            sa.Column("request_fingerprint", sa.String(64), nullable=False),
            sa.Column("resource_id", sa.String(26)),
            sa.Column("response_body", sa.JSON()),
            sa.Column("status", sa.String(24), nullable=False, server_default="CLAIMED"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.UniqueConstraint("actor_account_id", "operation", "idempotency_key", name="uq_fin_command_receipt"),
            sa.CheckConstraint("status IN ('CLAIMED','COMPLETED','REJECTED')", name="ck_fin_command_receipt_status"),
        )
    if not _table_exists("core_financial_payers"):
        op.create_table(
            "core_financial_payers",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("name", sa.String(240), nullable=False),
            sa.Column("payer_type", sa.String(32), nullable=False),
            sa.Column("jurisdiction", sa.String(80), nullable=False, server_default="IQ"),
            sa.Column("status", sa.String(24), nullable=False, server_default="ACTIVE"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.CheckConstraint("payer_type IN ('GOVERNMENT','PRIVATE','EMPLOYER','TPA','SELF_PAY','OTHER')", name="ck_fin_payer_type"),
            sa.CheckConstraint("status IN ('ACTIVE','SUSPENDED','TERMINATED')", name="ck_fin_payer_status"),
            sa.CheckConstraint("version > 0", name="ck_fin_payer_version"),
        )
    if not _table_exists("core_financial_coverages"):
        op.create_table(
            "core_financial_coverages",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("member_id", sa.String(26), nullable=False),
            sa.Column("payer_id", sa.String(26), sa.ForeignKey("core_financial_payers.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("plan_code", sa.String(120), nullable=False),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
            sa.Column("valid_to", sa.DateTime(timezone=True)),
            sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
            sa.Column("limits", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("network", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("benefits", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.CheckConstraint("status IN ('ACTIVE','EXPIRED','SUSPENDED','PENDING','UNKNOWN','TERMINATED')", name="ck_fin_coverage_status"),
            sa.CheckConstraint("version > 0", name="ck_fin_coverage_version"),
        )
    if not _table_exists("core_financial_eligibility_checks"):
        op.create_table(
            "core_financial_eligibility_checks",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("coverage_id", sa.String(26), sa.ForeignKey("core_financial_coverages.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("member_id", sa.String(26), nullable=False),
            sa.Column("service_id", sa.String(26)),
            sa.Column("provider_account_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="REQUESTED"),
            sa.Column("provider_reference", sa.String(160)),
            sa.Column("response_payload", sa.JSON()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("idempotency_key", sa.String(128), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("provider_account_id", "idempotency_key", name="uq_fin_eligibility_idempotency"),
            sa.CheckConstraint("status IN ('REQUESTED','PROCESSING','ELIGIBLE','INELIGIBLE','UNKNOWN','FAILED')", name="ck_fin_eligibility_status"),
            sa.CheckConstraint("version > 0", name="ck_fin_eligibility_version"),
        )
    if not _table_exists("core_financial_preauthorizations"):
        op.create_table(
            "core_financial_preauthorizations",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("member_id", sa.String(26), nullable=False),
            sa.Column("payer_id", sa.String(26), sa.ForeignKey("core_financial_payers.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("provider_account_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("service_id", sa.String(26), nullable=False),
            sa.Column("encounter_id", sa.String(26)),
            sa.Column("clinical_indication", sa.Text(), nullable=False),
            sa.Column("estimated_amount_minor", sa.BigInteger(), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False, server_default="IQD"),
            sa.Column("status", sa.String(24), nullable=False, server_default="REQUESTED"),
            sa.Column("decision_reason", sa.Text()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("idempotency_key", sa.String(128), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.CheckConstraint("estimated_amount_minor >= 0", name="ck_fin_preauth_amount"),
            sa.CheckConstraint("status IN ('REQUESTED','UNDER_REVIEW','APPROVED','PARTIALLY_APPROVED','DENIED','EXPIRED','CANCELLED')", name="ck_fin_preauth_status"),
        )
    if not _table_exists("core_financial_services"):
        op.create_table(
            "core_financial_services",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("code", sa.String(120), nullable=False),
            sa.Column("name", sa.String(240), nullable=False),
            sa.Column("specialty", sa.String(120)),
            sa.Column("provider_account_id", sa.String(26), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False, server_default="IQD"),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("facility_id", "code", "version", name="uq_fin_service_version"),
            sa.CheckConstraint("version > 0", name="ck_fin_service_version"),
        )
    if not _table_exists("core_financial_service_prices"):
        op.create_table(
            "core_financial_service_prices",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("service_id", sa.String(26), sa.ForeignKey("core_financial_services.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("amount_minor", sa.BigInteger(), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
            sa.Column("valid_to", sa.DateTime(timezone=True)),
            sa.Column("source", sa.String(80), nullable=False, server_default="SYNTHETIC"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.CheckConstraint("amount_minor >= 0", name="ck_fin_service_price_amount"),
            sa.CheckConstraint("version > 0", name="ck_fin_service_price_version"),
        )
    if not _table_exists("core_financial_bills"):
        op.create_table(
            "core_financial_bills",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("provider_account_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("encounter_id", sa.String(26)),
            sa.Column("coverage_id", sa.String(26), sa.ForeignKey("core_financial_coverages.id", ondelete="RESTRICT")),
            sa.Column("currency", sa.String(3), nullable=False, server_default="IQD"),
            sa.Column("gross_minor", sa.BigInteger(), nullable=False),
            sa.Column("discount_minor", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("covered_minor", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("copay_minor", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("deductible_minor", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("noncovered_minor", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("net_minor", sa.BigInteger(), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.CheckConstraint("gross_minor >= 0 AND discount_minor >= 0 AND covered_minor >= 0 AND copay_minor >= 0 AND deductible_minor >= 0 AND noncovered_minor >= 0 AND net_minor >= 0", name="ck_fin_bill_nonnegative"),
            sa.CheckConstraint("net_minor = gross_minor - discount_minor - covered_minor + deductible_minor + noncovered_minor", name="ck_fin_bill_total"),
            sa.CheckConstraint("status IN ('DRAFT','ISSUED','PARTIALLY_PAID','PAID','VOID','REFUNDED')", name="ck_fin_bill_status"),
            sa.CheckConstraint("version > 0", name="ck_fin_bill_version"),
        )
    if not _table_exists("core_financial_bill_items"):
        op.create_table(
            "core_financial_bill_items",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("bill_id", sa.String(26), sa.ForeignKey("core_financial_bills.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("service_id", sa.String(26), sa.ForeignKey("core_financial_services.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("description", sa.String(240), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("unit_price_minor", sa.BigInteger(), nullable=False),
            sa.Column("total_minor", sa.BigInteger(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.CheckConstraint("quantity > 0 AND unit_price_minor >= 0 AND total_minor = quantity * unit_price_minor", name="ck_fin_bill_item_math"),
        )
    if not _table_exists("core_financial_claims"):
        op.create_table(
            "core_financial_claims",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("bill_id", sa.String(26), sa.ForeignKey("core_financial_bills.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("provider_account_id", sa.String(26), nullable=False),
            sa.Column("payer_id", sa.String(26), sa.ForeignKey("core_financial_payers.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("amount_minor", sa.BigInteger(), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("idempotency_key", sa.String(128), nullable=False),
            sa.Column("submitted_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("provider_account_id", "idempotency_key", name="uq_fin_claim_idempotency"),
            sa.CheckConstraint("amount_minor > 0", name="ck_fin_claim_amount"),
            sa.CheckConstraint("status IN ('DRAFT','SUBMITTED','RECEIVED','UNDER_REVIEW','APPROVED','PARTIALLY_APPROVED','DENIED','PAID','REJECTED','APPEALED')", name="ck_fin_claim_status"),
        )
    if not _table_exists("core_financial_claim_items"):
        op.create_table(
            "core_financial_claim_items",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("claim_id", sa.String(26), sa.ForeignKey("core_financial_claims.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("service_id", sa.String(26), sa.ForeignKey("core_financial_services.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("amount_minor", sa.BigInteger(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.CheckConstraint("amount_minor > 0", name="ck_fin_claim_item_amount"),
        )
    if not _table_exists("core_financial_payments"):
        op.create_table(
            "core_financial_payments",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("bill_id", sa.String(26), sa.ForeignKey("core_financial_bills.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("payer_id", sa.String(26), sa.ForeignKey("core_financial_payers.id", ondelete="RESTRICT")),
            sa.Column("payee_organization_id", sa.String(26), nullable=False),
            sa.Column("amount_minor", sa.BigInteger(), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("reference", sa.String(160), nullable=False, unique=True),
            sa.Column("provider", sa.String(80), nullable=False, server_default="SYNTHETIC"),
            sa.Column("status", sa.String(24), nullable=False, server_default="INITIATED"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("idempotency_key", sa.String(128), nullable=False),
            sa.Column("captured_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("payee_organization_id", "idempotency_key", name="uq_fin_payment_idempotency"),
            sa.CheckConstraint("amount_minor > 0", name="ck_fin_payment_amount"),
            sa.CheckConstraint("status IN ('INITIATED','AUTHORIZED','CAPTURED','SETTLED','FAILED','CANCELLED','REFUNDED','PARTIALLY_REFUNDED','PENDING')", name="ck_fin_payment_status"),
        )
    if not _table_exists("core_financial_payment_events"):
        op.create_table(
            "core_financial_payment_events",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("payment_id", sa.String(26), sa.ForeignKey("core_financial_payments.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("event_id", sa.String(160), nullable=False, unique=True),
            sa.Column("event_type", sa.String(48), nullable=False),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("signature_valid", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("nonce", sa.String(160)),
            sa.Column("payload_hash", sa.String(64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("nonce", name="uq_core_financial_payment_event_nonce"),
        )
    if not _table_exists("core_financial_refunds"):
        op.create_table(
            "core_financial_refunds",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("payment_id", sa.String(26), sa.ForeignKey("core_financial_payments.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("amount_minor", sa.BigInteger(), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("reason", sa.String(500), nullable=False),
            sa.Column("reference", sa.String(160), nullable=False, unique=True),
            sa.Column("status", sa.String(24), nullable=False, server_default="REQUESTED"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("idempotency_key", sa.String(128), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("payment_id", "idempotency_key", name="uq_fin_refund_idempotency"),
            sa.CheckConstraint("amount_minor > 0", name="ck_fin_refund_amount"),
            sa.CheckConstraint("status IN ('REQUESTED','COMPLETED','FAILED','CANCELLED')", name="ck_fin_refund_status"),
        )
    if not _table_exists("core_financial_ledger_accounts"):
        op.create_table(
            "core_financial_ledger_accounts",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("code", sa.String(80), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.UniqueConstraint("organization_id", "code", name="uq_fin_ledger_account_code"),
        )
    if not _table_exists("core_financial_ledger_entries"):
        op.create_table(
            "core_financial_ledger_entries",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("transaction_id", sa.String(26), nullable=False),
            sa.Column("account_id", sa.String(26), sa.ForeignKey("core_financial_ledger_accounts.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("debit_minor", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("credit_minor", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("reference_type", sa.String(80), nullable=False),
            sa.Column("reference_id", sa.String(26), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.CheckConstraint("debit_minor >= 0 AND credit_minor >= 0 AND ((debit_minor > 0 AND credit_minor = 0) OR (credit_minor > 0 AND debit_minor = 0))", name="ck_fin_ledger_entry_side"),
        )
    if not _table_exists("core_financial_settlements"):
        op.create_table(
            "core_financial_settlements",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("payer_id", sa.String(26), sa.ForeignKey("core_financial_payers.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("amount_minor", sa.BigInteger(), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="PROPOSED"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("idempotency_key", sa.String(128), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_fin_settlement_idempotency"),
            sa.CheckConstraint("amount_minor >= 0", name="ck_fin_settlement_amount"),
            sa.CheckConstraint("status IN ('PROPOSED','APPROVED','PAID','CONFLICT','CANCELLED')", name="ck_fin_settlement_status"),
        )
    if not _table_exists("core_financial_reconciliation_records"):
        op.create_table(
            "core_financial_reconciliation_records",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("source", sa.String(48), nullable=False),
            sa.Column("external_reference", sa.String(160), nullable=False),
            sa.Column("local_reference", sa.String(160)),
            sa.Column("status", sa.String(24), nullable=False, server_default="OPEN"),
            sa.Column("mismatch_code", sa.String(80)),
            sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("source", "external_reference", name="uq_fin_reconciliation_external"),
            sa.CheckConstraint("status IN ('OPEN','MATCHED','RESOLVED','ESCALATED')", name="ck_fin_reconciliation_status"),
        )
    if not _table_exists("core_financial_outbox_events"):
        op.create_table(
            "core_financial_outbox_events",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("event_key", sa.String(160), nullable=False, unique=True),
            sa.Column("event_type", sa.String(80), nullable=False),
            sa.Column("aggregate_type", sa.String(80), nullable=False),
            sa.Column("aggregate_id", sa.String(26), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.CheckConstraint("status IN ('PENDING','SENT','FAILED')", name="ck_fin_outbox_status"),
        )

    if _table_exists("core_financial_bills"):
        bill_inspector = sa.inspect(op.get_bind())
        bill_columns = {column["name"] for column in bill_inspector.get_columns("core_financial_bills")}
        if "coverage_id" not in bill_columns:
            op.add_column("core_financial_bills", sa.Column("coverage_id", sa.String(26), nullable=True))
            op.create_foreign_key("fk_core_financial_bill_coverage", "core_financial_bills", "core_financial_coverages", ["coverage_id"], ["id"], ondelete="RESTRICT")
        if not _index_exists("ix_core_financial_bill_coverage"):
            op.create_index("ix_core_financial_bill_coverage", "core_financial_bills", ["coverage_id"])

    for name, table, columns in (
        ("ix_core_financial_command_actor_operation", "core_financial_command_receipts", ("actor_account_id", "operation", "created_at")),
        ("ix_core_financial_coverage_member_status", "core_financial_coverages", ("member_id", "status")),
        ("ix_core_financial_bill_scope_status", "core_financial_bills", ("organization_id", "facility_id", "status", "created_at")),
        ("ix_core_financial_claim_scope_status", "core_financial_claims", ("provider_account_id", "status", "created_at")),
        ("ix_core_financial_payment_scope_status", "core_financial_payments", ("payee_organization_id", "status", "created_at")),
        ("ix_core_financial_ledger_transaction", "core_financial_ledger_entries", ("transaction_id", "created_at")),
    ):
        _create_index(name, table, *columns)

    permissions = (
        ("P17FINPAYER000001", "financial.payer.manage", "Manage financial payers", "إدارة الجهات الدافعة", "financial_payer", "manage"),
        ("P17FINCOVR0000001", "financial.coverage.write", "Manage coverage", "إدارة التغطية", "financial_coverage", "write"),
        ("P17FINELIG0000001", "financial.eligibility.check", "Check eligibility", "فحص الأهلية", "financial_eligibility", "check"),
        ("P17FINPAUTH000001", "financial.preauth.write", "Create preauthorizations", "إنشاء الموافقات المسبقة", "financial_preauthorization", "write"),
        ("P17FINSERV0000001", "financial.service.manage", "Manage billable services", "إدارة الخدمات المسعرة", "financial_service", "manage"),
        ("P17FINBILL0000001", "financial.bill.create", "Create bills", "إنشاء الفواتير", "financial_bill", "create"),
        ("P17FINCLMW0000001", "financial.claim.write", "Create claims", "إنشاء المطالبات", "financial_claim", "write"),
        ("P17FINCLMR0000001", "financial.claim.review", "Review claims", "مراجعة المطالبات", "financial_claim", "review"),
        ("P17FINPAYW0000001", "financial.payment.write", "Initiate payments", "بدء المدفوعات", "financial_payment", "write"),
        ("P17FINPAYC0000001", "financial.payment.capture", "Capture payments", "تحصيل المدفوعات", "financial_payment", "capture"),
        ("P17FINREFW0000001", "financial.refund.write", "Create refunds", "إنشاء رد الأموال", "financial_refund", "write"),
    )
    for index, row in enumerate(permissions):
        if _table_exists("niam_permissions") and not op.get_bind().execute(sa.text("SELECT 1 FROM niam_permissions WHERE permission_key = :permission_key"), {"permission_key": row[1]}).scalar():
            op.get_bind().execute(sa.text("INSERT INTO niam_permissions (id, uuid, permission_key, name, name_ar, description, resource, action, sensitivity, status, version, created_at, updated_at) VALUES (:id, :uuid, :permission_key, :name, :name_ar, :description, :resource, :action, 'high', 'active', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"), {"id": row[0], "uuid": f"p17-finance-{index:02d}", "permission_key": row[1], "name": row[2], "name_ar": row[3], "description": row[2], "resource": row[4], "action": row[5]})


def downgrade() -> None:
    for table in ("core_financial_outbox_events", "core_financial_reconciliation_records", "core_financial_settlements", "core_financial_ledger_entries", "core_financial_ledger_accounts", "core_financial_refunds", "core_financial_payment_events", "core_financial_payments", "core_financial_claim_items", "core_financial_claims", "core_financial_bill_items", "core_financial_bills", "core_financial_service_prices", "core_financial_services", "core_financial_preauthorizations", "core_financial_eligibility_checks", "core_financial_coverages", "core_financial_payers", "core_financial_command_receipts"):
        if _table_exists(table):
            op.drop_table(table)
