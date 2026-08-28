from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.database import Base


def _id() -> str:
    return uuid.uuid4().hex.upper()[:26]


def _now() -> datetime:
    return datetime.now(UTC)


class FinancialCommandReceipt(Base):
    __tablename__ = "core_financial_command_receipts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_account_id = Column(String(26), nullable=False, index=True)
    operation = Column(String(100), nullable=False)
    idempotency_key = Column(String(128), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    resource_id = Column(String(26), nullable=True, index=True)
    response_body = Column(JSON, nullable=True)
    status = Column(String(24), nullable=False, default="CLAIMED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    completed_at = Column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("actor_account_id", "operation", "idempotency_key", name="uq_fin_command_receipt"), CheckConstraint("status IN ('CLAIMED','COMPLETED','REJECTED')", name="ck_fin_command_receipt_status"))


class FinancialPayer(Base):
    __tablename__ = "core_financial_payers"
    id = Column(String(26), primary_key=True, default=_id)
    organization_id = Column(String(26), nullable=False, index=True)
    name = Column(String(240), nullable=False)
    payer_type = Column(String(32), nullable=False)
    jurisdiction = Column(String(80), nullable=False, default="IQ")
    status = Column(String(24), nullable=False, default="ACTIVE")
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (CheckConstraint("payer_type IN ('GOVERNMENT','PRIVATE','EMPLOYER','TPA','SELF_PAY','OTHER')", name="ck_fin_payer_type"), CheckConstraint("status IN ('ACTIVE','SUSPENDED','TERMINATED')", name="ck_fin_payer_status"), CheckConstraint("version > 0", name="ck_fin_payer_version"))


class FinancialCoverage(Base):
    __tablename__ = "core_financial_coverages"
    id = Column(String(26), primary_key=True, default=_id)
    member_id = Column(String(26), nullable=False, index=True)
    payer_id = Column(String(26), ForeignKey("core_financial_payers.id", ondelete="RESTRICT"), nullable=False, index=True)
    plan_code = Column(String(120), nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    status = Column(String(24), nullable=False, default="PENDING")
    limits = Column(JSON, nullable=False, default=dict)
    network = Column(JSON, nullable=False, default=dict)
    benefits = Column(JSON, nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (CheckConstraint("status IN ('ACTIVE','EXPIRED','SUSPENDED','PENDING','UNKNOWN','TERMINATED')", name="ck_fin_coverage_status"), CheckConstraint("version > 0", name="ck_fin_coverage_version"), Index("ix_core_financial_coverage_member_status", "member_id", "status"))


class FinancialEligibilityCheck(Base):
    __tablename__ = "core_financial_eligibility_checks"
    id = Column(String(26), primary_key=True, default=_id)
    coverage_id = Column(String(26), ForeignKey("core_financial_coverages.id", ondelete="RESTRICT"), nullable=False, index=True)
    member_id = Column(String(26), nullable=False, index=True)
    service_id = Column(String(26), nullable=True, index=True)
    provider_account_id = Column(String(26), nullable=False)
    facility_id = Column(String(26), nullable=False)
    status = Column(String(24), nullable=False, default="REQUESTED")
    provider_reference = Column(String(160))
    response_payload = Column(JSON)
    version = Column(Integer, nullable=False, default=1)
    idempotency_key = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)
    __table_args__ = (UniqueConstraint("provider_account_id", "idempotency_key", name="uq_fin_eligibility_idempotency"), CheckConstraint("status IN ('REQUESTED','PROCESSING','ELIGIBLE','INELIGIBLE','UNKNOWN','FAILED')", name="ck_fin_eligibility_status"), CheckConstraint("version > 0", name="ck_fin_eligibility_version"))


class FinancialPreauthorization(Base):
    __tablename__ = "core_financial_preauthorizations"
    id = Column(String(26), primary_key=True, default=_id)
    member_id = Column(String(26), nullable=False, index=True)
    payer_id = Column(String(26), ForeignKey("core_financial_payers.id", ondelete="RESTRICT"), nullable=False)
    provider_account_id = Column(String(26), nullable=False)
    facility_id = Column(String(26), nullable=False)
    service_id = Column(String(26), nullable=False)
    encounter_id = Column(String(26), nullable=True)
    clinical_indication = Column(Text, nullable=False)
    estimated_amount_minor = Column(BigInteger, nullable=False)
    currency = Column(String(3), nullable=False, default="IQD")
    status = Column(String(24), nullable=False, default="REQUESTED")
    decision_reason = Column(Text)
    version = Column(Integer, nullable=False, default=1)
    idempotency_key = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (UniqueConstraint("provider_account_id", "idempotency_key", name="uq_fin_preauth_idempotency"), CheckConstraint("estimated_amount_minor >= 0", name="ck_fin_preauth_amount"), CheckConstraint("status IN ('REQUESTED','UNDER_REVIEW','APPROVED','PARTIALLY_APPROVED','DENIED','EXPIRED','CANCELLED')", name="ck_fin_preauth_status"))


class FinancialServiceCatalog(Base):
    __tablename__ = "core_financial_services"
    id = Column(String(26), primary_key=True, default=_id)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    code = Column(String(120), nullable=False)
    name = Column(String(240), nullable=False)
    specialty = Column(String(120))
    provider_account_id = Column(String(26), nullable=False, index=True)
    currency = Column(String(3), nullable=False, default="IQD")
    active = Column(Boolean, nullable=False, default=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (UniqueConstraint("facility_id", "code", "version", name="uq_fin_service_version"), CheckConstraint("version > 0", name="ck_fin_service_version"))


class FinancialServicePrice(Base):
    __tablename__ = "core_financial_service_prices"
    id = Column(String(26), primary_key=True, default=_id)
    service_id = Column(String(26), ForeignKey("core_financial_services.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount_minor = Column(BigInteger, nullable=False)
    currency = Column(String(3), nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    source = Column(String(80), nullable=False, default="SYNTHETIC")
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (CheckConstraint("amount_minor >= 0", name="ck_fin_service_price_amount"), CheckConstraint("version > 0", name="ck_fin_service_price_version"), Index("ix_core_financial_service_price_active", "service_id", "valid_from", "valid_to"))


class FinancialBill(Base):
    __tablename__ = "core_financial_bills"
    id = Column(String(26), primary_key=True, default=_id)
    patient_person_id = Column(String(26), nullable=False, index=True)
    provider_account_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    encounter_id = Column(String(26), nullable=True, index=True)
    coverage_id = Column(String(26), ForeignKey("core_financial_coverages.id", ondelete="RESTRICT"), nullable=True, index=True)
    currency = Column(String(3), nullable=False, default="IQD")
    gross_minor = Column(BigInteger, nullable=False)
    discount_minor = Column(BigInteger, nullable=False, default=0)
    covered_minor = Column(BigInteger, nullable=False, default=0)
    copay_minor = Column(BigInteger, nullable=False, default=0)
    deductible_minor = Column(BigInteger, nullable=False, default=0)
    noncovered_minor = Column(BigInteger, nullable=False, default=0)
    net_minor = Column(BigInteger, nullable=False)
    status = Column(String(24), nullable=False, default="DRAFT")
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (CheckConstraint("gross_minor >= 0 AND discount_minor >= 0 AND covered_minor >= 0 AND copay_minor >= 0 AND deductible_minor >= 0 AND noncovered_minor >= 0 AND net_minor >= 0", name="ck_fin_bill_nonnegative"), CheckConstraint("net_minor = gross_minor - discount_minor - covered_minor + deductible_minor + noncovered_minor", name="ck_fin_bill_total"), CheckConstraint("status IN ('DRAFT','ISSUED','PARTIALLY_PAID','PAID','VOID','REFUNDED')", name="ck_fin_bill_status"), CheckConstraint("version > 0", name="ck_fin_bill_version"))


class FinancialBillItem(Base):
    __tablename__ = "core_financial_bill_items"
    id = Column(String(26), primary_key=True, default=_id)
    bill_id = Column(String(26), ForeignKey("core_financial_bills.id", ondelete="RESTRICT"), nullable=False, index=True)
    service_id = Column(String(26), ForeignKey("core_financial_services.id", ondelete="RESTRICT"), nullable=False)
    description = Column(String(240), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price_minor = Column(BigInteger, nullable=False)
    total_minor = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (CheckConstraint("quantity > 0 AND unit_price_minor >= 0 AND total_minor = quantity * unit_price_minor", name="ck_fin_bill_item_math"),)


class FinancialClaim(Base):
    __tablename__ = "core_financial_claims"
    id = Column(String(26), primary_key=True, default=_id)
    bill_id = Column(String(26), ForeignKey("core_financial_bills.id", ondelete="RESTRICT"), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    provider_account_id = Column(String(26), nullable=False, index=True)
    payer_id = Column(String(26), ForeignKey("core_financial_payers.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount_minor = Column(BigInteger, nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(32), nullable=False, default="DRAFT")
    version = Column(Integer, nullable=False, default=1)
    idempotency_key = Column(String(128), nullable=False)
    submitted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (UniqueConstraint("provider_account_id", "idempotency_key", name="uq_fin_claim_idempotency"), CheckConstraint("amount_minor > 0", name="ck_fin_claim_amount"), CheckConstraint("status IN ('DRAFT','SUBMITTED','RECEIVED','UNDER_REVIEW','APPROVED','PARTIALLY_APPROVED','DENIED','PAID','REJECTED','APPEALED')", name="ck_fin_claim_status"))


class FinancialClaimItem(Base):
    __tablename__ = "core_financial_claim_items"
    id = Column(String(26), primary_key=True, default=_id)
    claim_id = Column(String(26), ForeignKey("core_financial_claims.id", ondelete="RESTRICT"), nullable=False, index=True)
    service_id = Column(String(26), ForeignKey("core_financial_services.id", ondelete="RESTRICT"), nullable=False)
    amount_minor = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (CheckConstraint("amount_minor > 0", name="ck_fin_claim_item_amount"),)


class FinancialPayment(Base):
    __tablename__ = "core_financial_payments"
    id = Column(String(26), primary_key=True, default=_id)
    bill_id = Column(String(26), ForeignKey("core_financial_bills.id", ondelete="RESTRICT"), nullable=False, index=True)
    payer_id = Column(String(26), ForeignKey("core_financial_payers.id", ondelete="RESTRICT"), nullable=True)
    payee_organization_id = Column(String(26), nullable=False, index=True)
    amount_minor = Column(BigInteger, nullable=False)
    currency = Column(String(3), nullable=False)
    reference = Column(String(160), nullable=False, unique=True)
    provider = Column(String(80), nullable=False, default="SYNTHETIC")
    status = Column(String(24), nullable=False, default="INITIATED")
    version = Column(Integer, nullable=False, default=1)
    idempotency_key = Column(String(128), nullable=False)
    captured_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (UniqueConstraint("payee_organization_id", "idempotency_key", name="uq_fin_payment_idempotency"), CheckConstraint("amount_minor > 0", name="ck_fin_payment_amount"), CheckConstraint("status IN ('INITIATED','AUTHORIZED','CAPTURED','SETTLED','FAILED','CANCELLED','REFUNDED','PARTIALLY_REFUNDED','PENDING')", name="ck_fin_payment_status"))


class FinancialPaymentEvent(Base):
    __tablename__ = "core_financial_payment_events"
    id = Column(String(26), primary_key=True, default=_id)
    payment_id = Column(String(26), ForeignKey("core_financial_payments.id", ondelete="RESTRICT"), nullable=False, index=True)
    event_id = Column(String(160), nullable=False, unique=True)
    event_type = Column(String(48), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    signature_valid = Column(Boolean, nullable=False, default=False)
    nonce = Column(String(160))
    payload_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (UniqueConstraint("nonce", name="uq_core_financial_payment_event_nonce"),)


class FinancialRefund(Base):
    __tablename__ = "core_financial_refunds"
    id = Column(String(26), primary_key=True, default=_id)
    payment_id = Column(String(26), ForeignKey("core_financial_payments.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount_minor = Column(BigInteger, nullable=False)
    currency = Column(String(3), nullable=False)
    reason = Column(String(500), nullable=False)
    reference = Column(String(160), nullable=False, unique=True)
    status = Column(String(24), nullable=False, default="REQUESTED")
    version = Column(Integer, nullable=False, default=1)
    idempotency_key = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (UniqueConstraint("payment_id", "idempotency_key", name="uq_fin_refund_idempotency"), CheckConstraint("amount_minor > 0", name="ck_fin_refund_amount"), CheckConstraint("status IN ('REQUESTED','COMPLETED','FAILED','CANCELLED')", name="ck_fin_refund_status"))


class FinancialLedgerAccount(Base):
    __tablename__ = "core_financial_ledger_accounts"
    id = Column(String(26), primary_key=True, default=_id)
    organization_id = Column(String(26), nullable=False, index=True)
    code = Column(String(80), nullable=False)
    name = Column(String(200), nullable=False)
    currency = Column(String(3), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_fin_ledger_account_code"),)


class FinancialLedgerEntry(Base):
    __tablename__ = "core_financial_ledger_entries"
    id = Column(String(26), primary_key=True, default=_id)
    transaction_id = Column(String(26), nullable=False, index=True)
    account_id = Column(String(26), ForeignKey("core_financial_ledger_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    debit_minor = Column(BigInteger, nullable=False, default=0)
    credit_minor = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(3), nullable=False)
    reference_type = Column(String(80), nullable=False)
    reference_id = Column(String(26), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (CheckConstraint("debit_minor >= 0 AND credit_minor >= 0 AND ((debit_minor > 0 AND credit_minor = 0) OR (credit_minor > 0 AND debit_minor = 0))", name="ck_fin_ledger_entry_side"), Index("ix_core_financial_ledger_transaction", "transaction_id", "created_at"))


class FinancialSettlement(Base):
    __tablename__ = "core_financial_settlements"
    id = Column(String(26), primary_key=True, default=_id)
    organization_id = Column(String(26), nullable=False, index=True)
    payer_id = Column(String(26), ForeignKey("core_financial_payers.id", ondelete="RESTRICT"), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    amount_minor = Column(BigInteger, nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(24), nullable=False, default="PROPOSED")
    version = Column(Integer, nullable=False, default=1)
    idempotency_key = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (UniqueConstraint("organization_id", "idempotency_key", name="uq_fin_settlement_idempotency"), CheckConstraint("amount_minor >= 0", name="ck_fin_settlement_amount"), CheckConstraint("status IN ('PROPOSED','APPROVED','PAID','CONFLICT','CANCELLED')", name="ck_fin_settlement_status"))


class FinancialReconciliationRecord(Base):
    __tablename__ = "core_financial_reconciliation_records"
    id = Column(String(26), primary_key=True, default=_id)
    source = Column(String(48), nullable=False)
    external_reference = Column(String(160), nullable=False)
    local_reference = Column(String(160))
    status = Column(String(24), nullable=False, default="OPEN")
    mismatch_code = Column(String(80))
    details = Column(JSON, nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (UniqueConstraint("source", "external_reference", name="uq_fin_reconciliation_external"), CheckConstraint("status IN ('OPEN','MATCHED','RESOLVED','ESCALATED')", name="ck_fin_reconciliation_status"))


class FinancialOutboxEvent(Base):
    __tablename__ = "core_financial_outbox_events"
    id = Column(String(26), primary_key=True, default=_id)
    event_key = Column(String(160), nullable=False, unique=True)
    event_type = Column(String(80), nullable=False)
    aggregate_type = Column(String(80), nullable=False)
    aggregate_id = Column(String(26), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(24), nullable=False, default="PENDING")
    attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (CheckConstraint("status IN ('PENDING','SENT','FAILED')", name="ck_fin_outbox_status"),)
