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

_AUTH_REQUIRED = [Depends(get_current_niam_actor)]

# PORTED from 304fc9c1 on claude/p0-2-pharmacy-reconciliation (NR-108, Mustafa's
# lane). Three of these routers were mounted with no dependency and carried no
# actor dependency of their own, so every one of their routes answered an
# unauthenticated request:
#
#   POST /niam/sessions/{session_uuid}/terminate            log anyone out
#   POST /niam/sessions/account/{account_id}/terminate-all  log an account out
#   GET  /niam/sessions/account/{account_id}                enumerate sessions
#   POST /niam/devices/{device_uuid}/trust                  mark a device trusted
#   POST /niam/devices/{device_uuid}/revoke                 revoke a device
#   POST /niam/devices/register                             register a device
#   POST /niam/persons/                                     write the registry
#   GET  /niam/persons/{person_uuid}                         read the registry
#
# ``trust`` is the worst: a trusted device is an input to the adaptive
# authentication decision, so an unauthenticated caller could elevate a device
# and weaken the MFA outcome for it — an authentication bypass enabler, not just
# an open endpoint. ``terminate-all`` is an unauthenticated, targeted, repeatable
# account logout.
#
# His measurement found these and mine did not: a mount-level dependency never
# appears in a route's own ``dependant``, so walking per-route dependencies
# reports a mounted-guarded route as unguarded and an unguarded one as fine. The
# only honest question is what the served application does with no credential.
#
# auth stays public because login, logout and refresh must be. accounts is public
# only in that every route answers 410 Gone. account_requests is public BY DESIGN
# — rate-limited, idempotency-keyed self-service intake that never creates or
# activates an account.
router.include_router(persons.router, dependencies=_AUTH_REQUIRED)
router.include_router(account_requests.router)
router.include_router(accounts.router)
router.include_router(auth.router)
router.include_router(sessions.router, dependencies=_AUTH_REQUIRED)
router.include_router(workspaces.router)
router.include_router(memberships.router)
router.include_router(roles.router)
router.include_router(audit.router)
router.include_router(consents.router)
router.include_router(security.router)
router.include_router(devices.router, dependencies=_AUTH_REQUIRED)
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
