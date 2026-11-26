"""Engineering Leap 03 — synthetic durable-core recovery evidence.

This module adds adversarial and end-to-end tests for additive, route-free
contracts over the Leap 02 national core workflow. It uses only synthetic
fixtures, in-memory adapters, and fake canonical sessions. It creates no
routes, DDL, migrations, production data, release-state change, real patient
record, or external disclosure.
"""

from __future__ import annotations

import asyncio
import copy
import importlib.util
import json
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from app._compat import UTC
from app.clinical.observability import clinical_safety_metrics
from app.integration.offline import OfflineQueueEntry, OfflineSyncEngine, StoreForwardEngine
from app.lab_slice.decision_engine import assess_result, authorize_release
from app.lab_slice.fhir_projector import build_bundle
from app.lab_slice.models import (
    RELEASE_PENDING,
    RELEASE_QUARANTINED,
    RELEASE_RELEASED,
)
from app.lab_slice.terminology_bindings import bind_test
from app.national.clinical_integration import ClinicalIntegrationDenied
from app.national.services.durable_clinical_core import (
    DURABLE_CORE_SCHEMA,
    RECEIPT_COMMITTED,
    RECEIPT_FAILED,
    RECEIPT_PENDING,
    DurableCoreAuthorizationError,
    DurableCoreConflict,
    DurableCoreError,
    DurableCoreIntegrityError,
    DurableCoreInterruptionError,
    DurableCoreJournal,
    DurableCoreOutbox,
    DurableCorePolicy,
    DurableCoreProjectionError,
    DurableCoreRecoveryRequired,
    DurableCoreReplayError,
    DurableNationalCoreCoordinator,
    FHIRDisclosureDenied,
    FHIRDisclosureGuard,
    LongitudinalProjectionContract,
    OfflineRecoveryPolicy,
    OutboxEnvelope,
    ResultLineageLedger,
)
from app.national.services.national_core_workflow import NationalCoreWorkflow
from app.platform.sync import SyncService
from app.services.reference.national_lab_catalog import NationalLaboratoryCatalog

# Reuse the Leap 02 synthetic fixtures without weakening or duplicating them.
# Loading by path makes this module independent of pytest import-mode details.
_LEAP02_PATH = Path(__file__).with_name("test_national_core_workflow_e2e.py")
_LEAP02_SPEC = importlib.util.spec_from_file_location(
    "gula_leap02_national_core_fixtures", _LEAP02_PATH
)
assert _LEAP02_SPEC is not None and _LEAP02_SPEC.loader is not None
_LEAP02 = importlib.util.module_from_spec(_LEAP02_SPEC)
_LEAP02_SPEC.loader.exec_module(_LEAP02)

FACILITY = _LEAP02.FACILITY
ORG = _LEAP02.ORG
PATIENT_REF = _LEAP02.PATIENT_REF
RAW_NID = _LEAP02.RAW_NID
REVIEWER = _LEAP02.REVIEWER
_adapter = _LEAP02._adapter
_case = _LEAP02._case
_command = _LEAP02._command
_consent = _LEAP02._consent
_FailingOnceSyncService = _LEAP02._FailingOnceSyncService
_IntegrationSession = _LEAP02._IntegrationSession

WORKFLOW_KEY = "NCW-DURABLE-0001"
# Authorization services use wall-clock time, while the wrapped workflow uses a
# fixed synthetic command clock. Anchor validity windows to the later of those
# clocks so the evidence remains reproducible at any execution time.
_NOW = max(datetime.now(UTC), _LEAP02.NOW).replace(microsecond=0)


def _dynamic_relationship() -> Any:
    return _LEAP02.CitizenRelationship(
        id="RELATIONSHIP-DURABLE",
        source_kind=_LEAP02.CitizenRelationshipSource.canonical_account.value,
        canonical_account_id=_LEAP02.ACCOUNT,
        citizen_id=_LEAP02.CITIZEN_ACCOUNT,
        patient_id=PATIENT_REF,
        relationship_type=_LEAP02.CitizenRelationshipType.self.value,
        status=_LEAP02.CitizenRelationshipStatus.active.value,
        purpose="TREATMENT",
        scope={"resources": ["patient_record", "patient_record:read"]},
        valid_from=_LEAP02.NOW - timedelta(minutes=5),
        verified_at=_LEAP02.NOW - timedelta(minutes=4),
        revoked_at=None,
        version=1,
    )


