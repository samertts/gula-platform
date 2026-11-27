"""Wave 05.3 internal government-verification adapter contract.

This module does not connect to a government system, add credentials, define a
real authority, or claim that synthetic output is government verification. It
defines the internal request/result contract, a default-empty authority
registry, fail-closed status handling, replay/idempotency guards, and a clearly
labelled synthetic mock for tests.

Canonical audit, NID normalization/hashing, and gateway trust-level primitives
are reused. No route, dependency, migration, or production configuration is
changed.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from app._compat import UTC
from app.gateways.base import DataTrustLevel
from app.identity.services.canonical_audit import AuditEventInput
from app.national.services.identity_access import (
    NID_VERIFICATION_REQUESTED,
    NID_VERIFICATION_RESULT,
    UNAUTHORIZED_ACCESS_ATTEMPT,
    build_wave053_audit_event,
)
from app.national.services.identity_governance import (
    GOVERNMENT_SOURCE_CONFIRMED,
    REVIEW_REQUIRED,
    GovernmentVerificationEvidence,
    IdentityEvidenceError,
    VerificationTransitionContext,
)
from app.services.identity import normalize_national_id


class GovernmentVerificationError(ValueError):
    """Base error for government adapter contract violations."""


class AdapterSecurityError(GovernmentVerificationError):
    """Raised when transport, replay, or registry security gates fail."""


class VerificationStatus(StrEnum):
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    NOT_FOUND = "NOT_FOUND"
    INDETERMINATE = "INDETERMINATE"
    TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTHORITY_UNAVAILABLE = "AUTHORITY_UNAVAILABLE"


ALL_VERIFICATION_STATUSES = frozenset(VerificationStatus)

# Wave 05.3 has no approved real authority. This explicit gate keeps the future
# state-upgrade branch documented while making it unreachable in this wave.
REAL_AUTHORITY_UPGRADE_APPROVED = False

_NON_AUTHORITATIVE_STATUSES = frozenset(
    {
        VerificationStatus.NOT_VERIFIED,
        VerificationStatus.NOT_FOUND,
        VerificationStatus.INDETERMINATE,
        VerificationStatus.TEMPORARILY_UNAVAILABLE,
        VerificationStatus.INVALID_REQUEST,
        VerificationStatus.AUTHORITY_UNAVAILABLE,
    },
)

_HEX_HASH = re.compile(r"^[0-9a-f]{64}$")
_OPAQUE_REFERENCE = re.compile(r"^[A-Za-z0-9._:\-/]{1,200}$")
_KEY_MATERIAL_MARKERS = ("-----BEGIN", "PRIVATE KEY", "SECRET KEY")


@dataclass(frozen=True)
class AdapterPolicy:
    """Bounded resilience policy required before any live authority is used."""

    timeout_seconds: float = 10.0
    max_attempts: int = 2
    bounded_backoff_base_seconds: float = 0.5
    bounded_backoff_max_seconds: float = 2.0
    replay_window_seconds: int = 300
    max_future_skew_seconds: int = 60
    rate_limit_per_minute: int = 20
    circuit_failure_threshold: int = 3
    circuit_cooldown_seconds: float = 120.0

    def __post_init__(self) -> None:
        if not 0 < self.timeout_seconds <= 60:
            raise GovernmentVerificationError("timeout must be positive and bounded")
        if not 1 <= self.max_attempts <= 5:
            raise GovernmentVerificationError("attempts must be bounded")
        if not 0 <= self.bounded_backoff_base_seconds <= self.bounded_backoff_max_seconds <= 10:
            raise GovernmentVerificationError("backoff must be bounded")
        if self.replay_window_seconds < 30 or self.max_future_skew_seconds < 0:
            raise GovernmentVerificationError("replay window is invalid")
        if self.rate_limit_per_minute < 1 or self.rate_limit_per_minute > 1000:
            raise GovernmentVerificationError("rate limit must be bounded")
        if self.circuit_failure_threshold < 1 or self.circuit_cooldown_seconds <= 0:
            raise GovernmentVerificationError("circuit breaker policy is invalid")


def bounded_backoff_delay(attempt: int, policy: AdapterPolicy) -> float:
    """Return a deterministic bounded backoff for a zero-based retry attempt."""
    if attempt < 0:
        raise GovernmentVerificationError("attempt must be non-negative")
    return min(policy.bounded_backoff_max_seconds, policy.bounded_backoff_base_seconds * attempt)


@dataclass(frozen=True)
class VerificationRequest:
    """Internal request using opaque references, never a raw national number."""

    correlation_id: str
    idempotency_key: str
    subject_reference: str
    national_id_hash: str
    lookup_token: str
    purpose: str
    actor: str
    organization_id: str
    facility_id: str
    requested_at: datetime

    def __post_init__(self) -> None:
        for label, value in (
            ("correlation_id", self.correlation_id),
            ("idempotency_key", self.idempotency_key),
            ("subject_reference", self.subject_reference),
            ("lookup_token", self.lookup_token),
            ("purpose", self.purpose),
            ("actor", self.actor),
            ("organization_id", self.organization_id),
            ("facility_id", self.facility_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise GovernmentVerificationError(f"{label} is required")
        if _OPAQUE_REFERENCE.fullmatch(self.subject_reference) is None:
            raise GovernmentVerificationError("subject reference must be an opaque reference")
        if re.fullmatch(r"\d{9,14}", self.subject_reference):
            raise GovernmentVerificationError("subject reference must not be a raw national number")
        if _HEX_HASH.fullmatch(self.national_id_hash) is None:
            raise GovernmentVerificationError("national ID hash must be a 64-character hex digest")
        if _OPAQUE_REFERENCE.fullmatch(self.lookup_token) is None:
            raise GovernmentVerificationError("lookup token must be opaque")
        if re.fullmatch(r"v[1-9][0-9]{0,2}\.[0-9a-f]{64}", self.lookup_token) is None:
            raise GovernmentVerificationError("lookup token must be a bounded versioned keyed HMAC digest")
        if self.lookup_token == self.national_id_hash:
            raise GovernmentVerificationError("lookup token must be distinct from the identity hash")

    def fingerprint(self) -> str:
        payload = "|".join(
            (
                self.correlation_id,
                self.idempotency_key,
                self.subject_reference,
                self.national_id_hash,
                self.lookup_token,
                self.purpose,
                self.actor,
                self.organization_id,
                self.facility_id,
                self.requested_at.isoformat(),
            ),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class VerifiedAttribute:
    """A verified attribute name with a protected, non-raw value."""

    name: str
    protected_value: str
    source_authority: str

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.protected_value.strip() or not self.source_authority.strip():
            raise GovernmentVerificationError("verified attribute fields are required")
        digits = normalize_national_id(self.protected_value)
        if digits and digits == self.protected_value:
            raise GovernmentVerificationError("verified attribute must not contain a raw national number")


@dataclass(frozen=True)
class VerificationResponse:
    """Internal verification result with full provenance and no raw NID."""

    correlation_id: str
    request_id: str
    status: VerificationStatus
    source_authority: str
    verified_attributes: tuple[VerifiedAttribute, ...]
    timestamp: datetime
    response_status: str
    failure_reason: str | None
    evidence_reference: str
    nonce: str
    sent_at: datetime
    signature_reference: str | None = None
    synthetic: bool = True

    def __post_init__(self) -> None:
        if not self.correlation_id.strip() or not self.request_id.strip():
            raise GovernmentVerificationError("correlation and request identifiers are required")
        if not self.source_authority.strip() or not self.evidence_reference.strip():
            raise GovernmentVerificationError("authority and evidence reference are required")
        if not self.nonce.strip() or _OPAQUE_REFERENCE.fullmatch(self.nonce) is None:
            raise GovernmentVerificationError("nonce must be opaque")
        if self.status in _NON_AUTHORITATIVE_STATUSES and not self.failure_reason:
            raise GovernmentVerificationError("non-authoritative status requires a failure reason")
        if self.status is VerificationStatus.VERIFIED and self.failure_reason:
            raise GovernmentVerificationError("verified status cannot carry a failure reason")
        if not 100 <= int(self.response_status) <= 599:
            raise GovernmentVerificationError("response_status must be an HTTP-like status")
        if self.signature_reference is not None and _OPAQUE_REFERENCE.fullmatch(self.signature_reference) is None:
            raise GovernmentVerificationError("signature reference must be opaque")

    def public(self) -> dict[str, object]:
        """Bounded representation that is safe for logs and audit metadata."""
        return {
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "status": self.status.value,
            "source_authority": self.source_authority,
            "attribute_names": tuple(item.name for item in self.verified_attributes),
            "timestamp": self.timestamp.isoformat(),
            "response_status": self.response_status,
            "failure_reason": self.failure_reason,
            "evidence_reference": self.evidence_reference,
            "signature_reference": self.signature_reference,
            "synthetic": self.synthetic,
        }


class AuthorityRegistryError(GovernmentVerificationError):
    """Raised when an authority fails registry approval or validity checks."""


@dataclass(frozen=True)
class AuthorityRegistryEntry:
    """An authority record. It stores references only, never key material."""

    authority_id: str
    organization: str
    service_name: str
    trust_level: DataTrustLevel
    valid_from: datetime
    valid_until: datetime
    approval_reference: str
    public_key_reference: str | None = None
    revocation_reference: str | None = None
    revoked: bool = False
    synthetic: bool = True

    def __post_init__(self) -> None:
        for label, value in (
            ("authority_id", self.authority_id),
            ("organization", self.organization),
            ("service_name", self.service_name),
            ("approval_reference", self.approval_reference),
        ):
            if not isinstance(value, str) or not value.strip():
                raise AuthorityRegistryError(f"{label} is required")
        if self.valid_until <= self.valid_from:
            raise AuthorityRegistryError("authority validity window is invalid")
        if self.public_key_reference is not None:
            if _OPAQUE_REFERENCE.fullmatch(self.public_key_reference) is None:
                raise AuthorityRegistryError("public key reference must be an opaque reference")
            upper = self.public_key_reference.upper()
            if any(marker in upper for marker in _KEY_MATERIAL_MARKERS):
                raise AuthorityRegistryError("authority registry must not store key material")
        if self.revoked and not self.revocation_reference:
            raise AuthorityRegistryError("revocation requires a reference")


class AuthorityRegistry:
    """Default-empty authority registry. Real authorities remain NOT APPROVED."""

    def __init__(self) -> None:
        self._entries: dict[str, AuthorityRegistryEntry] = {}
        self._lock = threading.Lock()

    def register(self, entry: AuthorityRegistryEntry) -> None:
        if entry.authority_id in self._entries:
            raise AuthorityRegistryError("authority already registered")
        self._entries[entry.authority_id] = entry

    def revoke(self, authority_id: str, *, reference: str, at: datetime) -> None:
        if not reference.strip():
            raise AuthorityRegistryError("revocation reference is required")
        with self._lock:
            entry = self._entries.get(authority_id)
            if entry is None:
                raise AuthorityRegistryError("authority is not registered")
            revoked = AuthorityRegistryEntry(
                authority_id=entry.authority_id,
                organization=entry.organization,
                service_name=entry.service_name,
                trust_level=entry.trust_level,
                valid_from=entry.valid_from,
                valid_until=entry.valid_until,
                approval_reference=entry.approval_reference,
                public_key_reference=entry.public_key_reference,
                revocation_reference=reference,
                revoked=True,
                synthetic=entry.synthetic,
            )
            self._entries[authority_id] = revoked
        del at

    def resolve(self, authority_id: str, *, at: datetime, require_signed: bool = True) -> AuthorityRegistryEntry:
        """Resolve an authority or fail closed."""
        with self._lock:
            entry = self._entries.get(authority_id)
        if entry is None:
            raise AuthorityRegistryError("authority is not registered")
        if entry.revoked:
            raise AuthorityRegistryError("authority is revoked")
        if not entry.synthetic:
            raise AuthorityRegistryError("real authority registration is NOT APPROVED")
        if not entry.approval_reference.strip():
            raise AuthorityRegistryError("authority approval reference is required")
        if not (entry.valid_from <= at <= entry.valid_until):
            raise AuthorityRegistryError("authority validity window is not active")
        if require_signed and entry.public_key_reference is None:
            raise AuthorityRegistryError("signed authority requires a public key reference")
        if entry.trust_level is DataTrustLevel.CRITICAL:
            raise AuthorityRegistryError("external authority cannot hold CRITICAL trust")
        return entry

    def entries(self) -> tuple[AuthorityRegistryEntry, ...]:
        with self._lock:
            return tuple(self._entries.values())


class NonceReplayGuard:
    """Bounded in-memory nonce replay guard for synthetic tests."""

    def __init__(self) -> None:
        self._seen: dict[str, float] = {}
        self._lock = threading.Lock()

    def check(
        self,
        *,
        nonce: str,
        sent_at: datetime,
        now: datetime,
        policy: AdapterPolicy,
    ) -> None:
        age = (now - sent_at).total_seconds()
        if age > policy.replay_window_seconds or age < -policy.max_future_skew_seconds:
            raise AdapterSecurityError("message timestamp is outside the replay window")
        with self._lock:
            if nonce in self._seen:
                raise AdapterSecurityError("message nonce has already been used")
            self._seen[nonce] = sent_at.timestamp()


@dataclass(frozen=True)
class AdapterSecurityRequirements:
    """Contract-level requirements, not a claim that live transport is enabled."""

    mutual_tls_when_supported: bool = True
    signed_messages: bool = True
    replay_protection: bool = True
    idempotency: bool = True
    bounded_backoff: bool = True
    correlation_required: bool = True
    complete_audit: bool = True


class GovernmentVerificationAdapter(Protocol):
    def verify(
        self,
        request: VerificationRequest,
        *,
        authority_id: str,
        registry: AuthorityRegistry,
    ) -> VerificationResponse: ...


def _unauthoritative_response(
    request: VerificationRequest,
    status: VerificationStatus,
    reason: str,
) -> VerificationResponse:
    now = datetime.now(UTC)
    return VerificationResponse(
        correlation_id=request.correlation_id,
        request_id=f"SYNTHETIC-REQ-{request.idempotency_key}",
        status=status,
        source_authority="SYNTHETIC-UNAVAILABLE-AUTHORITY",
        verified_attributes=(),
        timestamp=now,
        response_status="503" if status in {
            VerificationStatus.TEMPORARILY_UNAVAILABLE,
            VerificationStatus.AUTHORITY_UNAVAILABLE,
        } else "400",
        failure_reason=reason,
        evidence_reference=f"SYNTHETIC-EVIDENCE-{request.idempotency_key}",
        nonce=f"SYNTHETIC-NONCE-{request.idempotency_key}-{time.time_ns()}",
        sent_at=now,
        synthetic=True,
    )


class SyntheticGovernmentVerificationAdapter:
    """Clearly labelled mock adapter. It never contacts an authority."""

    def __init__(
        self,
        *,
        policy: AdapterPolicy | None = None,
        status: VerificationStatus = VerificationStatus.NOT_VERIFIED,
        requirements: AdapterSecurityRequirements | None = None,
    ) -> None:
        self.policy = policy or AdapterPolicy()
        self.status = status
        self.requirements = requirements or AdapterSecurityRequirements()
        self._cache: dict[str, tuple[str, VerificationResponse]] = {}
        self._replay = NonceReplayGuard()
        self._requests: list[float] = []
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0
        self._lock = threading.Lock()

    def verify(
        self,
        request: VerificationRequest,
        *,
        authority_id: str,
        registry: AuthorityRegistry,
        at: datetime | None = None,
    ) -> VerificationResponse:
        """Return a synthetic result while enforcing the internal safety gates."""
        now = at or datetime.now(UTC)
        fingerprint = request.fingerprint()

        with self._lock:
            cached = self._cache.get(request.idempotency_key)
            if cached is not None:
                old_fingerprint, response = cached
                if not hmac.compare_digest(old_fingerprint, fingerprint):
                    return _unauthoritative_response(
                        request,
                        VerificationStatus.INVALID_REQUEST,
                        "idempotency key reused with a different request",
                    )
                return response

            if now.timestamp() < self._circuit_open_until:
                return _unauthoritative_response(
                    request,
                    VerificationStatus.TEMPORARILY_UNAVAILABLE,
                    "synthetic circuit breaker is open",
                )

            window_start = now.timestamp() - 60
            self._requests = [stamp for stamp in self._requests if stamp >= window_start]
            if len(self._requests) >= self.policy.rate_limit_per_minute:
                return _unauthoritative_response(
                    request,
                    VerificationStatus.TEMPORARILY_UNAVAILABLE,
                    "synthetic rate limit exceeded",
                )
            self._requests.append(now.timestamp())

        try:
            authority = registry.resolve(
                authority_id,
                at=now,
                require_signed=self.requirements.signed_messages,
            )
        except AuthorityRegistryError:
            with self._lock:
                self._consecutive_failures += 1
                if self._consecutive_failures >= self.policy.circuit_failure_threshold:
                    self._circuit_open_until = now.timestamp() + self.policy.circuit_cooldown_seconds
            return _unauthoritative_response(
                request,
                VerificationStatus.AUTHORITY_UNAVAILABLE,
                "authority is unavailable or not approved",
            )

        if self.status is VerificationStatus.VERIFIED:
            attributes = (
                VerifiedAttribute(
                    name="identity_presence",
                    protected_value=f"ATTESTED-{request.subject_reference}",
                    source_authority=authority.authority_id,
                ),
            )
            failure_reason = None
            response_status = "200"
        else:
            attributes = ()
            failure_reason = f"SYNTHETIC_RESULT_{self.status.value}"
            response_status = "404" if self.status is VerificationStatus.NOT_FOUND else "200"

        response = VerificationResponse(
            correlation_id=request.correlation_id,
            request_id=f"SYNTHETIC-REQ-{request.idempotency_key}",
            status=self.status,
            source_authority=authority.authority_id,
            verified_attributes=attributes,
            timestamp=now,
            response_status=response_status,
            failure_reason=failure_reason,
            evidence_reference=f"SYNTHETIC-EVIDENCE-{request.idempotency_key}",
            nonce=f"SYNTHETIC-NONCE-{request.idempotency_key}-{time.time_ns()}",
            sent_at=now,
            signature_reference=f"SYNTHETIC-SIGNATURE-{authority.authority_id}",
            synthetic=True,
        )
        try:
            self._replay.check(
                nonce=response.nonce,
                sent_at=response.sent_at,
                now=now,
                policy=self.policy,
            )
        except AdapterSecurityError:
            return _unauthoritative_response(
                request,
                VerificationStatus.INVALID_REQUEST,
                "synthetic replay validation failed",
            )

        with self._lock:
            self._consecutive_failures = 0
            self._cache[request.idempotency_key] = (fingerprint, response)
        return response


@dataclass(frozen=True)
class AdapterDecision:
    """A fail-closed mapping from adapter status to identity governance."""

    status: VerificationStatus
    verification_event: str | None
    state_upgrade_allowed: bool
    reason: str
    audit_event: AuditEventInput


def decision_for_adapter_result(
    request: VerificationRequest,
    response: VerificationResponse,
    registry: AuthorityRegistry,
    *,
    actor: str,
    at: datetime,
) -> AdapterDecision:
    """Map an adapter result without allowing synthetic data to verify identity."""
    if response.correlation_id != request.correlation_id:
        raise AdapterSecurityError("response correlation id does not match the request")

    raw_audit_values: tuple[str | None, ...] = (
        response.failure_reason,
        response.source_authority,
        response.evidence_reference,
        response.request_id,
        response.correlation_id,
        response.signature_reference,
        *(
            value
            for attribute in response.verified_attributes
            for value in (attribute.name, attribute.protected_value, attribute.source_authority)
        ),
    )
    audit_event = build_wave053_audit_event(
        operation=NID_VERIFICATION_RESULT,
        actor_id=actor,
        purpose=request.purpose,
        facility_id=request.facility_id,
        organization_id=request.organization_id,
        gula_citizen_identifier=request.subject_reference,
        national_id_hash=request.national_id_hash,
        metadata={
            "status": response.status.value,
            "source_authority": response.source_authority,
            "correlation_id": response.correlation_id,
            "request_id": response.request_id,
            "evidence_reference": response.evidence_reference,
            "synthetic": response.synthetic,
            "response_public": response.public(),
        },
        correlation_id=request.correlation_id,
        raw_nid_for_check=None,
        raw_nid_values=raw_audit_values,
    )

    if response.status is not VerificationStatus.VERIFIED:
        return AdapterDecision(
            status=response.status,
            verification_event=None,
            state_upgrade_allowed=False,
            reason=response.failure_reason or "verification result is not authoritative",
            audit_event=audit_event,
        )

    try:
        authority = registry.resolve(
            response.source_authority,
            at=at,
            require_signed=True,
        )
    except AuthorityRegistryError as exc:
        raise AdapterSecurityError("verified result has no approved authority") from exc

    if not REAL_AUTHORITY_UPGRADE_APPROVED or response.synthetic or authority.synthetic:
        return AdapterDecision(
            status=response.status,
            verification_event=REVIEW_REQUIRED,
            state_upgrade_allowed=False,
            reason="no approved real authority, synthetic result, or synthetic authority can grant verification",
            audit_event=audit_event,
        )

    return AdapterDecision(
        status=response.status,
        verification_event=GOVERNMENT_SOURCE_CONFIRMED,
        state_upgrade_allowed=True,
        reason="approved authority result requires an authorized identity decision",
        audit_event=audit_event,
    )


def government_evidence_from_response(
    response: VerificationResponse,
    *,
    registry: AuthorityRegistry,
    at: datetime,
) -> GovernmentVerificationEvidence:
    """Build canonical government evidence or fail closed."""
    if response.status is not VerificationStatus.VERIFIED or response.synthetic:
        raise IdentityEvidenceError("synthetic or non-verified result is not government evidence")
    entry = registry.resolve(response.source_authority, at=at, require_signed=True)
    if entry.synthetic:
        raise IdentityEvidenceError("synthetic authority is not an official source")
    if not response.evidence_reference.strip() or not response.request_id.strip():
        raise IdentityEvidenceError("government evidence is incomplete")
    return GovernmentVerificationEvidence(
        authority=response.source_authority,
        operation_id=response.request_id,
        status=response.status.value,
        verified_at=response.timestamp,
    )


def verification_transition_context(
    request: VerificationRequest,
    response: VerificationResponse,
    *,
    reviewer: str | None = None,
    reason: str | None = None,
) -> VerificationTransitionContext:
    """Build the canonical transition context without exposing raw identifiers."""
    return VerificationTransitionContext(
        actor=request.actor,
        reviewer=reviewer,
        purpose=request.purpose,
        facility_id=request.facility_id,
        source="official_government_source",
        reason=reason or response.failure_reason,
        evidence_reference=response.evidence_reference,
        government_authority=response.source_authority,
        government_operation_id=response.request_id,
    )


def request_audit_event(
    request: VerificationRequest,
    *,
    authority_id: str,
) -> AuditEventInput:
    """Create the canonical audit event for a verification request."""
    return build_wave053_audit_event(
        operation=NID_VERIFICATION_REQUESTED,
        actor_id=request.actor,
        purpose=request.purpose,
        facility_id=request.facility_id,
        organization_id=request.organization_id,
        gula_citizen_identifier=request.subject_reference,
        national_id_hash=request.national_id_hash,
        metadata={
            "authority_id": authority_id,
            "correlation_id": request.correlation_id,
            "idempotency_key": request.idempotency_key,
            "lookup_token_version": request.lookup_token.split(".", 1)[0],
        },
        correlation_id=request.correlation_id,
        raw_nid_for_check=None,
        raw_nid_values=(
            request.actor,
            request.purpose,
            request.organization_id,
            request.facility_id,
            request.correlation_id,
            request.idempotency_key,
            request.subject_reference,
            request.lookup_token,
            request.lookup_token.split(".", 1)[0],
            authority_id,
        ),
    )


def unauthorized_attempt_audit_event(
    *,
    actor: str,
    purpose: str,
    organization_id: str,
    facility_id: str,
    subject_reference: str,
    national_id_hash: str,
    reason_code: str,
) -> AuditEventInput:
    """Create a canonical audit event for an unauthorized verification attempt."""
    return build_wave053_audit_event(
        operation=UNAUTHORIZED_ACCESS_ATTEMPT,
        actor_id=actor,
        purpose=purpose,
        facility_id=facility_id,
        organization_id=organization_id,
        gula_citizen_identifier=subject_reference,
        national_id_hash=national_id_hash,
        decision="deny",
        reason_code=reason_code,
        metadata={"reason_code": reason_code},
        raw_nid_for_check=None,
        raw_nid_values=(
            actor,
            purpose,
            organization_id,
            facility_id,
            subject_reference,
            reason_code,
        ),
    )


__all__ = [
    "ALL_VERIFICATION_STATUSES",
    "AdapterPolicy",
    "AdapterSecurityError",
    "AdapterSecurityRequirements",
    "AuthorityRegistry",
    "AuthorityRegistryEntry",
    "AuthorityRegistryError",
    "DataTrustLevel",
    "GovernmentVerificationAdapter",
    "GovernmentVerificationError",
    "NonceReplayGuard",
    "SyntheticGovernmentVerificationAdapter",
    "VerificationRequest",
    "VerificationResponse",
    "VerificationStatus",
    "VerifiedAttribute",
    "bounded_backoff_delay",
    "decision_for_adapter_result",
    "government_evidence_from_response",
    "request_audit_event",
    "unauthorized_attempt_audit_event",
    "verification_transition_context",
]
