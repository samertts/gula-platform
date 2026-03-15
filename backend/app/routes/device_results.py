"""Lab device integration - receive results from analyzers."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone

from ..database import get_db
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.sample import Sample
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services.interpretation import get_flag
from ..services.audit_service import log_action

router = APIRouter(prefix="/device", tags=["device"])


class DeviceResult(BaseModel):
    test_name: str
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    normal_range_low: Optional[float] = None
    normal_range_high: Optional[float] = None


class DeviceSubmission(BaseModel):
    barcode: str  # sample barcode to match
    device_id: Optional[str] = None
    results: List[DeviceResult]


@router.post("/results")
def receive_device_results(
    data: DeviceSubmission,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Receive results from a lab analyzer device.

    Matches results to an order via sample barcode, creates lab results,
    and updates sample status to 'analyzed'.
    """
    # Find sample by barcode
    sample = db.query(Sample).join(LabOrder).filter(
        Sample.barcode == data.barcode,
        LabOrder.lab_id == current_user.lab_id,
    ).first()
    if not sample:
        raise HTTPException(status_code=404, detail=f"Sample barcode {data.barcode} not found")

    if sample.status == "rejected":
        raise HTTPException(status_code=400, detail="Cannot add results to a rejected sample")

    order = db.query(LabOrder).filter(LabOrder.id == sample.order_id).first()

    created = []
    for item in data.results:
        flag = None
        if item.value is not None and item.normal_range_low is not None and item.normal_range_high is not None:
            flag = get_flag(item.value, item.normal_range_low, item.normal_range_high)

        import secrets
        from ..models.lab_result import hash_token
        token = secrets.token_urlsafe(32)

        result = LabResult(
            order_id=order.id,
            test_name=item.test_name,
            value=item.value,
            value_text=item.value_text,
            unit=item.unit,
            normal_range_low=item.normal_range_low,
            normal_range_high=item.normal_range_high,
            flag=flag,
            token=token,
            token_hash=hash_token(token),
        )
        db.add(result)
        created.append({"test": item.test_name, "token": token})

    # Update sample status
    sample.status = "analyzed"
    order.status = "completed"

    log_action(db, action="device_results", resource_type="lab_order",
               resource_id=order.id, user_id=current_user.id,
               user_role=current_user.role,
               details=f"Device {data.device_id or 'unknown'}: {len(created)} results via barcode {data.barcode}")
    db.commit()

    return {
        "message": f"{len(created)} results added from device",
        "barcode": data.barcode,
        "order_id": order.id,
        "results": created,
    }
