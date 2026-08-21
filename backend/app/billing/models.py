"""Server-backed billing and insurance projection models.

These models are intentionally limited to synthetic/demo-safe workflows. They do
not store payment credentials, card data, insurer secrets, or real EDI payloads.
Every tenant-facing query must filter by ``lab_id``.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import relationship

from app._compat import UTC

from ..database import Base

MONEY = Numeric(14, 2)


class BillingInvoice(Base):
    __tablename__ = "billing_invoices"
    __table_args__ = (
        UniqueConstraint("lab_id", "invoice_number", name="uq_billing_invoice_lab_number"),
        UniqueConstraint("lab_id", "idempotency_key", name="uq_billing_invoice_lab_idempotency"),
        CheckConstraint("gross_amount >= 0", name="ck_billing_invoice_gross_non_negative"),
        CheckConstraint("covered_amount >= 0", name="ck_billing_invoice_covered_non_negative"),
        CheckConstraint("patient_due >= 0", name="ck_billing_invoice_due_non_negative"),
        Index("ix_billing_invoices_lab_status", "lab_id", "status"),
        Index("ix_billing_invoices_lab_patient", "lab_id", "patient_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    encounter_ref = Column(String(128), nullable=False)
    invoice_number = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="draft", index=True)
    currency = Column(String(3), nullable=False, default="IQD")
    gross_amount = Column(MONEY, nullable=False, default=Decimal("0.00"))
    covered_amount = Column(MONEY, nullable=False, default=Decimal("0.00"))
    patient_due = Column(MONEY, nullable=False, default=Decimal("0.00"))
    claim_reference = Column(String(128), nullable=True, index=True)
    idempotency_key = Column(String(128), nullable=True)
    due_at = Column(Date, nullable=True)
    issued_at = Column(Date, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    lines = relationship("BillingInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("BillingPayment", back_populates="invoice", cascade="all, delete-orphan")


class BillingInvoiceLine(Base):
    __tablename__ = "billing_invoice_lines"
    __table_args__ = (
        UniqueConstraint("invoice_id", "line_number", name="uq_billing_invoice_line_number"),
        CheckConstraint("quantity > 0", name="ck_billing_invoice_line_quantity_positive"),
        CheckConstraint("unit_amount >= 0", name="ck_billing_invoice_line_unit_non_negative"),
        CheckConstraint("line_amount >= 0", name="ck_billing_invoice_line_amount_non_negative"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("billing_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    service_code = Column(String(128), nullable=False)
    description = Column(String(512), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_amount = Column(MONEY, nullable=False)
    line_amount = Column(MONEY, nullable=False)

    invoice = relationship("BillingInvoice", back_populates="lines")


class InsuranceCoverage(Base):
    __tablename__ = "insurance_coverages"
    __table_args__ = (
        UniqueConstraint("lab_id", "member_id", name="uq_insurance_coverage_lab_member"),
        Index("ix_insurance_coverages_lab_patient", "lab_id", "patient_id"),
        Index("ix_insurance_coverages_lab_state", "lab_id", "state"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    payer = Column(String(255), nullable=False)
    plan = Column(String(255), nullable=False)
    member_id = Column(String(128), nullable=False)
    expires_on = Column(Date, nullable=False)
    state = Column(String(32), nullable=False, default="needs_verification")
    verification = Column(String(512), nullable=False, default="لم يُتحقق")
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class BillingPayment(Base):
    __tablename__ = "billing_payments"
    __table_args__ = (
        UniqueConstraint("lab_id", "reference", name="uq_billing_payment_lab_reference"),
        CheckConstraint("amount > 0", name="ck_billing_payment_amount_positive"),
        Index("ix_billing_payments_lab_created", "lab_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("billing_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    amount = Column(MONEY, nullable=False)
    currency = Column(String(3), nullable=False, default="IQD")
    method = Column(String(64), nullable=False, default="synthetic_settlement")
    reference = Column(String(128), nullable=False)
    kind = Column(String(32), nullable=False, default="patient_payment")
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True)

    invoice = relationship("BillingInvoice", back_populates="payments")


class BillingAuditEvent(Base):
    __tablename__ = "billing_audit_events"
    __table_args__ = (
        Index("ix_billing_audit_lab_created", "lab_id", "created_at"),
        Index("ix_billing_audit_entity", "entity_type", "entity_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(128), nullable=False)
    action = Column(String(64), nullable=False)
    actor_user_id = Column(Integer, nullable=True)
    request_id = Column(String(128), nullable=True)
    safe_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True)


def _reject_audit_mutation(_mapper, _connection, _target) -> None:
    raise ValueError("Billing audit events are immutable")


event.listen(BillingAuditEvent, "before_update", _reject_audit_mutation)
event.listen(BillingAuditEvent, "before_delete", _reject_audit_mutation)