def _dynamic_consent(*, active: bool = True) -> Any:
    return _LEAP02.NiamConsent(
        id=_LEAP02.CONSENT_ID,
        subject_account_id=_LEAP02.CITIZEN_ACCOUNT,
        grantee_account_id=_LEAP02.ACCOUNT,
        purpose="TREATMENT",
        scope={
            "resource_domain": "patient_record",
            "actions": ["read"],
            "patient_reference": PATIENT_REF,
            "gula_citizen_identifier": _LEAP02.GULA,
        },
        resource_domain="patient_record",
        status=(
            _LEAP02.NiamConsentStatus.active.value
            if active
            else _LEAP02.NiamConsentStatus.withdrawn.value
        ),
        is_active=active,
        granted_at=_NOW - timedelta(minutes=5),
        expires_at=_NOW + timedelta(hours=1),
        version=1,
        source="user_portal",
    )


class _DynamicIntegrationSession(_IntegrationSession):
    """Leap 02 fake session with wall-clock-valid membership evidence."""

    def _memberships(self) -> list[Any]:
        return [
            _LEAP02.Membership(
                id="MEMBERSHIP-DURABLE",
                account_id=_LEAP02.ACCOUNT,
                identity_id=_LEAP02.IDENTITY,
                organization_id=ORG,
                facility_id=FACILITY,
                status=_LEAP02.MembershipStatus.active.value,
                is_active=True,
                expires_at=_NOW + timedelta(hours=1),
                revoked_at=None,
            )
        ]


def _dynamic_session(
    *,
    consents: list[Any] | None = None,
    relationships: list[Any] | None = None,
    role_key: str | None = None,
    fail_audit: bool = False,
) -> _DynamicIntegrationSession:
    return _DynamicIntegrationSession(
        consents=consents if consents is not None else [_dynamic_consent()],
        relationships=relationships if relationships is not None else [_dynamic_relationship()],
        role_key=role_key or _LEAP02.IdentityRole.PHYSICIAN.value,
        fail_audit=fail_audit,
    )


def _dynamic_command(**overrides: Any) -> Any:
    command = _command(**overrides)
    actor = command.access.actor
    session_model = _LEAP02.UserSession(
        id=actor.session.id,
        account_id=actor.session.account_id,
        is_active=True,
        expires_at=_NOW + timedelta(hours=1),
        started_at=_NOW - timedelta(minutes=5),
        mfa_used=True,
    )
    dynamic_actor = replace(actor, session=session_model)
    return replace(command, access=replace(command.access, actor=dynamic_actor))


class _AlwaysFailingSyncService(SyncService):
    def push_changes(self, changes: list[Any]) -> int:
        raise RuntimeError("synthetic persistent offline fault")


def _coordinator(
    *,
    workflow_key: str = WORKFLOW_KEY,
    policy: DurableCorePolicy | None = None,
    adapter: Any = None,
) -> tuple[DurableNationalCoreCoordinator, Any, Any]:
    persistence = adapter or _adapter()
    workflow = NationalCoreWorkflow(persistence)
    coordinator = DurableNationalCoreCoordinator(workflow, policy)
    return coordinator, workflow, _dynamic_command(workflow_key=workflow_key)


def _released_decision(case: Any) -> Any:
    catalog = NationalLaboratoryCatalog()
    catalog.seed_common_tests()
    binding = bind_test(catalog, case.result.test_code)
    decision = assess_result(
        order=case.order,
        specimen=case.specimen,
        result=case.result,
        qc=case.qc,
        binding=binding,
    )
    assert decision.status == RELEASE_PENDING
    return authorize_release(
        decision,
        reviewer=REVIEWER,
        reason="synthetic manual release",
        idempotency_key="synthetic-durable-release-key",
    )


def _bundle() -> dict[str, Any]:
    case = _case("durable-fhir")
    decision = _released_decision(case)
    catalog = NationalLaboratoryCatalog()
    catalog.seed_common_tests()
    return build_bundle(
        patient=case.patient,
        order=case.order,
        specimen=case.specimen,
        result=case.result,
        decision=decision,
        binding=bind_test(catalog, case.result.test_code),
    )


def _resource(bundle: dict[str, Any], resource_type: str) -> dict[str, Any]:
    for entry in bundle["entry"]:
        if entry["resource"]["resourceType"] == resource_type:
            return entry["resource"]
    raise AssertionError(f"synthetic bundle has no {resource_type}")


