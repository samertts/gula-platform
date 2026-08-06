"""FastAPI routes for the platform module — health, modules, capabilities."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from ..security.dependencies import get_current_user
from . import PlatformRegistry

logger = logging.getLogger("gula.platform.routes")

router = APIRouter(
    prefix="/platform",
    tags=["platform"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/health")
async def platform_health() -> dict:
    return {
        "status": "ok",
        "modules": PlatformRegistry.list_modules(),
        "module_count": len(PlatformRegistry.list_modules()),
    }


@router.get("/modules")
async def platform_modules() -> dict:
    modules = PlatformRegistry.list_modules()
    return {"modules": modules, "count": len(modules)}


@router.get("/capabilities")
async def platform_capabilities() -> dict:
    capabilities = PlatformRegistry.get_capabilities()
    return {"capabilities": capabilities, "count": len(capabilities)}
