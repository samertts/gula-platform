"""Synthetic citizen account registration lifecycle.

This module implements the staged citizen-account boundary authorized after the
Wave 05.3 closure review. It is deliberately additive and reversible:

* no DDL, migration, trigger, schema change, HTTP route, or government client;
* no real citizen data, card image, raw NFC payload, chip key, or credential;
* no duplicate identity, MPI, audit, authorization, or patient system;
* no path from an initial account to ``ACCOUNT_ACTIVE`` or medical data access.

Canonical components are reused directly: the Decision Engine, canonical audit
event builder, Wave 05.3 access guards, identity governance state machine,
NIDP original-card evaluator, MPI linkage guard, and idempotent identifier
reservation. All lifecycle persistence here is an in-process synthetic store;
durable persistence remains PROPOSED / PENDING SCHEMA OWNER APPROVAL.

Role names and purposes are design labels. The production role matrix remains
PENDING legal/clinical/institutional approval.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import threading
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, Protocol

from app._compat import UTC
from app.identity.services.authorization_decision import (
    AuthorizationDecision,
    AuthorizationDecisionService,
)
from app.national.services.document_authenticity import (
    DocumentAuthenticityDecision,
    NidpEvidenceBundle,
    apply_authenticity_transition,
    assert_no_manual_authenticity_override,
    evaluate_document_authenticity,
    registration_eligibility,
)
from app.national.services.identity_access import (
    DOCUMENT_REVIEW,
    IDENTITY_APPROVAL,
    IDENTITY_CORRECTION,
    IDENTITY_CREATED,
    IDENTITY_READ,
    IDENTITY_REJECTION,
    IDENTITY_SUSPENSION,
    NID_VERIFICATION_REQUESTED,
    REVIEW_OUTCOME,
    UNAUTHORIZED_VERIFICATION_ATTEMPT,
    IdentityAccessContext,
    IdentityAccessGrant,
    IdentityRole,
    assert_identity_access_v2,
    build_wave053_audit_event,
)
from app.national.services.identity_governance import (
    PENDING_REVIEW,
    UNVERIFIED,
    VERIFIED,
    IdentityTransitionError,
    LinkageCandidate,
    LinkageReviewer,
    assert_identity_access_allowed,
    assert_linkage_allowed,
)
from app.national.services.identity_persistence import (
    IdempotencyStore,
    RegistrationCoordinatorError,
    RegistrationRecord,
    RegistrationRequest,
    register_citizen_idempotently,
)

SYNTHETIC_NID_HASH = "0" * 64
REGISTRATION_PURPOSE = "citizen_workspace"
STAFF_REVIEW_PURPOSE = "ADMINISTRATION"
_OPAQUE_REFERENCE = re.compile(r"^[A-Za-z0-9._:\-/]{1,200}$")
_CONTACT_CODE = re.compile(r"^[0-9]{6}$")
_RAW_NID_RUN = re.compile(r"(?<!\d)\d{9,14}(?!\d)")


class CitizenRegistrationError(ValueError):
    """Base error for the synthetic citizen registration boundary."""


class InvalidRegistrationTransitionError(CitizenRegistrationError):
    """Raised when a lifecycle event is not allowed from the current state."""


class RegistrationAuthorizationError(PermissionError):
    """Raised when a canonical authorization decision is missing or denied."""


class MedicalDataAccessDeniedError(PermissionError):
    """Raised when an account that is not fully activated requests medical data."""


class RegistrationReplayError(CitizenRegistrationError):
    """Raised when a lifecycle event is replayed with different decision inputs."""


class RegistrationConflictError(CitizenRegistrationError):
    """Raised when duplicate or conflicting registration evidence is detected."""


class RegistrationEvidenceError(CitizenRegistrationError):
    """Raised when lifecycle evidence metadata is missing or malformed."""


class ActorType(StrEnum):
    """Design-time actor categories; the production role matrix is not approved."""

    CITIZEN = "citizen"
    STAFF = "staff"
    INSTITUTION = "institution"
    SYSTEM = "system"


class RegistrationLifecycleState(StrEnum):
    NOT_CREATED = "NO_ACCOUNT"
    INITIAL_ACCOUNT = "INITIAL_ACCOUNT_CREATED"
    CONTACT_VERIFIED = "CONTACT_VERIFIED"
    IDENTITY_SUBMITTED = "NATIONAL_IDENTITY_SUBMITTED"
    IDENTITY_REVIEW = "NATIONAL_IDENTITY_PENDING_REVIEW"
    HEALTH_APPROVED = "HEALTH_IDENTITY_APPROVED"
    SERVICE_ACTIVE = "SERVICE_ACTIVE"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class RegistrationLifecycleEvent(StrEnum):
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    CONTACT_VERIFIED = "CONTACT_VERIFIED"
    IDENTITY_SUBMITTED = "IDENTITY_SUBMITTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    HEALTH_APPROVED = "HEALTH_APPROVED"
    SERVICE_ACTIVATED = "SERVICE_ACTIVATED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"
    RESUBMITTED = "RESUBMITTED"
    APPEAL_RECONSIDERED = "APPEAL_RECONSIDERED"
    MANUAL_REVIEW_REQUESTED = "MANUAL_REVIEW_REQUESTED"


_LIFECYCLE_TRANSITIONS: dict[RegistrationLifecycleState, dict[RegistrationLifecycleEvent, RegistrationLifecycleState]] = {
    RegistrationLifecycleState.INITIAL_ACCOUNT: {
        RegistrationLifecycleEvent.CONTACT_VERIFIED: RegistrationLifecycleState.CONTACT_VERIFIED,
        RegistrationLifecycleEvent.REJECTED: RegistrationLifecycleState.REJECTED,
    },
    RegistrationLifecycleState.CONTACT_VERIFIED: {
        RegistrationLifecycleEvent.IDENTITY_SUBMITTED: RegistrationLifecycleState.IDENTITY_SUBMITTED,
        RegistrationLifecycleEvent.REJECTED: RegistrationLifecycleState.REJECTED,
    },
    RegistrationLifecycleState.IDENTITY_SUBMITTED: {
        RegistrationLifecycleEvent.REVIEW_REQUIRED: RegistrationLifecycleState.IDENTITY_REVIEW,
        RegistrationLifecycleEvent.MANUAL_REVIEW_REQUESTED: RegistrationLifecycleState.IDENTITY_REVIEW,
        RegistrationLifecycleEvent.REJECTED: RegistrationLifecycleState.REJECTED,
    },
    RegistrationLifecycleState.IDENTITY_REVIEW: {
        RegistrationLifecycleEvent.HEALTH_APPROVED: RegistrationLifecycleState.HEALTH_APPROVED,
        RegistrationLifecycleEvent.MANUAL_REVIEW_REQUESTED: RegistrationLifecycleState.IDENTITY_REVIEW,
        RegistrationLifecycleEvent.SUSPENDED: RegistrationLifecycleState.SUSPENDED,
        RegistrationLifecycleEvent.REJECTED: RegistrationLifecycleState.REJECTED,
    },
    RegistrationLifecycleState.HEALTH_APPROVED: {
        RegistrationLifecycleEvent.SERVICE_ACTIVATED: RegistrationLifecycleState.SERVICE_ACTIVE,
        RegistrationLifecycleEvent.SUSPENDED: RegistrationLifecycleState.SUSPENDED,
        RegistrationLifecycleEvent.REJECTED: RegistrationLifecycleState.REJECTED,
    },
    RegistrationLifecycleState.SERVICE_ACTIVE: {
        RegistrationLifecycleEvent.SUSPENDED: RegistrationLifecycleState.SUSPENDED,
    },
    RegistrationLifecycleState.SUSPENDED: {
        RegistrationLifecycleEvent.REVIEW_REQUIRED: RegistrationLifecycleState.IDENTITY_REVIEW,
        RegistrationLifecycleEvent.RESUBMITTED: RegistrationLifecycleState.IDENTITY_REVIEW,
        RegistrationLifecycleEvent.APPEAL_RECONSIDERED: RegistrationLifecycleState.IDENTITY_REVIEW,
        RegistrationLifecycleEvent.REJECTED: RegistrationLifecycleState.REJECTED,
    },
    RegistrationLifecycleState.REJECTED: {
        RegistrationLifecycleEvent.APPEAL_RECONSIDERED: RegistrationLifecycleState.IDENTITY_REVIEW,
    },
}


@dataclass(frozen=True)
class CitizenRegistrationAccount:
    """A synthetic account; no raw national identifier is ever retained."""

    gula_citizen_identifier: str
    subject_reference: str
    contact_reference: str
    registration_record: RegistrationRecord
    lifecycle_state: RegistrationLifecycleState
    verification_state: str = UNVERIFIED
    evidence_reference: str | None = None
    updated_at: datetime | None = None
    organization_id: str = ""
    facility_id: str = ""

    @property
    def can_access_medical_data(self) -> bool:
        return self.lifecycle_state is RegistrationLifecycleState.SERVICE_ACTIVE

    def to_public_dict(self) -> dict[str, Any]:
        """Return a bounded presentation model safe for a citizen workspace."""
        return {
            "gula_citizen_identifier": self.gula_citizen_identifier,
            "contact_reference": self.contact_reference,
            "lifecycle_state": self.lifecycle_state.value,
            "verification_state": self.verification_state,
            "can_access_medical_data": self.can_access_medical_data,
        }


@dataclass(frozen=True)
class RegistrationContext:
    """Trusted caller context; decisions come only from the canonical engine."""

    decision: AuthorizationDecision
    actor_id: str
    actor_type: ActorType
    organization_id: str
    facility_id: str
    purpose: str = REGISTRATION_PURPOSE
    now: datetime | None = None
    role: IdentityRole | None = None
    correlation_id: str | None = None
    national_id_hash: str = SYNTHETIC_NID_HASH

    def __post_init__(self) -> None:
        if not isinstance(self.actor_type, ActorType):
            raise RegistrationEvidenceError("actor type is required for every lifecycle decision")
        for label, value in (
            ("actor", self.actor_id),
            ("organization", self.organization_id),
            ("facility", self.facility_id),
            ("purpose", self.purpose),
        ):
            if not value or not value.strip():
                raise RegistrationEvidenceError(f"{label} is required for registration")

    def resolved_now(self) -> datetime:
        return self.now or datetime.now(UTC)


class RegistrationAccountStore(Protocol):
    """Synthetic account store contract for a future approved adapter."""

    def save(self, account: CitizenRegistrationAccount) -> None: ...

    def get(self, gula_citizen_identifier: str) -> CitizenRegistrationAccount | None: ...

    def records(self) -> tuple[CitizenRegistrationAccount, ...]: ...


class InMemoryRegistrationAccountStore:
    """Process-local synthetic store; not a second database."""

    def __init__(self) -> None:
        self._accounts: dict[str, CitizenRegistrationAccount] = {}
        self._lock = threading.Lock()

    def save(self, account: CitizenRegistrationAccount) -> None:
        with self._lock:
            self._accounts[account.gula_citizen_identifier] = account

    def get(self, gula_citizen_identifier: str) -> CitizenRegistrationAccount | None:
        with self._lock:
            return self._accounts.get(gula_citizen_identifier)

    def records(self) -> tuple[CitizenRegistrationAccount, ...]:
        with self._lock:
            return tuple(self._accounts.values())


def _transition_fingerprint(
    *,
    gula_citizen_identifier: str,
    event: RegistrationLifecycleEvent,
    correlation_id: str,
    actor_id: str,
    actor_type: ActorType,
    reason: str,
    decision_source: str,
    evidence_references: Sequence[str],
    authorization_decision: str,
) -> str:
    """Return a stable replay key from decision inputs.

    Lifecycle state is deliberately excluded: it changes after the first
    application, which would otherwise make an identical replay look like a
    conflict. The event plus decision inputs uniquely identify one decision.
    Wall-clock time is excluded so retries remain idempotent.
    """
    payload = {
        "actor_id": actor_id,
        "actor_type": actor_type.value,
        "authorization_decision": authorization_decision,
        "correlation_id": correlation_id,
        "decision_source": decision_source,
        "event": event.value,
        "evidence_references": sorted(evidence_references),
        "gula_citizen_identifier": gula_citizen_identifier,
        "reason": reason,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RegistrationTransitionRecord:
    """Append-only synthetic evidence for one lifecycle decision.

    This is not a durable audit authority. It binds the decision inputs to the
    canonical ``AuditEventInput`` returned by the existing Wave 05.3 builder.
    """

    transition_id: str
    gula_citizen_identifier: str
    event: RegistrationLifecycleEvent
    previous_state: RegistrationLifecycleState
    new_state: RegistrationLifecycleState
    actor_id: str
    actor_type: ActorType
    organization_id: str
    facility_id: str
    purpose: str
    occurred_at: datetime
    correlation_id: str
    reason: str
    decision_source: str
    evidence_references: tuple[str, ...]
    authorization_decision: Literal["ALLOW", "DENY"]
    authorization_reason_code: str | None
    audit_operation: str
    audit_event_reference: str
    replay_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.event, RegistrationLifecycleEvent):
            raise RegistrationEvidenceError("transition event is invalid")
        if not isinstance(self.previous_state, RegistrationLifecycleState):
            raise RegistrationEvidenceError("previous state is invalid")
        if not isinstance(self.new_state, RegistrationLifecycleState):
            raise RegistrationEvidenceError("new state is invalid")
        if not isinstance(self.actor_type, ActorType):
            raise RegistrationEvidenceError("actor type is invalid")
        if self.authorization_decision not in {"ALLOW", "DENY"}:
            raise RegistrationEvidenceError("authorization decision must be ALLOW or DENY")
        if self.occurred_at.tzinfo is None:
            raise RegistrationEvidenceError("transition timestamp must be timezone aware")
        for label, value in (
            ("transition id", self.transition_id),
            ("actor", self.actor_id),
            ("organization", self.organization_id),
            ("facility", self.facility_id),
            ("purpose", self.purpose),
            ("correlation id", self.correlation_id),
            ("decision source", self.decision_source),
            ("audit operation", self.audit_operation),
        ):
            if not value or not value.strip():
                raise RegistrationEvidenceError(f"{label} is required for a transition record")
        if not self.reason.strip():
            raise RegistrationEvidenceError("transition reason is required")
        if len(self.reason) > 500:
            raise RegistrationEvidenceError("transition reason must be at most 500 characters")
        if _RAW_NID_RUN.search(self.reason):
            raise RegistrationEvidenceError("transition reason must not contain a national number")
        for reference in self.evidence_references:
            _assert_opaque_reference("evidence reference", reference)

    def to_public_dict(self) -> dict[str, Any]:
        """Return a bounded synthetic decision summary, never a full evidence body."""
        return {
            "transition_id": self.transition_id,
            "event": self.event.value,
            "previous_state": self.previous_state.value,
            "new_state": self.new_state.value,
            "actor_type": self.actor_type.value,
            "reason_code": self.authorization_reason_code,
            "decision_source": self.decision_source,
            "correlation_id": self.correlation_id,
            "occurred_at": self.occurred_at.isoformat(),
        }


class RegistrationTransitionStore(Protocol):
    """Append-only synthetic history contract for a future approved adapter."""

    def append(self, record: RegistrationTransitionRecord) -> None: ...

    def records(self, gula_citizen_identifier: str) -> tuple[RegistrationTransitionRecord, ...]: ...


class InMemoryRegistrationTransitionStore:
    """Process-local append-only evidence; not a second audit service."""

    def __init__(self) -> None:
        self._records: dict[str, list[RegistrationTransitionRecord]] = {}
        self._ids: set[str] = set()
        self._lock = threading.Lock()

    def append(self, record: RegistrationTransitionRecord) -> None:
        with self._lock:
            if record.transition_id in self._ids:
                raise RegistrationReplayError("transition id has already been recorded")
            self._ids.add(record.transition_id)
            self._records.setdefault(record.gula_citizen_identifier, []).append(record)

    def records(self, gula_citizen_identifier: str) -> tuple[RegistrationTransitionRecord, ...]:
        with self._lock:
            return tuple(self._records.get(gula_citizen_identifier, ()))


class RegistrationReplayGuard:
    """Reject reused lifecycle correlations whose decision inputs changed.

    ``check`` is a pure preflight so a conflicting replay is rejected before
    any account mutation or audit write. ``remember`` is called only after the
    transition has been applied successfully.
    """

    def __init__(self) -> None:
        self._seen: dict[tuple[str, str], tuple[str, RegistrationTransitionRecord]] = {}
        self._lock = threading.Lock()

    def check(
        self,
        key: tuple[str, str],
        fingerprint: str,
    ) -> RegistrationTransitionRecord | None:
        with self._lock:
            existing = self._seen.get(key)
            if existing is None:
                return None
            if existing[0] != fingerprint:
                raise RegistrationReplayError(
                    "lifecycle correlation was replayed with different decision inputs",
                )
            return existing[1]

    def remember(
        self,
        key: tuple[str, str],
        fingerprint: str,
        record: RegistrationTransitionRecord,
    ) -> None:
        with self._lock:
            self._seen.setdefault(key, (fingerprint, record))


def _assert_opaque_reference(label: str, value: str) -> None:
    if _OPAQUE_REFERENCE.fullmatch(value) is None:
        raise CitizenRegistrationError(f"{label} must be an opaque reference")
    if _RAW_NID_RUN.search(value):
        raise CitizenRegistrationError(f"{label} must not contain a national number")


def _assert_canonical_decision(
    context: RegistrationContext,
    *,
    action: str,
) -> None:
    """Require an engine-issued allow decision with a bound purpose and scope."""
    if not context.decision.allowed:
        raise RegistrationAuthorizationError(
            f"canonical authorization denied: {context.decision.reason_code.value}",
        )
    try:
        assert_identity_access_allowed(
            decision=context.decision,
            action=action,
            purpose=context.purpose,
            facility_id=context.facility_id,
        )
    except (IdentityTransitionError, PermissionError, ValueError) as exc:
        if isinstance(exc, PermissionError):
            raise
        raise RegistrationAuthorizationError(str(exc)) from exc
    if context.purpose not in AuthorizationDecisionService.ALLOWED_PURPOSES:
        raise RegistrationAuthorizationError("purpose is not approved for registration")


def _assert_staff_access(
    context: RegistrationContext,
    *,
    account: CitizenRegistrationAccount,
    role: IdentityRole,
    action: str,
) -> IdentityAccessGrant:
    """Require a named staff role through the canonical access boundary."""
    if context.role is None or context.role is not role:
        raise RegistrationAuthorizationError("an approved named staff role is required")
    _assert_account_scope(context, account)
    try:
        return assert_identity_access_v2(
            IdentityAccessContext(
                decision=context.decision,
                role=context.role,
                actor_id=context.actor_id,
                organization_id=context.organization_id,
                facility_id=context.facility_id,
                purpose=context.purpose,
                action=action,
                requested_fields=("gula_citizen_identifier", "verification_state"),
                gula_citizen_identifier=account.gula_citizen_identifier,
                national_id_hash=context.national_id_hash,
                now=context.resolved_now(),
            ),
        )
    except PermissionError:
        raise
    except ValueError as exc:
        raise RegistrationAuthorizationError(str(exc)) from exc


def _assert_account_scope(
    context: RegistrationContext,
    account: CitizenRegistrationAccount,
) -> None:
    """Bind every privileged decision to the account's creation scope."""
    if account.organization_id and account.organization_id != context.organization_id:
        raise PermissionError("cross-organization registration access is denied")
    if account.facility_id and account.facility_id != context.facility_id:
        raise PermissionError("cross-facility registration access is denied")


