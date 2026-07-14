"""Batch operations - process multiple orders/results efficiently."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..models.patient import Patient
from ..security.dependencies import get_current_user
from ..security.rate_limit import get_client_ip
from ..services.order_service import create_order

router = APIRouter(prefix="/batch", tags=["batch"])


class BatchResultItem(BaseModel):
    test_name: str
    value: float | None = None
    value_text: str | None = None
    unit: str | None = None
    normal_range_low: float | None = None
    normal_range_high: float | None = None


class BatchOrderItem(BaseModel):
    patient_id: int
    doctor_name: str | None = None
    results: list[BatchResultItem]


class BatchOrderRequest(BaseModel):
    orders: list[BatchOrderItem]


@router.post("/orders", status_code=201)
def create_batch_orders(
    data: BatchOrderRequest,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create multiple orders at once."""
    if len(data.orders) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 orders per batch")

    # Pre-validate all patient IDs in a single query
    patient_ids = list({o.patient_id for o in data.orders})
    existing_patients = (
        db.query(Patient.id)
        .filter(
            Patient.id.in_(patient_ids),
            Patient.lab_id == current_user.lab_id,
        )
        .all()
    )
    valid_ids = {p.id for p in existing_patients}

    created_orders = []
    errors = []
    all_critical_alerts = []

    for i, order_data in enumerate(data.orders):
        if order_data.patient_id not in valid_ids:
            errors.append({"index": i, "error": f"Patient {order_data.patient_id} not found"})
            continue

        result = create_order(
            db=db,
            lab_id=current_user.lab_id,
            user_id=current_user.id,
            user_role=current_user.role,
            patient_id=order_data.patient_id,
            doctor_name=order_data.doctor_name or "",
            doctor_user_id=None,
            results_data=[
                {
                    "test_name": item.test_name,
                    "value": item.value,
                    "value_text": item.value_text,
                    "unit": item.unit,
                    "normal_range_low": item.normal_range_low,
                    "normal_range_high": item.normal_range_high,
                }
                for item in order_data.results
            ],
            ip_address=get_client_ip(request),
            idempotency_key=None,
        )

        order_critical = result.get("critical_alerts")
        created_orders.append(
            {
                "order_id": result["order"]["id"],
                "patient_id": order_data.patient_id,
                "results_count": len(order_data.results),
                "critical_count": len(order_critical) if order_critical else 0,
            }
        )
        if order_critical:
            all_critical_alerts.extend(order_critical)

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
        "critical_alerts": all_critical_alerts if all_critical_alerts else None,
    }
