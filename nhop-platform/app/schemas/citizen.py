"""Pydantic v2 schemas for the citizen registry API."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ─── National ID validator (Iraqi civil registry: 12 digits) ────────────────
_NID_MIN = 10
_NID_MAX = 14


def _validate_nid(v: str | None) -> str | None:
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
    mother_name: str | None = Field(default=None, max_length=200)
    birth_date:  date | None = None
    gender:      str | None  = Field(default=None, pattern=r"^[MFmf]$")
    phone:       str | None  = Field(default=None, max_length=30)
    email:       str | None  = Field(default=None, max_length=120)

    province: str | None = Field(default=None, max_length=80)
    district: str | None = Field(default=None, max_length=120)
    address:  str | None = Field(default=None, max_length=500)

    chronic_diseases: list[str] | None = None
    allergies:        list[str] | None = None
    blood_type:       str | None = Field(default=None, max_length=5)

    @field_validator("gender")
    @classmethod
    def _upper_gender(cls, v):
        return v.upper() if v else v


class CitizenCreate(CitizenBase):
    national_id: str | None = Field(default=None, description="Civil registry ID")

    _nid = field_validator("national_id")(_validate_nid)


class CitizenUpdate(BaseModel):
    """PUT payload. national_id and health_id are immutable and rejected."""
    model_config = ConfigDict(extra="forbid")

    full_name:   str | None = Field(default=None, min_length=2, max_length=200)
    mother_name: str | None = Field(default=None, max_length=200)
    birth_date:  date | None = None
    gender:      str | None  = Field(default=None, pattern=r"^[MFmf]$")
    phone:       str | None  = Field(default=None, max_length=30)
    email:       str | None  = Field(default=None, max_length=120)
    province:    str | None  = Field(default=None, max_length=80)
    district:    str | None  = Field(default=None, max_length=120)
    address:     str | None  = Field(default=None, max_length=500)
    chronic_diseases: list[str] | None = None
    allergies:        list[str] | None = None
    blood_type:       str | None = Field(default=None, max_length=5)

    @field_validator("gender")
    @classmethod
    def _upper_gender(cls, v):
        return v.upper() if v else v


class CitizenRead(CitizenBase):
    model_config = ConfigDict(from_attributes=True)

    id:          int
    health_id:   str
    national_id: str | None
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
    result_value: str | None
    result_unit:  str | None
    status:       str
    lab_name:     str | None
    performed_at: datetime


class CitizenSummary(BaseModel):
    citizen:          CitizenRead
    recent_tests:     list[LabTestRead]
    chronic_diseases: list[str]
    allergies:        list[str]
