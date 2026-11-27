"""Wave 05.3 NIDP original-card and live-document authenticity contracts.

This module adds a synthetic policy boundary around existing Wave 05.2 and
Wave 05.3 components. It does not define card layout, APDUs, chip keys,
certificates, reader protocols, government APIs, or authenticity success.
No real identity number, card image, or raw NFC payload is stored.

Every decision is routed to human review in this wave because no officially
documented chip-authenticity or alternative document-authenticity procedure is
approved. ``DOCUMENT_AUTHENTICITY_CONFIRMED`` and ``VERIFIED`` are therefore
unreachable through this boundary.
"""

from __future__ import annotations

import re
import secrets
import threading
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from app._compat import UTC
from app.national.services.document_extraction import (
    SOURCE_CARD_NFC,
    SOURCE_CARD_OCR,
    ExtractionArtifact,
    ExtractionStatus,
)
from app.national.services.identity_access import (
    AUTHENTICITY_FAILURE,
    AUTHENTICITY_INSPECTION,
    COPY_REJECTION,
    DOCUMENT_REVIEW,
    LIVE_CAPTURE_COMPLETED,
    LIVE_CAPTURE_STARTED,
    MANUAL_OVERRIDE_ATTEMPT,
    MRZ_EXTRACTION,
    NFC_EXTRACTION,
    ORIGINAL_CARD_PRESENTED,
    REVIEW_OUTCOME,
    SUSPICIOUS_DOCUMENT,
    UNAUTHORIZED_VERIFICATION_ATTEMPT,
    IdentityAccessContext,
    IdentityAccessGrant,
    assert_identity_access_v2,
    build_wave053_audit_event,
)
from app.national.services.identity_governance import (
    CARD_EXPIRED,
    DATA_EXTRACTED,
    DOCUMENT_CHECKED,
    EXPIRED,
    EXTRACTION_COMPLETED,
    GOVERNMENT_VERIFIED,
    INVESTIGATION_AUTHORIZED,
    NATIONAL_CARD_FIELDS,
    NEW_EVIDENCE_SUBMITTED,
    PENDING_REVIEW,
    REJECTED,
    REVIEW_REQUIRED,
    SUSPENDED,
    UNVERIFIED,
    VERIFICATION_STATES,
    VERIFIED,
    VerificationTransitionContext,
    transition_verification_state,
)


class DocumentAuthenticityError(ValueError):
    """Raised when the original-card policy boundary is violated."""


class DocumentAuthenticityState(StrEnum):
    ORIGINAL_CARD_PRESENTED = "ORIGINAL_CARD_PRESENTED"
    LIVE_CAPTURE_COMPLETED = "LIVE_CAPTURE_COMPLETED"
    VISUAL_INSPECTION_COMPLETED = "VISUAL_INSPECTION_COMPLETED"
    MRZ_READ_SUCCESSFULLY = "MRZ_READ_SUCCESSFULLY"
    NFC_READ_SUCCESSFULLY = "NFC_READ_SUCCESSFULLY"
    CHIP_AUTHENTICITY_VERIFIED = "CHIP_AUTHENTICITY_VERIFIED"
    DOCUMENT_AUTHENTICITY_CONFIRMED = "DOCUMENT_AUTHENTICITY_CONFIRMED"
    DOCUMENT_AUTHENTICITY_FAILED = "DOCUMENT_AUTHENTICITY_FAILED"
    DOCUMENT_REVIEW_REQUIRED = "DOCUMENT_REVIEW_REQUIRED"


class OriginalDocumentChannel(StrEnum):
    AUTHORIZED_LIVE_CAMERA_SESSION = "AUTHORIZED_LIVE_CAMERA_SESSION"
    PREVIOUS_CAPTURE = "PREVIOUS_CAPTURE"
    PHONE_GALLERY = "PHONE_GALLERY"
    WHATSAPP_IMAGE = "WHATSAPP_IMAGE"
    TELEGRAM_IMAGE = "TELEGRAM_IMAGE"
    EMAIL_ATTACHMENT = "EMAIL_ATTACHMENT"
    SCANNED_COPY = "SCANNED_COPY"
    PHOTOCOPY = "PHOTOCOPY"
    PRINTED_REPLICA = "PRINTED_REPLICA"
    PDF_DOCUMENT = "PDF_DOCUMENT"
    SCREENSHOT = "SCREENSHOT"
    DIGITAL_REPRODUCTION = "DIGITAL_REPRODUCTION"
    CERTIFIED_COPY = "CERTIFIED_COPY"
    UNCERTIFIED_COPY = "UNCERTIFIED_COPY"