def project_registration_status(
    account: CitizenRegistrationAccount,
) -> dict[str, Any]:
    """Return a bounded, synthetic-only citizen status presentation model.

    The projection never claims official government verification and never
    grants medical access from an incomplete lifecycle state.
    """
    state = account.lifecycle_state
    if state is RegistrationLifecycleState.INITIAL_ACCOUNT:
        next_step = "verify_contact"
    elif state is RegistrationLifecycleState.CONTACT_VERIFIED:
        next_step = "submit_identity"
    elif state in {
        RegistrationLifecycleState.IDENTITY_SUBMITTED,
        RegistrationLifecycleState.IDENTITY_REVIEW,
    }:
        next_step = "await_in_person_review"
    elif state is RegistrationLifecycleState.HEALTH_APPROVED:
        next_step = "activation_pending_owner_approval"
    elif state is RegistrationLifecycleState.SERVICE_ACTIVE:
        next_step = "none"
    else:
        next_step = "contact_support"
    return {
        **account.to_public_dict(),
        "case_reference": account.gula_citizen_identifier,
        "next_step": next_step,
        "requires_in_person_review": state
        in {
            RegistrationLifecycleState.IDENTITY_SUBMITTED,
            RegistrationLifecycleState.IDENTITY_REVIEW,
        },
        "identity_submitted": state
        in {
            RegistrationLifecycleState.IDENTITY_SUBMITTED,
            RegistrationLifecycleState.IDENTITY_REVIEW,
            RegistrationLifecycleState.HEALTH_APPROVED,
            RegistrationLifecycleState.SERVICE_ACTIVE,
        },
        "health_identity_approved": state
        in {
            RegistrationLifecycleState.HEALTH_APPROVED,
            RegistrationLifecycleState.SERVICE_ACTIVE,
        },
        "official_verification": False,
        "synthetic": True,
        "notice": "synthetic_workflow_not_government_verification",
    }


