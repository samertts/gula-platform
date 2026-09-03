from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LabOrderItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_code: str = Field(min_length=1, max_length=120)
    test_name: str = Field(min_length=1, max_length=240)
    specimen_type: str = Field(min_length=1, max_length=80)

    @field_validator("test_code", "test_name", "specimen_type")
    @classmethod
    def non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value


class CreateLabOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    encounter_id: str = Field(min_length=1, max_length=26)
    workspace_id: str = Field(min_length=1, max_length=26)
    priority: str = Field(default="ROUTINE", pattern="^(ROUTINE|URGENT|STAT)$")
    clinical_indication: str | None = Field(default=None, max_length=1000)
    items: list[LabOrderItemRequest] = Field(min_length=1, max_length=20)


class LabOrderActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=26)


class CreateSpecimenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=26)
    order_item_id: str = Field(min_length=1, max_length=26)


class RejectSpecimenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=26)
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("reason")
    @classmethod
    def reason_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("reason must not be blank")
        return value


class WorklistQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=26)
    status: str | None = Field(default=None, max_length=24)
    priority: str | None = Field(default=None, pattern="^(ROUTINE|URGENT|STAT)$")
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=1_000_000)


class LabOrderResponse(BaseModel):
    id: str
    encounter_id: str
    patient_person_id: str
    ordering_provider_account_id: str
    laboratory_id: str
    organization_id: str
    facility_id: str
    workspace_id: str
    status: str
    priority: str
    version: int
    item_count: int
    created_at: datetime
    correlation_id: str


class SpecimenResponse(BaseModel):
    id: str
    lab_order_id: str
    order_item_id: str
    patient_person_id: str
    specimen_type: str
    accession_number: str
    barcode: str
    status: str
    version: int
    correlation_id: str
