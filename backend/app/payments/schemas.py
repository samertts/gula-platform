"""Pydantic contracts for the GULA Health Payments foundation."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app._compat import UTC


CURRENCY = "IQD"


def _positive_amount(value: Decimal) -> Decimal:
    if value <= 0:
        raise ValueError("amount must be greater than zero")
    return value


class InvoiceLineCreate(BaseModel):
    description: str = Field(min_length=1, max_length=512)
    service_reference: str | None = Field(default=None, max_length=128)
    quantity: int = Field(default=1, ge=1, le=10_000)
    unit_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)


class InvoiceCreate(BaseModel):
    institution_id: int = Field(gt=0)
    patient_reference: str | None = Field(default=None, max_length=128)
    due_at: datetime | None = None
    lines: list[InvoiceLineCreate] = Field(min_length=1, max_length=100)


    @field_validator("due_at")
    @classmethod
    def due_at_must_be_timezone_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("due_at must include a timezone")
        return value.astimezone(UTC) if value is not None else None


class InvoiceResponse(BaseModel):
    id: str
    institution_id: int
    invoice_number: str
    status: str
    currency: str
    total_amount: Decimal
    paid_amount: Decimal
    refunded_amount: Decimal
    outstanding_amount: Decimal
    created_at: datetime


class PaymentIntentCreate(BaseModel):
    invoice_id: str = Field(min_length=36, max_length=36)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    method: Literal["CASH", "CARD", "WALLET", "QR", "BANK_TRANSFER", "PAYMENT_LINK"]
    expires_at: datetime | None = None


    @field_validator("expires_at")
    @classmethod
    def expiration_must_be_timezone_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("expires_at must include a timezone")
        return value.astimezone(UTC) if value is not None else None


class PaymentIntentResponse(BaseModel):
    id: str
    invoice_id: str
    institution_id: int
    amount: Decimal
    currency: str
    method: str
    status: str
    expires_at: datetime | None
    created_at: datetime


class CashShiftOpen(BaseModel):
    terminal_reference: str = Field(min_length=1, max_length=128)
    opening_float: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=18, decimal_places=2)


class CashShiftClose(BaseModel):
    actual_closing: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    variance_reason: str | None = Field(default=None, max_length=512)


class CashPaymentCapture(BaseModel):
    cash_shift_id: str = Field(min_length=36, max_length=36)
    cashier_reference: str = Field(min_length=1, max_length=128)


class RefundCreate(BaseModel):
    payment_intent_id: str = Field(min_length=36, max_length=36)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    reason: str = Field(min_length=3, max_length=512)
    external_reference: str | None = Field(default=None, max_length=128)


class RefundResponse(BaseModel):
    id: str
    invoice_id: str
    payment_intent_id: str
    amount: Decimal
    currency: str
    status: str
    reason: str
    created_at: datetime


class ReconciliationCaseResponse(BaseModel):
    id: str
    source_type: str
    source_reference: str
    status: str
    expected_amount: Decimal
    observed_amount: Decimal
    discrepancy_reason: str
    created_at: datetime


class PaymentProviderResponse(BaseModel):
    code: str
    display_name: str
    provider_type: str
    environment: str
    status: str
    supports_refund: bool
    supports_reconciliation: bool


class ProviderWebhookVerification(BaseModel):
    """Internal contract reserved for P1 provider adapters.

    It intentionally accepts only normalized fields after an adapter verifies a
    signature. External webhooks must never call the core with this body alone.
    """

    provider_code: str = Field(min_length=1, max_length=64)
    provider_transaction_id: str = Field(min_length=1, max_length=128)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: str = Field(default=CURRENCY, min_length=3, max_length=3)
    merchant_reference: str = Field(min_length=1, max_length=128)
    occurred_at: datetime

    @field_validator("currency")
    @classmethod
    def currency_must_be_iqd(cls, value: str) -> str:
        normalized = value.upper()
        if normalized != CURRENCY:
            raise ValueError("P0 supports IQD only")
        return normalized


class LedgerLineCreate(BaseModel):
    account_code: str = Field(min_length=1, max_length=64)
    debit_amount: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=18, decimal_places=2)
    credit_amount: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=18, decimal_places=2)

    @model_validator(mode="after")
    def exactly_one_side_is_positive(self) -> "LedgerLineCreate":
        debit_positive = self.debit_amount > 0
        credit_positive = self.credit_amount > 0
        if debit_positive == credit_positive:
            raise ValueError("exactly one of debit_amount or credit_amount must be positive")
        return self
