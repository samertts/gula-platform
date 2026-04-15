"""MPI HTTP API — resolve / lookup / merge.

Endpoints:
    POST /mpi/resolve          — find or create the canonical citizen for a lab patient
    GET  /mpi/citizens/{ulid}  — admin-only projection (no raw PII)
    POST /mpi/merge            — admin-only manual merge

All endpoints require authentication. Resolve enforces lab ownership:
a user can only resolve patients in their own lab (ABAC via require_own_lab).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.lab_user import LabUser
from ...models.patient import Patient
from ...security.dependencies import get_current_user
from ...security.rbac import require_own_lab, require_role

from . import resolver as mpi_resolver
from .models import Citizen
from .schemas import (
    CitizenResponse, MergeRequest, MergeResponse,
    ResolveRequest, ResolveResponse,
)


router = APIRouter(prefix="/mpi", tags=["mpi"])


# ── POST /mpi/resolve ────────────────────────────────────────────────────────

@router.post("/resolve", response_model=ResolveResponse, status_code=200)
def resolve(
    data: ResolveRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResolveResponse:
    """Find or create the canonical citizen for a LIMS patient.

    Idempotent: re-calling for the same (lab_id, patient_id) returns the
    existing claim.
    """
    # ABAC: must be a user in the target lab (platform admins may cross labs)
    require_own_lab(current_user, data.lab_id)

    # Sanity check: the LIMS patient exists and belongs to the declared lab
    patient = (db.query(Patient)
                 .filter(Patient.id == data.patient_id, Patient.lab_id == data.lab_id)
                 .first())
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
    current_user: LabUser = Depends(require_role(
        "master_admin", "ministry_admin", "province_admin",
    )),
    db: Session = Depends(get_db),
) -> CitizenResponse:
    """Admin-only projection of a canonical citizen.

    Never exposes raw PII (name, phone, NID). The citizen's own portal
    uses a different endpoint after consent verification.
    """
    citizen = (db.query(Citizen)
                 .filter(Citizen.citizen_ulid == citizen_ulid)
                 .first())
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
    current_user: LabUser = Depends(require_role(
        "master_admin", "ministry_admin",
    )),
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
