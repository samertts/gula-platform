from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_niam_db as get_db
from app.identity.security import get_current_identity

from .services import ProfessionalRegistryService, RegistryError

router = APIRouter(
    prefix="/professional-registry",
    tags=["NIAM Professional Registry"],
    dependencies=[Depends(get_current_identity)],
)


@router.post("/")
async def register_professional(
    person_id: str,
    identity_id: str,
    profession: str,
    registration_number: str,
    issuing_authority: str,
    issued_at: str,
    specialty: str | None = None,
    issuing_authority_id: str | None = None,
    issuing_country: str = "IRQ",
    expires_at: str | None = None,
    license_number: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    from datetime import date

    service = ProfessionalRegistryService(db)
    try:
        entry = await service.register(
            person_id=person_id,
            identity_id=identity_id,
            profession=profession,
            registration_number=registration_number,
            issuing_authority=issuing_authority,
            issued_at=date.fromisoformat(issued_at),
            specialty=specialty,
            issuing_authority_id=issuing_authority_id,
            issuing_country=issuing_country,
            expires_at=date.fromisoformat(expires_at) if expires_at else None,
            license_number=license_number,
        )
    except RegistryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"entry": entry.to_dict()}


@router.get("/{registry_id}")
async def get_entry(registry_id: str, db: AsyncSession = Depends(get_db)):
    service = ProfessionalRegistryService(db)
    entry = await service.get_entry(registry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="entry_not_found")
    return {"entry": entry.to_dict()}


@router.get("/person/{person_id}")
async def list_person_entries(person_id: str, db: AsyncSession = Depends(get_db)):
    service = ProfessionalRegistryService(db)
    entries = await service.list_for_person(person_id)
    return {"entries": [e.to_dict() for e in entries], "count": len(entries)}


@router.post("/{registry_id}/verify")
async def verify_entry(
    registry_id: str,
    verified_by: str,
    verification_method: str = "authority_confirmation",
    db: AsyncSession = Depends(get_db),
):
    service = ProfessionalRegistryService(db)
    try:
        entry = await service.verify(
            registry_id=registry_id,
            verified_by=verified_by,
            verification_method=verification_method,
        )
    except RegistryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"entry": entry.to_dict()}


@router.post("/{registry_id}/suspend")
async def suspend_entry(
    registry_id: str, reason: str, actor: str, db: AsyncSession = Depends(get_db)
):
    service = ProfessionalRegistryService(db)
    try:
        entry = await service.suspend(registry_id, reason, actor)
    except RegistryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"entry": entry.to_dict()}


@router.post("/{registry_id}/revoke")
async def revoke_entry(
    registry_id: str, reason: str, actor: str, db: AsyncSession = Depends(get_db)
):
    service = ProfessionalRegistryService(db)
    try:
        entry = await service.revoke(registry_id, reason, actor)
    except RegistryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"entry": entry.to_dict()}


@router.get("/{person_id}/privileges/check")
async def check_privileges(
    person_id: str, profession: str | None = None, db: AsyncSession = Depends(get_db)
):
    service = ProfessionalRegistryService(db)
    privileged = await service.is_privileged(person_id, profession)
    return {"privileged": privileged, "person_id": person_id, "profession": profession}
