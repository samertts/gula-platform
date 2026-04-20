"""v1 HTTP API surface for nhop-platform."""
from fastapi import APIRouter

from .citizens import router as citizens_router
from .outbreak import router as outbreak_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(citizens_router)
api_router.include_router(outbreak_router)