# -- Happy path, replay, and race safety ------------------------------------


def test_happy_path_commits_receipt_journal_outbox_and_offline_contract() -> None:
    coordinator, _, command = _coordinator()
    session = _dynamic_session()

    result = asyncio.run(coordinator.run(session, command))

    assert result.schema_version == DURABLE_CORE_SCHEMA
    assert result.replayed is False
    assert result.receipt.status == RECEIPT_COMMITTED
    assert result.receipt.result_digest
    assert result.workflow_result is not None
    assert result.workflow_result.audit_verification["status"] == "VALID"
    assert result.integrity["status"] == "VALID"
    assert result.outbox_summary["total"] == 1
    assert result.offline_summary["attempted"] >= 0
    assert result.offline_summary["deferred"] >= 0
    assert coordinator.journal.entries()[0].kind == "intent"
    assert coordinator.journal.entries()[-1].kind == "commit"


def test_commit_replay_is_idempotent_and_changed_input_is_rejected() -> None:
    coordinator, _, command = _coordinator()
    session = _dynamic_session()

    first = asyncio.run(coordinator.run(session, command))
    entries_after_first = len(session.audit_entries)
    replay = asyncio.run(coordinator.run(session, command))

    assert replay.replayed is True
    assert replay.receipt == first.receipt
    assert replay.workflow_result is None
    assert coordinator.outbox.summary()["total"] == 1
    assert len(session.audit_entries) == entries_after_first
    assert coordinator.journal.entries()[-1].kind == "replay"

    changed = replace(command, correlation_id=f"{command.correlation_id}-CHANGED")
    with pytest.raises(DurableCoreReplayError, match="different inputs"):
        asyncio.run(coordinator.run(session, changed))


def test_same_key_concurrency_executes_once_and_replays_once() -> None:
    coordinator, _, command = _coordinator()
    session = _dynamic_session()

    async def run_twice() -> list[Any]:
        return list(
            await asyncio.gather(
                coordinator.run(session, command),
                coordinator.run(session, command),
            )
        )

    results = asyncio.run(run_twice())
    assert sum(1 for result in results if result.replayed is False) == 1
    assert sum(1 for result in results if result.replayed is True) == 1
    assert all(result.receipt.status == RECEIPT_COMMITTED for result in results)
    assert coordinator.outbox.summary()["total"] == 1


# -- Identity, authorization, and consent preflight --------------------------


def test_unresolved_identity_conflict_vetoes_before_mutation() -> None:
    coordinator, workflow, command = _coordinator()
    conflicted = replace(
        command,
        identity=replace(command.identity, secondary_nid_hash="b" * 64),
    )

    with pytest.raises(DurableCoreAuthorizationError, match="D-IDENTITY-02"):
        asyncio.run(coordinator.run(_dynamic_session(), conflicted))

    assert coordinator.receipts == {}
    assert coordinator.outbox.summary()["total"] == 0
    assert workflow.adapter._runs == {}


def test_cross_institution_and_cross_facility_access_are_denied() -> None:
    institution, _, command = _coordinator(workflow_key="NCW-DURABLE-ORG")
    with pytest.raises(DurableCoreAuthorizationError, match="cross-institution"):
        asyncio.run(institution.run(_dynamic_session(), replace(command, organization_id="ORG-OTHER-SYN")))

    facility, _, command = _coordinator(workflow_key="NCW-DURABLE-FAC")
    with pytest.raises(DurableCoreAuthorizationError, match="cross-facility"):
        asyncio.run(facility.run(_dynamic_session(), replace(command, facility_id="FACILITY-OTHER-SYN")))


def test_expired_session_and_unverified_identity_fail_closed() -> None:
    expired, _, command = _coordinator(workflow_key="NCW-DURABLE-EXPIRED")
    actor = command.access.actor
    expired_session = _LEAP02.UserSession(
        id=actor.session.id,
        account_id=actor.session.account_id,
        is_active=True,
        expires_at=command.now - timedelta(seconds=1),
        started_at=command.now - timedelta(minutes=5),
        mfa_used=True,
    )
    expired_actor = replace(actor, session=expired_session)
    expired_command = replace(
        command,
        access=replace(command.access, actor=expired_actor),
    )
    with pytest.raises(DurableCoreAuthorizationError, match="expired"):
        asyncio.run(expired.run(_dynamic_session(), expired_command))

    unverified, _, command = _coordinator(workflow_key="NCW-DURABLE-UNVERIFIED")
    unverified_command = replace(
        command,
        identity=replace(command.identity, nid_verified=False),
    )
    with pytest.raises(DurableCoreAuthorizationError, match="not verified"):
        asyncio.run(unverified.run(_dynamic_session(), unverified_command))

    assert expired.outbox.summary()["total"] == 0
    assert unverified.outbox.summary()["total"] == 0


