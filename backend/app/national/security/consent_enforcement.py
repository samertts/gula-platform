from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService
from app.national.security.reference import pseudonymous_reference


@dataclass
class ConsentCheckResult:
    granted: bool
    reason: str = ""
    consent_id: str | None = None
    scope: str | None = None
    expires_at: datetime | None = None


class ConsentEnforcementService:
    """Fail-closed adapter over canonical consent and audit boundaries.

    A canonical institution/subject consent authority requires an owner-approved
    mapping from national citizen identifiers to NIAM consent records. Until that
    mapping exists, this service denies every check and records the decision in
    the canonical v2 audit stream. It is not a second consent engine and it does
    not claim that any consent has been verified.
    """

    AUTHORITY_UNAVAILABLE = "CONSENT_AUTHORITY_UNAVAILABLE"
    INPUT_INVALID = "CONSENT_INPUT_INVALID"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = CanonicalAuditService(session)

    async def check_consent(
        self,
        patient_id: str,
        scope: str,
        requestor_id: str,
        purpose: str | None = None,
    ) -> ConsentCheckResult:
        reason = self.AUTHORITY_UNAVAILABLE
        if not patient_id or not scope or not requestor_id:
            reason = self.INPUT_INVALID
        await self.log_consent_check(
            patient_id=patient_id,
            requestor_id=requestor_id,
            scope=scope,
            granted=False,
            reason=reason,
            purpose=purpose,
        )
        return ConsentCheckResult(granted=False, reason=reason, scope=scope)

    async def verify_consent_before_access(
        self,
        patient_id: str,
        resource_type: str,
        resource_id: str,
        requestor_id: str,
        purpose: str,
    ) -> ConsentCheckResult:
        reason = self.AUTHORITY_UNAVAILABLE
        if not patient_id or not resource_type or not resource_id or not requestor_id or not purpose:
            reason = self.INPUT_INVALID
        await self.log_consent_check(
            patient_id=patient_id,
            requestor_id=requestor_id,
            scope=resource_type,
            granted=False,
            reason=reason,
            purpose=purpose,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        return ConsentCheckResult(granted=False, reason=reason)

    async def log_consent_check(
        self,
        *,
        patient_id: str,
        requestor_id: str,
        scope: str,
        granted: bool,
        reason: str,
        purpose: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> None:
        subject_digest = pseudonymous_reference(patient_id)
        resource_digest = pseudonymous_reference(resource_id)
        await self.audit.record(
            AuditEventInput(
                event_type="CONSENT_CHECK_DENIED" if not granted else "CONSENT_CHECK_GRANTED",
                category="CONSENT",
                action="consent.enforcement.check",
                actor_id=requestor_id,
                target_type=resource_type or "consent_subject",
                target_id=subject_digest or resource_digest,
                decision="DENY" if not granted else "ALLOW",
                reason_code=reason,
                source="national_consent_enforcement",
                data_classification="SENSITIVE",
                outcome="denied" if not granted else "success",
                metadata={
                    "scope_digest": pseudonymous_reference(scope),
                    "resource_digest": resource_digest,
                    "purpose": purpose,
                },
            ),
        )