def _audit_event(
    *,
    context: RegistrationContext,
    account: CitizenRegistrationAccount,
    operation: str,
    decision: str = "success",
    reason_code: str | None = None,
    metadata: dict[str, Any] | None = None,
):
    return build_wave053_audit_event(
        operation=operation,
        actor_id=context.actor_id,
        purpose=context.purpose,
        facility_id=context.facility_id,
        organization_id=context.organization_id,
        gula_citizen_identifier=account.gula_citizen_identifier,
        national_id_hash=context.national_id_hash,
        metadata={
            "lifecycle_state": account.lifecycle_state.value,
            "verification_state": account.verification_state,
            **(metadata or {}),
        },
        decision=decision,
        reason_code=reason_code,
        correlation_id=context.correlation_id,
        raw_nid_values=(
            context.actor_id,
            context.purpose,
            context.organization_id,
            context.facility_id,
            context.correlation_id,
            account.contact_reference,
        ),
    )


def _transition(
    account: CitizenRegistrationAccount,
    event: RegistrationLifecycleEvent,
    *,
    at: datetime,
) -> CitizenRegistrationAccount:
    target = _LIFECYCLE_TRANSITIONS.get(account.lifecycle_state, {}).get(event)
    if target is None:
        raise InvalidRegistrationTransitionError(
            f"lifecycle event {event.value} is not allowed from {account.lifecycle_state.value}",
        )
    return replace(account, lifecycle_state=target, updated_at=at)


