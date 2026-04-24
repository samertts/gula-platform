"""v1 HTTP API surface for nhop-platform."""
from fastapi import APIRouter

from .citizens import router as citizens_router
from .notifications import router as notifications_router
from .test_results import router as test_results_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(citizens_router)
api_router.include_router(test_results_router)
api_router.include_router(notifications_router)
