from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.services.person_service import PersonService

from .workspaces import NiamActor, get_current_niam_actor

router = APIRouter(prefix="/persons", tags=["NIAM Persons"])


@router.post("/")
async def create_person(
    given_name: str,
    family_name: str,
    middle_name: str | None = None,
    full_name_ar: str | None = None,
    gender: str | None = None,
    birth_date: date | None = None,
    nationality: str = "IRQ",
    email: str | None = None,
    phone: str | None = None,
    national_id_hash: str | None = None,
    health_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    actor: NiamActor = Depends(get_current_niam_actor),
):
    # Defense in depth: the parent router also requires this dependency, but
    # the handler must remain safe if it is ever mounted elsewhere.
    del actor
    service = PersonService(db)
    person = await service.create_person(
        given_name=given_name,
        family_name=family_name,
        middle_name=middle_name,
        full_name_ar=full_name_ar,
        gender=gender,
        birth_date=birth_date,
        nationality=nationality,
        email=email,
        phone=phone,
        national_id_hash=national_id_hash,
        health_id=health_id,
    )
    return {"uuid": person.uuid, "id": person.id}


@router.get("/{person_uuid}")
async def get_person(
    person_uuid: str,
    db: AsyncSession = Depends(get_db),
    actor: NiamActor = Depends(get_current_niam_actor),
):
    del actor
    service = PersonService(db)
    person = await service.get_person_by_uuid(person_uuid)
    if not person:
        # A 200 with {"error": "not_found"} made misses indistinguishable
        # from successful reads for callers and monitoring.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return {"uuid": person.uuid, "given_name": person.given_name, "family_name": person.family_name}