def create_initial_account(
    *,
    request: RegistrationRequest,
    idempotency_store: IdempotencyStore,
    account_store: RegistrationAccountStore,
    context: RegistrationContext,
    contact_reference: str,
) -> CitizenRegistrationAccount:
    """Create a minimal, unverified account; NFC is not required."""
    _assert_canonical_decision(context, action="MODIFY")
    _assert_opaque_reference("contact reference", contact_reference)
    at = context.resolved_now()
    record: RegistrationRecord = register_citizen_idempotently(
        request,
        store=idempotency_store,
        now=at,
    )
    account = CitizenRegistrationAccount(
        gula_citizen_identifier=record.reserved_identifier or "",
        subject_reference=request.subject_reference,
        contact_reference=contact_reference,
        registration_record=record,
        lifecycle_state=RegistrationLifecycleState.INITIAL_ACCOUNT,
        verification_state=UNVERIFIED,
        updated_at=at,
        organization_id=context.organization_id,
        facility_id=context.facility_id,
    )
    if not account.gula_citizen_identifier:
        raise RegistrationCoordinatorError("registration did not reserve an identifier")
    account_store.save(account)
    _audit_event(context=context, account=account, operation=IDENTITY_CREATED)
    return account


def verify_contact(
    *,
    account: CitizenRegistrationAccount,
    contact_code: str,
    context: RegistrationContext,
    account_store: RegistrationAccountStore,
) -> CitizenRegistrationAccount:
    """Record contact verification without touching identity or medical access."""
    _assert_canonical_decision(context, action="MODIFY")
    _assert_account_scope(context, account)
    if _CONTACT_CODE.fullmatch(contact_code) is None:
        raise CitizenRegistrationError("contact code must be a six-digit synthetic code")
    updated = _transition(
        account,
        RegistrationLifecycleEvent.CONTACT_VERIFIED,
        at=context.resolved_now(),
    )
    account_store.save(updated)
    _audit_event(context=context, account=updated, operation=IDENTITY_READ)
    return updated


def submit_national_identity(
    *,
    account: CitizenRegistrationAccount,
    evidence: NidpEvidenceBundle,
    context: RegistrationContext,
    account_store: RegistrationAccountStore,
) -> CitizenRegistrationAccount:
    """Submit original-card evidence; every outcome routes to human review."""
    _assert_canonical_decision(context, action="VERIFY")
    _assert_account_scope(context, account)
    evidence_reference = evidence.presentation.evidence_reference
    if account.lifecycle_state is RegistrationLifecycleState.INITIAL_ACCOUNT:
        raise InvalidRegistrationTransitionError("contact verification is required first")
    if account.lifecycle_state not in {
        RegistrationLifecycleState.CONTACT_VERIFIED,
        RegistrationLifecycleState.IDENTITY_SUBMITTED,
        RegistrationLifecycleState.IDENTITY_REVIEW,
    }:
        raise InvalidRegistrationTransitionError("identity evidence cannot be submitted from this state")
    if account.evidence_reference is not None:
        if account.evidence_reference == evidence_reference:
            return account  # idempotent resume after network interruption
        raise InvalidRegistrationTransitionError("different identity evidence was already submitted")

    if evidence.path.value == "HOME_NFC" and not evidence.capture.challenge.device_capabilities.nfc_supported:
        raise CitizenRegistrationError("home NFC path requires an NFC-capable device")

    submitted = _transition(
        account,
        RegistrationLifecycleEvent.IDENTITY_SUBMITTED,
        at=context.resolved_now(),
    )
    authenticity_decision: DocumentAuthenticityDecision = evaluate_document_authenticity(evidence)
    eligibility = registration_eligibility(evidence, authenticity_decision)
    if eligibility.identity_verified is not False:
        raise CitizenRegistrationError("initial submission cannot grant verified identity")
    review = apply_authenticity_transition(
        authenticity_decision,
        current_state=submitted.verification_state,
        reviewer=context.actor_id,
    )
    if review.state == VERIFIED:
        raise CitizenRegistrationError("document authenticity must never produce VERIFIED")
    reviewed = _transition(
        submitted,
        RegistrationLifecycleEvent.REVIEW_REQUIRED,
        at=context.resolved_now(),
    )
    updated = replace(
        reviewed,
        verification_state=review.state,
        evidence_reference=evidence_reference,
        updated_at=context.resolved_now(),
    )
    if updated.verification_state != PENDING_REVIEW:
        raise CitizenRegistrationError("identity evidence must remain in human review")
    account_store.save(updated)
    _audit_event(
        context=context,
        account=updated,
        operation=NID_VERIFICATION_REQUESTED,
        metadata={"path": evidence.path.value, "reasons": authenticity_decision.reasons},
    )
    return updated


def approve_health_identity(
    *,
    account: CitizenRegistrationAccount,
    primary: LinkageCandidate,
    secondary: LinkageCandidate,
    reviewer: LinkageReviewer,
    reason: str,
    evidence_reference: str,
    context: RegistrationContext,
    account_store: RegistrationAccountStore,
) -> CitizenRegistrationAccount:
    """Authorize a health-identity linkage decision through the canonical MPI guard."""
    _assert_staff_access(
        context,
        account=account,
        role=IdentityRole.IDENTITY_REVIEWER,
        action=IDENTITY_APPROVAL,
    )
    if account.lifecycle_state is not RegistrationLifecycleState.IDENTITY_REVIEW:
        raise InvalidRegistrationTransitionError("human identity review is required before health approval")
    if account.verification_state != PENDING_REVIEW:
        raise InvalidRegistrationTransitionError("identity verification is incomplete")
    _assert_opaque_reference("evidence reference", evidence_reference)
    assert_linkage_allowed(
        primary,
        secondary,
        decision="APPROVED",
        reviewer=reviewer,
        reason=reason,
        evidence_reference=evidence_reference,
    )
    updated = _transition(
        account,
        RegistrationLifecycleEvent.HEALTH_APPROVED,
        at=context.resolved_now(),
    )
    account_store.save(updated)
    _audit_event(
        context=context,
        account=updated,
        operation=IDENTITY_APPROVAL,
        metadata={"reviewer": reviewer.name, "evidence_reference": evidence_reference},
    )
    return updated


