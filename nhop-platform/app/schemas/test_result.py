"""Pydantic v2 schemas for the test-results API."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..models.test_result import ResultCategory, ResultStatus


class TestResultBase(BaseModel):
    test_code: str = Field(..., min_length=1, max_length=60)
    test_name: str = Field(..., min_length=1, max_length=200)
    category: ResultCategory = ResultCategory.other

    value_numeric: float | None = None
    value_text: str | None = Field(default=None, max_length=400)
    unit: str | None = Field(default=None, max_length=40)

    reference_min: float | None = None
    reference_max: float | None = None

    @field_validator("test_code")
    @classmethod
    def _upper_code(cls, v: str) -> str:
        return v.strip().upper()


class TestResultCreate(TestResultBase):
    health_id: str = Field(..., min_length=1, max_length=20)
    lab_id: UUID
    performed_at: datetime | None = None


class TestResultValidateRequest(TestResultBase):
    """Pre-save validation. No citizen / lab context required."""


class ValidationWarning(BaseModel):
    code: str
    message: str
    severity: str = "warning"  # 'info' | 'warning' | 'critical'


class TestResultValidateResponse(BaseModel):
    is_valid: bool
    is_critical: bool
    is_abnormal: bool
    direction: str | None = None
    interpretation_ar: str | None = None
    warnings: list[ValidationWarning] = Field(default_factory=list)


class TestResultRead(TestResultBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    citizen_id: int
    lab_id: UUID
    sample_barcode: str

    is_abnormal: bool
    is_critical: bool
    direction: str | None = None
    interpretation_ar: str | None = None
    warnings: list | None = None
    status: ResultStatus

    performed_at: datetime
    received_at: datetime
    reported_at: datetime | None = None
    verified_by: str | None = None
    verified_at: datetime | None = None
    created_at: datetime


class TestResultListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[TestResultRead]


class TestResultVerifyRequest(BaseModel):
    """Verification takes nothing from the caller (NR-144).

    It used to carry ``verified_by``, so the request named the clinician
    attesting the result. That is the most authority-bearing field on the row --
    it is the whole point of a verification -- and it was whatever string the
    client sent. The verifier is now read from the trusted context in
    ``api/v1/test_results.py``, which leaves this request with nothing to say.

    The model is kept rather than deleted so that a future field has an obvious
    place to land, and so ``extra="forbid"`` keeps rejecting the old shape
    instead of accepting and ignoring it.
    """

    model_config = ConfigDict(extra="forbid")


class TimelinePoint(BaseModel):
    performed_at: datetime
    value_numeric: float | None = None
    value_text: str | None = None
    unit: str | None = None
    is_abnormal: bool
    is_critical: bool
    reference_min: float | None = None
    reference_max: float | None = None


class TimelineSeries(BaseModel):
    test_code: str
    test_name: str
    unit: str | None = None
    points: list[TimelinePoint]


class CitizenTimelineResponse(BaseModel):
    health_id: str
    series: list[TimelineSeries]
