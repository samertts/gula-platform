from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/encounter-management/health", tags=["health"])


@router.get("/")
async def health_check() -> dict:
    return {"status": "ok", "capability": "encounter_management", "version": "1.0.0"}


@router.get("/ready")
async def readiness() -> dict:
    return {"ready": True, "capability": "encounter_management"}
