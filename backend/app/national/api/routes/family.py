from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.domain.family import Family, FamilyMember
from app.security.dependencies import get_current_user, require_permission
from app.services.route_audit import audit_mutation

router = APIRouter(prefix="/families", tags=["Family Registry"], dependencies=[Depends(require_permission("patients:read"))])


class FamilyCreate(BaseModel):
    family_id_hash: str | None = None
    family_name: str | None = None
    governorate: str | None = None
    address: str | None = None


class FamilyMemberAdd(BaseModel):
    citizen_id: str
    relationship: str
    is_primary: bool = False


class FamilyResponse(BaseModel):
    id: str
    family_id_hash: str | None = None
    family_name: str | None = None
    member_count: int = 0
    created_at: str = ""


class FamilyMemberResponse(BaseModel):
    citizen_id: str
    relationship: str
    is_primary: bool = False


@router.post("/", response_model=FamilyResponse, status_code=201, dependencies=[Depends(require_permission("patients:write"))])
async def create_family(
    data: FamilyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    family = Family(
        family_id_hash=data.family_id_hash,
        family_name=data.family_name,
        governorate=data.governorate,
        address=data.address,
    )
    db.add(family)
    db.flush()
    audit_mutation(
        db,
        action="national.family.create",
        resource_type="Family",
        resource_id=family.id,
        user=current_user,
        before=None,
        after={"family_id_hash_present": bool(family.family_id_hash), "governorate": family.governorate},
    )
    db.commit()
    db.refresh(family)
    return FamilyResponse(
        id=family.id,
        family_id_hash=family.family_id_hash,
        family_name=family.family_name,
        created_at=family.created_at.isoformat() if family.created_at else "",
    )


@router.get("/{family_id}", response_model=FamilyResponse)
async def get_family(
    family_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family or family.is_deleted:
        raise HTTPException(status_code=404, detail="Family not found")
    return FamilyResponse(
        id=family.id,
        family_id_hash=family.family_id_hash,
        family_name=family.family_name,
        created_at=family.created_at.isoformat() if family.created_at else "",
    )


@router.post("/{family_id}/members", response_model=FamilyMemberResponse, status_code=201, dependencies=[Depends(require_permission("patients:write"))])
async def add_family_member(
    family_id: str,
    data: FamilyMemberAdd,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family or family.is_deleted:
        raise HTTPException(status_code=404, detail="Family not found")
    member = FamilyMember(
        family_id=family_id,
        citizen_id=data.citizen_id,
        relationship=data.relationship,
        is_primary=data.is_primary,
    )
    db.add(member)
    db.flush()
    audit_mutation(
        db,
        action="national.family.member.add",
        resource_type="FamilyMember",
        resource_id=member.id,
        user=current_user,
        before=None,
        after={"family_id": family_id, "citizen_id": member.citizen_id, "relationship": member.relationship, "is_primary": member.is_primary},
    )
    db.commit()
    db.refresh(member)
    return FamilyMemberResponse(
        citizen_id=member.citizen_id,
        relationship=member.relationship,
        is_primary=member.is_primary,
    )


@router.delete("/{family_id}/members/{member_id}", status_code=204, response_model=None, dependencies=[Depends(require_permission("patients:write"))])
async def remove_family_member(
    family_id: str,
    member_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.family_id == family_id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")
    before = {"family_id": member.family_id, "citizen_id": member.citizen_id, "relationship": member.relationship, "is_primary": member.is_primary}
    db.delete(member)
    audit_mutation(
        db,
        action="national.family.member.delete",
        resource_type="FamilyMember",
        resource_id=member_id,
        user=current_user,
        before=before,
        after=None,
    )
    db.commit()
