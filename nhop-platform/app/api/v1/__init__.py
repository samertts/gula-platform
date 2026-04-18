"""v1 HTTP API surface for nhop-platform."""
from fastapi import APIRouter

from .citizens import router as citizens_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(citizens_router)
