"""Citizen registry CRUD endpoints.

Routes:
    POST   /citizens/register            Register a new citizen
    GET    /citizens/search              Search by name / national_id / province
    GET    /citizens/{health_id}         Read a citizen
    PUT    /citizens/{health_id}         Update mutable fields
    GET    /citizens/{health_id}/summary Basic info + last 5 tests + chronic diseases

Every endpoint writes to the audit log via services.audit.log_action.

Route order matters: the static ``/search`` path is declared before the
``/{health_id}`` dynamic path so FastAPI does not treat "search" as a
health_id.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.citizen import Citizen
from ...models.lab_test import LabTest
from ...schemas.citizen import (
    CitizenCreate,
    CitizenRead,
    CitizenSearchResult,
    CitizenSummary,
    CitizenUpdate,
    DuplicateMatch,
    LabTestRead,
)
from ...services.audit import log_action
from ...services.duplicates import DUPLICATE_CONFLICT_THRESHOLD, find_duplicates
from ...services.health_id import generate_health_id

router = APIRouter(prefix="/citizens", tags=["citizens"])


def _actor_id(request: Request) -> str | None:
    """Best-effort actor identifier for audit log entries.

    In the full integration this will read the authenticated user from the
    request; for now we pass through an optional ``X-Actor-Id`` header so the
    endpoints are testable standalone.
    """
    return request.headers.get("X-Actor-Id")


def _client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


# ─── POST /citizens/register ────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=CitizenRead,
    status_code=status.HTTP_201_CREATED,
)
def register_citizen(
    payload: CitizenCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> CitizenRead:
    if payload.national_id:
        clash = (db.query(Citizen)
                   .filter(Citizen.national_id == payload.national_id)
                   .first())
        if clash is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "national_id_exists",
                    "health_id": clash.health_id,
                },
            )

    hits = find_duplicates(
        db,
        full_name=payload.full_name,
        birth_date=payload.birth_date,
        phone=payload.phone,
        mother_name=payload.mother_name,
        national_id=payload.national_id,
    )
    if hits and hits[0].score > DUPLICATE_CONFLICT_THRESHOLD:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "duplicate_candidate",
                "threshold": DUPLICATE_CONFLICT_THRESHOLD,
                "matches": [
                    DuplicateMatch(
                        health_id=h.health_id,
                        full_name=h.full_name,
                        score=h.score,
                        reasons=h.reasons,
                    ).model_dump()
                    for h in hits[:5]
                ],
            },
        )

    citizen = Citizen(
        health_id=generate_health_id(db),
        national_id=payload.national_id,
        full_name=payload.full_name,
        mother_name=payload.mother_name,
        birth_date=payload.birth_date,
        gender=payload.gender,
        phone=payload.phone,
        email=payload.email,
        province=payload.province,
        district=payload.district,
        address=payload.address,
        chronic_diseases=payload.chronic_diseases or [],
        allergies=payload.allergies or [],
        blood_type=payload.blood_type,
    )
    db.add(citizen)
    db.flush()

    log_action(
        db,
        action="citizen.register",
        target_type="citizen",
        target_id=citizen.health_id,
        actor_id=_actor_id(request),
        ip_address=_client_ip(request),
        metadata={"candidates_considered": len(hits)},
    )
    db.commit()
    db.refresh(citizen)
    return CitizenRead.model_validate(citizen)


# ─── GET /citizens/search ───────────────────────────────────────────────────

@router.get("/search", response_model=CitizenSearchResult)
def search_citizens(
    request: Request,
    q:        str | None = Query(default=None, description="Name or national_id substring"),
    province: str | None = Query(default=None, max_length=80),
    skip:     int = Query(0, ge=0),
    limit:    int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> CitizenSearchResult:
    query = db.query(Citizen)
    if q:
        needle = q.strip()
        if needle:
            query = query.filter(or_(
                Citizen.full_name.ilike(f"%{needle}%"),
                Citizen.national_id == needle,
            ))
    if province:
        query = query.filter(Citizen.province == province)

    total = query.count()
    rows  = (query.order_by(desc(Citizen.created_at))
                  .offset(skip).limit(limit).all())

    log_action(
        db,
        action="citizen.search",
        target_type="citizen_collection",
        target_id="-",
        actor_id=_actor_id(request),
        ip_address=_client_ip(request),
        metadata={"q": q, "province": province, "skip": skip, "limit": limit, "total": total},
    )
    db.commit()

    return CitizenSearchResult(
        total=total,
        skip=skip,
        limit=limit,
        items=[CitizenRead.model_validate(r) for r in rows],
    )


# ─── GET /citizens/{health_id}/summary ──────────────────────────────────────

@router.get("/{health_id}/summary", response_model=CitizenSummary)
def citizen_summary(
    health_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> CitizenSummary:
    citizen = db.query(Citizen).filter(Citizen.health_id == health_id).first()
    if citizen is None:
        raise HTTPException(status_code=404, detail="citizen not found")

    recent = (db.query(LabTest)
                .filter(LabTest.citizen_id == citizen.id)
                .order_by(desc(LabTest.performed_at))
                .limit(5)
                .all())

    log_action(
        db,
        action="citizen.summary",
        target_type="citizen",
        target_id=citizen.health_id,
        actor_id=_actor_id(request),
        ip_address=_client_ip(request),
        metadata={"tests_returned": len(recent)},
    )
    db.commit()

    return CitizenSummary(
        citizen=CitizenRead.model_validate(citizen),
        recent_tests=[LabTestRead.model_validate(t) for t in recent],
        chronic_diseases=list(citizen.chronic_diseases or []),
        allergies=list(citizen.allergies or []),
    )


# ─── GET /citizens/{health_id} ──────────────────────────────────────────────

@router.get("/{health_id}", response_model=CitizenRead)
def get_citizen(
    health_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> CitizenRead:
    citizen = db.query(Citizen).filter(Citizen.health_id == health_id).first()
    if citizen is None:
        raise HTTPException(status_code=404, detail="citizen not found")

    log_action(
        db,
        action="citizen.read",
        target_type="citizen",
        target_id=citizen.health_id,
        actor_id=_actor_id(request),
        ip_address=_client_ip(request),
    )
    db.commit()
    return CitizenRead.model_validate(citizen)


# ─── PUT /citizens/{health_id} ──────────────────────────────────────────────

@router.put("/{health_id}", response_model=CitizenRead)
def update_citizen(
    health_id: str,
    payload: CitizenUpdate,
    request: Request,
    db: Session = Depends(get_db),
) -> CitizenRead:
    citizen = db.query(Citizen).filter(Citizen.health_id == health_id).first()
    if citizen is None:
        raise HTTPException(status_code=404, detail="citizen not found")

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="no fields to update")

    for field, value in changes.items():
        setattr(citizen, field, value)

    log_action(
        db,
        action="citizen.update",
        target_type="citizen",
        target_id=citizen.health_id,
        actor_id=_actor_id(request),
        ip_address=_client_ip(request),
        metadata={"fields": sorted(changes.keys())},
    )
    db.commit()
    db.refresh(citizen)
    return CitizenRead.model_validate(citizen)