def test_withdrawn_consent_fails_closed_after_preflight() -> None:
    coordinator, _, command = _coordinator(workflow_key="NCW-DURABLE-CONSENT")
    session = _dynamic_session(consents=[_dynamic_consent(active=False)])

    with pytest.raises(ClinicalIntegrationDenied, match="consent"):
        asyncio.run(coordinator.run(session, command))

    assert coordinator.receipts[command.workflow_key].status == RECEIPT_FAILED
    assert coordinator.outbox.summary()["total"] == 0


# -- Interruption, recovery, and audit integrity -----------------------------


def test_post_workflow_interruption_is_retried_without_duplicate_envelope() -> None:
    coordinator, _, command = _coordinator(
        workflow_key="NCW-DURABLE-INTERRUPT",
        policy=DurableCorePolicy(fail_after_workflow=True),
    )
    with pytest.raises(DurableCoreInterruptionError, match="post-workflow"):
        asyncio.run(coordinator.run(_dynamic_session(), command))
    assert coordinator.receipts[command.workflow_key].status == RECEIPT_FAILED

    recovered = DurableNationalCoreCoordinator(coordinator.workflow)
    recovered.restore(coordinator.snapshot())
    result = asyncio.run(recovered.run(_dynamic_session(), command))

    assert result.receipt.status == RECEIPT_COMMITTED
    assert result.receipt.attempts == 2
    assert recovered.outbox.summary()["total"] == 1
    assert recovered.journal.verify()["status"] == "VALID"


def test_process_restart_snapshot_requires_explicit_recovery() -> None:
    coordinator, _, command = _coordinator(
        workflow_key="NCW-DURABLE-RESTART",
        policy=DurableCorePolicy(hard_interrupt_before_workflow=True),
    )
    with pytest.raises(KeyboardInterrupt):
        asyncio.run(coordinator.run(_dynamic_session(), command))

    assert coordinator.receipts[command.workflow_key].status == RECEIPT_PENDING

    restarted = DurableNationalCoreCoordinator(coordinator.workflow)
    restarted.restore(coordinator.snapshot())
    with pytest.raises(DurableCoreRecoveryRequired, match="recovered first"):
        asyncio.run(restarted.run(_dynamic_session(), command))

    recovery = restarted.recover()
    assert recovery.pending_found == 1
    assert recovery.recovered == 1
    assert restarted.receipts[command.workflow_key].status == RECEIPT_FAILED

    result = asyncio.run(restarted.run(_dynamic_session(), command))
    assert result.receipt.status == RECEIPT_COMMITTED
    assert restarted.journal.verify()["status"] == "VALID"


def test_audit_corruption_fails_closed_and_records_safe_metric() -> None:
    coordinator, _, command = _coordinator(workflow_key="NCW-DURABLE-AUDIT")
    with pytest.raises(ClinicalIntegrationDenied, match="canonical linkage audit failure"):
        asyncio.run(coordinator.run(_dynamic_session(fail_audit=True), command))

    assert coordinator.receipts[command.workflow_key].status == RECEIPT_FAILED
    assert coordinator.outbox.summary()["total"] == 0
    _, audit_failures = clinical_safety_metrics.snapshot()
    assert ("durable_national_core", "durable_core_receipt") in audit_failures


def test_journal_tampering_and_truncation_are_detected() -> None:
    journal = DurableCoreJournal()
    journal.append(
        kind="intent",
        workflow_key="NCW-DURABLE-JOURNAL",
        fingerprint="a" * 64,
        payload={"status": RECEIPT_PENDING},
    )
    snapshot = journal.snapshot()

    tampered = copy.deepcopy(snapshot)
    tampered["entries"][0]["payload"]["status"] = "tampered"
    with pytest.raises(DurableCoreIntegrityError, match="digest"):
        journal.restore(tampered)
    assert journal.snapshot() == snapshot
    assert journal.verify()["status"] == "VALID"

    truncated = copy.deepcopy(snapshot)
    truncated["entries"] = []
    with pytest.raises(DurableCoreIntegrityError, match="declaration"):
        journal.restore(truncated)
    assert journal.snapshot() == snapshot
    assert journal.verify()["status"] == "VALID"