class RejectionClassification(StrEnum):
    COPY_PRESENTED = "COPY_PRESENTED"
    PRINTED_REPLICA_PRESENTED = "PRINTED_REPLICA_PRESENTED"
    DIGITAL_IMAGE_PRESENTED = "DIGITAL_IMAGE_PRESENTED"
    SCREENSHOT_PRESENTED = "SCREENSHOT_PRESENTED"
    ORIGINALITY_UNCERTAIN = "ORIGINALITY_UNCERTAIN"
    SECURITY_FEATURE_MISMATCH = "SECURITY_FEATURE_MISMATCH"


class NfcState(StrEnum):
    NFC_UNAVAILABLE = "NFC_UNAVAILABLE"
    NFC_UNSUPPORTED = "NFC_UNSUPPORTED"
    NFC_READ_FAILED = "NFC_READ_FAILED"
    NFC_READ_SUCCESSFULLY = "NFC_READ_SUCCESSFULLY"
    CHIP_AUTHENTICITY_UNVERIFIED = "CHIP_AUTHENTICITY_UNVERIFIED"


class LiveCaptureMethod(StrEnum):
    SERVER_CHALLENGE_LIVE_CAMERA = "SERVER_CHALLENGE_LIVE_CAMERA"


class LiveCaptureSource(StrEnum):
    AUTHORIZED_LIVE_CAMERA_SESSION = "AUTHORIZED_LIVE_CAMERA_SESSION"


class LiveCaptureOutcome(StrEnum):
    COMPLETED = "LIVE_CAPTURE_COMPLETED"


class RegistrationPath(StrEnum):
    HOME_NFC = "HOME_NFC"
    IN_PERSON_OFFICER = "IN_PERSON_OFFICER"


class RegistrationEligibilityState(StrEnum):
    IDENTITY_VERIFICATION_INCOMPLETE = "IDENTITY_VERIFICATION_INCOMPLETE"
    DOCUMENT_REVIEW_REQUIRED = "DOCUMENT_REVIEW_REQUIRED"


_COPY_CHANNELS = frozenset(
    {
        OriginalDocumentChannel.PREVIOUS_CAPTURE,
        OriginalDocumentChannel.PHONE_GALLERY,
        OriginalDocumentChannel.WHATSAPP_IMAGE,
        OriginalDocumentChannel.TELEGRAM_IMAGE,
        OriginalDocumentChannel.EMAIL_ATTACHMENT,
        OriginalDocumentChannel.SCANNED_COPY,
        OriginalDocumentChannel.PHOTOCOPY,
        OriginalDocumentChannel.CERTIFIED_COPY,
        OriginalDocumentChannel.UNCERTIFIED_COPY,
    },
)
_PRINTED_CHANNELS = frozenset({OriginalDocumentChannel.PRINTED_REPLICA})
_SCREENSHOT_CHANNELS = frozenset({OriginalDocumentChannel.SCREENSHOT})
_DIGITAL_IMAGE_CHANNELS = frozenset(
    {
        OriginalDocumentChannel.PDF_DOCUMENT,
        OriginalDocumentChannel.DIGITAL_REPRODUCTION,
    },
)
_OPAQUE_REFERENCE = re.compile(r"^[A-Za-z0-9._:\-/]{1,200}$")
_RAW_NID_RUN = re.compile(r"(?<!\d)\d{9,14}(?!\d)")
_HASH_LIKE_TEXT = re.compile(r"^(?:[0-9a-f]{64}|v[1-9][0-9]{0,2}\.[0-9a-f]{64})$")
_ARABIC_TO_ASCII_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_MIN_CONFIDENCE = 0.80


def classify_originality_channel(
    channel: OriginalDocumentChannel,
) -> RejectionClassification | None:
    """Return the explicit rejection class for a non-original channel."""
    if channel in _COPY_CHANNELS:
        return RejectionClassification.COPY_PRESENTED
    if channel in _PRINTED_CHANNELS:
        return RejectionClassification.PRINTED_REPLICA_PRESENTED
    if channel in _SCREENSHOT_CHANNELS:
        return RejectionClassification.SCREENSHOT_PRESENTED
    if channel in _DIGITAL_IMAGE_CHANNELS:
        return RejectionClassification.DIGITAL_IMAGE_PRESENTED
    if channel is OriginalDocumentChannel.AUTHORIZED_LIVE_CAMERA_SESSION:
        return None
    return RejectionClassification.ORIGINALITY_UNCERTAIN


