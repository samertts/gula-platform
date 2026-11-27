"""Wave 05.3 NIDP original Iraqi national identity card policy tests.

All values are synthetic. No card image, raw NFC payload, real identity number,
chip specification, government credential, or external service is used. The
tests pin the fail-closed original-card and live-capture boundary and prove
that no extraction, NFC read, or synthetic government result reaches VERIFIED.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from app._compat import UTC
from app.identity.services.authorization_decision import (
    AuthorizationDecision,
    AuthorizationReason,
)
from app.national.services.document_authenticity import (
    LIVE_CAPTURE_COMPLETED,
    ORIGINAL_CARD_PRESENTED,
    CaptureSessionRegistry,
    DeviceCapabilityMetadata,
    DocumentAuthenticityDecision,
    DocumentAuthenticityError,
    DocumentAuthenticityState,
    FieldComparison,
    LiveCaptureMethod,
    LiveCaptureOutcome,
    LiveCaptureSource,
    NfcReadOutcome,
    NfcState,
    NidpEvidenceBundle,
    OriginalCardPresentation,
    OriginalDocumentChannel,
    RegistrationEligibilityState,
    RegistrationPath,
    RejectionClassification,
    VisualInspection,
    apply_authenticity_transition,
    assert_identity_verification_blocked,
    assert_no_manual_authenticity_override,
    authorize_nidp_operation,
    classify_originality_channel,
    compare_ocr_and_mrz,
    evaluate_document_authenticity,
    nidp_audit_event,
    normalize_document_numerals,
    registration_eligibility,
)
from app.national.services.document_extraction import (
    ExtractionArtifact,
    ExtractionStatus,
)
from app.national.services.identity_access import (
    WAVE053_AUDIT_OPERATIONS,
    IdentityAccessContext,
    IdentityAccessDeniedError,
    IdentityEvidenceError,
    IdentityRole,
)
from app.national.services.identity_governance import (
    CARD_EXPIRED,
    DATA_EXTRACTED,
    DOCUMENT_CHECKED,
    EXPIRED,
    EXTRACTION_COMPLETED,
    GOVERNMENT_VERIFIED,
    INVESTIGATION_AUTHORIZED,
    NEW_EVIDENCE_SUBMITTED,
    PENDING_REVIEW,
    REJECTED,
    REVIEW_REQUIRED,
    SOURCE_CARD_NFC,
    SOURCE_CARD_OCR,
    SUSPENDED,
    UNVERIFIED,
    VERIFIED,
    ExtractedField,
)

NOW = datetime(2026, 11, 25, 10, 30, 0, tzinfo=UTC)
CORRELATION_ID = "CORR-SYNTHETIC-NIDP"
SYNTHETIC_NID = "000000000001"
OTHER_SYNTHETIC_NID = "000000000002"
ARABIC_SYNTHETIC_NID = "\u0660" * 11 + "\u0661"
SYNTHETIC_GULA_ID = "199000000001"
SYNTHETIC_HASH = "a" * 64

REQUIRED_DOCUMENT_STATES = {
    "ORIGINAL_CARD_PRESENTED",
    "LIVE_CAPTURE_COMPLETED",
    "VISUAL_INSPECTION_COMPLETED",
    "MRZ_READ_SUCCESSFULLY",
    "NFC_READ_SUCCESSFULLY",
    "CHIP_AUTHENTICITY_VERIFIED",
    "DOCUMENT_AUTHENTICITY_CONFIRMED",
    "DOCUMENT_AUTHENTICITY_FAILED",
    "DOCUMENT_REVIEW_REQUIRED",
}
NIDP_AUDIT_OPERATIONS = {
    "ORIGINAL_CARD_PRESENTED",
    "LIVE_CAPTURE_STARTED",
    "LIVE_CAPTURE_COMPLETED",
    "MRZ_EXTRACTION",
    "AUTHENTICITY_INSPECTION",
    "AUTHENTICITY_FAILURE",
    "COPY_REJECTION",
    "SUSPICIOUS_DOCUMENT",
    "DOCUMENT_REVIEW",
    "REVIEW_OUTCOME",
    "IDENTITY_APPROVAL",
    "IDENTITY_REJECTION",
    "UNAUTHORIZED_VERIFICATION_ATTEMPT",
    "MANUAL_OVERRIDE_ATTEMPT",
    "IDENTITY_CORRECTION",
}


def _fields(nid: str = SYNTHETIC_NID, *, expired: bool = False) -> dict[str, str]:
    return {
        "national_id": nid,
        "full_name": "Synthetic Citizen",
        "mother_name": "Synthetic Mother",
        "birth_date": "1990-01-01",
        "family_number": "1000000001",
        "birth_place": "Baghdad",
        "card_issue_date": "2020-01-01",
        "card_expiry_date": "20200101" if expired else "20300101",
    }


def _artifact(
    *,
    source: str,
    nid: str = SYNTHETIC_NID,
    missing: tuple[str, ...] = (),
    confidence: float | None = 1.0,
    status: ExtractionStatus = ExtractionStatus.SUCCESS,
    expired: bool = False,
) -> ExtractionArtifact:
    values = _fields(nid, expired=expired)
    for name in missing:
        values.pop(name, None)
    return ExtractionArtifact(
        source=source,
        status=status,
        fields={
            name: ExtractedField(value, source, confidence, NOW)
            for name, value in values.items()
        },
        captured_at=NOW,
        confidence=confidence,
        card_expiry_date="20200101" if expired else "20300101",
        evidence_reference="SYNTHETIC-ARTIFACT-0001",
    )


def _ocr(**kwargs) -> ExtractionArtifact:
    return _artifact(source=SOURCE_CARD_OCR, **kwargs)


def _nfc(**kwargs) -> ExtractionArtifact:
    return _artifact(source=SOURCE_CARD_NFC, **kwargs)


def _challenge(
    registry: CaptureSessionRegistry,
    *,
    nfc_supported: bool = True,
    session_id: str = "SYNTHETIC-SESSION-0001",
) -> object:
    return registry.issue(
        session_id=session_id,
        actor_id="officer-1",
        organization_id="ORG-SYNTHETIC",
        facility_id="FACILITY-SYNTHETIC",
        purpose="TREATMENT",
        correlation_id=CORRELATION_ID,
        device_capabilities=DeviceCapabilityMetadata(
            nfc_supported=nfc_supported,
            camera_available=True,
        ),
        at=NOW,
        nonce="a" * 32,
    )


def _capture(
    registry: CaptureSessionRegistry,
    **challenge_kwargs,
):
    challenge = _challenge(registry, **challenge_kwargs)
    return registry.complete(
        challenge,
        front_evidence_reference="SYNTHETIC-FRONT-0001",
        back_evidence_reference="SYNTHETIC-BACK-0001",
        captured_at=NOW + timedelta(seconds=1),
    )


def _presentation(
    *,
    channel: object = OriginalDocumentChannel.AUTHORIZED_LIVE_CAMERA_SESSION,
    physical_presented: bool = True,
) -> OriginalCardPresentation:
    return OriginalCardPresentation(
        channel=channel,
        actor_id="officer-1",
        organization_id="ORG-SYNTHETIC",
        facility_id="FACILITY-SYNTHETIC",
        purpose="TREATMENT",
        correlation_id=CORRELATION_ID,
        presented_at=NOW,
        evidence_reference="SYNTHETIC-ORIGINAL-0001",
        physical_presented=physical_presented,
    )


def _inspection(
    *,
    mismatch: bool = False,
    uncertain: bool = False,
) -> VisualInspection:
    return VisualInspection(
        inspector_id="officer-1",
        organization_id="ORG-SYNTHETIC",
        facility_id="FACILITY-SYNTHETIC",
        purpose="TREATMENT",
        correlation_id=CORRELATION_ID,
        inspected_at=NOW + timedelta(seconds=2),
        evidence_reference="SYNTHETIC-INSPECTION-0001",
        security_features_observed=("synthetic-feature-a", "synthetic-feature-b"),
        mismatch=mismatch,
        uncertain=uncertain,
    )


def _evidence(
    *,
    path: RegistrationPath = RegistrationPath.HOME_NFC,
    nfc_state: NfcState | None = NfcState.NFC_READ_SUCCESSFULLY,
    nfc_supported: bool = True,
    official_nfc_reading_documented: bool = True,
    authenticity_checks_completed: bool = True,
    authorized_officer_reviewed: bool = True,
    central_workflow_recorded: bool = True,
    mismatch: bool = False,
    uncertain: bool = False,
    expired: bool = False,
    suspected_forgery: bool = False,
    rejection: RejectionClassification | None = None,
    comparison: FieldComparison | None = None,
    ocr: ExtractionArtifact | None = None,
    nfc_artifact: ExtractionArtifact | None = None,
) -> NidpEvidenceBundle:
    capture = _capture(CaptureSessionRegistry(), nfc_supported=nfc_supported)
    nfc = None
    if nfc_state is not None:
        nfc = NfcReadOutcome(
            state=nfc_state,
            read_at=NOW + timedelta(seconds=3),
            evidence_reference="SYNTHETIC-NFC-0001",
        )
    return NidpEvidenceBundle(
        path=path,
        presentation=_presentation(),
        capture=capture,
        visual_inspection=_inspection(mismatch=mismatch, uncertain=uncertain),
        ocr=ocr,
        nfc=nfc,
        comparison=comparison,
        rejection=rejection,
        expired=expired,
        suspected_forgery=suspected_forgery,
        official_nfc_reading_documented=official_nfc_reading_documented,
        authenticity_checks_completed=authenticity_checks_completed,
        authorized_officer_reviewed=authorized_officer_reviewed,
        central_workflow_recorded=central_workflow_recorded,
        **({"mrz": nfc_artifact} if nfc_artifact is not None else {}),
    )


def _context(**overrides) -> IdentityAccessContext:
    values = {
        "decision": AuthorizationDecision.allow(),
        "role": IdentityRole.IDENTITY_REVIEWER,
        "actor_id": "reviewer-1",
        "organization_id": "ORG-SYNTHETIC",
        "facility_id": "FACILITY-SYNTHETIC",
        "purpose": "TREATMENT",
        "action": "DOCUMENT_REVIEW",
        "requested_fields": ("gula_citizen_identifier", "verification_state"),
        "gula_citizen_identifier": SYNTHETIC_GULA_ID,
        "national_id_hash": SYNTHETIC_HASH,
        "now": NOW,
    }
    values.update(overrides)
    return IdentityAccessContext(**values)


def test_all_required_document_states_are_defined() -> None:
    assert {state.value for state in DocumentAuthenticityState} == REQUIRED_DOCUMENT_STATES


def test_all_required_rejection_and_nfc_states_are_defined() -> None:
    assert {state.value for state in RejectionClassification} == {
        "COPY_PRESENTED",
        "PRINTED_REPLICA_PRESENTED",
        "DIGITAL_IMAGE_PRESENTED",
        "SCREENSHOT_PRESENTED",
        "ORIGINALITY_UNCERTAIN",
        "SECURITY_FEATURE_MISMATCH",
    }
    assert {state.value for state in NfcState} == {
        "NFC_UNAVAILABLE",
        "NFC_UNSUPPORTED",
        "NFC_READ_FAILED",
        "NFC_READ_SUCCESSFULLY",
        "CHIP_AUTHENTICITY_UNVERIFIED",
    }


@pytest.mark.parametrize(
    ("channel", "classification"),
    [
        *[(channel, RejectionClassification.COPY_PRESENTED) for channel in (
            OriginalDocumentChannel.PREVIOUS_CAPTURE,
            OriginalDocumentChannel.PHONE_GALLERY,
            OriginalDocumentChannel.WHATSAPP_IMAGE,
            OriginalDocumentChannel.TELEGRAM_IMAGE,
            OriginalDocumentChannel.EMAIL_ATTACHMENT,
            OriginalDocumentChannel.SCANNED_COPY,
            OriginalDocumentChannel.PHOTOCOPY,
            OriginalDocumentChannel.CERTIFIED_COPY,
            OriginalDocumentChannel.UNCERTIFIED_COPY,
        )],
        (OriginalDocumentChannel.PRINTED_REPLICA, RejectionClassification.PRINTED_REPLICA_PRESENTED),
        (OriginalDocumentChannel.PDF_DOCUMENT, RejectionClassification.DIGITAL_IMAGE_PRESENTED),
        (OriginalDocumentChannel.DIGITAL_REPRODUCTION, RejectionClassification.DIGITAL_IMAGE_PRESENTED),
        (OriginalDocumentChannel.SCREENSHOT, RejectionClassification.SCREENSHOT_PRESENTED),
        ("UNRECOGNISED-CHANNEL", RejectionClassification.ORIGINALITY_UNCERTAIN),
    ],
)
def test_non_original_channels_are_explicitly_rejected(channel, classification) -> None:
    assert classify_originality_channel(channel) is classification
    with pytest.raises(DocumentAuthenticityError, match=classification.value):
        _presentation(channel=channel)


def test_authorized_live_camera_channel_is_not_rejected() -> None:
    assert classify_originality_channel(
        OriginalDocumentChannel.AUTHORIZED_LIVE_CAMERA_SESSION,
    ) is None
    assert _presentation().channel is OriginalDocumentChannel.AUTHORIZED_LIVE_CAMERA_SESSION


def test_physical_card_must_be_presented() -> None:
    with pytest.raises(DocumentAuthenticityError, match="original physical card"):
        _presentation(physical_presented=False)


def test_capture_requires_server_issued_challenge() -> None:
    foreign_challenge = _challenge(CaptureSessionRegistry())
    with pytest.raises(DocumentAuthenticityError, match="not issued by this registry"):
        CaptureSessionRegistry().complete(
            foreign_challenge,
            front_evidence_reference="SYNTHETIC-FRONT-0002",
            back_evidence_reference="SYNTHETIC-BACK-0002",
            captured_at=NOW + timedelta(seconds=1),
        )


def test_capture_challenge_replay_is_rejected() -> None:
    registry = CaptureSessionRegistry()
    challenge = _challenge(registry)
    registry.complete(
        challenge,
        front_evidence_reference="SYNTHETIC-FRONT-0003",
        back_evidence_reference="SYNTHETIC-BACK-0003",
        captured_at=NOW + timedelta(seconds=1),
    )
    with pytest.raises(DocumentAuthenticityError, match="replay is rejected"):
        registry.complete(
            challenge,
            front_evidence_reference="SYNTHETIC-FRONT-0004",
            back_evidence_reference="SYNTHETIC-BACK-0004",
            captured_at=NOW + timedelta(seconds=2),
        )


def test_saved_upload_cannot_satisfy_live_capture() -> None:
    registry = CaptureSessionRegistry()
    challenge = _challenge(registry)
    with pytest.raises(DocumentAuthenticityError, match="authorized live-camera session"):
        registry.complete(
            challenge,
            front_evidence_reference="SYNTHETIC-FRONT-0005",
            back_evidence_reference="SYNTHETIC-BACK-0005",
            captured_at=NOW + timedelta(seconds=1),
            source="PRE_EXISTING_UPLOAD",
        )

    with pytest.raises(DocumentAuthenticityError, match=r"synthetic in Wave 05\.3"):
        registry.complete(
            challenge,
            front_evidence_reference="uploads/saved-card-image.png",
            back_evidence_reference="SYNTHETIC-BACK-0006",
            captured_at=NOW + timedelta(seconds=1),
        )


def test_capture_metadata_records_method_source_outcome_and_minimal_capability() -> None:
    capture = _capture(CaptureSessionRegistry())
    assert capture.capture_method is LiveCaptureMethod.SERVER_CHALLENGE_LIVE_CAMERA
    assert capture.source is LiveCaptureSource.AUTHORIZED_LIVE_CAMERA_SESSION
    assert capture.outcome is LiveCaptureOutcome.COMPLETED
    assert capture.captured_at > capture.challenge.issued_at
    assert capture.challenge.session_id == "SYNTHETIC-SESSION-0001"
    assert capture.challenge.device_capabilities.public() == {
        "nfc_supported": True,
        "camera_available": True,
    }


def test_front_and_back_evidence_references_must_differ() -> None:
    registry = CaptureSessionRegistry()
    challenge = _challenge(registry)
    with pytest.raises(DocumentAuthenticityError, match="front and back"):
        registry.complete(
            challenge,
            front_evidence_reference="SYNTHETIC-CARD-0001",
            back_evidence_reference="SYNTHETIC-CARD-0001",
            captured_at=NOW + timedelta(seconds=1),
        )


def test_capture_cannot_precede_challenge() -> None:
    registry = CaptureSessionRegistry()
    challenge = _challenge(registry)
    with pytest.raises(DocumentAuthenticityError, match="cannot precede"):
        registry.complete(
            challenge,
            front_evidence_reference="SYNTHETIC-FRONT-0007",
            back_evidence_reference="SYNTHETIC-BACK-0007",
            captured_at=NOW - timedelta(seconds=1),
        )


def test_arabic_and_western_numerals_are_normalized_for_comparison() -> None:
    assert normalize_document_numerals(ARABIC_SYNTHETIC_NID) == SYNTHETIC_NID
    mixed_digits = " " + "\u0660\u0661\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9" + " "
    assert normalize_document_numerals(mixed_digits) == "0123456789"


def test_matching_ocr_and_mrz_never_confirm_authenticity() -> None:
    compared = compare_ocr_and_mrz(_ocr(nid=ARABIC_SYNTHETIC_NID), _nfc())
    assert compared.requires_review() is False
    assert set(compared.matched_fields) == {
        "national_id",
        "full_name",
        "mother_name",
        "birth_date",
        "family_number",
        "birth_place",
        "card_issue_date",
        "card_expiry_date",
    }
    decision = evaluate_document_authenticity(_evidence(comparison=compared))
    assert decision.state is DocumentAuthenticityState.DOCUMENT_REVIEW_REQUIRED
    assert decision.verified is False
    assert DocumentAuthenticityState.DOCUMENT_AUTHENTICITY_CONFIRMED.value not in repr(decision)
    assert SYNTHETIC_NID not in repr(decision)


def test_conflicting_fields_route_to_review() -> None:
    compared = compare_ocr_and_mrz(_ocr(), _nfc(nid=OTHER_SYNTHETIC_NID))
    assert "national_id" in compared.conflicting_fields
    decision = evaluate_document_authenticity(_evidence(comparison=compared))
    assert decision.state is DocumentAuthenticityState.DOCUMENT_REVIEW_REQUIRED
    assert any("comparison" in reason for reason in decision.reasons)


def test_missing_and_low_confidence_fields_route_to_review() -> None:
    missing = compare_ocr_and_mrz(_ocr(missing=("mother_name",)), _nfc())
    assert "mother_name" in missing.missing_fields
    low_confidence = compare_ocr_and_mrz(_ocr(confidence=0.5), _nfc())
    assert "national_id" in low_confidence.uncertain_fields
    for compared in (missing, low_confidence):
        decision = evaluate_document_authenticity(_evidence(comparison=compared))
        assert decision.state is DocumentAuthenticityState.DOCUMENT_REVIEW_REQUIRED


@pytest.mark.parametrize(
    "state",
    [
        ExtractionStatus.UNREADABLE,
        ExtractionStatus.UNSUPPORTED_CHIP,
        ExtractionStatus.READ_FAILURE,
        ExtractionStatus.INVALID_CONFIDENCE,
        ExtractionStatus.PARTIAL,
    ],
)
def test_ocr_or_nfc_failure_status_routes_to_review(state: ExtractionStatus) -> None:
    compared = compare_ocr_and_mrz(_ocr(status=state), _nfc())
    assert compared.requires_review() is True
    decision = evaluate_document_authenticity(_evidence(comparison=compared))
    assert decision.state is DocumentAuthenticityState.DOCUMENT_REVIEW_REQUIRED


def test_nfc_read_success_alone_does_not_establish_chip_authenticity() -> None:
    decision = evaluate_document_authenticity(_evidence())
    assert decision.state is DocumentAuthenticityState.DOCUMENT_REVIEW_REQUIRED
    assert any("chip authenticity" in reason for reason in decision.reasons)
    assert DocumentAuthenticityState.CHIP_AUTHENTICITY_VERIFIED.value not in repr(decision)


@pytest.mark.parametrize(
    "state",
    [
        NfcState.NFC_UNAVAILABLE,
        NfcState.NFC_UNSUPPORTED,
        NfcState.NFC_READ_FAILED,
        NfcState.CHIP_AUTHENTICITY_UNVERIFIED,
    ],
)
def test_nfc_failure_states_route_review_without_counterfeit_label(state: NfcState) -> None:
    decision = evaluate_document_authenticity(_evidence(nfc_state=state))
    assert decision.state is DocumentAuthenticityState.DOCUMENT_REVIEW_REQUIRED
    assert decision.rejection is None
    assert state.value in " ".join(decision.reasons)
    assert "counterfeit" not in repr(decision).lower()


def test_security_feature_mismatch_routes_to_review() -> None:
    decision = evaluate_document_authenticity(_evidence(mismatch=True))
    assert decision.rejection is RejectionClassification.SECURITY_FEATURE_MISMATCH
    assert decision.state is DocumentAuthenticityState.DOCUMENT_REVIEW_REQUIRED


def test_uncertain_originality_is_not_counterfeit() -> None:
    decision = evaluate_document_authenticity(_evidence(uncertain=True))
    assert decision.rejection is RejectionClassification.ORIGINALITY_UNCERTAIN
    assert "counterfeit" not in repr(decision).lower()


def test_suspected_forgery_requires_human_review() -> None:
    decision = evaluate_document_authenticity(_evidence(suspected_forgery=True))
    assert decision.rejection is RejectionClassification.ORIGINALITY_UNCERTAIN
    assert decision.state is DocumentAuthenticityState.DOCUMENT_REVIEW_REQUIRED


def test_explicit_copy_rejection_routes_to_review() -> None:
    decision = evaluate_document_authenticity(
        _evidence(rejection=RejectionClassification.COPY_PRESENTED),
    )
    assert decision.rejection is RejectionClassification.COPY_PRESENTED
    assert "original-card path rejected" in decision.reasons


def test_expired_document_routes_to_review() -> None:
    decision = evaluate_document_authenticity(_evidence(expired=True))
    assert any("expired" in reason for reason in decision.reasons)
    assert decision.state is DocumentAuthenticityState.DOCUMENT_REVIEW_REQUIRED


def test_home_nfc_requires_capability_official_reading_and_completed_checks() -> None:
    decision = evaluate_document_authenticity(
        _evidence(
            nfc_supported=False,
            official_nfc_reading_documented=False,
            authenticity_checks_completed=False,
        ),
    )
    reasons = " ".join(decision.reasons)
    assert "NFC-capable device" in reasons
    assert "officially documented direct reading" in reasons
    assert "completed authenticity checks" in reasons
    assert decision.state is DocumentAuthenticityState.DOCUMENT_REVIEW_REQUIRED


def test_home_nfc_success_still_produces_incomplete_eligibility() -> None:
    evidence = _evidence()
    decision = evaluate_document_authenticity(evidence)
    eligibility = registration_eligibility(evidence, decision)
    assert eligibility.state is RegistrationEligibilityState.DOCUMENT_REVIEW_REQUIRED
    assert eligibility.identity_verified is False
    with pytest.raises(DocumentAuthenticityError, match="verification remains incomplete"):
        assert_identity_verification_blocked(decision)


def test_without_nfc_only_initial_incomplete_account_is_allowed() -> None:
    evidence = _evidence(
        path=RegistrationPath.IN_PERSON_OFFICER,
        nfc_state=None,
        authorized_officer_reviewed=False,
        central_workflow_recorded=False,
    )
    decision = evaluate_document_authenticity(evidence)
    eligibility = registration_eligibility(evidence, decision)
    assert eligibility.state is RegistrationEligibilityState.IDENTITY_VERIFICATION_INCOMPLETE
    assert eligibility.identity_verified is False
    reasons = " ".join(eligibility.reasons)
    assert "authorized officer inspection" in reasons
    assert "central workflow recording" in reasons
    assert "initial incomplete account" in reasons


@pytest.mark.parametrize(
    "current_state",
    [
        UNVERIFIED,
        DATA_EXTRACTED,
        PENDING_REVIEW,
        DOCUMENT_CHECKED,
        GOVERNMENT_VERIFIED,
        SUSPENDED,
        EXPIRED,
        REJECTED,
        VERIFIED,
    ],
)
def test_review_routing_uses_only_canonical_transitions(current_state: str) -> None:
    decision = evaluate_document_authenticity(_evidence())
    result = apply_authenticity_transition(decision, current_state=current_state)
    assert result.state == PENDING_REVIEW
    assert VERIFIED not in result.events
    for event in result.events:
        assert event in {
            EXTRACTION_COMPLETED,
            REVIEW_REQUIRED,
            INVESTIGATION_AUTHORIZED,
            NEW_EVIDENCE_SUBMITTED,
            CARD_EXPIRED,
        }


def test_previously_verified_record_is_expired_before_review() -> None:
    decision = evaluate_document_authenticity(_evidence())
    result = apply_authenticity_transition(decision, current_state=VERIFIED)
    assert result.events == (CARD_EXPIRED, NEW_EVIDENCE_SUBMITTED)
    assert result.state == PENDING_REVIEW


def test_confirmed_authenticity_decision_cannot_be_constructed() -> None:
    with pytest.raises(DocumentAuthenticityError, match="approved official procedure"):
        DocumentAuthenticityDecision(
            state=DocumentAuthenticityState.DOCUMENT_AUTHENTICITY_CONFIRMED,
            canonical_event="DOCUMENT_AUTHENTICITY_CONFIRMED",
            canonical_state=DOCUMENT_CHECKED,
            reasons=("synthetic only",),
        )


@pytest.mark.parametrize(
    "target_state",
    [
        VERIFIED,
        DocumentAuthenticityState.CHIP_AUTHENTICITY_VERIFIED.value,
        DocumentAuthenticityState.DOCUMENT_AUTHENTICITY_CONFIRMED.value,
    ],
)
def test_manual_authenticity_override_is_prohibited(target_state: str) -> None:
    with pytest.raises(DocumentAuthenticityError, match="manual authenticity override"):
        assert_no_manual_authenticity_override(target_state)


def test_synthetic_government_verification_cannot_activate_identity() -> None:
    decision = evaluate_document_authenticity(_evidence())
    with pytest.raises(DocumentAuthenticityError, match="synthetic government verification"):
        assert_identity_verification_blocked(
            decision,
            synthetic_government_verified=True,
        )


def test_authorization_requires_canonical_allow_decision() -> None:
    with pytest.raises(IdentityAccessDeniedError, match="canonical authorization denied"):
        authorize_nidp_operation(
            _context(
                decision=AuthorizationDecision.deny(AuthorizationReason.permission_missing),
            ),
        )


def test_registration_officer_cannot_perform_reviewer_only_operation() -> None:
    with pytest.raises(IdentityAccessDeniedError, match="role is not approved"):
        authorize_nidp_operation(
            _context(role=IdentityRole.REGISTRATION_OFFICER, action="DOCUMENT_REVIEW"),
        )


@pytest.mark.parametrize(
    ("action", "role"),
    [
        (ORIGINAL_CARD_PRESENTED, IdentityRole.REGISTRATION_OFFICER),
        (LIVE_CAPTURE_COMPLETED, IdentityRole.REGISTRATION_OFFICER),
        ("DOCUMENT_REVIEW", IdentityRole.IDENTITY_REVIEWER),
        ("MANUAL_OVERRIDE_ATTEMPT", IdentityRole.IDENTITY_REVIEWER),
    ],
)
def test_nidp_operations_are_authorized_through_canonical_boundary(action, role) -> None:
    grant = authorize_nidp_operation(_context(action=action, role=role))
    assert grant.action == action
    assert grant.audit_event.decision == "success"
    assert "national_id" not in grant.allowed_fields


def test_nidp_audit_operations_are_registered_and_safe() -> None:
    assert NIDP_AUDIT_OPERATIONS <= WAVE053_AUDIT_OPERATIONS
    for operation in sorted(NIDP_AUDIT_OPERATIONS):
        event = nidp_audit_event(
            operation=operation,
            actor_id="officer-1",
            purpose="TREATMENT",
            organization_id="ORG-SYNTHETIC",
            facility_id="FACILITY-SYNTHETIC",
            gula_citizen_identifier=SYNTHETIC_GULA_ID,
            national_id_hash=SYNTHETIC_HASH,
            correlation_id=CORRELATION_ID,
            evidence_reference="SYNTHETIC-EVIDENCE-0001",
        )
        assert event.action == operation.lower()
        assert SYNTHETIC_NID not in repr(event)


def test_capture_audit_metadata_records_required_session_fields() -> None:
    evidence = _evidence()
    event = nidp_audit_event(
        operation=LIVE_CAPTURE_COMPLETED,
        actor_id="officer-1",
        purpose="TREATMENT",
        organization_id="ORG-SYNTHETIC",
        facility_id="FACILITY-SYNTHETIC",
        gula_citizen_identifier=SYNTHETIC_GULA_ID,
        national_id_hash=SYNTHETIC_HASH,
        correlation_id=CORRELATION_ID,
        evidence_reference="SYNTHETIC-EVIDENCE-0002",
        capture=evidence.capture,
        decision=evaluate_document_authenticity(evidence),
    )
    metadata = event.metadata
    assert metadata["capture_session_id"] == "SYNTHETIC-SESSION-0001"
    assert metadata["capture_method"] == LiveCaptureMethod.SERVER_CHALLENGE_LIVE_CAMERA.value
    assert metadata["capture_source"] == LiveCaptureSource.AUTHORIZED_LIVE_CAMERA_SESSION.value
    assert metadata["capture_outcome"] == LiveCaptureOutcome.COMPLETED.value
    assert metadata["device_capabilities"]["nfc_supported"] is True
    assert metadata["document_authenticity_state"] == (
        DocumentAuthenticityState.DOCUMENT_REVIEW_REQUIRED.value
    )
    assert SYNTHETIC_NID not in repr(event)


def test_audit_builder_rejects_full_national_id_in_evidence_reference() -> None:
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        nidp_audit_event(
            operation="DOCUMENT_REVIEW",
            actor_id="reviewer-1",
            purpose="TREATMENT",
            organization_id="ORG-SYNTHETIC",
            facility_id="FACILITY-SYNTHETIC",
            gula_citizen_identifier=SYNTHETIC_GULA_ID,
            national_id_hash=SYNTHETIC_HASH,
            correlation_id=CORRELATION_ID,
            evidence_reference=SYNTHETIC_NID,
        )


def test_evidence_correlation_ids_must_match_across_boundaries() -> None:
    evidence = _evidence()
    inspection = VisualInspection(
        inspector_id="officer-1",
        organization_id="ORG-SYNTHETIC",
        facility_id="FACILITY-SYNTHETIC",
        purpose="TREATMENT",
        correlation_id="CORR-SYNTHETIC-DIFFERENT",
        inspected_at=NOW,
        evidence_reference="SYNTHETIC-INSPECTION-0002",
    )
    from dataclasses import replace

    with pytest.raises(DocumentAuthenticityError, match="share one correlation id"):
        replace(evidence, visual_inspection=inspection)
