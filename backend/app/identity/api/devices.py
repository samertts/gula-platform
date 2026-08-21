from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.models.device import Device
from app.identity.models.identity import IdentityRecord
from app.identity.models.person import Person
from app.identity.services.device_service import DeviceOwnershipError, DeviceService
from app.security.rate_limit import get_client_ip

router = APIRouter(prefix="/devices", tags=["NIAM Devices"])


async def _person_for_actor(db: AsyncSession, actor: NiamActor, person_uuid: str) -> Person | None:
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
    return result.scalar_one_or_none()


async def _owned_device(
    service: DeviceService,
    actor: NiamActor,
    device_uuid: str,
) -> Device | None:
    device = await service.repo.get_by_uuid(device_uuid)
    if device is None or str(device.account_id) != str(actor.account.id):
        return None
    return device


@router.post("/register")
async def register_device(
    person_uuid: str,
    device_fingerprint: str,
    request: Request,
    actor: NiamActor = Depends(get_current_niam_actor),
    device_name: str | None = None,
    device_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    person = await _person_for_actor(db, actor, person_uuid)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    service = DeviceService(db)
    try:
        device = await service.register_device(
            person_id=person.id,
            account_id=actor.account.id,
            device_fingerprint=device_fingerprint,
            device_name=device_name,
            device_type=device_type,
            ip_address=get_client_ip(request),
        )
    except DeviceOwnershipError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device fingerprint is already registered to another account",
        ) from None
    await db.commit()
    return {"uuid": device.uuid, "id": device.id}


@router.post("/{device_uuid}/trust")
async def trust_device(
    device_uuid: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    service = DeviceService(db)
    device = await _owned_device(service, actor, device_uuid)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    await service.trust_device(device.id)
    await db.commit()
    return {"success": True}


@router.post("/{device_uuid}/revoke")
async def revoke_device(
    device_uuid: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    service = DeviceService(db)
    device = await _owned_device(service, actor, device_uuid)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    await service.revoke_device(device.id)
    await db.commit()
    return {"success": True}
