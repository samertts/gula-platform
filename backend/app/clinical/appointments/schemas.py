from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AppointmentSlotCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=26)
    provider_account_id: str = Field(min_length=1, max_length=26)
    service_code: str = Field(min_length=1, max_length=120)
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def validate_window(self) -> AppointmentSlotCreateRequest:
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("starts_at and ends_at must include a timezone")
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class AppointmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=26)
    patient_person_id: str = Field(min_length=1, max_length=26)
    slot_id: str = Field(min_length=1, max_length=26)
    purpose: Literal["TREATMENT", "DIAGNOSIS"] = "TREATMENT"


class AppointmentConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=240)


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    state: str
    version: int
    slot_id: str
    service_code: str
    purpose: str
    provider_account_id: str
    organization_id: str
    facility_id: str
    workspace_id: str
    starts_at: datetime
    ends_at: datetime
    requested_at: datetime
    confirmed_at: datetime | None
    correlation_id: str


class AppointmentListResponse(BaseModel):
    items: list[AppointmentResponse]
    limit: int
    offset: int
    total: int


class SlotResponse(BaseModel):
    id: str
    workspace_id: str
    provider_account_id: str
    service_code: str
    starts_at: datetime
    ends_at: datetime
    status: str
    version: int


class SlotListResponse(BaseModel):
    items: list[SlotResponse]
    limit: int
    offset: int


class CoreErrorDetail(BaseModel):
    code: str
    message: str
    message_ar: str
    correlation_id: str
