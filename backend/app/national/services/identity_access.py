"""Wave 05.3 identity authorization and audit boundary helpers.

The canonical Authorization Decision Engine remains the only RBAC/ABAC
decision source. This module adds fail-closed identity-specific checks that are
not policy decisions: purpose binding, organization/facility scope, named-role
minimum-necessary field access, consent/relationship requirements, bounded
break-glass expiry, and complete canonical audit event construction.

Role names are design labels only. The production role matrix remains PENDING
legal/clinical/institutional approval.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from app._compat import UTC
from app.identity.services.authorization_decision import (
    AuthorizationDecision,
    AuthorizationDecisionService,
)
from app.identity.services.canonical_audit import AuditEventInput
from app.national.services.identity_governance import (
    IdentityAccessDeniedError,
    IdentityEvidenceError,
    assert_no_full_national_identifier,
)
from app.services.identity import normalize_national_id


class IdentityRole(StrEnum):
    IDENTITY_ADMINISTRATOR = "IDENTITY_ADMINISTRATOR"
    REGISTRATION_OFFICER = "REGISTRATION_OFFICER"
    IDENTITY_REVIEWER = "IDENTITY_REVIEWER"
    HEALTHCARE_PROVIDER = "HEALTHCARE_PROVIDER"
    PHYSICIAN = "PHYSICIAN"
    LABORATORY_TECHNICIAN = "LABORATORY_TECHNICIAN"
    PHARMACIST = "PHARMACIST"
    FACILITY_ADMINISTRATOR = "FACILITY_ADMINISTRATOR"
    AUDITOR = "AUDITOR"
    SYSTEM_ADMINISTRATOR = "SYSTEM_ADMINISTRATOR"


IDENTITY_CREATED = "IDENTITY_CREATED"
IDENTITY_READ = "IDENTITY_READ"
NID_VERIFICATION_REQUESTED = "NID_VERIFICATION_REQUESTED"
NID_VERIFICATION_RESULT = "NID_VERIFICATION_RESULT"
OCR_EXTRACTION = "OCR_EXTRACTION"
NFC_EXTRACTION = "NFC_EXTRACTION"
DOCUMENT_AUTHENTICITY_CHECK = "DOCUMENT_AUTHENTICITY_CHECK"
ORIGINAL_CARD_PRESENTED = "ORIGINAL_CARD_PRESENTED"
LIVE_CAPTURE_STARTED = "LIVE_CAPTURE_STARTED"
LIVE_CAPTURE_COMPLETED = "LIVE_CAPTURE_COMPLETED"
MRZ_EXTRACTION = "MRZ_EXTRACTION"
AUTHENTICITY_INSPECTION = "AUTHENTICITY_INSPECTION"
AUTHENTICITY_FAILURE = "AUTHENTICITY_FAILURE"
COPY_REJECTION = "COPY_REJECTION"
SUSPICIOUS_DOCUMENT = "SUSPICIOUS_DOCUMENT"
DOCUMENT_REVIEW = "DOCUMENT_REVIEW"
REVIEW_OUTCOME = "REVIEW_OUTCOME"
IDENTITY_APPROVAL = "IDENTITY_APPROVAL"
IDENTITY_REJECTION = "IDENTITY_REJECTION"
UNAUTHORIZED_VERIFICATION_ATTEMPT = "UNAUTHORIZED_VERIFICATION_ATTEMPT"
MANUAL_OVERRIDE_ATTEMPT = "MANUAL_OVERRIDE_ATTEMPT"
IDENTITY_CORRECTION = "IDENTITY_CORRECTION"
IDENTITY_SUSPENSION = "IDENTITY_SUSPENSION"
IDENTITY_REACTIVATION = "IDENTITY_REACTIVATION"
PATIENT_LINKAGE = "PATIENT_LINKAGE"
LINKAGE_REVIEW = "LINKAGE_REVIEW"
LINKAGE_ROLLBACK = "LINKAGE_ROLLBACK"
DATA_EXPORT = "DATA_EXPORT"
UNAUTHORIZED_ACCESS_ATTEMPT = "UNAUTHORIZED_ACCESS_ATTEMPT"
KEY_ACCESS = "KEY_ACCESS"
KEY_ROTATION = "KEY_ROTATION"
KEY_REVOCATION = "KEY_REVOCATION"

WAVE053_AUDIT_OPERATIONS = frozenset(
    {
        IDENTITY_CREATED,
        IDENTITY_READ,
        NID_VERIFICATION_REQUESTED,
        NID_VERIFICATION_RESULT,
        OCR_EXTRACTION,
        NFC_EXTRACTION,
        DOCUMENT_AUTHENTICITY_CHECK,
        ORIGINAL_CARD_PRESENTED,
        LIVE_CAPTURE_STARTED,
        LIVE_CAPTURE_COMPLETED,
        MRZ_EXTRACTION,
        AUTHENTICITY_INSPECTION,
        AUTHENTICITY_FAILURE,
        COPY_REJECTION,
        SUSPICIOUS_DOCUMENT,
        DOCUMENT_REVIEW,
        REVIEW_OUTCOME,
        IDENTITY_APPROVAL,
        IDENTITY_REJECTION,
        UNAUTHORIZED_VERIFICATION_ATTEMPT,
        MANUAL_OVERRIDE_ATTEMPT,
        IDENTITY_CORRECTION,
        IDENTITY_SUSPENSION,
        IDENTITY_REACTIVATION,
        PATIENT_LINKAGE,
        LINKAGE_REVIEW,
        LINKAGE_ROLLBACK,
        DATA_EXPORT,
        UNAUTHORIZED_ACCESS_ATTEMPT,
        KEY_ACCESS,
        KEY_ROTATION,
        KEY_REVOCATION,
    },
)

RAW_IDENTITY_FIELDS = frozenset(
    {
        "national_id",
        "national_number",
        "raw_national_id",
        "raw_nfc_data",
        "nfc_payload",
        "card_image",
        "encrypted_national_id",
    },
)

DEMOGRAPHIC_FIELDS = frozenset(
    {
        "full_name",
        "mother_name",
        "birth_date",
        "family_number",
        "birth_place",
        "card_issue_date",
        "card_expiry_date",
    },
)
IDENTITY_REFERENCE_FIELDS = frozenset(
    {
        "gula_citizen_identifier",
        "health_number",
        "masked_national_id",
        "national_id_hash",
        "verification_state",
        "provenance",
        "correction_history",
        "evidence_reference",
    },
)
CLINICAL_REFERENCE_FIELDS = frozenset(
    {"patient_record_reference", "medical_record_reference", "facility_id"},
)

_ROLE_FIELDS: dict[IdentityRole, frozenset[str]] = {
    IdentityRole.IDENTITY_ADMINISTRATOR: IDENTITY_REFERENCE_FIELDS | DEMOGRAPHIC_FIELDS,
    IdentityRole.REGISTRATION_OFFICER: IDENTITY_REFERENCE_FIELDS | DEMOGRAPHIC_FIELDS,
    IdentityRole.IDENTITY_REVIEWER: (
        IDENTITY_REFERENCE_FIELDS | DEMOGRAPHIC_FIELDS | CLINICAL_REFERENCE_FIELDS
    ),
    IdentityRole.HEALTHCARE_PROVIDER: (
        IDENTITY_REFERENCE_FIELDS | CLINICAL_REFERENCE_FIELDS | frozenset({"full_name", "birth_date"})
    ),
    IdentityRole.PHYSICIAN: (
        IDENTITY_REFERENCE_FIELDS | CLINICAL_REFERENCE_FIELDS | frozenset({"full_name", "birth_date"})
    ),
    IdentityRole.LABORATORY_TECHNICIAN: (
        frozenset({"gula_citizen_identifier", "health_number", "full_name", "birth_date", "facility_id"})
    ),
    IdentityRole.PHARMACIST: (
        frozenset({"gula_citizen_identifier", "health_number", "full_name", "birth_date", "facility_id"})
    ),
    IdentityRole.FACILITY_ADMINISTRATOR: (
        IDENTITY_REFERENCE_FIELDS | CLINICAL_REFERENCE_FIELDS | frozenset({"full_name"})
    ),
    IdentityRole.AUDITOR: frozenset(
        {"gula_citizen_identifier", "national_id_hash", "verification_state", "evidence_reference", "facility_id"},
    ),
    IdentityRole.SYSTEM_ADMINISTRATOR: frozenset(
        {"gula_citizen_identifier", "verification_state", "facility_id"},
    ),
}

_ROLE_ACTIONS: dict[IdentityRole, frozenset[str]] = {
    IdentityRole.IDENTITY_ADMINISTRATOR: frozenset({IDENTITY_READ, IDENTITY_CORRECTION}),
    IdentityRole.REGISTRATION_OFFICER: frozenset(
        {
            IDENTITY_CREATED,
            IDENTITY_READ,
            ORIGINAL_CARD_PRESENTED,
            LIVE_CAPTURE_STARTED,
            LIVE_CAPTURE_COMPLETED,
            OCR_EXTRACTION,
            MRZ_EXTRACTION,
            NFC_EXTRACTION,
            AUTHENTICITY_INSPECTION,
        },
    ),
    IdentityRole.IDENTITY_REVIEWER: frozenset(
        {
            IDENTITY_READ,
            NID_VERIFICATION_REQUESTED,
            NID_VERIFICATION_RESULT,
            DOCUMENT_AUTHENTICITY_CHECK,
            AUTHENTICITY_INSPECTION,
            AUTHENTICITY_FAILURE,
            COPY_REJECTION,
            SUSPICIOUS_DOCUMENT,
            DOCUMENT_REVIEW,
            REVIEW_OUTCOME,
            IDENTITY_APPROVAL,
            IDENTITY_REJECTION,
            UNAUTHORIZED_VERIFICATION_ATTEMPT,
            MANUAL_OVERRIDE_ATTEMPT,
            IDENTITY_CORRECTION,
            IDENTITY_SUSPENSION,
            IDENTITY_REACTIVATION,
            LINKAGE_REVIEW,
            UNAUTHORIZED_ACCESS_ATTEMPT,
        },
    ),
    IdentityRole.HEALTHCARE_PROVIDER: frozenset({IDENTITY_READ, PATIENT_LINKAGE}),
    IdentityRole.PHYSICIAN: frozenset({IDENTITY_READ, PATIENT_LINKAGE}),
    IdentityRole.LABORATORY_TECHNICIAN: frozenset({IDENTITY_READ}),
    IdentityRole.PHARMACIST: frozenset({IDENTITY_READ}),
    IdentityRole.FACILITY_ADMINISTRATOR: frozenset({IDENTITY_READ, PATIENT_LINKAGE}),
    IdentityRole.AUDITOR: frozenset({IDENTITY_READ, UNAUTHORIZED_ACCESS_ATTEMPT}),
    IdentityRole.SYSTEM_ADMINISTRATOR: frozenset({UNAUTHORIZED_ACCESS_ATTEMPT}),
}


@dataclass(frozen=True)
class IdentityAccessContext:
    decision: AuthorizationDecision
    role: IdentityRole
    actor_id: str
    organization_id: str
    facility_id: str
    purpose: str
    action: str
    requested_fields: tuple[str, ...]
    gula_citizen_identifier: str
    national_id_hash: str
    now: datetime
    consent_required: bool = False
    consent_present: bool = False
    relationship_required: bool = False
    patient_relationship: str | None = None
    break_glass: bool = False
    break_glass_authorized: bool = False
    break_glass_reason: str | None = None
    break_glass_expires_at: datetime | None = None
    allowed_purposes: frozenset[str] | None = None


@dataclass(frozen=True)
class IdentityAccessGrant:
    role: IdentityRole
    action: str
    purpose: str
    organization_id: str
    facility_id: str
    allowed_fields: tuple[str, ...]
    break_glass: bool
    audit_event: AuditEventInput


def assert_minimum_necessary(
    role: IdentityRole,
    requested_fields: tuple[str, ...] | frozenset[str],
) -> frozenset[str]:
    """Return the subset of fields the named role may receive."""
    allowed = _ROLE_FIELDS[role]
    if not requested_fields:
        raise IdentityAccessDeniedError("at least one field is required")
    for field_name in requested_fields:
        if field_name in RAW_IDENTITY_FIELDS:
            raise IdentityAccessDeniedError("raw identity fields are never released")
        if field_name not in allowed:
            raise IdentityAccessDeniedError(f"field {field_name} is outside the role's minimum necessary set")
    return frozenset(requested_fields)


def _assert_gula_identifier_shape(identifier: str) -> None:
    """Reject a raw national number used in place of a GULA Citizen Identifier."""
    if len(identifier) != 12 or not identifier.isascii() or not identifier.isdigit():
        raise IdentityEvidenceError("target must be a valid GULA Citizen Identifier")
    if not 1900 <= int(identifier[:4]) <= 2099:
        raise IdentityEvidenceError("target must use a birth-year prefix")


_RAW_NID_RUN = re.compile(r"(?<!\d)\d{9,14}(?!\d)")
_HASH_LIKE_TEXT = re.compile(r"^(?:[0-9a-f]{64}|v[1-9][0-9]{0,2}\.[0-9a-f]{64})$")


def _iter_audit_text(value: Any) -> Iterator[str]:
    """Yield every string embedded in audit metadata, including nested values."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _iter_audit_text(item)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from _iter_audit_text(item)
    elif isinstance(value, (int, float, bool)):
        yield str(value)


