"""Authorization dependencies for the national identity registry (S-03).

The ``/niam/persons``, ``/niam/sessions`` and ``/niam/devices`` routes are
administrative identity-registry operations. They previously had *no* guard at
all, so anonymous callers could create and read person records (including PII),
terminate sessions and elevate device trust.

Policy
------
Authentication is provided by the canonical ``get_current_identity`` dependency
(identity-domain tokens or legacy platform tokens, matching the rest of the NIAM
API). Authorization is layered on top:

* **Platform identity operators** (``master_admin`` / ``ministry_admin`` through
  a platform token) may read the registry.
* **The platform operator** (``master_admin``) may mutate the registry.
* **NIAM identities without an assigned identity-registry role** are denied.
  The NIAM role catalog currently has no identity-registry administrator role,
  so this fails closed rather than guessing privilege from account type.
* Machine identities are *not* implicitly trusted: being an authenticated
  service does not grant access to national PII.

This is deliberately stricter than authentication-only. When a NIAM
identity-registry role/permission is introduced, the ``Account`` branch below is
where it must be resolved.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.models.account import Account
from app.identity.models.authorization import (
    CatalogStatus,
    Role,
    RoleAssignment,
    RoleAssignmentStatus,
)
from app.identity.security import get_current_identity

# Roles (from the canonical shared RBAC table) allowed to read registry data.
_PLATFORM_IDENTITY_READ_ROLES = frozenset({"master_admin", "ministry_admin"})
# Roles allowed to mutate registry data (create persons, terminate sessions,
# register/trust/revoke devices).
_PLATFORM_IDENTITY_WRITE_ROLES = frozenset({"master_admin"})


def _is_niam_account(principal) -> bool:
    return isinstance(principal, Account)


def _platform_role(principal) -> str | None:
    if _is_niam_account(principal):
        return None
    return getattr(principal, "role", None)


def _deny() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Identity registry authorization denied",
    )


async def require_niam_registry_reader(principal=Depends(get_current_identity)):
    """Authorize read access to national identity-registry records."""
    if _is_niam_account(principal):
        # No identity-registry administrator role exists in the NIAM catalog.
        raise _deny()
    if _platform_role(principal) in _PLATFORM_IDENTITY_READ_ROLES:
        return principal
    raise _deny()


async def require_niam_registry_writer(principal=Depends(get_current_identity)):
    """Authorize mutation of national identity-registry records."""
    if _is_niam_account(principal):
        raise _deny()
    if _platform_role(principal) in _PLATFORM_IDENTITY_WRITE_ROLES:
        return principal
    raise _deny()


# ── National control-plane authorization (AUD-SEC-001) ────────────────────────
# Governance, trust, lifecycle, federation, certificates, adaptive-auth,
# notifications and the professional registry are national trust operations.
# Authentication alone (a valid NIAM account + active session) is NOT
# sufficient: every enrolled identity previously could suspend identities,
# revoke certificates, alter trust anchors and terminate federations.
#
# Authorization is resolved from the canonical NIAM RBAC catalog: the account
# must hold an ACTIVE assignment to a role that carries platform-level
# management authority. No implicit privilege is derived from account type,
# identity verification or session possession. Deny by default.
_CONTROL_PLANE_AUTHORITIES = frozenset(
    {
        "master_admin",
        "ministry_admin",
        "organization_administrator",
        "security_administrator",
        "compliance_officer",
    }
)


async def require_niam_control_plane_authority(
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
) -> NiamActor:
    """Authorize mutation/observation of national NIAM control planes."""
    result = await db.execute(
        select(RoleAssignment.id)
        .join(Role, Role.id == RoleAssignment.role_id)
        .where(
            RoleAssignment.account_id == actor.account.id,
            RoleAssignment.status == RoleAssignmentStatus.active.value,
            Role.status == CatalogStatus.active.value,
            Role.role_key.in_(_CONTROL_PLANE_AUTHORITIES),
        )
    )
    if result.first() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="NIAM control-plane authorization denied",
        )
    return actor
