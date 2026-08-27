from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImagingOrderCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    encounter_id: str = Field(min_length=1, max_length=26)
    modality: str = Field(min_length=1, max_length=32)
    body_part: str | None = Field(default=None, max_length=120)
    clinical_indication: str | None = Field(default=None, max_length=2000)
    priority: str = Field(default="ROUTINE", pattern="^(ROUTINE|URGENT|STAT)$")


class ImagingOrderActionRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)


class ImagingStudyIngestRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    order_id: str = Field(min_length=1, max_length=26)
    study_instance_uid: str = Field(min_length=1, max_length=128)
    accession_number: str = Field(min_length=1, max_length=80)
    modality: str = Field(min_length=1, max_length=32)
    source_message_id: str = Field(min_length=1, max_length=200)
    provenance_type: str = Field(default="SYNTHETIC_ADAPTER", pattern="^(SYNTHETIC_ADAPTER|DICOMWEB_ADAPTER|PACS_ADAPTER)$")
    study_description: str | None = Field(default=None, max_length=256)


class ImagingInstanceIngestRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    study_id: str = Field(min_length=1, max_length=26)
    series_instance_uid: str = Field(min_length=1, max_length=128)
    sop_instance_uid: str = Field(min_length=1, max_length=128)
    source_message_id: str = Field(min_length=1, max_length=200)
    object_reference: str = Field(min_length=1, max_length=512)
    checksum: str = Field(min_length=16, max_length=128)
    file_size_bytes: int = Field(gt=0, le=10_000_000_000)

    @field_validator("object_reference")
    @classmethod
    def internal_object_reference(cls, value: str) -> str:
        value = value.strip()
        if value.startswith(("http://", "https://")):
            raise ValueError("public image URLs are not accepted")
        return value


class ImagingReportCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    study_id: str = Field(min_length=1, max_length=26)
    findings: str | None = Field(default=None, max_length=10000)
    impression: str | None = Field(default=None, max_length=5000)
    critical: bool = False


class ImagingReportAmendRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    reason: str = Field(min_length=3, max_length=500)
    findings: str | None = Field(default=None, max_length=10000)
    impression: str | None = Field(default=None, max_length=5000)
    critical: bool = False

    @field_validator("reason")
    @classmethod
    def reason_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("reason must not be blank")
        return value


class ImagingReportActionRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)


class CriticalAcknowledgeRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    reason: str = Field(min_length=3, max_length=500)


class ImagingStudyResponse(_StrictModel):
    id: str
    study_id: str
    order_id: str
    patient_person_id: str
    study_instance_uid: str
    accession_number: str
    modality: str
    status: str
    provenance_type: str
    series_count: int
    instance_count: int
    version: int
    correlation_id: str


class ImagingReportResponse(_StrictModel):
    id: str
    report_id: str
    study_id: str
    patient_person_id: str
    ordering_provider_account_id: str
    radiologist_account_id: str
    version: int
    status: str
    findings: str | None
    impression: str | None
    critical: bool
    supersedes_id: str | None
    signed_at: datetime | None
    released_at: datetime | None
    correlation_id: str
