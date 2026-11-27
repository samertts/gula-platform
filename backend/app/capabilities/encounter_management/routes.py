"""Non-functional encounter-management stub endpoints.

These handlers return fixed placeholder payloads only. No encounter is read or
written, and this router is not a canonical clinical encounter implementation.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.security.dependencies import get_current_user

router = APIRouter(prefix="/encounter-management", tags=["Encounter Management"])


@router.get(
    "/",
    summary="[STUB] List encounter-management placeholders",
    description="Placeholder only; no encounter is read or written.",
)
async def list_encounter_management(
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"items": [], "total": 0, "skip": skip, "limit": limit}


@router.get(
    "/{id}",
    summary="[STUB] Get encounter-management placeholder",
    description="Placeholder only; no encounter is read or written.",
)
async def get_encounter_management(
    id: str,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"id": id}


@router.post(
    "/",
    summary="[STUB] Create encounter-management placeholder",
    description="Placeholder only; no encounter is read or written.",
)
async def create_encounter_management(
    data: dict,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"success": True, "id": ""}


@router.put(
    "/{id}",
    summary="[STUB] Update encounter-management placeholder",
    description="Placeholder only; no encounter is read or written.",
)
async def update_encounter_management(
    id: str,
    data: dict,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"success": True}


@router.delete(
    "/{id}",
    summary="[STUB] Delete encounter-management placeholder",
    description="Placeholder only; no encounter is read or written.",
)
async def delete_encounter_management(
    id: str,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {"success": True}