def normalize_document_numerals(value: str) -> str:
    """Normalize Arabic and Western numerals for field comparison only."""
    return value.translate(_ARABIC_TO_ASCII_DIGITS).strip()


def _assert_safe_text(label: str, value: str | None) -> None:
    if value is None or not value:
        return
    if not _HASH_LIKE_TEXT.fullmatch(value) and _RAW_NID_RUN.search(value):
        raise DocumentAuthenticityError(f"full national ID must not appear in {label}")


def _assert_opaque_reference(label: str, value: str, *, synthetic: bool = True) -> None:
    if _OPAQUE_REFERENCE.fullmatch(value) is None:
        raise DocumentAuthenticityError(f"{label} must be an opaque reference")
    if synthetic and not value.startswith("SYNTHETIC-"):
        raise DocumentAuthenticityError(f"{label} must be synthetic in Wave 05.3")
    _assert_safe_text(label, value)


@dataclass(frozen=True)
class DeviceCapabilityMetadata:
    """Minimal capability flags; no device identifier or fingerprint is collected."""

    nfc_supported: bool = False
    camera_available: bool = True

    def public(self) -> dict[str, bool]:
        return {
            "nfc_supported": self.nfc_supported,
            "camera_available": self.camera_available,
        }


@dataclass(frozen=True)
class LiveCaptureChallenge:
    """Server-issued challenge for one authorized capture session."""

    session_id: str
    nonce: str
    issued_at: datetime
    actor_id: str
    organization_id: str
    facility_id: str
    purpose: str
    correlation_id: str
    device_capabilities: DeviceCapabilityMetadata
    channel: OriginalDocumentChannel = OriginalDocumentChannel.AUTHORIZED_LIVE_CAMERA_SESSION

    def __post_init__(self) -> None:
        if _OPAQUE_REFERENCE.fullmatch(self.session_id) is None:
            raise DocumentAuthenticityError("capture session id must be opaque")
        if not re.fullmatch(r"[A-Fa-f0-9]{32,128}", self.nonce):
            raise DocumentAuthenticityError("capture challenge must be a server nonce")
        if not self.device_capabilities.camera_available:
            raise DocumentAuthenticityError("live capture requires camera capability")
        for label, value in (
            ("actor", self.actor_id),
            ("organization", self.organization_id),
            ("facility", self.facility_id),
            ("purpose", self.purpose),
            ("correlation id", self.correlation_id),
        ):
            if not value or not value.strip():
                raise DocumentAuthenticityError(f"{label} is required for live capture")
            _assert_safe_text(label, value)
        if self.channel is not OriginalDocumentChannel.AUTHORIZED_LIVE_CAMERA_SESSION:
            raise DocumentAuthenticityError("live capture challenge requires an authorized channel")

    @property
    def key(self) -> tuple[str, str]:
        return self.session_id, self.nonce


@dataclass(frozen=True)
class LiveCaptureSession:
    """Completed live capture with opaque evidence references only."""

    challenge: LiveCaptureChallenge
    front_evidence_reference: str
    back_evidence_reference: str
    captured_at: datetime
    capture_method: LiveCaptureMethod = LiveCaptureMethod.SERVER_CHALLENGE_LIVE_CAMERA
    source: LiveCaptureSource = LiveCaptureSource.AUTHORIZED_LIVE_CAMERA_SESSION
    outcome: LiveCaptureOutcome = LiveCaptureOutcome.COMPLETED

    def __post_init__(self) -> None:
        _assert_opaque_reference("front evidence reference", self.front_evidence_reference)
        _assert_opaque_reference("back evidence reference", self.back_evidence_reference)
        if self.front_evidence_reference == self.back_evidence_reference:
            raise DocumentAuthenticityError("front and back evidence references must differ")
        if self.captured_at < self.challenge.issued_at:
            raise DocumentAuthenticityError("capture cannot precede its challenge")
        if self.challenge.channel is not OriginalDocumentChannel.AUTHORIZED_LIVE_CAMERA_SESSION:
            raise DocumentAuthenticityError("live capture channel is not authorized")
        if self.capture_method is not LiveCaptureMethod.SERVER_CHALLENGE_LIVE_CAMERA:
            raise DocumentAuthenticityError("capture method must be an authorized live-camera challenge")
        if self.source is not LiveCaptureSource.AUTHORIZED_LIVE_CAMERA_SESSION:
            raise DocumentAuthenticityError("capture source must be an authorized live-camera session")
        if self.outcome is not LiveCaptureOutcome.COMPLETED:
            raise DocumentAuthenticityError("capture outcome must be a completed live capture")


