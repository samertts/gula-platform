"""Phase 1 adversarial tests for synthetic citizen lifecycle orchestration.

All identifiers and evidence are synthetic. No DDL, route, database, external
service, government connection, or real citizen data is used.
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
    InMemoryRegistrationAccountStore,
    InvalidRegistrationTransitionError,
    RegistrationAuthorizationError,
    RegistrationConflictError,
    RegistrationContext,
    RegistrationEvidenceError,
    RegistrationLifecycleEvent,
    RegistrationLifecycleService,
    RegistrationLifecycleState,
    RegistrationReplayError,
    assert_no_registration_conflict,
)
from app.national.services.document_authenticity import (
    CaptureSessionRegistry,
    DeviceCapabilityMetadata,
    LiveCaptureSession,
    NfcReadOutcome,
    NfcState,
    NidpEvidenceBundle,
    OriginalCardPresentation,
    OriginalDocumentChannel,
    RegistrationPath,
    VisualInspection,
)
from app.national.services.identity_access import IdentityRole
from app.national.services.identity_governance import (
    LinkageCandidate,
    LinkageReviewer,
)
from app.national.services.identity_persistence import (
    InMemoryIdempotencyStore,
    RegistrationRequest,
)

NOW = datetime(2026, 11, 26, 9, 0, tzinfo=UTC)
NID_HASH = "c" * 64


def _context(*, correlation_id: str, **overrides) -> RegistrationContext:
    values = {
        "decision": AuthorizationDecision.allow(),
        "actor_id": "citizen-synthetic",
        "actor_type": ActorType.CITIZEN,
        "organization_id": "ORG-SYNTHETIC",
        "facility_id": "FACILITY-SYNTHETIC",
        "purpose": "citizen_workspace",
        "now": NOW,
        "role": None,
        "correlation_id": correlation_id,
        "national_id_hash": NID_HASH,
    }
    values.update(overrides)
    return RegistrationContext(**values)


def _staff_context(*, correlation_id: str, **overrides) -> RegistrationContext:
    values = {
        "correlation_id": correlation_id,
        "actor_id": "reviewer-synthetic",
        "actor_type": ActorType.STAFF,
        "purpose": "ADMINISTRATION",
        "role": IdentityRole.IDENTITY_REVIEWER,
    }
    values.update(overrides)
    return _context(**values)


def _request(key: str = "idem-phase1-1", subject: str = "SUBJ-SYNTHETIC-PHASE1") -> RegistrationRequest:
    return RegistrationRequest(
        idempotency_key=key,
        subject_reference=subject,
        birth_year=1990,
        requested_at=NOW,
    )


def _capture(*, nfc_supported: bool = True) -> LiveCaptureSession:
    registry = CaptureSessionRegistry()
    challenge = registry.issue(
        session_id="SESSION-PHASE1-0001",
        actor_id="citizen-synthetic",
        organization_id="ORG-SYNTHETIC",
        facility_id="FACILITY-SYNTHETIC",
        purpose="citizen_workspace",
        correlation_id="CORR-PHASE1-SUBMIT",
        device_capabilities=DeviceCapabilityMetadata(
            nfc_supported=nfc_supported,
            camera_available=True,
        ),
        at=NOW,
        nonce="b" * 32,
    )
    return registry.complete(
        challenge,
        front_evidence_reference="SYNTHETIC-FRONT-PHASE1",
        back_evidence_reference="SYNTHETIC-BACK-PHASE1",
        captured_at=NOW + timedelta(seconds=1),
    )


def _evidence(*, path: RegistrationPath = RegistrationPath.IN_PERSON_OFFICER) -> NidpEvidenceBundle:
    nfc = None
    if path is RegistrationPath.HOME_NFC:
        nfc = NfcReadOutcome(
            state=NfcState.NFC_READ_SUCCESSFULLY,
            read_at=NOW + timedelta(seconds=2),
            evidence_reference="SYNTHETIC-NFC-PHASE1",
        )
    return NidpEvidenceBundle(
        path=path,
        presentation=OriginalCardPresentation(
            channel=OriginalDocumentChannel.AUTHORIZED_LIVE_CAMERA_SESSION,
            actor_id="citizen-synthetic",
            organization_id="ORG-SYNTHETIC",
            facility_id="FACILITY-SYNTHETIC",
            purpose="citizen_workspace",
            correlation_id="CORR-PHASE1-SUBMIT",
            presented_at=NOW,
            evidence_reference="SYNTHETIC-PRESENTATION-PHASE1",
            physical_presented=True,
        ),
        capture=_capture(nfc_supported=path is RegistrationPath.HOME_NFC),
        visual_inspection=VisualInspection(
            inspector_id="reviewer-synthetic",
            organization_id="ORG-SYNTHETIC",
            facility_id="FACILITY-SYNTHETIC",
            purpose="citizen_workspace",
            correlation_id="CORR-PHASE1-SUBMIT",
            inspected_at=NOW + timedelta(seconds=2),
            evidence_reference="SYNTHETIC-INSPECTION-PHASE1",
        ),
        nfc=nfc,
    )


def _service() -> RegistrationLifecycleService:
    return RegistrationLifecycleService(
        idempotency_store=InMemoryIdempotencyStore(),
        account_store=InMemoryRegistrationAccountStore(),
    )


def _reviewed_service():
    service = _service()
    created = service.create(
        request=_request(),
        context=_context(correlation_id="CORR-PHASE1-CREATE"),
        contact_reference="CONTACT-SYNTHETIC-PHASE1",
    )
    service.verify_contact(
        gula_citizen_identifier=created.account.gula_citizen_identifier,
        contact_code="123456",
        context=_context(correlation_id="CORR-PHASE1-CONTACT"),
    )
    submitted = service.submit_identity(
        gula_citizen_identifier=created.account.gula_citizen_identifier,
        evidence=_evidence(),
        context=_context(correlation_id="CORR-PHASE1-SUBMIT"),
    )
    return service, submitted.account


def _candidates():
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


def test_every_transition_records_required_decision_metadata() -> None:
    service, account = _reviewed_service()
    primary, secondary = _candidates()
    approved = service.approve_health_identity(
        gula_citizen_identifier=account.gula_citizen_identifier,
        primary=primary,
        secondary=secondary,
        reviewer=LinkageReviewer(name="reviewer-synthetic", user_id=7),
        reason="synthetic approval",
        evidence_reference="SYNTHETIC-REVIEW-PHASE1",
        context=_staff_context(correlation_id="CORR-PHASE1-APPROVE"),
    )

    history = service.history(approved.account.gula_citizen_identifier)
    assert len(history) == 4
    assert [record.event for record in history] == [
        RegistrationLifecycleEvent.ACCOUNT_CREATED,
        RegistrationLifecycleEvent.CONTACT_VERIFIED,
        RegistrationLifecycleEvent.IDENTITY_SUBMITTED,
        RegistrationLifecycleEvent.HEALTH_APPROVED,
    ]
    last = history[-1]
    assert last.previous_state is RegistrationLifecycleState.IDENTITY_REVIEW
    assert last.new_state is RegistrationLifecycleState.HEALTH_APPROVED
    assert last.actor_id == "reviewer-synthetic"
    assert last.actor_type is ActorType.STAFF
    assert last.correlation_id == "CORR-PHASE1-APPROVE"
    assert last.decision_source == "canonical_mpi_linkage_guard"
    assert last.evidence_references == ("SYNTHETIC-REVIEW-PHASE1",)
    assert last.authorization_decision == "ALLOW"
    assert last.audit_operation == "IDENTITY_APPROVAL"
    assert len(last.audit_event_reference) == 64
    assert len(last.replay_fingerprint) == 64
    public = last.to_public_dict()
    assert "national_id" not in public
    assert "raw_nid" not in public
    assert "199000000001" not in str(public)


def test_initial_creation_event_is_recorded_as_non_verified() -> None:
    service = _service()
    created = service.create(
        request=_request(),
        context=_context(correlation_id="CORR-PHASE1-CREATE"),
        contact_reference="CONTACT-SYNTHETIC-PHASE1",
    )
    record = service.history(created.account.gula_citizen_identifier)[0]
    assert record.event is RegistrationLifecycleEvent.ACCOUNT_CREATED
    assert record.previous_state is RegistrationLifecycleState.NOT_CREATED
    assert record.new_state is RegistrationLifecycleState.INITIAL_ACCOUNT
    assert created.account.verification_state == "UNVERIFIED"
    assert created.account.can_access_medical_data is False
    status = service.status(created.account.gula_citizen_identifier)
    assert status["official_verification"] is False
    assert status["synthetic"] is True


def test_replay_with_different_decision_inputs_is_rejected_before_mutation() -> None:
    service, account = _reviewed_service()
    before_count = len(service.history(account.gula_citizen_identifier))
    before_state = service.status(account.gula_citizen_identifier)["lifecycle_state"]
    with pytest.raises(RegistrationReplayError, match="different decision inputs"):
        service.request_manual_review(
            gula_citizen_identifier=account.gula_citizen_identifier,
            reason="different reason on replay",
            evidence_reference="SYNTHETIC-REVIEW-REPLAY",
            context=_staff_context(correlation_id="CORR-PHASE1-SUBMIT"),
        )
    assert len(service.history(account.gula_citizen_identifier)) == before_count
    assert service.status(account.gula_citizen_identifier)["lifecycle_state"] == before_state


def test_identical_replay_is_idempotent_and_does_not_grow_history() -> None:
    service, account = _reviewed_service()
    before = len(service.history(account.gula_citizen_identifier))
    result = service.request_manual_review(
        gula_citizen_identifier=account.gula_citizen_identifier,
        reason="manual review requested",
        evidence_reference="SYNTHETIC-MANUAL-PHASE1",
        context=_staff_context(correlation_id="CORR-PHASE1-MANUAL"),
    )
    replay = service.request_manual_review(
        gula_citizen_identifier=account.gula_citizen_identifier,
        reason="manual review requested",
        evidence_reference="SYNTHETIC-MANUAL-PHASE1",
        context=_staff_context(correlation_id="CORR-PHASE1-MANUAL"),
    )
    assert replay.transition == result.transition
    assert len(service.history(account.gula_citizen_identifier)) == before + 1


def test_non_self_loop_identical_replay_is_idempotent() -> None:
    service = _service()
    created = service.create(
        request=_request(key="idem-replay-non-loop"),
        context=_context(correlation_id="CORR-PHASE1-NONLOOP-CREATE"),
        contact_reference="CONTACT-SYNTHETIC-NONLOOP",
    )
    identifier = created.account.gula_citizen_identifier
    first = service.verify_contact(
        gula_citizen_identifier=identifier,
        contact_code="123456",
        context=_context(correlation_id="CORR-PHASE1-NONLOOP-CONTACT"),
    )
    replay = service.verify_contact(
        gula_citizen_identifier=identifier,
        contact_code="123456",
        context=_context(correlation_id="CORR-PHASE1-NONLOOP-CONTACT"),
    )
    assert replay.transition == first.transition
    assert replay.account.lifecycle_state is RegistrationLifecycleState.CONTACT_VERIFIED
    assert len(service.history(identifier)) == 2


def test_wrong_contact_reference_cannot_resubmit_another_case() -> None:
    service, account = _reviewed_service()
    service.suspend(
        gula_citizen_identifier=account.gula_citizen_identifier,
        reason="synthetic suspension",
        evidence_reference="SYNTHETIC-SUSPENSION-SCOPE",
        context=_staff_context(correlation_id="CORR-PHASE1-SUSPEND-SCOPE"),
    )
    with pytest.raises(RegistrationAuthorizationError, match="account contact reference"):
        service.resubmit(
            gula_citizen_identifier=account.gula_citizen_identifier,
            contact_reference="CONTACT-SYNTHETIC-OTHER",
            evidence_reference="SYNTHETIC-RESUBMISSION-SCOPE",
            reason="unauthorized resubmission",
            context=_context(correlation_id="CORR-PHASE1-RESUBMIT-SCOPE"),
        )


def test_suspension_resubmission_and_appeal_do_not_grant_verification() -> None:
    service, account = _reviewed_service()
    suspended = service.suspend(
        gula_citizen_identifier=account.gula_citizen_identifier,
        reason="synthetic suspension",
        evidence_reference="SYNTHETIC-SUSPENSION-PHASE1",
        context=_staff_context(correlation_id="CORR-PHASE1-SUSPEND"),
    )
    assert suspended.account.lifecycle_state is RegistrationLifecycleState.SUSPENDED
    assert suspended.account.can_access_medical_data is False

    resubmitted = service.resubmit(
        gula_citizen_identifier=account.gula_citizen_identifier,
        contact_reference="CONTACT-SYNTHETIC-PHASE1",
        evidence_reference="SYNTHETIC-RESUBMISSION-PHASE1",
        reason="synthetic resubmission",
        context=_context(correlation_id="CORR-PHASE1-RESUBMIT"),
    )
    assert resubmitted.account.lifecycle_state is RegistrationLifecycleState.IDENTITY_REVIEW
    assert resubmitted.account.verification_state == "PENDING_REVIEW"

    rejected = service.reject(
        gula_citizen_identifier=account.gula_citizen_identifier,
        reason="synthetic rejection",
        context=_staff_context(correlation_id="CORR-PHASE1-REJECT"),
    )
    appealed = service.appeal(
        gula_citizen_identifier=account.gula_citizen_identifier,
        reason="synthetic appeal",
        evidence_reference="SYNTHETIC-APPEAL-PHASE1",
        reviewer_id="independent-reviewer-synthetic",
        context=_staff_context(correlation_id="CORR-PHASE1-APPEAL"),
    )
    assert rejected.account.lifecycle_state is RegistrationLifecycleState.REJECTED
    assert appealed.account.lifecycle_state is RegistrationLifecycleState.IDENTITY_REVIEW
    assert appealed.account.verification_state == "PENDING_REVIEW"
    assert appealed.account.can_access_medical_data is False


def test_cross_facility_and_wrong_role_staff_actions_are_denied() -> None:
    service, account = _reviewed_service()
    with pytest.raises(PermissionError):
        service.suspend(
            gula_citizen_identifier=account.gula_citizen_identifier,
            reason="cross facility attempt",
            evidence_reference="SYNTHETIC-SUSPENSION-CROSS",
            context=_staff_context(
                correlation_id="CORR-PHASE1-CROSS-FACILITY",
                facility_id="FACILITY-OTHER-SYNTHETIC",
            ),
        )
    with pytest.raises(RegistrationAuthorizationError, match="named staff role"):
        service.approve_health_identity(
            gula_citizen_identifier=account.gula_citizen_identifier,
            primary=_candidates()[0],
            secondary=_candidates()[1],
            reviewer=LinkageReviewer(name="lab-synthetic", user_id=9),
            reason="privilege escalation attempt",
            evidence_reference="SYNTHETIC-ESCALATION-PHASE1",
            context=_staff_context(
                correlation_id="CORR-PHASE1-ESCALATION",
                role=IdentityRole.LABORATORY_TECHNICIAN,
            ),
        )
    assert service.history(account.gula_citizen_identifier)[-1].event is RegistrationLifecycleEvent.IDENTITY_SUBMITTED


def test_conflicting_duplicate_subject_evidence_is_rejected() -> None:
    service = _service()
    first = service.create(
        request=_request(key="idem-conflict-1", subject="SUBJ-SYNTHETIC-CONFLICT"),
        context=_context(correlation_id="CORR-PHASE1-CONFLICT-1"),
        contact_reference="CONTACT-SYNTHETIC-CONFLICT-1",
    )
    second = RegistrationLifecycleService(
        idempotency_store=InMemoryIdempotencyStore(),
        account_store=InMemoryRegistrationAccountStore(),
    ).create(
        request=_request(key="idem-conflict-2", subject="SUBJ-SYNTHETIC-CONFLICT"),
        context=_context(correlation_id="CORR-PHASE1-CONFLICT-2"),
        contact_reference="CONTACT-SYNTHETIC-CONFLICT-2",
    ).account
    with pytest.raises(RegistrationConflictError, match="duplicate registration subjects"):
        assert_no_registration_conflict(
            (first.account, second),
            subject_reference="SUBJ-SYNTHETIC-CONFLICT",
            evidence_reference="SYNTHETIC-CONFLICT-PHASE1",
        )


def test_concurrent_create_with_same_intent_yields_single_transition() -> None:
    service = _service()

    def create() -> str:
        result = service.create(
            request=_request(key="idem-concurrent-phase1"),
            context=_context(correlation_id="CORR-PHASE1-CONCURRENT"),
            contact_reference="CONTACT-SYNTHETIC-CONCURRENT",
        )
        return result.account.gula_citizen_identifier

    with ThreadPoolExecutor(max_workers=2) as executor:
        identifiers = list(executor.map(lambda _: create(), range(2)))
    assert len(set(identifiers)) == 1
    assert len(service.history(identifiers[0])) == 1


def test_activation_remains_denied_and_creates_no_transition() -> None:
    service, account = _reviewed_service()
    primary, secondary = _candidates()
    service.approve_health_identity(
        gula_citizen_identifier=account.gula_citizen_identifier,
        primary=primary,
        secondary=secondary,
        reviewer=LinkageReviewer(name="reviewer-synthetic", user_id=7),
        reason="synthetic approval",
        evidence_reference="SYNTHETIC-ACTIVATION-PHASE1",
        context=_staff_context(correlation_id="CORR-PHASE1-ACTIVATION-APPROVE"),
    )
    before = len(service.history(account.gula_citizen_identifier))
    with pytest.raises(Exception, match="blocked pending an approved official authenticity procedure"):
        service.activate(
            gula_citizen_identifier=account.gula_citizen_identifier,
            context=_staff_context(correlation_id="CORR-PHASE1-ACTIVATION-DENY"),
        )
    assert len(service.history(account.gula_citizen_identifier)) == before
    assert service.status(account.gula_citizen_identifier)["can_access_medical_data"] is False


def test_transition_requires_correlation_and_timezone_aware_timestamp() -> None:
    service = _service()
    with pytest.raises(RegistrationEvidenceError, match="correlation id"):
        service.create(
            request=_request(key="idem-no-corr"),
            context=_context(correlation_id=None),
            contact_reference="CONTACT-SYNTHETIC-NOCORR",
        )
    # The transition record is the authoritative boundary for timestamp truth;
    # its validator rejects a naive timestamp reached through the real service.
    with pytest.raises(RegistrationEvidenceError, match="timezone aware"):
        service.create(
            request=_request(key="idem-naive"),
            context=_context(correlation_id="CORR-PHASE1-NAIVE", now=datetime(2026, 11, 26, 9, 0)),
            contact_reference="CONTACT-SYNTHETIC-NAIVE",
        )
