from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..gateways.national_identity_gateway import verify_national_id
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
    return verify_national_id(data.national_id)