def assert_break_glass_window(
    *,
    break_glass: bool,
    authorized: bool,
    reason: str | None,
    expires_at: datetime | None,
    now: datetime,
) -> None:
    """Require a bounded, authorized, reasoned break-glass window."""
    if not break_glass:
        return
    if not authorized or not reason or not reason.strip():
        raise IdentityAccessDeniedError("break-glass access requires authorization and reason")
    if expires_at is None:
        raise IdentityAccessDeniedError("break-glass access requires an expiry")
    if expires_at <= now:
        raise IdentityAccessDeniedError("break-glass access window has expired")


def build_wave053_audit_event(
    *,
    operation: str,
    actor_id: str,
    purpose: str,
    facility_id: str,
    organization_id: str,
    gula_citizen_identifier: str,
    national_id_hash: str,
    metadata: dict[str, Any] | None = None,
    decision: str = "success",
    reason_code: str | None = None,
    correlation_id: str | None = None,
    raw_nid_for_check: str | None = None,
    raw_nid_values: tuple[str | None, ...] = (),
) -> AuditEventInput:
    """Build a canonical audit event for every Wave 05.3 identity operation."""
    if operation not in WAVE053_AUDIT_OPERATIONS:
        raise IdentityEvidenceError("unknown Wave 05.3 identity audit operation")
    if not actor_id.strip() or not purpose.strip() or not facility_id.strip() or not organization_id.strip():
        raise IdentityEvidenceError("audit requires actor, purpose, organization, and facility")
    if re.fullmatch(r"[0-9a-f]{64}", national_id_hash) is None:
        raise IdentityEvidenceError("audit requires a 64-character hex national ID hash")
    if re.fullmatch(r"\d{12}", gula_citizen_identifier):
        _assert_gula_identifier_shape(gula_citizen_identifier)
    elif _RAW_NID_RUN.search(gula_citizen_identifier):
        raise IdentityEvidenceError("full national ID must not appear in logs or audit text")

    safe_metadata: dict[str, Any] = {
        "operation": operation,
        "purpose": purpose,
        "organization_id": organization_id,
        "facility_id": facility_id,
        "national_id_hash": national_id_hash,
    }
    for key, value in (metadata or {}).items():
        if str(key).lower() in {"raw_national_id", "national_id", "national_number", "nid"}:
            raise IdentityEvidenceError("raw national ID is forbidden in audit metadata")
        safe_metadata[str(key)] = value

    embedded_text: list[str] = [
        actor_id,
        purpose,
        facility_id,
        organization_id,
        decision,
        reason_code or "",
        correlation_id or "",
    ]
    embedded_text.extend(_iter_audit_text(metadata or {}))
    for candidate in embedded_text:
        if candidate and not _HASH_LIKE_TEXT.fullmatch(candidate) and _RAW_NID_RUN.search(candidate):
            raise IdentityEvidenceError("full national ID must not appear in logs or audit text")

    event = AuditEventInput(
        event_type="IDENTITY_OPERATION_WAVE053",
        category="IDENTITY_GOVERNANCE",
        action=operation.lower(),
        actor_id=actor_id,
        actor_type="human",
        organization_id=organization_id,
        facility_id=facility_id,
        target_type="citizen_identity",
        target_id=gula_citizen_identifier,
        decision=decision,
        reason_code=reason_code,
        correlation_id=correlation_id,
        source="wave05_3_domain",
        data_classification="HIGHLY_RESTRICTED_IDENTITY_DATA",
        metadata=safe_metadata,
    )
    checked_raw_values: list[str] = []
    for value in (raw_nid_for_check, *raw_nid_values):
        if value and len(normalize_national_id(value)) >= 12:
            checked_raw_values.append(value)
    assert_no_full_national_identifier(repr(event), *checked_raw_values)
    return event


