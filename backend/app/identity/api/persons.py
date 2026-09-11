from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.services.person_service import PersonService

router = APIRouter(prefix="/persons", tags=["NIAM Persons"])


@router.post("/")
def create_person(
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
    db: Session = Depends(get_db),
):
    service = PersonService(db)
    person = service.create_person(
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
def get_person(
    person_uuid: str,
    db: Session = Depends(get_db),
):
    service = PersonService(db)
    person = service.get_person_by_uuid(person_uuid)
    if not person:
        return {"error": "not_found"}
    return {"uuid": person.uuid, "given_name": person.given_name, "family_name": person.family_name}
