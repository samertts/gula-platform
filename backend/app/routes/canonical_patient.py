from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.canonical_patient import CanonicalPatient
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services.mpi.canonical_service import (
    get_canonical_by_citizen,
    get_canonical_by_patient,
    link_citizen,
    link_patient,
    merge_canonicals,
)
from ..services.mpi.scope import (
    not_found,
    provenance_lab_id,
    require_national_scope,
    require_own_patient,
    visible_canonical,
)

router = APIRouter(prefix="/api/v1/canonical-patients", tags=["canonical-patients"])


# ── Schemas ──


class CanonicalPatientCreate(BaseModel):
    """NR-148: this carries no lab_id.

    It used to, and `CanonicalPatient(**data.model_dump())` wrote it straight
    onto the record, so a laboratory could file a canonical patient under
    another laboratory's name. lab_id on this table is PROVENANCE — which lab
    contributed the record — and provenance the client chooses is not
    provenance. It is now taken from the authenticated caller.
    """

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
    canonical = CanonicalPatient(
        **data.model_dump(),
        lab_id=provenance_lab_id(current_user),
    )
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
    # NR-148. A laboratory sees a canonical record it is connected to — one it
    # contributed, or one linked to a patient of its own. A national role sees
    # the index. Anything else reads as absent rather than forbidden, so this
    # does not become an existence oracle over the national population.
    canonical = visible_canonical(db, canonical_id, current_user)
    if canonical is None:
        raise not_found()
    return canonical


# ── POST /merge ──


@router.post("/merge", response_model=MergeResult)
def merge(
    data: CanonicalPatientMerge,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MergeResult:
    # NR-148. Merging declares that two records are the same person. It is a
    # national identity judgement, not a laboratory one, and it was reachable
    # by any authenticated user.
    require_national_scope(current_user, "merging canonical records")
    merge_canonicals(db, target_id=data.target_id, source_id=data.source_id)
    db.commit()
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
    # NR-148. Resolving YOUR patient to their canonical record is the MPI
    # working as intended; resolving someone else's is not.
    require_own_patient(db, patient_id, current_user)
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
    # NR-148. A citizen is a national subject; a laboratory has no standing to
    # resolve one it has not been given.
    require_national_scope(current_user, "resolving a citizen")
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
    # NR-148. This searches the whole national index by name, phone or
    # national-id hash. It was open to every authenticated user, including a
    # technician at a single private laboratory.
    require_national_scope(current_user, "searching the patient index")
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
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LinkResponse:
    # NR-148. Without this a laboratory could attach ANOTHER laboratory's
    # patient to any canonical person — writing a false identity claim into
    # the national index under someone else's name.
    require_own_patient(db, data.patient_id, current_user)
    if visible_canonical(db, data.canonical_id, current_user) is None:
        raise not_found()
    link = link_patient(
        db,
        patient_id=data.patient_id,
        canonical_id=data.canonical_id,
        method=data.method,
        confidence=data.confidence,
    )
    db.commit()
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
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LinkResponse:
    # NR-148. Binding a national citizen to a canonical person is a national
    # identity assertion.
    require_national_scope(current_user, "linking a citizen")
    link = link_citizen(
        db,
        citizen_id=data.citizen_id,
        canonical_id=data.canonical_id,
        method=data.method,
        confidence=data.confidence,
    )
    db.commit()
    return LinkResponse(
        id=link.id,
        link_type="citizen",
        linked_id=link.citizen_id,
        canonical_id=link.canonical_id,
        method=link.linkage_method,
        confidence=link.confidence,
        created_at=link.created_at,
    )
