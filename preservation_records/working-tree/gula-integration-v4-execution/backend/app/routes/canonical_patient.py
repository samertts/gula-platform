import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..domain.exceptions import ConflictError, NotFoundError
from ..models.canonical_patient import CanonicalPatient
from ..models.lab_user import LabUser
from ..models.patient import Patient
from ..security.dependencies import get_current_user
from ..security.rbac import require_own_lab, require_role
from ..services.audit_service import log_action
from ..services.mpi.canonical_service import (
    get_canonical_by_citizen,
    get_canonical_by_patient,
    link_citizen,
    link_patient,
    merge_canonicals,
)
from ..services.mpi.models import Citizen

router = APIRouter(prefix="/api/v1/canonical-patients", tags=["canonical-patients"])
logger = logging.getLogger("gula.routes.canonical_patient")

# AUD-02: link writes are identity-changing operations.  They require an
# INSTITUTIONAL account (LabUser with a lab) with an administrative role --
# never a bare authenticated principal or a citizen ``User`` account.
_LINK_ROLES = frozenset(
    {"master_admin", "ministry_admin", "province_admin", "admin", "lab_admin"}
)


def require_link_actor():
    def checker(current_user=Depends(get_current_user)) -> LabUser:
        if (
            not isinstance(current_user, LabUser)
            or current_user.lab_id is None
            or current_user.role not in _LINK_ROLES
        ):
            raise HTTPException(status_code=403, detail="insufficient permissions to link identities")
        return current_user

    return checker


def _write_canonical_audit(db, current_user, action: str, resource_id: int, details: dict) -> None:
    """Append a tamper-evident, hash-chained audit entry (AUD-12).

    CanonicalPatient rows are not MPI ``citizens``, so the MPI MergeAudit FK
    cannot hold them.  The general ``audit_logs`` chain is used instead: same
    tamper-evidence, no DDL, no schema coupling.

    A real SQLAlchemy ``Session`` (the only kind ``Depends(get_db)`` supplies in
    production) always exposes ``get_bind()`` and therefore always receives the
    chained ``audit_logs`` row in the SAME transaction as the merge.  Lightweight
    unit-test doubles do not wrap a DBAPI connection; for those we still emit an
    explicit audit log line (so an identity change is never silent) and warn that
    no durable row was written.  This is a test-only degradation, never a
    production path.
    """
    logger.info(
        "%s audit actor=%s role=%s lab=%s resource=%s details=%s",
        action,
        getattr(current_user, "id", None),
        getattr(current_user, "role", None),
        getattr(current_user, "lab_id", None),
        resource_id,
        details,
    )
    if not hasattr(db, "get_bind"):
        logger.warning(
            "%s audit: session has no get_bind() (unit-test double); no durable audit row written",
            action,
        )
        return
    log_action(
        db,
        action=action,
        resource_type="canonical_patient",
        resource_id=resource_id,
        user_id=getattr(current_user, "id", None),
        user_role=getattr(current_user, "role", None),
        lab_id=getattr(current_user, "lab_id", None),
        details=details,
    )


# ── Schemas ──


class CanonicalPatientCreate(BaseModel):
    lab_id: int | None = None
    national_id_hash: str | None = None
    health_id: str | None = None
    full_name: str = Field(..., min_length=1, max_length=300)
    full_name_ar: str | None = None
    date_of_birth: datetime | None = None
    gender: str | None = Field(default=None, pattern=r"^[MFmf]$")
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    province: str | None = None
    district: str | None = None
    blood_type: str | None = None
    source_system: str | None = None
    source_id: str | None = None


class CanonicalPatientResponse(BaseModel):
    id: int
    lab_id: int | None = None
    national_id_hash: str | None = None
    health_id: str | None = None
    full_name: str
    full_name_ar: str | None = None
    date_of_birth: datetime | None = None
    gender: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    province: str | None = None
    district: str | None = None
    blood_type: str | None = None
    mpi_score: float | None = None
    is_verified: bool = False
    is_deceased: bool = False
    source_system: str | None = None
    source_id: str | None = None
    version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CanonicalPatientMerge(BaseModel):
    target_id: int = Field(..., ge=1)
    source_id: int = Field(..., ge=1)


class MergeResult(BaseModel):
    target_id: int
    source_id: int
    detail: str


class LinkPatientRequest(BaseModel):
    patient_id: int = Field(..., ge=1)
    canonical_id: int = Field(..., ge=1)
    method: str = "manual"
    confidence: float | None = None


