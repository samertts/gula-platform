from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..gateways.mode import AdapterMode
from ..gateways.national_identity_gateway import get_national_identity_gateway, verify_national_id
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user

router = APIRouter()


class NationalIdRequest(BaseModel):
    national_id: str


@router.post("/national-id/verify")
def verify(
    data: NationalIdRequest,
    current_user: LabUser = Depends(get_current_user),
):
    if not data.national_id or len(data.national_id) < 5:
        raise HTTPException(status_code=400, detail="Invalid national ID")
    if len(data.national_id) > 20:
        raise HTTPException(status_code=400, detail="National ID too long")
    gateway = get_national_identity_gateway()
    gateway_mode = gateway.current_mode()
    gateway_mode_value = getattr(gateway_mode, "value", str(gateway_mode)).lower()
    if gateway_mode_value != AdapterMode.LIVE.value:
        raise HTTPException(
            status_code=503,
            detail="National identity verification requires an authorized live provider",
        )
    return verify_national_id(data.national_id)
