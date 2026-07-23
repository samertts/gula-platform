from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.services.device_service import DeviceService

router = APIRouter(prefix="/devices", tags=["NIAM Devices"])


@router.post("/register")
async def register_device(
    person_uuid: str,
    device_fingerprint: str,
    device_name: Optional[str] = None,
    device_type: Optional[str] = None,
    ip_address: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    service = DeviceService(db)
    device = await service.register_device(
        person_id=person_uuid,
        device_fingerprint=device_fingerprint,
        device_name=device_name,
        device_type=device_type,
        ip_address=ip_address,
    )
    return {"uuid": device.uuid, "id": device.id}


@router.post("/{device_uuid}/trust")
async def trust_device(
    device_uuid: str,
    db: AsyncSession = Depends(get_db),
):
    service = DeviceService(db)
    device = await service.repo.get_by_uuid(device_uuid)
    if not device:
        return {"error": "not_found"}
    result = await service.trust_device(device.id)
    return {"success": True}


@router.post("/{device_uuid}/revoke")
async def revoke_device(
    device_uuid: str,
    db: AsyncSession = Depends(get_db),
):
    service = DeviceService(db)
    device = await service.repo.get_by_uuid(device_uuid)
    if not device:
        return {"error": "not_found"}
    result = await service.revoke_device(device.id)
    return {"success": True}
