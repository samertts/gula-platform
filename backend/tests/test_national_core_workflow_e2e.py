"""National Core Leap 02 — synthetic end-to-end workflow evidence.

This matrix composes the Phase 1 registration lifecycle with the existing
NationalClinicalIntegration chain through one additive, route-free facade. It
uses only synthetic identifiers, in-memory stores, and fake canonical sessions.
It creates no routes, DDL, migrations, production data, or release-state change.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from app._compat import UTC
from app.clinical.observability import clinical_safety_metrics, prometheus_lines
from app.identity.models.account import Account, AccountStatus
from app.identity.models.citizen_relationship import (
    CitizenRelationship,
    CitizenRelationshipSource,
    CitizenRelationshipStatus,
    CitizenRelationshipType,
)
from app.identity.models.consent import NiamConsent, NiamConsentStatus
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.models.session import UserSession
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecision,
    AuthorizationReason,
    AuthorizationRequest,
)
from app.identity.services.canonical_audit import CanonicalAuditService
from app.lab_slice.models import (
    CustodyEvent,
    SyntheticLabCase,
    SyntheticOrder,
    SyntheticPatient,
    SyntheticQCControl,
    SyntheticResult,
    SyntheticSpecimen,
)
from app.national.clinical_integration import ClinicalIntegrationConflict, ClinicalIntegrationDenied
from app.national.enums import EncounterStatus
from app.national.intelligence.laboratory.analytics import DeltaCheckEngine
from app.national.services.citizen_registration import (
    ActorType,
    CitizenRegistrationError,
    MedicalDataAccessDeniedError,
    RegistrationAuthorizationError,
    RegistrationContext,
    RegistrationLifecycleService,
    assert_medical_data_access_allowed,
)
from app.national.services.document_authenticity import (
    CaptureSessionRegistry,
    DeviceCapabilityMetadata,
    LiveCaptureSession,
    NidpEvidenceBundle,
    OriginalCardPresentation,
    OriginalDocumentChannel,
    RegistrationPath,
    VisualInspection,
)
from app.national.services.identity_access import IdentityRole
from app.national.services.identity_governance import IdentityAccessDeniedError
from app.national.services.national_core_workflow import (
    WORKFLOW_LAYERS,
    WORKFLOW_SCHEMA,
    InMemoryNationalCorePersistenceAdapter,
    NationalCoreAccessInput,
    NationalCoreClinicalInput,
    NationalCoreIdentityInput,
    NationalCoreRegistrationInput,
    NationalCoreWorkflow,
    NationalCoreWorkflowCommand,
    NationalCoreWorkflowError,
    NationalCoreWorkflowReplayError,
)
from app.platform.sync import SyncService
from app.services.reference.national_lab_catalog import NationalLaboratoryCatalog

CORR = "NCW-E2E-20261126"
WORKFLOW_KEY = "NCW-WORKFLOW-0001"
ORG = "ORG-SYN-NCW"
FACILITY = "FACILITY-SYN-NCW"
SECONDARY_FACILITY = "FACILITY-SYN-NCW-B"
ACCOUNT = "ACCOUNT-NCW"
CITIZEN_ACCOUNT = "ACCOUNT-CITIZEN-NCW"
IDENTITY = "IDENTITY-NCW"
PERSON = "PERSON-NCW"
GULA = "199000000001"
GULA_SECONDARY = "SYN-GULA-0002"
RAW_NID = "123456789012"
NID_HASH = "a" * 64
REVIEWER = "synthetic-reviewer-ncw"
CONSENT_ID = "CONSENT-SYN-NCW"
PATIENT_REF = "synthetic-patient-ncw"
NOW = datetime(2026, 11, 26, 9, 0, tzinfo=UTC)


def _allow(policy_id: str, audit_reference: str) -> AuthorizationDecision:
    """Build an allow decision carrying engine-style provenance references."""

    return AuthorizationDecision.allow(
        policy_id=policy_id,
        policy_version="v1",
        audit_reference=audit_reference,
    )


class _Result:
    def __init__(self, values: Any = None, scalar: Any = None) -> None:
        self.values = list(values or [])
        self.scalar_value = scalar

    def scalars(self) -> _Result:
        return self

    def all(self) -> list[Any]:
        return list(self.values)

    def scalar_one_or_none(self) -> Any:
        return self.scalar_value

    def first(self) -> Any:
        return self.values[0] if self.values else None


class _IntegrationSession:
    """Table-routed fake AsyncSession for canonical decision/consent/audit."""

    def __init__(
        self,
        *,
        consents: list[NiamConsent] | None = None,
        relationships: list[CitizenRelationship] | None = None,
        role_key: str = IdentityRole.PHYSICIAN.value,
        fail_audit: bool = False,
    ) -> None:
        self.consents = list(consents if consents is not None else [_consent()])
        self.relationships = (
            list(relationships) if relationships is not None else [_relationship()]
        )
        self.role_key = role_key
        self.fail_audit = fail_audit
        self.audit_entries: list[Any] = []

    def _memberships(self) -> list[Membership]:
        return [
            Membership(
                id="MEMBERSHIP-NCW",
                account_id=ACCOUNT,
                identity_id=IDENTITY,
                organization_id=ORG,
                facility_id=FACILITY,
                status=MembershipStatus.active.value,
                is_active=True,
                expires_at=NOW + timedelta(hours=1),
                revoked_at=None,
            ),
        ]

    async def execute(self, statement: Any) -> _Result:
        sql = str(statement)
        if "niam_roles" in sql and "role_key" in sql:
            return _Result([self.role_key])
        if "niam_identities" in sql:
            return _Result([SimpleNamespace(id=IDENTITY, person_id=PERSON)])
        if "niam_employments" in sql:
            today = NOW.date()
            return _Result(
                [
                    SimpleNamespace(
                        id="EMPLOYMENT-NCW",
                        person_id=PERSON,
                        organization_id=ORG,
                        status="active",
                        is_active=True,
                        start_date=today - timedelta(days=30),
                        end_date=None,
                        termination_date=None,
                    ),
                ],
            )
        if "niam_memberships" in sql:
            if "organization_id" in sql and "limit" in sql:
                return _Result(scalar=ORG)
            return _Result(self._memberships())
        if "niam_role_assignments" in sql:
            return _Result(["patient_record.read"])
        if "niam_policies" in sql:
            return _Result([])
        if "niam_citizen_relationships" in sql:
            return _Result(self.relationships)
        if "niam_consents" in sql:
            return _Result(self.consents)
        if "niam_audit_entries" in sql:
            entries = self.audit_entries
            if "event_version" in sql:
                entries = [item for item in entries if getattr(item, "event_version", None) == "2"]
            if "entry_hash" in sql and "limit" in sql.lower():
                return _Result(scalar=getattr(entries[-1], "entry_hash", None) if entries else None)
            return _Result(entries)
        return _Result([])

    async def scalar(self, statement: Any) -> Any:
        return "permission-id"

    async def get(self, model: Any, identifier: Any) -> Any:
        if "NiamConsent" in getattr(model, "__name__", ""):
            return next((item for item in self.consents if item.id == identifier), None)
        return None

    def add(self, entry: Any) -> None:
        if self.fail_audit and getattr(entry, "event_version", None) == "2":
            raise RuntimeError("canonical audit write failure")
        if not getattr(entry, "id", None):
            entry.id = f"synthetic-audit-{len(self.audit_entries) + 1}"
        self.audit_entries.append(entry)

    async def flush(self) -> None:
        return None


class _FailingOnceSyncService(SyncService):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def push_changes(self, changes: list[Any]) -> int:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("synthetic transient offline fault")
        return super().push_changes(changes)


def _relationship(*, patient_id: str = PATIENT_REF) -> CitizenRelationship:
    now = NOW
    return CitizenRelationship(
        id="RELATIONSHIP-NCW",
        source_kind=CitizenRelationshipSource.canonical_account.value,
        canonical_account_id=ACCOUNT,
        citizen_id=CITIZEN_ACCOUNT,
        patient_id=patient_id,
        relationship_type=CitizenRelationshipType.self.value,
        status=CitizenRelationshipStatus.active.value,
        purpose="TREATMENT",
        scope={"resources": ["patient_record", "patient_record:read"]},
        valid_from=now - timedelta(minutes=5),
        verified_at=now - timedelta(minutes=4),
        revoked_at=None,
        version=1,
    )


def _consent(*, active: bool = True, patient_reference: str = PATIENT_REF) -> NiamConsent:
    return NiamConsent(
        id=CONSENT_ID,
        subject_account_id=CITIZEN_ACCOUNT,
        grantee_account_id=ACCOUNT,
        purpose="TREATMENT",
        scope={
            "resource_domain": "patient_record",
            "actions": ["read"],
            "patient_reference": patient_reference,
            "gula_citizen_identifier": GULA,
        },
        resource_domain="patient_record",
        status=NiamConsentStatus.active.value if active else NiamConsentStatus.withdrawn.value,
        is_active=active,
        granted_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(hours=1),
        version=1,
        source="user_portal",
    )


def _actor() -> AuthorizationActor:
    return AuthorizationActor(
        account=Account(
            id=ACCOUNT,
            identity_id=IDENTITY,
            status=AccountStatus.active.value,
            is_active=True,
            is_locked=False,
        ),
        session=UserSession(
            id="SESSION-NCW",
            account_id=ACCOUNT,
            is_active=True,
            expires_at=NOW + timedelta(hours=1),
            started_at=NOW - timedelta(minutes=5),
            mfa_used=True,
        ),
    )


def _ade_request(**overrides: Any) -> AuthorizationRequest:
    values: dict[str, Any] = {
        "subject_account_id": ACCOUNT,
        "action": "read",
        "resource_type": "patient_record",
        "resource_id": PATIENT_REF,
        "permission_key": "patient_record.read",
        "organization_id": ORG,
        "facility_id": FACILITY,
        "purpose": "TREATMENT",
        "purpose_validated": True,
        "sensitivity": "high",
        "resource_context": {
            "exists": True,
            "organization_id": ORG,
            "facility_id": FACILITY,
            "patient_id": PATIENT_REF,
            "privacy_probe": RAW_NID,
        },
    }
    values.update(overrides)
    return AuthorizationRequest(**values)


def _case(suffix: str = "ncw-happy", *, value: float = 95.0) -> SyntheticLabCase:
    patient = SyntheticPatient(
        patient_id=PATIENT_REF,
        age_years=35,
        region="synthetic-region",
    )
    order = SyntheticOrder(
        order_id=f"synthetic-order-{suffix}",
        patient_id=patient.patient_id,
        test_code="GLU",
        status="completed",
    )
    specimen = SyntheticSpecimen(
        specimen_id=f"synthetic-specimen-{suffix}",
        order_id=order.order_id,
        patient_id=patient.patient_id,
        specimen_type="Serum",
        state="analyzed",
        custody=(
            CustodyEvent(
                event_id=f"synthetic-custody-{suffix}",
                location=FACILITY,
                actor=REVIEWER,
                recorded_at="2026-11-26T09:00:00+00:00",
            ),
        ),
    )
    qc = SyntheticQCControl(
        control_id=f"synthetic-qc-{suffix}",
        test_code="GLU",
        value=100.0,
        mean=100.0,
        sd=2.0,
        history=(99.0, 101.0),
    )
    result = SyntheticResult(
        result_id=f"synthetic-result-{suffix}",
        order_id=order.order_id,
        specimen_id=specimen.specimen_id,
        patient_id=patient.patient_id,
        test_code="GLU",
        value=value,
        unit="mg/dL",
        reference_low=70.0,
        reference_high=110.0,
        critical_low=50.0,
        critical_high=300.0,
        previous_value=88.0,
        reportable_condition="influenza",
    )
    return SyntheticLabCase(
        patient=patient,
        order=order,
        specimen=specimen,
        result=result,
        qc=qc,
    )


def _capture(correlation_id: str) -> LiveCaptureSession:
    registry = CaptureSessionRegistry()
    challenge = registry.issue(
        session_id="SESSION-NCW-CAPTURE",
        actor_id="SUBJ-SYN-NCW",
        organization_id=ORG,
        facility_id=FACILITY,
        purpose="citizen_workspace",
        correlation_id=correlation_id,
        device_capabilities=DeviceCapabilityMetadata(
            nfc_supported=False,
            camera_available=True,
        ),
        at=NOW,
        nonce="b" * 32,
    )
    return registry.complete(
        challenge,
        front_evidence_reference="SYNTHETIC-FRONT-NCW",
        back_evidence_reference="SYNTHETIC-BACK-NCW",
        captured_at=NOW + timedelta(seconds=1),
    )


def _evidence(correlation_id: str) -> NidpEvidenceBundle:
    return NidpEvidenceBundle(
        path=RegistrationPath.IN_PERSON_OFFICER,
        presentation=OriginalCardPresentation(
            channel=OriginalDocumentChannel.AUTHORIZED_LIVE_CAMERA_SESSION,
            actor_id="SUBJ-SYN-NCW",
            organization_id=ORG,
            facility_id=FACILITY,
            purpose="citizen_workspace",
            correlation_id=correlation_id,
            presented_at=NOW,
            evidence_reference="SYNTHETIC-PRESENTATION-NCW",
            physical_presented=True,
        ),
        capture=_capture(correlation_id),
        visual_inspection=VisualInspection(
            inspector_id="synthetic-inspector-ncw",
            organization_id=ORG,
            facility_id=FACILITY,
            purpose="citizen_workspace",
            correlation_id=correlation_id,
            inspected_at=NOW + timedelta(seconds=2),
            evidence_reference="SYNTHETIC-INSPECTION-NCW",
        ),
        nfc=None,
    )


def _adapter(
    *,
    sync_service: SyncService | None = None,
    precompleted_registrations: dict[str, str] | None = None,
) -> InMemoryNationalCorePersistenceAdapter:
    catalog = NationalLaboratoryCatalog()
    catalog.seed_common_tests()
    delta = DeltaCheckEngine()
    delta.set_delta_threshold("GLU", 2.0, 20.0)
    return InMemoryNationalCorePersistenceAdapter(
        catalog=catalog,
        delta_engine=delta,
        sync_service=sync_service,
        precompleted_registrations=precompleted_registrations
        or {"NCW-IDEM-REG-0001": GULA},
    )


def _command(
    *,
    workflow_key: str = WORKFLOW_KEY,
    correlation_id: str = CORR,
    secondary_nid_hash: str | None = None,
    case: SyntheticLabCase | None = None,
    access_overrides: dict[str, Any] | None = None,
    citizen_decision: AuthorizationDecision | None = None,
    staff_decision: AuthorizationDecision | None = None,
) -> NationalCoreWorkflowCommand:
    case = case or _case()
    encounter = SimpleNamespace(
        id="abcdef1234-synthetic",
        patient_id=PATIENT_REF,
        organization_id=ORG,
        facility_id=FACILITY,
        status=EncounterStatus.COMPLETED,
        privacy_probe=RAW_NID,
    )
    encounter_reference = f"synthetic-encounter-{str(encounter.id)[:8].lower()}"
    return NationalCoreWorkflowCommand(
        workflow_key=workflow_key,
        correlation_id=correlation_id,
        organization_id=ORG,
        facility_id=FACILITY,
        reviewer_name=REVIEWER,
        reviewer_user_id=42,
        review_reason="synthetic documented cross-facility review",
        registration=NationalCoreRegistrationInput(
            idempotency_key="NCW-IDEM-REG-0001",
            subject_reference="SUBJ-SYN-NCW",
            contact_reference="CONTACT-SYN-NCW",
            contact_code="123456",
            evidence=_evidence(correlation_id),
        ),
        identity=NationalCoreIdentityInput(
            primary_facility_id=FACILITY,
            secondary_facility_id=SECONDARY_FACILITY,
            primary_local_patient_id="synthetic-local-ncw-a",
            secondary_local_patient_id="synthetic-local-ncw-b",
            secondary_gula_citizen_identifier=GULA_SECONDARY,
            linkage_evidence_reference="SYNTHETIC-LINKAGE-NCW",
            national_id_hash=NID_HASH,
            birth_year=1990,
            birth_month=1,
            birth_day=2,
            phone_last10="0000000001",
            secondary_nid_hash=secondary_nid_hash,
        ),
        clinical=NationalCoreClinicalInput(
            encounter_reference=encounter_reference,
            case=case,
            release_idempotency_key=f"{workflow_key}-release",
            event_idempotency_key=f"{workflow_key}-event",
            encounter=encounter,
        ),
        access=NationalCoreAccessInput(
            actor=_actor(),
            request=_ade_request(**(access_overrides or {})),
            consent_id=CONSENT_ID,
            citizen_account_id=CITIZEN_ACCOUNT,
        ),
        citizen_decision=citizen_decision
        or _allow("SYNTHETIC-REGISTRATION-POLICY", "AUDIT-SYN-REGISTRATION"),
        staff_decision=staff_decision
        or _allow("SYNTHETIC-REVIEW-POLICY", "AUDIT-SYN-REVIEW"),
        now=NOW,
    )


def test_happy_path_composes_all_layers_and_withholds_citizen_result() -> None:
    adapter = _adapter()
    workflow = NationalCoreWorkflow(adapter)
    session = _IntegrationSession()

    result = asyncio.run(workflow.run(session, _command()))

    assert result.schema_version == WORKFLOW_SCHEMA
    assert set(result.layers) == set(WORKFLOW_LAYERS)
    assert result.registration_transitions == 4
    assert result.linkage.action == "LINK_APPROVED"
    assert result.release_status == "released"
    assert result.bundle_reference is not None
    assert result.event_summary is not None
    assert result.event_summary.delivered == ("synthetic-result-ncw-happy-lims.result.validated",)
    assert result.audit_verification["status"] == "VALID"
    assert result.decision_summary["clinical_access"]["decision"] == "allow"
    assert result.stages[-1] == "authorized_citizen_access"
    assert result.citizen_view["can_access_medical_data"] is False
    assert result.citizen_view["medical_result_withheld"] is True
    assert result.citizen_view["result_generated_in_synthetic_chain"] is True
    assert result.citizen_view["next_step"] == "await_owner_activation_decision"
    assert result.citizen_view["official_verification"] is False

    event_types = [item.event_type for item in session.audit_entries]
    assert event_types.count("IDENTITY_OPERATION_WAVE053") == 2
    assert "CONSENT_CHECKED" in event_types
    assert "NATIONAL_CLINICAL_ACCESS" in event_types
    assert "NATIONAL_CORE_CITIZEN_RESULT_WITHHELD" in event_types
    last = session.audit_entries[-1]
    assert CanonicalAuditService._hash(last) == last.entry_hash


def test_replay_returns_same_receipt_and_rejects_changed_inputs() -> None:
    adapter = _adapter()
    workflow = NationalCoreWorkflow(adapter)
    session = _IntegrationSession()
    command = _command()

    first = asyncio.run(workflow.run(session, command))
    audit_count = len(session.audit_entries)
    replay = asyncio.run(workflow.run(session, command))

    assert replay.replayed is True
    assert replay.registration_transitions == first.registration_transitions
    assert replay.event_summary == first.event_summary
    assert len(session.audit_entries) == audit_count

    commands_before, _ = clinical_safety_metrics.snapshot()
    duplicate_key = (
        "national_core_workflow",
        "national_core_workflow",
        "rejected",
        "duplicate_command",
    )
    before_count = commands_before.get(duplicate_key, 0)

    changed = replace(
        command,
        staff_decision=AuthorizationDecision.deny(AuthorizationReason.scope_mismatch),
    )
    with pytest.raises(NationalCoreWorkflowReplayError, match="different inputs"):
        asyncio.run(workflow.run(session, changed))

    changed_scope = replace(command, facility_id="FACILITY-OTHER-SYN")
    with pytest.raises(NationalCoreWorkflowReplayError, match="different inputs"):
        asyncio.run(workflow.run(session, changed_scope))

    commands_after, _ = clinical_safety_metrics.snapshot()
    assert commands_after.get(duplicate_key, 0) == before_count + 2


def test_identity_conflict_is_blocked_before_clinical_release() -> None:
    adapter = _adapter()
    workflow = NationalCoreWorkflow(adapter)
    session = _IntegrationSession()
    command = _command(secondary_nid_hash="b" * 64)

    with pytest.raises(ClinicalIntegrationConflict, match="conflicting NID hashes"):
        asyncio.run(workflow.run(session, command))

    event_types = [item.event_type for item in session.audit_entries]
    assert "NATIONAL_CLINICAL_ACCESS" not in event_types
    assert "NATIONAL_CLINICAL_ACCESS_DENIED" not in event_types
    assert "NATIONAL_CORE_CITIZEN_RESULT_WITHHELD" not in event_types
    assert adapter.event_pipeline.process().delivered == ()


def test_scope_denial_is_audited_and_fails_closed() -> None:
    adapter = _adapter()
    workflow = NationalCoreWorkflow(adapter)
    session = _IntegrationSession()
    command = _command(access_overrides={"organization_id": "ORG-OTHER-SYN"})

    with pytest.raises(ClinicalIntegrationDenied, match="organization scope mismatch"):
        asyncio.run(workflow.run(session, command))

    denials = [item for item in session.audit_entries if item.decision == "DENY"]
    assert any(item.reason_code == "ORGANIZATION_SCOPE_MISMATCH" for item in denials)


def test_consent_denial_is_audited_and_fails_closed() -> None:
    adapter = _adapter()
    workflow = NationalCoreWorkflow(adapter)
    session = _IntegrationSession(consents=[])
    command = _command()

    with pytest.raises(ClinicalIntegrationDenied, match="consent is absent or invalid"):
        asyncio.run(workflow.run(session, command))

    denials = [item for item in session.audit_entries if item.decision == "DENY"]
    assert any(item.reason_code == "CONSENT_INVALID" for item in denials)


def test_critical_result_is_quarantined_never_projected_and_still_withheld() -> None:
    adapter = _adapter()
    workflow = NationalCoreWorkflow(adapter)
    session = _IntegrationSession()
    command = _command(case=_case("ncw-critical", value=350.0))

    result = asyncio.run(workflow.run(session, command))

    assert result.release_status == "quarantined"
    assert result.bundle_reference is None
    assert result.event_summary is None
    assert result.citizen_view["medical_result_withheld"] is True
    assert result.citizen_view["result_generated_in_synthetic_chain"] is False
    assert any(
        item.event_type == "NATIONAL_CORE_CITIZEN_RESULT_WITHHELD"
        for item in session.audit_entries
    )


def test_offline_sync_failure_replays_once_and_duplicate_receipt_is_suppressed() -> None:
    sync_service = _FailingOnceSyncService()
    adapter = _adapter(sync_service=sync_service)
    workflow = NationalCoreWorkflow(adapter)
    session = _IntegrationSession()
    command = _command()

    result = asyncio.run(workflow.run(session, command))
    assert result.offline_summary["failed"] == 1

    retry = asyncio.run(adapter.offline_sync.sync_all())
    assert retry["synced"] == 1
    assert len(sync_service.pull_changes()) == 1

    first = asyncio.run(
        workflow._queue_offline_receipt(
            command,
            entity_id="synthetic-bundle-ncw",
            decision_id="synthetic-decision-ncw",
            released=True,
        ),
    )
    duplicate = asyncio.run(
        workflow._queue_offline_receipt(
            command,
            entity_id="synthetic-bundle-ncw",
            decision_id="synthetic-decision-ncw",
            released=True,
        ),
    )
    assert first["enqueued"] is True
    assert duplicate["enqueued"] is False
    assert adapter.store_forward.queue_size()["completed"] == 2


def test_audit_failure_fails_closed_and_records_safe_metric() -> None:
    adapter = _adapter()
    workflow = NationalCoreWorkflow(adapter)
    session = _IntegrationSession(fail_audit=True)

    with pytest.raises(ClinicalIntegrationDenied, match="canonical linkage audit failure"):
        asyncio.run(workflow.run(session, _command()))

    commands, audit_failures = clinical_safety_metrics.snapshot()
    assert ("national_core_workflow", "national_core_workflow", "rejected", "audit_write_failed") in commands
    assert ("national_core_workflow", "national_core_workflow") in audit_failures


def test_public_evidence_and_metrics_never_expose_raw_identity() -> None:
    adapter = _adapter()
    workflow = NationalCoreWorkflow(adapter)
    session = _IntegrationSession()

    command = _command()
    assert RAW_NID in json.dumps(command.access.request.resource_context)
    assert RAW_NID in json.dumps(vars(command.clinical.encounter), default=str)

    result = asyncio.run(workflow.run(session, command))
    serialized = json.dumps(result.to_public_dict())
    audit_serialized = json.dumps(session.audit_entries, default=str)
    assert RAW_NID not in serialized
    assert RAW_NID not in audit_serialized
    assert "national_id" not in serialized
    assert "contact_code" not in serialized
    assert all(RAW_NID not in line for line in prometheus_lines())


def test_concurrent_same_key_executes_once_and_replays_once() -> None:
    adapter = _adapter()
    workflow = NationalCoreWorkflow(adapter)
    session = _IntegrationSession()
    command = _command()

    async def run_twice() -> list[Any]:
        return list(
            await asyncio.gather(
                workflow.run(session, command),
                workflow.run(session, command),
            ),
        )

    results = asyncio.run(run_twice())
    assert sum(1 for result in results if result.replayed is False) == 1
    assert sum(1 for result in results if result.replayed is True) == 1
    assert results[0].registration_transitions == results[1].registration_transitions


def test_unattested_allow_and_denied_decisions_fail_closed() -> None:
    with pytest.raises(NationalCoreWorkflowError, match="requires policy, version, and audit"):
        _command(citizen_decision=AuthorizationDecision.allow())

    citizen_session = _IntegrationSession()
    with pytest.raises(RegistrationAuthorizationError):
        asyncio.run(
            NationalCoreWorkflow(_adapter()).run(
                citizen_session,
                _command(
                    citizen_decision=AuthorizationDecision.deny(
                        AuthorizationReason.scope_mismatch,
                    ),
                ),
            ),
        )
    assert citizen_session.audit_entries == []

    staff_adapter = _adapter()
    staff_session = _IntegrationSession()
    with pytest.raises(IdentityAccessDeniedError):
        asyncio.run(
            NationalCoreWorkflow(staff_adapter).run(
                staff_session,
                _command(
                    staff_decision=AuthorizationDecision.deny(
                        AuthorizationReason.scope_mismatch,
                    ),
                ),
            ),
        )
    assert (
        staff_adapter.account_store.get(GULA).lifecycle_state.value
        == "NATIONAL_IDENTITY_PENDING_REVIEW"
    )


def test_activation_and_medical_access_remain_blocked_after_workflow() -> None:
    adapter = _adapter()
    command = _command()
    result = asyncio.run(NationalCoreWorkflow(adapter).run(_IntegrationSession(), command))
    identifier = result.registration_status["case_reference"]
    account = adapter.account_store.get(identifier)
    def probe_context(role: IdentityRole, label: str) -> RegistrationContext:
        return RegistrationContext(
            decision=command.staff_decision,
            actor_id=ACCOUNT,
            actor_type=ActorType.STAFF,
            organization_id=ORG,
            facility_id=FACILITY,
            purpose="ADMINISTRATION",
            role=role,
            correlation_id=f"{CORR}-{label}",
            national_id_hash=NID_HASH,
            now=NOW,
        )

    with pytest.raises(CitizenRegistrationError):
        adapter.registration_service().activate(
            gula_citizen_identifier=identifier,
            context=probe_context(IdentityRole.IDENTITY_REVIEWER, "ACTIVATION-PROBE"),
        )
    with pytest.raises(MedicalDataAccessDeniedError):
        assert_medical_data_access_allowed(
            account=account,
            context=probe_context(IdentityRole.HEALTHCARE_PROVIDER, "MEDICAL-PROBE"),
        )
    assert account.lifecycle_state.value == "HEALTH_IDENTITY_APPROVED"


def test_wrong_facility_scope_is_denied() -> None:
    with pytest.raises(ClinicalIntegrationDenied, match="facility scope mismatch"):
        asyncio.run(
            NationalCoreWorkflow(_adapter()).run(
                _IntegrationSession(),
                _command(access_overrides={"facility_id": "FACILITY-OTHER-SYN"}),
            ),
        )


def test_withdrawn_consent_is_denied() -> None:
    with pytest.raises(ClinicalIntegrationDenied, match="consent is absent or invalid"):
        asyncio.run(
            NationalCoreWorkflow(_adapter()).run(
                _IntegrationSession(consents=[_consent(active=False)]),
                _command(),
            ),
        )
