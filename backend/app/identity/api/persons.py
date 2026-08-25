from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.models.audit import AuditAction
from app.identity.services.audit_service import AuditService
from app.identity.services.person_service import PersonService

from .ownership import require_actor_person, require_person_provisioning_actor
from .workspaces import NiamActor, get_current_niam_actor

router = APIRouter(prefix="/persons", tags=["NIAM Persons"])


@router.post("/")
async def create_person(
    given_name: str = Query(..., min_length=1, max_length=100),
    family_name: str = Query(..., min_length=1, max_length=100),
    middle_name: str | None = Query(default=None, max_length=100),
    full_name_ar: str | None = Query(default=None, max_length=300),
    gender: str | None = Query(default=None, max_length=20),
    birth_date: date | None = Query(default=None),
    nationality: str = Query(default="IRQ", min_length=2, max_length=3),
    email: str | None = Query(default=None, max_length=200),
    phone: str | None = Query(default=None, max_length=30),
    national_id_hash: str | None = Query(default=None, max_length=255),
    health_id: str | None = Query(default=None, max_length=100),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    await require_person_provisioning_actor(db, actor)
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
    await AuditService(db).record(
        AuditAction.person_created,
        actor_id=actor.account.id,
        actor_type="account",
        target_type="person",
        target_id=person.uuid,
        session_id=actor.session.uuid,
    )
    return {"uuid": person.uuid, "id": person.id}


@router.get("/{person_uuid}")
async def get_person(
    person_uuid: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    person = await require_actor_person(db, actor, person_uuid)
    return {"uuid": person.uuid, "given_name": person.given_name, "family_name": person.family_name}
