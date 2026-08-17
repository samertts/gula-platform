from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.domain.advance_directive import AdvanceDirective
from app.security.dependencies import get_current_user, require_permission
from app.services.route_audit import audit_mutation

router = APIRouter(prefix="/advance-directives", tags=["Advance Directives"], dependencies=[Depends(require_permission("patients:read"))])


class AdvanceDirectiveCreate(BaseModel):
    patient_id: str
    citizen_id: str | None = None
    directive_type: str
    title: str | None = None
    description: str | None = None
    content: str | None = None
    witness_name: str | None = None
    witness_relationship: str | None = None
    witness_signature: str | None = None
    legal_representative_id: str | None = None
    legal_representative_name: str | None = None
    legal_representative_relationship: str | None = None
    effective_date: datetime | None = None
    expiration_date: datetime | None = None
    document_url: str | None = None
    notes: str | None = None


class AdvanceDirectiveUpdate(BaseModel):
    directive_type: str | None = None
    title: str | None = None
    description: str | None = None
    content: str | None = None
    witness_name: str | None = None
    witness_relationship: str | None = None
    witness_signature: str | None = None
    legal_representative_id: str | None = None
    legal_representative_name: str | None = None
    legal_representative_relationship: str | None = None
    effective_date: datetime | None = None
    expiration_date: datetime | None = None
    document_url: str | None = None
    notes: str | None = None


class AdvanceDirectiveResponse(BaseModel):
    id: str
    patient_id: str
    citizen_id: str | None
    directive_type: str
    status: str
    title: str | None
    description: str | None
    content: str | None
    witness_name: str | None
    witness_relationship: str | None
    witness_signature: str | None
    legal_representative_id: str | None
    legal_representative_name: str | None
    legal_representative_relationship: str | None
    effective_date: datetime | None
    expiration_date: datetime | None
    revoked_at: datetime | None
    revoked_by: str | None
    revocation_reason: str | None
    document_url: str | None
    notes: str | None
    is_deleted: bool
    created_at: datetime | None
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AdvanceDirectiveListResponse(BaseModel):
    items: list[AdvanceDirectiveResponse]
    total: int
    skip: int
    limit: int


def _get_directive_or_404(db: Session, directive_id: str) -> AdvanceDirective:
    directive = db.query(AdvanceDirective).filter(
        AdvanceDirective.id == directive_id,
        ~AdvanceDirective.is_deleted,
    ).first()
    if not directive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Advance directive not found: {directive_id}")
    return directive


@router.post("/", response_model=AdvanceDirectiveResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("patients:write"))])
async def create_advance_directive(
    data: AdvanceDirectiveCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    directive_data = data.model_dump(exclude_none=True)
    directive_data["status"] = "active"
    directive = AdvanceDirective(**directive_data)
    db.add(directive)
    db.flush()
    audit_mutation(
        db,
        action="national.advance_directive.create",
        resource_type="AdvanceDirective",
        resource_id=directive.id,
        user=user,
        after={"patient_id": directive.patient_id, "directive_type": directive.directive_type, "status": directive.status},
    )
    db.commit()
    return directive


@router.get("/{directive_id}", response_model=AdvanceDirectiveResponse)
async def get_advance_directive(
    directive_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return _get_directive_or_404(db, directive_id)


@router.put("/{directive_id}", response_model=AdvanceDirectiveResponse, dependencies=[Depends(require_permission("patients:write"))])
async def update_advance_directive(
    directive_id: str,
    data: AdvanceDirectiveUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    directive = _get_directive_or_404(db, directive_id)
    before = {"directive_type": directive.directive_type, "status": directive.status, "title": directive.title}
    update_data = data.model_dump(exclude_none=True)
    for key, value in update_data.items():
        if hasattr(directive, key):
            setattr(directive, key, value)
    db.flush()
    audit_mutation(
        db,
        action="national.advance_directive.update",
        resource_type="AdvanceDirective",
        resource_id=directive.id,
        user=user,
        before=before,
        after={"directive_type": directive.directive_type, "status": directive.status, "title": directive.title},
    )
    db.commit()
    return directive


@router.delete("/{directive_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, dependencies=[Depends(require_permission("patients:write"))])
async def delete_advance_directive(
    directive_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    directive = _get_directive_or_404(db, directive_id)
    before = {"directive_type": directive.directive_type, "status": directive.status, "is_deleted": directive.is_deleted}
    directive.soft_delete()
    db.flush()
    audit_mutation(
        db,
        action="national.advance_directive.delete",
        resource_type="AdvanceDirective",
        resource_id=directive.id,
        user=user,
        before=before,
        after={"is_deleted": True},
    )
    db.commit()


@router.get("/by-patient/{patient_id}", response_model=AdvanceDirectiveListResponse)
async def get_advance_directives_by_patient(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.query(AdvanceDirective).filter(
        AdvanceDirective.patient_id == patient_id,
        ~AdvanceDirective.is_deleted,
    )
    total = query.count()
    directives = query.order_by(AdvanceDirective.effective_date.desc()).offset(skip).limit(limit).all()
    return AdvanceDirectiveListResponse(items=directives, total=total, skip=skip, limit=limit)


@router.post("/{directive_id}/revoke", response_model=AdvanceDirectiveResponse, dependencies=[Depends(require_permission("patients:write"))])
async def revoke_advance_directive(
    directive_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    directive = _get_directive_or_404(db, directive_id)
    before = {"status": directive.status, "revoked_at": directive.revoked_at.isoformat() if directive.revoked_at else None}
    directive.status = "revoked"
    directive.revoked_at = datetime.now()
    directive.revoked_by = user.id
    db.flush()
    audit_mutation(
        db,
        action="national.advance_directive.revoke",
        resource_type="AdvanceDirective",
        resource_id=directive.id,
        user=user,
        before=before,
        after={"status": directive.status, "revoked_at": directive.revoked_at.isoformat() if directive.revoked_at else None},
    )
    db.commit()
    return directive
