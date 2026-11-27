"""Wave 05.2 national identity governance domain helpers.

These helpers are pure-Python, synthetic-data safe, and reversible. They add no
DDL, migration, HTTP route, government connection, NFC specification, OCR
service, or persistence write. They also do not perform identity verification;
they only express the fail-closed boundaries that an approved flow must follow.

Four separate phases are represented:

1. Data Extraction (OCR/NFC/citizen input)
2. Document Authenticity Verification (approved official mechanism only)
3. Identity Verification (authorized decision only)
4. Government Source Verification (approved government authority only)

The canonical MPI safety, NID normalization/HMAC, privacy masking,
authorization decision, audit-input, and encryption helpers are reused.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Any

from app._compat import UTC
from app.core.privacy import PIIMasker
from app.identity.services.authorization_decision import (
    AuthorizationDecision,
    AuthorizationDecisionService,
)
from app.identity.services.canonical_audit import AuditEventInput
from app.services.identity import hash_national_id, normalize_name, normalize_national_id
from app.services.mpi.identity_safety import (
    DETERMINISTIC_UNCERTAIN,
    NID_CONFLICT,
    NO_MATCH,
    assert_merge_allowed,
    classify_nid_match,
    secondary_corroboration,
)
from shared.security.encryption import encrypt_national_id as canonical_encrypt_national_id


class IdentityEvidenceError(ValueError):
    """Raised when extracted or supplied identity evidence is unusable."""


class IdentityTransitionError(ValueError):
    """Raised when a requested verification state transition is not allowed."""


class IdentityAccessDeniedError(PermissionError):
    """Raised when an identity operation lacks an approved authorization decision."""


# Verification states from the owner-approved Wave 05.2 design.
UNVERIFIED = "UNVERIFIED"
DATA_EXTRACTED = "DATA_EXTRACTED"
PENDING_REVIEW = "PENDING_REVIEW"
DOCUMENT_CHECKED = "DOCUMENT_CHECKED"
GOVERNMENT_VERIFIED = "GOVERNMENT_VERIFIED"
VERIFIED = "VERIFIED"
REJECTED = "REJECTED"
EXPIRED = "EXPIRED"
SUSPENDED = "SUSPENDED"

VERIFICATION_STATES = frozenset(
    {
        UNVERIFIED,
        DATA_EXTRACTED,
        PENDING_REVIEW,
        DOCUMENT_CHECKED,
        GOVERNMENT_VERIFIED,
        VERIFIED,
        REJECTED,
        EXPIRED,
        SUSPENDED,
    },
)

EXTRACTION_COMPLETED = "EXTRACTION_COMPLETED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
REVIEW_APPROVED = "REVIEW_APPROVED"
REVIEW_REJECTED = "REVIEW_REJECTED"
DOCUMENT_AUTHENTICITY_CONFIRMED = "DOCUMENT_AUTHENTICITY_CONFIRMED"
GOVERNMENT_SOURCE_CONFIRMED = "GOVERNMENT_SOURCE_CONFIRMED"
IDENTITY_DECISION_APPROVED = "IDENTITY_DECISION_APPROVED"
CARD_EXPIRED = "CARD_EXPIRED"
CONFLICT_DETECTED = "CONFLICT_DETECTED"
INVESTIGATION_AUTHORIZED = "INVESTIGATION_AUTHORIZED"
INVALIDATION_CONFIRMED = "INVALIDATION_CONFIRMED"
NEW_EVIDENCE_SUBMITTED = "NEW_EVIDENCE_SUBMITTED"

VERIFICATION_EVENTS = frozenset(
    {
        EXTRACTION_COMPLETED,
        REVIEW_REQUIRED,
        REVIEW_APPROVED,
        REVIEW_REJECTED,
        DOCUMENT_AUTHENTICITY_CONFIRMED,
        GOVERNMENT_SOURCE_CONFIRMED,
        IDENTITY_DECISION_APPROVED,
        CARD_EXPIRED,
        CONFLICT_DETECTED,
        INVESTIGATION_AUTHORIZED,
        INVALIDATION_CONFIRMED,
        NEW_EVIDENCE_SUBMITTED,
    },
)

_TRANSITIONS: dict[str, dict[str, str]] = {
    UNVERIFIED: {EXTRACTION_COMPLETED: DATA_EXTRACTED},
    DATA_EXTRACTED: {
        REVIEW_REQUIRED: PENDING_REVIEW,
        DOCUMENT_AUTHENTICITY_CONFIRMED: DOCUMENT_CHECKED,
        GOVERNMENT_SOURCE_CONFIRMED: GOVERNMENT_VERIFIED,
        CARD_EXPIRED: EXPIRED,
    },
    PENDING_REVIEW: {
        REVIEW_APPROVED: VERIFIED,
        REVIEW_REJECTED: REJECTED,
        CARD_EXPIRED: EXPIRED,
    },
    DOCUMENT_CHECKED: {
        REVIEW_REQUIRED: PENDING_REVIEW,
        GOVERNMENT_SOURCE_CONFIRMED: GOVERNMENT_VERIFIED,
        CARD_EXPIRED: EXPIRED,
    },
    GOVERNMENT_VERIFIED: {
        IDENTITY_DECISION_APPROVED: VERIFIED,
        REVIEW_REQUIRED: PENDING_REVIEW,
        CARD_EXPIRED: EXPIRED,
    },
    VERIFIED: {CARD_EXPIRED: EXPIRED, CONFLICT_DETECTED: SUSPENDED},
    SUSPENDED: {
        INVESTIGATION_AUTHORIZED: PENDING_REVIEW,
        INVALIDATION_CONFIRMED: REJECTED,
        CARD_EXPIRED: EXPIRED,
    },
    EXPIRED: {NEW_EVIDENCE_SUBMITTED: PENDING_REVIEW},
    REJECTED: {NEW_EVIDENCE_SUBMITTED: PENDING_REVIEW},
}


@dataclass(frozen=True)
class VerificationTransitionContext:
    """Trusted context for a verification-state transition.

    Authority names are never implicitly trusted. The caller must pass explicit
    approved authority sets to :func:`transition_verification_state`; the
    default is deny. Test evidence uses clearly labelled synthetic authorities.
    """

    actor: str | None = None
    reviewer: str | None = None
    purpose: str | None = None
    facility_id: str | None = None
    source: str | None = None
    reason: str | None = None
    evidence_reference: str | None = None
    government_authority: str | None = None
    government_operation_id: str | None = None
    document_authority: str | None = None
    citizen_confirmation: bool = False


def transition_verification_state(
    current: str,
    event: str,
    *,
    context: VerificationTransitionContext | None = None,
    allowed_government_authorities: frozenset[str] = frozenset(),
    allowed_document_authorities: frozenset[str] = frozenset(),
) -> str:
    """Return the next verification state or fail closed."""
    if current not in VERIFICATION_STATES:
        raise IdentityTransitionError("unknown current verification state")
    if event not in VERIFICATION_EVENTS:
        raise IdentityTransitionError("unknown verification transition event")

    target = _TRANSITIONS.get(current, {}).get(event)
    if target is None:
        raise IdentityTransitionError(f"transition {event} is not allowed from {current}")

    ctx = context or VerificationTransitionContext()

    if event == EXTRACTION_COMPLETED and not ctx.source:
        raise IdentityTransitionError("extraction transition requires a source")
    if event == DOCUMENT_AUTHENTICITY_CONFIRMED:
        if not ctx.document_authority or ctx.document_authority not in allowed_document_authorities:
            raise IdentityTransitionError("document authority is not approved")
        if not ctx.evidence_reference:
            raise IdentityTransitionError("document authenticity evidence reference is required")
    if event == GOVERNMENT_SOURCE_CONFIRMED:
        if not ctx.government_authority or ctx.government_authority not in allowed_government_authorities:
            raise IdentityTransitionError("government source authority is not approved")
        if not ctx.government_operation_id or not ctx.evidence_reference:
            raise IdentityTransitionError("government verification evidence is incomplete")
    if event in {REVIEW_REQUIRED, REVIEW_APPROVED, REVIEW_REJECTED, CONFLICT_DETECTED} and not ctx.reason:
        raise IdentityTransitionError("review transition requires a reason")
    if event in {REVIEW_APPROVED, REVIEW_REJECTED, CONFLICT_DETECTED} and not ctx.reviewer:
        raise IdentityTransitionError("review transition requires a named reviewer")
    if event == IDENTITY_DECISION_APPROVED:
        if not ctx.citizen_confirmation:
            raise IdentityTransitionError("final identity decision requires citizen confirmation")
        if not ctx.reviewer or not ctx.reason:
            raise IdentityTransitionError("final identity decision requires reviewer and reason")
    if (
        event in {INVESTIGATION_AUTHORIZED, INVALIDATION_CONFIRMED}
        and not (ctx.reviewer and ctx.reason)
    ):
        raise IdentityTransitionError("transition requires reviewer and reason")

    return target


SOURCE_OFFICIAL_GOVERNMENT = "official_government_source"
SOURCE_CARD_OCR = "card_ocr"
SOURCE_CARD_NFC = "card_nfc"
SOURCE_CITIZEN_ATTESTATION = "citizen_attestation"
SOURCE_AUTHORIZED_REVIEWER = "authorized_reviewer"

NATIONAL_CARD_FIELDS = (
    "national_id",
    "full_name",
    "mother_name",
    "birth_date",
    "family_number",
    "birth_place",
    "card_issue_date",
    "card_expiry_date",
)

_NUMERIC_FIELDS = frozenset(
    {"national_id", "family_number", "birth_date", "card_issue_date", "card_expiry_date"},
)
_NAME_FIELDS = frozenset({"full_name", "mother_name", "birth_place"})


@dataclass(frozen=True)
class ExtractedField:
    """A field captured from one extraction mechanism, never a verification."""

    value: str | None
    source: str
    confidence: float | None = None
    extracted_at: datetime | None = None


@dataclass(frozen=True)
class FieldComparison:
    field: str
    agreement: bool
    conflict: bool
    uncertain: bool
    missing: bool
    reason: str


@dataclass(frozen=True)
class ExtractionComparison:
    agreements: tuple[str, ...]
    conflicts: tuple[FieldComparison, ...]
    uncertain_fields: tuple[FieldComparison, ...]
    missing_fields: tuple[FieldComparison, ...]
    recommended_event: str


def _as_extracted_field(value: ExtractedField | str | None, source: str) -> ExtractedField:
    if value is None:
        return ExtractedField(value=None, source=source, confidence=0.0)
    if isinstance(value, ExtractedField):
        return value
    confidence = 1.0 if source == SOURCE_CARD_NFC else 0.0
    return ExtractedField(value=str(value), source=source, confidence=confidence)


def _canonical_field_value(field: str, value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if field in _NAME_FIELDS:
        return normalize_name(text)
    if field in _NUMERIC_FIELDS:
        return normalize_national_id(text)
    return text.casefold()


def classify_card_extraction(
    ocr_fields: Mapping[str, ExtractedField | str | None],
    nfc_fields: Mapping[str, ExtractedField | str | None],
    *,
    required_fields: tuple[str, ...] = NATIONAL_CARD_FIELDS,
    low_confidence_threshold: float = 0.85,
) -> ExtractionComparison:
    """Compare synthetic OCR/NFC extraction without granting verification."""
    if not 0.0 <= low_confidence_threshold <= 1.0:
        raise IdentityEvidenceError("low_confidence_threshold must be between 0 and 1")

    agreements: list[str] = []
    conflicts: list[FieldComparison] = []
    uncertain: list[FieldComparison] = []
    missing: list[FieldComparison] = []

    for name in dict.fromkeys((*required_fields, *ocr_fields.keys(), *nfc_fields.keys())):
        ocr = _as_extracted_field(ocr_fields.get(name), SOURCE_CARD_OCR)
        nfc = _as_extracted_field(nfc_fields.get(name), SOURCE_CARD_NFC)
        ocr_value = _canonical_field_value(name, ocr.value)
        nfc_value = _canonical_field_value(name, nfc.value)

        if ocr_value is None and nfc_value is None:
            missing.append(FieldComparison(name, False, False, False, True, "field absent from both sources"))
            continue
        if ocr_value is None or nfc_value is None:
            uncertain.append(
                FieldComparison(name, False, False, True, True, "field present in only one source")
            )
            continue

        low_confidence = (
            ocr.confidence is not None and ocr.confidence < low_confidence_threshold
        ) or (nfc.confidence is not None and nfc.confidence < low_confidence_threshold)
        if low_confidence:
            uncertain.append(FieldComparison(name, False, False, True, False, "low extraction confidence"))
            continue
        if ocr_value != nfc_value:
            conflicts.append(FieldComparison(name, False, True, False, False, "OCR/NFC disagreement"))
            continue
        agreements.append(name)

    unsafe = bool(conflicts or uncertain or missing)
    return ExtractionComparison(
        agreements=tuple(agreements),
        conflicts=tuple(conflicts),
        uncertain_fields=tuple(uncertain),
        missing_fields=tuple(missing),
        recommended_event=REVIEW_REQUIRED if unsafe else EXTRACTION_COMPLETED,
    )


def _parse_card_date(value: date | datetime | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    digits = normalize_national_id(str(value))
    if len(digits) != 8:
        raise IdentityEvidenceError("card date must contain an eight-digit date")
    try:
        return datetime.strptime(digits, "%Y%m%d").date()
    except ValueError as exc:
        raise IdentityEvidenceError("card date is not a valid calendar date") from exc


def card_validity_event(
    card_expiry_date: date | datetime | str,
    *,
    now: datetime | None = None,
) -> str | None:
    """Return CARD_EXPIRED when the card validity period has ended."""
    expiry = _parse_card_date(card_expiry_date)
    current = (now or datetime.now(UTC)).date()
    return CARD_EXPIRED if current > expiry else None


def mask_national_id(value: str) -> str:
    """Return a UI/log-safe masked form; the full value is never returned."""
    digits = normalize_national_id(value)
    if not digits:
        return "[ID_MASKED]"
    if len(digits) <= 4:
        return "*" * len(digits)
    return f"{'*' * (len(digits) - 4)}{digits[-4:]}"


@dataclass(frozen=True)
class NationalIdEvidence:
    national_id_hash: str
    masked_national_id: str
    source: str
    captured_at: datetime
    confidence: float | None = None
    is_verification_authority: bool = False


def build_national_id_evidence(
    raw_national_id: str,
    *,
    source: str,
    captured_at: datetime,
    confidence: float | None = None,
) -> NationalIdEvidence:
    """Accept a raw ID at the boundary and retain only hash/masked forms."""
    normalized = normalize_national_id(raw_national_id)
    if not normalized:
        raise IdentityEvidenceError("national ID evidence is empty")
    if source not in {
        SOURCE_OFFICIAL_GOVERNMENT,
        SOURCE_CARD_OCR,
        SOURCE_CARD_NFC,
        SOURCE_CITIZEN_ATTESTATION,
        SOURCE_AUTHORIZED_REVIEWER,
    }:
        raise IdentityEvidenceError("unknown national ID evidence source")
    return NationalIdEvidence(
        national_id_hash=hash_national_id(normalized),
        masked_national_id=mask_national_id(normalized),
        source=source,
        captured_at=captured_at,
        confidence=confidence,
        is_verification_authority=False,
    )


@dataclass(frozen=True)
class CitizenAttestation:
    confirmed_by: str
    confirmed_at: datetime
    fields_confirmed: tuple[str, ...]


@dataclass(frozen=True)
class DocumentAuthenticityEvidence:
    authority: str
    evidence_reference: str
    checked_at: datetime
    result: str


@dataclass(frozen=True)
class GovernmentVerificationEvidence:
    authority: str
    operation_id: str
    status: str
    verified_at: datetime


@dataclass(frozen=True)
class IdentityVerificationDecision:
    reviewer: str
    reason: str
    decided_at: datetime
    evidence_reference: str


@dataclass(frozen=True)
class IdentityFieldProvenance:
    field: str
    source: str
    extracted_at: datetime
    confidence: float | None = None
    verification_state: str = UNVERIFIED
    last_verified_at: datetime | None = None


@dataclass(frozen=True)
class CorrectionEvent:
    field: str
    old_value: Any
    new_value: Any
    source: str
    actor: str
    reason: str
    changed_at: datetime


@dataclass(frozen=True)
class UnifiedCitizenIdentity:
    """Domain-level civil identity; no raw national ID is retained."""

    gula_citizen_identifier: str
    national_id_hash: str
    masked_national_id: str
    full_name: str
    mother_name: str
    birth_date: str
    family_number: str | None = None
    birth_place: str | None = None
    card_issue_date: str | None = None
    card_expiry_date: str | None = None
    verification_state: str = UNVERIFIED
    last_verification_at: datetime | None = None
    corrections: tuple[CorrectionEvent, ...] = ()
    provenance: tuple[IdentityFieldProvenance, ...] = ()

    def to_public_dict(self) -> dict[str, Any]:
        """Return a masked presentation model suitable for UI display."""
        return {
            "gula_citizen_identifier": self.gula_citizen_identifier,
            "masked_national_id": self.masked_national_id,
            "full_name": self.full_name,
            "mother_name": self.mother_name,
            "birth_date": self.birth_date,
            "family_number": self.family_number,
            "birth_place": self.birth_place,
            "card_issue_date": self.card_issue_date,
            "card_expiry_date": self.card_expiry_date,
            "verification_state": self.verification_state,
            "last_verification_at": self.last_verification_at,
        }


_IDENTITY_CORRECTABLE_FIELDS = frozenset(
    {
        "national_id_hash",
        "masked_national_id",
        "full_name",
        "mother_name",
        "birth_date",
        "family_number",
        "birth_place",
        "card_issue_date",
        "card_expiry_date",
    },
)


def append_identity_correction(
    identity: UnifiedCitizenIdentity,
    *,
    field_name: str,
    new_value: Any,
    source: str,
    actor: str,
    reason: str,
    changed_at: datetime,
) -> UnifiedCitizenIdentity:
    """Return a corrected identity with append-only history and stable ID."""
    if field_name == "gula_citizen_identifier":
        raise IdentityEvidenceError("GULA Citizen Identifier is immutable")
    if field_name not in _IDENTITY_CORRECTABLE_FIELDS:
        raise IdentityEvidenceError("unknown correctable identity field")
    if not reason.strip() or not actor.strip():
        raise IdentityEvidenceError("correction requires actor and reason")

    old_value = getattr(identity, field_name)
    event = CorrectionEvent(
        field=field_name,
        old_value=old_value,
        new_value=new_value,
        source=source,
        actor=actor,
        reason=reason,
        changed_at=changed_at,
    )
    updated_provenance = (
        *(item for item in identity.provenance if item.field != field_name),
        IdentityFieldProvenance(
            field=field_name,
            source=source,
            extracted_at=changed_at,
            confidence=1.0,
            verification_state=identity.verification_state,
            last_verified_at=identity.last_verification_at,
        ),
    )
    return replace(
        identity,
        **{field_name: new_value},
        corrections=(*identity.corrections, event),
        provenance=updated_provenance,
    )


RESIDENCE_SOURCE_CITIZEN = "citizen_entered"
RESIDENCE_SOURCE_INDEPENDENT = "independent_verification"


@dataclass(frozen=True)
class ResidenceRecord:
    """Separate, future-extendable residence aggregate."""

    value: str
    source: str
    valid_from: date
    valid_until: date | None
    updated_at: datetime
    citizen_entered: bool
    verification_state: str


def build_residence_record(
    *,
    value: str,
    source: str,
    valid_from: date,
    valid_until: date | None,
    updated_at: datetime,
    enabled: bool,
) -> ResidenceRecord:
    """Build a residence record only when the feature is explicitly enabled."""
    if not enabled:
        raise IdentityEvidenceError("residential data collection is not enabled")
    if source not in {RESIDENCE_SOURCE_CITIZEN, RESIDENCE_SOURCE_INDEPENDENT}:
        raise IdentityEvidenceError("unknown residence data source")
    if valid_until is not None and valid_until < valid_from:
        raise IdentityEvidenceError("residence validity period is inverted")
    return ResidenceRecord(
        value=value,
        source=source,
        valid_from=valid_from,
        valid_until=valid_until,
        updated_at=updated_at,
        citizen_entered=source == RESIDENCE_SOURCE_CITIZEN,
        verification_state=UNVERIFIED,
    )


@dataclass(frozen=True)
class LinkageReviewer:
    name: str
    user_id: int | None = None


@dataclass(frozen=True)
class LinkageCandidate:
    """Minimal existing-field view compatible with canonical MPI guards."""

    id: str
    status: str = "active"
    nid_hash: str | None = None
    nid_verified: bool = False
    birth_year: int | None = None
    birth_month: int | None = None
    birth_day: int | None = None
    phone_last10: str | None = None
    family_id_hash: str | None = None


def assert_linkage_allowed(
    primary: LinkageCandidate,
    secondary: LinkageCandidate,
    *,
    decision: str,
    reviewer: LinkageReviewer,
    reason: str,
    evidence_reference: str,
) -> None:
    """Fail closed on name-only linkage, NID conflict, and missing authority."""
    if decision != "APPROVED":
        raise IdentityEvidenceError("linkage decision must be an explicit approval")
    if not reviewer.name.strip() or reviewer.user_id is None:
        raise IdentityEvidenceError("linkage requires a named reviewer with an account")
    if not reason.strip() or not evidence_reference.strip():
        raise IdentityEvidenceError("linkage requires reason and evidence reference")

    classification = classify_nid_match(
        profile_hash=primary.nid_hash,
        candidate_hash=secondary.nid_hash,
        candidate_verified=secondary.nid_verified,
        corroborated=secondary_corroboration(primary, secondary),
    )
    if classification.disposition == NID_CONFLICT:
        raise IdentityEvidenceError("conflicting NID hashes veto linkage")
    if classification.disposition in {NO_MATCH, DETERMINISTIC_UNCERTAIN}:
        # Explicit human approval is permitted for uncertain cases, but the
        # recorded reason/evidence/reference above are mandatory. No name,
        # mother name, or DOB similarity is considered by this guard.
        pass

    assert_merge_allowed(
        primary,
        secondary,
        reason=reason,
        decided_by_user_id=reviewer.user_id,
    )


@dataclass(frozen=True)
class LinkageRollback:
    reviewer: LinkageReviewer
    reason: str
    rolled_back_at: datetime


@dataclass(frozen=True)
class LinkageDecision:
    primary_identifier: str
    secondary_identifier: str
    reviewer: LinkageReviewer
    reason: str
    evidence_reference: str
    decided_at: datetime
    active: bool = True
    rollback: LinkageRollback | None = None

    def to_audit_metadata(self) -> dict[str, Any]:
        return {
            "primary_identifier": self.primary_identifier,
            "secondary_identifier": self.secondary_identifier,
            "reviewer": self.reviewer.name,
            "reason": self.reason,
            "evidence_reference": self.evidence_reference,
            "active": self.active,
            "rolled_back": self.rollback is not None,
        }


def append_linkage_rollback(
    decision: LinkageDecision,
    *,
    reviewer: LinkageReviewer,
    reason: str,
    rolled_back_at: datetime,
) -> LinkageDecision:
    """Record a policy-bounded rollback without deleting the original decision."""
    if not decision.active:
        raise IdentityEvidenceError("linkage decision is already rolled back")
    if not reviewer.name.strip() or reviewer.user_id is None or not reason.strip():
        raise IdentityEvidenceError("rollback requires a named reviewer and reason")
    rollback = LinkageRollback(reviewer=reviewer, reason=reason, rolled_back_at=rolled_back_at)
    return replace(decision, active=False, rollback=rollback)


READ = "READ"
MODIFY = "MODIFY"
EXPORT = "EXPORT"
VERIFY = "VERIFY"
REVIEW = "REVIEW"
MERGE = "MERGE"
ROLLBACK = "ROLLBACK"
IDENTITY_AUDIT_OPERATIONS = frozenset({READ, MODIFY, EXPORT, VERIFY, REVIEW, MERGE, ROLLBACK})
IDENTITY_ACCESS_ACTIONS = IDENTITY_AUDIT_OPERATIONS


def assert_no_full_national_identifier(text: str, *raw_values: str | None) -> None:
    """Fail when a raw national number appears in text intended for logs/audit."""
    for raw in raw_values:
        if not raw:
            continue
        normalized = normalize_national_id(raw)
        if normalized and normalized in normalize_national_id(text):
            raise IdentityEvidenceError("full national ID must not appear in logs or audit text")


def safe_identity_log_context(
    *,
    gula_citizen_identifier: str,
    national_id_hash: str,
    masked_national_id: str,
    free_text: str | None = None,
    raw_nid_for_check: str | None = None,
) -> dict[str, Any]:
    """Return a bounded log context with no full national number."""
    context: dict[str, Any] = {
        "gula_citizen_identifier": gula_citizen_identifier,
        "national_id_hash": national_id_hash,
        "masked_national_id": masked_national_id,
    }
    if free_text:
        context["redacted_text"] = PIIMasker.mask_string(free_text)
    rendered = repr(context)
    assert_no_full_national_identifier(rendered, raw_nid_for_check)
    return context


def build_identity_audit_event(
    *,
    operation: str,
    actor_id: str,
    purpose: str,
    facility_id: str,
    gula_citizen_identifier: str,
    national_id_hash: str,
    metadata: Mapping[str, Any] | None = None,
    decision: str = "success",
    reason_code: str | None = None,
    raw_nid_for_check: str | None = None,
) -> AuditEventInput:
    """Build a canonical audit input that never contains a full national ID."""
    if operation not in IDENTITY_AUDIT_OPERATIONS:
        raise IdentityEvidenceError("unknown identity audit operation")
    if not actor_id.strip() or not purpose.strip() or not facility_id.strip():
        raise IdentityEvidenceError("audit requires actor, purpose, and facility")

    safe_metadata: dict[str, Any] = {
        "operation": operation,
        "purpose": purpose,
        "facility_id": facility_id,
        "national_id_hash": national_id_hash,
    }
    if metadata:
        for key, value in metadata.items():
            if str(key) in {"raw_national_id", "national_id", "nid"}:
                raise IdentityEvidenceError("raw national ID is forbidden in audit metadata")
            safe_metadata[str(key)] = value

    event = AuditEventInput(
        event_type="IDENTITY_OPERATION",
        category="IDENTITY_GOVERNANCE",
        action=operation.lower(),
        actor_id=actor_id,
        actor_type="human",
        facility_id=facility_id,
        target_type="citizen_identity",
        target_id=gula_citizen_identifier,
        decision=decision,
        reason_code=reason_code,
        source="wave05_2_domain",
        data_classification="SENSITIVE",
        metadata=safe_metadata,
    )
    assert_no_full_national_identifier(repr(event), raw_nid_for_check)
    return event


def assert_identity_access_allowed(
    *,
    decision: AuthorizationDecision,
    action: str,
    purpose: str,
    facility_id: str,
    allowed_purposes: frozenset[str] | None = None,
) -> None:
    """Require an existing canonical allow decision with a bound purpose/scope."""
    purposes = allowed_purposes or AuthorizationDecisionService.ALLOWED_PURPOSES
    if action not in IDENTITY_ACCESS_ACTIONS:
        raise IdentityAccessDeniedError("unknown identity action")
    if not decision.allowed:
        raise IdentityAccessDeniedError(f"authorization denied: {decision.reason_code.value}")
    if not purpose or purpose not in purposes:
        raise IdentityAccessDeniedError("purpose is not approved for identity access")
    if not facility_id.strip():
        raise IdentityAccessDeniedError("facility scope is required")


@dataclass(frozen=True)
class ProtectedNationalIdEnvelope:
    national_id_hash: str
    encrypted_token: str
    masked_national_id: str


def protect_national_id_for_storage(
    raw_national_id: str,
    *,
    encryption_key: str,
    hmac_key: str,
) -> ProtectedNationalIdEnvelope:
    """Use the canonical encryption/HMAC helpers; keys stay outside the DB."""
    normalized = normalize_national_id(raw_national_id)
    if not normalized:
        raise IdentityEvidenceError("national ID envelope input is empty")
    return ProtectedNationalIdEnvelope(
        national_id_hash=hash_national_id(normalized),
        encrypted_token=canonical_encrypt_national_id(normalized, encryption_key, hmac_key),
        masked_national_id=mask_national_id(normalized),
    )