@dataclass
class CaptureSessionRegistry:
    """In-process anti-replay registry; durable storage remains PROPOSED."""

    _issued: dict[tuple[str, str], LiveCaptureChallenge] = field(default_factory=dict)
    _completed: set[tuple[str, str]] = field(default_factory=set)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def issue(
        self,
        *,
        session_id: str,
        actor_id: str,
        organization_id: str,
        facility_id: str,
        purpose: str,
        correlation_id: str,
        device_capabilities: DeviceCapabilityMetadata,
        at: datetime | None = None,
        nonce: str | None = None,
    ) -> LiveCaptureChallenge:
        challenge = LiveCaptureChallenge(
            session_id=session_id,
            nonce=nonce or secrets.token_hex(16),
            issued_at=at or datetime.now(UTC),
            actor_id=actor_id,
            organization_id=organization_id,
            facility_id=facility_id,
            purpose=purpose,
            correlation_id=correlation_id,
            device_capabilities=device_capabilities,
        )
        with self._lock:
            if any(key[0] == challenge.session_id for key in self._issued):
                raise DocumentAuthenticityError("capture session id has already been issued")
            self._issued[challenge.key] = challenge
        return challenge

    def complete(
        self,
        challenge: LiveCaptureChallenge,
        *,
        front_evidence_reference: str,
        back_evidence_reference: str,
        captured_at: datetime | None = None,
        capture_method: LiveCaptureMethod = LiveCaptureMethod.SERVER_CHALLENGE_LIVE_CAMERA,
        source: LiveCaptureSource = LiveCaptureSource.AUTHORIZED_LIVE_CAMERA_SESSION,
        outcome: LiveCaptureOutcome = LiveCaptureOutcome.COMPLETED,
    ) -> LiveCaptureSession:
        session = LiveCaptureSession(
            challenge=challenge,
            front_evidence_reference=front_evidence_reference,
            back_evidence_reference=back_evidence_reference,
            captured_at=captured_at or datetime.now(UTC),
            capture_method=capture_method,
            source=source,
            outcome=outcome,
        )
        with self._lock:
            if challenge.key not in self._issued:
                raise DocumentAuthenticityError("capture challenge was not issued by this registry")
            if challenge.key in self._completed:
                raise DocumentAuthenticityError("capture challenge replay is rejected")
            self._completed.add(challenge.key)
        return session


@dataclass(frozen=True)
class OriginalCardPresentation:
    """Original physical card presentation record."""

    channel: OriginalDocumentChannel
    actor_id: str
    organization_id: str
    facility_id: str
    purpose: str
    correlation_id: str
    presented_at: datetime
    evidence_reference: str
    physical_presented: bool = True

    def __post_init__(self) -> None:
        classification = classify_originality_channel(self.channel)
        if classification is not None:
            raise DocumentAuthenticityError(
                f"{classification.value}: original-card path is rejected",
            )
        if not self.physical_presented:
            raise DocumentAuthenticityError("original physical card must be presented")
        _assert_opaque_reference("presentation evidence reference", self.evidence_reference)
        for label, value in (
            ("actor", self.actor_id),
            ("organization", self.organization_id),
            ("facility", self.facility_id),
            ("purpose", self.purpose),
            ("correlation id", self.correlation_id),
        ):
            _assert_safe_text(label, value)


@dataclass(frozen=True)
class VisualInspection:
    """Visual security-feature inspection, separate from OCR/MRZ/NFC."""

    inspector_id: str
    organization_id: str
    facility_id: str
    purpose: str
    correlation_id: str
    inspected_at: datetime
    evidence_reference: str
    security_features_observed: tuple[str, ...] = ()
    mismatch: bool = False
    uncertain: bool = False

    def __post_init__(self) -> None:
        _assert_opaque_reference("inspection evidence reference", self.evidence_reference)
        for label, value in (
            ("inspector", self.inspector_id),
            ("organization", self.organization_id),
            ("facility", self.facility_id),
            ("purpose", self.purpose),
            ("correlation id", self.correlation_id),
        ):
            _assert_safe_text(label, value)
        for feature in self.security_features_observed:
            _assert_safe_text("security feature", feature)


