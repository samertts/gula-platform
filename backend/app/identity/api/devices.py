from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.services.device_service import DeviceService

router = APIRouter(prefix="/devices", tags=["NIAM Devices"])


@router.post("/register")
def register_device(
    person_uuid: str,
    device_fingerprint: str,
    device_name: str | None = None,
    device_type: str | None = None,
    ip_address: str | None = None,
    db: Session = Depends(get_db),
):
    service = DeviceService(db)
    device = service.register_device(
        person_id=person_uuid,
        device_fingerprint=device_fingerprint,
        device_name=device_name,
        device_type=device_type,
        ip_address=ip_address,
    )
    return {"uuid": device.uuid, "id": device.id}


@router.post("/{device_uuid}/trust")
def trust_device(
    device_uuid: str,
    db: Session = Depends(get_db),
):
    service = DeviceService(db)
    device = service.repo.get_by_uuid(device_uuid)
    if not device:
        return {"error": "not_found"}
    service.trust_device(device.id)
    return {"success": True}


@router.post("/{device_uuid}/revoke")
def revoke_device(
    device_uuid: str,
    db: Session = Depends(get_db),
):
    service = DeviceService(db)
    device = service.repo.get_by_uuid(device_uuid)
    if not device:
        return {"error": "not_found"}
    service.revoke_device(device.id)
    return {"success": True}
