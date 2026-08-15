from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class VerificationMethod(StrEnum):
    phone = "phone"
    email = "email"
    official_identity = "official_identity"
    ocr = "ocr"
    nfc = "nfc"
    professional_registry = "professional_registry"
    organization_registry = "organization_registry"


class VerificationStatus(StrEnum):
    not_started = "not_started"
    sent = "sent"
    pending = "pending"
    in_progress = "in_progress"
    verified = "verified"
    failed = "failed"
    expired = "expired"
    locked = "locked"
    revoked = "revoked"
    requires_review = "requires_review"
    not_connected = "not_connected"


class AssuranceLevel(StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"


_ASSURANCE_ORDER = {level: index for index, level in enumerate(AssuranceLevel)}


@dataclass(frozen=True)
class VerificationRequest:
    account_id: str
    identity_id: str
    method: VerificationMethod
    reference: str | None = None


@dataclass(frozen=True)
class VerificationResult:
    status: VerificationStatus
    assurance: AssuranceLevel
    provider: str
    method: VerificationMethod
    reason: str | None = None
    provider_reference: str | None = None
    verified_attributes: dict[str, str] | None = None


@dataclass(frozen=True)
class VerificationSession:
    session_id: str
    account_id: str
    identity_id: str
    provider: str
    method: VerificationMethod
    expires_at: str


class IdentityVerificationProvider(Protocol):
    name: str
    connected: bool

    async def start_verification(self, request: VerificationRequest) -> VerificationSession | VerificationResult:
        ...

    async def check_status(self, session: VerificationSession) -> VerificationResult:
        ...

    async def complete_verification(self, session: VerificationSession, evidence: object | None = None) -> VerificationResult:
        ...

    async def cancel_verification(self, session: VerificationSession) -> VerificationResult:
        ...

    async def revoke_verification(self, reference: str) -> VerificationResult:
        ...


class ProfessionalVerificationProvider(IdentityVerificationProvider, Protocol):
    """Boundary for future official registry adapters; no registry is fabricated."""


class NotConnectedProvider:
    """Explicit safe adapter for integrations not available in this deployment."""

    connected = False

    def __init__(self, method: VerificationMethod) -> None:
        self.name = f"{method.value}:not-connected"
        self.method = method

    def _result(self, status: VerificationStatus = VerificationStatus.not_connected) -> VerificationResult:
        return VerificationResult(
            status=status,
            assurance=AssuranceLevel.L0,
            provider=self.name,
            method=self.method,
            reason="Provider integration is not connected in this deployment",
        )

    async def start_verification(self, request: VerificationRequest) -> VerificationResult:
        return self._result()

    async def check_status(self, session: VerificationSession) -> VerificationResult:
        return self._result()

    async def complete_verification(self, session: VerificationSession, evidence: object | None = None) -> VerificationResult:
        return self._result(VerificationStatus.failed)

    async def cancel_verification(self, session: VerificationSession) -> VerificationResult:
        return self._result(VerificationStatus.failed)

    async def revoke_verification(self, reference: str) -> VerificationResult:
        return self._result(VerificationStatus.failed)

    async def verify(self, request: VerificationRequest) -> VerificationResult:
        """Backward-compatible one-shot operation; it never claims success."""
        return await self.start_verification(request)


class VerificationPolicy:
    """Single authoritative method-to-assurance mapping."""

    _levels = {
        VerificationMethod.phone: AssuranceLevel.L1,
        VerificationMethod.email: AssuranceLevel.L1,
        VerificationMethod.official_identity: AssuranceLevel.L2,
        VerificationMethod.ocr: AssuranceLevel.L0,
        VerificationMethod.nfc: AssuranceLevel.L0,
        VerificationMethod.professional_registry: AssuranceLevel.L3,
        VerificationMethod.organization_registry: AssuranceLevel.L4,
    }

    @classmethod
    def assurance_for(cls, result: VerificationResult) -> AssuranceLevel:
        if result.status != VerificationStatus.verified:
            return AssuranceLevel.L0
        return cls._levels.get(result.method, result.assurance)


class AssuranceEngine:
    """Central server-side assurance evaluator; callers do not compare strings."""

    @staticmethod
    def level_for(results: list[VerificationResult]) -> AssuranceLevel:
        if not results:
            return AssuranceLevel.L0
        levels = [VerificationPolicy.assurance_for(result) for result in results]
        return max(levels, key=lambda level: _ASSURANCE_ORDER[level])

    @staticmethod
    def require(results: list[VerificationResult], required: AssuranceLevel) -> None:
        actual = AssuranceEngine.level_for(results)
        if _ASSURANCE_ORDER[actual] < _ASSURANCE_ORDER[required]:
            raise PermissionError(f"Required assurance {required.value}; actual assurance {actual.value}")
