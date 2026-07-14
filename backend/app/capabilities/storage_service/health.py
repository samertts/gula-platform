from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/storage-service/health", tags=["health"])


@router.get("/")
async def health_check() -> dict:
    return {"status": "ok", "capability": "storage_service", "version": "1.0.0"}


@router.get("/ready")
async def readiness() -> dict:
    return {"ready": True, "capability": "storage_service"}
