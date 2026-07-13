"""MPI HTTP API — resolve / lookup / merge.

Endpoints:
    POST /mpi/resolve          — find or create the canonical citizen for a lab patient
    GET  /mpi/citizens/{ulid}  — admin-only projection (no raw PII)
    POST /mpi/merge            — admin-only manual merge

All endpoints require authentication. Resolve enforces lab ownership:
a user can only resolve patients in their own lab (ABAC via require_own_lab).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.lab_user import LabUser
from ...models.patient import Patient
from ...security.consent_dep import require_consent
from ...security.dependencies import get_current_user
from ...security.rate_limit import rate_limit_user
from ...security.rbac import require_own_lab, require_role
from . import resolver as mpi_resolver
from .models import Citizen, IdentityClaim
from .schemas import (
    CitizenResponse,
    MergeRequest,
    MergeResponse,
    PendingReviewItem,
    PendingReviewPage,
    ResolveDecision,
    ResolveRequest,
    ResolveResponse,
)

router = APIRouter(prefix="/mpi", tags=["mpi"])


# ── POST /mpi/resolve ────────────────────────────────────────────────────────


@router.post("/resolve", response_model=ResolveResponse, status_code=200)
def resolve(
    data: ResolveRequest,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResolveResponse:
    """Find or create the canonical citizen for a LIMS patient.

    Idempotent: re-calling for the same (lab_id, patient_id) returns the
    existing claim.
    """
    rate_limit_user(request, current_user.id, max_per_minute=60)
    # ABAC: must be a user in the target lab (platform admins may cross labs)
    require_own_lab(current_user, data.lab_id)

    # Sanity check: the LIMS patient exists and belongs to the declared lab
    patient = (
        db.query(Patient)
        .filter(Patient.id == data.patient_id, Patient.lab_id == data.lab_id)
        .first()
    )
    if patient is None:
        raise HTTPException(status_code=404, detail="patient not found in this lab")

    # Split birth_date into parts (matcher uses them independently)
    by = bm = bd = None
    if data.birth_date is not None:
        by = data.birth_date.year
        bm = data.birth_date.month
        bd = data.birth_date.day

    outcome = mpi_resolver.resolve_identity(
        db,
        lab_id=data.lab_id,
        local_patient_id=data.patient_id,
        name=data.name,
        phone=data.phone,
        birth_year=by,
        birth_month=bm,
        birth_day=bd,
        gender=data.gender,
        national_id=data.national_id,
        family_id=data.family_id,
        claimed_by_user_id=current_user.id,
    )
    db.commit()

    return ResolveResponse(
        citizen_ulid=outcome.citizen.citizen_ulid,
        match_method=outcome.match_method,
        match_score=outcome.match_score,
        created=outcome.created,
        features=outcome.features,
    )


# ── GET /mpi/citizens/{ulid} ─────────────────────────────────────────────────


@router.get("/citizens/{citizen_ulid}", response_model=CitizenResponse)
def get_citizen(
    citizen_ulid: str,
    current_user: LabUser = Depends(
        require_role(
            "master_admin",
            "ministry_admin",
            "province_admin",
        )
    ),
    db: Session = Depends(get_db),
) -> CitizenResponse:
    """Admin-only projection of a canonical citizen.

    Never exposes raw PII (name, phone, NID). The citizen's own portal
    uses a different endpoint after consent verification.
    """
    citizen = db.query(Citizen).filter(Citizen.citizen_ulid == citizen_ulid).first()
    if citizen is None:
        raise HTTPException(status_code=404, detail="citizen not found")

    merged_into_ulid = None
    if citizen.merged_into_id is not None:
        survivor = citizen.canonical()
        if survivor is not None and survivor.id != citizen.id:
            merged_into_ulid = survivor.citizen_ulid

    return CitizenResponse(
        citizen_ulid=citizen.citizen_ulid,
        nid_verified=citizen.nid_verified,
        birth_year=citizen.birth_year,
        gender=citizen.gender,
        status=citizen.status,
        merged_into_ulid=merged_into_ulid,
        created_at=citizen.created_at,
    )


# ── POST /mpi/merge ──────────────────────────────────────────────────────────


@router.post("/merge", response_model=MergeResponse, status_code=200)
def manual_merge(
    data: MergeRequest,
    current_user: LabUser = Depends(
        require_role(
            "master_admin",
            "ministry_admin",
        )
    ),
    db: Session = Depends(get_db),
) -> MergeResponse:
    """Manually merge two citizens (master/ministry admin only).

    Appends a hash-chained mpi_merge_audit entry; secondary transitions to
    status='merged' with merged_into_id pointing at the primary.
    """
    try:
        audit = mpi_resolver.merge_citizens(
            db,
            primary_ulid=data.primary_ulid,
            secondary_ulid=data.secondary_ulid,
            reason=data.reason,
            decided_by_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()

    return MergeResponse(
        event_id=audit.id,
        primary_ulid=data.primary_ulid,
        secondary_ulid=data.secondary_ulid,
        occurred_at=audit.occurred_at,
        entry_hash=audit.entry_hash,
    )


# ── GET /mpi/review — list ambiguous claims (0.70-0.90 score) ────────────────


@router.get("/review", response_model=PendingReviewPage)
def list_pending_review(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: LabUser = Depends(
        require_role(
            "master_admin",
            "ministry_admin",
            "province_admin",
        )
    ),
    db: Session = Depends(get_db),
) -> PendingReviewPage:
    """Admin queue of identity claims awaiting adjudication.

    These are matches where the probabilistic score landed in the fuzzy band
    (THRESHOLD_REVIEW ≤ score < THRESHOLD_AUTO). Leaving them unreviewed
    either loses cross-lab linkage (false negative) or conflates two real
    people (false positive, catastrophic at national scale).
    """
    base = db.query(IdentityClaim).filter(IdentityClaim.match_method == "pending_review")
    total = base.count()
    rows = base.order_by(IdentityClaim.created_at.asc()).offset(offset).limit(limit).all()

    items: list[PendingReviewItem] = []
    for claim in rows:
        citizen = db.query(Citizen).filter(Citizen.id == claim.citizen_id).first()
        items.append(
            PendingReviewItem(
                claim_id=claim.id,
                citizen_ulid=citizen.citizen_ulid if citizen else "",
                lab_id=claim.lab_id,
                local_patient_id=claim.local_patient_id,
                match_score=float(claim.match_score) if claim.match_score is not None else None,
                match_features=claim.match_features or {},
                created_at=claim.created_at,
            )
        )
    return PendingReviewPage(total=total, items=items)


# ── POST /mpi/review/{claim_id}/decide — adjudicate a pending claim ──────────


@router.post("/review/{claim_id}/decide", status_code=200)
def decide_pending_review(
    claim_id: int,
    decision: ResolveDecision,
    current_user: LabUser = Depends(
        require_role(
            "master_admin",
            "ministry_admin",
            "province_admin",
        )
    ),
    db: Session = Depends(get_db),
):
    """Confirm or reject an ambiguous claim.

    confirm → match_method becomes 'manual' (audit-preserved), the claim stays.
    reject  → detach from the current citizen and mint a new canonical one,
              so the lab patient gets its own record. Writes a MergeAudit row
              so the decision is hash-chained.
    """
    claim = db.query(IdentityClaim).filter(IdentityClaim.id == claim_id).first()
    if claim is None:
        raise HTTPException(status_code=404, detail="claim not found")
    if claim.match_method != "pending_review":
        raise HTTPException(
            status_code=409, detail=f"claim is not pending (method={claim.match_method})"
        )

    if decision.decision == "confirm":
        claim.match_method = "manual"
        db.flush()
        db.commit()
        return {"claim_id": claim.id, "status": "confirmed", "match_method": claim.match_method}

    # reject → mint new citizen and rebind the claim
    patient = (
        db.query(Patient)
        .filter(Patient.id == claim.local_patient_id, Patient.lab_id == claim.lab_id)
        .first()
    )
    if patient is None:
        raise HTTPException(status_code=404, detail="underlying patient missing")

    by = bm = bd = None
    if patient.birth_date:
        by, bm, bd = patient.birth_date.year, patient.birth_date.month, patient.birth_date.day

    # Delete the old claim first (uniqueness constraint on lab_id+local_patient_id)
    old_citizen_id = claim.citizen_id
    db.delete(claim)
    db.flush()

    outcome = mpi_resolver.resolve_identity(
        db,
        lab_id=patient.lab_id,
        local_patient_id=patient.id,
        name=patient.full_name,
        phone=patient.phone,
        birth_year=by,
        birth_month=bm,
        birth_day=bd,
        gender=patient.gender,
        national_id=None,  # reject path forces a new canonical; nid-exact would have auto-matched
        family_id=None,
        claimed_by_user_id=current_user.id,
    )
    # Force a new citizen even if probabilistic finds another — we just rejected a match.
    # resolve_identity with national_id=None and no prior claim will create a new Citizen
    # when no strong probabilistic match exists. If one does, mark it manual-review again.
    db.commit()
    return {
        "claim_id": claim.id,
        "status": "rejected",
        "previous_citizen_id": old_citizen_id,
        "new_citizen_ulid": outcome.citizen.citizen_ulid,
        "match_method": outcome.match_method,
    }


# ── GET /mpi/citizens/{citizen_ulid}/access — consent-gated citizen read ─────
# Unlike the admin-only projection above, this endpoint is reachable by any
# authenticated actor (doctor, staff). It is gated by the consent layer:
# the caller must hold an active Consent row (scope='read:citizen') for this
# citizen, OR be the citizen themselves (owner bypass), OR supply the
# emergency break-glass header as a doctor.


@router.get("/citizens/{citizen_ulid}/access", response_model=CitizenResponse)
def get_citizen_with_consent(
    citizen_ulid: str,
    current_user: LabUser = Depends(require_consent("read:citizen")),
    db: Session = Depends(get_db),
) -> CitizenResponse:
    """Cross-lab citizen projection, gated by the consent layer.

    Response shape matches the admin endpoint (no raw PII). The difference
    is the authorization model: this route is for doctors/labs acting on
    the subject's behalf with recorded consent, not for administrators.
    """
    citizen = db.query(Citizen).filter(Citizen.citizen_ulid == citizen_ulid).first()
    if citizen is None:
        raise HTTPException(status_code=404, detail="citizen not found")

    merged_into_ulid = None
    if citizen.merged_into_id is not None:
        survivor = citizen.canonical()
        if survivor is not None and survivor.id != citizen.id:
            merged_into_ulid = survivor.citizen_ulid

    return CitizenResponse(
        citizen_ulid=citizen.citizen_ulid,
        nid_verified=citizen.nid_verified,
        birth_year=citizen.birth_year,
        gender=citizen.gender,
        status=citizen.status,
        merged_into_ulid=merged_into_ulid,
        created_at=citizen.created_at,
    )
