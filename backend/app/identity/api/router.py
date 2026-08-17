from fastapi import APIRouter, Depends

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

from . import (
    account_requests,
    accounts,
    audit,
    auth,
    consents,
    devices,
    memberships,
    persons,
    roles,
    security,
    sessions,
    workspaces,
)
from .workspaces import get_current_niam_actor

router = APIRouter(prefix="/niam", tags=["NIAM"])

router.include_router(persons.router)
router.include_router(account_requests.router)
router.include_router(accounts.router)
router.include_router(auth.router)
router.include_router(sessions.router)
router.include_router(workspaces.router)
router.include_router(memberships.router)
router.include_router(roles.router)
router.include_router(audit.router)
router.include_router(consents.router)
router.include_router(security.router)
router.include_router(devices.router)
_AUTH_REQUIRED = [Depends(get_current_niam_actor)]

router.include_router(governance_routes.router, dependencies=_AUTH_REQUIRED)
router.include_router(trust_routes.router, dependencies=_AUTH_REQUIRED)
router.include_router(lifecycle_routes.router, dependencies=_AUTH_REQUIRED)
router.include_router(federation_routes.router, dependencies=_AUTH_REQUIRED)
router.include_router(certificates_routes.router, dependencies=_AUTH_REQUIRED)
router.include_router(workflows_routes.router, dependencies=_AUTH_REQUIRED)
router.include_router(notifications_routes.router, dependencies=_AUTH_REQUIRED)
router.include_router(adaptive_auth_routes.router, dependencies=_AUTH_REQUIRED)
router.include_router(admin_routes.router, dependencies=_AUTH_REQUIRED)
router.include_router(compliance_routes.router, dependencies=_AUTH_REQUIRED)


@router.get("/health")
async def niam_health() -> dict[str, str]:
    return {"status": "healthy", "domain": "niam", "version": "1.0.0"}
