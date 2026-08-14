from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

CONTRACT_VERSION = "1.0"
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


class ClinicalResource(StrEnum):
    patients = "patients"
    orders = "orders"


class ClinicalGatewayErrorCode(StrEnum):
    unauthenticated = "UNAUTHENTICATED"
    unauthorized = "UNAUTHORIZED"
    not_found = "NOT_FOUND"
    context_conflict = "CONTEXT_CONFLICT"
    invalid_request = "INVALID_REQUEST"
    rate_limited = "RATE_LIMITED"
    unavailable = "UNAVAILABLE"


class ClinicalGatewayError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ClinicalGatewayErrorCode
    message: str = Field(min_length=1, max_length=240)
    request_id: UUID
    correlation_id: UUID


class ClinicalWorkspaceContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: str = Field(min_length=1, max_length=80)
    facility_id: str = Field(min_length=1, max_length=80)
    workspace_id: str = Field(min_length=1, max_length=80)
    department_id: str | None = Field(default=None, max_length=80)


class ClinicalPageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cursor: str | None = Field(default=None, min_length=1, max_length=200)
    limit: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
    search: str | None = Field(default=None, min_length=1, max_length=80)

    @field_validator("search")
    @classmethod
    def reject_identifier_search(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("search must contain at least two non-space characters")
        if normalized.isdigit() or normalized.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("identifier and phone enumeration are not supported by this contract")
        return normalized


class PatientRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=80)
    display_name: str = Field(min_length=1, max_length=200)
    birth_date: str | None = None
    gender: str | None = Field(default=None, max_length=32)
    created_at: datetime | None = None


class OrderRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=80)
    patient_display_name: str | None = Field(default=None, max_length=200)
    practitioner_display_name: str | None = Field(default=None, max_length=200)
    status: str = Field(min_length=1, max_length=40)
    test_count: int = Field(default=0, ge=0)
    created_at: datetime | None = None


T = TypeVar("T")



class ClinicalReadEnvelope[T](BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = Field(default=CONTRACT_VERSION, pattern=r"^1\.0$")
    request_id: UUID
    correlation_id: UUID
    workspace_context: ClinicalWorkspaceContext
    items: list[T]
    limit: int = Field(ge=1, le=MAX_PAGE_SIZE)
    next_cursor: str | None = Field(default=None, max_length=200)
    total: int | None = Field(default=None, ge=0)


class ClinicalGatewayErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ClinicalGatewayError