def activate_service(
    *,
    account: CitizenRegistrationAccount,
    context: RegistrationContext,
    account_store: RegistrationAccountStore,
) -> CitizenRegistrationAccount:
    """Fail closed: activation requires an officially approved procedure and owner decision."""
    _assert_staff_access(
        context,
        account=account,
        role=IdentityRole.IDENTITY_REVIEWER,
        action="IDENTITY_REACTIVATION",
    )
    if account.lifecycle_state is not RegistrationLifecycleState.HEALTH_APPROVED:
        raise InvalidRegistrationTransitionError("health identity approval is required before activation")
    try:
        assert_no_manual_authenticity_override(VERIFIED)
    except ValueError as exc:
        raise CitizenRegistrationError(
            "service activation remains blocked pending an approved official authenticity procedure",
        ) from exc
    raise CitizenRegistrationError(
        "service activation requires owner authorization and an approved official procedure",
    )


def assert_medical_data_access_allowed(
    *,
    account: CitizenRegistrationAccount,
    context: RegistrationContext,
) -> IdentityAccessGrant:
    """Deny medical data access unless the account reached SERVICE_ACTIVE."""
    if not account.can_access_medical_data:
        raise MedicalDataAccessDeniedError(
            "medical data access requires a fully activated, verified account",
        )
    return _assert_staff_access(
        context,
        account=account,
        role=IdentityRole.HEALTHCARE_PROVIDER,
        action=IDENTITY_READ,
    )


def reject_registration(
    *,
    account: CitizenRegistrationAccount,
    reason: str,
    context: RegistrationContext,
    account_store: RegistrationAccountStore,
) -> CitizenRegistrationAccount:
    """Record an explicit rejection without deleting earlier decisions."""
    _assert_canonical_decision(context, action="REVIEW")
    _assert_account_scope(context, account)
    if not reason.strip():
        raise CitizenRegistrationError("rejection requires a reason")
    updated = _transition(account, RegistrationLifecycleEvent.REJECTED, at=context.resolved_now())
    account_store.save(updated)
    _audit_event(
        context=context,
        account=updated,
        operation="IDENTITY_REJECTION",
        decision="denied",
        reason_code="REGISTRATION_REJECTED",
        metadata={"reason": reason[:200]},
    )
    return updated


def assert_no_registration_conflict(
    accounts: Iterable[CitizenRegistrationAccount],
    *,
    subject_reference: str,
    evidence_reference: str,
) -> CitizenRegistrationAccount:
    """Fail closed when duplicate subjects or conflicting evidence are present."""
    _assert_opaque_reference("evidence reference", evidence_reference)
    matches = [item for item in accounts if item.subject_reference == subject_reference]
    if not matches:
        raise RegistrationConflictError("no registration exists for the subject reference")
    if len(matches) > 1:
        raise RegistrationConflictError("duplicate registration subjects are not auto-merged")
    account = matches[0]
    if account.evidence_reference is not None and account.evidence_reference != evidence_reference:
        raise RegistrationConflictError("conflicting identity evidence requires manual review")
    return account


def suspend_registration(
    *,
    account: CitizenRegistrationAccount,
    reason: str,
    evidence_reference: str,
    context: RegistrationContext,
    account_store: RegistrationAccountStore,
) -> CitizenRegistrationAccount:
    """Suspend an account through the canonical identity-suspension guard."""
    _assert_staff_access(
        context,
        account=account,
        role=IdentityRole.IDENTITY_REVIEWER,
        action=IDENTITY_SUSPENSION,
    )
    if not reason.strip():
        raise RegistrationEvidenceError("suspension requires a reason")
    _assert_opaque_reference("evidence reference", evidence_reference)
    if account.lifecycle_state not in {
        RegistrationLifecycleState.IDENTITY_REVIEW,
        RegistrationLifecycleState.HEALTH_APPROVED,
        RegistrationLifecycleState.SERVICE_ACTIVE,
    }:
        raise InvalidRegistrationTransitionError(
            f"suspension is not allowed from {account.lifecycle_state.value}",
        )
    updated = replace(
        _transition(account, RegistrationLifecycleEvent.SUSPENDED, at=context.resolved_now()),
        updated_at=context.resolved_now(),
    )
    account_store.save(updated)
    _audit_event(
        context=context,
        account=updated,
        operation=IDENTITY_SUSPENSION,
        metadata={"reason": reason[:200], "evidence_reference": evidence_reference},
    )
    return updated


def resubmit_registration(
    *,
    account: CitizenRegistrationAccount,
    contact_reference: str,
    evidence_reference: str,
    reason: str,
    context: RegistrationContext,
    account_store: RegistrationAccountStore,
) -> CitizenRegistrationAccount:
    """Reopen a suspended case with new evidence; never grant verified identity."""
    _assert_canonical_decision(context, action="VERIFY")
    _assert_account_scope(context, account)
    if context.actor_type is not ActorType.CITIZEN:
        raise RegistrationAuthorizationError("resubmission requires a citizen actor")
    if not hmac.compare_digest(contact_reference, account.contact_reference):
        raise RegistrationAuthorizationError("resubmission requires the account contact reference")
    if not reason.strip():
        raise RegistrationEvidenceError("resubmission requires a reason")
    _assert_opaque_reference("evidence reference", evidence_reference)
    if account.lifecycle_state is not RegistrationLifecycleState.SUSPENDED:
        raise InvalidRegistrationTransitionError("only suspended registrations can be resubmitted")
    if account.evidence_reference == evidence_reference:
        raise RegistrationReplayError("resubmission requires new evidence")
    updated = replace(
        _transition(account, RegistrationLifecycleEvent.RESUBMITTED, at=context.resolved_now()),
        verification_state=PENDING_REVIEW,
        evidence_reference=evidence_reference,
        updated_at=context.resolved_now(),
    )
    if updated.verification_state == VERIFIED:
        raise CitizenRegistrationError("resubmission cannot produce a verified identity")
    account_store.save(updated)
    _audit_event(
        context=context,
        account=updated,
        operation=IDENTITY_CORRECTION,
        metadata={"reason": reason[:200], "evidence_reference": evidence_reference},
    )
    return updated


def request_manual_review(
    *,
    account: CitizenRegistrationAccount,
    reason: str,
    evidence_reference: str,
    context: RegistrationContext,
    account_store: RegistrationAccountStore,
) -> CitizenRegistrationAccount:
    """Explicitly assign a case to manual review without changing verification truth."""
    _assert_staff_access(
        context,
        account=account,
        role=IdentityRole.IDENTITY_REVIEWER,
        action=DOCUMENT_REVIEW,
    )
    if context.actor_type not in {ActorType.STAFF, ActorType.INSTITUTION}:
        raise RegistrationAuthorizationError("manual review requires a named reviewer actor")
    if not reason.strip():
        raise RegistrationEvidenceError("manual review requires a reason")
    _assert_opaque_reference("evidence reference", evidence_reference)
    if account.lifecycle_state not in {
        RegistrationLifecycleState.IDENTITY_SUBMITTED,
        RegistrationLifecycleState.IDENTITY_REVIEW,
    }:
        raise InvalidRegistrationTransitionError("manual review requires submitted identity evidence")
    updated = _transition(
        account,
        RegistrationLifecycleEvent.MANUAL_REVIEW_REQUESTED,
        at=context.resolved_now(),
    )
    account_store.save(updated)
    _audit_event(
        context=context,
        account=updated,
        operation=DOCUMENT_REVIEW,
        metadata={"reason": reason[:200], "evidence_reference": evidence_reference},
    )
    return updated


