from fastapi import APIRouter
from ..gateways.insurance_gateway import check_insurance

router=APIRouter()

@router.get("/insurance/{insurance_id}")

def insurance(insurance_id:str):

    return check_insurance(insurance_id)
