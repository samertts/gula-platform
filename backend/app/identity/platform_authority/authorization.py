"""Platform Authority resolution: authenticated NIAM identity -> capability check.

    authenticated NIAM identity (NiamActor.account.identity_id)
            v
    active Platform Authority assignments (PlatformAuthorityService)
            v
    capability check
            v
    allow / deny

Deliberately does not touch Membership, RoleAssignment, or
AuthorizationDecisionService: organization RBAC and Platform Authority are
separate axes (docs/security/NIAM_PLATFORM_AUTHORITY_ARCHITECTURE.md
Section 1/14) and an organization role must never satisfy a platform
capability. Deliberately does not read a capability or identity claim from
the request -- the identity comes only from the session-resolved actor, the
capability only from a caller-supplied constant, never from client input.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.api.workspaces import NiamActor
from app.identity.platform_authority.services import PlatformAuthorityService

PLATFORM_AUTHORITY_DENIED = "Platform authority denied"


async def require_platform_capability(
    actor: NiamActor | None,
    db: AsyncSession,
    capability: str,
) -> None:
    """Fail-closed. Raises HTTPException(403) unless `actor` currently holds
    an active Platform Authority assignment for exactly `capability`.

    A missing actor/account, a missing identity_id, and an unrecognized
    capability string all deny the same way as an absent assignment -- there
    is no separate "misconfigured" path that could be mistaken for allow.
    """
    identity_id = getattr(getattr(actor, "account", None), "identity_id", None) if actor else None
    allowed = await PlatformAuthorityService(db).has_capability(identity_id, capability)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=PLATFORM_AUTHORITY_DENIED)
