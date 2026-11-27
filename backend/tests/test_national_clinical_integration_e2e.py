"""National Clinical Integration Layer — synthetic end-to-end evidence.

All identifiers are synthetic and bounded. This matrix composes canonical
service-layer primitives: encounter service, identity/MPI guards, clinical
command guard, synthetic lab slice, FHIR validation, consent, Authorization
Decision Engine, canonical audit, offline sync, and kernel recovery. It does not
create routes, DDL, production configuration, real patient data, or a second
identity/MPI/LIMS/FHIR/event system.

The matrix proves composition and fail-closed behavior only. It does not change
the Wave 05.3 release posture or declare production readiness.
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
from app.clinical.command_guard import ClinicalCommandGuard
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
from app.integration.fhir_r4_exchange import FHIRContractError, validate_synthetic_bundle
from app.integration.offline import (
    ConflictResolver,
    DeltaSyncEngine,
    OfflineQueueEntry,
    OfflineSyncEngine,
)
from app.lab_slice.decision_engine import assess_result, authorize_release
from app.lab_slice.event_pipeline import SyntheticLabEventPipeline
from app.lab_slice.fhir_projector import build_bundle
from app.lab_slice.models import (
    RELEASE_QUARANTINED,
    RELEASE_RELEASED,
    CustodyEvent,
    SyntheticLabCase,
    SyntheticOrder,
    SyntheticPatient,
    SyntheticQCControl,
    SyntheticResult,
    SyntheticSpecimen,
)
from app.lab_slice.terminology_bindings import bind_test
from app.national.clinical_integration import (
    ChainBinding,
    ClinicalIntegrationConflict,
    ClinicalIntegrationDenied,
    NationalClinicalIntegration,
)
from app.national.enums import EncounterStatus, EncounterType
from app.national.fhir.validation import FHIRValidationEngine
from app.national.intelligence.laboratory.analytics import DeltaCheckEngine
from app.national.services.identity_access import (
    PATIENT_LINKAGE,
    IdentityAccessContext,
    IdentityAccessDeniedError,
    IdentityRole,
    assert_identity_access_v2,
)
from app.national.services.identity_governance import IdentityEvidenceError, LinkageReviewer
from app.national.services.patient_identity_safety import FacilityIdentityRecord
from app.platform.sync import SyncService
from app.services.mpi.identity_safety import NID_CONFLICT, classify_nid_match
from app.services.offline_sync_service import (
    ConflictResolution,
    SyncOperation,
)
from app.services.offline_sync_service import (
    OfflineSyncEngine as ClinicalOfflineSyncEngine,
)
from app.services.reference.national_lab_catalog import NationalLaboratoryCatalog
from fastapi import HTTPException

CORR = "NCI-E2E-20261125"
ORG = "ORG-SYN-NCI"
FACILITY = "FACILITY-SYN-NCI"
ACCOUNT = "ACCOUNT-NCI"
CITIZEN_ACCOUNT = "ACCOUNT-CITIZEN-NCI"
IDENTITY = "IDENTITY-NCI"
PERSON = "PERSON-NCI"
GULA = "199000000001"
GULA_SECONDARY = "199000000002"
RAW_NID = "123456789012"
NID_HASH = "a" * 64
REVIEWER = "synthetic-reviewer-nci"
CONSENT_ID = "CONSENT-SYN-NCI-001"
PATIENT_REF = "synthetic-patient-nci"


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


def _relationship(
    *,
    patient_id: str = PATIENT_REF,
    purpose: str = "TREATMENT",
    relationship_type: CitizenRelationshipType = CitizenRelationshipType.self,
    active: bool = True,
) -> CitizenRelationship:
    now = datetime.now(UTC)
    return CitizenRelationship(
        id="RELATIONSHIP-NCI",
        source_kind=CitizenRelationshipSource.canonical_account.value,
        canonical_account_id=ACCOUNT,
        citizen_id=CITIZEN_ACCOUNT,
        patient_id=patient_id,
        relationship_type=relationship_type.value,
        status=(
            CitizenRelationshipStatus.active.value
            if active
            else CitizenRelationshipStatus.revoked.value
        ),
        purpose=purpose,
        scope={"resources": ["patient_record", "patient_record:read"]},
        valid_from=now - timedelta(minutes=5),
        verified_at=now - timedelta(minutes=4),
        revoked_at=None if active else now,
        version=1,
    )


class _IntegrationSession:
    """Table-routed fake AsyncSession for canonical decision/consent/audit."""

    def __init__(
        self,
        *,
        consents: list[NiamConsent] | None = None,
        relationships: list[CitizenRelationship] | None = None,
        role_key: str = IdentityRole.PHYSICIAN.value,
        membership_facility: str = FACILITY,
        membership_org: str = ORG,
        permission_exists: bool = True,
        include_membership: bool = True,
    ) -> None:
        self.consents = list(consents or [])
        self.relationships = list(relationships) if relationships is not None else [_relationship()]
        self.role_key = role_key
        self.audit_entries: list[Any] = []
        self.membership_facility = membership_facility
        self.membership_org = membership_org
        self.permission_exists = permission_exists
        self.include_membership = include_membership

    def _memberships(self) -> list[Membership]:
        if not self.include_membership:
            return []
        return [
            Membership(
                id="MEMBERSHIP-NCI",
                account_id=ACCOUNT,
                identity_id=IDENTITY,
                organization_id=self.membership_org,
                facility_id=self.membership_facility,
                status=MembershipStatus.active.value,
                is_active=True,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
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
            today = datetime.now(UTC).date()
            return _Result(
                [
                    SimpleNamespace(
                        id="EMPLOYMENT-NCI",
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
                return _Result(scalar=ORG if self.include_membership else None)
            return _Result(self._memberships())
        if "niam_role_assignments" in sql:
            return _Result(["patient_record.read"] if self.permission_exists else [])
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
        return "permission-id" if self.permission_exists else None

    async def get(self, model: Any, identifier: Any) -> Any:
        if "NiamConsent" in getattr(model, "__name__", ""):
            return next((item for item in self.consents if item.id == identifier), None)
        return None

    def add(self, entry: Any) -> None:
        if not getattr(entry, "id", None):
            entry.id = f"synthetic-audit-{len(self.audit_entries) + 1}"
        self.audit_entries.append(entry)

    async def flush(self) -> None:
        return None


def _actor(*, active: bool = True) -> AuthorizationActor:
    return AuthorizationActor(
        account=Account(
            id=ACCOUNT,
            identity_id=IDENTITY,
            status=AccountStatus.active.value if active else AccountStatus.suspended.value,
            is_active=active,
            is_locked=False,
        ),
        session=UserSession(
            id="SESSION-NCI",
            account_id=ACCOUNT,
            is_active=True,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            started_at=datetime.now(UTC) - timedelta(minutes=5),
            mfa_used=True,
        ),
    )


def _consent(
    *, active: bool = True, patient_reference: str | None = None, **overrides: Any
) -> NiamConsent:
    scope = dict(overrides.pop("scope", {}) or {})
    scope.setdefault("resource_domain", "patient_record")
    scope.setdefault("actions", ["read"])
    if patient_reference is not None:
        scope["patient_reference"] = patient_reference
    scope.setdefault("patient_reference", PATIENT_REF)
    scope.setdefault("gula_citizen_identifier", GULA)
    values: dict[str, Any] = {
        "id": CONSENT_ID,
        "subject_account_id": CITIZEN_ACCOUNT,
        "grantee_account_id": ACCOUNT,
        "purpose": "TREATMENT",
        "scope": scope,
        "resource_domain": "patient_record",
        "status": NiamConsentStatus.active.value if active else NiamConsentStatus.withdrawn.value,
        "is_active": active,
        "granted_at": datetime.now(UTC) - timedelta(minutes=5),
        "expires_at": datetime.now(UTC) + timedelta(hours=1),
        "version": 1,
        "source": "user_portal",
    }
    values.update(overrides)
    return NiamConsent(**values)


def _ade_request(**overrides: Any) -> AuthorizationRequest:
    values = {
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
        },
    }
    values.update(overrides)
    return AuthorizationRequest(**values)


def _identity_context(**overrides: Any) -> IdentityAccessContext:
    values = {
        "decision": AuthorizationDecision.allow(),
        "role": IdentityRole.PHYSICIAN,
        "actor_id": ACCOUNT,
        "organization_id": ORG,
        "facility_id": FACILITY,
        "purpose": "TREATMENT",
        "action": PATIENT_LINKAGE,
        "requested_fields": ("gula_citizen_identifier", "patient_record_reference", "facility_id"),
        "gula_citizen_identifier": GULA,
        "national_id_hash": NID_HASH,
        "now": datetime.now(UTC),
        "consent_required": True,
        "consent_present": True,
        "relationship_required": True,
        "patient_relationship": "self",
    }
    values.update(overrides)
    return IdentityAccessContext(**values)


def _access_kwargs(*, binding: ChainBinding | None = None, **overrides: Any) -> dict[str, Any]:
    """Trusted binding arguments for the authorized-access stage."""
    patient_reference = binding.patient_reference if binding is not None else PATIENT_REF
    values: dict[str, Any] = {
        "actor": _actor(),
        "request": _ade_request(
            resource_id=patient_reference,
            resource_context={
                "exists": True,
                "organization_id": ORG,
                "facility_id": FACILITY,
                "patient_id": patient_reference,
            },
        ),
        "consent_id": CONSENT_ID,
        "citizen_account_id": CITIZEN_ACCOUNT,
        "expected_gula_identifier": GULA,
        "national_id_hash": NID_HASH,
    }
    if binding is not None:
        values["binding"] = binding
    values.update(overrides)
    return values


def _facility_records(
    *, conflict: bool = False
) -> tuple[FacilityIdentityRecord, FacilityIdentityRecord]:
    secondary_hash = "b" * 64 if conflict else NID_HASH
    primary = FacilityIdentityRecord(
        facility_id=FACILITY,
        local_patient_id="synthetic-local-nci-a",
        gula_citizen_identifier=GULA,
        nid_hash=NID_HASH,
        nid_verified=True,
        birth_year=1990,
        birth_month=1,
        birth_day=1,
        phone_last10="0000000001",
    )
    secondary = FacilityIdentityRecord(
        facility_id="FACILITY-SYN-NCI-B",
        local_patient_id="synthetic-local-nci-b",
        gula_citizen_identifier=GULA_SECONDARY,
        nid_hash=secondary_hash,
        nid_verified=True,
        birth_year=1990,
        birth_month=1,
        birth_day=1,
        phone_last10="0000000001",
    )
    return primary, secondary


def _reviewer() -> LinkageReviewer:
    return LinkageReviewer(name=REVIEWER, user_id=42)


def _catalog() -> NationalLaboratoryCatalog:
    catalog = NationalLaboratoryCatalog()
    catalog.seed_common_tests()
    return catalog


def _delta() -> DeltaCheckEngine:
    engine = DeltaCheckEngine()
    engine.set_delta_threshold("GLU", 2.0, 20.0)
    return engine


def _case(
    suffix: str = "001", *, value: float = 90.0, order_status: str = "completed"
) -> SyntheticLabCase:
    patient = SyntheticPatient(
        patient_id=f"synthetic-patient-{suffix}",
        age_years=35,
        region="synthetic-region",
    )
    order = SyntheticOrder(
        order_id=f"synthetic-order-{suffix}",
        patient_id=patient.patient_id,
        test_code="GLU",
        status=order_status,
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
                recorded_at="2026-11-25T12:00:00+00:00",
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


@pytest.fixture()
def integration() -> NationalClinicalIntegration:
    return NationalClinicalIntegration(
        correlation_id=CORR,
        organization_id=ORG,
        facility_id=FACILITY,
        reviewer=REVIEWER,
        review_reason="synthetic documented review",
        release_idempotency_key="nci-release-0001",
        event_idempotency_key="nci-event-0001",
        catalog=_catalog(),
        delta_engine=_delta(),
    )


class _CommandDb:
    """Minimal session shape for the canonical clinical command guard."""

    def __init__(self) -> None:
        self.receipts: list[Any] = []

    def query(self, _model: Any) -> _CommandDb:
        return self

    def filter(self, *_conditions: Any) -> _CommandDb:
        return self

    def first(self) -> Any:
        return self.receipts[0] if self.receipts else None

    def add(self, receipt: Any) -> None:
        self.receipts.append(receipt)

    def flush(self) -> None:
        return None

    def rollback(self) -> None:
        return None


@pytest.mark.integration
def test_happy_path_synthetic_chain_and_authorized_citizen_read(db, make_lab, integration) -> None:
    from app.national.services.encounter_service import complete_encounter, create_encounter

    lab = make_lab(name="NCI Synthetic Lab")
    case = _case("happy", value=95.0)
    encounter = create_encounter(
        db,
        {
            "patient_id": case.patient.patient_id,
            "encounter_type": EncounterType.OUTPATIENT,
            "status": EncounterStatus.PLANNED,
            "facility_id": FACILITY,
            "practitioner_id": "synthetic-practitioner-nci",
            "organization_id": ORG,
            "period_start": datetime.now(UTC),
            "reason_description": "Synthetic national integration follow-up",
            "lab_id": lab.id,
        },
    )
    db.flush()
    assert encounter.patient_id == case.patient.patient_id
    assert (
        complete_encounter(db, encounter.id, "synthetic-reviewer-user").status
        is EncounterStatus.COMPLETED
    )

    primary, secondary = _facility_records()
    linkage = integration.link_health_identity(
        primary,
        secondary,
        reviewer=_reviewer(),
        reason="synthetic corroborated cross-facility review",
        evidence_reference="synthetic-evidence-nci-001",
        decided_at=datetime.now(UTC),
    )
    assert linkage.action == "LINK_APPROVED"
    assert primary.gula_citizen_identifier == GULA

    encounter_reference = f"synthetic-encounter-{str(encounter.id)[:8].lower()}"
    assert str(encounter.patient_id) == case.patient.patient_id
    with pytest.raises(ClinicalIntegrationConflict, match="encounter reference does not match"):
        integration.bind_chain(
            case,
            patient_reference=case.patient.patient_id,
            encounter_reference="synthetic-encounter-not-the-created-visit",
            gula_citizen_identifier=GULA,
            national_id_hash=NID_HASH,
            encounter=encounter,
        )
    binding = integration.bind_chain(
        case,
        patient_reference=case.patient.patient_id,
        encounter_reference=encounter_reference,
        gula_citizen_identifier=GULA,
        national_id_hash=NID_HASH,
        encounter=encounter,
        linkage=linkage,
        profile_hash=NID_HASH,
        candidate_hash=NID_HASH,
        candidate_verified=True,
        corroborated=True,
    )
    decision = integration.validate_and_release(case)
    assert decision.status == RELEASE_RELEASED
    bundle = integration.project_clinical_record(case, decision)
    assert validate_synthetic_bundle(bundle) == []
    validator = FHIRValidationEngine()
    assert all(validator.validate(entry["resource"]).valid for entry in bundle["entry"])
    assert "national_id" not in json.dumps(bundle)
    summary = integration.publish_result_event(case, decision)
    assert summary.delivered == (f"{case.result.result_id}-lims.result.validated",)

    other_decision = integration.validate_and_release(_case("record-decision-swap", value=90.0))
    with pytest.raises(ClinicalIntegrationConflict, match="release decision does not match"):
        integration.build_record(
            linkage=linkage,
            binding=binding,
            decision=other_decision,
            bundle=None,
            event_summary=None,
            access=None,
        )

    session = _IntegrationSession(
        consents=[_consent(patient_reference=case.patient.patient_id)],
        relationships=[_relationship(patient_id=case.patient.patient_id)],
    )
    linkage_event = asyncio.run(integration.record_linkage_audit(session, linkage, binding))
    assert linkage_event.event_type == "IDENTITY_OPERATION_WAVE053"
    access = asyncio.run(
        integration.authorize_citizen_access(session, **_access_kwargs(binding=binding)),
    )
    assert access.decision.allowed is True
    assert access.patient_reference == binding.patient_reference
    assert access.result_id == binding.result_id
    assert "gula_citizen_identifier" in access.projected_fields
    assert access.identity_audit_event.event_type == "IDENTITY_OPERATION_WAVE053"
    assert access.audit_event.event_type == "NATIONAL_CLINICAL_ACCESS"
    event_types = [item.event_type for item in session.audit_entries]
    assert event_types.count("IDENTITY_OPERATION_WAVE053") == 2
    assert "CONSENT_CHECKED" in event_types
    assert "NATIONAL_CLINICAL_ACCESS" in event_types

    record = integration.build_record(
        linkage=linkage,
        binding=binding,
        decision=decision,
        bundle=bundle,
        event_summary=summary,
        access=access,
    )
    assert record.stages[-1].name == "authorized_citizen_access"
    assert record.correlation_id == CORR

    unbound_session = _IntegrationSession(consents=[_consent()])
    unbound_access = asyncio.run(
        integration.authorize_citizen_access(unbound_session, **_access_kwargs())
    )
    with pytest.raises(ClinicalIntegrationConflict, match="different patient"):
        integration.build_record(
            linkage=linkage,
            binding=binding,
            decision=decision,
            bundle=bundle,
            event_summary=summary,
            access=unbound_access,
        )

    assert integration.audit_event_for_linkage(linkage, binding).correlation_id == CORR
    assert (
        CanonicalAuditService._hash(session.audit_entries[-1])
        == session.audit_entries[-1].entry_hash
    )


def test_wrong_patient_reference_never_produces_fhir_projection(integration) -> None:
    case = _case("wrong-patient")
    wrong = replace(
        case,
        specimen=replace(case.specimen, patient_id="synthetic-patient-999"),
    )
    decision = authorize_release(
        assess_result(
            order=wrong.order,
            specimen=wrong.specimen,
            result=wrong.result,
            qc=wrong.qc,
            binding=bind_test(_catalog(), wrong.result.test_code),
            delta_engine=_delta(),
        ),
        reviewer=REVIEWER,
        reason="synthetic documented review",
        idempotency_key="nci-wrong-patient",
    )
    with pytest.raises(FHIRContractError, match="same patient"):
        build_bundle(
            patient=wrong.patient,
            order=wrong.order,
            specimen=wrong.specimen,
            result=wrong.result,
            decision=decision,
            binding=bind_test(_catalog(), wrong.result.test_code),
        )
    with pytest.raises(ClinicalIntegrationConflict, match="specimen patient"):
        integration.bind_chain(
            wrong,
            patient_reference=wrong.patient.patient_id,
            encounter_reference="synthetic-encounter-wrong",
            gula_citizen_identifier=GULA,
            national_id_hash=NID_HASH,
        )


@pytest.mark.integration
def test_duplicate_order_key_cannot_create_a_second_clinical_command() -> None:
    command_db = _CommandDb()
    guard = ClinicalCommandGuard(
        command_db,
        actor_user_id=7,
        lab_id=7,
        actor_role="lab_admin",
    )
    payload = {"patient_reference": PATIENT_REF, "test_code": "GLU"}
    receipt = guard.claim(
        operation="create_laboratory_order",
        resource_type="laboratory_order",
        resource_id="synthetic-order-duplicate",
        idempotency_key="NCI-E2E-DUP-ORDER",
        payload=payload,
    )
    assert receipt.status == "claimed"
    assert len(command_db.receipts) == 1

    with pytest.raises(HTTPException) as replay:
        guard.claim(
            operation="create_laboratory_order",
            resource_type="laboratory_order",
            resource_id="synthetic-order-duplicate",
            idempotency_key="NCI-E2E-DUP-ORDER",
            payload=payload,
        )
    assert replay.value.status_code == 409
    assert replay.value.detail["error"] == "clinical_command_already_processed"

    with pytest.raises(HTTPException) as collision:
        guard.claim(
            operation="create_laboratory_order",
            resource_type="laboratory_order",
            resource_id="synthetic-order-duplicate",
            idempotency_key="NCI-E2E-DUP-ORDER",
            payload={**payload, "test_code": "HB"},
        )
    assert collision.value.status_code == 409
    assert collision.value.detail["error"] == "idempotency_key_reused"
    assert len(command_db.receipts) == 1


def test_duplicate_result_event_is_deduped_and_audited(integration) -> None:
    pipeline = SyntheticLabEventPipeline()
    event = SyntheticLabEventPipeline.released_event("synthetic-result-dup")
    assert pipeline.publish(event) is True
    assert pipeline.publish(event) is False
    first = pipeline.process()
    assert first.delivered == ("synthetic-result-dup-lims.result.validated",)
    assert first.duplicates == ()
    replay = SyntheticLabEventPipeline.released_event("synthetic-result-dup", version=2)
    assert pipeline.publish(replay) is True
    second = pipeline.process()
    assert second.delivered == ()
    assert second.duplicates == ("synthetic-result-dup-lims.result.validated",)
    outcomes = [outcome.outcome for outcome in pipeline.audit.decisions]
    assert outcomes.count("delivered") == 1
    assert outcomes.count("duplicate") == 1

    case = _case("dup-integration")
    decision = integration.validate_and_release(case)
    expected = f"{case.result.result_id}-lims.result.validated"
    first = integration.publish_result_event(case, decision)
    replay = integration.publish_result_event(case, decision)
    assert first.delivered == (expected,)
    assert replay.delivered == ()
    assert replay.duplicates == (expected,)


@pytest.mark.asyncio
async def test_network_interruption_fails_closed_then_replays_once() -> None:
    sync_service = SyncService()
    delta = DeltaSyncEngine(sync_service)
    calls: list[int] = []

    def failing_push(changes: Any) -> Any:
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("synthetic transient fault")
        return sync_service.push_changes(changes)

    delta.push_delta = failing_push
    engine = OfflineSyncEngine(sync_service=sync_service, delta_sync=delta)
    assert engine.store_forward.enqueue(
        OfflineQueueEntry(
            id="synthetic-nci-fault",
            entity_type="clinical_note",
            entity_id="synthetic-note-nci",
            action="sync",
            payload={"version": 4, "text": "synthetic"},
            timestamp=2.0,
        ),
    )
    failed = await engine.sync_all()
    assert failed["failed"] == 1
    recovered = await engine.sync_all()
    assert recovered["synced"] == 1
    assert len(calls) == 2
    assert len(sync_service.pull_changes()) == 1


def test_clinical_record_conflict_preserves_both_versions_and_requires_manual_review() -> None:
    engine = ClinicalOfflineSyncEngine(device_secret="synthetic-secret")
    first = SyncOperation(
        operation_id="synthetic-nci-local",
        entity_type="clinical_note",
        entity_id="synthetic-note-nci",
        operation="update",
        data={"text": "local synthetic version"},
        vector_clock={"device-a": 1},
        device_id="device-a",
        user_id="synthetic-user-a",
        timestamp=100.0,
    )
    first.signature = engine._sign_operation(first.operation_id, first.data, first.device_id)
    second = SyncOperation(
        operation_id="synthetic-nci-remote",
        entity_type="clinical_note",
        entity_id="synthetic-note-nci",
        operation="update",
        data={"text": "remote synthetic version"},
        vector_clock={"device-b": 1},
        device_id="device-b",
        user_id="synthetic-user-b",
        timestamp=110.0,
    )
    second.signature = engine._sign_operation(second.operation_id, second.data, second.device_id)
    engine.receive_operation(first)
    engine.receive_operation(second)
    conflict = engine.get_conflicts()[0]
    assert conflict.resolution is ConflictResolution.MANUAL
    assert conflict.operation_a.data == {"text": "local synthetic version"}
    assert conflict.operation_b.data == {"text": "remote synthetic version"}
    assert (
        engine.resolve_conflict(
            conflict.conflict_id,
            ConflictResolution.LAST_WRITE_WINS,
            resolver="system",
        )
        is None
    )
    assert conflict.resolved_at is None
    assert (
        engine.resolve_conflict(
            conflict.conflict_id,
            ConflictResolution.MANUAL,
            resolver=REVIEWER,
        )
        is not None
    )
    assert conflict.resolved_at is not None


def test_critical_result_is_quarantined_and_never_released_or_broadcast(integration) -> None:
    case = _case("critical-e2e", value=350.0)
    decision = integration.validate_and_release(case)
    assert decision.status == RELEASE_QUARANTINED
    assert "critical_value" in decision.reasons
    assert "outside_reference_range" in decision.reasons
    assert (
        authorize_release(
            decision,
            reviewer=REVIEWER,
            reason="synthetic documented review",
            idempotency_key="nci-critical-release",
        )
        == decision
    )
    with pytest.raises(ClinicalIntegrationDenied):
        integration.project_clinical_record(case, decision)
    with pytest.raises(ClinicalIntegrationDenied):
        integration.publish_result_event(case, decision)

    released_other = integration.validate_and_release(_case("release-swap", value=90.0))
    with pytest.raises(ClinicalIntegrationConflict, match="different result"):
        integration.project_clinical_record(case, released_other)
    with pytest.raises(ClinicalIntegrationConflict, match="different result"):
        integration.publish_result_event(case, released_other)

    with pytest.raises(ClinicalIntegrationDenied, match="configured reviewer"):
        primary, secondary = _facility_records()
        integration.link_health_identity(
            primary,
            secondary,
            reviewer=LinkageReviewer(name="synthetic-other-reviewer", user_id=43),
            reason="synthetic review",
            evidence_reference="synthetic-evidence-nci-reviewer",
            decided_at=datetime.now(UTC),
        )
    with pytest.raises(ClinicalIntegrationConflict, match="identity linkage"):
        primary, secondary = _facility_records(conflict=True)
        integration.link_health_identity(
            primary,
            secondary,
            reviewer=_reviewer(),
            reason="synthetic review",
            evidence_reference="synthetic-evidence-nci-critical",
            decided_at=datetime.now(UTC),
        )


@pytest.mark.integration
def test_unauthorized_actor_denied_at_canonical_and_scope_boundaries(integration) -> None:
    assert (
        classify_nid_match(
            profile_hash=NID_HASH,
            candidate_hash="b" * 64,
            candidate_verified=True,
            corroborated=True,
        ).disposition
        == NID_CONFLICT
    )
    with pytest.raises(IdentityAccessDeniedError):
        assert_identity_access_v2(
            _identity_context(
                decision=AuthorizationDecision.deny(AuthorizationReason.permission_missing)
            ),
        )
    session = _IntegrationSession(consents=[_consent()])
    with pytest.raises(ClinicalIntegrationDenied, match="organization scope mismatch"):
        asyncio.run(
            integration.authorize_citizen_access(
                session,
                **_access_kwargs(request=_ade_request(organization_id="ORG-SYN-OTHER")),
            ),
        )

    wrong_subject_session = _IntegrationSession(
        consents=[_consent(subject_account_id="ACCOUNT-OTHER-NCI")],
    )
    with pytest.raises(ClinicalIntegrationDenied, match="consent subject is not the citizen"):
        asyncio.run(
            integration.authorize_citizen_access(wrong_subject_session, **_access_kwargs()),
        )

    wrong_patient_session = _IntegrationSession(
        consents=[
            _consent(
                scope={
                    "resource_domain": "patient_record",
                    "actions": ["read"],
                    "patient_reference": "synthetic-patient-other",
                    "gula_citizen_identifier": GULA,
                },
            ),
        ],
    )
    with pytest.raises(ClinicalIntegrationDenied, match="consent patient reference mismatch"):
        asyncio.run(
            integration.authorize_citizen_access(wrong_patient_session, **_access_kwargs()),
        )

    unsupported_role_session = _IntegrationSession(
        consents=[_consent()],
        role_key="UNSUPPORTED_CLINICAL_ROLE",
    )
    with pytest.raises(ClinicalIntegrationDenied, match="not approved for clinical access"):
        asyncio.run(
            integration.authorize_citizen_access(unsupported_role_session, **_access_kwargs()),
        )
    assert any(
        item.event_type == "NATIONAL_CLINICAL_ACCESS_DENIED"
        and item.reason_code == "IDENTITY_ROLE_UNSUPPORTED"
        for item in unsupported_role_session.audit_entries
    )

    missing_relationship_session = _IntegrationSession(consents=[_consent()], relationships=[])
    with pytest.raises(ClinicalIntegrationDenied, match="patient relationship is not uniquely"):
        asyncio.run(
            integration.authorize_citizen_access(missing_relationship_session, **_access_kwargs()),
        )
    assert any(
        item.event_type == "NATIONAL_CLINICAL_ACCESS_DENIED"
        and item.reason_code == "PATIENT_RELATIONSHIP_NOT_VERIFIED"
        for item in missing_relationship_session.audit_entries
    )

    mismatch_case = _case("binding-mismatch")
    mismatch_binding = integration.bind_chain(
        mismatch_case,
        patient_reference=mismatch_case.patient.patient_id,
        encounter_reference="synthetic-encounter-binding-mismatch",
        gula_citizen_identifier=GULA,
        national_id_hash=NID_HASH,
    )
    with pytest.raises(ClinicalIntegrationDenied, match="authorized patient does not match"):
        asyncio.run(
            integration.authorize_citizen_access(
                session,
                **_access_kwargs(
                    binding=mismatch_binding,
                    request=_ade_request(
                        resource_id=PATIENT_REF,
                        resource_context={
                            "exists": True,
                            "organization_id": ORG,
                            "facility_id": FACILITY,
                            "patient_id": PATIENT_REF,
                        },
                    ),
                ),
            ),
        )


@pytest.mark.integration
def test_absent_consent_denies_citizen_result_access(integration) -> None:
    session = _IntegrationSession(consents=[])
    with pytest.raises(ClinicalIntegrationDenied, match="consent is absent or invalid"):
        asyncio.run(integration.authorize_citizen_access(session, **_access_kwargs()))
    with pytest.raises(IdentityAccessDeniedError, match="consent is required"):
        assert_identity_access_v2(_identity_context(consent_present=False))


@pytest.mark.integration
def test_cross_organization_access_denied_at_scope_and_tenant_layers(integration) -> None:
    session = _IntegrationSession(
        consents=[_consent()],
        membership_facility="FACILITY-SYN-OTHER",
    )
    with pytest.raises(ClinicalIntegrationDenied, match="canonical authorization denied"):
        asyncio.run(integration.authorize_citizen_access(session, **_access_kwargs()))

    local_session = _IntegrationSession(consents=[_consent()])
    other_facility_request = _ade_request(
        facility_id="FACILITY-SYN-OTHER",
        resource_context={
            "exists": True,
            "organization_id": ORG,
            "facility_id": "FACILITY-SYN-OTHER",
            "patient_id": PATIENT_REF,
        },
    )
    with pytest.raises(ClinicalIntegrationDenied, match="facility scope mismatch"):
        asyncio.run(
            integration.authorize_citizen_access(
                local_session,
                **_access_kwargs(request=other_facility_request),
            ),
        )
    assert (
        classify_nid_match(
            profile_hash=NID_HASH,
            candidate_hash=None,
            candidate_verified=True,
            corroborated=True,
        ).disposition
        != NID_CONFLICT
    )


@pytest.mark.integration
@pytest.mark.kernel
def test_restart_after_interruption_replays_outbox_without_duplicate_side_effect(
    integration,
) -> None:
    from app.kernel import Kernel

    pipeline = SyntheticLabEventPipeline()
    event = SyntheticLabEventPipeline.released_event("synthetic-result-restart")
    assert pipeline.publish(event) is True
    assert pipeline.process().delivered == ("synthetic-result-restart-lims.result.validated",)
    replay = SyntheticLabEventPipeline.released_event("synthetic-result-restart", version=2)
    assert pipeline.publish(replay) is True
    assert pipeline.process().duplicates == ("synthetic-result-restart-lims.result.validated",)

    first_kernel = Kernel()
    assert first_kernel is not None
    Kernel.reset_instance()
    second_kernel = Kernel()
    assert second_kernel is not first_kernel

    case = _case("restart")
    decision = integration.validate_and_release(case)
    expected = f"{case.result.result_id}-lims.result.validated"
    assert integration.publish_result_event(case, decision).delivered == (expected,)
    restarted = NationalClinicalIntegration(
        correlation_id=CORR,
        organization_id=ORG,
        facility_id=FACILITY,
        reviewer=REVIEWER,
        review_reason="synthetic documented review",
        release_idempotency_key="nci-release-0001",
        event_idempotency_key="nci-event-0001",
        catalog=_catalog(),
        delta_engine=_delta(),
        event_pipeline=integration.event_pipeline,
    )
    replay = restarted.publish_result_event(case, decision)
    assert replay.delivered == ()
    assert replay.duplicates == (expected,)

    sync_service = SyncService()
    engine = OfflineSyncEngine(sync_service=sync_service)
    assert engine.store_forward.enqueue(
        OfflineQueueEntry(
            id="synthetic-restart-entry",
            entity_type="clinical_note",
            entity_id="synthetic-note-restart",
            action="sync",
            payload={"version": 1, "text": "synthetic"},
            timestamp=3.0,
        ),
    )
    assert (
        engine.store_forward.enqueue(
            OfflineQueueEntry(
                id="synthetic-restart-entry",
                entity_type="clinical_note",
                entity_id="synthetic-note-restart",
                action="sync",
                payload={"version": 1, "text": "synthetic"},
                timestamp=3.0,
            ),
        )
        is False
    )
    assert asyncio.run(engine.sync_all())["synced"] == 1
    assert asyncio.run(engine.sync_all())["synced"] == 0
    assert len(sync_service.pull_changes()) == 1


@pytest.mark.integration
def test_redacted_canonical_audit_and_fail_closed_access_denial(integration) -> None:
    case = _case("redaction", value=90.0)
    primary, secondary = _facility_records()
    linkage = integration.link_health_identity(
        primary,
        secondary,
        reviewer=_reviewer(),
        reason="synthetic corroborated review",
        evidence_reference="synthetic-evidence-redaction",
        decided_at=datetime.now(UTC),
    )
    binding = integration.bind_chain(
        case,
        patient_reference=case.patient.patient_id,
        encounter_reference="synthetic-encounter-redaction",
        gula_citizen_identifier=GULA,
        national_id_hash=NID_HASH,
        profile_hash=NID_HASH,
        candidate_hash=NID_HASH,
        candidate_verified=True,
        corroborated=True,
    )
    event = integration.audit_event_for_linkage(linkage, binding)
    serialized = repr(event)
    assert RAW_NID not in serialized
    assert "raw_national_id" not in serialized
    assert "national_number" not in serialized
    assert "raw_nfc_data" not in serialized
    assert "national_id_hash" in serialized
    assert event.correlation_id == CORR
    assert event.actor_id == REVIEWER
    assert event.organization_id == ORG
    assert event.facility_id == FACILITY

    raw_linkage = replace(linkage, evidence_reference=RAW_NID)
    with pytest.raises(IdentityEvidenceError, match="full national ID"):
        integration.audit_event_for_linkage(raw_linkage, binding)

    session = _IntegrationSession(consents=[_consent()])
    access = asyncio.run(integration.authorize_citizen_access(session, **_access_kwargs()))
    assert RAW_NID not in repr(access.audit_event)
    assert RAW_NID not in repr(access.identity_audit_event)

    denied_session = _IntegrationSession(
        consents=[_consent()],
        relationships=[_relationship(purpose="RESEARCH")],
    )
    with pytest.raises(ClinicalIntegrationDenied, match="consent purpose mismatch"):
        asyncio.run(
            integration.authorize_citizen_access(
                denied_session,
                **_access_kwargs(request=_ade_request(purpose="RESEARCH")),
            ),
        )
    assert any(
        item.event_type == "NATIONAL_CLINICAL_ACCESS_DENIED"
        for item in denied_session.audit_entries
    )

    verification = asyncio.run(CanonicalAuditService(session).verify(organization_id=ORG))
    assert verification["status"] == "VALID", verification
    assert verification["entries_checked"] >= 1
