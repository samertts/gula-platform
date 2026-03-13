from fastapi import APIRouter
from ..gateways.national_identity_gateway import verify_national_id

router = APIRouter()

@router.post("/national-id/verify")
def verify(data:dict):

    national_id=data.get("national_id")

    return verify_national_id(national_id)
