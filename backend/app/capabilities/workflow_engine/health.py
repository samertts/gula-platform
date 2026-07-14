from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/workflow-engine/health", tags=["health"])


@router.get("/")
async def health_check() -> dict:
    return {"status": "ok", "capability": "workflow_engine", "version": "1.0.0"}


@router.get("/ready")
async def readiness() -> dict:
    return {"ready": True, "capability": "workflow_engine"}
