"""Wave 05.2 national identity governance tests.

Synthetic values only. These tests pin reversible domain behavior without
government access, NFC/card keys, external OCR, real citizen data, DDL, routes,
or verification claims.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from random import Random

import pytest
from app._compat import UTC
from app.identity.services.authorization_decision import AuthorizationDecision, AuthorizationReason
from app.national.exceptions import (
    GulaCitizenIdentifierCollisionError,
    GulaCitizenIdentifierExhaustedError,
    InvalidGulaCitizenIdentifierError,
)
from app.national.services import citizen_service as citizen_service_module
from app.national.services.citizen_service import (
    assert_gula_citizen_identifier_format,
    assert_gula_citizen_identifier_immutable,
    generate_gula_citizen_identifier,
)
from app.national.services.identity_governance import (
    CARD_EXPIRED,
    DATA_EXTRACTED,
    DOCUMENT_AUTHENTICITY_CONFIRMED,
    DOCUMENT_CHECKED,
    EXPIRED,
    EXTRACTION_COMPLETED,
    GOVERNMENT_SOURCE_CONFIRMED,
    GOVERNMENT_VERIFIED,
    IDENTITY_AUDIT_OPERATIONS,
    IDENTITY_DECISION_APPROVED,
    MODIFY,
    PENDING_REVIEW,
    READ,
    REVIEW,
    REVIEW_APPROVED,
    REVIEW_REQUIRED,
    ROLLBACK,
    SOURCE_AUTHORIZED_REVIEWER,
    SOURCE_CARD_NFC,
    SOURCE_CARD_OCR,
    SOURCE_CITIZEN_ATTESTATION,
    SOURCE_OFFICIAL_GOVERNMENT,
    UNVERIFIED,
    VERIFIED,
    VERIFY,
    CitizenAttestation,
    ExtractedField,
    ExtractionComparison,
    IdentityAccessDeniedError,
    IdentityEvidenceError,
    IdentityTransitionError,
    LinkageCandidate,
    LinkageDecision,
    LinkageReviewer,
    UnifiedCitizenIdentity,
    VerificationTransitionContext,
    append_identity_correction,
    append_linkage_rollback,
    assert_identity_access_allowed,
    assert_linkage_allowed,
    assert_no_full_national_identifier,
    build_identity_audit_event,
    build_national_id_evidence,
    build_residence_record,
    card_validity_event,
    classify_card_extraction,
    mask_national_id,
    protect_national_id_for_storage,
    safe_identity_log_context,
    transition_verification_state,
)
from app.services.identity import hash_national_id
from cryptography.fernet import Fernet

from shared.security.encryption import decrypt_national_id

NOW = datetime(2026, 11, 25, tzinfo=UTC)
SYNTHETIC_NID = "000000000001"  # obviously synthetic test value, not a real NID
SYNTHETIC_GULA_ID = "199000000001"
SYNTHETIC_GOVERNMENT_AUTHORITY = "SYNTHETIC_GOVERNMENT_SOURCE"
SYNTHETIC_DOCUMENT_AUTHORITY = "SYNTHETIC_DOCUMENT_AUTHENTICITY"


def _reserve_all() -> tuple:
    return set()


def _card_ocr(**overrides) -> dict[str, ExtractedField]:
    base = {
        "national_id": ExtractedField(SYNTHETIC_NID, SOURCE_CARD_OCR, 0.99, NOW),
        "full_name": ExtractedField("Test Citizen", SOURCE_CARD_OCR, 0.98, NOW),
        "mother_name": ExtractedField("Test Mother", SOURCE_CARD_OCR, 0.97, NOW),
        "birth_date": ExtractedField("1990-01-01", SOURCE_CARD_OCR, 0.99, NOW),
        "family_number": ExtractedField("1000000001", SOURCE_CARD_OCR, 0.96, NOW),
        "birth_place": ExtractedField("Baghdad", SOURCE_CARD_OCR, 0.95, NOW),
        "card_issue_date": ExtractedField("2020-01-01", SOURCE_CARD_OCR, 0.98, NOW),
        "card_expiry_date": ExtractedField("2030-01-01", SOURCE_CARD_OCR, 0.98, NOW),
    }
    base.update(overrides)
    return base


def _card_nfc(**overrides) -> dict[str, ExtractedField]:
    base = {
        "national_id": ExtractedField(SYNTHETIC_NID, SOURCE_CARD_NFC, 1.0, NOW),
        "full_name": ExtractedField("Test Citizen", SOURCE_CARD_NFC, 1.0, NOW),
        "mother_name": ExtractedField("Test Mother", SOURCE_CARD_NFC, 1.0, NOW),
        "birth_date": ExtractedField("1990-01-01", SOURCE_CARD_NFC, 1.0, NOW),
        "family_number": ExtractedField("1000000001", SOURCE_CARD_NFC, 1.0, NOW),
        "birth_place": ExtractedField("Baghdad", SOURCE_CARD_NFC, 1.0, NOW),
        "card_issue_date": ExtractedField("2020-01-01", SOURCE_CARD_NFC, 1.0, NOW),
        "card_expiry_date": ExtractedField("2030-01-01", SOURCE_CARD_NFC, 1.0, NOW),
    }
    base.update(overrides)
    return base


def _identity(**overrides) -> UnifiedCitizenIdentity:
    base = {
        "gula_citizen_identifier": SYNTHETIC_GULA_ID,
        "national_id_hash": hash_national_id(SYNTHETIC_NID),
        "masked_national_id": mask_national_id(SYNTHETIC_NID),
        "full_name": "Test Citizen",
        "mother_name": "Test Mother",
        "birth_date": "1990-01-01",
        "family_number": "1000000001",
        "birth_place": "Baghdad",
        "card_issue_date": "2020-01-01",
        "card_expiry_date": "2030-01-01",
        "verification_state": DATA_EXTRACTED,
    }
    base.update(overrides)
    return UnifiedCitizenIdentity(**base)


def _candidate(citizen_id: str, nid_hash: str | None, **overrides) -> LinkageCandidate:
    base = {
        "id": citizen_id,
        "nid_hash": nid_hash,
        "nid_verified": True,
        "birth_year": 1990,
        "birth_month": 1,
        "birth_day": 1,
        "phone_last10": "0000000001",
        "family_id_hash": "family-a",
        "status": "active",
    }
    base.update(overrides)
    return LinkageCandidate(**base)


def _reviewer() -> LinkageReviewer:
    return LinkageReviewer(name="synthetic-reviewer", user_id=4242)


# --- GULA Citizen Identifier -------------------------------------------------


def test_identifier_format_and_birth_year_prefix() -> None:
    identifier = generate_gula_citizen_identifier(
        birth_year=1990,
        reserve=lambda _candidate: True,
        random_source=lambda: 42,
    )
    assert identifier == "199000000042"
    assert_gula_citizen_identifier_format(identifier)


def test_identifier_uses_module_csprng_by_default(monkeypatch) -> None:
    monkeypatch.setattr(citizen_service_module.secrets, "randbelow", lambda _n: 7)
    identifier = generate_gula_citizen_identifier(birth_year=2001, reserve=lambda _candidate: True)
    assert identifier == "200100000007"


def test_identifier_retries_after_atomic_collision() -> None:
    values = iter([0, 0, 0, 1])
    calls: list[str] = []

    def reserve(candidate: str) -> bool:
        calls.append(candidate)
        if candidate.endswith("00000000"):
            raise GulaCitizenIdentifierCollisionError(candidate)
        return True

    identifier = generate_gula_citizen_identifier(
        birth_year=1988,
        reserve=reserve,
        max_attempts=5,
        random_source=lambda: next(values),
    )
    assert identifier == "198800000001"
    assert len(calls) == 4


def test_identifier_exhausts_after_bounded_attempts() -> None:
    with pytest.raises(GulaCitizenIdentifierExhaustedError):
        generate_gula_citizen_identifier(
            birth_year=2000,
            reserve=lambda _candidate: False,
            max_attempts=3,
            random_source=lambda: 1,
        )


def test_identifier_concurrent_reservations_are_unique() -> None:
    reserved: set[str] = set()
    lock = threading.Lock()

    def reserve(candidate: str) -> bool:
        with lock:
            if candidate in reserved:
                raise GulaCitizenIdentifierCollisionError(candidate)
            reserved.add(candidate)
            return True

    with ThreadPoolExecutor(max_workers=32) as pool:
        identifiers = list(
            pool.map(
                lambda _: generate_gula_citizen_identifier(birth_year=1995, reserve=reserve),
                range(256),
            )
        )

    assert len(identifiers) == 256
    assert len(set(identifiers)) == 256
    assert reserved == set(identifiers)


def test_identifier_simulation_one_million_generations() -> None:
    """Million-scale deterministic simulation with collision retry."""
    rng = Random(20261125)
    reserved: set[str] = set()

    def reserve(candidate: str) -> bool:
        if candidate in reserved:
            raise GulaCitizenIdentifierCollisionError(candidate)
        reserved.add(candidate)
        return True

    identifiers = [
        generate_gula_citizen_identifier(
            birth_year=1999,
            reserve=reserve,
            max_attempts=20,
            random_source=lambda: rng.randrange(100_000_000),
        )
        for _ in range(1_000_000)
    ]
    assert len(set(identifiers)) == 1_000_000
    assert all(identifier.startswith("1999") for identifier in identifiers)


def test_identifier_immutable_after_dob_correction() -> None:
    corrected = append_identity_correction(
        _identity(),
        field_name="birth_date",
        new_value="1990-01-02",
        source=SOURCE_AUTHORIZED_REVIEWER,
        actor="synthetic-reviewer",
        reason="synthetic demographic correction",
        changed_at=NOW,
    )
    assert corrected.birth_date == "1990-01-02"
    assert corrected.gula_citizen_identifier == SYNTHETIC_GULA_ID
    assert_gula_citizen_identifier_immutable(
        SYNTHETIC_GULA_ID, corrected.gula_citizen_identifier
    )
    with pytest.raises(InvalidGulaCitizenIdentifierError):
        assert_gula_citizen_identifier_immutable(SYNTHETIC_GULA_ID, "200000000001")


def test_correction_history_is_append_only() -> None:
    original = _identity()
    corrected = append_identity_correction(
        original,
        field_name="mother_name",
        new_value="Corrected Mother",
        source="authorized_reviewer",
        actor="synthetic-reviewer",
        reason="synthetic correction",
        changed_at=NOW,
    )
    assert original.mother_name == "Test Mother"
    assert original.corrections == ()
    assert corrected.mother_name == "Corrected Mother"
    assert len(corrected.corrections) == 1
    assert corrected.corrections[0].old_value == "Test Mother"
    assert corrected.corrections[0].new_value == "Corrected Mother"
    with pytest.raises(IdentityEvidenceError):
        append_identity_correction(
            original,
            field_name="gula_citizen_identifier",
            new_value="200000000001",
            source="authorized_reviewer",
            actor="synthetic-reviewer",
            reason="must not change",
            changed_at=NOW,
        )


@pytest.mark.parametrize("bad", ["", "123", "abcdefghijkl", "19900000000a"])
def test_invalid_identifier_shapes_rejected(bad: str) -> None:
    with pytest.raises(InvalidGulaCitizenIdentifierError):
        assert_gula_citizen_identifier_format(bad)


# --- Extraction, provenance and states ---------------------------------------


def test_card_extraction_agreement_routes_to_extracted() -> None:
    comparison = classify_card_extraction(_card_ocr(), _card_nfc())
    assert isinstance(comparison, ExtractionComparison)
    assert comparison.recommended_event == EXTRACTION_COMPLETED
    assert comparison.conflicts == ()
    assert comparison.uncertain_fields == ()
    assert comparison.missing_fields == ()
    assert len(comparison.agreements) == 8


def test_unclear_ocr_routes_to_review() -> None:
    ocr = _card_ocr(full_name=ExtractedField("Test Citizen", SOURCE_CARD_OCR, 0.42, NOW))
    comparison = classify_card_extraction(ocr, _card_nfc())
    assert comparison.recommended_event == REVIEW_REQUIRED
    assert any(item.field == "full_name" for item in comparison.uncertain_fields)


def test_ocr_nfc_mismatch_routes_to_review() -> None:
    ocr = _card_ocr(national_id=ExtractedField("000000000002", SOURCE_CARD_OCR, 0.99, NOW))
    comparison = classify_card_extraction(ocr, _card_nfc())
    assert comparison.recommended_event == REVIEW_REQUIRED
    assert any(item.field == "national_id" for item in comparison.conflicts)


def test_nfc_failure_routes_to_review() -> None:
    comparison = classify_card_extraction(_card_ocr(), {})
    assert comparison.recommended_event == REVIEW_REQUIRED
    assert comparison.uncertain_fields
    assert all(item.missing for item in comparison.uncertain_fields)


def test_incomplete_card_routes_to_review() -> None:
    ocr = _card_ocr()
    nfc = _card_nfc()
    del ocr["mother_name"]
    del nfc["mother_name"]
    comparison = classify_card_extraction(ocr, nfc)
    assert comparison.recommended_event == REVIEW_REQUIRED
    assert any(item.field == "mother_name" for item in comparison.missing_fields)


def test_expired_card_routes_to_expired_state() -> None:
    assert card_validity_event("2020-01-01", now=NOW) == CARD_EXPIRED
    assert card_validity_event("2030-01-01", now=NOW) is None
    assert (
        transition_verification_state(DATA_EXTRACTED, CARD_EXPIRED) == EXPIRED
    )


def test_document_checked_is_not_government_verified() -> None:
    checked = transition_verification_state(
        DATA_EXTRACTED,
        DOCUMENT_AUTHENTICITY_CONFIRMED,
        context=VerificationTransitionContext(
            document_authority=SYNTHETIC_DOCUMENT_AUTHORITY,
            evidence_reference="SYNTHETIC-DOC-EVIDENCE",
        ),
        allowed_document_authorities=frozenset({SYNTHETIC_DOCUMENT_AUTHORITY}),
    )
    assert checked == DOCUMENT_CHECKED
    assert checked != GOVERNMENT_VERIFIED
    with pytest.raises(IdentityTransitionError):
        transition_verification_state(
            checked,
            IDENTITY_DECISION_APPROVED,
            context=VerificationTransitionContext(citizen_confirmation=True, reviewer="r", reason="x"),
        )


def test_government_transition_denies_unapproved_authority_by_default() -> None:
    context = VerificationTransitionContext(
        government_authority=SYNTHETIC_GOVERNMENT_AUTHORITY,
        government_operation_id="SYNTHETIC-OP",
        evidence_reference="SYNTHETIC-GOV-EVIDENCE",
    )
    with pytest.raises(IdentityTransitionError):
        transition_verification_state(DATA_EXTRACTED, GOVERNMENT_SOURCE_CONFIRMED, context=context)

    assert (
        transition_verification_state(
            DATA_EXTRACTED,
            GOVERNMENT_SOURCE_CONFIRMED,
            context=context,
            allowed_government_authorities=frozenset({SYNTHETIC_GOVERNMENT_AUTHORITY}),
        )
        == GOVERNMENT_VERIFIED
    )


def test_review_transitions_require_named_reviewer_and_reason() -> None:
    with pytest.raises(IdentityTransitionError):
        transition_verification_state(DATA_EXTRACTED, REVIEW_REQUIRED)

    assert (
        transition_verification_state(
            DATA_EXTRACTED,
            REVIEW_REQUIRED,
            context=VerificationTransitionContext(reason="synthetic conflict"),
        )
        == PENDING_REVIEW
    )
    with pytest.raises(IdentityTransitionError):
        transition_verification_state(
            PENDING_REVIEW,
            REVIEW_APPROVED,
            context=VerificationTransitionContext(reason="synthetic reason"),
        )
    assert (
        transition_verification_state(
            PENDING_REVIEW,
            REVIEW_APPROVED,
            context=VerificationTransitionContext(
                reviewer="synthetic-reviewer", reason="synthetic approved review"
            ),
        )
        == VERIFIED
    )


def test_final_identity_decision_requires_citizen_confirmation() -> None:
    with pytest.raises(IdentityTransitionError):
        transition_verification_state(
            GOVERNMENT_VERIFIED,
            IDENTITY_DECISION_APPROVED,
            context=VerificationTransitionContext(reviewer="r", reason="x"),
        )
    assert (
        transition_verification_state(
            GOVERNMENT_VERIFIED,
            IDENTITY_DECISION_APPROVED,
            context=VerificationTransitionContext(
                reviewer="synthetic-reviewer",
                reason="synthetic final decision",
                citizen_confirmation=True,
            ),
        )
        == VERIFIED
    )


def test_national_id_evidence_never_retains_raw_value() -> None:
    official = build_national_id_evidence(
        SYNTHETIC_NID,
        source=SOURCE_OFFICIAL_GOVERNMENT,
        captured_at=NOW,
    )
    card = build_national_id_evidence(
        SYNTHETIC_NID,
        source=SOURCE_CARD_OCR,
        captured_at=NOW,
        confidence=0.99,
    )
    assert official.source != card.source
    assert official.national_id_hash == card.national_id_hash
    assert official.is_verification_authority is False
    assert card.is_verification_authority is False
    assert SYNTHETIC_NID not in repr(official)
    assert SYNTHETIC_NID not in repr(card)


def test_unicode_nid_digits_normalize_to_same_hash() -> None:
    arabic_synthetic = "\u0660" * 11 + "\u0661"
    assert hash_national_id(arabic_synthetic) == hash_national_id(SYNTHETIC_NID)


def test_citizen_attestation_does_not_grant_verified() -> None:
    identity = _identity(verification_state=DATA_EXTRACTED)
    attestation = CitizenAttestation(
        confirmed_by="synthetic-citizen",
        confirmed_at=NOW,
        fields_confirmed=("full_name", "birth_date"),
    )
    assert identity.verification_state == DATA_EXTRACTED
    assert attestation.confirmed_by == "synthetic-citizen"
    assert identity.verification_state != VERIFIED


def test_public_identity_view_is_masked() -> None:
    public = _identity().to_public_dict()
    assert public["masked_national_id"] == mask_national_id(SYNTHETIC_NID)
    assert SYNTHETIC_NID not in repr(public)
    assert "national_id_hash" not in public


def test_residence_requires_enabled_flag_and_is_not_government_trusted() -> None:
    with pytest.raises(IdentityEvidenceError):
        build_residence_record(
            value="Synthetic Street 1",
            source="citizen_entered",
            valid_from=date(2026, 1, 1),
            valid_until=None,
            updated_at=NOW,
            enabled=False,
        )
    residence = build_residence_record(
        value="Synthetic Street 1",
        source="citizen_entered",
        valid_from=date(2026, 1, 1),
        valid_until=date(2027, 1, 1),
        updated_at=NOW,
        enabled=True,
    )
    assert residence.citizen_entered is True
    assert residence.verification_state == UNVERIFIED
    assert residence.source == "citizen_entered"
    assert residence.updated_at == NOW
    independent = build_residence_record(
        value="Synthetic Street 2",
        source="independent_verification",
        valid_from=date(2026, 1, 1),
        valid_until=None,
        updated_at=NOW,
        enabled=True,
    )
    assert independent.verification_state == UNVERIFIED


# --- Linkage safety ----------------------------------------------------------


def test_duplicate_nid_review_gate() -> None:
    primary = _candidate("primary", "hash-a")
    secondary = _candidate("secondary", "hash-b")
    with pytest.raises(IdentityEvidenceError, match="conflicting"):
        assert_linkage_allowed(
            primary,
            secondary,
            decision="APPROVED",
            reviewer=_reviewer(),
            reason="synthetic review",
            evidence_reference="SYNTHETIC-EVIDENCE",
        )


def test_no_name_only_merge_without_review_evidence() -> None:
    primary = _candidate("primary", None, nid_verified=False)
    secondary = _candidate("secondary", None, nid_verified=False)
    with pytest.raises(IdentityEvidenceError, match="evidence reference"):
        assert_linkage_allowed(
            primary,
            secondary,
            decision="APPROVED",
            reviewer=_reviewer(),
            reason="names look similar",
            evidence_reference="",
        )


def test_linkage_requires_explicit_approval_and_reviewer() -> None:
    primary = _candidate("primary", "hash-a")
    secondary = _candidate("secondary", "hash-a")
    with pytest.raises(IdentityEvidenceError, match="explicit approval"):
        assert_linkage_allowed(
            primary,
            secondary,
            decision="AUTO",
            reviewer=_reviewer(),
            reason="synthetic",
            evidence_reference="SYNTHETIC-EVIDENCE",
        )
    with pytest.raises(IdentityEvidenceError, match="named reviewer"):
        assert_linkage_allowed(
            primary,
            secondary,
            decision="APPROVED",
            reviewer=LinkageReviewer(name="", user_id=None),
            reason="synthetic",
            evidence_reference="SYNTHETIC-EVIDENCE",
        )


def test_approved_rollback_preserves_original_decision() -> None:
    decision = LinkageDecision(
        primary_identifier="primary",
        secondary_identifier="secondary",
        reviewer=_reviewer(),
        reason="synthetic approved linkage",
        evidence_reference="SYNTHETIC-EVIDENCE",
        decided_at=NOW,
    )
    rolled_back = append_linkage_rollback(
        decision,
        reviewer=_reviewer(),
        reason="synthetic approved rollback",
        rolled_back_at=NOW,
    )
    assert decision.active is True
    assert decision.rollback is None
    assert rolled_back.active is False
    assert rolled_back.rollback is not None
    assert rolled_back.rollback.reviewer.name == "synthetic-reviewer"
    assert decision.to_audit_metadata()["active"] is True
    assert rolled_back.to_audit_metadata()["rolled_back"] is True
    with pytest.raises(IdentityEvidenceError):
        append_linkage_rollback(
            rolled_back,
            reviewer=_reviewer(),
            reason="again",
            rolled_back_at=NOW,
        )


# --- Privacy, access and audit -----------------------------------------------


def test_unauthorized_identity_access_fails_closed() -> None:
    denied = AuthorizationDecision.deny(AuthorizationReason.permission_missing)
    with pytest.raises(IdentityAccessDeniedError):
        assert_identity_access_allowed(
            decision=denied,
            action=READ,
            purpose="TREATMENT",
            facility_id="synthetic-facility",
        )


def test_authorized_access_still_requires_purpose_and_facility() -> None:
    allowed = AuthorizationDecision.allow()
    assert_identity_access_allowed(
        decision=allowed,
        action=READ,
        purpose="TREATMENT",
        facility_id="synthetic-facility",
    )
    with pytest.raises(IdentityAccessDeniedError):
        assert_identity_access_allowed(
            decision=allowed,
            action=READ,
            purpose="NOT_AN_APPROVED_PURPOSE",
            facility_id="synthetic-facility",
        )
    with pytest.raises(IdentityAccessDeniedError):
        assert_identity_access_allowed(
            decision=allowed,
            action=READ,
            purpose="TREATMENT",
            facility_id="",
        )


def test_national_id_log_leakage_is_blocked() -> None:
    context = safe_identity_log_context(
        gula_citizen_identifier=SYNTHETIC_GULA_ID,
        national_id_hash=hash_national_id(SYNTHETIC_NID),
        masked_national_id=mask_national_id(SYNTHETIC_NID),
        free_text=f"synthetic national id {SYNTHETIC_NID}",
        raw_nid_for_check=SYNTHETIC_NID,
    )
    assert SYNTHETIC_NID not in repr(context)
    with pytest.raises(IdentityEvidenceError):
        safe_identity_log_context(
            gula_citizen_identifier=SYNTHETIC_NID,
            national_id_hash=hash_national_id(SYNTHETIC_NID),
            masked_national_id=mask_national_id(SYNTHETIC_NID),
            raw_nid_for_check=SYNTHETIC_NID,
        )
    with pytest.raises(IdentityEvidenceError):
        assert_no_full_national_identifier(f"nid={SYNTHETIC_NID}", SYNTHETIC_NID)


def test_identity_audit_covers_all_required_operations() -> None:
    assert frozenset(
        {READ, MODIFY, "EXPORT", VERIFY, REVIEW, "MERGE", ROLLBACK}
    ) == IDENTITY_AUDIT_OPERATIONS
    for operation in IDENTITY_AUDIT_OPERATIONS:
        event = build_identity_audit_event(
            operation=operation,
            actor_id="synthetic-actor",
            purpose="TREATMENT",
            facility_id="synthetic-facility",
            gula_citizen_identifier=SYNTHETIC_GULA_ID,
            national_id_hash=hash_national_id(SYNTHETIC_NID),
            raw_nid_for_check=SYNTHETIC_NID,
        )
        assert event.event_type == "IDENTITY_OPERATION"
        assert event.action == operation.lower()
        assert event.metadata["operation"] == operation
        assert event.target_id == SYNTHETIC_GULA_ID
        assert SYNTHETIC_NID not in repr(event)


def test_human_review_audit_is_recorded() -> None:
    event = build_identity_audit_event(
        operation=REVIEW,
        actor_id="synthetic-reviewer",
        purpose="AUDIT",
        facility_id="synthetic-facility",
        gula_citizen_identifier=SYNTHETIC_GULA_ID,
        national_id_hash=hash_national_id(SYNTHETIC_NID),
        metadata={"reviewer": "synthetic-reviewer", "reason": "OCR/NFC conflict"},
        decision="PENDING_REVIEW",
        reason_code="OCR_NFC_CONFLICT",
        raw_nid_for_check=SYNTHETIC_NID,
    )
    assert event.metadata["reviewer"] == "synthetic-reviewer"
    assert event.metadata["reason"] == "OCR/NFC conflict"
    assert event.decision == "PENDING_REVIEW"
    assert event.reason_code == "OCR_NFC_CONFLICT"
    with pytest.raises(IdentityEvidenceError):
        build_identity_audit_event(
            operation=MODIFY,
            actor_id="synthetic-actor",
            purpose="TREATMENT",
            facility_id="synthetic-facility",
            gula_citizen_identifier=SYNTHETIC_GULA_ID,
            national_id_hash=hash_national_id(SYNTHETIC_NID),
            metadata={"raw_national_id": SYNTHETIC_NID},
        )


def test_encrypted_nid_envelope_uses_external_keys() -> None:
    encryption_key = Fernet.generate_key().decode()
    hmac_key = "synthetic-hmac-key"
    envelope = protect_national_id_for_storage(
        SYNTHETIC_NID,
        encryption_key=encryption_key,
        hmac_key=hmac_key,
    )
    assert SYNTHETIC_NID not in repr(envelope)
    assert envelope.national_id_hash == hash_national_id(SYNTHETIC_NID)
    assert decrypt_national_id(envelope.encrypted_token, encryption_key, hmac_key) == SYNTHETIC_NID
