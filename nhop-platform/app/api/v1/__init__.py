"""v1 HTTP API surface for nhop-platform."""
from fastapi import APIRouter, Depends

from ...core.trusted_context import require_trusted_context
from .citizens import router as citizens_router
from .doctor import router as doctor_router
from .notifications import router as notifications_router
from .outbreak import router as outbreak_router
from .test_results import router as test_results_router

# One dependency, applied once here, covering every v1 route — including
# POST /v1/test-results/, which files a clinical result against a lab named
# in the request body and previously read no server-verified actor at all.
# Attaching it per-handler would risk missing exactly that route. /health
# stays open: it is mounted on the app, not on this router.
api_router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(require_trusted_context)],
)
api_router.include_router(citizens_router)
api_router.include_router(test_results_router)
api_router.include_router(notifications_router)
api_router.include_router(doctor_router)
api_router.include_router(outbreak_router)