def request_appeal_reconsideration(
    *,
    account: CitizenRegistrationAccount,
    reason: str,
    evidence_reference: str,
    reviewer_id: str,
    context: RegistrationContext,
    account_store: RegistrationAccountStore,
) -> CitizenRegistrationAccount:
    """Reopen a rejected or suspended case with an independent named reviewer."""
    _assert_staff_access(
        context,
        account=account,
        role=IdentityRole.IDENTITY_REVIEWER,
        action=REVIEW_OUTCOME,
    )
    if context.actor_type not in {ActorType.STAFF, ActorType.INSTITUTION}:
        raise RegistrationAuthorizationError("appeal reconsideration requires an institutional actor")
    if not reviewer_id.strip() or reviewer_id == context.actor_id:
        raise RegistrationAuthorizationError("appeal requires an independent named reviewer")
    if not reason.strip():
        raise RegistrationEvidenceError("appeal requires a reason")
    _assert_opaque_reference("evidence reference", evidence_reference)
    if account.lifecycle_state not in {
        RegistrationLifecycleState.REJECTED,
        RegistrationLifecycleState.SUSPENDED,
    }:
        raise InvalidRegistrationTransitionError(
            "appeal reconsideration requires a rejected or suspended case",
        )
    updated = replace(
        _transition(account, RegistrationLifecycleEvent.APPEAL_RECONSIDERED, at=context.resolved_now()),
        verification_state=PENDING_REVIEW,
        updated_at=context.resolved_now(),
    )
    account_store.save(updated)
    _audit_event(
        context=context,
        account=updated,
        operation=REVIEW_OUTCOME,
        metadata={
            "reason": reason[:200],
            "evidence_reference": evidence_reference,
            "independent_reviewer": reviewer_id,
        },
    )
    return updated


@dataclass(frozen=True)
class RegistrationTransitionOutcome:
    """A lifecycle result paired with its synthetic transition evidence."""

    account: CitizenRegistrationAccount
    transition: RegistrationTransitionRecord


