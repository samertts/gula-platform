from platform.api.dependencies.container import get_lab_service
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


@router.get("/{lab_id}")
async def get_lab(
    lab_id: str,
    lab_service=Depends(get_lab_service),
) -> dict[str, Any]:
    result = await lab_service.get_by_id(lab_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Lab not found")
    return result


@router.get("/")
async def list_labs(
    lab_service=Depends(get_lab_service),
) -> list[dict[str, Any]]:
    return await lab_service.list_active()
