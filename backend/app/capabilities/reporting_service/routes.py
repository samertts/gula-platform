from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.security.dependencies import get_current_user

router = APIRouter(prefix="/reporting-service", tags=["Reporting Service"])


@router.get("/")
async def list_reporting_service(
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"items": [], "total": 0, "skip": skip, "limit": limit}


@router.get("/{id}")
async def get_reporting_service(
    id: str,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"id": id}


@router.post("/")
async def create_reporting_service(
    data: dict,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"success": True, "id": ""}


@router.put("/{id}")
async def update_reporting_service(
    id: str,
    data: dict,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"success": True}


@router.delete("/{id}")
async def delete_reporting_service(
    id: str,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"success": True}
