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

import re
import threading
from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol

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
    IDENTITY_APPROVAL,
    IDENTITY_CREATED,
    IDENTITY_READ,
    NID_VERIFICATION_REQUESTED,
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


class RegistrationLifecycleState(StrEnum):
    INITIAL_ACCOUNT = "INITIAL_ACCOUNT_CREATED"
    CONTACT_VERIFIED = "CONTACT_VERIFIED"
    IDENTITY_SUBMITTED = "NATIONAL_IDENTITY_SUBMITTED"
    IDENTITY_REVIEW = "NATIONAL_IDENTITY_PENDING_REVIEW"
    HEALTH_APPROVED = "HEALTH_IDENTITY_APPROVED"
    SERVICE_ACTIVE = "SERVICE_ACTIVE"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class RegistrationLifecycleEvent(StrEnum):
    CONTACT_VERIFIED = "CONTACT_VERIFIED"
    IDENTITY_SUBMITTED = "IDENTITY_SUBMITTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    HEALTH_APPROVED = "HEALTH_APPROVED"
    SERVICE_ACTIVATED = "SERVICE_ACTIVATED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


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
        RegistrationLifecycleEvent.REJECTED: RegistrationLifecycleState.REJECTED,
    },
    RegistrationLifecycleState.IDENTITY_REVIEW: {
        RegistrationLifecycleEvent.HEALTH_APPROVED: RegistrationLifecycleState.HEALTH_APPROVED,
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
    },
    RegistrationLifecycleState.REJECTED: {},
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
    organization_id: str
    facility_id: str
    purpose: str = REGISTRATION_PURPOSE
    now: datetime | None = None
    role: IdentityRole | None = None
    correlation_id: str | None = None
    national_id_hash: str = SYNTHETIC_NID_HASH

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
    "CitizenRegistrationAccount",
    "CitizenRegistrationError",
    "InMemoryRegistrationAccountStore",
    "InvalidRegistrationTransitionError",
    "MedicalDataAccessDeniedError",
    "RegistrationAccountStore",
    "RegistrationAuthorizationError",
    "RegistrationContext",
    "RegistrationLifecycleEvent",
    "RegistrationLifecycleState",
    "activate_service",
    "approve_health_identity",
    "assert_medical_data_access_allowed",
    "assert_single_initial_account",
    "create_initial_account",
    "reject_registration",
    "submit_national_identity",
    "verify_contact",
]
