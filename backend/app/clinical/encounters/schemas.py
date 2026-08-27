from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CheckInRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    appointment_id: str = Field(min_length=1, max_length=26)
    workspace_id: str = Field(min_length=1, max_length=26)


class TransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=26)


class NoteFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chief_complaint: str | None = Field(default=None, max_length=10000)
    history: str | None = Field(default=None, max_length=20000)
    examination: str | None = Field(default=None, max_length=20000)
    assessment: str | None = Field(default=None, max_length=20000)
    plan: str | None = Field(default=None, max_length=20000)


class CreateNoteRequest(NoteFields):
    workspace_id: str = Field(min_length=1, max_length=26)
    encounter_id: str = Field(min_length=1, max_length=26)


class UpdateNoteRequest(NoteFields):
    workspace_id: str = Field(min_length=1, max_length=26)


class AmendNoteRequest(NoteFields):
    workspace_id: str = Field(min_length=1, max_length=26)
    reason: str = Field(min_length=1, max_length=500)


class EncounterResponse(BaseModel):
    id: str
    appointment_id: str
    patient_person_id: str
    provider_account_id: str
    organization_id: str
    facility_id: str
    workspace_id: str
    status: str
    version: int
    checked_in_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    correlation_id: str


class ClinicalNoteResponse(BaseModel):
    id: str
    note_id: str
    encounter_id: str
    patient_person_id: str
    author_account_id: str
    status: str
    version: int
    chief_complaint: str | None
    history: str | None
    examination: str | None
    assessment: str | None
    plan: str | None
    amendment_reason: str | None
    supersedes_id: str | None
    signed_by_account_id: str | None
    signed_at: datetime | None
    correlation_id: str
