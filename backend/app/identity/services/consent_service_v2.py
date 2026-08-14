from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.base import _ulid
from app.identity.models.consent import NiamConsent, NiamConsentSource, NiamConsentStatus
from app.identity.models.membership import Membership
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService


class NiamConsentError(ValueError):
    pass


class NiamConsentAccessDenied(PermissionError):
    pass


class NiamConsentService:
    MAX_CONSENT_HOURS = 72
    ALLOWED_PURPOSES = frozenset(
        {"TREATMENT", "RESEARCH", "BILLING", "AUDIT", "PUBLIC_HEALTH", "citizen_workspace"},
    )
    ALLOWED_STATUSES = frozenset(item.value for item in NiamConsentStatus)

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = CanonicalAuditService(session)

    @staticmethod
    def _validate_scope(scope: dict[str, Any]) -> dict[str, Any]:
        if not scope or len(scope) > 20:
            raise NiamConsentError("scope must contain between 1 and 20 fields")
        return {str(key): value for key, value in scope.items() if isinstance(key, str)}

    @classmethod
    def _validate_expiry(cls, expires_at: datetime) -> datetime:
        now = datetime.now(UTC)
        expiry = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=UTC)
        expiry = expiry.astimezone(UTC)
        if expiry <= now or expiry > now + timedelta(hours=cls.MAX_CONSENT_HOURS):
            raise NiamConsentError(f"expires_at must be within {cls.MAX_CONSENT_HOURS} hours")
        return expiry

    async def _organization_for_account(self, account_id: str) -> str | None:
        result = await self.session.execute(
            select(Membership.organization_id)
            .where(Membership.account_id == account_id, Membership.status == "active")
            .order_by(Membership.created_at.asc())
            .limit(1),
        )
        return result.scalar_one_or_none()

    async def grant(
        self,
        *,
        actor_account_id: str,
        subject_account_id: str,
        grantee_account_id: str,
        purpose: str,
        scope: dict[str, Any],
        resource_domain: str,
        expires_at: datetime,
        legal_basis: str | None = None,
        source: str = NiamConsentSource.user_portal.value,
        reason: str | None = None,
    ) -> NiamConsent:
        if subject_account_id != actor_account_id:
            raise NiamConsentAccessDenied("Only the subject may grant this consent workflow")
        if not grantee_account_id or grantee_account_id == subject_account_id:
            raise NiamConsentError("grantee_account_id must identify another account")
        if purpose not in self.ALLOWED_PURPOSES:
            raise NiamConsentError("purpose is not an approved consent purpose")
        if not resource_domain or len(resource_domain) > 120:
            raise NiamConsentError("resource_domain is required")
        clean_scope = self._validate_scope(scope)
        expiry = self._validate_expiry(expires_at)
        previous = (
            await self.session.execute(
                select(NiamConsent)
                .where(
                    NiamConsent.subject_account_id == subject_account_id,
                    NiamConsent.grantee_account_id == grantee_account_id,
                    NiamConsent.purpose == purpose,
                    NiamConsent.resource_domain == resource_domain,
                )
                .order_by(NiamConsent.version.desc())
                .limit(1)
                .with_for_update(),
            )
        ).scalar_one_or_none()
        version = 1 if previous is None else previous.version + 1
        if previous is not None and previous.status == NiamConsentStatus.active.value:
            previous.status = NiamConsentStatus.revoked.value
            previous.reason = "superseded_by_new_version"
            previous.is_active = False
        consent = NiamConsent(
            uuid=_ulid(),
            subject_account_id=subject_account_id,
            grantee_account_id=grantee_account_id,
            purpose=purpose,
            scope=clean_scope,
            resource_domain=resource_domain,
            status=NiamConsentStatus.active.value,
            granted_at=datetime.now(UTC),
            expires_at=expiry,
            version=version,
            source=source,
            legal_basis=legal_basis,
            created_by=actor_account_id,
            supersedes_id=previous.id if previous is not None else None,
            reason=reason,
            is_active=True,
        )
        self.session.add(consent)
        await self.session.flush()
        await self.audit.record(
            AuditEventInput(
                event_type="CONSENT_GRANTED",
                category="CONSENT",
                action="consent.grant",
                actor_id=actor_account_id,
                organization_id=await self._organization_for_account(actor_account_id),
                target_type="consent",
                target_id=consent.id,
                decision="ALLOW",
                reason_code="CONSENT_VERSION_CREATED",
                data_classification="SENSITIVE",
                metadata={"purpose": purpose, "resource_domain": resource_domain, "version": version},
            ),
        )
        return consent

    async def withdraw(self, *, actor_account_id: str, consent_id: str, reason: str | None = None) -> NiamConsent:
        consent = await self.session.get(NiamConsent, consent_id)
        if consent is None:
            raise NiamConsentError("consent not found")
        if actor_account_id not in {consent.subject_account_id, consent.grantee_account_id}:
            raise NiamConsentAccessDenied("consent withdrawal denied")
        if consent.status != NiamConsentStatus.active.value:
            raise NiamConsentError("consent is not active")
        consent.status = NiamConsentStatus.withdrawn.value
        consent.withdrawn_at = datetime.now(UTC)
        consent.reason = reason
        consent.is_active = False
        await self.session.flush()
        await self.audit.record(
            AuditEventInput(
                event_type="CONSENT_WITHDRAWN",
                category="CONSENT",
                action="consent.withdraw",
                actor_id=actor_account_id,
                organization_id=await self._organization_for_account(actor_account_id),
                target_type="consent",
                target_id=consent.id,
                decision="ALLOW",
                reason_code="SUBJECT_OR_GRANTEE_WITHDRAWAL",
                data_classification="SENSITIVE",
            ),
        )
        return consent

    async def check(self, *, actor_account_id: str, consent_id: str) -> NiamConsent | None:
        consent = await self.session.get(NiamConsent, consent_id)
        if consent is None:
            return None
        if actor_account_id not in {consent.subject_account_id, consent.grantee_account_id}:
            raise NiamConsentAccessDenied("consent check denied")
        if consent.status == NiamConsentStatus.active.value and not consent.is_valid_now():
            consent.status = NiamConsentStatus.expired.value
            consent.is_active = False
            await self.session.flush()
        await self.audit.record(
            AuditEventInput(
                event_type="CONSENT_CHECKED",
                category="CONSENT",
                action="consent.check",
                actor_id=actor_account_id,
                organization_id=await self._organization_for_account(actor_account_id),
                target_type="consent",
                target_id=consent.id,
                decision="ALLOW" if consent.is_valid_now() else "DENY",
                reason_code="ACTIVE" if consent.is_valid_now() else "NOT_ACTIVE",
                data_classification="SENSITIVE",
            ),
        )
        return consent if consent.is_valid_now() else None

    async def list_for_account(self, *, actor_account_id: str, limit: int = 100, offset: int = 0) -> list[NiamConsent]:
        result = await self.session.execute(
            select(NiamConsent)
            .where(
                (NiamConsent.subject_account_id == actor_account_id)
                | (NiamConsent.grantee_account_id == actor_account_id),
            )
            .order_by(NiamConsent.created_at.desc())
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 100)),
        )
        return list(result.scalars().all())
