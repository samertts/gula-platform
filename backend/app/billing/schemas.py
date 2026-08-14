from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineCreate(BaseModel):
    service_code: str = Field(min_length=1, max_length=128)
    description: str = Field(min_length=1, max_length=512)
    quantity: int = Field(default=1, ge=1, le=10_000)
    unit_amount: Decimal = Field(ge=0, decimal_places=2, max_digits=14)


class InvoiceCreate(BaseModel):
    patient_id: int = Field(gt=0)
    encounter_ref: str = Field(min_length=1, max_length=128)
    lines: list[InvoiceLineCreate] = Field(min_length=1, max_length=100)
    covered_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2, max_digits=14)
    due_at: date | None = None


class InvoiceLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    line_number: int
    service_code: str
    description: str
    quantity: int
    unit_amount: Decimal
    line_amount: Decimal


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int
    patient_id: int
    amount: Decimal
    currency: str
    method: str
    reference: str
    kind: str
    created_at: datetime


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    encounter_ref: str
    invoice_number: str
    status: str
    currency: str
    gross_amount: Decimal
    covered_amount: Decimal
    patient_due: Decimal
    claim_reference: str | None
    due_at: date | None
    issued_at: date | None
    created_at: datetime
    lines: list[InvoiceLineResponse]
    payments: list[PaymentResponse]


class CoverageCreate(BaseModel):
    patient_id: int = Field(gt=0)
    payer: str = Field(min_length=1, max_length=255)
    plan: str = Field(min_length=1, max_length=255)
    member_id: str = Field(min_length=1, max_length=128)
    expires_on: date


class CoverageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    payer: str
    plan: str
    member_id: str
    expires_on: date
    state: str
    verification: str
    last_checked_at: datetime | None
    active: bool


class ClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    order_id: int | None
    status: str
    total_amount: Decimal | None
    currency: str
    external_ref: str | None
    submitted_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_id: str
    action: str
    actor_user_id: int | None
    request_id: str | None
    safe_metadata: dict
    created_at: datetime


class BillingSummaryResponse(BaseModel):
    open_invoices: int
    outstanding: Decimal
    rejected_claims: int
    pending_verification: int
    synthetic: bool
    external_integrations: bool
    as_of: date


class AlertResponse(BaseModel):
    type: str
    severity: str
    reference: str
    message: str