class LinkCitizenRequest(BaseModel):
    citizen_id: int = Field(..., ge=1)
    canonical_id: int = Field(..., ge=1)
    method: str = "manual"
    confidence: float | None = None


class LinkResponse(BaseModel):
    id: int
    link_type: str
    linked_id: int
    canonical_id: int
    method: str
    confidence: float | None = None
    created_at: datetime | None = None


class SearchResponse(BaseModel):
    total: int
    items: list[CanonicalPatientResponse]


# ── POST / ──


@router.post("", response_model=CanonicalPatientResponse, status_code=201)
def create_canonical(
    data: CanonicalPatientCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CanonicalPatientResponse:
    canonical = CanonicalPatient(**data.model_dump())
    db.add(canonical)
    db.commit()
    db.refresh(canonical)
    return canonical


# ── GET /{id} ──


@router.get("/{canonical_id}", response_model=CanonicalPatientResponse)
def get_canonical(
    canonical_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CanonicalPatientResponse:
    canonical = db.query(CanonicalPatient).filter(CanonicalPatient.id == canonical_id).first()
    if canonical is None:
        raise HTTPException(status_code=404, detail="canonical patient not found")
    return canonical


# ── POST /merge ──


@router.post("/merge", response_model=MergeResult)
def merge(
    data: CanonicalPatientMerge,
    current_user: LabUser = Depends(
        require_role("master_admin", "ministry_admin", "admin", "lab_admin")
    ),
    db: Session = Depends(get_db),
) -> MergeResult:
    """Merge two canonical patient records.

    SECURITY (F-067 / D-023, Phase G): previously this endpoint accepted any
    authenticated user and performed no tenant check — a non-admin could link
    or overwrite patient identity records across labs. Admin role is required
    (mirrors the authoritative MPI manual-merge policy), both records must exist,
    must belong to the same lab, and non-platform roles are additionally bound
    to their own lab. All merges are audit-logged.
    """
    target = db.query(CanonicalPatient).filter(CanonicalPatient.id == data.target_id).first()
    source = db.query(CanonicalPatient).filter(CanonicalPatient.id == data.source_id).first()
    if target is None or source is None:
        raise HTTPException(status_code=404, detail="canonical patient not found")

    # Tenant isolation: never merge across labs.
    if target.lab_id != source.lab_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "cross_lab_merge_denied",
                "message": "Cannot merge patient records from different laboratories.",
                "message_ar": "لا يمكن دمج سجلات مرضى من مختبرات مختلفة.",
            },
        )
    # Non-platform roles (if the role dependency is ever widened) stay lab-bound.
    if target.lab_id is not None:
        require_own_lab(current_user, target.lab_id)

    from sqlalchemy.exc import SQLAlchemyError

    try:
        merge_canonicals(db, target_id=data.target_id, source_id=data.source_id)
        # AUD-12: a chained audit row, not just a log line, and in the SAME
        # transaction as the merge (rolled back together on failure).
        _write_canonical_audit(
            db,
            current_user,
            action="canonical_merge",
            resource_id=data.target_id,
            details={
                "target_id": data.target_id,
                "source_id": data.source_id,
                "target_lab_id": target.lab_id,
            },
        )
        db.commit()
    except (ConflictError, NotFoundError):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        # Commit ambiguity (DB committed, ack lost) must not be reported as a
        # clean success; translate to 503 without deleting the audit evidence.
        db.rollback()
        raise HTTPException(
            status_code=503, detail="Canonical merge could not be committed"
        ) from exc
    logger.info(
        "canonical_merge actor=%s role=%s lab=%s target=%s source=%s",
        getattr(current_user, "id", "unknown"), getattr(current_user, "role", "unknown"),
        target.lab_id, data.target_id, data.source_id,
    )
    return MergeResult(
        target_id=data.target_id,
        source_id=data.source_id,
        detail="canonical records merged successfully",
    )


# ── GET /by-patient/{patient_id} ──


