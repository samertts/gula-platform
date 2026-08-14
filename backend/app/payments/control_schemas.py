from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app._compat import UTC


ControlStatus = Literal["REQUESTED", "APPROVED", "REJECTED", "APPLIED", "EXPIRED"]


class FinancialControlRequestCreate(BaseModel):
    institution_id: int = Field(gt=0)
    control_type: str = Field(min_length=3, max_length=64)
    resource_type: str = Field(min_length=1, max_length=64)
    resource_id: str = Field(min_length=1, max_length=128)
    requested_action: str = Field(min_length=1, max_length=64)
    reason: str = Field(min_length=3, max_length=1024)
    expires_at: datetime | None = None

    @field_validator("expires_at")
    @classmethod
    def expiry_must_be_timezone_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("expires_at must include a timezone")
        return value.astimezone(UTC) if value is not None else None


class FinancialControlReject(BaseModel):
    rejection_reason: str = Field(min_length=3, max_length=1024)


class FinancialControlResponse(BaseModel):
    id: str
    institution_id: int
    control_type: str
    resource_type: str
    resource_id: str
    requested_action: str
    status: ControlStatus
    idempotency_key: str
    reason: str
    rejection_reason: str | None
    requested_by: int
    approved_by: int | None
    applied_by: int | None
    request_id: str | None
    evidence_hash: str | None
    external_operation: bool
    requested_at: datetime
    approved_at: datetime | None
    applied_at: datetime | None
    expires_at: datetime | None


class FinancialControlListResponse(BaseModel):
    items: list[FinancialControlResponse]
    count: int


class FinancialControlSummaryResponse(BaseModel):
    institution_id: int
    as_of: datetime
    currency: str
    billed_amount: Decimal
    collected_amount: Decimal
    outstanding_amount: Decimal
    refunded_amount: Decimal
    invoice_count: int
    control_requests: dict[str, int]
    open_reconciliation_cases: int
    cash_variance_cases: int
    live_operation_enabled: bool
    external_provider_calls: int
    data_basis: str
    limitations: list[str]
