"""Versioned synthetic OCR pipeline sequencing.

This module does not read images, contact an OCR service, retain card bytes, or
assert document authenticity. It sequences the existing canonical extraction
contracts into explicit stages and records only opaque references, stage
statuses, field names, and confidences. Every anomaly is routed to human review
through ``reconcile_document_extraction``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from app._compat import UTC
from app.national.services.document_extraction import (
    ExtractionArtifact,
    ExtractionOutcome,
    NfcCardReference,
    OcrDocumentReference,
    SyntheticNFCReaderAdapter,
    SyntheticOCRProvider,
    extraction_audit_event,
    reconcile_document_extraction,
)
from app.national.services.identity_governance import (
    NATIONAL_CARD_FIELDS,
    VERIFIED,
    ExtractedField,
)

PIPELINE_VERSION = "phase1-synthetic-ocr-v1"

STAGE_VERSIONS: Mapping[str, str] = {
    "image_quality": "1.0.0",
    "document_classification": "1.0.0",
    "boundary_perspective": "1.0.0",
    "preprocessing": "1.0.0",
    "field_ocr": "1.0.0",
    "mrz_read": "1.0.0",
    "normalization": "1.0.0",
    "cross_field_checks": "1.0.0",
    "duplicate_anomaly": "1.0.0",
    "human_review": "1.0.0",
    "retention_deletion_hooks": "1.0.0",
}

STAGE_ORDER: tuple[str, ...] = tuple(STAGE_VERSIONS)

_MIN_CONFIDENCE = 0.80


class OcrPipelineError(ValueError):
    """Raised for malformed synthetic pipeline input."""


class StageStatus(StrEnum):
    COMPLETED = "COMPLETED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class OcrStageResult:
    stage: str
    version: str
    status: StageStatus
    confidence: float | None
    reasons: tuple[str, ...]
    evidence_reference: str | None = None

    def __post_init__(self) -> None:
        if self.stage not in STAGE_VERSIONS:
            raise OcrPipelineError("unknown OCR pipeline stage")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise OcrPipelineError("stage confidence must be between 0 and 1")


@dataclass(frozen=True)
class SyntheticOcrInput:
    document: OcrDocumentReference
    card: NfcCardReference
    ocr_fields: Mapping[str, ExtractedField | str | None]
    nfc_fields: Mapping[str, ExtractedField | str | None]
    language: Literal["ar", "en"] = "ar"
    quality_confidence: float = 0.95
    classification: str = "national_identity_card"
    perspective_valid: bool = True
    preprocessing_valid: bool = True
    duplicate_indicator: bool = False
    anomaly_indicator: bool = False
    retention_hook: str = "synthetic_retention_hook"
    deletion_hook: str = "synthetic_deletion_hook"

    def __post_init__(self) -> None:
        if self.language not in {"ar", "en"}:
            raise OcrPipelineError("only Arabic and English synthetic inputs are supported")
        if not 0.0 <= self.quality_confidence <= 1.0:
            raise OcrPipelineError("quality confidence must be between 0 and 1")
        for fields, label in ((self.ocr_fields, "OCR"), (self.nfc_fields, "NFC")):
            unknown = set(fields) - set(NATIONAL_CARD_FIELDS)
            if unknown:
                raise OcrPipelineError(f"{label} fixture contains unsupported field names")
        for hook in (self.retention_hook, self.deletion_hook):
            if not hook or not hook.strip() or "/" in hook:
                raise OcrPipelineError("retention and deletion hooks must be opaque labels")


@dataclass(frozen=True)
class SyntheticOcrPipelineResult:
    pipeline_version: str
    stages: tuple[OcrStageResult, ...]
    outcome: ExtractionOutcome
    extracted_field_names: tuple[str, ...]
    field_confidences: Mapping[str, float | None]
    audit_events: tuple[Any, ...]
    retention_hook: str
    deletion_hook: str

    @property
    def review_required(self) -> bool:
        return any(stage.status is StageStatus.REVIEW_REQUIRED for stage in self.stages)

    def to_public_dict(self) -> dict[str, Any]:
        """Return a summary that never contains OCR values or national numbers."""
        return {
            "pipeline_version": self.pipeline_version,
            "recommended_state": self.outcome.recommended_state,
            "verified": self.outcome.verified,
            "review_required": self.review_required,
            "extracted_field_names": sorted(self.extracted_field_names),
            "reasons": self.outcome.reasons,
        }


class SyntheticOcrPipeline:
    """Synthetic stage sequencer; all decisions remain review-only."""

    def run(
        self,
        data: SyntheticOcrInput,
        *,
        now: datetime | None = None,
        actor_id: str,
        purpose: str,
        organization_id: str,
        facility_id: str,
        gula_citizen_identifier: str,
        national_id_hash: str,
        correlation_id: str | None = None,
        raw_nid_for_check: str | None = None,
    ) -> SyntheticOcrPipelineResult:
        timestamp = now or datetime.now(UTC)
        stages: list[OcrStageResult] = []

        def stage(name: str, status: StageStatus, reason: str = "", *, confidence: float | None = None,
                  evidence_reference: str | None = None) -> None:
            stages.append(
                OcrStageResult(
                    stage=name,
                    version=STAGE_VERSIONS[name],
                    status=status,
                    confidence=confidence,
                    reasons=(reason,) if reason else (),
                    evidence_reference=evidence_reference,
                ),
            )

        quality_status = (
            StageStatus.COMPLETED
            if data.quality_confidence >= _MIN_CONFIDENCE
            else StageStatus.REVIEW_REQUIRED
        )
        stage(
            "image_quality",
            quality_status,
            "" if quality_status is StageStatus.COMPLETED else "image quality is below threshold",
            confidence=data.quality_confidence,
        )

        classification_status = (
            StageStatus.COMPLETED
            if data.classification == "national_identity_card"
            else StageStatus.REVIEW_REQUIRED
        )
        stage(
            "document_classification",
            classification_status,
            "" if classification_status is StageStatus.COMPLETED else "unsupported document class",
        )

        stage(
            "boundary_perspective",
            StageStatus.COMPLETED if data.perspective_valid else StageStatus.REVIEW_REQUIRED,
            "" if data.perspective_valid else "boundary or perspective check failed",
        )
        stage(
            "preprocessing",
            StageStatus.COMPLETED if data.preprocessing_valid else StageStatus.REVIEW_REQUIRED,
            "" if data.preprocessing_valid else "preprocessing check failed",
        )

        ocr_provider = SyntheticOCRProvider(
            fields=data.ocr_fields,
            confidence=data.quality_confidence,
        )
        nfc_provider = SyntheticNFCReaderAdapter(
            fields=data.nfc_fields,
            confidence=1.0,
        )
        ocr_artifact: ExtractionArtifact = ocr_provider.extract(data.document, captured_at=timestamp)
        nfc_artifact: ExtractionArtifact = nfc_provider.read(data.card, captured_at=timestamp)
        stage(
            "field_ocr",
            StageStatus.COMPLETED,
            confidence=ocr_artifact.confidence,
            evidence_reference=ocr_artifact.evidence_reference,
        )
        stage(
            "mrz_read",
            StageStatus.COMPLETED,
            confidence=nfc_artifact.confidence,
            evidence_reference=nfc_artifact.evidence_reference,
        )

        # Field names come from the canonical allowlist validated at input.
        # Do not filter them by normalized value truthiness: value content is
        # sensitive and must not influence the public field-name summary.
        normalized_field_names = tuple(
            sorted(
                name
                for name, field_value in ocr_artifact.fields.items()
                if name in NATIONAL_CARD_FIELDS and field_value.confidence is not None
            ),
        )
        low_confidence_fields = tuple(
            name
            for name, field_value in ocr_artifact.fields.items()
            if field_value.confidence is not None and field_value.confidence < _MIN_CONFIDENCE
        )
        stage(
            "normalization",
            StageStatus.REVIEW_REQUIRED if low_confidence_fields else StageStatus.COMPLETED,
            "" if not low_confidence_fields else f"low confidence fields: {', '.join(low_confidence_fields)}",
        )

        outcome: ExtractionOutcome = reconcile_document_extraction(
            ocr_artifact,
            nfc_artifact,
            now=timestamp,
            raw_nid_for_check=raw_nid_for_check,
        )
        conflict_count = len(outcome.comparison.conflicts)
        stage(
            "cross_field_checks",
            StageStatus.REVIEW_REQUIRED if conflict_count else StageStatus.COMPLETED,
            "" if not conflict_count else f"conflicting fields: {conflict_count}",
        )
        anomaly = data.duplicate_indicator or data.anomaly_indicator
        stage(
            "duplicate_anomaly",
            StageStatus.REVIEW_REQUIRED if anomaly else StageStatus.COMPLETED,
            "" if not anomaly else "duplicate or anomaly indicator requires human review",
        )
        stage(
            "human_review",
            StageStatus.REVIEW_REQUIRED,
            "synthetic extraction never establishes identity or document authenticity",
        )
        stage(
            "retention_deletion_hooks",
            StageStatus.COMPLETED,
            evidence_reference=data.retention_hook,
        )

        if outcome.verified or outcome.recommended_state == VERIFIED:
            raise OcrPipelineError("synthetic OCR pipeline must never produce VERIFIED")

        audit_events = (
            extraction_audit_event(
                ocr_artifact,
                actor=actor_id,
                purpose=purpose,
                organization_id=organization_id,
                facility_id=facility_id,
                gula_citizen_identifier=gula_citizen_identifier,
                national_id_hash=national_id_hash,
                correlation_id=correlation_id,
                raw_nid_for_check=raw_nid_for_check,
            ),
            extraction_audit_event(
                nfc_artifact,
                actor=actor_id,
                purpose=purpose,
                organization_id=organization_id,
                facility_id=facility_id,
                gula_citizen_identifier=gula_citizen_identifier,
                national_id_hash=national_id_hash,
                correlation_id=correlation_id,
                raw_nid_for_check=raw_nid_for_check,
            ),
        )
        return SyntheticOcrPipelineResult(
            pipeline_version=PIPELINE_VERSION,
            stages=tuple(stages),
            outcome=outcome,
            extracted_field_names=normalized_field_names,
            field_confidences={
                name: field_value.confidence
                for name, field_value in ocr_artifact.fields.items()
            },
            audit_events=audit_events,
            retention_hook=data.retention_hook,
            deletion_hook=data.deletion_hook,
        )


__all__ = [
    "PIPELINE_VERSION",
    "STAGE_ORDER",
    "STAGE_VERSIONS",
    "OcrPipelineError",
    "OcrStageResult",
    "StageStatus",
    "SyntheticOcrInput",
    "SyntheticOcrPipeline",
    "SyntheticOcrPipelineResult",
]