@router.get("/by-patient/{patient_id}", response_model=CanonicalPatientResponse)
def get_by_patient(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CanonicalPatientResponse:
    canonical = get_canonical_by_patient(db, patient_id)
    if canonical is None:
        raise HTTPException(status_code=404, detail="no canonical record linked to this patient")
    return canonical


# ── GET /by-citizen/{citizen_id} ──


@router.get("/by-citizen/{citizen_id}", response_model=CanonicalPatientResponse)
def get_by_citizen(
    citizen_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CanonicalPatientResponse:
    canonical = get_canonical_by_citizen(db, citizen_id)
    if canonical is None:
        raise HTTPException(status_code=404, detail="no canonical record linked to this citizen")
    return canonical


# ── GET /search ──


@router.get("", response_model=SearchResponse)
def search_canonical(
    q: str | None = Query(default=None, max_length=200),
    province: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchResponse:
    base = db.query(CanonicalPatient)

    if q:
        like = f"%{q}%"
        base = base.filter(
            or_(
                CanonicalPatient.full_name.ilike(like),
                CanonicalPatient.full_name_ar.ilike(like),
                CanonicalPatient.phone.ilike(like),
                CanonicalPatient.national_id_hash.ilike(like),
                CanonicalPatient.health_id.ilike(like),
            ),
        )

    if province:
        base = base.filter(CanonicalPatient.province == province)

    total = base.count()
    items = (
        base.order_by(CanonicalPatient.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return SearchResponse(total=total, items=items)


# ── POST /link-patient ──


@router.post("/link-patient", response_model=LinkResponse)
def create_patient_link(
    data: LinkPatientRequest,
    current_user: LabUser = Depends(require_link_actor()),
    db: Session = Depends(get_db),
) -> LinkResponse:
    """Link a LIMS patient to a canonical identity (AUD-02 hardened).

    The caller must be an institutional admin, must own the patient's lab and
    (when the canonical is lab-scoped) the canonical's lab.  A patient already
    linked to a different canonical is a 409 conflict, not a silent duplicate.
    """
    from sqlalchemy.exc import SQLAlchemyError

    patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="patient not found")
    require_own_lab(current_user, patient.lab_id)

    canonical = (
        db.query(CanonicalPatient).filter(CanonicalPatient.id == data.canonical_id).first()
    )
    if canonical is None:
        raise HTTPException(status_code=404, detail="canonical patient not found")
    if canonical.lab_id is not None:
        require_own_lab(current_user, canonical.lab_id)

    try:
        link = link_patient(
            db,
            patient_id=data.patient_id,
            canonical_id=data.canonical_id,
            method=data.method,
            confidence=data.confidence,
        )
        _write_canonical_audit(
            db,
            current_user,
            action="canonical_link_patient",
            resource_id=link.id,
            details={
                "patient_id": link.patient_id,
                "canonical_id": link.canonical_id,
                "lab_id": patient.lab_id,
            },
        )
        db.commit()
    except ConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=exc.message) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=503, detail="Canonical link could not be committed"
        ) from exc

    return LinkResponse(
        id=link.id,
        link_type="patient",
        linked_id=link.patient_id,
        canonical_id=link.canonical_id,
        method=link.linkage_method,
        confidence=link.confidence,
        created_at=link.created_at,
    )


# ── POST /link-citizen ──


@router.post("/link-citizen", response_model=LinkResponse)
def create_citizen_link(
    data: LinkCitizenRequest,
    current_user: LabUser = Depends(require_link_actor()),
    db: Session = Depends(get_db),
) -> LinkResponse:
    """Link a national citizen to a canonical identity (AUD-02 hardened).

    Citizens are national (no lab), so lab authority is derived from the
    lab-scoped canonical.  One canonical link per citizen; conflicts are 409.
    """
    from sqlalchemy.exc import SQLAlchemyError

    citizen = db.query(Citizen).filter(Citizen.id == data.citizen_id).first()
    if citizen is None:
        raise HTTPException(status_code=404, detail="citizen not found")

    canonical = (
        db.query(CanonicalPatient).filter(CanonicalPatient.id == data.canonical_id).first()
    )
    if canonical is None:
        raise HTTPException(status_code=404, detail="canonical patient not found")
    if canonical.lab_id is not None:
        require_own_lab(current_user, canonical.lab_id)

    try:
        link = link_citizen(
            db,
            citizen_id=data.citizen_id,
            canonical_id=data.canonical_id,
            method=data.method,
            confidence=data.confidence,
        )
        _write_canonical_audit(
            db,
            current_user,
            action="canonical_link_citizen",
            resource_id=link.id,
            details={
                "citizen_id": link.citizen_id,
                "canonical_id": link.canonical_id,
            },
        )
        db.commit()
    except ConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=exc.message) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=503, detail="Canonical link could not be committed"
        ) from exc

    return LinkResponse(
        id=link.id,
        link_type="citizen",
        linked_id=link.citizen_id,
        canonical_id=link.canonical_id,
        method=link.linkage_method,
        confidence=link.confidence,
        created_at=link.created_at,
    )