class RegistrationLifecycleService:
    """Synthetic orchestration that records a decision for every lifecycle change.

    The service uses the existing stage functions and canonical guards. It adds
    serialized read-modify-write behavior, replay detection, and append-only
    transition evidence. It is not durable and is not an audit authority.
    """

    def __init__(
        self,
        *,
        idempotency_store: IdempotencyStore,
        account_store: RegistrationAccountStore,
        transition_store: RegistrationTransitionStore | None = None,
        replay_guard: RegistrationReplayGuard | None = None,
    ) -> None:
        self._idempotency_store = idempotency_store
        self._account_store = account_store
        self._transition_store = transition_store or InMemoryRegistrationTransitionStore()
        self._replay_guard = replay_guard or RegistrationReplayGuard()
        self._lock = threading.RLock()

    @staticmethod
    def _require_correlation(context: RegistrationContext) -> str:
        if context.correlation_id is None or not context.correlation_id.strip():
            raise RegistrationEvidenceError("correlation id is required for every transition")
        return context.correlation_id

    @staticmethod
    def _account(identifier: str, store: RegistrationAccountStore) -> CitizenRegistrationAccount:
        account = store.get(identifier)
        if account is None:
            raise RegistrationEvidenceError("registration account is unknown")
        return account

    def history(self, gula_citizen_identifier: str) -> tuple[RegistrationTransitionRecord, ...]:
        """Internal synthetic history; no HTTP projection exposes this method."""
        return self._transition_store.records(gula_citizen_identifier)

    def history_public(self, gula_citizen_identifier: str) -> tuple[dict[str, Any], ...]:
        """Bounded decision summaries safe for an authorized status surface."""
        return tuple(record.to_public_dict() for record in self.history(gula_citizen_identifier))

    def status(self, gula_citizen_identifier: str) -> dict[str, Any]:
        return project_registration_status(self._account(gula_citizen_identifier, self._account_store))

    @staticmethod
    def _fingerprint(
        *,
        identifier: str,
        event: RegistrationLifecycleEvent,
        context: RegistrationContext,
        reason: str,
        decision_source: str,
        evidence_references: Sequence[str],
    ) -> str:
        return _transition_fingerprint(
            gula_citizen_identifier=identifier,
            event=event,
            correlation_id=RegistrationLifecycleService._require_correlation(context),
            actor_id=context.actor_id,
            actor_type=context.actor_type,
            reason=reason,
            decision_source=decision_source,
            evidence_references=tuple(evidence_references),
            authorization_decision="ALLOW",
        )

    def _preflight(
        self,
        *,
        identifier: str,
        event: RegistrationLifecycleEvent,
        context: RegistrationContext,
        reason: str,
        decision_source: str,
        evidence_references: Sequence[str],
    ) -> RegistrationTransitionRecord | None:
        """Reject conflicting replays before any mutation or audit write."""
        fingerprint = self._fingerprint(
            identifier=identifier,
            event=event,
            context=context,
            reason=reason,
            decision_source=decision_source,
            evidence_references=evidence_references,
        )
        return self._replay_guard.check((identifier, self._require_correlation(context)), fingerprint)

    def _record(
        self,
        *,
        before: CitizenRegistrationAccount,
        after: CitizenRegistrationAccount,
        event: RegistrationLifecycleEvent,
        context: RegistrationContext,
        reason: str,
        decision_source: str,
        evidence_references: Sequence[str],
        audit_operation: str,
    ) -> RegistrationTransitionRecord:
        correlation_id = self._require_correlation(context)
        references = tuple(evidence_references)
        fingerprint = _transition_fingerprint(
            gula_citizen_identifier=after.gula_citizen_identifier,
            event=event,
            correlation_id=correlation_id,
            actor_id=context.actor_id,
            actor_type=context.actor_type,
            reason=reason,
            decision_source=decision_source,
            evidence_references=references,
            authorization_decision="ALLOW",
        )
        # A retried decision must not append a second transition or audit event.
        # Conflicting replays are rejected earlier by ``_preflight`` before any
        # mutation; this check is the final idempotency guard for all paths.
        existing = self._replay_guard.check(
            (after.gula_citizen_identifier, correlation_id),
            fingerprint,
        )
        if existing is not None:
            return existing
        # A full hex digest is hash-like text and cannot be mistaken for a
        # national identifier; truncated hex can contain a nine-digit run.
        transition_id = hashlib.sha256(f"transition:{fingerprint}".encode()).hexdigest()
        audit_event = _audit_event(
            context=context,
            account=after,
            operation=audit_operation,
            metadata={
                "actor_type": context.actor_type.value,
                "decision_source": decision_source,
                "transition_id": transition_id,
                "previous_state": before.lifecycle_state.value,
                "new_state": after.lifecycle_state.value,
                "reason": reason[:200],
                "evidence_references": references,
            },
        )
        record = RegistrationTransitionRecord(
            transition_id=transition_id,
            gula_citizen_identifier=after.gula_citizen_identifier,
            event=event,
            previous_state=before.lifecycle_state,
            new_state=after.lifecycle_state,
            actor_id=context.actor_id,
            actor_type=context.actor_type,
            organization_id=context.organization_id,
            facility_id=context.facility_id,
            purpose=context.purpose,
            occurred_at=context.resolved_now(),
            correlation_id=correlation_id,
            reason=reason,
            decision_source=decision_source,
            evidence_references=references,
            authorization_decision="ALLOW",
            authorization_reason_code=getattr(
                context.decision.reason_code,
                "value",
                str(context.decision.reason_code),
            ),
            audit_operation=audit_operation,
            audit_event_reference=hashlib.sha256(repr(audit_event).encode("utf-8")).hexdigest(),
            replay_fingerprint=fingerprint,
        )
        self._replay_guard.remember((after.gula_citizen_identifier, correlation_id), fingerprint, record)
        self._transition_store.append(record)
        return record

    def create(
        self,
        *,
        request: RegistrationRequest,
        context: RegistrationContext,
        contact_reference: str,
    ) -> RegistrationTransitionOutcome:
        self._require_correlation(context)
        with self._lock:
            account = create_initial_account(
                request=request,
                idempotency_store=self._idempotency_store,
                account_store=self._account_store,
                context=context,
                contact_reference=contact_reference,
            )
            before = replace(account, lifecycle_state=RegistrationLifecycleState.NOT_CREATED)
            transition = self._record(
                before=before,
                after=account,
                event=RegistrationLifecycleEvent.ACCOUNT_CREATED,
                context=context,
                reason="initial account creation without identity verification",
                decision_source="canonical_authorization_decision",
                evidence_references=("SYNTHETIC-ACCOUNT-EVIDENCE",),
                audit_operation=IDENTITY_CREATED,
            )
            return RegistrationTransitionOutcome(account=account, transition=transition)

    def verify_contact(
        self,
        *,
        gula_citizen_identifier: str,
        contact_code: str,
        context: RegistrationContext,
    ) -> RegistrationTransitionOutcome:
        self._require_correlation(context)
        with self._lock:
            before = self._account(gula_citizen_identifier, self._account_store)
            existing = self._preflight(
                identifier=gula_citizen_identifier,
                event=RegistrationLifecycleEvent.CONTACT_VERIFIED,
                context=context,
                reason="synthetic contact verification completed",
                decision_source="canonical_authorization_decision",
                evidence_references=(before.contact_reference,),
            )
            if existing is not None:
                return RegistrationTransitionOutcome(account=before, transition=existing)
            after = verify_contact(
                account=before,
                contact_code=contact_code,
                context=context,
                account_store=self._account_store,
            )
            transition = self._record(
                before=before,
                after=after,
                event=RegistrationLifecycleEvent.CONTACT_VERIFIED,
                context=context,
                reason="synthetic contact verification completed",
                decision_source="canonical_authorization_decision",
                evidence_references=(after.contact_reference,),
                audit_operation=IDENTITY_READ,
            )
            return RegistrationTransitionOutcome(account=after, transition=transition)

    def submit_identity(
        self,
        *,
        gula_citizen_identifier: str,
        evidence: NidpEvidenceBundle,
        context: RegistrationContext,
    ) -> RegistrationTransitionOutcome:
        self._require_correlation(context)
        with self._lock:
            before = self._account(gula_citizen_identifier, self._account_store)
            existing = self._preflight(
                identifier=gula_citizen_identifier,
                event=RegistrationLifecycleEvent.IDENTITY_SUBMITTED,
                context=context,
                reason=evidence.path.value,
                decision_source="nidp_original_card_evaluator",
                evidence_references=(evidence.presentation.evidence_reference,),
            )
            if existing is not None:
                return RegistrationTransitionOutcome(account=before, transition=existing)
            after = submit_national_identity(
                account=before,
                evidence=evidence,
                context=context,
                account_store=self._account_store,
            )
            transition = self._record(
                before=before,
                after=after,
                event=RegistrationLifecycleEvent.IDENTITY_SUBMITTED,
                context=context,
                reason=evidence.path.value,
                decision_source="nidp_original_card_evaluator",
                evidence_references=(evidence.presentation.evidence_reference,),
                audit_operation=NID_VERIFICATION_REQUESTED,
            )
            return RegistrationTransitionOutcome(account=after, transition=transition)

    def approve_health_identity(
        self,
        *,
        gula_citizen_identifier: str,
        primary: LinkageCandidate,
        secondary: LinkageCandidate,
        reviewer: LinkageReviewer,
        reason: str,
        evidence_reference: str,
        context: RegistrationContext,
    ) -> RegistrationTransitionOutcome:
        self._require_correlation(context)
        with self._lock:
            before = self._account(gula_citizen_identifier, self._account_store)
            existing = self._preflight(
                identifier=gula_citizen_identifier,
                event=RegistrationLifecycleEvent.HEALTH_APPROVED,
                context=context,
                reason=reason,
                decision_source="canonical_mpi_linkage_guard",
                evidence_references=(evidence_reference,),
            )
            if existing is not None:
                return RegistrationTransitionOutcome(account=before, transition=existing)
            after = approve_health_identity(
                account=before,
                primary=primary,
                secondary=secondary,
                reviewer=reviewer,
                reason=reason,
                evidence_reference=evidence_reference,
                context=context,
                account_store=self._account_store,
            )
            transition = self._record(
                before=before,
                after=after,
                event=RegistrationLifecycleEvent.HEALTH_APPROVED,
                context=context,
                reason=reason,
                decision_source="canonical_mpi_linkage_guard",
                evidence_references=(evidence_reference,),
                audit_operation=IDENTITY_APPROVAL,
            )
            return RegistrationTransitionOutcome(account=after, transition=transition)

    def reject(
        self,
        *,
        gula_citizen_identifier: str,
        reason: str,
        context: RegistrationContext,
    ) -> RegistrationTransitionOutcome:
        self._require_correlation(context)
        with self._lock:
            before = self._account(gula_citizen_identifier, self._account_store)
            rejection_reference = f"REJECTION-{context.correlation_id}"
            existing = self._preflight(
                identifier=gula_citizen_identifier,
                event=RegistrationLifecycleEvent.REJECTED,
                context=context,
                reason=reason,
                decision_source="canonical_authorization_decision",
                evidence_references=(rejection_reference,),
            )
            if existing is not None:
                return RegistrationTransitionOutcome(account=before, transition=existing)
            after = reject_registration(
                account=before,
                reason=reason,
                context=context,
                account_store=self._account_store,
            )
            transition = self._record(
                before=before,
                after=after,
                event=RegistrationLifecycleEvent.REJECTED,
                context=context,
                reason=reason,
                decision_source="canonical_authorization_decision",
                evidence_references=(rejection_reference,),
                audit_operation=IDENTITY_REJECTION,
            )
            return RegistrationTransitionOutcome(account=after, transition=transition)

    def suspend(
        self,
        *,
        gula_citizen_identifier: str,
        reason: str,
        evidence_reference: str,
        context: RegistrationContext,
    ) -> RegistrationTransitionOutcome:
        self._require_correlation(context)
        with self._lock:
            before = self._account(gula_citizen_identifier, self._account_store)
            existing = self._preflight(
                identifier=gula_citizen_identifier,
                event=RegistrationLifecycleEvent.SUSPENDED,
                context=context,
                reason=reason,
                decision_source="canonical_identity_suspension_guard",
                evidence_references=(evidence_reference,),
            )
            if existing is not None:
                return RegistrationTransitionOutcome(account=before, transition=existing)
            after = suspend_registration(
                account=before,
                reason=reason,
                evidence_reference=evidence_reference,
                context=context,
                account_store=self._account_store,
            )
            transition = self._record(
                before=before,
                after=after,
                event=RegistrationLifecycleEvent.SUSPENDED,
                context=context,
                reason=reason,
                decision_source="canonical_identity_suspension_guard",
                evidence_references=(evidence_reference,),
                audit_operation=IDENTITY_SUSPENSION,
            )
            return RegistrationTransitionOutcome(account=after, transition=transition)

    def resubmit(
        self,
        *,
        gula_citizen_identifier: str,
        contact_reference: str,
        evidence_reference: str,
        reason: str,
        context: RegistrationContext,
    ) -> RegistrationTransitionOutcome:
        self._require_correlation(context)
        with self._lock:
            before = self._account(gula_citizen_identifier, self._account_store)
            existing = self._preflight(
                identifier=gula_citizen_identifier,
                event=RegistrationLifecycleEvent.RESUBMITTED,
                context=context,
                reason=reason,
                decision_source="canonical_authorization_decision",
                evidence_references=(evidence_reference,),
            )
            if existing is not None:
                return RegistrationTransitionOutcome(account=before, transition=existing)
            after = resubmit_registration(
                account=before,
                contact_reference=contact_reference,
                evidence_reference=evidence_reference,
                reason=reason,
                context=context,
                account_store=self._account_store,
            )
            transition = self._record(
                before=before,
                after=after,
                event=RegistrationLifecycleEvent.RESUBMITTED,
                context=context,
                reason=reason,
                decision_source="canonical_authorization_decision",
                evidence_references=(evidence_reference,),
                audit_operation=IDENTITY_CORRECTION,
            )
            return RegistrationTransitionOutcome(account=after, transition=transition)

    def request_manual_review(
        self,
        *,
        gula_citizen_identifier: str,
        reason: str,
        evidence_reference: str,
        context: RegistrationContext,
    ) -> RegistrationTransitionOutcome:
        self._require_correlation(context)
        with self._lock:
            before = self._account(gula_citizen_identifier, self._account_store)
            existing = self._preflight(
                identifier=gula_citizen_identifier,
                event=RegistrationLifecycleEvent.MANUAL_REVIEW_REQUESTED,
                context=context,
                reason=reason,
                decision_source="canonical_authorization_decision",
                evidence_references=(evidence_reference,),
            )
            if existing is not None:
                return RegistrationTransitionOutcome(account=before, transition=existing)
            after = request_manual_review(
                account=before,
                reason=reason,
                evidence_reference=evidence_reference,
                context=context,
                account_store=self._account_store,
            )
            transition = self._record(
                before=before,
                after=after,
                event=RegistrationLifecycleEvent.MANUAL_REVIEW_REQUESTED,
                context=context,
                reason=reason,
                decision_source="canonical_authorization_decision",
                evidence_references=(evidence_reference,),
                audit_operation=DOCUMENT_REVIEW,
            )
            return RegistrationTransitionOutcome(account=after, transition=transition)

    def appeal(
        self,
        *,
        gula_citizen_identifier: str,
        reason: str,
        evidence_reference: str,
        reviewer_id: str,
        context: RegistrationContext,
    ) -> RegistrationTransitionOutcome:
        self._require_correlation(context)
        with self._lock:
            before = self._account(gula_citizen_identifier, self._account_store)
            existing = self._preflight(
                identifier=gula_citizen_identifier,
                event=RegistrationLifecycleEvent.APPEAL_RECONSIDERED,
                context=context,
                reason=reason,
                decision_source="independent_reviewer_decision",
                evidence_references=(evidence_reference,),
            )
            if existing is not None:
                return RegistrationTransitionOutcome(account=before, transition=existing)
            after = request_appeal_reconsideration(
                account=before,
                reason=reason,
                evidence_reference=evidence_reference,
                reviewer_id=reviewer_id,
                context=context,
                account_store=self._account_store,
            )
            transition = self._record(
                before=before,
                after=after,
                event=RegistrationLifecycleEvent.APPEAL_RECONSIDERED,
                context=context,
                reason=reason,
                decision_source="independent_reviewer_decision",
                evidence_references=(evidence_reference,),
                audit_operation=REVIEW_OUTCOME,
            )
            return RegistrationTransitionOutcome(account=after, transition=transition)

    def activate(
        self,
        *,
        gula_citizen_identifier: str,
        context: RegistrationContext,
    ) -> CitizenRegistrationAccount:
        """Record the denial and keep activation unreachable."""
        self._require_correlation(context)
        with self._lock:
            account = self._account(gula_citizen_identifier, self._account_store)
            try:
                return activate_service(
                    account=account,
                    context=context,
                    account_store=self._account_store,
                )
            except CitizenRegistrationError as exc:
                _audit_event(
                    context=context,
                    account=account,
                    operation=UNAUTHORIZED_VERIFICATION_ATTEMPT,
                    decision="denied",
                    reason_code="ACTIVATION_OWNER_GATE",
                    metadata={"reason": str(exc)[:200]},
                )
                raise


