"""Wave 05.3 OCR/NFC interface and reconciliation contracts.

This module defines provider interfaces only. It does not define card layout,
APDUs, chip keys, certificates, protocols, reader hardware behavior, or
authenticity success. Synthetic providers accept opaque references, never raw
card images or raw NFC payloads.

The canonical Wave 05.2 extraction comparator and verification state machine
are reused. Extraction never grants ``VERIFIED``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol

from app._compat import UTC
from app.national.services.identity_access import (
    NFC_EXTRACTION,
    OCR_EXTRACTION,
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
    SOURCE_CARD_NFC,
    SOURCE_CARD_OCR,
    SUSPENDED,
    UNVERIFIED,
    VERIFICATION_STATES,
    VERIFIED,
    ExtractedField,
    ExtractionComparison,
    NationalIdEvidence,
    VerificationTransitionContext,
    assert_no_full_national_identifier,
    build_national_id_evidence,
    card_validity_event,
    classify_card_extraction,
    transition_verification_state,
)


class ExtractionStatus(StrEnum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    UNREADABLE = "UNREADABLE"
    UNSUPPORTED_CHIP = "UNSUPPORTED_CHIP"
    READ_FAILURE = "READ_FAILURE"
    INVALID_CONFIDENCE = "INVALID_CONFIDENCE"


_OPAQUE_REFERENCE = re.compile(r"^[A-Za-z0-9._:\-/]{1,200}$")
_ALLOWED_MIME = frozenset({"image/jpeg", "image/png", "image/webp"})


class ExtractionContractError(ValueError):
    """Base error for OCR/NFC contract violations."""


@dataclass(frozen=True)
class OcrDocumentReference:
    """Opaque document pointer. Raw image bytes are intentionally excluded."""

    document_reference: str
    mime_type: str = "image/jpeg"
    synthetic: bool = True

    def __post_init__(self) -> None:
        if _OPAQUE_REFERENCE.fullmatch(self.document_reference) is None:
            raise ExtractionContractError("document reference must be opaque")
        if self.mime_type not in _ALLOWED_MIME:
            raise ExtractionContractError("unsupported document mime type")
        if not self.synthetic:
            raise ExtractionContractError("only synthetic document references are allowed in Wave 05.3")


@dataclass(frozen=True)
class NfcCardReference:
    """Opaque card pointer. No APDU, chip layout, key, or raw payload is defined."""

    reader_reference: str
    card_reference: str
    synthetic: bool = True

    def __post_init__(self) -> None:
        if _OPAQUE_REFERENCE.fullmatch(self.reader_reference) is None:
            raise ExtractionContractError("reader reference must be opaque")
        if _OPAQUE_REFERENCE.fullmatch(self.card_reference) is None:
            raise ExtractionContractError("card reference must be opaque")
        if not self.synthetic:
            raise ExtractionContractError("only synthetic card references are allowed in Wave 05.3")


@dataclass(frozen=True)
class ExtractionArtifact:
    """Non-retaining extraction output; no image or raw NFC payload field exists."""

    source: str
    status: ExtractionStatus
    fields: Mapping[str, ExtractedField]
    captured_at: datetime
    confidence: float | None = None
    card_expiry_date: date | datetime | str | None = None
    quality_issue: str | None = None
    evidence_reference: str | None = None
    synthetic: bool = True

    def __post_init__(self) -> None:
        if self.source not in {SOURCE_CARD_OCR, SOURCE_CARD_NFC}:
            raise ExtractionContractError("unknown extraction source")
        if not self.synthetic:
            raise ExtractionContractError("only synthetic extraction artifacts are allowed in Wave 05.3")
        unknown = set(self.fields) - set(NATIONAL_CARD_FIELDS)
        if unknown:
            raise ExtractionContractError("extraction artifact contains unsupported field names")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ExtractionContractError("artifact confidence must be between 0 and 1")
        for name, field in self.fields.items():
            if field.confidence is not None and not 0.0 <= field.confidence <= 1.0:
                raise ExtractionContractError(f"field {name} confidence must be between 0 and 1")


class OCRProvider(Protocol):
    """Future OCR provider interface. No external provider is configured."""

    def extract(self, reference: OcrDocumentReference) -> ExtractionArtifact: ...


class NFCReaderAdapter(Protocol):
    """Future NFC reader interface. No chip protocol or key material is defined."""

    def read(self, reference: NfcCardReference) -> ExtractionArtifact: ...


class SyntheticOCRProvider:
    """Synthetic OCR provider for contract tests only."""

    def __init__(
        self,
        *,
        fields: Mapping[str, ExtractedField | str | None],
        status: ExtractionStatus = ExtractionStatus.SUCCESS,
        confidence: float | None = 0.95,
        card_expiry_date: date | datetime | str | None = None,
        quality_issue: str | None = None,
    ) -> None:
        self.fields = fields
        self.status = status
        self.confidence = confidence
        self.card_expiry_date = card_expiry_date
        self.quality_issue = quality_issue

    def extract(
        self,
        reference: OcrDocumentReference,
        *,
        captured_at: datetime | None = None,
    ) -> ExtractionArtifact:
        prepared: dict[str, ExtractedField] = {}
        for name, value in self.fields.items():
            if name not in NATIONAL_CARD_FIELDS:
                raise ExtractionContractError("OCR fixture contains unsupported field names")
            if isinstance(value, ExtractedField):
                prepared[name] = value
            elif value is not None:
                prepared[name] = ExtractedField(str(value), SOURCE_CARD_OCR, self.confidence)
        return ExtractionArtifact(
            source=SOURCE_CARD_OCR,
            status=self.status,
            fields=prepared,
            captured_at=captured_at or datetime.now(UTC),
            confidence=self.confidence,
            card_expiry_date=self.card_expiry_date,
            quality_issue=self.quality_issue,
            evidence_reference=f"SYNTHETIC-OCR-{reference.document_reference}",
            synthetic=True,
        )


class SyntheticNFCReaderAdapter:
    """Synthetic NFC reader for contract tests only."""

    def __init__(
        self,
        *,
        fields: Mapping[str, ExtractedField | str | None],
        status: ExtractionStatus = ExtractionStatus.SUCCESS,
        confidence: float | None = 1.0,
        card_expiry_date: date | datetime | str | None = None,
        quality_issue: str | None = None,
    ) -> None:
        self.fields = fields
        self.status = status
        self.confidence = confidence
        self.card_expiry_date = card_expiry_date
        self.quality_issue = quality_issue

    def read(
        self,
        reference: NfcCardReference,
        *,
        captured_at: datetime | None = None,
    ) -> ExtractionArtifact:
        prepared: dict[str, ExtractedField] = {}
        for name, value in self.fields.items():
            if name not in NATIONAL_CARD_FIELDS:
                raise ExtractionContractError("NFC fixture contains unsupported field names")
            if isinstance(value, ExtractedField):
                prepared[name] = value
            elif value is not None:
                prepared[name] = ExtractedField(str(value), SOURCE_CARD_NFC, self.confidence)
        return ExtractionArtifact(
            source=SOURCE_CARD_NFC,
            status=self.status,
            fields=prepared,
            captured_at=captured_at or datetime.now(UTC),
            confidence=self.confidence,
            card_expiry_date=self.card_expiry_date,
            quality_issue=self.quality_issue,
            evidence_reference=f"SYNTHETIC-NFC-{reference.card_reference}",
            synthetic=True,
        )


@dataclass(frozen=True)
class ExtractionOutcome:
    """A review-safe result of OCR/NFC reconciliation."""

    recommended_state: str
    events: tuple[str, ...]
    reasons: tuple[str, ...]
    comparison: ExtractionComparison
    protected_national_id: NationalIdEvidence | None
    verified: bool = False

    def __post_init__(self) -> None:
        if self.recommended_state not in VERIFICATION_STATES:
            raise ExtractionContractError("unknown recommended verification state")
        if self.verified:
            raise ExtractionContractError("extraction outcome must never be verified")


def protected_national_id_evidence(artifact: ExtractionArtifact) -> NationalIdEvidence | None:
    """Convert a boundary raw field to hash/masked evidence only."""
    field = artifact.fields.get("national_id")
    if field is None or not field.value:
        return None
    return build_national_id_evidence(
        field.value,
        source=artifact.source,
        captured_at=field.extracted_at or artifact.captured_at,
        confidence=field.confidence,
    )


def _confidence_reasons(artifact: ExtractionArtifact) -> list[str]:
    reasons: list[str] = []
    values = [artifact.confidence] if artifact.confidence is not None else []
    values.extend(field.confidence for field in artifact.fields.values())
    for value in values:
        if value is not None and not 0.0 <= value <= 1.0:
            reasons.append(f"{artifact.source} confidence is outside 0..1")
            break
    return reasons


def _expiry_reason(ocr: ExtractionArtifact, nfc: ExtractionArtifact, *, now: datetime) -> str | None:
    candidates = [ocr.card_expiry_date, nfc.card_expiry_date]
    for field_name in ("card_expiry_date",):
        for artifact in (ocr, nfc):
            field = artifact.fields.get(field_name)
            if field is not None and field.value:
                candidates.append(field.value)
    for candidate in candidates:
        if candidate is None:
            continue
        if card_validity_event(candidate, now=now) == CARD_EXPIRED:
            return "card expiry date has passed"
    return None


def _transition_to_pending_review(
    current_state: str,
    *,
    reason: str,
    evidence_reference: str,
    reviewer: str | None = None,
) -> tuple[str, tuple[str, ...]]:
    """Route to PENDING_REVIEW using only canonical state-machine transitions.

    Extraction is never an authority to verify identity. A previously verified
    record is first expired through the canonical CARD_EXPIRED event and then
    reopened for review through NEW_EVIDENCE_SUBMITTED. No transition table or
    state definition is modified here.
    """
    if current_state not in VERIFICATION_STATES:
        raise ExtractionContractError("unknown current verification state")
    context = VerificationTransitionContext(
        reviewer=reviewer or "SYNTHETIC-EXTRACTION-REVIEW",
        source=SOURCE_CARD_OCR,
        reason=reason,
        evidence_reference=evidence_reference,
    )
    events: list[str] = []
    state = current_state

    if state == PENDING_REVIEW:
        return state, ()
    if state == UNVERIFIED:
        state = transition_verification_state(
            state,
            EXTRACTION_COMPLETED,
            context=VerificationTransitionContext(source=SOURCE_CARD_OCR),
        )
        events.append(EXTRACTION_COMPLETED)
    if state in {DATA_EXTRACTED, DOCUMENT_CHECKED, GOVERNMENT_VERIFIED}:
        state = transition_verification_state(state, REVIEW_REQUIRED, context=context)
        events.append(REVIEW_REQUIRED)
        return state, tuple(events)
    if state == SUSPENDED:
        state = transition_verification_state(state, INVESTIGATION_AUTHORIZED, context=context)
        events.append(INVESTIGATION_AUTHORIZED)
        return state, tuple(events)
    if state in {EXPIRED, REJECTED}:
        state = transition_verification_state(state, NEW_EVIDENCE_SUBMITTED, context=context)
        events.append(NEW_EVIDENCE_SUBMITTED)
        return state, tuple(events)
    if state == VERIFIED:
        state = transition_verification_state(state, CARD_EXPIRED, context=context)
        events.append(CARD_EXPIRED)
        state = transition_verification_state(state, NEW_EVIDENCE_SUBMITTED, context=context)
        events.append(NEW_EVIDENCE_SUBMITTED)
        return state, tuple(events)
    raise ExtractionContractError(f"cannot route {state} to pending review")


def reconcile_document_extraction(
    ocr: ExtractionArtifact,
    nfc: ExtractionArtifact,
    *,
    current_state: str = UNVERIFIED,
    now: datetime | None = None,
    reviewer: str | None = None,
    raw_nid_for_check: str | None = None,
) -> ExtractionOutcome:
    """Reconcile synthetic OCR/NFC output without granting identity verification."""
    timestamp = now or datetime.now(UTC)
    reasons: list[str] = []

    if ocr.status is not ExtractionStatus.SUCCESS:
        reasons.append(f"OCR status is {ocr.status.value}")
    if nfc.status is not ExtractionStatus.SUCCESS:
        reasons.append(f"NFC status is {nfc.status.value}")
    if ocr.quality_issue:
        reasons.append(f"OCR quality issue: {ocr.quality_issue}")
    if nfc.quality_issue:
        reasons.append(f"NFC quality issue: {nfc.quality_issue}")
    reasons.extend(_confidence_reasons(ocr))
    reasons.extend(_confidence_reasons(nfc))

    expiry_reason = _expiry_reason(ocr, nfc, now=timestamp)
    if expiry_reason is not None:
        state, events = _transition_to_pending_review(
            current_state,
            reason=expiry_reason,
            evidence_reference=ocr.evidence_reference or nfc.evidence_reference or "SYNTHETIC-EVIDENCE",
            reviewer=reviewer,
        )
        outcome = ExtractionOutcome(
            recommended_state=state,
            events=events,
            reasons=(*reasons, expiry_reason),
            comparison=classify_card_extraction(ocr.fields, nfc.fields),
            protected_national_id=protected_national_id_evidence(ocr),
            verified=False,
        )
        assert_no_full_national_identifier(repr(outcome), raw_nid_for_check)
        return outcome

    comparison = classify_card_extraction(ocr.fields, nfc.fields)
    for conflict in comparison.conflicts:
        reasons.append(f"conflicting field: {conflict.field}")
    for uncertain in comparison.uncertain_fields:
        reasons.append(f"uncertain field: {uncertain.field}")
    for missing in comparison.missing_fields:
        reasons.append(f"missing field: {missing.field}")

    if reasons or comparison.recommended_event != EXTRACTION_COMPLETED:
        if not reasons:
            reasons.append("extraction requires human review")
        review_reason = "; ".join(reasons)
    else:
        review_reason = "synthetic OCR/NFC fields agree but require human review"
    state, events = _transition_to_pending_review(
        current_state,
        reason=review_reason,
        evidence_reference=ocr.evidence_reference or nfc.evidence_reference or "SYNTHETIC-EVIDENCE",
        reviewer=reviewer,
    )

    if state == VERIFIED:
        raise ExtractionContractError("extraction must never produce VERIFIED")
    outcome = ExtractionOutcome(
        recommended_state=state,
        events=events,
        reasons=tuple(reasons),
        comparison=comparison,
        protected_national_id=protected_national_id_evidence(ocr),
        verified=False,
    )
    assert_no_full_national_identifier(repr(outcome), raw_nid_for_check)
    return outcome


def extraction_audit_event(
    artifact: ExtractionArtifact,
    *,
    actor: str,
    purpose: str,
    organization_id: str,
    facility_id: str,
    gula_citizen_identifier: str,
    national_id_hash: str,
    correlation_id: str | None = None,
    raw_nid_for_check: str | None = None,
) -> object:
    """Create a canonical audit event for OCR or NFC extraction."""
    operation = OCR_EXTRACTION if artifact.source == SOURCE_CARD_OCR else NFC_EXTRACTION
    return build_wave053_audit_event(
        operation=operation,
        actor_id=actor,
        purpose=purpose,
        facility_id=facility_id,
        organization_id=organization_id,
        gula_citizen_identifier=gula_citizen_identifier,
        national_id_hash=national_id_hash,
        metadata={
            "status": artifact.status.value,
            "synthetic": artifact.synthetic,
            "evidence_reference": artifact.evidence_reference,
            "quality_issue": artifact.quality_issue,
            "field_names": tuple(sorted(artifact.fields)),
        },
        correlation_id=correlation_id,
        raw_nid_for_check=raw_nid_for_check,
    )


__all__ = [
    "DATA_EXTRACTED",
    "EXPIRED",
    "PENDING_REVIEW",
    "ExtractionArtifact",
    "ExtractionContractError",
    "ExtractionOutcome",
    "ExtractionStatus",
    "NFCReaderAdapter",
    "NfcCardReference",
    "OCRProvider",
    "OcrDocumentReference",
    "SyntheticNFCReaderAdapter",
    "SyntheticOCRProvider",
    "extraction_audit_event",
    "protected_national_id_evidence",
    "reconcile_document_extraction",
]
