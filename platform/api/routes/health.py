from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready")
async def readiness() -> dict[str, str]:
    return {"status": "ready"}


@router.get("/status")
async def status() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime": "running",
    }
