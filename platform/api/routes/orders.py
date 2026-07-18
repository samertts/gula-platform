from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from platform.api.dependencies.container import get_order_service

router = APIRouter()


@router.post("/")
async def create_order(
    data: dict[str, Any],
    order_service=Depends(get_order_service),
) -> dict[str, Any]:
    try:
        from platform.domain.services.order import OrderData

        od = OrderData(
            patient_id=data.get("patient_id", ""),
            lab_id=data.get("lab_id", ""),
            test_type_ids=data.get("test_type_ids", []),
            doctor_name=data.get("doctor_name", ""),
            notes=data.get("notes", ""),
            priority=data.get("priority", "routine"),
        )
        result = await order_service.create(od)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    order_service=Depends(get_order_service),
) -> dict[str, Any]:
    result = await order_service.get_by_id(order_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return result


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: str,
    data: dict[str, str],
    order_service=Depends(get_order_service),
) -> dict[str, Any]:
    status = data.get("status", "")
    if not status:
        raise HTTPException(status_code=400, detail="Status required")
    result = await order_service.update_status(order_id, status)
    if result is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return result
