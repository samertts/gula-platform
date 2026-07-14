"""Pydantic v2 schemas for the doctor-portal API (CMD-017)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..models.test_order import TestOrderStatus

# ─── POST /doctor/order-tests ───────────────────────────────────────────────

class OrderTestsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citizen_health_id: str = Field(..., min_length=1, max_length=20)
    tests: list[str] = Field(..., min_length=1, max_length=50)
    clinical_indication: str = Field(..., min_length=2, max_length=500)
    preferred_lab_id: UUID | None = None
    urgent: bool = False

    @field_validator("tests")
    @classmethod
    def _normalize_codes(cls, v: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for code in v:
            code = (code or "").strip().upper()
            if code and code not in seen:
                seen.add(code)
                out.append(code)
        if not out:
            raise ValueError("tests must contain at least one non-empty code")
        return out


class DuplicateTestNotice(BaseModel):
    """One entry per test code that was dropped due to the 7-day dedup rule."""
    test_code: str
    last_performed_at: datetime
    last_result_id: UUID


class OrderTestsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    citizen_id: int
    doctor_id: str
    lab_id: UUID | None
    tests: list[str]
    suggested_additions: list[str] = Field(default_factory=list)
    duplicates_skipped: list[DuplicateTestNotice] = Field(default_factory=list)
    clinical_indication: str
    urgent: bool
    status: TestOrderStatus
    created_at: datetime


# ─── GET /doctor/patient/{health_id}/overview ───────────────────────────────

class OverviewCitizen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    health_id: str
    full_name: str
    gender: str | None = None
    birth_date: datetime | None = None
    blood_type: str | None = None
    province: str | None = None
    chronic_diseases: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)


class OverviewResultRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    test_code: str
    test_name: str
    value_numeric: float | None = None
    value_text: str | None = None
    unit: str | None = None
    is_abnormal: bool
    is_critical: bool
    direction: str | None = None
    performed_at: datetime


class OverviewAlert(BaseModel):
    code: str
    message: str
    severity: str  # 'info' | 'warning' | 'critical'


class PatientOverviewResponse(BaseModel):
    citizen: OverviewCitizen
    recent_results: list[OverviewResultRow]
    medications: list[str] = Field(default_factory=list)
    active_alerts: list[OverviewAlert] = Field(default_factory=list)
    health_score: int = Field(..., ge=0, le=100)


# ─── GET /doctor/patient/{health_id}/timeline/{test_code} ───────────────────

class TimelineDoctorPoint(BaseModel):
    performed_at: datetime
    value_numeric: float | None = None
    value_text: str | None = None
    unit: str | None = None
    is_abnormal: bool
    is_critical: bool
    direction: str | None = None
    reference_min: float | None = None
    reference_max: float | None = None


class DoctorTimelineResponse(BaseModel):
    health_id: str
    test_code: str
    test_name: str | None = None
    unit: str | None = None
    points: list[TimelineDoctorPoint]


# ─── POST /doctor/refer ─────────────────────────────────────────────────────

class ReferralRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citizen_health_id: str = Field(..., min_length=1, max_length=20)
    to_doctor_id: str = Field(..., min_length=1, max_length=80)
    reason: str = Field(..., min_length=2, max_length=1000)
    include_recent_results: int = Field(default=5, ge=0, le=20)


class ReferralResponse(BaseModel):
    id: UUID
    citizen_health_id: str
    from_doctor_id: str
    to_doctor_id: str
    reason: str
    summary: dict
    created_at: datetime