def test_journal_restore_reapplies_bounds_and_allowlists() -> None:
    journal = DurableCoreJournal(DurableCorePolicy(max_journal_entries=1))
    journal.append(
        kind="intent",
        workflow_key="NCW-DURABLE-JOURNAL-BOUND",
        fingerprint="a" * 64,
        payload={"status": RECEIPT_PENDING},
    )
    snapshot = journal.snapshot()

    unsupported = copy.deepcopy(snapshot)
    unsupported["entries"][0]["kind"] = "unsupported"
    with pytest.raises(DurableCoreIntegrityError, match="unsupported journal entry kind"):
        journal.restore(unsupported)
    assert journal.snapshot() == snapshot

    extraneous = copy.deepcopy(snapshot)
    extraneous["entries"][0]["payload"]["credential"] = "synthetic-secret"
    with pytest.raises(DurableCoreIntegrityError, match="unsupported journal payload key"):
        journal.restore(extraneous)
    assert journal.verify()["status"] == "VALID"

    oversized = copy.deepcopy(snapshot)
    oversized["entries"].append(copy.deepcopy(snapshot["entries"][0]))
    oversized["declared_count"] = 2
    with pytest.raises(DurableCoreIntegrityError, match="bounded range"):
        journal.restore(oversized)
    assert journal.snapshot() == snapshot


def test_bounded_outbox_rejects_depth_cap_and_payload_conflict() -> None:
    outbox = DurableCoreOutbox(DurableCorePolicy(max_outbox_entries=1))
    first = OutboxEnvelope(
        fingerprint="a" * 64,
        workflow_key="NCW-DURABLE-CAP",
        correlation_id="NCW-DURABLE-CAP-CORR",
        entity_type="durable_core_recovery",
        entity_id="synthetic-receipt-a",
        payload_digest="b" * 64,
    )
    assert outbox.enqueue(first) is True
    assert outbox.enqueue(first) is False

    conflicting = replace(first, payload_digest="c" * 64)
    with pytest.raises(DurableCoreConflict, match="different payload"):
        outbox.enqueue(conflicting)

    other = replace(first, fingerprint="d" * 64)
    with pytest.raises(DurableCoreError, match="depth cap"):
        outbox.enqueue(other)


# -- Offline recovery and interrupted sync -----------------------------------


def test_offline_replay_is_deduplicated_with_bounded_backoff() -> None:
    store_forward = StoreForwardEngine()
    entry = OfflineQueueEntry(
        id="synthetic-offline-durable-entry",
        entity_type="patient_record",
        entity_id=PATIENT_REF,
        action="sync",
        payload={"version": 1},
        timestamp=1000.0,
    )
    assert store_forward.enqueue(entry) is True
    assert store_forward.enqueue(replace(entry)) is False

    adapter = SimpleNamespace(
        store_forward=store_forward,
        offline_sync=OfflineSyncEngine(
            sync_service=_FailingOnceSyncService(),
            store_forward=store_forward,
        ),
    )
    policy = OfflineRecoveryPolicy(
        adapter,
        DurableCorePolicy(backoff_base_seconds=1.0, backoff_cap_seconds=2.0),
    )

    failed = asyncio.run(policy.sync(now=1000.0))
    assert failed["failed"] == 1
    assert failed["scheduled"] == 1

    deferred = asyncio.run(policy.sync(now=1000.5))
    assert deferred["deferred"] == 1
    assert deferred["attempted"] == 0

    synced = asyncio.run(policy.sync(now=1010.0))
    assert synced["synced"] == 1
    assert synced["duplicates"] == 0
    assert synced["scheduled"] == 0