@dataclass(frozen=True)
class NfcReadOutcome:
    """NFC read result; chip authenticity is never inferred from a read."""

    state: NfcState
    read_at: datetime
    evidence_reference: str
    chip_authenticity_verified: Literal[False] = False

    def __post_init__(self) -> None:
        if self.chip_authenticity_verified is not False:
            raise DocumentAuthenticityError(
                "chip authenticity requires an officially documented successful procedure",
            )
        _assert_opaque_reference("NFC evidence reference", self.evidence_reference)


@dataclass(frozen=True)
class FieldComparison:
    """Synthetic field-level OCR/MRZ comparison without storing field values."""

    matched_fields: tuple[str, ...]
    conflicting_fields: tuple[str, ...]
    uncertain_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]

    def requires_review(self) -> bool:
        return bool(self.conflicting_fields or self.uncertain_fields or self.missing_fields)


def compare_ocr_and_mrz(
    ocr: ExtractionArtifact,
    mrz: ExtractionArtifact,
) -> FieldComparison:
    """Compare OCR and MRZ artifacts using normalized values only."""
    if ocr.source != SOURCE_CARD_OCR or mrz.source != SOURCE_CARD_NFC:
        raise DocumentAuthenticityError("comparison requires one OCR and one NFC/MRZ artifact")
    if ocr.status is not ExtractionStatus.SUCCESS or mrz.status is not ExtractionStatus.SUCCESS:
        return FieldComparison((), (), ("extraction status is not SUCCESS",), ())
    matched: list[str] = []
    conflicting: list[str] = []
    uncertain: list[str] = []
    missing: list[str] = []
    for field_name in sorted(NATIONAL_CARD_FIELDS):
        left = ocr.fields.get(field_name)
        right = mrz.fields.get(field_name)
        if left is None or right is None or not left.value or not right.value:
            missing.append(field_name)
            continue
        if normalize_document_numerals(left.value) != normalize_document_numerals(right.value):
            conflicting.append(field_name)
            continue
        confidences = [ocr.confidence, mrz.confidence, left.confidence, right.confidence]
        if any(value is not None and value < _MIN_CONFIDENCE for value in confidences):
            uncertain.append(field_name)
            continue
        matched.append(field_name)
    return FieldComparison(
        matched_fields=tuple(matched),
        conflicting_fields=tuple(conflicting),
        uncertain_fields=tuple(uncertain),
        missing_fields=tuple(missing),
    )


@dataclass(frozen=True)
class NidpEvidenceBundle:
    """Synthetic evidence bundle with no image bytes or raw NFC payload.

    This is a boundary container, not a replacement for the canonical
    ``identity_governance.DocumentAuthenticityEvidence`` record. That canonical
    record requires an approved document authority, which does not exist in this
    wave, so it is deliberately not instantiated here.
    """

    path: RegistrationPath
    presentation: OriginalCardPresentation
    capture: LiveCaptureSession
    visual_inspection: VisualInspection
    ocr: ExtractionArtifact | None = None
    mrz: ExtractionArtifact | None = None
    nfc: NfcReadOutcome | None = None
    comparison: FieldComparison | None = None
    rejection: RejectionClassification | None = None
    expired: bool = False
    suspected_forgery: bool = False
    official_nfc_reading_documented: bool = False
    authenticity_checks_completed: bool = False
    authorized_officer_reviewed: bool = False
    central_workflow_recorded: bool = False

    def __post_init__(self) -> None:
        if self.comparison is None and self.ocr is not None and self.mrz is not None:
            raise DocumentAuthenticityError("OCR/MRZ comparison is required when both artifacts exist")
        correlation_ids = {
            self.presentation.correlation_id,
            self.capture.challenge.correlation_id,
            self.visual_inspection.correlation_id,
        }
        if len(correlation_ids) != 1:
            raise DocumentAuthenticityError("presentation, capture, and inspection must share one correlation id")


@dataclass(frozen=True)
class DocumentAuthenticityDecision:
    """Review-safe authenticity decision; confirmed states are unavailable."""

    state: DocumentAuthenticityState
    canonical_event: str
    canonical_state: str
    reasons: tuple[str, ...]
    rejection: RejectionClassification | None = None
    verified: Literal[False] = False

    def __post_init__(self) -> None:
        if self.verified is not False:
            raise DocumentAuthenticityError("authenticity decision must never be verified")
        if self.state in {
            DocumentAuthenticityState.CHIP_AUTHENTICITY_VERIFIED,
            DocumentAuthenticityState.DOCUMENT_AUTHENTICITY_CONFIRMED,
        }:
            raise DocumentAuthenticityError(
                "authenticity confirmation requires an approved official procedure",
            )
        if self.canonical_state not in VERIFICATION_STATES:
            raise DocumentAuthenticityError("canonical state is unknown")
        if self.canonical_state == VERIFIED:
            raise DocumentAuthenticityError("authenticity must never produce VERIFIED")


