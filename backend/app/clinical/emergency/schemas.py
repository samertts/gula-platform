from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TemporarySubjectCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    synthetic_label: str = Field(min_length=1, max_length=160)


class IncidentCreateRequest(_StrictModel):
    incident_id: str = Field(min_length=8, max_length=64)
    workspace_id: str = Field(min_length=1, max_length=26)
    chief_complaint: str = Field(min_length=1, max_length=4000)
    priority: str = Field(default="URGENT", pattern="^(ROUTINE|URGENT|STAT|CRITICAL)$")
    patient_person_id: str | None = Field(default=None, max_length=26)
    temporary_subject_id: str | None = Field(default=None, max_length=26)
    location_summary: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def require_one_subject(self):
        if bool(self.patient_person_id) == bool(self.temporary_subject_id):
            raise ValueError("exactly one known patient or temporary subject is required")
        return self


class WorkflowActionRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    target_status: str = Field(min_length=1, max_length=32)
    reason: str | None = Field(default=None, max_length=2000)


class TriageCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    incident_id: str = Field(min_length=1, max_length=26)
    triage_id: str = Field(min_length=8, max_length=64)
    category: str = Field(pattern="^(IMMEDIATE|VERY_URGENT|URGENT|STANDARD|DELAYED|EXPECTANT)$")
    clinician_summary: str = Field(min_length=1, max_length=4000)
    vital_snapshot: dict[str, Any]


class DispatchCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    dispatch_request_id: str = Field(min_length=8, max_length=100)
    incident_id: str = Field(min_length=1, max_length=26)
    ambulance_reference: str = Field(min_length=1, max_length=120)
    crew_references: list[str] = Field(min_length=1, max_length=20)
    dispatch_notes: str | None = Field(default=None, max_length=2000)


class TreatmentCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    treatment_request_id: str = Field(min_length=8, max_length=100)
    incident_id: str = Field(min_length=1, max_length=26)
    treatment_type: str = Field(min_length=1, max_length=100)
    treatment_details: str = Field(min_length=1, max_length=4000)


class PrealertCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    prealert_request_id: str = Field(min_length=8, max_length=100)
    incident_id: str = Field(min_length=1, max_length=26)
    destination_facility_reference: str = Field(min_length=1, max_length=120)
    acuity: str = Field(pattern="^(ROUTINE|URGENT|STAT|CRITICAL)$")
    estimated_arrival_minutes: int = Field(ge=0, le=1440)
    minimal_payload: dict[str, Any]


class HandoverCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    handover_request_id: str = Field(min_length=8, max_length=100)
    incident_id: str = Field(min_length=1, max_length=26)
    receiving_facility_reference: str = Field(min_length=1, max_length=120)
    minimal_summary: dict[str, Any]


class EPCRCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    epcr_id: str = Field(min_length=8, max_length=64)
    incident_id: str = Field(min_length=1, max_length=26)
    chief_complaint: str = Field(min_length=1, max_length=2000)
    narrative: str = Field(min_length=1, max_length=8000)
    interventions: list[dict[str, Any]] = Field(max_length=100)
    destination_facility_reference: str | None = Field(default=None, max_length=120)
    signature_evidence: dict[str, Any] | None = None


class EPCRActionRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    signature_evidence: dict[str, Any] | None = None


class TemporarySubjectReconciliationRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    resolution: str = Field(pattern="^(MATCHED|MULTIPLE_MATCHES|NO_MATCH|REQUIRES_REVIEW)$")
    person_id: str | None = Field(default=None, max_length=26)
    reason: str = Field(min_length=1, max_length=2000)


class HandoverAmendRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    handover_request_id: str = Field(min_length=8, max_length=100)
    receiving_facility_reference: str = Field(min_length=1, max_length=120)
    minimal_summary: dict[str, Any]
    amendment_reason: str = Field(min_length=1, max_length=2000)


class EPCRAmendRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    epcr_id: str = Field(min_length=8, max_length=64)
    chief_complaint: str = Field(min_length=1, max_length=2000)
    narrative: str = Field(min_length=1, max_length=8000)
    interventions: list[dict[str, Any]] = Field(max_length=100)
    destination_facility_reference: str | None = Field(default=None, max_length=120)
    amendment_reason: str = Field(min_length=1, max_length=2000)