def test_offline_retry_exhaustion_moves_entry_to_dead_state() -> None:
    store_forward = StoreForwardEngine()
    store_forward.enqueue(
        OfflineQueueEntry(
            id="synthetic-offline-dead-entry",
            entity_type="patient_record",
            entity_id=PATIENT_REF,
            action="sync",
            payload={"version": 1},
        )
    )
    adapter = SimpleNamespace(
        store_forward=store_forward,
        offline_sync=OfflineSyncEngine(
            sync_service=_AlwaysFailingSyncService(),
            store_forward=store_forward,
        ),
    )
    policy = OfflineRecoveryPolicy(
        adapter,
        DurableCorePolicy(max_offline_attempts=1, backoff_base_seconds=1.0),
    )

    summary = asyncio.run(policy.sync(now=2000.0))
    assert summary["failed"] == 1
    assert summary["dead"] == 1
    assert summary["newly_dead"] == 1
    assert summary["scheduled"] == 0


def test_offline_recovery_snapshot_rejects_conflicting_duplicate_id() -> None:
    store_forward = StoreForwardEngine()
    entry = OfflineQueueEntry(
        id="synthetic-offline-conflict-entry",
        entity_type="patient_record",
        entity_id=PATIENT_REF,
        action="sync",
        payload={"version": 1},
    )
    store_forward.enqueue(entry)
    snapshot = list(store_forward.snapshot())

    assert store_forward.restore(snapshot) is None
    conflict = copy.deepcopy(snapshot)
    conflict.append({**conflict[0], "payload": {"version": 2}})
    with pytest.raises(ValueError, match="duplicate entry id"):
        store_forward.restore(conflict)


def test_offline_retry_schedule_restore_rejects_unsafe_entries() -> None:
    policy = OfflineRecoveryPolicy(
        SimpleNamespace(),
        DurableCorePolicy(max_offline_entries=3),
    )
    schedule = [{"id": "synthetic-offline-retry-a", "next_retry_at": 1000.0}]
    policy.restore(schedule)
    assert policy.snapshot() == schedule

    with pytest.raises(DurableCoreIntegrityError, match="duplicate id"):
        policy.restore(
            [
                {"id": "synthetic-offline-retry-a", "next_retry_at": 1000.0},
                {"id": "synthetic-offline-retry-a", "next_retry_at": 2000.0},
            ]
        )
    with pytest.raises(DurableCoreIntegrityError, match="non-finite"):
        policy.restore([{"id": "synthetic-offline-retry-a", "next_retry_at": float("nan")}])
    bounded = OfflineRecoveryPolicy(
        SimpleNamespace(),
        DurableCorePolicy(max_offline_entries=1),
    )
    with pytest.raises(DurableCoreIntegrityError, match="depth cap"):
        bounded.restore(
            [
                {"id": "synthetic-offline-retry-a", "next_retry_at": 1000.0},
                {"id": "synthetic-offline-retry-b", "next_retry_at": 1000.0},
            ]
        )
    assert policy.snapshot() == schedule


# -- FHIR disclosure pre-check -----------------------------------------------


def test_fhir_guard_accepts_valid_synthetic_bundle() -> None:
    guard = FHIRDisclosureGuard()
    result = guard.assert_valid(
        _bundle(),
        expected_patient_reference=PATIENT_REF,
        expected_organization_id="synthetic-facility-001",
    )
    assert result.valid is True
    assert result.errors == ()
    assert "Observation" in result.resource_types
    assert result.reference_count > 0


def test_fhir_guard_rejects_cross_patient_invalid_reference_and_phi() -> None:
    guard = FHIRDisclosureGuard()

    cross_patient = _bundle()
    _resource(cross_patient, "Observation")["subject"] = {
        "reference": "Patient/synthetic-patient-other"
    }
    with pytest.raises(FHIRDisclosureDenied, match="different patient"):
        guard.assert_valid(cross_patient, expected_patient_reference=PATIENT_REF)

    invalid_reference = _bundle()
    _resource(invalid_reference, "Specimen")["request"] = [
        {"reference": "ServiceRequest/synthetic-missing-request"}
    ]
    with pytest.raises(FHIRDisclosureDenied, match="missing"):
        guard.assert_valid(invalid_reference, expected_patient_reference=PATIENT_REF)

    phi = _bundle()
    _resource(phi, "Patient")["national_id"] = RAW_NID
    with pytest.raises(FHIRDisclosureDenied, match=r"raw identifier|disallowed fields"):
        guard.assert_valid(phi, expected_patient_reference=PATIENT_REF)


