"""Synthetic citizen account registration lifecycle tests.

Covers the staged boundary authorized after Wave 05.3 closure. All values are
synthetic. No DDL, route, government connection, card image, raw NFC payload,
real identity number, or production account state is used.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pytest
from app._compat import UTC
from app.identity.services.authorization_decision import (
    AuthorizationDecision,
    AuthorizationReason,
)
from app.national.services.citizen_registration import (
    ActorType,
    CitizenRegistrationError,
    InMemoryRegistrationAccountStore,
    InvalidRegistrationTransitionError,
    MedicalDataAccessDeniedError,
    RegistrationAuthorizationError,
    RegistrationContext,
    RegistrationLifecycleState,
    activate_service,
    approve_health_identity,
    assert_medical_data_access_allowed,
    assert_single_initial_account,
    create_initial_account,
    project_registration_status,
    submit_national_identity,
    verify_contact,
)
from app.national.services.document_authenticity import (
    CaptureSessionRegistry,
    DeviceCapabilityMetadata,
    DocumentAuthenticityError,
    LiveCaptureSession,
    NfcReadOutcome,
    NfcState,
    NidpEvidenceBundle,
    OriginalCardPresentation,
    OriginalDocumentChannel,
    RegistrationEligibilityState,
    RegistrationPath,
    RejectionClassification,
    VisualInspection,
    assert_identity_verification_blocked,
    assert_no_manual_authenticity_override,
    evaluate_document_authenticity,
    registration_eligibility,
)
from app.national.services.identity_access import (
    IdentityRole,
    build_wave053_audit_event,
)
from app.national.services.identity_governance import (
    IdentityEvidenceError,
    LinkageCandidate,
    LinkageReviewer,
)
from app.national.services.identity_persistence import (
    InMemoryIdempotencyStore,
    RegistrationInProgressError,
    RegistrationRequest,
)

NOW = datetime(2026, 11, 25, 12, 0, 0, tzinfo=UTC)
SYNTHETIC_HASH = "b" * 64
CORRELATION_ID = "CORR-SYNTHETIC-0001"


def _context(**overrides) -> RegistrationContext:
    values = {
        "decision": AuthorizationDecision.allow(),
        "actor_id": "officer-1",
        "actor_type": ActorType.CITIZEN,
        "organization_id": "ORG-SYNTHETIC",
        "facility_id": "FACILITY-SYNTHETIC",
        "purpose": "citizen_workspace",
        "now": NOW,
        "role": None,
        "correlation_id": CORRELATION_ID,
        "national_id_hash": SYNTHETIC_HASH,
    }
    values.update(overrides)
    return RegistrationContext(**values)


def _staff_context(**overrides) -> RegistrationContext:
    return _context(
        purpose="ADMINISTRATION",
        actor_type=ActorType.STAFF,
        role=IdentityRole.IDENTITY_REVIEWER,
        **overrides,
    )


def _request(key: str = "idem-0001", subject: str = "SUBJ-SYNTHETIC-0001") -> RegistrationRequest:
    return RegistrationRequest(
        idempotency_key=key,
        subject_reference=subject,
        birth_year=1990,
        requested_at=NOW,
    )


def _capture(nfc_supported: bool) -> LiveCaptureSession:
    registry = CaptureSessionRegistry()
    challenge = registry.issue(
        session_id="SESSION-SYNTHETIC-0001",
        actor_id="officer-1",
        organization_id="ORG-SYNTHETIC",
        facility_id="FACILITY-SYNTHETIC",
        purpose="citizen_workspace",
        correlation_id=CORRELATION_ID,
        device_capabilities=DeviceCapabilityMetadata(
            nfc_supported=nfc_supported,
            camera_available=True,
        ),
        at=NOW,
        nonce="a" * 32,
    )
    return registry.complete(
        challenge,
        front_evidence_reference="SYNTHETIC-FRONT-0001",
        back_evidence_reference="SYNTHETIC-BACK-0001",
        captured_at=NOW + timedelta(seconds=1),
    )


def _presentation() -> OriginalCardPresentation:
    return OriginalCardPresentation(
        channel=OriginalDocumentChannel.AUTHORIZED_LIVE_CAMERA_SESSION,
        actor_id="officer-1",
        organization_id="ORG-SYNTHETIC",
        facility_id="FACILITY-SYNTHETIC",
        purpose="citizen_workspace",
        correlation_id=CORRELATION_ID,
        presented_at=NOW,
        evidence_reference="SYNTHETIC-ORIGINAL-0001",
        physical_presented=True,
    )


def _inspection() -> VisualInspection:
    return VisualInspection(
        inspector_id="officer-1",
        organization_id="ORG-SYNTHETIC",
        facility_id="FACILITY-SYNTHETIC",
        purpose="citizen_workspace",
        correlation_id=CORRELATION_ID,
        inspected_at=NOW + timedelta(seconds=2),
        evidence_reference="SYNTHETIC-INSPECTION-0001",
        security_features_observed=("synthetic-feature-a",),
    )


def _evidence(
    *,
    path: RegistrationPath = RegistrationPath.IN_PERSON_OFFICER,
    nfc_supported: bool = False,
    official_nfc_reading_documented: bool = True,
    authenticity_checks_completed: bool = True,
    authorized_officer_reviewed: bool = True,
    central_workflow_recorded: bool = True,
    rejection: RejectionClassification | None = None,
) -> NidpEvidenceBundle:
    nfc = None
    if path is RegistrationPath.HOME_NFC:
        nfc = NfcReadOutcome(
            state=NfcState.NFC_READ_SUCCESSFULLY,
            read_at=NOW + timedelta(seconds=3),
            evidence_reference="SYNTHETIC-NFC-0001",
        )
    return NidpEvidenceBundle(
        path=path,
        presentation=_presentation(),
        capture=_capture(nfc_supported=nfc_supported),
        visual_inspection=_inspection(),
        nfc=nfc,
        rejection=rejection,
        official_nfc_reading_documented=official_nfc_reading_documented,
        authenticity_checks_completed=authenticity_checks_completed,
        authorized_officer_reviewed=authorized_officer_reviewed,
        central_workflow_recorded=central_workflow_recorded,
    )


def _initial_account():
    idempotency_store = InMemoryIdempotencyStore()
    account_store = InMemoryRegistrationAccountStore()
    account = create_initial_account(
        request=_request(),
        idempotency_store=idempotency_store,
        account_store=account_store,
        context=_context(),
        contact_reference="CONTACT-SYNTHETIC-0001",
    )
    return idempotency_store, account_store, account


def _contact_verified_account():
    idempotency_store, account_store, account = _initial_account()
    verified = verify_contact(
        account=account,
        contact_code="123456",
        context=_context(),
        account_store=account_store,
    )
    return idempotency_store, account_store, verified


def _reviewed_account(**evidence_kwargs):
    idempotency_store, account_store, account = _contact_verified_account()
    reviewed = submit_national_identity(
        account=account,
        evidence=_evidence(**evidence_kwargs),
        context=_context(),
        account_store=account_store,
    )
    return idempotency_store, account_store, reviewed


def _linkage_candidates():
    primary = LinkageCandidate(
        id="199000000001",
        status="active",
        birth_year=1990,
        birth_month=1,
        birth_day=2,
        phone_last10="0000000001",
    )
    secondary = LinkageCandidate(
        id="198000000002",
        status="active",
        birth_year=1990,
        birth_month=1,
        birth_day=2,
        phone_last10="0000000001",
    )
    return primary, secondary


# Phase 1 architecture-boundary tests (run before implementation gating).


def test_phase1_non_nfc_eligibility_never_verifies() -> None:
    evidence = _evidence(path=RegistrationPath.IN_PERSON_OFFICER, nfc_supported=False)
    decision = evaluate_document_authenticity(evidence)
    eligibility = registration_eligibility(evidence, decision)
    assert eligibility.identity_verified is False
    assert eligibility.state is RegistrationEligibilityState.IDENTITY_VERIFICATION_INCOMPLETE


def test_phase1_manual_override_to_verified_is_rejected() -> None:
    with pytest.raises(DocumentAuthenticityError, match="manual authenticity override"):
        assert_no_manual_authenticity_override("VERIFIED")


def test_phase1_synthetic_government_verification_cannot_activate() -> None:
    decision = evaluate_document_authenticity(_evidence())
    with pytest.raises(DocumentAuthenticityError, match="synthetic government verification"):
        assert_identity_verification_blocked(decision, synthetic_government_verified=True)


def test_phase1_audit_builder_rejects_raw_national_identifier() -> None:
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        build_wave053_audit_event(
            operation="IDENTITY_CREATED",
            actor_id="officer-1",
            purpose="citizen_workspace",
            facility_id="FACILITY-SYNTHETIC",
            organization_id="ORG-SYNTHETIC",
            gula_citizen_identifier="199000000001",
            national_id_hash=SYNTHETIC_HASH,
            metadata={"note": "000000000001"},
            raw_nid_for_check="000000000001",
        )


# Phase 2/3 lifecycle tests.


def test_initial_account_created_without_nfc_or_medical_access() -> None:
    _, account_store, account = _initial_account()
    assert account.lifecycle_state is RegistrationLifecycleState.INITIAL_ACCOUNT
    assert account.verification_state == "UNVERIFIED"
    assert account.can_access_medical_data is False
    assert account_store.get(account.gula_citizen_identifier) == account
    assert "national_id" not in account.to_public_dict()


def test_non_nfc_phone_path_does_not_block_initial_account() -> None:
    idempotency_store = InMemoryIdempotencyStore()
    account_store = InMemoryRegistrationAccountStore()
    account = create_initial_account(
        request=_request(key="idem-non-nfc", subject="SUBJ-SYNTHETIC-NONNFC"),
        idempotency_store=idempotency_store,
        account_store=account_store,
        context=_context(),
        contact_reference="PHONE-SYNTHETIC-0001",
    )
    verified = verify_contact(
        account=account,
        contact_code="654321",
        context=_context(),
        account_store=account_store,
    )
    reviewed = submit_national_identity(
        account=verified,
        evidence=_evidence(path=RegistrationPath.IN_PERSON_OFFICER, nfc_supported=False),
        context=_context(),
        account_store=account_store,
    )
    assert reviewed.lifecycle_state is RegistrationLifecycleState.IDENTITY_REVIEW
    assert reviewed.can_access_medical_data is False


def test_duplicate_submission_creates_one_account() -> None:
    idempotency_store = InMemoryIdempotencyStore()
    account_store = InMemoryRegistrationAccountStore()
    first = create_initial_account(
        request=_request(),
        idempotency_store=idempotency_store,
        account_store=account_store,
        context=_context(),
        contact_reference="CONTACT-SYNTHETIC-0001",
    )
    second = create_initial_account(
        request=_request(),
        idempotency_store=idempotency_store,
        account_store=account_store,
        context=_context(),
        contact_reference="CONTACT-SYNTHETIC-0001",
    )
    assert first.gula_citizen_identifier == second.gula_citizen_identifier
    assert len(account_store.records()) == 1
    assert assert_single_initial_account(
        account_store.records(), "SUBJ-SYNTHETIC-0001",
    ) == first


def test_concurrent_duplicate_submission_is_single_account() -> None:
    idempotency_store = InMemoryIdempotencyStore()
    account_store = InMemoryRegistrationAccountStore()

    def create() -> str:
        try:
            account = create_initial_account(
                request=_request(),
                idempotency_store=idempotency_store,
                account_store=account_store,
                context=_context(),
                contact_reference="CONTACT-SYNTHETIC-0001",
            )
        except RegistrationInProgressError:
            return "IN_PROGRESS"
        return account.gula_citizen_identifier

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: create(), range(2)))
    completed = [value for value in results if value != "IN_PROGRESS"]
    assert completed
    assert len(set(completed)) == 1
    assert len(account_store.records()) == 1


def test_no_activation_before_verification() -> None:
    _, account_store, account = _initial_account()
    with pytest.raises(InvalidRegistrationTransitionError, match="health identity approval"):
        activate_service(
            account=account,
            context=_staff_context(),
            account_store=account_store,
        )


def test_inactive_account_cannot_access_medical_data() -> None:
    _, _, account = _initial_account()
    with pytest.raises(MedicalDataAccessDeniedError, match="fully activated"):
        assert_medical_data_access_allowed(account=account, context=_context())


def test_state_jump_prevention() -> None:
    _, account_store, account = _initial_account()
    with pytest.raises(InvalidRegistrationTransitionError, match="contact verification"):
        submit_national_identity(
            account=account,
            evidence=_evidence(),
            context=_context(),
            account_store=account_store,
        )
    _, account_store, verified = _contact_verified_account()
    primary, secondary = _linkage_candidates()
    with pytest.raises(InvalidRegistrationTransitionError, match="human identity review"):
        approve_health_identity(
            account=verified,
            primary=primary,
            secondary=secondary,
            reviewer=LinkageReviewer(name="reviewer-1", user_id=7),
            reason="synthetic review",
            evidence_reference="SYNTHETIC-REVIEW-0001",
            context=_staff_context(),
            account_store=account_store,
        )


def test_nfc_path_within_approved_specs_routes_to_review_only() -> None:
    _, _, reviewed = _reviewed_account(
        path=RegistrationPath.HOME_NFC,
        nfc_supported=True,
        official_nfc_reading_documented=True,
        authenticity_checks_completed=True,
    )
    assert reviewed.lifecycle_state is RegistrationLifecycleState.IDENTITY_REVIEW
    assert reviewed.verification_state == "PENDING_REVIEW"
    assert reviewed.can_access_medical_data is False


def test_copy_rejection_routes_to_review_without_verification() -> None:
    _, _, reviewed = _reviewed_account(
        path=RegistrationPath.IN_PERSON_OFFICER,
        rejection=RejectionClassification.COPY_PRESENTED,
    )
    assert reviewed.lifecycle_state is RegistrationLifecycleState.IDENTITY_REVIEW
    assert reviewed.verification_state == "PENDING_REVIEW"
    assert reviewed.can_access_medical_data is False


def test_nfc_without_capability_is_rejected() -> None:
    _, account_store, verified = _contact_verified_account()
    with pytest.raises(CitizenRegistrationError, match="NFC-capable device"):
        submit_national_identity(
            account=verified,
            evidence=_evidence(path=RegistrationPath.HOME_NFC, nfc_supported=False),
            context=_context(),
            account_store=account_store,
        )


def test_network_interruption_resume_is_idempotent() -> None:
    _, account_store, reviewed = _reviewed_account()
    resumed = submit_national_identity(
        account=reviewed,
        evidence=_evidence(path=RegistrationPath.IN_PERSON_OFFICER),
        context=_context(),
        account_store=account_store,
    )
    assert resumed == reviewed
    assert len(account_store.records()) == 1


def test_authorized_in_person_review_and_unauthorized_staff_rejection() -> None:
    _, account_store, reviewed = _reviewed_account()
    primary, secondary = _linkage_candidates()
    approved = approve_health_identity(
        account=reviewed,
        primary=primary,
        secondary=secondary,
        reviewer=LinkageReviewer(name="reviewer-1", user_id=7),
        reason="synthetic in-person approval",
        evidence_reference="SYNTHETIC-REVIEW-0001",
        context=_staff_context(),
        account_store=account_store,
    )
    assert approved.lifecycle_state is RegistrationLifecycleState.HEALTH_APPROVED
    assert approved.can_access_medical_data is False

    _, other_store, other_reviewed = _reviewed_account()
    with pytest.raises(RegistrationAuthorizationError, match="named staff role"):
        approve_health_identity(
            account=other_reviewed,
            primary=primary,
            secondary=secondary,
            reviewer=LinkageReviewer(name="reviewer-1", user_id=7),
            reason="unauthorized attempt",
            evidence_reference="SYNTHETIC-REVIEW-0002",
            context=_context(purpose="ADMINISTRATION", role=IdentityRole.LABORATORY_TECHNICIAN),
            account_store=other_store,
        )


def test_canonical_deny_is_not_overridden() -> None:
    idempotency_store = InMemoryIdempotencyStore()
    account_store = InMemoryRegistrationAccountStore()
    with pytest.raises(RegistrationAuthorizationError, match="canonical authorization denied"):
        create_initial_account(
            request=_request(key="idem-denied", subject="SUBJ-SYNTHETIC-DENIED"),
            idempotency_store=idempotency_store,
            account_store=account_store,
            context=_context(
                decision=AuthorizationDecision.deny(AuthorizationReason.permission_missing),
            ),
            contact_reference="CONTACT-SYNTHETIC-DENIED",
        )
    assert account_store.records() == ()


def test_activation_remains_blocked_after_health_approval() -> None:
    _, account_store, reviewed = _reviewed_account()
    primary, secondary = _linkage_candidates()
    approved = approve_health_identity(
        account=reviewed,
        primary=primary,
        secondary=secondary,
        reviewer=LinkageReviewer(name="reviewer-1", user_id=7),
        reason="synthetic approval",
        evidence_reference="SYNTHETIC-REVIEW-0003",
        context=_staff_context(),
        account_store=account_store,
    )
    with pytest.raises(CitizenRegistrationError, match="activation remains blocked"):
        activate_service(
            account=approved,
            context=_staff_context(),
            account_store=account_store,
        )
    with pytest.raises(MedicalDataAccessDeniedError):
        assert_medical_data_access_allowed(account=approved, context=_staff_context())


# Synthetic status projection mirrored by the demo-only Arabic RTL citizen surface.


def test_status_projection_for_initial_account_is_bounded_and_non_official() -> None:
    _, _, account = _initial_account()
    view = project_registration_status(account)

    assert view["lifecycle_state"] == "INITIAL_ACCOUNT_CREATED"
    assert view["verification_state"] == "UNVERIFIED"
    assert view["next_step"] == "verify_contact"
    assert view["can_access_medical_data"] is False
    assert view["official_verification"] is False
    assert view["synthetic"] is True
    assert view["case_reference"] == account.gula_citizen_identifier
    assert "national_id" not in view
    assert "raw_nid" not in view


def test_status_projection_for_review_requires_in_person_review() -> None:
    _, _, reviewed = _reviewed_account()
    view = project_registration_status(reviewed)

    assert view["lifecycle_state"] == "NATIONAL_IDENTITY_PENDING_REVIEW"
    assert view["verification_state"] == "PENDING_REVIEW"
    assert view["requires_in_person_review"] is True
    assert view["identity_submitted"] is True
    assert view["next_step"] == "await_in_person_review"
    assert view["health_identity_approved"] is False
    assert view["can_access_medical_data"] is False
    assert view["official_verification"] is False


def test_status_projection_never_claims_medical_access_after_health_approval() -> None:
    _, account_store, reviewed = _reviewed_account()
    primary, secondary = _linkage_candidates()
    approved = approve_health_identity(
        account=reviewed,
        primary=primary,
        secondary=secondary,
        reviewer=LinkageReviewer(name="reviewer-1", user_id=7),
        reason="synthetic approval for projection",
        evidence_reference="SYNTHETIC-REVIEW-PROJECTION-0001",
        context=_staff_context(),
        account_store=account_store,
    )
    view = project_registration_status(approved)

    assert view["health_identity_approved"] is True
    assert view["next_step"] == "activation_pending_owner_approval"
    assert view["can_access_medical_data"] is False
    assert view["official_verification"] is False
