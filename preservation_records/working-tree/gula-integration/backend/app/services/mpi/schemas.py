"""Pydantic v2 request/response schemas for the MPI HTTP API."""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class ResolveRequest(BaseModel):
    """POST /mpi/resolve body.

    The lab submits the identity it has on file; raw NID is hashed on the
    server side (never stored).
    """

    lab_id: int = Field(..., ge=1)
    patient_id: int = Field(..., ge=1, description="Local LIMS patient ID")
    name: str = Field(..., min_length=2, max_length=200)
    phone: str | None = Field(default=None, max_length=30)
    birth_date: date | None = None
    gender: str | None = Field(default=None, pattern=r"^[MFmf]$")
    national_id: str | None = Field(default=None, max_length=30)
    family_id: str | None = Field(default=None, max_length=30)

    @field_validator("gender")
    @classmethod
    def _upper_gender(cls, v):
        return v.upper() if v else v


class ResolveResponse(BaseModel):
    citizen_ulid: str
    match_method: str  # 'nid_exact' | 'probabilistic' | 'pending_review' | 'new'
    match_score: float | None = None
    created: bool
    features: dict = Field(default_factory=dict)


class CitizenResponse(BaseModel):
    citizen_ulid: str
    nid_verified: bool
    birth_year: int | None = None
    gender: str | None = None
    status: str
    merged_into_ulid: str | None = None
    created_at: datetime

    # Deliberately NOT exposed:
    #   - id (internal BigInt)
    #   - nid_hash (sensitive)
    #   - phone_last10 (sensitive)
    #   - full name / family_id_hash
    # The citizen portal uses a different endpoint that returns the citizen's
    # own PII to themselves after consent verification.


class MergeRequest(BaseModel):
    primary_ulid: str = Field(..., min_length=26, max_length=26)
    secondary_ulid: str = Field(..., min_length=26, max_length=26)
    reason: str = Field(..., min_length=10, max_length=500)


class MergeResponse(BaseModel):
    event_id: int
    primary_ulid: str
    secondary_ulid: str
    occurred_at: datetime
    entry_hash: str


class PendingReviewItem(BaseModel):
    """A single ambiguous claim awaiting admin adjudication."""

    claim_id: int
    citizen_ulid: str
    lab_id: int
    local_patient_id: int
    match_score: float | None = None
    match_features: dict = Field(default_factory=dict)
    created_at: datetime


class PendingReviewPage(BaseModel):
    total: int
    items: list[PendingReviewItem]


class ReconciliationItem(BaseModel):
    """A temporary/degraded MPI identity awaiting reconciliation.

    Derived from the canonical audit trail. Contains identifiers and status
    only — no raw national ID, name, phone or other PHI.
    """

    reconciliation_key: str
    patient_id: int | None = None
    lab_id: int | None = None
    status: str
    source: str | None = None
    error_type: str | None = None
    citizen_ulid: str | None = None
    first_seen_at: datetime
    marker_count: int = 1


class ReconciliationPage(BaseModel):
    total: int
    items: list[ReconciliationItem]


class ResolveDecision(BaseModel):
    """Body of POST /mpi/review/{claim_id}/decide.

    Canonical decisions (AUD-01):
      - 'ACCEPT_MATCH'        keep the claim, flip match_method to 'manual'
      - 'REJECT_MATCH'        detach from the rejected citizen and mint a NEW
                              canonical citizen (never re-score / re-link)
      - 'CREATE_NEW_IDENTITY' explicitly mint a NEW canonical citizen
      - 'NEEDS_MANUAL_REVIEW' leave the claim pending (no mutation)

    API compatibility: the legacy values 'confirm' and 'reject' are still
    accepted by the ``before`` validator below and normalise to ACCEPT_MATCH
    and REJECT_MATCH respectively.  Existing clients need no change; the
    response ``status`` field keeps its legacy 'confirmed'/'rejected' values.
    Additive change only -- no field was removed, renamed or narrowed.
    """

    decision: str = Field(
        ...,
        pattern=r"^(ACCEPT_MATCH|REJECT_MATCH|CREATE_NEW_IDENTITY|NEEDS_MANUAL_REVIEW)$",
    )
    reason: str = Field(..., min_length=10, max_length=500)

    @field_validator("decision", mode="before")
    @classmethod
    def _normalize_decision(cls, v: object) -> object:
        if isinstance(v, str):
            canonical = v.strip().upper()
            if canonical in {
                "ACCEPT_MATCH",
                "REJECT_MATCH",
                "CREATE_NEW_IDENTITY",
                "NEEDS_MANUAL_REVIEW",
            }:
                return canonical
            if v in ("confirm", "reject"):
                return {"confirm": "ACCEPT_MATCH", "reject": "REJECT_MATCH"}[v]
        return v
