from fastapi import APIRouter, Depends

from app.identity.adaptive_auth import routes as adaptive_auth_routes
from app.identity.admin import routes as admin_routes
from app.identity.certificates import routes as certificates_routes
from app.identity.citizen_registry import routes as citizen_routes
from app.identity.compliance import routes as compliance_routes
from app.identity.federation import routes as federation_routes
from app.identity.governance import routes as governance_routes
from app.identity.lifecycle import routes as lifecycle_routes
from app.identity.professional_registry import routes as professional_registry_routes
from app.identity.trust import routes as trust_routes
from app.identity.workflows import routes as workflows_routes
from app.identity.workspaces import routes as workspaces_routes
from app.notifications.routes import router as notifications_routes
from app.security.abac_enforcement import require_abac

from . import accounts, auth, devices, persons, sessions

router = APIRouter(prefix="/niam", tags=["NIAM"])

router.include_router(
    persons.router, dependencies=[Depends(require_abac("niam:persons"))]
)
router.include_router(
    accounts.router, dependencies=[Depends(require_abac("niam:accounts"))]
)
router.include_router(auth.router)
router.include_router(
    sessions.router, dependencies=[Depends(require_abac("niam:sessions"))]
)
router.include_router(
    devices.router, dependencies=[Depends(require_abac("niam:devices"))]
)
router.include_router(
    governance_routes.router,
    dependencies=[Depends(require_abac("niam:governance"))],
)
router.include_router(
    trust_routes.router, dependencies=[Depends(require_abac("niam:trust"))]
)
router.include_router(
    lifecycle_routes.router, dependencies=[Depends(require_abac("niam:lifecycle"))]
)
router.include_router(
    federation_routes.router,
    dependencies=[Depends(require_abac("niam:federation"))],
)
router.include_router(
    certificates_routes.router,
    dependencies=[Depends(require_abac("niam:certificates"))],
)
router.include_router(
    workflows_routes.router, dependencies=[Depends(require_abac("niam:workflows"))]
)
router.include_router(
    notifications_routes,
    dependencies=[Depends(require_abac("niam:notifications"))],
)
router.include_router(
    adaptive_auth_routes.router,
    dependencies=[Depends(require_abac("niam:adaptive-auth"))],
)
router.include_router(
    admin_routes.router, dependencies=[Depends(require_abac("niam:admin"))]
)
router.include_router(
    compliance_routes.router,
    dependencies=[Depends(require_abac("niam:compliance"))],
)
router.include_router(
    workspaces_routes.router,
    dependencies=[Depends(require_abac("niam:workspaces"))],
)
router.include_router(
    citizen_routes.router, dependencies=[Depends(require_abac("niam:citizens"))]
)
router.include_router(
    professional_registry_routes.router,
    dependencies=[Depends(require_abac("niam:professional-registry"))],
)


@router.get("/health")
async def niam_health():
    return {"status": "healthy", "domain": "niam", "version": "1.0.0"}
