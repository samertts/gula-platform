"""Platform Authority assignment lifecycle: grant, revoke, check.

No route in this module is exposed publicly (Phase 10 deliberately does not
solve the bootstrap problem -- see docs/security/NIAM_PLATFORM_AUTHORITY_ARCHITECTURE.md
Phase 9 Section 13 step 2). This service exists so the resolver
(authorization.py) and a future, separately-approved administration surface
have one place that enforces the grant/revoke invariants.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.platform_authority.models import (
    PlatformAuthorityAssignment,
    PlatformAuthorityAssignmentStatus,
    PlatformCapability,
)
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService

_KNOWN_CAPABILITIES = frozenset(c.value for c in PlatformCapability)


class UnknownPlatformCapability(ValueError):
    """Raised when a capability string is not one of the four canonical ones."""


class PlatformAuthorityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = CanonicalAuditService(session)

    async def _active_assignment(
        self,
        identity_id: str,
        capability: str,
    ) -> PlatformAuthorityAssignment | None:
        stmt = select(PlatformAuthorityAssignment).where(
            PlatformAuthorityAssignment.identity_id == identity_id,
            PlatformAuthorityAssignment.capability == capability,
            PlatformAuthorityAssignment.status == PlatformAuthorityAssignmentStatus.active.value,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_capability(self, identity_id: str | None, capability: str) -> bool:
        """Fail-closed capability check. Never raises for a malformed/unknown input."""
        if not identity_id or capability not in _KNOWN_CAPABILITIES:
            return False
        return await self._active_assignment(identity_id, capability) is not None

    async def grant(
        self,
        *,
        identity_id: str,
        capability: str,
        granted_by_account_id: str | None,
    ) -> PlatformAuthorityAssignment:
        if capability not in _KNOWN_CAPABILITIES:
            raise UnknownPlatformCapability(capability)

        existing = await self._active_assignment(identity_id, capability)
        if existing is not None:
            return existing  # idempotent: granting an already-active capability is a no-op

        assignment = PlatformAuthorityAssignment(
            uuid=str(uuid.uuid4()),
            identity_id=identity_id,
            capability=capability,
            status=PlatformAuthorityAssignmentStatus.active.value,
            granted_by=granted_by_account_id,
            granted_at=datetime.now(UTC),
        )
        self.session.add(assignment)
        await self.session.flush()

        await self.audit.record(
            AuditEventInput(
                event_type="PLATFORM_AUTHORITY_GRANTED",
                category="PLATFORM_AUTHORITY",
                action="platform_authority.grant",
                actor_id=granted_by_account_id,
                target_type="platform_authority_assignment",
                target_id=assignment.id,
                decision="ALLOW",
                reason_code="PLATFORM_AUTHORITY_GRANT",
                data_classification="INTERNAL",
                metadata={"identity_id": identity_id, "capability": capability},
            ),
        )
        return assignment

    async def revoke(
        self,
        *,
        identity_id: str,
        capability: str,
        revoked_by_account_id: str | None,
        reason: str | None = None,
    ) -> PlatformAuthorityAssignment | None:
        if capability not in _KNOWN_CAPABILITIES:
            raise UnknownPlatformCapability(capability)

        existing = await self._active_assignment(identity_id, capability)
        if existing is None:
            return None

        existing.status = PlatformAuthorityAssignmentStatus.revoked.value
        existing.revoked_at = datetime.now(UTC)
        existing.revoked_by = revoked_by_account_id
        existing.revocation_reason = reason
        await self.session.flush()

        await self.audit.record(
            AuditEventInput(
                event_type="PLATFORM_AUTHORITY_REVOKED",
                category="PLATFORM_AUTHORITY",
                action="platform_authority.revoke",
                actor_id=revoked_by_account_id,
                target_type="platform_authority_assignment",
                target_id=existing.id,
                decision="ALLOW",
                reason_code="PLATFORM_AUTHORITY_REVOKE",
                data_classification="INTERNAL",
                metadata={"identity_id": identity_id, "capability": capability, "reason": reason},
            ),
        )
        return existing
