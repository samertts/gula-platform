"""Batch operations - process multiple orders/results efficiently."""
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from ..database import get_db
from ..models.patient import Patient
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult, hash_token
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services.interpretation import get_flag
from ..services.audit_service import log_action
from ..config import BASE_URL

router = APIRouter(prefix="/batch", tags=["batch"])


class BatchResultItem(BaseModel):
    test_name: str
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    normal_range_low: Optional[float] = None
    normal_range_high: Optional[float] = None


class BatchOrderItem(BaseModel):
    patient_id: int
    doctor_name: Optional[str] = None
    results: List[BatchResultItem]


class BatchOrderRequest(BaseModel):
    orders: List[BatchOrderItem]


@router.post("/orders")
def create_batch_orders(
    data: BatchOrderRequest,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create multiple orders at once - significantly faster than individual API calls.
    Useful for end-of-day batch processing or device integration."""
    if len(data.orders) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 orders per batch")

    # Pre-validate all patient IDs in a single query
    patient_ids = list(set(o.patient_id for o in data.orders))
    existing_patients = db.query(Patient.id).filter(
        Patient.id.in_(patient_ids),
        Patient.lab_id == current_user.lab_id,
    ).all()
    valid_ids = {p.id for p in existing_patients}

    created_orders = []
    errors = []

    for i, order_data in enumerate(data.orders):
        if order_data.patient_id not in valid_ids:
            errors.append({"index": i, "error": f"Patient {order_data.patient_id} not found"})
            continue

        order = LabOrder(
            patient_id=order_data.patient_id,
            lab_id=current_user.lab_id,
            doctor_name=order_data.doctor_name,
            status="completed",
        )
        db.add(order)
        db.flush()

        result_count = 0
        critical_count = 0
        for item in order_data.results:
            flag = "unknown"
            if item.value is not None and item.normal_range_low is not None and item.normal_range_high is not None:
                flag = get_flag(item.value, item.normal_range_low, item.normal_range_high)

            token = secrets.token_urlsafe(32)
            token_h = hash_token(token)

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
                token_hash=token_h,
            )
            db.add(result)
            result_count += 1
            if flag == "critical":
                critical_count += 1

        created_orders.append({
            "order_id": order.id,
            "patient_id": order_data.patient_id,
            "results_count": result_count,
            "critical_count": critical_count,
        })

    log_action(
        db,
        action="batch_create",
        resource_type="lab_order",
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Batch created {len(created_orders)} orders with {sum(o['results_count'] for o in created_orders)} results",
        ip_address=request.client.host if request.client else None,
    )

    db.commit()

    total_critical = sum(o["critical_count"] for o in created_orders)
    return {
        "message": f"Batch processed: {len(created_orders)} orders created",
        "message_ar": f"تمت المعالجة الدفعية: تم إنشاء {len(created_orders)} طلب",
        "created": created_orders,
        "errors": errors,
        "summary": {
            "total_orders": len(created_orders),
            "total_results": sum(o["results_count"] for o in created_orders),
            "total_critical": total_critical,
            "errors": len(errors),
        },
        "critical_alert": total_critical > 0,
    }
