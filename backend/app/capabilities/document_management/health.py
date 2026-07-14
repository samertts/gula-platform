from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/document-management/health", tags=["health"])


@router.get("/")
async def health_check() -> dict:
    return {"status": "ok", "capability": "document_management", "version": "1.0.0"}


@router.get("/ready")
async def readiness() -> dict:
    return {"ready": True, "capability": "document_management"}
