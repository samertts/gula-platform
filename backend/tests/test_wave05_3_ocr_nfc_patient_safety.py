"""Wave 05.3 OCR/NFC and patient identity safety tests.

Synthetic card references and protected values only. No card image, raw NFC
payload, chip layout, reader protocol, external OCR service, or real person is
used. Extraction outcomes never reach VERIFIED and never auto-merge patients.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from app._compat import UTC
from app.national.services.document_extraction import (
    PENDING_REVIEW,
    ExtractionArtifact,
    ExtractionContractError,
    ExtractionStatus,
    NfcCardReference,
    OcrDocumentReference,
    SyntheticNFCReaderAdapter,
    SyntheticOCRProvider,
    extraction_audit_event,
    reconcile_document_extraction,
)
from app.national.services.identity_governance import (
    CARD_EXPIRED,
    EXTRACTION_COMPLETED,
    INVESTIGATION_AUTHORIZED,
    REVIEW_REQUIRED,
    SOURCE_CARD_NFC,
    SOURCE_CARD_OCR,
    SUSPENDED,
    VERIFIED,
    ExtractedField,
    IdentityEvidenceError,
    LinkageReviewer,
)
from app.national.services.identity_persistence import (
    RegistrationRecord,
    RegistrationRequest,
    RegistrationState,
)
from app.national.services.patient_identity_safety import (
    AUTO_MERGE_PROHIBITED,
    FacilityIdentityRecord,
    PatientSafetyAction,
    assert_no_duplicate_registration,
    build_linkage_decision,
    cross_facility_linkage_decision,
    rollback_patient_linkage,
)

NOW = datetime(2026, 11, 25, 7, 2, 38, tzinfo=UTC)
SYNTHETIC_NID = "000000000001"
OTHER_SYNTHETIC_NID = "000000000002"
SYNTHETIC_GULA_A = "199000000001"
SYNTHETIC_GULA_B = "199100000002"
SYNTHETIC_HASH = "a" * 64
OTHER_HASH = "b" * 64


def _fields(nid: str = SYNTHETIC_NID, *, expired: bool = False) -> dict[str, str]:
    return {
        "national_id": nid,
        "full_name": "Test Citizen",
        "mother_name": "Test Mother",
        "birth_date": "1990-01-01",
        "family_number": "1000000001",
        "birth_place": "Baghdad",
        "card_issue_date": "2020-01-01",
        "card_expiry_date": "20200101" if expired else "20300101",
    }


def _ocr(
    *,
    nid: str = SYNTHETIC_NID,
    status: ExtractionStatus = ExtractionStatus.SUCCESS,
    missing: tuple[str, ...] = (),
    expired: bool = False,
    confidence: float | None = 0.95,
) -> SyntheticOCRProvider:
    values = _fields(nid, expired=expired)
    for name in missing:
        values.pop(name, None)
    fields = {
        name: ExtractedField(value, SOURCE_CARD_OCR, confidence, NOW)
        for name, value in values.items()
    }
    return SyntheticOCRProvider(
        fields=fields,
        status=status,
        confidence=confidence,
        card_expiry_date="20200101" if expired else "20300101",
    )


def _nfc(
    *,
    nid: str = SYNTHETIC_NID,
    status: ExtractionStatus = ExtractionStatus.SUCCESS,
    missing: tuple[str, ...] = (),
    expired: bool = False,
    confidence: float | None = 1.0,
) -> SyntheticNFCReaderAdapter:
    values = _fields(nid, expired=expired)
    for name in missing:
        values.pop(name, None)
    fields = {
        name: ExtractedField(value, SOURCE_CARD_NFC, confidence, NOW)
        for name, value in values.items()
    }
    return SyntheticNFCReaderAdapter(
        fields=fields,
        status=status,
        confidence=confidence,
        card_expiry_date="20200101" if expired else "20300101",
    )


def _ocr_artifact(**kwargs) -> ExtractionArtifact:
    return _ocr(**kwargs).extract(OcrDocumentReference("SYNTHETIC-DOC-0001"))


def _nfc_artifact(**kwargs) -> ExtractionArtifact:
    return _nfc(**kwargs).read(NfcCardReference("SYNTHETIC-READER-0001", "SYNTHETIC-CARD-0001"))


def _reconcile(ocr, nfc):
    return reconcile_document_extraction(
        ocr,
        nfc,
        now=NOW,
        raw_nid_for_check=SYNTHETIC_NID,
    )


def test_matching_ocr_and_nfc_still_requires_human_review() -> None:
    outcome = _reconcile(_ocr_artifact(), _nfc_artifact())
    assert outcome.recommended_state == PENDING_REVIEW
    assert outcome.events == (EXTRACTION_COMPLETED, REVIEW_REQUIRED)
    assert outcome.verified is False
    assert SYNTHETIC_NID not in repr(outcome)


def test_nid_mismatch_routes_to_pending_review() -> None:
    outcome = _reconcile(_ocr_artifact(), _nfc_artifact(nid=OTHER_SYNTHETIC_NID))
    assert outcome.recommended_state == PENDING_REVIEW
    assert REVIEW_REQUIRED in outcome.events
    assert any(item.field == "national_id" for item in outcome.comparison.conflicts)
    assert outcome.verified is False


def test_partial_extraction_routes_to_pending_review() -> None:
    outcome = _reconcile(_ocr_artifact(missing=("mother_name",)), _nfc_artifact())
    assert outcome.recommended_state == PENDING_REVIEW
    assert any(item.field == "mother_name" for item in outcome.comparison.uncertain_fields)


@pytest.mark.parametrize(
    "status",
    [
        ExtractionStatus.UNREADABLE,
        ExtractionStatus.UNSUPPORTED_CHIP,
        ExtractionStatus.READ_FAILURE,
        ExtractionStatus.INVALID_CONFIDENCE,
        ExtractionStatus.PARTIAL,
    ],
)
def test_ocr_and_nfc_failure_statuses_route_to_pending_review(status: ExtractionStatus) -> None:
    outcome = _reconcile(_ocr_artifact(status=status), _nfc_artifact())
    assert outcome.recommended_state == PENDING_REVIEW
    assert any(status.value in reason for reason in outcome.reasons)


def test_conflicting_fields_route_to_pending_review() -> None:
    from dataclasses import replace

    conflicting_nfc = _nfc_artifact()
    fields = dict(conflicting_nfc.fields)
    fields["full_name"] = ExtractedField("Different Name", SOURCE_CARD_NFC, 1.0, NOW)
    outcome = _reconcile(_ocr_artifact(), replace(conflicting_nfc, fields=fields))
    assert outcome.recommended_state == PENDING_REVIEW
    assert any(item.field == "full_name" for item in outcome.comparison.conflicts)


def test_expired_card_routes_to_pending_review() -> None:
    outcome = _reconcile(_ocr_artifact(expired=True), _nfc_artifact(expired=True))
    assert outcome.recommended_state == PENDING_REVIEW
    assert REVIEW_REQUIRED in outcome.events
    assert any("expiry" in reason for reason in outcome.reasons)
    assert outcome.verified is False


def test_expired_card_from_verified_state_is_downgraded_to_pending_review() -> None:
    outcome = reconcile_document_extraction(
        _ocr_artifact(expired=True),
        _nfc_artifact(expired=True),
        current_state=VERIFIED,
        now=NOW,
        raw_nid_for_check=SYNTHETIC_NID,
    )
    assert outcome.recommended_state == PENDING_REVIEW
    assert CARD_EXPIRED in outcome.events
    assert outcome.verified is False


def test_suspended_state_routes_to_pending_review() -> None:
    outcome = reconcile_document_extraction(
        _ocr_artifact(),
        _nfc_artifact(),
        current_state=SUSPENDED,
        now=NOW,
        raw_nid_for_check=SYNTHETIC_NID,
    )
    assert outcome.recommended_state == PENDING_REVIEW
    assert INVESTIGATION_AUTHORIZED in outcome.events
    assert outcome.verified is False


def test_ocr_alone_or_nfc_alone_never_reaches_data_extracted() -> None:
    ocr_only = _reconcile(_ocr_artifact(), ExtractionArtifact(
        source=SOURCE_CARD_NFC,
        status=ExtractionStatus.SUCCESS,
        fields={},
        captured_at=NOW,
        synthetic=True,
    ))
    nfc_only = _reconcile(ExtractionArtifact(
        source=SOURCE_CARD_OCR,
        status=ExtractionStatus.SUCCESS,
        fields={},
        captured_at=NOW,
        synthetic=True,
    ), _nfc_artifact())
    assert ocr_only.recommended_state == PENDING_REVIEW
    assert nfc_only.recommended_state == PENDING_REVIEW
    assert ocr_only.verified is False and nfc_only.verified is False


def test_artifacts_do_not_hold_image_or_raw_nfc_payload() -> None:
    artifact = _ocr_artifact()
    assert "card_image" not in artifact.fields
    assert not hasattr(artifact, "image_bytes")
    assert not hasattr(artifact, "raw_nfc_data")
    assert set(artifact.fields) <= {
        "national_id",
        "full_name",
        "mother_name",
        "birth_date",
        "family_number",
        "birth_place",
        "card_issue_date",
        "card_expiry_date",
    }


def test_invalid_confidence_fails_at_artifact_boundary() -> None:
    with pytest.raises(ExtractionContractError, match="confidence"):
        ExtractionArtifact(
            source=SOURCE_CARD_OCR,
            status=ExtractionStatus.INVALID_CONFIDENCE,
            fields={},
            captured_at=NOW,
            confidence=1.5,
            synthetic=True,
        )


def test_protected_nid_evidence_contains_hash_and_mask_only() -> None:
    outcome = _reconcile(_ocr_artifact(), _nfc_artifact())
    evidence = outcome.protected_national_id
    assert evidence is not None
    assert evidence.national_id_hash != SYNTHETIC_NID
    assert evidence.masked_national_id != SYNTHETIC_NID
    assert SYNTHETIC_NID not in repr(evidence)


def test_extraction_audit_rejects_raw_nid_in_caller_text() -> None:
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        extraction_audit_event(
            _ocr_artifact(),
            actor=f"actor {SYNTHETIC_NID}",
            purpose="REGISTRATION",
            organization_id="ORG-SYNTHETIC",
            facility_id="FACILITY-SYNTHETIC",
            gula_citizen_identifier=SYNTHETIC_GULA_A,
            national_id_hash=SYNTHETIC_HASH,
        )
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        extraction_audit_event(
            _ocr_artifact(),
            actor="actor",
            purpose="REGISTRATION",
            organization_id="ORG-SYNTHETIC",
            facility_id="FACILITY-SYNTHETIC",
            gula_citizen_identifier=f"GULA-{SYNTHETIC_NID}",
            national_id_hash=SYNTHETIC_HASH,
        )


def test_extraction_audit_events_do_not_leak_raw_nid() -> None:
    event = extraction_audit_event(
        _ocr_artifact(),
        actor="registration-officer",
        purpose="REGISTRATION",
        organization_id="ORG-SYNTHETIC",
        facility_id="FACILITY-SYNTHETIC",
        gula_citizen_identifier=SYNTHETIC_GULA_A,
        national_id_hash=SYNTHETIC_HASH,
        correlation_id="CORR-SYNTHETIC",
        raw_nid_for_check=SYNTHETIC_NID,
    )
    assert event.action == "ocr_extraction"
    assert SYNTHETIC_NID not in repr(event)


def _record(
    *,
    facility: str,
    identifier: str,
    nid_hash: str | None,
    nid_verified: bool = False,
    corroborated: bool = False,
    similarity: float | None = None,
    correction_count: int = 0,
    old_record: str | None = None,
) -> FacilityIdentityRecord:
    return FacilityIdentityRecord(
        facility_id=facility,
        local_patient_id=f"PATIENT-{identifier}",
        gula_citizen_identifier=identifier,
        nid_hash=nid_hash,
        nid_verified=nid_verified,
        birth_year=1990,
        birth_month=1,
        birth_day=1,
        phone_last10="1234567890" if corroborated else None,
        family_id_hash=None,
        name_similarity=similarity,
        mother_name_similarity=similarity,
        dob_match=similarity is not None,
        old_medical_record_reference=old_record,
        correction_count=correction_count,
    )


def _reviewer() -> LinkageReviewer:
    return LinkageReviewer(name="reviewer-1", user_id=42)


def test_name_mother_dob_similarity_alone_does_not_link() -> None:
    primary = _record(facility="FACILITY-A", identifier=SYNTHETIC_GULA_A, nid_hash=None, similarity=0.99)
    secondary = _record(facility="FACILITY-B", identifier=SYNTHETIC_GULA_B, nid_hash=None, similarity=0.99)
    decision = cross_facility_linkage_decision(
        primary,
        secondary,
        decision="APPROVED",
        reviewer=_reviewer(),
        reason="synthetic similarity request",
        evidence_reference="SYNTHETIC-EVIDENCE-0001",
        decided_at=NOW,
    )
    assert decision.action is PatientSafetyAction.PENDING_REVIEW
    assert decision.merged is False
    assert any("similarity alone" in reason for reason in decision.reasons)


def test_conflicting_nid_hashes_block_linkage() -> None:
    primary = _record(facility="FACILITY-A", identifier=SYNTHETIC_GULA_A, nid_hash=SYNTHETIC_HASH)
    secondary = _record(facility="FACILITY-B", identifier=SYNTHETIC_GULA_B, nid_hash=OTHER_HASH, nid_verified=True, corroborated=True)
    decision = cross_facility_linkage_decision(
        primary,
        secondary,
        decision="APPROVED",
        reviewer=_reviewer(),
        reason="synthetic conflict case",
        evidence_reference="SYNTHETIC-EVIDENCE-0002",
        decided_at=NOW,
    )
    assert decision.action is PatientSafetyAction.BLOCKED
    assert decision.merged is False


def test_missing_nid_data_routes_to_pending_review() -> None:
    primary = _record(facility="FACILITY-A", identifier=SYNTHETIC_GULA_A, nid_hash=SYNTHETIC_HASH)
    secondary = _record(facility="FACILITY-B", identifier=SYNTHETIC_GULA_B, nid_hash=None)
    decision = cross_facility_linkage_decision(
        primary,
        secondary,
        decision="APPROVED",
        reviewer=_reviewer(),
        reason="synthetic missing-data case",
        evidence_reference="SYNTHETIC-EVIDENCE-0003",
        decided_at=NOW,
    )
    assert decision.action is PatientSafetyAction.PENDING_REVIEW


def test_cross_facility_link_requires_explicit_approval_and_corroboration() -> None:
    primary = _record(
        facility="FACILITY-A",
        identifier=SYNTHETIC_GULA_A,
        nid_hash=SYNTHETIC_HASH,
        nid_verified=True,
        corroborated=True,
        old_record="OLD-RECORD-A",
    )
    secondary = _record(
        facility="FACILITY-B",
        identifier=SYNTHETIC_GULA_B,
        nid_hash=SYNTHETIC_HASH,
        nid_verified=True,
        corroborated=True,
        old_record="OLD-RECORD-B",
    )
    decision = cross_facility_linkage_decision(
        primary,
        secondary,
        decision="APPROVED",
        reviewer=_reviewer(),
        reason="synthetic approved cross-facility link",
        evidence_reference="SYNTHETIC-EVIDENCE-0004",
        decided_at=NOW,
    )
    assert decision.action is PatientSafetyAction.LINK_APPROVED
    assert decision.merged is False
    assert AUTO_MERGE_PROHIBITED is True
    assert decision.audit_metadata["old_medical_record_references"] == ("OLD-RECORD-A", "OLD-RECORD-B")


def test_duplicate_registration_is_rejected_for_one_subject() -> None:
    request_a = RegistrationRequest(
        idempotency_key="safety-a",
        subject_reference="SUBJECT-REF-SAFETY",
        birth_year=1990,
        requested_at=NOW,
    )
    request_b = RegistrationRequest(
        idempotency_key="safety-b",
        subject_reference="SUBJECT-REF-SAFETY",
        birth_year=1990,
        requested_at=NOW,
    )
    records = (
        RegistrationRecord(request_a, RegistrationState.COMPLETED, SYNTHETIC_GULA_A),
        RegistrationRecord(request_b, RegistrationState.COMPLETED, SYNTHETIC_GULA_B),
    )
    with pytest.raises(ValueError, match="found 2"):
        assert_no_duplicate_registration(list(records), subject_reference="SUBJECT-REF-SAFETY")


def test_rollback_preserves_original_decision_and_does_not_merge() -> None:
    decision = build_linkage_decision(
        primary_identifier=SYNTHETIC_GULA_A,
        secondary_identifier=SYNTHETIC_GULA_B,
        reviewer=_reviewer(),
        reason="synthetic link",
        evidence_reference="SYNTHETIC-EVIDENCE-0005",
        decided_at=NOW,
    )
    outcome = rollback_patient_linkage(
        decision,
        reviewer=_reviewer(),
        reason="synthetic rollback after review",
        rolled_back_at=NOW,
    )
    assert outcome.original_decision_retained is True
    assert outcome.decision.active is False
    assert outcome.decision.decided_at == decision.decided_at
    assert outcome.decision.rollback is not None
    assert outcome.audit_metadata["automatic_merge"] is False


def test_correction_history_is_preserved_in_safety_metadata() -> None:
    primary = _record(
        facility="FACILITY-A",
        identifier=SYNTHETIC_GULA_A,
        nid_hash=SYNTHETIC_HASH,
        correction_count=2,
    )
    secondary = _record(facility="FACILITY-B", identifier=SYNTHETIC_GULA_B, nid_hash=OTHER_HASH, nid_verified=True)
    decision = cross_facility_linkage_decision(
        primary,
        secondary,
        decision="PENDING",
        reviewer=_reviewer(),
        reason="synthetic correction case",
        evidence_reference="SYNTHETIC-EVIDENCE-0006",
        decided_at=NOW,
    )
    assert decision.action is PatientSafetyAction.BLOCKED
    assert decision.audit_metadata["correction_counts"]["primary"] == 2