def test_fhir_guard_rejects_mismatched_organization_reference() -> None:
    guard = FHIRDisclosureGuard()
    wrong_organization = _bundle()
    _resource(wrong_organization, "Patient")["managingOrganization"] = {
        "reference": "Organization/synthetic-organization-other"
    }
    with pytest.raises(FHIRDisclosureDenied, match="different organization"):
        guard.assert_valid(
            wrong_organization,
            expected_patient_reference=PATIENT_REF,
            expected_organization_id="synthetic-facility-001",
        )


def test_fhir_guard_rejects_unsupported_terminology_and_missing_ucum_code() -> None:
    guard = FHIRDisclosureGuard()

    unsupported = _bundle()
    _resource(unsupported, "ServiceRequest")["code"]["coding"][0]["system"] = "urn:unapproved"
    with pytest.raises(FHIRDisclosureDenied, match="unsupported code system"):
        guard.assert_valid(unsupported, expected_patient_reference=PATIENT_REF)

    no_ucum = _bundle()
    _resource(no_ucum, "Observation")["valueQuantity"].pop("code")
    with pytest.raises(FHIRDisclosureDenied, match="UCUM"):
        guard.assert_valid(no_ucum, expected_patient_reference=PATIENT_REF)


# -- Laboratory lineage, quarantine, and longitudinal projection -------------


def test_duplicate_registration_conflict_and_correction_lineage() -> None:
    ledger = ResultLineageLedger()
    case = _case("durable-lineage")

    first = ledger.register(case)
    replayed = ledger.register(case)
    assert first.revision == 1
    assert replayed.replayed is True
    assert replayed.fingerprint == first.fingerprint

    with pytest.raises(DurableCoreConflict, match="different payload"):
        ledger.register(replace(case, result=replace(case.result, value=96.0)))

    decision = _released_decision(case)
    assert decision.status == RELEASE_RELEASED
    ledger.mark_released(
        result_id=case.result.result_id,
        decision_status=decision.status,
        decision_result_id=decision.result_id,
    )
    with pytest.raises(DurableCoreError, match="explicit release"):
        ledger.mark_released(
            result_id=case.result.result_id,
            decision_status=RELEASE_PENDING,
            decision_result_id=case.result.result_id,
        )

    correction = ledger.correct(
        case,
        corrected_value=96.0,
        reason="synthetic_correction",
        reviewer=REVIEWER,
        corrected_result_id="synthetic-result-durable-lineage-corrected",
    )
    assert correction.registration.revision == 2
    assert correction.registration.supersedes == case.result.result_id
    assert correction.registration.status == "pending_review"
    assert correction.registration.released is False

    with pytest.raises(DurableCoreConflict, match="already has a correction"):
        ledger.correct(
            case,
            corrected_value=97.0,
            reason="synthetic_second_correction",
            reviewer=REVIEWER,
            corrected_result_id="synthetic-result-durable-lineage-second",
        )

    restored = ResultLineageLedger()
    restored.restore(ledger.snapshot())
    assert len(restored.snapshot()) == 2


def test_correction_cannot_reuse_or_overwrite_registered_identifiers() -> None:
    ledger = ResultLineageLedger()
    case = _case("durable-lineage-id-reuse")
    other = _case("durable-lineage-id-other")
    ledger.register(case)
    ledger.register(other)
    decision = _released_decision(case)
    ledger.mark_released(
        result_id=case.result.result_id,
        decision_status=decision.status,
        decision_result_id=decision.result_id,
    )
    before = ledger.snapshot()

    with pytest.raises(DurableCoreConflict, match="new result id"):
        ledger.correct(
            case,
            corrected_value=96.0,
            reason="synthetic_same_id_correction",
            reviewer=REVIEWER,
            corrected_result_id=case.result.result_id,
        )
    assert ledger.snapshot() == before

    with pytest.raises(DurableCoreConflict, match="already registered"):
        ledger.correct(
            case,
            corrected_value=96.0,
            reason="synthetic_registered_id_correction",
            reviewer=REVIEWER,
            corrected_result_id=other.result.result_id,
        )
    assert ledger.snapshot() == before


def test_critical_result_is_quarantined_and_cannot_be_released() -> None:
    case = _case("durable-critical", value=350.0)
    catalog = NationalLaboratoryCatalog()
    catalog.seed_common_tests()
    decision = assess_result(
        order=case.order,
        specimen=case.specimen,
        result=case.result,
        qc=case.qc,
        binding=bind_test(catalog, case.result.test_code),
    )
    assert decision.status == RELEASE_QUARANTINED
    assert (
        authorize_release(
            decision,
            reviewer=REVIEWER,
            reason="synthetic unauthorized release attempt",
            idempotency_key="synthetic-unauthorized",
        )
        is decision
    )

    projection = LongitudinalProjectionContract()
    with pytest.raises(DurableCoreProjectionError, match="unreleased"):
        projection.project(
            case,
            decision,
            expected_patient_reference=PATIENT_REF,
        )


