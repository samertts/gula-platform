"""v1 HTTP API surface for nhop-platform."""
from fastapi import APIRouter, Depends

from ...core.trusted_context import require_trusted_context
from .citizens import router as citizens_router
from .notifications import router as notifications_router
from .test_results import router as test_results_router

# NR-127/NR-128. One dependency, applied once, covering every v1 route.
#
# It is attached HERE rather than to each handler because the route that made
# this urgent -- POST /v1/test-results/, which files a clinical result against
# a lab named in the request body -- reads no actor at all, so anything applied
# per-handler-that-reads-an-actor would have missed exactly the worst one.
# /health stays open: it is mounted on the app, not on this router.
api_router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(require_trusted_context)],
)
api_router.include_router(citizens_router)
api_router.include_router(test_results_router)
api_router.include_router(notifications_router)
