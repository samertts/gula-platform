from platform.api.routes.health import router as health_router
from platform.api.routes.patients import router as patients_router
from platform.api.routes.orders import router as orders_router
from platform.api.routes.results import router as results_router
from platform.api.routes.labs import router as labs_router
from platform.api.routes.auth import router as auth_router

__all__ = [
    "health_router", "patients_router", "orders_router",
    "results_router", "labs_router", "auth_router",
]
