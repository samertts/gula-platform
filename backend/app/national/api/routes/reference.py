from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/reference", tags=["Reference Data"])


@router.get("/{ref_type}")
async def list_reference(ref_type: str):
    return {"ref_type": ref_type, "message": "Reference data list endpoint"}


@router.get("/{ref_type}/{code}")
async def get_reference(ref_type: str, code: str):
    return {"ref_type": ref_type, "code": code, "message": "Reference data lookup endpoint"}
