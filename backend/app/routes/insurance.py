from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..gateways.insurance_gateway import check_insurance
from ..models.lab_user import LabUser
from ..security.dependencies import require_permission
from ..services.audit_service import log_action

router = APIRouter(tags=["insurance"])


@router.get("/insurance/{insurance_id}")
def insurance(
    insurance_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(require_permission("patients:read")),
):
    if not insurance_id or len(insurance_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid insurance ID")
    result = check_insurance(insurance_id)
    log_action(
        db,
        action="insurance_lookup",
        resource_type="insurance",
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Insurance lookup for {insurance_id}",
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return result
