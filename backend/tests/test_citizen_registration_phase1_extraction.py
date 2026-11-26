"""Phase 1 adversarial tests for synthetic OCR sequencing and NFC read guards.

These tests use only opaque synthetic references. No image bytes, chip payloads,
keys, external providers, database, or national identity source is involved.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from app._compat import UTC
from app.national.services.document_authenticity import (
    CaptureSessionRegistry,
    DeviceCapabilityMetadata,
    NfcState,
)
from app.national.services.document_extraction import (
    NfcCardReference,
    OcrDocumentReference,
)
from app.national.services.nfc_read_guard import (
    NfcReadGuard,
    NfcReadGuardError,
    NfcReadRequest,
)
from app.national.services.ocr_pipeline import (
    PIPELINE_VERSION,
    STAGE_ORDER,
    OcrPipelineError,
    StageStatus,
    SyntheticOcrInput,
    SyntheticOcrPipeline,
)

NOW = datetime(2026, 11, 26, 10, 0, tzinfo=UTC)
NID_HASH = "c" * 64
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def _ocr_input(**overrides):
    values = {
        "document": OcrDocumentReference("SYNTHETIC-DOC-PHASE1"),
        "card": NfcCardReference("SYNTHETIC-READER-PHASE1", "SYNTHETIC-CARD-PHASE1"),
        "ocr_fields": {
            "full_name": "SYNTHETIC NAME",
            "mother_name": "SYNTHETIC MOTHER",
        },
        "nfc_fields": {
            "full_name": "SYNTHETIC NAME",
            "mother_name": "SYNTHETIC MOTHER",
        },
        "language": "ar",
        "quality_confidence": 0.95,
    }
    values.update(overrides)
    return SyntheticOcrInput(**values)


def _run(data: SyntheticOcrInput | None = None, **overrides):
    return SyntheticOcrPipeline().run(
        data or _ocr_input(),
        now=NOW,
        actor_id="officer-synthetic",
        purpose="identity_verification",
        organization_id="ORG-SYNTHETIC",
        facility_id="FACILITY-SYNTHETIC",
        gula_citizen_identifier="199000000001",
        national_id_hash=NID_HASH,
        correlation_id="CORR-PHASE1-OCR",
        **overrides,
    )


def _session(*, nfc_supported: bool = True):
    registry = CaptureSessionRegistry()
    challenge = registry.issue(
        session_id="SESSION-PHASE1-NFC",
        actor_id="citizen-synthetic",
        organization_id="ORG-SYNTHETIC",
        facility_id="FACILITY-SYNTHETIC",
        purpose="citizen_workspace",
        correlation_id="CORR-PHASE1-NFC",
        device_capabilities=DeviceCapabilityMetadata(
            nfc_supported=nfc_supported,
            camera_available=True,
        ),
        at=NOW,
        nonce="b" * 32,
    )
    return registry.complete(
        challenge,
        front_evidence_reference="SYNTHETIC-FRONT-NFC",
        back_evidence_reference="SYNTHETIC-BACK-NFC",
        captured_at=NOW,
    )


def _nfc_request(**overrides):
    values = {
        "session": _session(),
        "card": NfcCardReference("SYNTHETIC-READER-NFC", "SYNTHETIC-CARD-NFC"),
        "actor_id": "citizen-synthetic",
        "organization_id": "ORG-SYNTHETIC",
        "facility_id": "FACILITY-SYNTHETIC",
        "purpose": "citizen_workspace",
        "correlation_id": "CORR-PHASE1-NFC",
        "consent_reference": "CONSENT:SESSION-PHASE1-NFC:CORR-PHASE1-NFC",
        "evidence_reference": "SYNTHETIC-EVIDENCE-NFC",
        "state": NfcState.NFC_READ_SUCCESSFULLY,
        "read_at": NOW + timedelta(seconds=1),
        "field_digests": {"full_name": DIGEST_A},
    }
    values.update(overrides)
    return NfcReadRequest(**values)


def test_ocr_pipeline_runs_all_versioned_stages_and_never_verifies() -> None:
    result = _run()
    assert result.pipeline_version == PIPELINE_VERSION
    assert tuple(stage.stage for stage in result.stages) == STAGE_ORDER
    assert all(stage.version for stage in result.stages)
    assert result.outcome.verified is False
    assert result.outcome.recommended_state != "VERIFIED"
    assert result.review_required is True
    assert any(stage.stage == "human_review" for stage in result.stages)
    public = result.to_public_dict()
    assert "156" not in str(public)
    assert "national_id_value" not in public


def test_low_confidence_and_conflicting_fields_route_to_review() -> None:
    low = _run(_ocr_input(quality_confidence=0.42))
    assert low.review_required is True
    quality_stage = next(stage for stage in low.stages if stage.stage == "image_quality")
    assert quality_stage.status is StageStatus.REVIEW_REQUIRED

    conflict = _run(
        _ocr_input(
            ocr_fields={"full_name": "SYNTHETIC NAME"},
            nfc_fields={"full_name": "DIFFERENT SYNTHETIC NAME"},
        ),
    )
    assert conflict.review_required is True
    assert any("conflicting field" in reason for reason in conflict.outcome.reasons)


def test_anomalies_unsupported_doc_and_forged_references_are_review_only() -> None:
    anomaly = _run(_ocr_input(duplicate_indicator=True, anomaly_indicator=True))
    assert anomaly.review_required is True
    assert any(stage.stage == "duplicate_anomaly" and stage.status is StageStatus.REVIEW_REQUIRED for stage in anomaly.stages)

    unsupported = _run(_ocr_input(classification="passport_scan"))
    assert unsupported.review_required is True

    with pytest.raises(OcrPipelineError, match="Arabic and English"):
        _ocr_input(language="ku")

    with pytest.raises(Exception, match="document reference must be opaque"):
        _ocr_input(document=OcrDocumentReference("bad ref with spaces"))


def test_pipeline_rejects_unsupported_field_names_and_invalid_hooks() -> None:
    with pytest.raises(OcrPipelineError, match="unsupported field names"):
        _ocr_input(ocr_fields={"passport_number": "SYNTHETIC"})
    with pytest.raises(OcrPipelineError, match="opaque labels"):
        _ocr_input(retention_hook="s3://bucket/key")


def test_nfc_guard_binds_session_and_never_claims_chip_authenticity() -> None:
    guard = NfcReadGuard()
    evidence = guard.authorize(
        _nfc_request(),
        national_id_hash=NID_HASH,
        gula_citizen_identifier="199000000001",
    )
    assert evidence.chip_authenticity_verified is False
    assert evidence.requires_review is True
    assert evidence.to_public_dict()["state"] == NfcState.NFC_READ_SUCCESSFULLY.value


def test_nfc_replay_and_session_hijack_are_rejected() -> None:
    guard = NfcReadGuard()
    request = _nfc_request()
    guard.authorize(request, national_id_hash=NID_HASH, gula_citizen_identifier="199000000001")
    with pytest.raises(NfcReadGuardError, match="replay is rejected"):
        guard.authorize(request, national_id_hash=NID_HASH, gula_citizen_identifier="199000000001")
    hijack = _nfc_request(evidence_reference="SYNTHETIC-EVIDENCE-HIJACK")
    with pytest.raises(NfcReadGuardError, match="hijack"):
        guard.authorize(hijack, national_id_hash=NID_HASH, gula_citizen_identifier="199000000001")


def test_nfc_context_mismatch_unsupported_capability_and_consent_are_denied() -> None:
    guard = NfcReadGuard()
    with pytest.raises(NfcReadGuardError, match="actor does not match"):
        guard.authorize(
            _nfc_request(actor_id="other-actor-synthetic"),
            national_id_hash=NID_HASH,
            gula_citizen_identifier="199000000001",
        )
    with pytest.raises(NfcReadGuardError, match="NFC-capable device"):
        guard.authorize(
            _nfc_request(session=_session(nfc_supported=False)),
            national_id_hash=NID_HASH,
            gula_citizen_identifier="199000000001",
        )
    with pytest.raises(NfcReadGuardError, match="consent reference"):
        _nfc_request(consent_reference="")
    with pytest.raises(NfcReadGuardError, match="consent must be bound"):
        _nfc_request(consent_reference="CONSENT:ANOTHER-SESSION:CORR-PHASE1-NFC")


def test_malformed_and_inconsistent_nfc_reads_route_to_review() -> None:
    guard = NfcReadGuard()
    failed = guard.authorize(
        _nfc_request(state=NfcState.NFC_READ_FAILED),
        national_id_hash=NID_HASH,
        gula_citizen_identifier="199000000001",
    )
    assert failed.requires_review is True
    assert any("NFC state is" in reason for reason in failed.reasons)

    inconsistent = NfcReadGuard().authorize(
        _nfc_request(field_digests={"full_name": DIGEST_B}),
        national_id_hash=NID_HASH,
        gula_citizen_identifier="199000000001",
        ocr_field_digests={"full_name": DIGEST_A},
    )
    assert any("inconsistent NFC field" in reason for reason in inconsistent.reasons)

    with pytest.raises(NfcReadGuardError, match="field digests must be"):
        _nfc_request(field_digests={"full_name": "not-a-digest"})
