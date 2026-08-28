from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AdmissionCreateRequest(_StrictModel):
    admission_request_id: str = Field(min_length=8, max_length=100)
    encounter_id: str = Field(min_length=1, max_length=26)
    workspace_id: str = Field(min_length=1, max_length=26)
    ward_id: str = Field(min_length=1, max_length=26)
    admission_reason: str = Field(min_length=1, max_length=2000)
    admission_type: str = Field(default="ELECTIVE", pattern="^(EMERGENCY|ELECTIVE|TRANSFER|OBSERVATION)$")


class ResourceActionRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)


class WorkflowActionRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    target_status: str = Field(min_length=1, max_length=32)


class BedAllocationRequest(_StrictModel):
    admission_id: str = Field(min_length=1, max_length=26)
    bed_id: str = Field(min_length=1, max_length=26)
    workspace_id: str = Field(min_length=1, max_length=26)


class NursingTaskCreateRequest(_StrictModel):
    admission_id: str = Field(min_length=1, max_length=26)
    workspace_id: str = Field(min_length=1, max_length=26)
    task_type: str = Field(min_length=1, max_length=80)
    instructions: str | None = Field(default=None, max_length=4000)


class VitalCreateRequest(_StrictModel):
    admission_id: str | None = Field(default=None, max_length=26)
    encounter_id: str = Field(min_length=1, max_length=26)
    workspace_id: str = Field(min_length=1, max_length=26)
    vital_type: str = Field(min_length=1, max_length=64)
    value_numeric: str = Field(min_length=1, max_length=64)
    unit: str = Field(min_length=1, max_length=40)
    method: str = Field(min_length=1, max_length=80)
    source: str = Field(default="MANUAL", min_length=1, max_length=80)
    observed_at: datetime
    device_reference: str | None = Field(default=None, max_length=160)


class MedicationAdministrationCreateRequest(_StrictModel):
    admission_id: str = Field(min_length=1, max_length=26)
    prescription_id: str = Field(min_length=1, max_length=26)
    prescription_item_id: str = Field(min_length=1, max_length=26)
    workspace_id: str = Field(min_length=1, max_length=26)
    administration_key: str = Field(min_length=8, max_length=120)
    dose_value: str = Field(min_length=1, max_length=80)
    dose_unit: str = Field(min_length=1, max_length=40)
    route: str = Field(min_length=1, max_length=80)
    scheduled_at: datetime | None = None


class MedicationAdministrationActionRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    target_status: str = Field(pattern="^(VERIFIED|SCHEDULED|ADMINISTERED|HELD|REFUSED|MISSED|CANCELLED)$")
    reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def require_reason_for_exception(self):
        if self.target_status in {"HELD", "REFUSED", "MISSED", "CANCELLED"} and not self.reason:
            raise ValueError("reason is required for this medication administration outcome")
        return self


class SafetyEventCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    event_type: str = Field(min_length=1, max_length=80)
    severity: str = Field(default="LOW", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    description: str = Field(min_length=1, max_length=4000)


class TransferCreateRequest(_StrictModel):
    transfer_request_id: str = Field(min_length=8, max_length=100)
    admission_id: str = Field(min_length=1, max_length=26)
    from_bed_id: str = Field(min_length=1, max_length=26)
    to_bed_id: str = Field(min_length=1, max_length=26)
    workspace_id: str = Field(min_length=1, max_length=26)
    reason: str = Field(min_length=1, max_length=2000)


class HandoverCreateRequest(_StrictModel):
    handover_request_id: str = Field(min_length=8, max_length=100)
    admission_id: str = Field(min_length=1, max_length=26)
    workspace_id: str = Field(min_length=1, max_length=26)
    minimal_summary: dict[str, Any]


class HandoverAcknowledgeRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)


class DischargeCreateRequest(_StrictModel):
    discharge_request_id: str = Field(min_length=8, max_length=100)
    admission_id: str = Field(min_length=1, max_length=26)
    workspace_id: str = Field(min_length=1, max_length=26)
    disposition: str = Field(default="HOME", pattern="^(HOME|TRANSFER|OTHER_FACILITY|DEATH)$")


class DischargeReadinessRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    medication_reconciliation_complete: bool
    pending_results_reviewed: bool
    follow_up_plan: str | None = Field(default=None, max_length=4000)
    instructions: str | None = Field(default=None, max_length=4000)


class DischargeSummaryRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    admission_reason: str = Field(min_length=1, max_length=2000)
    diagnoses: list[str] = Field(default_factory=list, max_length=100)
    procedures: list[str] = Field(default_factory=list, max_length=100)
    treatment: str = Field(min_length=1, max_length=4000)
    medications: list[str] = Field(default_factory=list, max_length=100)
    results: list[str] = Field(default_factory=list, max_length=100)
    condition: str = Field(min_length=1, max_length=1000)
    follow_up: str | None = Field(default=None, max_length=4000)


class WardCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=240)
    capacity: int = Field(ge=0, le=100000)


class RoomCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    ward_id: str = Field(min_length=1, max_length=26)
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=240)
    capacity: int = Field(gt=0, le=1000)


class BedCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    room_id: str = Field(min_length=1, max_length=26)
    code: str = Field(min_length=1, max_length=80)
    bed_type: str = Field(default="STANDARD", min_length=1, max_length=48)


class CareTeamMemberCreateRequest(_StrictModel):
    workspace_id: str = Field(min_length=1, max_length=26)
    admission_id: str = Field(min_length=1, max_length=26)
    account_id: str = Field(min_length=1, max_length=26)
    role: str = Field(min_length=1, max_length=40)
    scope: str = Field(min_length=1, max_length=240)
    purpose: str = Field(min_length=1, max_length=120)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
