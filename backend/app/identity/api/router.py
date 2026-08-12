from fastapi import APIRouter

from app.identity.adaptive_auth import routes as adaptive_auth_routes
from app.identity.admin import routes as admin_routes
from app.identity.certificates import routes as certificates_routes
from app.identity.compliance import routes as compliance_routes
from app.identity.federation import routes as federation_routes
from app.identity.governance import routes as governance_routes
from app.identity.lifecycle import routes as lifecycle_routes
from app.identity.notifications import routes as notifications_routes
from app.identity.trust import routes as trust_routes
from app.identity.workflows import routes as workflows_routes

from . import accounts, auth, devices, persons, sessions

router = APIRouter(prefix="/niam", tags=["NIAM"])

router.include_router(persons.router)
router.include_router(accounts.router)
router.include_router(auth.router)
router.include_router(sessions.router)
router.include_router(devices.router)
router.include_router(governance_routes.router)
router.include_router(trust_routes.router)
router.include_router(lifecycle_routes.router)
router.include_router(federation_routes.router)
router.include_router(certificates_routes.router)
router.include_router(workflows_routes.router)
router.include_router(notifications_routes.router)
router.include_router(adaptive_auth_routes.router)
router.include_router(admin_routes.router)
router.include_router(compliance_routes.router)


@router.get("/health")
async def niam_health():
    return {"status": "healthy", "domain": "niam", "version": "1.0.0"}