@dataclass(frozen=True)
class AuthenticityTransitionResult:
    state: str
    events: tuple[str, ...]


def _route_to_pending_review(
    current_state: str,
    *,
    reason: str,
    evidence_reference: str,
    reviewer: str,
) -> AuthenticityTransitionResult:
    if current_state not in VERIFICATION_STATES:
        raise DocumentAuthenticityError("unknown current verification state")
    context = VerificationTransitionContext(
        reviewer=reviewer,
        source="SYNTHETIC_NIDP",
        reason=reason,
        evidence_reference=evidence_reference,
    )
    events: list[str] = []
    state = current_state
    if state == PENDING_REVIEW:
        return AuthenticityTransitionResult(state, ())
    if state == UNVERIFIED:
        state = transition_verification_state(
            state,
            EXTRACTION_COMPLETED,
            context=VerificationTransitionContext(source="SYNTHETIC_NIDP"),
        )
        events.append(EXTRACTION_COMPLETED)
    if state in {DATA_EXTRACTED, DOCUMENT_CHECKED, GOVERNMENT_VERIFIED}:
        state = transition_verification_state(state, REVIEW_REQUIRED, context=context)
        events.append(REVIEW_REQUIRED)
    elif state == SUSPENDED:
        state = transition_verification_state(state, INVESTIGATION_AUTHORIZED, context=context)
        events.append(INVESTIGATION_AUTHORIZED)
    elif state in {EXPIRED, REJECTED}:
        state = transition_verification_state(state, NEW_EVIDENCE_SUBMITTED, context=context)
        events.append(NEW_EVIDENCE_SUBMITTED)
    elif state == VERIFIED:
        state = transition_verification_state(state, CARD_EXPIRED, context=context)
        events.append(CARD_EXPIRED)
        state = transition_verification_state(state, NEW_EVIDENCE_SUBMITTED, context=context)
        events.append(NEW_EVIDENCE_SUBMITTED)
    if state == VERIFIED:
        raise DocumentAuthenticityError("NIDP must never produce VERIFIED")
    return AuthenticityTransitionResult(state, tuple(events))


def evaluate_document_authenticity(
    evidence: NidpEvidenceBundle,
) -> DocumentAuthenticityDecision:
    """Evaluate original-card evidence and always route to human review."""
    reasons: list[str] = []
    rejection = evidence.rejection

    if rejection is not None:
        reasons.append(f"explicit rejection: {rejection.value}")
        reasons.append("original-card path rejected")
    if evidence.suspected_forgery:
        rejection = rejection or RejectionClassification.ORIGINALITY_UNCERTAIN
        reasons.append("suspected forgery requires human review")
    if evidence.visual_inspection.mismatch:
        rejection = rejection or RejectionClassification.SECURITY_FEATURE_MISMATCH
        reasons.append("security feature mismatch requires human review")
    if evidence.visual_inspection.uncertain:
        rejection = rejection or RejectionClassification.ORIGINALITY_UNCERTAIN
        reasons.append("uncertain originality requires human review")
    if evidence.expired:
        reasons.append("expired document requires human review")
    if evidence.comparison is not None and evidence.comparison.requires_review():
        reasons.append("OCR/MRZ comparison requires human review")
    if evidence.path is RegistrationPath.HOME_NFC:
        if not evidence.capture.challenge.device_capabilities.nfc_supported:
            reasons.append("home NFC requires an NFC-capable device")
        if not evidence.official_nfc_reading_documented:
            reasons.append("home NFC requires an officially documented direct reading procedure")
        if evidence.nfc is None:
            reasons.append("NFC result is absent")
        elif evidence.nfc.state is not NfcState.NFC_READ_SUCCESSFULLY:
            reasons.append(f"NFC state is {evidence.nfc.state.value}")
        else:
            reasons.append("NFC read alone does not establish chip authenticity")
        if not evidence.authenticity_checks_completed:
            reasons.append("home NFC requires completed authenticity checks")
    elif evidence.path is RegistrationPath.IN_PERSON_OFFICER:
        if not evidence.authorized_officer_reviewed:
            reasons.append("in-person path requires authorized officer inspection")
        if not evidence.central_workflow_recorded:
            reasons.append("in-person outcome requires approved central workflow recording")
        if not evidence.authenticity_checks_completed:
            reasons.append("in-person path requires completed authenticity checks")
    if not reasons:
        reasons.append("no approved official authenticity procedure is active")

    return DocumentAuthenticityDecision(
        state=DocumentAuthenticityState.DOCUMENT_REVIEW_REQUIRED,
        canonical_event=REVIEW_REQUIRED,
        canonical_state=PENDING_REVIEW,
        reasons=tuple(reasons),
        rejection=rejection,
    )


