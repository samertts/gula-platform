"""Professional authorization — separable privilege layer over the registry.

The registry entry (``ProfessionalRegistryEntry``) records **identity** — who
the professional is and whether the issuing authority verified them. The
authorization (``ProfessionalAuthorization``) records **privilege** — the
jurisdictional scope, duration and current status of operational authority.
The two layers stay separable:

* An authorization is issued ONLY from a verified, non-expired, active entry.
* Any registry-level suspension/revocation invalidates every derived
  authorization when ``is_authorized`` is consulted.
* Revoking an authorization never touches the registry entry (the identity
  layer), preserving the audit trail of both.

``is_authorized`` is the single enforcement point: it requires BOTH a
still-privileged registry entry AND an active, unexpired authorization whose
scope matches the requested jurisdiction.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.models.audit import AuditAction
from app.identity.professional_registry.models import (
    AuthorizationScopeType,
    AuthorizationStatus,
    ProfessionalAuthorization,
    ProfessionalRegistryEntry,
)
from app.identity.professional_registry.services import (
    ProfessionalRegistryService,
)
from app.identity.services.audit_service import AuditService


class AuthorizationError(Exception):
    """Raised for invalid authorization operations."""


class ScopeError(AuthorizationError):
    """Raised when a scope is missing or malformed."""


def validate_scope(scope_type: str, scope_id: str | None) -> None:
    """Validate scope shape: national requires no id; others require one."""
    if scope_type == AuthorizationScopeType.national.value:
        return
    try:
        AuthorizationScopeType(scope_type)
    except ValueError as exc:
        raise ScopeError(f"invalid scope_type '{scope_type}'") from exc
    if not scope_id:
        raise ScopeError(f"scope_type '{scope_type}' requires scope_id")


def scope_matches(
    scope_type: str,
    scope_id: str | None,
    requested_type: str,
    requested_id: str | None,
) -> bool:
    """National authorizations match any jurisdiction; others need exact id."""
    if scope_type == AuthorizationScopeType.national.value:
        return True
    if requested_type == AuthorizationScopeType.national.value:
        return True
    return bool(scope_id) and scope_id == requested_id


class ProfessionalAuthorizationService:
    """Issue, renew, suspend and revoke professional authorizations."""

    def __init__(
        self,
        session: AsyncSession,
        audit: AuditService | None = None,
        registry: ProfessionalRegistryService | None = None,
    ) -> None:
        self.session = session
        self.audit = audit
        self.registry = registry or ProfessionalRegistryService(session)

    async def get(self, authorization_id: str) -> ProfessionalAuthorization | None:
        stmt = select(ProfessionalAuthorization).where(
            ProfessionalAuthorization.authorization_id == authorization_id,
            ProfessionalAuthorization.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_person(self, person_id: str) -> list[ProfessionalAuthorization]:
        stmt = select(ProfessionalAuthorization).where(
            ProfessionalAuthorization.person_id == person_id,
            ProfessionalAuthorization.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_scope(
        self,
        scope_type: str,
        scope_id: str | None = None,
    ) -> list[ProfessionalAuthorization]:
        validate_scope(scope_type, scope_id)
        stmt = select(ProfessionalAuthorization).where(
            ProfessionalAuthorization.scope_type == scope_type,
            ProfessionalAuthorization.is_active.is_(True),
        )
        if scope_id:
            stmt = stmt.where(ProfessionalAuthorization.scope_id == scope_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def issue(
        self,
        entry: ProfessionalRegistryEntry,
        *,
        scope_type: str = AuthorizationScopeType.national.value,
        scope_id: str | None = None,
        granted_by: str,
        expires_at: datetime | None = None,
    ) -> ProfessionalAuthorization:
        """Issue an authorization from a verified, non-expired registry entry.

        This is the ONLY path that materializes operational privilege. The
        registry remains the source of truth: an entry that is not verified,
        expired, suspended or revoked cannot yield an authorization.
        """
        validate_scope(scope_type, scope_id)
        if not entry.verified:
            raise AuthorizationError("entry_not_verified")
        if entry.status != "verified":
            raise AuthorizationError(f"entry_not_verified_status:{entry.status}")
        if entry.expires_at and entry.expires_at < date.today():
            raise AuthorizationError("entry_expired")
        now = datetime.now(UTC)
        authorization = ProfessionalAuthorization(
            id=...,
            uuid=str(uuid.uuid4()),
            authorization_id=f"AUTH-{uuid.uuid4().hex[:16].upper()}",
            registry_id=entry.id,
            person_id=entry.person_id,
            profession=entry.profession,
            scope_type=scope_type,
            scope_id=scope_id,
            status=AuthorizationStatus.active.value,
            granted_at=now,
            granted_by=granted_by,
            expires_at=expires_at,
            is_active=True,
        )
        self.session.add(authorization)
        await self.session.flush()
        if self.audit is not None:
            await self.audit.record(
                AuditAction.authorization_issued,
                actor_id=granted_by,
                target_type="professional",
                target_id=entry.person_id,
                metadata={
                    "authorization_id": authorization.authorization_id,
                    "registry_id": entry.registry_id,
                    "profession": entry.profession,
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                },
            )
        return authorization

    async def renew(
        self,
        authorization_id: str,
        *,
        granted_by: str,
        expires_at: datetime | None,
    ) -> ProfessionalAuthorization:
        authorization = await self.get(authorization_id)
        if not authorization:
            raise AuthorizationError("authorization_not_found")
        if authorization.status == AuthorizationStatus.revoked.value:
            raise AuthorizationError("authorization_revoked")
        authorization.expires_at = expires_at
        authorization.granted_by = granted_by
        await self.session.flush()
        if self.audit is not None:
            await self.audit.record(
                AuditAction.authorization_renewed,
                actor_id=granted_by,
                target_type="professional",
                target_id=authorization.person_id,
                metadata={
                    "authorization_id": authorization.authorization_id,
                    "expires_at": expires_at.isoformat() if expires_at else None,
                },
            )
        return authorization

    async def suspend(
        self,
        authorization_id: str,
        *,
        reason: str,
        actor: str,
    ) -> ProfessionalAuthorization:
        authorization = await self.get(authorization_id)
        if not authorization:
            raise AuthorizationError("authorization_not_found")
        if authorization.status == AuthorizationStatus.revoked.value:
            raise AuthorizationError("authorization_revoked")
        authorization.status = AuthorizationStatus.suspended.value
        authorization.status_reason = reason
        await self.session.flush()
        if self.audit is not None:
            await self.audit.record(
                AuditAction.authorization_suspended,
                actor_id=actor,
                target_type="professional",
                target_id=authorization.person_id,
                metadata={
                    "authorization_id": authorization.authorization_id,
                    "reason": reason,
                },
            )
        return authorization

    async def revoke(
        self,
        authorization_id: str,
        *,
        reason: str,
        actor: str,
    ) -> ProfessionalAuthorization:
        authorization = await self.get(authorization_id)
        if not authorization:
            raise AuthorizationError("authorization_not_found")
        authorization.status = AuthorizationStatus.revoked.value
        authorization.status_reason = reason
        authorization.is_active = False
        await self.session.flush()
        if self.audit is not None:
            await self.audit.record(
                AuditAction.authorization_revoked,
                actor_id=actor,
                target_type="professional",
                target_id=authorization.person_id,
                metadata={
                    "authorization_id": authorization.authorization_id,
                    "reason": reason,
                },
            )
        return authorization

    async def is_authorized(
        self,
        person_id: str,
        profession: str,
        *,
        scope_type: str = AuthorizationScopeType.facility.value,
        scope_id: str | None = None,
        now: datetime | None = None,
    ) -> bool:
        """Single enforcement point for professional operational authority.

        Requires BOTH the underlying registry entry to still be privileged
        (verified, unexpired, unsuspended/unrevoked) AND an active, unexpired
        authorization whose scope matches the requested jurisdiction. Registry
        suspension/revocation therefore invalidates authorizations even when the
        authorization row itself still looks active.
        """
        if not await self.registry.is_privileged(person_id, profession=profession):
            return False
        check = now or datetime.now(UTC)
        stmt = select(ProfessionalAuthorization).where(
            ProfessionalAuthorization.person_id == person_id,
            ProfessionalAuthorization.profession == profession,
            ProfessionalAuthorization.status == AuthorizationStatus.active.value,
            ProfessionalAuthorization.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        authorizations = list(result.scalars().all())
        for authorization in authorizations:
            if authorization.status != AuthorizationStatus.active.value:
                continue
            if not authorization.is_active:
                continue
            if authorization.profession != profession:
                continue
            if authorization.expires_at and authorization.expires_at < check:
                continue
            if scope_matches(
                authorization.scope_type,
                authorization.scope_id,
                scope_type,
                scope_id,
            ):
                return True
        return False

    async def matching_authorization(
        self,
        person_id: str,
        profession: str,
        *,
        scope_type: str = AuthorizationScopeType.facility.value,
        scope_id: str | None = None,
        now: datetime | None = None,
    ) -> ProfessionalAuthorization | None:
        """Return the first matching active authorization, if any."""
        check = now or datetime.now(UTC)
        stmt = select(ProfessionalAuthorization).where(
            ProfessionalAuthorization.person_id == person_id,
            ProfessionalAuthorization.profession == profession,
            ProfessionalAuthorization.status == AuthorizationStatus.active.value,
            ProfessionalAuthorization.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        authorizations: Sequence[ProfessionalAuthorization] = list(result.scalars().all())
        for authorization in authorizations:
            if authorization.status != AuthorizationStatus.active.value:
                continue
            if not authorization.is_active:
                continue
            if authorization.profession != profession:
                continue
            if authorization.expires_at and authorization.expires_at < check:
                continue
            if scope_matches(
                authorization.scope_type,
                authorization.scope_id,
                scope_type,
                scope_id,
            ):
                return authorization
        return None

    async def sync_status_from_registry(self, entry: ProfessionalRegistryEntry) -> int:
        """Mark derived authorizations to match the registry entry status.

        Registry suspension/revocation/retirement must invalidate derived
        authorizations. Never deletes rows — preserves the audit trail.
        Returns the number of authorizations synchronized.
        """
        stmt = select(ProfessionalAuthorization).where(
            ProfessionalAuthorization.registry_id == entry.id,
            ProfessionalAuthorization.status == AuthorizationStatus.active.value,
            ProfessionalAuthorization.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        authorizations = list(result.scalars().all())
        if entry.status in ("suspended", "revoked", "retired", "expired"):
            target = (
                AuthorizationStatus.suspended.value
                if entry.status == "suspended"
                else AuthorizationStatus.revoked.value
            )
            for authorization in authorizations:
                authorization.status = target
                authorization.status_reason = f"registry_{entry.status}"
        await self.session.flush()
        return len(authorizations)
