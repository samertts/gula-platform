"""Pydantic v2 schemas for the test-results API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..models.test_result import ResultCategory, ResultStatus


class TestResultBase(BaseModel):
    test_code: str = Field(..., min_length=1, max_length=60)
    test_name: str = Field(..., min_length=1, max_length=200)
    category: ResultCategory = ResultCategory.other

    value_numeric: Optional[float] = None
    value_text: Optional[str] = Field(default=None, max_length=400)
    unit: Optional[str] = Field(default=None, max_length=40)

    reference_min: Optional[float] = None
    reference_max: Optional[float] = None

    @field_validator("test_code")
    @classmethod
    def _upper_code(cls, v: str) -> str:
        return v.strip().upper()


class TestResultCreate(TestResultBase):
    health_id: str = Field(..., min_length=1, max_length=20)
    lab_id: UUID
    performed_at: Optional[datetime] = None


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
    direction: Optional[str] = None
    interpretation_ar: Optional[str] = None
    warnings: list[ValidationWarning] = Field(default_factory=list)


class TestResultRead(TestResultBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    citizen_id: int
    lab_id: UUID
    sample_barcode: str

    is_abnormal: bool
    is_critical: bool
    direction: Optional[str] = None
    interpretation_ar: Optional[str] = None
    warnings: Optional[list] = None
    status: ResultStatus

    performed_at: datetime
    received_at: datetime
    reported_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime


class TestResultListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[TestResultRead]


class TestResultVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verified_by: str = Field(..., min_length=1, max_length=80)


class TimelinePoint(BaseModel):
    performed_at: datetime
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    is_abnormal: bool
    is_critical: bool
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None


class TimelineSeries(BaseModel):
    test_code: str
    test_name: str
    unit: Optional[str] = None
    points: list[TimelinePoint]


class CitizenTimelineResponse(BaseModel):
    health_id: str
    series: list[TimelineSeries]
