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
    pending = "pending"
    verified = "verified"
    rejected = "rejected"
    expired = "expired"
    not_connected = "not_connected"


class AssuranceLevel(StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"


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


class IdentityVerificationProvider(Protocol):
    name: str
    connected: bool

    async def verify(self, request: VerificationRequest) -> VerificationResult:
        """Return a provider result; never infer success from a missing provider."""


class NotConnectedProvider:
    """Explicit safe adapter for integrations not available in this deployment."""

    connected = False

    def __init__(self, method: VerificationMethod) -> None:
        self.name = f"{method.value}:not-connected"
        self.method = method

    async def verify(self, request: VerificationRequest) -> VerificationResult:
        return VerificationResult(
            status=VerificationStatus.not_connected,
            assurance=AssuranceLevel.L0,
            provider=self.name,
            method=self.method,
            reason="Provider integration is not connected in this deployment",
        )


class VerificationPolicy:
    """Single authoritative mapping from verified methods to assurance levels."""

    _levels = {
        VerificationMethod.phone: AssuranceLevel.L1,
        VerificationMethod.email: AssuranceLevel.L1,
        VerificationMethod.official_identity: AssuranceLevel.L2,
        VerificationMethod.ocr: AssuranceLevel.L2,
        VerificationMethod.nfc: AssuranceLevel.L2,
        VerificationMethod.professional_registry: AssuranceLevel.L3,
        VerificationMethod.organization_registry: AssuranceLevel.L4,
    }

    @classmethod
    def assurance_for(cls, result: VerificationResult) -> AssuranceLevel:
        if result.status != VerificationStatus.verified:
            return AssuranceLevel.L0
        return cls._levels.get(result.method, result.assurance)
