from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MedicationCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    code: str = Field(min_length=1, max_length=120)
    code_system: str = Field(default="SYNTHETIC", min_length=1, max_length=80)
    generic_name: str = Field(min_length=1, max_length=300)
    brand_name: str | None = Field(default=None, max_length=300)
    strength_value: str | None = Field(default=None, max_length=80)
    strength_unit: str | None = Field(default=None, max_length=40)
    dosage_form: str | None = Field(default=None, max_length=80)
    route: str | None = Field(default=None, max_length=80)
    is_controlled: bool = False


class PrescriptionItemRequest(_StrictModel):
    medication_catalog_id: str = Field(min_length=1, max_length=26)
    dose_value: str = Field(min_length=1, max_length=80)
    dose_unit: str = Field(min_length=1, max_length=40)
    frequency: str = Field(min_length=1, max_length=120)
    route: str = Field(min_length=1, max_length=80)
    duration_days: int = Field(gt=0, le=3650)
    quantity: int = Field(gt=0, le=1_000_000)
    quantity_unit: str = Field(min_length=1, max_length=40)
    instructions: str | None = Field(default=None, max_length=2000)
    substitution_allowed: bool = False


class PrescriptionCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    encounter_id: str = Field(min_length=1, max_length=26)
    purpose: str = Field(default="treatment", min_length=1, max_length=40)
    note: str | None = Field(default=None, max_length=2000)
    items: list[PrescriptionItemRequest] = Field(min_length=1, max_length=50)


class PrescriptionAmendRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    reason: str = Field(min_length=3, max_length=500)
    items: list[PrescriptionItemRequest] = Field(min_length=1, max_length=50)

    @field_validator("reason")
    @classmethod
    def reason_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("reason must not be blank")
        return value


class PrescriptionActionRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)


class BatchCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    medication_catalog_id: str = Field(min_length=1, max_length=26)
    batch_number: str = Field(min_length=1, max_length=120)
    expiry_date: date
    quantity_received: int = Field(gt=0, le=10_000_000)


class DispenseCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    prescription_row_id: str = Field(min_length=1, max_length=26)
    prescription_item_id: str = Field(min_length=1, max_length=26)
    batch_id: str = Field(min_length=1, max_length=26)
    quantity: int = Field(gt=0, le=1_000_000)


class DispenseActionRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)


class PrescriptionResponse(_StrictModel):
    id: str
    prescription_id: str
    prescription_number: str
    version: int
    encounter_id: str
    patient_person_id: str
    prescriber_account_id: str
    organization_id: str
    facility_id: str
    workspace_id: str
    status: str
    purpose: str
    controlled_policy_status: str
    controlled_policy_approved_by_account_id: str | None
    controlled_policy_approved_at: datetime | None
    controlled_policy_reason: str | None
    controlled_policy_evidence: dict | None
    signed_at: datetime | None
    supersedes_id: str | None
    items: list[dict]
    correlation_id: str


class DispenseResponse(_StrictModel):
    id: str
    prescription_row_id: str
    prescription_item_id: str
    patient_person_id: str
    medication_catalog_id: str
    batch_id: str
    quantity: int
    status: str
    version: int
    prepared_by_account_id: str
    verified_by_account_id: str | None
    dispensed_by_account_id: str | None
    correlation_id: str


class ControlledPolicyActionRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    reason: str = Field(min_length=4, max_length=500)


class FefoDispenseCreateRequest(_StrictModel):
    prescription_row_id: str = Field(min_length=1, max_length=26)
    prescription_item_id: str = Field(min_length=1, max_length=26)
    workspace_id: str = Field(min_length=1, max_length=26)
    quantity: int = Field(gt=0, le=1_000_000)


class BatchActionRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    reason: str = Field(min_length=4, max_length=500)


class StockAdjustmentRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    quantity_delta: int = Field(ge=-100_000, le=100_000)
    kind: Literal["WASTE", "REVERSAL"]
    reason: str = Field(min_length=4, max_length=500)

    @field_validator("quantity_delta")
    @classmethod
    def quantity_must_not_be_zero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("quantity_delta must not be zero")
        return value