def assert_identity_access_v2(context: IdentityAccessContext) -> IdentityAccessGrant:
    """Validate identity-specific constraints around a canonical allow decision."""
    if context.action not in WAVE053_AUDIT_OPERATIONS:
        raise IdentityAccessDeniedError("unknown identity operation")
    if not context.decision.allowed:
        raise IdentityAccessDeniedError(
            f"canonical authorization denied: {context.decision.reason_code.value}",
        )
    if context.role not in _ROLE_ACTIONS or context.action not in _ROLE_ACTIONS[context.role]:
        raise IdentityAccessDeniedError("role is not approved for this identity operation")

    purposes = context.allowed_purposes or AuthorizationDecisionService.ALLOWED_PURPOSES
    if context.purpose not in purposes:
        raise IdentityAccessDeniedError("purpose is not approved for identity access")
    if not context.organization_id.strip() or not context.facility_id.strip():
        raise IdentityAccessDeniedError("organization and facility scope are required")
    if not context.actor_id.strip():
        raise IdentityAccessDeniedError("actor is required")
    _assert_gula_identifier_shape(context.gula_citizen_identifier)

    if context.consent_required and not context.consent_present:
        raise IdentityAccessDeniedError("consent is required for this access")
    if context.relationship_required and not (context.patient_relationship or "").strip():
        raise IdentityAccessDeniedError("patient relationship is required for this access")

    assert_break_glass_window(
        break_glass=context.break_glass,
        authorized=context.break_glass_authorized,
        reason=context.break_glass_reason,
        expires_at=context.break_glass_expires_at,
        now=context.now,
    )
    fields = assert_minimum_necessary(context.role, context.requested_fields)

    audit_event = build_wave053_audit_event(
        operation=context.action,
        actor_id=context.actor_id,
        purpose=context.purpose,
        facility_id=context.facility_id,
        organization_id=context.organization_id,
        gula_citizen_identifier=context.gula_citizen_identifier,
        national_id_hash=context.national_id_hash,
        metadata={
            "role": context.role.value,
            "requested_fields": sorted(fields),
            "consent_present": context.consent_present,
            "patient_relationship": context.patient_relationship,
            "break_glass": context.break_glass,
            "break_glass_reason": context.break_glass_reason,
        },
        raw_nid_values=(
            context.actor_id,
            context.purpose,
            context.organization_id,
            context.facility_id,
            context.role.value,
            *context.requested_fields,
            context.patient_relationship,
            context.break_glass_reason,
        ),
    )
    return IdentityAccessGrant(
        role=context.role,
        action=context.action,
        purpose=context.purpose,
        organization_id=context.organization_id,
        facility_id=context.facility_id,
        allowed_fields=tuple(sorted(fields)),
        break_glass=context.break_glass,
        audit_event=audit_event,
    )


def utc_now() -> datetime:
    return datetime.now(UTC)