def assert_single_initial_account(
    accounts: Iterable[CitizenRegistrationAccount],
    subject_reference: str,
) -> CitizenRegistrationAccount:
    """Fail if duplicate submissions leaked into more than one initial account."""
    matches = [item for item in accounts if item.subject_reference == subject_reference]
    if len(matches) != 1:
        raise RegistrationCoordinatorError(
            f"expected one initial registration for subject reference, found {len(matches)}",
        )
    return matches[0]


__all__ = [
    "ActorType",
    "CitizenRegistrationAccount",
    "CitizenRegistrationError",
    "InMemoryRegistrationAccountStore",
    "InMemoryRegistrationTransitionStore",
    "InvalidRegistrationTransitionError",
    "MedicalDataAccessDeniedError",
    "RegistrationAccountStore",
    "RegistrationAuthorizationError",
    "RegistrationConflictError",
    "RegistrationContext",
    "RegistrationEvidenceError",
    "RegistrationLifecycleEvent",
    "RegistrationLifecycleService",
    "RegistrationLifecycleState",
    "RegistrationReplayError",
    "RegistrationReplayGuard",
    "RegistrationTransitionOutcome",
    "RegistrationTransitionRecord",
    "RegistrationTransitionStore",
    "activate_service",
    "approve_health_identity",
    "assert_medical_data_access_allowed",
    "assert_no_registration_conflict",
    "assert_single_initial_account",
    "create_initial_account",
    "project_registration_status",
    "reject_registration",
    "request_appeal_reconsideration",
    "request_manual_review",
    "resubmit_registration",
    "submit_national_identity",
    "suspend_registration",
    "verify_contact",
]