def apply_authenticity_transition(
    decision: DocumentAuthenticityDecision,
    *,
    current_state: str = UNVERIFIED,
    reviewer: str = "SYNTHETIC-DOCUMENT-REVIEW",
) -> AuthenticityTransitionResult:
    """Apply only evaluator-produced review decisions to the canonical state machine."""
    if decision.state in {
        DocumentAuthenticityState.CHIP_AUTHENTICITY_VERIFIED,
        DocumentAuthenticityState.DOCUMENT_AUTHENTICITY_CONFIRMED,
        DocumentAuthenticityState.DOCUMENT_AUTHENTICITY_FAILED,
    }:
        raise DocumentAuthenticityError("this authenticity state is not activatable in Wave 05.3")
    if decision.canonical_event != REVIEW_REQUIRED:
        raise DocumentAuthenticityError("only review routing is permitted in Wave 05.3")
    return _route_to_pending_review(
        current_state,
        reason="; ".join(decision.reasons) or "document authenticity requires review",
        evidence_reference="SYNTHETIC-DOCUMENT-REVIEW",
        reviewer=reviewer,
    )


def assert_no_manual_authenticity_override(target_state: str) -> None:
    """Reject direct attempts to set a protected document or identity state."""
    protected = {
        VERIFIED,
        DocumentAuthenticityState.CHIP_AUTHENTICITY_VERIFIED.value,
        DocumentAuthenticityState.DOCUMENT_AUTHENTICITY_CONFIRMED.value,
    }
    if target_state in protected:
        raise DocumentAuthenticityError("manual authenticity override is prohibited")


@dataclass(frozen=True)
class RegistrationEligibility:
    state: RegistrationEligibilityState
    identity_verified: Literal[False] = False
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.identity_verified is not False:
            raise DocumentAuthenticityError("initial registration cannot grant verified identity")


def registration_eligibility(
    evidence: NidpEvidenceBundle,
    decision: DocumentAuthenticityDecision,
) -> RegistrationEligibility:
    """Return incomplete registration eligibility; no path grants VERIFIED."""
    reasons = list(decision.reasons)
    if evidence.path is RegistrationPath.HOME_NFC:
        reasons.append("home NFC registration requires approved official NFC specifications")
        state = RegistrationEligibilityState.DOCUMENT_REVIEW_REQUIRED
    else:
        reasons.append("in-person registration requires officer inspection and central recording")
        reasons.append("no-NFC path creates only an initial incomplete account")
        state = RegistrationEligibilityState.IDENTITY_VERIFICATION_INCOMPLETE
    return RegistrationEligibility(state=state, reasons=tuple(reasons))


def assert_identity_verification_blocked(
    decision: DocumentAuthenticityDecision,
    *,
    synthetic_government_verified: bool = False,
) -> None:
    """Prevent synthetic verification from activating a citizen identity."""
    if synthetic_government_verified:
        raise DocumentAuthenticityError("synthetic government verification cannot activate identity")
    if decision.state is not DocumentAuthenticityState.DOCUMENT_AUTHENTICITY_CONFIRMED:
        raise DocumentAuthenticityError("identity verification remains incomplete")
    raise DocumentAuthenticityError("identity activation requires separate approval")


def authorize_nidp_operation(context: IdentityAccessContext) -> IdentityAccessGrant:
    """Authorize an NIDP operation through the canonical Decision Engine boundary."""
    return assert_identity_access_v2(context)


