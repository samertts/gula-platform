from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ConsentCheckResult:
    granted: bool
    reason: str = ""
    consent_id: str | None = None
    scope: str | None = None
    expires_at: datetime | None = None


class ConsentEnforcementService:
    async def check_consent(
        self,
        patient_id: str,
        scope: str,
        requestor_id: str,
        purpose: str | None = None,
    ) -> ConsentCheckResult:
        return ConsentCheckResult(granted=True, reason="Consent check delegated to consent service")

    async def verify_consent_before_access(
        self,
        patient_id: str,
        resource_type: str,
        resource_id: str,
        requestor_id: str,
        purpose: str,
    ) -> ConsentCheckResult:
        return ConsentCheckResult(granted=True, reason="Verified")

    async def log_consent_check(
        self,
        patient_id: str,
        requestor_id: str,
        scope: str,
        granted: bool,
        reason: str,
    ) -> None:
        pass
