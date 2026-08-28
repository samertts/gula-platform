from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PayerCreateRequest(StrictRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=2, max_length=240)
    payer_type: Literal["GOVERNMENT", "PRIVATE", "EMPLOYER", "TPA", "SELF_PAY", "OTHER"]
    jurisdiction: str = Field(default="IQ", min_length=2, max_length=80)


class CoverageCreateRequest(StrictRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    member_id: str = Field(min_length=1, max_length=80)
    payer_id: str = Field(min_length=1, max_length=40)
    plan_code: str = Field(min_length=1, max_length=120)
    valid_from: datetime
    valid_to: datetime | None = None


class EligibilityCreateRequest(StrictRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    coverage_id: str = Field(min_length=1, max_length=40)
    service_id: str | None = Field(default=None, max_length=40)
    synthetic_outcome: Literal["ELIGIBLE", "INELIGIBLE", "UNKNOWN"] = "UNKNOWN"


class PreauthorizationCreateRequest(StrictRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    member_id: str = Field(min_length=1, max_length=80)
    payer_id: str = Field(min_length=1, max_length=40)
    service_id: str = Field(min_length=1, max_length=40)
    encounter_id: str | None = Field(default=None, max_length=40)
    clinical_indication: str = Field(min_length=3, max_length=1000)
    estimated_amount_minor: int = Field(ge=0, le=10**15)
    currency: Literal["IQD", "USD", "EUR"] = "IQD"


class ServiceCreateRequest(StrictRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    code: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=2, max_length=240)
    specialty: str | None = Field(default=None, max_length=120)
    currency: Literal["IQD", "USD", "EUR"] = "IQD"


class PriceCreateRequest(StrictRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    service_id: str = Field(min_length=1, max_length=40)
    amount_minor: int = Field(ge=0, le=10**15)
    currency: Literal["IQD", "USD", "EUR"]
    valid_from: datetime
    valid_to: datetime | None = None


class BillItemRequest(StrictRequest):
    service_id: str = Field(min_length=1, max_length=40)
    quantity: int = Field(gt=0, le=10000)


class BillCreateRequest(StrictRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    patient_person_id: str = Field(min_length=1, max_length=80)
    encounter_id: str | None = Field(default=None, max_length=40)
    currency: Literal["IQD", "USD", "EUR"]
    items: list[BillItemRequest] = Field(min_length=1, max_length=100)
    coverage_id: str | None = Field(default=None, max_length=40)
    discount_minor: int = Field(default=0, ge=0, le=10**15)


class ClaimCreateRequest(StrictRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    bill_id: str = Field(min_length=1, max_length=40)
    payer_id: str = Field(min_length=1, max_length=40)


class PaymentCreateRequest(StrictRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    bill_id: str = Field(min_length=1, max_length=40)
    amount_minor: int = Field(gt=0, le=10**15)
    currency: Literal["IQD", "USD", "EUR"]
    provider: Literal["SYNTHETIC"] = "SYNTHETIC"
    provider_available: bool = True


class PaymentCaptureRequest(StrictRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    event_id: str = Field(min_length=8, max_length=160)
    nonce: str = Field(min_length=8, max_length=160)
    occurred_at: datetime | None = None


class RefundCreateRequest(StrictRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    payment_id: str = Field(min_length=1, max_length=40)
    amount_minor: int = Field(gt=0, le=10**15)
    currency: Literal["IQD", "USD", "EUR"]
    reason: str = Field(min_length=3, max_length=500)


class WorkflowRequest(StrictRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    target_status: str = Field(min_length=1, max_length=40)
