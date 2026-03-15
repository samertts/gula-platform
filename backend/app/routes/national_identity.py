from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..gateways.national_identity_gateway import verify_national_id

router = APIRouter()


class NationalIdRequest(BaseModel):
    national_id: str


@router.post("/national-id/verify")
def verify(data: NationalIdRequest):
    if not data.national_id or len(data.national_id) < 5:
        raise HTTPException(status_code=400, detail="Invalid national ID")
    return verify_national_id(data.national_id)
