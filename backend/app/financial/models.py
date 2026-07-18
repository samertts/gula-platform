"""Financial Engine — ORM models for Phase B (invoices, payments, pricing)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import declarative_base

FinBase = declarative_base()


class FinProvider(FinBase):
    __tablename__ = "fin_providers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    provider_type = Column(String(50), nullable=True)
    status = Column(String(20), nullable=True, default="active")
    contact_email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    quality_score = Column(Float, nullable=True, default=0.0)
    accredited = Column(Boolean, nullable=True, default=False)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)


class FinSubscription(FinBase):
    __tablename__ = "fin_subscriptions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey("fin_providers.id"), nullable=False)
    plan = Column(String(50), nullable=True, default="basic")
    status = Column(String(20), nullable=True, default="active")
    billing_cycle = Column(String(20), nullable=True, default="monthly")
    amount = Column(Numeric(12, 2), nullable=True, default=0)
    currency = Column(String(3), nullable=True, default="IQD")
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, nullable=True, default=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)


class FinTransaction(FinBase):
    __tablename__ = "fin_transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey("fin_providers.id"), nullable=True)
    subscription_id = Column(Integer, ForeignKey("fin_subscriptions.id"), nullable=True)
    transaction_type = Column(String(50), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=True, default="IQD")
    status = Column(String(20), nullable=True, default="pending")
    description = Column(Text, nullable=True)
    reference_id = Column(String(255), nullable=True)
    reference_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    settled_at = Column(DateTime, nullable=True)


class FinInvoice(FinBase):
    __tablename__ = "fin_invoices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)
    invoice_number = Column(String(50), nullable=False, unique=True)
    subscription_id = Column(Integer, ForeignKey("fin_subscriptions.id"), nullable=True)
    status = Column(String(20), nullable=True, default="issued")
    amount = Column(Numeric(12, 2), nullable=False, default=0)
    paid_amount = Column(Numeric(12, 2), nullable=True, default=0)
    currency = Column(String(3), nullable=True, default="IQD")
    due_date = Column(Date, nullable=True)
    issued_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class FinInvoiceItem(FinBase):
    __tablename__ = "fin_invoice_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("fin_invoices.id"), nullable=False)
    line_number = Column(Integer, nullable=True)
    description = Column(String(500), nullable=True)
    quantity = Column(Integer, nullable=True, default=1)
    unit_price = Column(Numeric(12, 2), nullable=True, default=0)
    total_price = Column(Numeric(12, 2), nullable=True, default=0)


class FinPayment(FinBase):
    __tablename__ = "fin_payments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("fin_invoices.id"), nullable=False)
    lab_id = Column(Integer, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=True, default="IQD")
    method = Column(String(50), nullable=True, default="bank_transfer")
    status = Column(String(20), nullable=True, default="completed")
    reference = Column(String(255), nullable=True)
    processed_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    notes = Column(Text, nullable=True)


class FinReceivable(FinBase):
    __tablename__ = "fin_receivables"
    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("fin_invoices.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=True, default="IQD")
    status = Column(String(20), nullable=True, default="pending")
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)


class FinPayable(FinBase):
    __tablename__ = "fin_payables"
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey("fin_providers.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=True, default="IQD")
    status = Column(String(20), nullable=True, default="pending")
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)


class FinPricingRule(FinBase):
    __tablename__ = "fin_pricing_rules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    test_type = Column(String(100), nullable=True, index=True)
    base_price = Column(Numeric(12, 2), nullable=False, default=10000)
    currency = Column(String(3), nullable=True, default="IQD")
    quality_discount_pct = Column(Float, nullable=True, default=0.0)
    volume_discount_pct = Column(Float, nullable=True, default=0.0)
    active = Column(Boolean, nullable=True, default=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