def test_failed_ehr_projection_is_replayable_and_cross_patient_denied() -> None:
    case = _case("durable-projection")
    decision = _released_decision(case)
    projection = LongitudinalProjectionContract()

    with pytest.raises(DurableCoreProjectionError, match="interruption"):
        projection.project(
            case,
            decision,
            expected_patient_reference=PATIENT_REF,
            fail=True,
        )
    assert sum(projection.snapshot()["failures"].values()) == 1

    event = projection.project(case, decision, expected_patient_reference=PATIENT_REF)
    replay = projection.project(case, decision, expected_patient_reference=PATIENT_REF)
    assert event.status == "projected_envelope_only"
    assert event.synthetic is True
    assert replay.event_id == event.event_id
    assert replay.replayed is True

    with pytest.raises(DurableCoreProjectionError, match="different patient"):
        projection.project(
            case,
            decision,
            expected_patient_reference="synthetic-patient-other",
        )


# -- Privacy and boundary evidence -------------------------------------------


def test_public_evidence_and_recovery_snapshot_never_expose_phi() -> None:
    coordinator, _, command = _coordinator(workflow_key="NCW-DURABLE-PRIVACY")

    result = asyncio.run(coordinator.run(_dynamic_session(), command))
    serialized = json.dumps(
        {
            "result": result.to_public_dict(),
            "journal": coordinator.journal.snapshot(),
            "outbox": coordinator.outbox.snapshot(),
            "offline": coordinator.offline.snapshot(),
        },
        sort_keys=True,
    )
    assert RAW_NID not in serialized
    assert "national_id" not in serialized
    assert "contact_code" not in serialized
    assert "credential" not in serialized
    assert result.workflow_result is not None
    assert result.workflow_result.citizen_view["medical_result_withheld"] is True


def test_pre_workflow_partial_failure_is_retried_without_duplicate_envelope() -> None:
    interrupted, _, command = _coordinator(
        workflow_key="NCW-DURABLE-PARTIAL",
        policy=DurableCorePolicy(fail_before_workflow=True),
    )

    with pytest.raises(DurableCoreInterruptionError, match="pre-workflow"):
        asyncio.run(interrupted.run(_dynamic_session(), command))

    assert interrupted.receipts[command.workflow_key].status == RECEIPT_FAILED
    assert interrupted.outbox.summary()["total"] == 0

    retried = DurableNationalCoreCoordinator(interrupted.workflow)
    retried.restore(interrupted.snapshot())
    result = asyncio.run(retried.run(_dynamic_session(), command))

    assert result.receipt.status == RECEIPT_COMMITTED
    assert result.receipt.attempts == 2
    assert retried.outbox.summary()["total"] == 1
    assert retried.journal.verify()["status"] == "VALID"


def test_offline_engine_recovery_snapshot_restores_queue_and_dedupe_markers() -> None:
    store_forward = StoreForwardEngine()
    entry = OfflineQueueEntry(
        id="synthetic-offline-engine-recovery-entry",
        entity_type="patient_record",
        entity_id=PATIENT_REF,
        action="sync",
        payload={"version": 1},
    )
    assert store_forward.enqueue(entry) is True

    engine = OfflineSyncEngine(sync_service=SyncService(), store_forward=store_forward)
    summary = asyncio.run(engine.sync_all())
    assert summary["synced"] == 1

    snapshot = engine.recovery_snapshot()
    assert len(snapshot["queue"]) == 1
    assert len(snapshot["processed"]) == 1

    restored = OfflineSyncEngine(
        sync_service=SyncService(),
        store_forward=StoreForwardEngine(),
    )
    restored.restore_recovery_snapshot(snapshot)
    assert restored._store_forward.queue_size()["completed"] == 1
    assert len(restored._processed) == 1

    invalid = copy.deepcopy(snapshot)
    invalid["processed"][0]["fingerprint"] = ""
    with pytest.raises(ValueError, match="incomplete dedupe marker"):
        restored.restore_recovery_snapshot(invalid)
