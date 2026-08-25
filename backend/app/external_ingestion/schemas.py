from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExternalSourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_key: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,79}$")
    source_kind: Literal["professional_registry", "ministry_workforce", "civil_identity"]
    display_name: str = Field(min_length=3, max_length=200)
    schema_version: int = Field(ge=1, le=100)
    allowed_fields: list[str] = Field(min_length=1, max_length=80)
    service_account_id: int | None = Field(default=None, ge=1)
    contract_expires_at: datetime | None = None

    @field_validator("allowed_fields")
    @classmethod
    def validate_allowed_fields(cls, value: list[str]) -> list[str]:
        cleaned = sorted({field.strip() for field in value if field.strip()})
        if not cleaned:
            raise ValueError("allowed_fields must contain at least one field")
        if any(len(field) > 80 for field in cleaned):
            raise ValueError("allowed field names are too long")
        return cleaned


class SourceActivationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    legal_approval_ref: str = Field(min_length=3, max_length=240)
    security_review_ref: str = Field(min_length=3, max_length=240)
    second_reviewer_id: int = Field(ge=1)


class ImportManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_key: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,79}$")
    export_id: str = Field(min_length=1, max_length=160)
    idempotency_key: str = Field(min_length=16, max_length=240)
    content_sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    object_uri: str = Field(pattern=r"^(s3|gs|azure)://[^\s]{3,512}$")
    schema_version: int = Field(ge=1, le=100)
    declared_record_count: int = Field(ge=0, le=50_000_000)
    expires_at: datetime

    @field_validator("expires_at")
    @classmethod
    def require_timezone_aware_expiry(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("expires_at must be timezone-aware")
        return value


class ProfessionalRecordInput(BaseModel):
    """Bounded record used by a trusted staging worker, not a public upload."""

    model_config = ConfigDict(extra="forbid")

    source_record_id: str = Field(min_length=1, max_length=160)
    source_record_version: str | None = Field(default=None, max_length=80)
    profession: Literal[
        "doctor",
        "pharmacist",
        "laboratory_scientist",
        "dentist",
        "nurse",
    ]
    full_name: str = Field(min_length=1, max_length=240)
    national_id: str | None = Field(default=None, max_length=64)
    license_number: str | None = Field(default=None, max_length=100)
    license_authority: str | None = Field(default=None, max_length=120)
    specialty: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    birth_date: str | None = Field(default=None, max_length=10)
    employer_reference: str | None = Field(default=None, max_length=160)
    employment_status: str | None = Field(default=None, max_length=40)

    @field_validator("full_name")
    @classmethod
    def normalize_required_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("full_name must not be blank")
        return normalized


class ProfessionalRecordChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[ProfessionalRecordInput] = Field(min_length=1, max_length=500)


class MatchDecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "reject"]
    candidate_entity_id: int | None = Field(default=None, ge=1)
    reason_code: Literal[
        "verified_by_authority",
        "duplicate_source_record",
        "incorrect_match",
        "insufficient_evidence",
        "other",
    ]
    expected_version: int = Field(ge=1)


class ImportBatchResponse(BaseModel):
    id: int
    status: str
    source_key: str
    export_id: str
    expires_at: datetime


class ChunkResponse(BaseModel):
    batch_id: int
    status: str
    staged: int
    auto_matched: int
    pending_review: int
    rejected: int
