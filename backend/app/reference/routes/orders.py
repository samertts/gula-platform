from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.reference.infrastructure.dependencies import get_order_service
from app.reference.services import (
    DomainError,
    InvalidOrderError,
    LabOrderDomain,
    OrderNotFoundError,
    PatientNotFoundError,
    Priority,
)
from app.reference.services.order_service import OrderService

router = APIRouter(prefix="/reference/orders", tags=["reference-orders"])


@router.post("")
async def create_order(
    patient_id: str = Query(..., description="معرف المريض"),
    lab_id: str = Query(..., description="معرف المختبر"),
    test_type: str = Query(..., description="نوع الفحص"),
    priority: Priority | None = Query(None, description="الأولوية"),
    notes: str = Query("", description="ملاحظات"),
    service: OrderService = Depends(get_order_service),
) -> dict:
    order = LabOrderDomain(
        patient_id=patient_id,
        lab_id=lab_id,
        test_type=test_type,
        priority=priority or Priority.ROUTINE,
        notes=notes,
    )
    try:
        created = await service.create_order(order)
    except (InvalidOrderError, PatientNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _order_to_response(created)


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    service: OrderService = Depends(get_order_service),
) -> dict:
    try:
        order = await service.get_order(order_id)
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return _order_to_response(order)


def _order_to_response(order: LabOrderDomain) -> dict:
    return {
        "order_id": order.order_id,
        "patient_id": order.patient_id,
        "lab_id": order.lab_id,
        "test_type": order.test_type,
        "status": order.status.value,
        "priority": order.priority.value,
        "notes": order.notes,
        "created_at": (
            order.created_at.isoformat() if order.created_at else None
        ),
        "updated_at": (
            order.updated_at.isoformat() if order.updated_at else None
        ),
        "performed_by": order.performed_by,
    }
