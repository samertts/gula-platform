from fastapi import APIRouter, Depends, HTTPException
from ..gateways.insurance_gateway import check_insurance
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user

router = APIRouter(tags=["insurance"])


@router.get("/insurance/{insurance_id}")
def insurance(
    insurance_id: str,
    current_user: LabUser = Depends(get_current_user),
):
    if not insurance_id or len(insurance_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid insurance ID")
    return check_insurance(insurance_id)
