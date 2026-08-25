from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.models.audit import AuditAction
from app.identity.services.audit_service import AuditService
from app.identity.services.device_service import DeviceRegistrationConflict, DeviceService

from .ownership import require_actor_device, require_actor_person
from .workspaces import NiamActor, get_current_niam_actor

router = APIRouter(prefix="/devices", tags=["NIAM Devices"])


@router.post("/register")
async def register_device(
    person_uuid: str = Query(..., min_length=1, max_length=36),
    device_fingerprint: str = Query(..., min_length=8, max_length=255),
    device_name: str | None = Query(default=None, max_length=200),
    device_type: str | None = Query(default=None, max_length=50),
    ip_address: str | None = Query(default=None, max_length=45),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    person = await require_actor_person(db, actor, person_uuid)
    service = DeviceService(db)
    try:
        device = await service.register_device(
            person_id=person.id,
            device_fingerprint=device_fingerprint,
            device_name=device_name,
            device_type=device_type,
            ip_address=ip_address,
            account_id=actor.account.id,
        )
    except DeviceRegistrationConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device fingerprint is already registered",
        ) from exc

    await AuditService(db).record(
        AuditAction.credential_created,
        actor_id=actor.account.id,
        actor_type="account",
        target_type="device",
        target_id=device.uuid,
        session_id=actor.session.uuid,
        metadata={"device_type": device_type},
    )
    return {"uuid": device.uuid, "id": device.id}


@router.post("/{device_uuid}/trust")
async def trust_device(
    device_uuid: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    device = await require_actor_device(db, actor, device_uuid)
    service = DeviceService(db)
    trusted = await service.trust_device(device.id)
    if trusted is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Device could not be trusted")
    await AuditService(db).record(
        AuditAction.device_trusted,
        actor_id=actor.account.id,
        actor_type="account",
        target_type="device",
        target_id=device.uuid,
        session_id=actor.session.uuid,
    )
    return {"success": True}


@router.post("/{device_uuid}/revoke")
async def revoke_device(
    device_uuid: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    device = await require_actor_device(db, actor, device_uuid)
    service = DeviceService(db)
    revoked = await service.revoke_device(device.id)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Device could not be revoked")
    await AuditService(db).record(
        AuditAction.device_revoked,
        actor_id=actor.account.id,
        actor_type="account",
        target_type="device",
        target_id=device.uuid,
        session_id=actor.session.uuid,
    )
    return {"success": True}
