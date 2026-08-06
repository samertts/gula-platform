from platform.api.dependencies.container import get_result_service
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


@router.post("/")
async def create_result(
    data: dict[str, Any],
    result_service=Depends(get_result_service),
) -> dict[str, Any]:
    try:
        result = await result_service.create(
            order_id=data.get("order_id", ""),
            test_type_id=data.get("test_type_id", ""),
            value=data.get("value", ""),
            lab_id=data.get("lab_id", ""),
            performed_by=data.get("performed_by", ""),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/by-order/{order_id}")
async def get_results_by_order(
    order_id: str,
    result_service=Depends(get_result_service),
) -> list[dict[str, Any]]:
    return await result_service.get_by_order(order_id)
