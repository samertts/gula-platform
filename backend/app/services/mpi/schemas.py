"""Pydantic v2 request/response schemas for the MPI HTTP API."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ResolveRequest(BaseModel):
    """POST /mpi/resolve body.

    The lab submits the identity it has on file; raw NID is hashed on the
    server side (never stored).
    """
    lab_id:       int = Field(..., ge=1)
    patient_id:   int = Field(..., ge=1, description="Local LIMS patient ID")
    name:         str = Field(..., min_length=2, max_length=200)
    phone:        Optional[str] = Field(default=None, max_length=30)
    birth_date:   Optional[date] = None
    gender:       Optional[str] = Field(default=None, pattern=r"^[MFmf]$")
    national_id:  Optional[str] = Field(default=None, max_length=30)
    family_id:    Optional[str] = Field(default=None, max_length=30)

    @field_validator("gender")
    @classmethod
    def _upper_gender(cls, v):
        return v.upper() if v else v


class ResolveResponse(BaseModel):
    citizen_ulid: str
    match_method: str        # 'nid_exact' | 'probabilistic' | 'pending_review' | 'new'
    match_score:  Optional[float] = None
    created:      bool
    features:     dict = Field(default_factory=dict)


class CitizenResponse(BaseModel):
    citizen_ulid: str
    nid_verified: bool
    birth_year:   Optional[int] = None
    gender:       Optional[str] = None
    status:       str
    merged_into_ulid: Optional[str] = None
    created_at:   datetime

    # Deliberately NOT exposed:
    #   - id (internal BigInt)
    #   - nid_hash (sensitive)
    #   - phone_last10 (sensitive)
    #   - full name / family_id_hash
    # The citizen portal uses a different endpoint that returns the citizen's
    # own PII to themselves after consent verification.


class MergeRequest(BaseModel):
    primary_ulid:    str = Field(..., min_length=26, max_length=26)
    secondary_ulid:  str = Field(..., min_length=26, max_length=26)
    reason:          str = Field(..., min_length=10, max_length=500)


class MergeResponse(BaseModel):
    event_id:        int
    primary_ulid:    str
    secondary_ulid:  str
    occurred_at:     datetime
    entry_hash:      str
