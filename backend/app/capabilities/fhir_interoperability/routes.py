from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from backend.app.security.dependencies import get_current_user, require_permission

router = APIRouter(prefix="/fhir-interoperability", tags=["Fhir Interoperability"])


@router.get("/")
async def list_fhir-interoperability(
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"items": [], "total": 0, "skip": skip, "limit": limit}


@router.get("/{id}")
async def get_fhir-interoperability(
    id: str,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"id": id}


@router.post("/")
async def create_fhir-interoperability(
    data: dict,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"success": True, "id": ""}


@router.put("/{id}")
async def update_fhir-interoperability(
    id: str,
    data: dict,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"success": True}


@router.delete("/{id}")
async def delete_fhir-interoperability(
    id: str,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"success": True}
