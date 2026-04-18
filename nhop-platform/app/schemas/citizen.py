"""Pydantic v2 schemas for the citizen registry API."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ─── National ID validator (Iraqi civil registry: 12 digits) ────────────────
_NID_MIN = 10
_NID_MAX = 14


def _validate_nid(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    if not v:
        return None
    if not v.isdigit():
        raise ValueError("national_id must contain digits only")
    if not (_NID_MIN <= len(v) <= _NID_MAX):
        raise ValueError(f"national_id length must be between {_NID_MIN} and {_NID_MAX}")
    return v


# ─── Input / output ─────────────────────────────────────────────────────────

class CitizenBase(BaseModel):
    full_name:   str  = Field(..., min_length=2, max_length=200)
    mother_name: Optional[str] = Field(default=None, max_length=200)
    birth_date:  Optional[date] = None
    gender:      Optional[str]  = Field(default=None, pattern=r"^[MFmf]$")
    phone:       Optional[str]  = Field(default=None, max_length=30)
    email:       Optional[str]  = Field(default=None, max_length=120)

    province: Optional[str] = Field(default=None, max_length=80)
    district: Optional[str] = Field(default=None, max_length=120)
    address:  Optional[str] = Field(default=None, max_length=500)

    chronic_diseases: Optional[list[str]] = None
    allergies:        Optional[list[str]] = None
    blood_type:       Optional[str] = Field(default=None, max_length=5)

    @field_validator("gender")
    @classmethod
    def _upper_gender(cls, v):
        return v.upper() if v else v


class CitizenCreate(CitizenBase):
    national_id: Optional[str] = Field(default=None, description="Civil registry ID")

    _nid = field_validator("national_id")(_validate_nid)


class CitizenUpdate(BaseModel):
    """PUT payload. national_id and health_id are immutable and rejected."""
    model_config = ConfigDict(extra="forbid")

    full_name:   Optional[str] = Field(default=None, min_length=2, max_length=200)
    mother_name: Optional[str] = Field(default=None, max_length=200)
    birth_date:  Optional[date] = None
    gender:      Optional[str]  = Field(default=None, pattern=r"^[MFmf]$")
    phone:       Optional[str]  = Field(default=None, max_length=30)
    email:       Optional[str]  = Field(default=None, max_length=120)
    province:    Optional[str]  = Field(default=None, max_length=80)
    district:    Optional[str]  = Field(default=None, max_length=120)
    address:     Optional[str]  = Field(default=None, max_length=500)
    chronic_diseases: Optional[list[str]] = None
    allergies:        Optional[list[str]] = None
    blood_type:       Optional[str] = Field(default=None, max_length=5)

    @field_validator("gender")
    @classmethod
    def _upper_gender(cls, v):
        return v.upper() if v else v


class CitizenRead(CitizenBase):
    model_config = ConfigDict(from_attributes=True)

    id:          int
    health_id:   str
    national_id: Optional[str]
    created_at:  datetime
    updated_at:  datetime


class CitizenSearchResult(BaseModel):
    total: int
    skip:  int
    limit: int
    items: list[CitizenRead]


class DuplicateMatch(BaseModel):
    health_id:  str
    full_name:  str
    score:      float
    reasons:    list[str]


class LabTestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:           int
    test_name:    str
    result_value: Optional[str]
    result_unit:  Optional[str]
    status:       str
    lab_name:     Optional[str]
    performed_at: datetime


class CitizenSummary(BaseModel):
    citizen:          CitizenRead
    recent_tests:     list[LabTestRead]
    chronic_diseases: list[str]
    allergies:        list[str]
