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
    pending = "pending"
    in_progress = "in_progress"
    verified = "verified"
    failed = "failed"
    expired = "expired"
    revoked = "revoked"
    requires_review = "requires_review"
    not_connected = "not_connected"


class VerificationPurpose(StrEnum):
    """What a verification actually establishes.

    These are independent questions, not points on one scale. Verifying that an
    organization holds a licence says nothing about who the human holding the
    account is, and vice versa. The values match ``VerificationRecordType`` on
    the persisted record so the two never drift into separate vocabularies.
    """

    contact = "contact"            # the holder can receive at, and controls, this address
    identity = "identity"          # who the real-world person is
    professional = "professional"  # this person is licensed to practise
    organization = "organization"  # this organization is real and eligible


class AssuranceLevel(StrEnum):
    """How strongly a single purpose has been established.

    Deliberately four levels, applied *per purpose*:

    * ``L0`` nothing established — also the level any non-verified status has.
    * ``L1`` a self-asserted channel was demonstrated (a code was received).
    * ``L2`` an authoritative source was consulted (a registry, an official
      identity check).
    * ``L3`` reserved for in-person or government-attested proofing. No method
      reaches it today; it exists so that a future high-assurance operation has
      somewhere to point that current methods cannot satisfy.

    L4/L5 were removed in AUTH-004. They existed only to rank *organization*
    and *professional* verification above identity proofing on a single ladder,
    which is the conflation this module now refuses to express.
    """

    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


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
    """Single authoritative mapping from method to (purpose, assurance).

    A method establishes exactly one purpose. Before AUTH-004 this was a map to
    a bare level, and ``organization_registry`` sat at L4 — above
    ``official_identity`` at L2 — so an account whose *organization* had been
    verified out-ranked one whose *holder's identity* had been proven. Any
    caller asking for "at least L2, meaning we know who this person is" was
    satisfied by an organization check. Purposes are not comparable, so they no
    longer share a ladder.
    """

    _METHODS: dict[VerificationMethod, tuple[VerificationPurpose, AssuranceLevel]] = {
        # Account control: a code arrived at an address the holder controls.
        VerificationMethod.email: (VerificationPurpose.contact, AssuranceLevel.L1),
        VerificationMethod.phone: (VerificationPurpose.contact, AssuranceLevel.L1),
        # Identity: only an authoritative source establishes it. OCR and NFC are
        # capture techniques — they read a document, they do not attest to it —
        # so alone they establish nothing and stay at L0 until an authority
        # validates what was captured.
        VerificationMethod.official_identity: (VerificationPurpose.identity, AssuranceLevel.L2),
        VerificationMethod.ocr: (VerificationPurpose.identity, AssuranceLevel.L0),
        VerificationMethod.nfc: (VerificationPurpose.identity, AssuranceLevel.L0),
        # Registries attest to a licence or an entity, never to a person's identity.
        VerificationMethod.professional_registry: (VerificationPurpose.professional, AssuranceLevel.L2),
        VerificationMethod.organization_registry: (VerificationPurpose.organization, AssuranceLevel.L2),
    }

    @classmethod
    def purpose_for(cls, method: VerificationMethod) -> VerificationPurpose:
        try:
            return cls._METHODS[method][0]
        except KeyError:
            raise ValueError(f"No purpose is declared for verification method {method!r}") from None

    @classmethod
    def assurance_for(cls, result: VerificationResult) -> AssuranceLevel:
        """The level this single result establishes for its own purpose."""
        if result.status != VerificationStatus.verified:
            return AssuranceLevel.L0
        entry = cls._METHODS.get(result.method)
        if entry is None:
            # An unmapped method proves nothing. Falling back to the provider's
            # self-reported assurance would let a provider grade its own work.
            return AssuranceLevel.L0
        return entry[1]


@dataclass(frozen=True)
class AssuranceProfile:
    """What has been established, per purpose.

    This replaces a single scalar. A profile can say "we know how to reach this
    person and their employer is a real hospital, and we do not know who they
    are" — which a single number cannot express without lying in one direction
    or the other.
    """

    levels: dict[VerificationPurpose, AssuranceLevel]

    def level_for(self, purpose: VerificationPurpose) -> AssuranceLevel:
        return self.levels.get(purpose, AssuranceLevel.L0)

    def meets(self, purpose: VerificationPurpose, required: AssuranceLevel) -> bool:
        return _ASSURANCE_ORDER[self.level_for(purpose)] >= _ASSURANCE_ORDER[required]


class AssuranceEngine:
    """Central server-side assurance evaluator; callers do not compare strings."""

    @staticmethod
    def profile_for(results: list[VerificationResult]) -> AssuranceProfile:
        levels: dict[VerificationPurpose, AssuranceLevel] = {}
        for result in results:
            level = VerificationPolicy.assurance_for(result)
            if level == AssuranceLevel.L0:
                continue
            purpose = VerificationPolicy.purpose_for(result.method)
            current = levels.get(purpose, AssuranceLevel.L0)
            if _ASSURANCE_ORDER[level] > _ASSURANCE_ORDER[current]:
                levels[purpose] = level
        return AssuranceProfile(levels=levels)

    @staticmethod
    def level_for(results: list[VerificationResult], purpose: VerificationPurpose) -> AssuranceLevel:
        """The level established for one named purpose.

        ``purpose`` is required. A caller that does not say which question it is
        asking cannot be answered safely, and the resulting ``TypeError`` fails
        closed at the call site rather than returning a number that means
        something other than what the caller assumed.
        """
        return AssuranceEngine.profile_for(results).level_for(purpose)

    @staticmethod
    def require(
        results: list[VerificationResult],
        purpose: VerificationPurpose,
        required: AssuranceLevel,
    ) -> None:
        profile = AssuranceEngine.profile_for(results)
        if not profile.meets(purpose, required):
            actual = profile.level_for(purpose)
            raise PermissionError(
                f"Required {purpose.value} assurance {required.value}; "
                f"actual {purpose.value} assurance {actual.value}"
            )
