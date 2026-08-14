from __future__ import annotations

from fastapi import APIRouter, Depends

from app.security.dependencies import require_permission

router = APIRouter(
    prefix="/reference",
    tags=["Reference Data"],
    dependencies=[Depends(require_permission("system:admin"))],
)


@router.get("/{ref_type}")
async def list_reference(ref_type: str):
    return {"ref_type": ref_type, "message": "Reference data list endpoint"}


@router.get("/{ref_type}/{code}")
async def get_reference(ref_type: str, code: str):
    return {"ref_type": ref_type, "code": code, "message": "Reference data lookup endpoint"}
