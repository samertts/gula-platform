from .governance_routes import router as governance_router
from .analytics_routes import router as analytics_router

__all__ = ["governance_router", "analytics_router"]