def nidp_audit_event(
    *,
    operation: str,
    actor_id: str,
    purpose: str,
    organization_id: str,
    facility_id: str,
    gula_citizen_identifier: str,
    national_id_hash: str,
    correlation_id: str,
    evidence_reference: str,
    capture: LiveCaptureSession | None = None,
    decision: DocumentAuthenticityDecision | None = None,
    reason_code: str | None = None,
) -> object:
    """Build a canonical audit event without raw identity data."""
    metadata: dict[str, Any] = {
        "evidence_reference": evidence_reference,
        "nidp_boundary": "SYNTHETIC",
    }
    if capture is not None:
        metadata.update(
            {
                "capture_session_id": capture.challenge.session_id,
                "capture_method": capture.capture_method.value,
                "capture_source": capture.source.value,
                "capture_outcome": capture.outcome.value,
                "captured_at": capture.captured_at.isoformat(),
                "challenge_issued_at": capture.challenge.issued_at.isoformat(),
                "device_capabilities": capture.challenge.device_capabilities.public(),
                "front_evidence_reference": capture.front_evidence_reference,
                "back_evidence_reference": capture.back_evidence_reference,
                "channel": capture.challenge.channel.value,
            },
        )
    if decision is not None:
        metadata.update(
            {
                "document_authenticity_state": decision.state.value,
                "canonical_event": decision.canonical_event,
                "canonical_state": decision.canonical_state,
                "rejection": decision.rejection.value if decision.rejection else None,
                "reasons": decision.reasons,
            },
        )
    return build_wave053_audit_event(
        operation=operation,
        actor_id=actor_id,
        purpose=purpose,
        facility_id=facility_id,
        organization_id=organization_id,
        gula_citizen_identifier=gula_citizen_identifier,
        national_id_hash=national_id_hash,
        metadata=metadata,
        decision="success",
        reason_code=reason_code,
        correlation_id=correlation_id,
        raw_nid_values=(evidence_reference, reason_code),
    )


OPERATION_BY_STATE: Mapping[DocumentAuthenticityState, str] = {
    DocumentAuthenticityState.ORIGINAL_CARD_PRESENTED: ORIGINAL_CARD_PRESENTED,
    DocumentAuthenticityState.LIVE_CAPTURE_COMPLETED: LIVE_CAPTURE_COMPLETED,
    DocumentAuthenticityState.VISUAL_INSPECTION_COMPLETED: AUTHENTICITY_INSPECTION,
    DocumentAuthenticityState.MRZ_READ_SUCCESSFULLY: MRZ_EXTRACTION,
    DocumentAuthenticityState.NFC_READ_SUCCESSFULLY: NFC_EXTRACTION,
    DocumentAuthenticityState.DOCUMENT_AUTHENTICITY_FAILED: AUTHENTICITY_FAILURE,
    DocumentAuthenticityState.DOCUMENT_REVIEW_REQUIRED: DOCUMENT_REVIEW,
}

__all__ = [
    "AUTHENTICITY_FAILURE",
    "AUTHENTICITY_INSPECTION",
    "COPY_REJECTION",
    "DOCUMENT_REVIEW",
    "LIVE_CAPTURE_COMPLETED",
    "LIVE_CAPTURE_STARTED",
    "MANUAL_OVERRIDE_ATTEMPT",
    "MRZ_EXTRACTION",
    "NFC_EXTRACTION",
    "OPERATION_BY_STATE",
    "ORIGINAL_CARD_PRESENTED",
    "REVIEW_OUTCOME",
    "SUSPICIOUS_DOCUMENT",
    "UNAUTHORIZED_VERIFICATION_ATTEMPT",
    "AuthenticityTransitionResult",
    "CaptureSessionRegistry",
    "DeviceCapabilityMetadata",
    "DocumentAuthenticityDecision",
    "DocumentAuthenticityError",
    "DocumentAuthenticityState",
    "FieldComparison",
    "LiveCaptureChallenge",
    "LiveCaptureMethod",
    "LiveCaptureOutcome",
    "LiveCaptureSession",
    "LiveCaptureSource",
    "NfcReadOutcome",
    "NfcState",
    "NidpEvidenceBundle",
    "OriginalCardPresentation",
    "OriginalDocumentChannel",
    "RegistrationEligibility",
    "RegistrationEligibilityState",
    "RegistrationPath",
    "RejectionClassification",
    "VisualInspection",
    "apply_authenticity_transition",
    "assert_identity_verification_blocked",
    "assert_no_manual_authenticity_override",
    "authorize_nidp_operation",
    "classify_originality_channel",
    "compare_ocr_and_mrz",
    "evaluate_document_authenticity",
    "nidp_audit_event",
    "normalize_document_numerals",
    "registration_eligibility",
]
