from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.models.identity import IdentityRecord
from app.identity.models.person import Person

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
    _actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    del _actor, db, given_name, family_name, middle_name, full_name_ar, gender, birth_date
    del nationality, email, phone, national_id_hash, health_id
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Direct person creation is disabled. Use an approved account or institutional workflow.",
    )


@router.get("/{person_uuid}")
async def get_person(
    person_uuid: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Person)
        .join(IdentityRecord, IdentityRecord.person_id == Person.id)
        .where(
            Person.uuid == person_uuid,
            Person.is_active.is_(True),
            IdentityRecord.id == actor.account.identity_id,
            IdentityRecord.is_active.is_(True),
        ),
    )
    person = result.scalar_one_or_none()
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")
    return {"uuid": person.uuid, "given_name": person.given_name, "family_name": person.family_name}
