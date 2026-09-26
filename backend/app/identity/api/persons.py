"""NIAM person records.

A Person carries national identity PII — national_id_hash, health_id, birth date,
email and phone. Both routes here are behind ``get_current_niam_actor``, the same
actor dependency the rest of the NIAM API uses (memberships, consents, security,
workspaces). They previously had no authentication dependency at all, so any caller
who could reach the service could create a national identity record or read one by
UUID.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.services.person_service import PersonService

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
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
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
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    service = PersonService(db)
    person = await service.get_person_by_uuid(person_uuid)
    if not person:
        # Was returned as a 200 with an error body, which reads as success to every
        # client and to any monitoring that only checks status codes.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return {"uuid": person.uuid, "given_name": person.given_name, "family_name": person.family_name}
