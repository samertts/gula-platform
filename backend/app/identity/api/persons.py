from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.services.person_service import PersonService

router = APIRouter(prefix="/persons", tags=["NIAM Persons"])


@router.post("/")
async def create_person(
    given_name: str,
    family_name: str,
    middle_name: Optional[str] = None,
    full_name_ar: Optional[str] = None,
    gender: Optional[str] = None,
    birth_date: Optional[date] = None,
    nationality: str = "IRQ",
    email: Optional[str] = None,
    phone: Optional[str] = None,
    national_id_hash: Optional[str] = None,
    health_id: Optional[str] = None,
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
    db: AsyncSession = Depends(get_db),
):
    service = PersonService(db)
    person = await service.get_person_by_uuid(person_uuid)
    if not person:
        return {"error": "not_found"}
    return {"uuid": person.uuid, "given_name": person.given_name, "family_name": person.family_name}
