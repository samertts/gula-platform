"""Persistent models for the GULA Health Payments foundation.

The module deliberately stores no card PAN, CVV, wallet secret, or provider
credential.  It records healthcare billing, payment lifecycle, accounting
entries, cash shifts, reconciliation, and audit events only.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    event,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)

from app._compat import UTC
from app.financial.models import FinBase


MONEY = Numeric(18, 2)
FX_AMOUNT = Numeric(24, 6)


def _uuid() -> str:
    return str(uuid4())


class PaymentInvoice(FinBase):
    __tablename__ = "pay_invoices"
    __table_args__ = (
        UniqueConstraint("institution_id", "invoice_number", name="uq_pay_invoice_number"),
        CheckConstraint("total_amount >= 0", name="ck_pay_invoice_total_non_negative"),
        CheckConstraint("paid_amount >= 0", name="ck_pay_invoice_paid_non_negative"),
        CheckConstraint("refunded_amount >= 0", name="ck_pay_invoice_refunded_non_negative"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    institution_id = Column(Integer, nullable=False, index=True)
    patient_reference = Column(String(128), nullable=True, index=True)
    invoice_number = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="DRAFT", index=True)
    currency = Column(String(3), nullable=False, default="IQD")
    total_amount = Column(MONEY, nullable=False, default=Decimal("0.00"))
    paid_amount = Column(MONEY, nullable=False, default=Decimal("0.00"))
    refunded_amount = Column(MONEY, nullable=False, default=Decimal("0.00"))
    issued_at = Column(DateTime(timezone=True), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    voided_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class PaymentInvoiceLine(FinBase):
    __tablename__ = "pay_invoice_lines"
    __table_args__ = (
        UniqueConstraint("invoice_id", "line_number", name="uq_pay_invoice_line_number"),
        CheckConstraint("quantity > 0", name="ck_pay_invoice_line_quantity_positive"),
        CheckConstraint("unit_amount >= 0", name="ck_pay_invoice_line_unit_non_negative"),
        CheckConstraint("line_amount >= 0", name="ck_pay_invoice_line_total_non_negative"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    invoice_id = Column(String(36), ForeignKey("pay_invoices.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    service_reference = Column(String(128), nullable=True)
    description = Column(String(512), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_amount = Column(MONEY, nullable=False)
    line_amount = Column(MONEY, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class PaymentIntent(FinBase):
    __tablename__ = "pay_payment_intents"
    __table_args__ = (
        UniqueConstraint("institution_id", "idempotency_key", name="uq_pay_intent_idempotency"),
        CheckConstraint("amount > 0", name="ck_pay_intent_amount_positive"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    institution_id = Column(Integer, nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("pay_invoices.id"), nullable=False, index=True)
    payment_entity_id = Column(String(36), ForeignKey("pay_payment_entities.id"), nullable=True, index=True)
    idempotency_key = Column(String(128), nullable=False)
    amount = Column(MONEY, nullable=False)
    currency = Column(String(3), nullable=False, default="IQD")
    method = Column(String(32), nullable=False, default="CASH")
    status = Column(String(32), nullable=False, default="CREATED", index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    provider_reference = Column(String(128), nullable=True, unique=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class PaymentAttempt(FinBase):
    __tablename__ = "pay_payment_attempts"
    __table_args__ = (
        UniqueConstraint("provider_code", "provider_transaction_id", name="uq_pay_provider_transaction"),
        CheckConstraint("amount > 0", name="ck_pay_attempt_amount_positive"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    intent_id = Column(String(36), ForeignKey("pay_payment_intents.id"), nullable=False, index=True)
    cash_shift_id = Column(String(36), ForeignKey("pay_cash_shifts.id"), nullable=True, index=True)
    provider_code = Column(String(64), nullable=False, default="cashier")
    provider_transaction_id = Column(String(128), nullable=True)
    amount = Column(MONEY, nullable=False)
    currency = Column(String(3), nullable=False, default="IQD")
    status = Column(String(32), nullable=False, default="PENDING", index=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    failure_code = Column(String(64), nullable=True)
    failure_reason = Column(String(512), nullable=True)
    safe_provider_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class PaymentProvider(FinBase):
    __tablename__ = "pay_providers"

    id = Column(String(36), primary_key=True, default=_uuid)
    code = Column(String(64), nullable=False, unique=True)
    display_name = Column(String(128), nullable=False)
    provider_type = Column(String(32), nullable=False)  # bank, psp, wallet, qr, cash
    environment = Column(String(16), nullable=False, default="sandbox")
    created_by = Column(Integer, nullable=True)
    payment_entity_id = Column(String(36), ForeignKey("pay_payment_entities.id"), nullable=True, index=True)
    rail_code = Column(String(64), ForeignKey("pay_payment_rails.code"), nullable=True, index=True)
    jurisdiction_code = Column(String(16), nullable=True)
    live_approved = Column(Boolean, nullable=False, default=False)
    status = Column(String(32), nullable=False, default="PENDING_REVIEW")
    supports_refund = Column(Boolean, nullable=False, default=False)
    supports_reconciliation = Column(Boolean, nullable=False, default=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class LedgerAccount(FinBase):
    __tablename__ = "pay_ledger_accounts"
    __table_args__ = (UniqueConstraint("institution_id", "code", name="uq_pay_ledger_account_code"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    institution_id = Column(Integer, nullable=False, index=True)
    code = Column(String(64), nullable=False)
    name = Column(String(128), nullable=False)
    account_type = Column(String(32), nullable=False)  # asset, liability, revenue, expense, equity
    currency = Column(String(3), nullable=False, default="IQD")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class LedgerEntry(FinBase):
    __tablename__ = "pay_ledger_entries"

    id = Column(String(36), primary_key=True, default=_uuid)
    institution_id = Column(Integer, nullable=False, index=True)
    reference_type = Column(String(64), nullable=False)
    reference_id = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="POSTED")
    reversal_of_entry_id = Column(String(36), ForeignKey("pay_ledger_entries.id"), nullable=True)
    description = Column(String(512), nullable=False)
    posted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    posted_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class LedgerLine(FinBase):
    __tablename__ = "pay_ledger_lines"
    __table_args__ = (
        CheckConstraint("debit_amount >= 0", name="ck_pay_ledger_line_debit_non_negative"),
        CheckConstraint("credit_amount >= 0", name="ck_pay_ledger_line_credit_non_negative"),
        CheckConstraint(
            "(debit_amount > 0 AND credit_amount = 0) OR "
            "(credit_amount > 0 AND debit_amount = 0)",
            name="ck_pay_ledger_line_one_sided",
        ),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    entry_id = Column(String(36), ForeignKey("pay_ledger_entries.id"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("pay_ledger_accounts.id"), nullable=False, index=True)
    debit_amount = Column(MONEY, nullable=False, default=Decimal("0.00"))
    credit_amount = Column(MONEY, nullable=False, default=Decimal("0.00"))
    currency = Column(String(3), nullable=False, default="IQD")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class CashShift(FinBase):
    __tablename__ = "pay_cash_shifts"
    __table_args__ = (CheckConstraint("opening_float >= 0", name="ck_pay_cash_shift_opening_non_negative"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    institution_id = Column(Integer, nullable=False, index=True)
    cashier_user_id = Column(Integer, nullable=False, index=True)
    terminal_reference = Column(String(128), nullable=False)
    currency = Column(String(3), nullable=False, default="IQD")
    status = Column(String(32), nullable=False, default="OPEN", index=True)
    opening_float = Column(MONEY, nullable=False, default=Decimal("0.00"))
    expected_closing = Column(MONEY, nullable=True)
    actual_closing = Column(MONEY, nullable=True)
    variance_amount = Column(MONEY, nullable=True)
    variance_reason = Column(String(512), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    closed_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Integer, nullable=True)


class PaymentRefund(FinBase):
    __tablename__ = "pay_refunds"
    __table_args__ = (CheckConstraint("amount > 0", name="ck_pay_refund_amount_positive"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    institution_id = Column(Integer, nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("pay_invoices.id"), nullable=False, index=True)
    payment_intent_id = Column(String(36), ForeignKey("pay_payment_intents.id"), nullable=False, index=True)
    cash_shift_id = Column(String(36), ForeignKey("pay_cash_shifts.id"), nullable=True, index=True)
    amount = Column(MONEY, nullable=False)
    currency = Column(String(3), nullable=False, default="IQD")
    reason = Column(String(512), nullable=False)
    external_reference = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False, default="REQUESTED", index=True)
    requested_by = Column(Integer, nullable=False)
    approved_by = Column(Integer, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ReconciliationCase(FinBase):
    __tablename__ = "pay_reconciliation_cases"

    id = Column(String(36), primary_key=True, default=_uuid)
    institution_id = Column(Integer, nullable=False, index=True)
    source_type = Column(String(32), nullable=False)  # cash_shift, provider, bank
    source_reference = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="PENDING", index=True)
    expected_amount = Column(MONEY, nullable=False)
    observed_amount = Column(MONEY, nullable=False)
    currency = Column(String(3), nullable=False, default="IQD")
    discrepancy_reason = Column(String(512), nullable=False)
    resolved_by = Column(Integer, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class PaymentAuditEvent(FinBase):
    __tablename__ = "pay_audit_events"
    __table_args__ = (Index("ix_pay_audit_entity", "entity_type", "entity_id"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    institution_id = Column(Integer, nullable=False, index=True)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)
    actor_user_id = Column(Integer, nullable=True)
    request_id = Column(String(128), nullable=True)
    safe_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class FinancialControlRequest(FinBase):
    """Maker-checker request for high-impact financial configuration actions."""

    __tablename__ = "pay_financial_control_requests"
    __table_args__ = (
        UniqueConstraint("institution_id", "idempotency_key", name="uq_pay_control_institution_idempotency"),
        CheckConstraint(
            "status IN ('REQUESTED', 'APPROVED', 'REJECTED', 'APPLIED', 'EXPIRED')",
            name="ck_pay_control_status",
        ),
        Index("ix_pay_control_institution_status", "institution_id", "status"),
        Index("ix_pay_control_resource", "resource_type", "resource_id"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    institution_id = Column(Integer, nullable=False, index=True)
    control_type = Column(String(64), nullable=False)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=False)
    requested_action = Column(String(64), nullable=False)
    status = Column(String(24), nullable=False, default="REQUESTED", index=True)
    idempotency_key = Column(String(128), nullable=False)
    reason = Column(String(1024), nullable=False)
    rejection_reason = Column(String(1024), nullable=True)
    requested_by = Column(Integer, nullable=False, index=True)
    approved_by = Column(Integer, nullable=True)
    applied_by = Column(Integer, nullable=True)
    request_id = Column(String(128), nullable=True, index=True)
    evidence_hash = Column(String(128), nullable=True)
    safe_metadata = Column(JSON, nullable=True)
    requested_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    approved_at = Column(DateTime(timezone=True), nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


# Ledger and audit history are append-only. Financial corrections must be
# represented by a separately linked reversal/refund record, never an update.
def _reject_financial_history_mutation(_mapper, _connection, _target) -> None:
    raise ValueError("Financial ledger and payment audit records are immutable")


for _immutable_model in (LedgerEntry, LedgerLine, PaymentAuditEvent):
    event.listen(_immutable_model, "before_update", _reject_financial_history_mutation)
    event.listen(_immutable_model, "before_delete", _reject_financial_history_mutation)


class CurrencyDefinition(FinBase):
    """A centrally governed currency registry; not a wallet balance table."""

    __tablename__ = "pay_currency_definitions"

    code = Column(String(3), primary_key=True)
    display_name = Column(String(96), nullable=False)
    minor_unit = Column(Integer, nullable=False, default=2)
    rounding_mode = Column(String(32), nullable=False, default="HALF_UP")
    enabled = Column(Boolean, nullable=False, default=True)
    fx_quote_enabled = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class FxRateSnapshot(FinBase):
    """Immutable source-rate evidence used by time-limited quotes."""

    __tablename__ = "pay_fx_rate_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "source_code", "source_reference", "base_currency", "quote_currency", "rate_version",
            name="uq_pay_fx_snapshot_source_version",
        ),
        CheckConstraint("reference_rate > 0", name="ck_pay_fx_rate_positive"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    source_code = Column(String(64), nullable=False)  # e.g. CBI_PUBLISHED_RATE
    source_reference = Column(String(512), nullable=False)
    source_digest = Column(String(128), nullable=True)
    rate_version = Column(String(96), nullable=False)
    base_currency = Column(String(3), ForeignKey("pay_currency_definitions.code"), nullable=False)
    quote_currency = Column(String(3), ForeignKey("pay_currency_definitions.code"), nullable=False)
    reference_rate = Column(Numeric(24, 10), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False)
    imported_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    verification_status = Column(String(32), nullable=False, default="PENDING_REVIEW")
    created_by = Column(Integer, nullable=True)
    verified_by = Column(Integer, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class FxFeePolicy(FinBase):
    """Versioned, data-backed policy for transparent administrative FX fees."""

    __tablename__ = "pay_fx_fee_policies"
    __table_args__ = (
        UniqueConstraint("policy_version", name="uq_pay_fx_fee_policy_version"),
        CheckConstraint("fee_bps >= 0 AND fee_bps <= 10000", name="ck_pay_fx_fee_bps_range"),
        CheckConstraint("minimum_fee >= 0", name="ck_pay_fx_fee_minimum_non_negative"),
        CheckConstraint("maximum_fee IS NULL OR maximum_fee >= minimum_fee", name="ck_pay_fx_fee_maximum"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    institution_id = Column(Integer, nullable=True, index=True)
    policy_version = Column(String(96), nullable=False)
    base_currency = Column(String(3), nullable=True)
    quote_currency = Column(String(3), nullable=True)
    service_reference = Column(String(128), nullable=True)
    provider_code = Column(String(64), nullable=True)
    fee_bps = Column(Integer, nullable=False, default=200)
    minimum_fee = Column(FX_AMOUNT, nullable=False, default=Decimal("0.00"))
    maximum_fee = Column(FX_AMOUNT, nullable=True)
    currency = Column(String(3), nullable=False, default="IQD")
    effective_from = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    effective_until = Column(DateTime(timezone=True), nullable=True)
    active = Column(Boolean, nullable=False, default=False)
    created_by = Column(Integer, nullable=True)
    approved_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class FxQuote(FinBase):
    """A transparent, time-limited reference quote; it does not execute FX."""

    __tablename__ = "pay_fx_quotes"
    __table_args__ = (
        CheckConstraint("base_amount > 0", name="ck_pay_fx_quote_base_positive"),
        CheckConstraint("reference_rate > 0", name="ck_pay_fx_quote_rate_positive"),
        CheckConstraint("base_converted_amount >= 0", name="ck_pay_fx_quote_converted_non_negative"),
        CheckConstraint("administrative_fee_amount >= 0", name="ck_pay_fx_quote_fee_non_negative"),
        CheckConstraint("provider_fee_amount >= 0", name="ck_pay_fx_quote_provider_fee_non_negative"),
        CheckConstraint("total_quote_amount >= 0", name="ck_pay_fx_quote_total_non_negative"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    institution_id = Column(Integer, nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("pay_invoices.id"), nullable=True, index=True)
    rate_snapshot_id = Column(String(36), ForeignKey("pay_fx_rate_snapshots.id"), nullable=False, index=True)
    fee_policy_id = Column(String(36), ForeignKey("pay_fx_fee_policies.id"), nullable=True, index=True)
    base_currency = Column(String(3), nullable=False)
    quote_currency = Column(String(3), nullable=False)
    base_amount = Column(FX_AMOUNT, nullable=False)
    reference_rate = Column(Numeric(24, 10), nullable=False)
    base_converted_amount = Column(FX_AMOUNT, nullable=False)
    administrative_fee_amount = Column(FX_AMOUNT, nullable=False, default=Decimal("0.00"))
    provider_fee_amount = Column(FX_AMOUNT, nullable=False, default=Decimal("0.00"))
    total_quote_amount = Column(FX_AMOUNT, nullable=False)
    status = Column(String(32), nullable=False, default="CREATED", index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class PaymentRiskAssessment(FinBase):
    """Non-blocking risk signal. Human or provider policy decides any action."""

    __tablename__ = "pay_risk_assessments"
    __table_args__ = (CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="ck_pay_risk_score_range"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    institution_id = Column(Integer, nullable=False, index=True)
    payment_intent_id = Column(String(36), ForeignKey("pay_payment_intents.id"), nullable=True, index=True)
    fx_quote_id = Column(String(36), ForeignKey("pay_fx_quotes.id"), nullable=True, index=True)
    risk_score = Column(Numeric(5, 2), nullable=False)
    risk_level = Column(String(16), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    recommended_action = Column(String(32), nullable=False, default="REVIEW")
    reason_codes = Column(JSON, nullable=False, default=list)
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_outcome = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class PaymentEntity(FinBase):
    """A legal and accounting boundary; never a shared wallet or balance."""

    __tablename__ = "pay_payment_entities"

    id = Column(String(36), primary_key=True, default=_uuid)
    code = Column(String(64), nullable=False, unique=True)
    legal_name = Column(String(256), nullable=False)
    jurisdiction_code = Column(String(16), nullable=False)
    entity_type = Column(String(32), nullable=False)  # DOMESTIC, INTERNATIONAL, SANDBOX
    ledger_namespace = Column(String(96), nullable=False, unique=True)
    status = Column(String(32), nullable=False, default="PENDING_REVIEW")
    created_by = Column(Integer, nullable=True)
    live_operations_approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class PaymentRail(FinBase):
    """A payment route owned by exactly one legal entity."""

    __tablename__ = "pay_payment_rails"
    __table_args__ = (
        UniqueConstraint("payment_entity_id", "code", name="uq_pay_rail_entity_code"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    payment_entity_id = Column(String(36), ForeignKey("pay_payment_entities.id"), nullable=False, index=True)
    code = Column(String(64), nullable=False, unique=True)
    rail_type = Column(String(32), nullable=False)  # IRAQ_DOMESTIC, INTERNATIONAL, CASH, SANDBOX
    jurisdiction_code = Column(String(16), nullable=False)
    supported_currencies = Column(JSON, nullable=False, default=list)
    status = Column(String(32), nullable=False, default="DISABLED")
    created_by = Column(Integer, nullable=True)
    kill_switch_enabled = Column(Boolean, nullable=False, default=False)
    live_operations_approved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class PaymentRoutingRule(FinBase):
    """Versioned routing policy. Rules are advisory until a live adapter is approved."""

    __tablename__ = "pay_payment_routing_rules"
    __table_args__ = (
        UniqueConstraint("rule_version", name="uq_pay_routing_rule_version"),
        CheckConstraint("priority >= 0", name="ck_pay_routing_priority_non_negative"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    payment_entity_id = Column(String(36), ForeignKey("pay_payment_entities.id"), nullable=False, index=True)
    rail_code = Column(String(64), ForeignKey("pay_payment_rails.code"), nullable=False, index=True)
    provider_code = Column(String(64), ForeignKey("pay_providers.code"), nullable=False, index=True)
    rule_version = Column(String(96), nullable=False)
    priority = Column(Integer, nullable=False, default=100)
    minimum_amount = Column(FX_AMOUNT, nullable=True)
    maximum_amount = Column(FX_AMOUNT, nullable=True)
    currency_code = Column(String(3), nullable=True)
    required_risk_level = Column(String(16), nullable=True)
    service_reference = Column(String(128), nullable=True)
    estimated_fee_bps = Column(Integer, nullable=False, default=0)
    success_rate_bps = Column(Integer, nullable=False, default=0)
    latency_ms = Column(Integer, nullable=True)
    active = Column(Boolean, nullable=False, default=False)
    created_by = Column(Integer, nullable=True)
    approved_by = Column(Integer, nullable=True)
    effective_from = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    effective_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class PaymentRoutingDecision(FinBase):
    """Append-only explanation of a routing recommendation; it does not initiate payment."""

    __tablename__ = "pay_payment_routing_decisions"

    id = Column(String(36), primary_key=True, default=_uuid)
    payment_intent_id = Column(String(36), ForeignKey("pay_payment_intents.id"), nullable=False, index=True)
    payment_entity_id = Column(String(36), ForeignKey("pay_payment_entities.id"), nullable=False, index=True)
    rail_code = Column(String(64), nullable=True)
    provider_code = Column(String(64), nullable=True)
    correlation_id = Column(String(128), nullable=False, index=True)
    decision = Column(String(32), nullable=False)  # ADVISORY_SELECT, MANUAL_REVIEW, NO_ELIGIBLE_ROUTE
    score = Column(Numeric(10, 4), nullable=True)
    reason_codes = Column(JSON, nullable=False, default=list)
    evaluated_candidates = Column(JSON, nullable=False, default=list)
    rule_version = Column(String(96), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


for _immutable_model in (PaymentRoutingDecision,):
    event.listen(_immutable_model, "before_update", _reject_financial_history_mutation)
    event.listen(_immutable_model, "before_delete", _reject_financial_history_mutation)
