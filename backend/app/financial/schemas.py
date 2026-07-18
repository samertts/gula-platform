"""Financial Engine — Pydantic request/response schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator


class InvoiceCreate(BaseModel):
    lab_id: int
    subscription_id: int | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    amount: Decimal
    currency: str = "IQD"
    due_date: date | None = None
    notes: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class InvoiceResponse(BaseModel):
    id: int
    lab_id: int
    invoice_number: str
    status: str
    amount: Decimal
    currency: str
    paid_amount: Decimal = Decimal("0")
    due_date: date | None = None
    issued_at: datetime | None = None
    paid_at: datetime | None = None
    notes: str | None = None


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: Decimal
    currency: str = "IQD"
    method: str = "bank_transfer"
    reference: str | None = None
    notes: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v

    @field_validator("method")
    @classmethod
    def method_must_be_valid(cls, v: str) -> str:
        allowed = {"bank_transfer", "cash", "card", "check", "online", "wallet"}
        if v not in allowed:
            raise ValueError(f"method must be one of {allowed}")
        return v


class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    amount: Decimal
    currency: str
    method: str
    status: str
    reference: str | None = None
    processed_at: datetime | None = None
    notes: str | None = None


class ReceivableResponse(BaseModel):
    id: int
    lab_id: int
    invoice_id: int | None = None
    amount: Decimal
    currency: str
    status: str
    due_date: date | None = None
    aging_days: int = 0


class PayableResponse(BaseModel):
    id: int
    provider_id: int
    amount: Decimal
    currency: str
    status: str
    due_date: date | None = None


class PricingRuleCreate(BaseModel):
    name: str
    test_type: str | None = None
    base_price: Decimal
    currency: str = "IQD"
    quality_discount_pct: float = 0.0
    volume_discount_pct: float = 0.0
    active: bool = True


class PricingRuleResponse(BaseModel):
    id: int
    name: str
    test_type: str | None = None
    base_price: Decimal
    currency: str
    active: bool


class InvoiceFilterParams(BaseModel):
    lab_id: int | None = None
    status: str | None = None
    date_from: date | None = None
    date_to: date | None = None


class FinancialReportParams(BaseModel):
    lab_id: int
    date_from: date
    date_to: date
    group_by: str = "month"


class FinancialReportResponse(BaseModel):
    lab_id: int
    period: dict[str, date]
    total_invoiced: Decimal
    total_collected: Decimal
    total_outstanding: Decimal
    invoice_count: int
    payment_count: int
    group_by: str
    breakdown: list[dict[str, Any]]
