"""Batch operations - process multiple orders/results efficiently."""

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..models.patient import Patient
from ..security.dependencies import get_current_user
from ..security.rate_limit import get_client_ip
from ..services import idempotency
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
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create multiple orders at once.

    Idempotency is claimed for the batch as a whole, because the batch is one
    HTTP request: a retry after a timeout must reproduce the same outcome for
    all of it, including the per-item `errors`. Claiming per item instead would
    leave the caller unable to retry the request they actually sent.

    This is why `create_order` below is still called with
    `idempotency_key=None` -- not because the items are unprotected, but
    because the envelope around them already is, and a second claim per item
    would refuse the replay this one is serving.
    """
    if len(data.orders) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 orders per batch")

    idem = idempotency.begin(
        scope="batch-orders",
        tenant_id=current_user.lab_id,
        key=idempotency_key,
        payload=data.model_dump(mode="json"),
    )
    if idem.conflict:
        raise HTTPException(status_code=idem.conflict["status_code"], detail=idem.conflict["error"])
    if idem.replay is not None:
        return idem.replay

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
            # Covered by the batch-level claim above; see the docstring.
            idempotency_key=None,
        )

        order_critical = result.get("critical_alerts")
        created_orders.append(
            {
                "order_id": result["order"]["id"],
                "patient_id": order_data.patient_id,
                "results_count": len(order_data.results),
                "critical_count": len(order_critical) if order_critical else 0,
            },
        )
        if order_critical:
            all_critical_alerts.extend(order_critical)

    db.commit()

    total_critical = sum(o["critical_count"] for o in created_orders)
    response = {
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
        "critical_alerts": all_critical_alerts or None,
    }
    idem.complete(response)
    return response
