"""Producer-consumer conformance for explicit Health Core event semantics.

Workstream B closure of WS-E finding F-01. Real clinical and lab services emit
events; the real WS-C catalogue validates them. The legacy overloads are
exercised as reconstructed pre-1.1.0 shapes, never as fabricated service output.

Synthetic data only: no DB, no MPI, no network, no production activation.
"""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.health_core.clinical import (
    ClinicalContext,
    DiagnosisStatus,
    EncounterStatus,
    RecordScope,
    Severity,
)
from app.health_core.clinical.services import TRANSITION_EVENTS
from app.health_core.clinical.validation import require_synthetic_ref
from app.health_core.common import (
    EVENT_SCHEMA_VERSION,
    LEGACY_DIAGNOSIS_RESOLVE_ACTION,
    LEGACY_ENCOUNTER_START_STATUS,
    LEGACY_EVENT_TYPE_MAP,
    LEGACY_TRANSITION_KEY,
    AggregateType,
    DomainEvent,
    EventType,
    InvalidSyntheticReferenceError,
    canonical_event_type,
    is_synthetic_id,
    new_event,
    new_synthetic_id,
)
from app.health_core.contracts import (
    EVENT_CATALOGUE,
    EventContractViolation,
    validate_domain_event,
)
from app.health_core.contracts.events import (
    EVENT_SCHEMA_VERSION as CONTRACT_EVENT_SCHEMA_VERSION,
)
from app.health_core.identity import SyntheticPatientRegistry
from app.health_core.lab import (
    LabWorkflowService,
    Priority,
    SpecimenStatus,
    VerificationDecision,
)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
CLINICAL_SERVICES_SOURCE = BACKEND_ROOT / "app" / "health_core" / "clinical" / "services.py"
TENANT = "SYN-LAB-0001"
PRACTITIONER = "SYN-PRC-0001"
FACILITY = "SYN-FAC-0001"
ACTOR = "SYN-ACT-00000001"
REVIEWER = "SYN-REV-00000001"

EXPLICIT_LIFECYCLE_VALUES = {
    EventType.ORGANIZATION_REGISTERED: "organization.registered",
    EventType.ENCOUNTER_STARTED: "encounter.started",
    EventType.DIAGNOSIS_RESOLVED: "diagnosis.resolved",
    EventType.PRACTITIONER_DEACTIVATED: "practitioner.deactivated",
}


class _ClinicalSlice:
    """Real clinical producer output, including both fixed lifecycle changes."""

    def __init__(self, registry: SyntheticPatientRegistry, patient_ref: str) -> None:
        self.context = ClinicalContext(identity=registry)
        self.context.practitioners.register(
            tenant_id=TENANT,
            idempotency_key=PRACTITIONER,
            role="physician",
            qualification="MBBS",
        )
        organization = self.context.organizations.register_organization(
            tenant_id=TENANT,
            idempotency_key="SYN-ORG-0001",
            label="synthetic-hospital",
        )
        self.context.organizations.register_facility(
            tenant_id=TENANT,
            idempotency_key=FACILITY,
            organization_id=organization.organization_id,
            label="synthetic-ward",
            facility_type="hospital",
        )
        self.encounter = self.context.encounters.create(
            tenant_id=TENANT,
            idempotency_key="SYN-ENC-0001",
            patient_ref=patient_ref,
            practitioner_id=PRACTITIONER,
            facility_id=FACILITY,
            reason="event semantics conformance",
        )
        self.started = self.context.encounters.transition(
            tenant_id=TENANT,
            encounter_id=self.encounter.encounter_id,
            to_status=EncounterStatus.IN_PROGRESS,
            idempotency_key="SYN-TRN-0001",
        )
        self.context.encounters.add_note(
            tenant_id=TENANT,
            encounter_id=self.encounter.encounter_id,
            idempotency_key="SYN-NOT-0001",
            author_practitioner_id=PRACTITIONER,
            text="synthetic progress note",
        )
        self.diagnosis = self.context.diagnoses.record(
            tenant_id=TENANT,
            idempotency_key="SYN-DIA-0001",
            patient_ref=patient_ref,
            encounter_id=self.encounter.encounter_id,
            code="E11.9",
            description="synthetic diabetes",
            severity=Severity.MODERATE,
        )
        self.resolved = self.context.diagnoses.resolve(
            tenant_id=TENANT,
            diagnosis_id=self.diagnosis.diagnosis_id,
            idempotency_key="SYN-TRN-0002",
        )
        self.context.observations.record(
            tenant_id=TENANT,
            idempotency_key="SYN-OBS-0001",
            patient_ref=patient_ref,
            encounter_id=self.encounter.encounter_id,
            code="8867-4",
            display="synthetic heart rate",
            value=78.0,
            unit="bpm",
            recorded_at=datetime.now(UTC),
        )
        self.context.medical_records.open(
            scope=RecordScope(tenant_id=TENANT, patient_refs=(patient_ref,))
        )

    def events(self) -> tuple[DomainEvent, ...]:
        return self.context.event_history()

    def of_type(self, event_type: EventType) -> tuple[DomainEvent, ...]:
        return tuple(event for event in self.events() if event.event_type == event_type.value)


@pytest.fixture
def clinical_slice(synthetic_registry, synthetic_patient) -> _ClinicalSlice:
    return _ClinicalSlice(synthetic_registry, synthetic_patient.ref)


# --- Requirement 1: explicit shared vocabulary --------------------------------


def test_explicit_lifecycle_values_have_exact_dotted_strings() -> None:
    for event_type, value in EXPLICIT_LIFECYCLE_VALUES.items():
        assert event_type.value == value
    assert len(set(EXPLICIT_LIFECYCLE_VALUES)) == 4


def test_legacy_overloaded_values_are_retained_unchanged() -> None:
    assert EventType.ENCOUNTER_CREATED.value == "encounter.created"
    assert EventType.DIAGNOSIS_RECORDED.value == "diagnosis.recorded"
    assert set(LEGACY_EVENT_TYPE_MAP) == {
        EventType.ENCOUNTER_CREATED,
        EventType.DIAGNOSIS_RECORDED,
    }


def test_every_event_type_including_lifecycle_has_a_catalogue_definition() -> None:
    assert set(EVENT_CATALOGUE) == set(EventType)
    for event_type in EXPLICIT_LIFECYCLE_VALUES:
        assert event_type in EVENT_CATALOGUE


@pytest.mark.parametrize(
    ("event_type", "aggregate", "required_keys"),
    (
        (
            EventType.ORGANIZATION_REGISTERED,
            AggregateType.ORGANIZATION,
            frozenset({"organization_ref", "tenant_id"}),
        ),
        (
            EventType.PRACTITIONER_DEACTIVATED,
            AggregateType.PRACTITIONER,
            frozenset({"practitioner_ref", "tenant_id"}),
        ),
        (
            EventType.ENCOUNTER_STARTED,
            AggregateType.ENCOUNTER,
            frozenset(
                {"encounter_ref", "tenant_id", "patient_ref", "from_status", "to_status"}
            ),
        ),
        (
            EventType.DIAGNOSIS_RESOLVED,
            AggregateType.DIAGNOSIS,
            frozenset({"diagnosis_ref", "encounter_ref", "patient_ref", "status"}),
        ),
    ),
)
def test_lifecycle_definitions_match_aggregates_and_real_payload_keys(
    event_type: EventType, aggregate: AggregateType, required_keys: frozenset[str]
) -> None:
    definition = EVENT_CATALOGUE[event_type]
    assert definition.aggregate_type is aggregate
    assert definition.required_payload_keys == required_keys
    sample = new_event(
        event_type=event_type.value,
        aggregate_type=aggregate.value,
        aggregate_id=new_synthetic_id("AGG"),
        tenant_id=new_synthetic_id("LAB"),
        payload={key: new_synthetic_id("PLD") for key in required_keys},
    )
    validate_domain_event(sample)


@pytest.mark.parametrize(
    ("event_type", "missing_key"),
    (
        (EventType.ENCOUNTER_STARTED, "to_status"),
        (EventType.DIAGNOSIS_RESOLVED, "diagnosis_ref"),
    ),
)
def test_lifecycle_definitions_fail_closed_on_missing_required_key(
    event_type: EventType, missing_key: str
) -> None:
    definition = EVENT_CATALOGUE[event_type]
    payload = {
        key: new_synthetic_id("PLD")
        for key in definition.required_payload_keys
        if key != missing_key
    }
    event = new_event(
        event_type=event_type.value,
        aggregate_type=definition.aggregate_type.value,
        aggregate_id=new_synthetic_id("AGG"),
        tenant_id=new_synthetic_id("LAB"),
        payload=payload,
    )
    with pytest.raises(EventContractViolation, match="missing payload keys"):
        validate_domain_event(event)


# --- Requirements 2 and 5: real emitters no longer reuse legacy names ---------


def test_encounter_start_emits_explicit_event_with_all_legacy_payload_keys(
    clinical_slice: _ClinicalSlice,
) -> None:
    started = clinical_slice.of_type(EventType.ENCOUNTER_STARTED)
    assert len(started) == 1
    event = started[0]
    assert event.aggregate_type == AggregateType.ENCOUNTER.value
    assert event.aggregate_id == clinical_slice.encounter.encounter_id
    assert set(event.payload) >= {
        "encounter_ref",
        "tenant_id",
        "patient_ref",
        LEGACY_TRANSITION_KEY,
        "from_status",
        "to_status",
        "version",
    }
    assert event.payload["from_status"] == "planned"
    assert event.payload["to_status"] == LEGACY_ENCOUNTER_START_STATUS
    assert event.payload["version"] == 2
    validate_domain_event(event)


def test_no_encounter_created_transition_reuse_remains(
    clinical_slice: _ClinicalSlice,
) -> None:
    created = clinical_slice.of_type(EventType.ENCOUNTER_CREATED)
    assert len(created) == 1
    assert not any(event.payload.get(LEGACY_TRANSITION_KEY) for event in created)
    assert TRANSITION_EVENTS[EncounterStatus.IN_PROGRESS] is EventType.ENCOUNTER_STARTED
    assert TRANSITION_EVENTS[EncounterStatus.IN_PROGRESS] is not EventType.ENCOUNTER_CREATED


def test_diagnosis_resolve_emits_explicit_event_with_all_legacy_payload_keys(
    clinical_slice: _ClinicalSlice,
) -> None:
    resolved = clinical_slice.of_type(EventType.DIAGNOSIS_RESOLVED)
    assert len(resolved) == 1
    event = resolved[0]
    assert event.aggregate_type == AggregateType.DIAGNOSIS.value
    assert event.aggregate_id == clinical_slice.diagnosis.diagnosis_id
    assert set(event.payload) >= {
        "diagnosis_ref",
        "encounter_ref",
        "patient_ref",
        LEGACY_TRANSITION_KEY,
        "status",
        "version",
    }
    assert event.payload[LEGACY_TRANSITION_KEY] == LEGACY_DIAGNOSIS_RESOLVE_ACTION
    assert event.payload["status"] == DiagnosisStatus.RESOLVED.value
    assert event.payload["version"] == 2
    validate_domain_event(event)


def test_no_diagnosis_recorded_transition_reuse_remains(
    clinical_slice: _ClinicalSlice,
) -> None:
    recorded = clinical_slice.of_type(EventType.DIAGNOSIS_RECORDED)
    assert len(recorded) == 1
    assert all(LEGACY_TRANSITION_KEY not in event.payload for event in recorded)
    assert not clinical_slice.of_type(EventType.DIAGNOSIS_RESOLVED)[0].payload.get("code")


def test_note_added_aggregate_is_still_encounter(clinical_slice: _ClinicalSlice) -> None:
    notes = clinical_slice.of_type(EventType.NOTE_ADDED)
    assert len(notes) == 1
    assert notes[0].aggregate_type == AggregateType.ENCOUNTER.value
    assert notes[0].aggregate_id == clinical_slice.encounter.encounter_id
    validate_domain_event(notes[0])


def test_emitter_source_has_no_legacy_type_inside_transition_or_resolve() -> None:
    tree = ast.parse(CLINICAL_SERVICES_SOURCE.read_text(encoding="utf-8"))

    def event_type_references(node: ast.AST) -> set[str]:
        return {
            child.attr
            for child in ast.walk(node)
            if isinstance(child, ast.Attribute)
            and isinstance(child.value, ast.Name)
            and child.value.id == "EventType"
        }

    usages: dict[str, set[str]] = {}
    for class_node in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
        for method in (node for node in class_node.body if isinstance(node, ast.FunctionDef)):
            for attribute in event_type_references(method):
                usages.setdefault(attribute, set()).add(method.name)
    module_level = event_type_references(tree) - set(usages)

    assert usages["ENCOUNTER_CREATED"] == {"create"}
    assert usages["DIAGNOSIS_RECORDED"] == {"record"}
    assert usages["DIAGNOSIS_RESOLVED"] == {"resolve"}
    assert "ENCOUNTER_STARTED" in module_level
    assert "ENCOUNTER_STARTED" not in usages
    assert TRANSITION_EVENTS[EncounterStatus.IN_PROGRESS] is EventType.ENCOUNTER_STARTED


def test_all_real_clinical_events_validate_against_catalogue(
    clinical_slice: _ClinicalSlice,
) -> None:
    events = clinical_slice.events()
    assert len(events) == 9
    for event in events:
        assert isinstance(event, DomainEvent)
        validate_domain_event(event)


def test_real_lab_events_still_validate_against_catalogue(
    synthetic_registry, synthetic_patient
) -> None:
    lab = LabWorkflowService(identity=synthetic_registry)
    order = lab.place_order(
        tenant_id=TENANT,
        patient_ref=synthetic_patient.ref,
        test_codes=["GLU"],
        idempotency_key="SYN-KEY-0001",
        priority=Priority.URGENT,
        actor_id=ACTOR,
    )
    specimen = lab.register_specimen(
        tenant_id=TENANT,
        order_id=order.order_id,
        barcode="SYN-BAR-00000001",
        actor_id=ACTOR,
    )
    for target in (SpecimenStatus.COLLECTED, SpecimenStatus.RECEIVED):
        specimen = lab.transition_specimen(
            tenant_id=TENANT, specimen_id=specimen.specimen_id, to_status=target, actor_id=ACTOR
        )
    execution = lab.enter_testing(
        tenant_id=TENANT, specimen_id=specimen.specimen_id, actor_id=ACTOR
    )
    lab.complete_testing(
        tenant_id=TENANT, execution_id=execution.execution_id, actor_id=ACTOR
    )
    result = lab.record_result(
        tenant_id=TENANT,
        order_id=order.order_id,
        specimen_id=specimen.specimen_id,
        patient_ref=synthetic_patient.ref,
        test_code="GLU",
        value=92.0,
        unit="mg/dL",
        idempotency_key="SYN-KEY-0002",
        actor_id=ACTOR,
    )
    lab.verify_result(
        tenant_id=TENANT,
        result_id=result.result_id,
        reviewer_id=REVIEWER,
        decision=VerificationDecision.VERIFIED,
        idempotency_key="SYN-KEY-0003",
    )
    events = lab.all_events(tenant_id=TENANT)
    assert len(events) == 11
    for event in events:
        validate_domain_event(event)
        assert EventType(event.event_type) not in set(EXPLICIT_LIFECYCLE_VALUES)


# --- Requirements 4 and 6: compatibility, versioning, immutability ------------


def test_event_schema_version_is_explicit_and_shared(clinical_slice: _ClinicalSlice) -> None:
    assert EVENT_SCHEMA_VERSION == "1.1.0"
    assert CONTRACT_EVENT_SCHEMA_VERSION == EVENT_SCHEMA_VERSION
    assert all(event.schema_version == EVENT_SCHEMA_VERSION for event in clinical_slice.events())


def test_new_event_signature_remains_backward_compatible() -> None:
    old_style = new_event(
        event_type=EventType.PATIENT_REGISTERED.value,
        aggregate_type=AggregateType.PATIENT.value,
        aggregate_id=new_synthetic_id("AGG"),
        tenant_id=new_synthetic_id("LAB"),
        payload={"legacy_key": "SYN-PAT-0001"},
    )
    explicit = new_event(
        event_type=EventType.ORGANIZATION_REGISTERED.value,
        aggregate_type=AggregateType.ORGANIZATION.value,
        aggregate_id=new_synthetic_id("AGG"),
        tenant_id=new_synthetic_id("LAB"),
        schema_version="1.1.0",
    )
    assert old_style.schema_version == EVENT_SCHEMA_VERSION
    assert explicit.schema_version == "1.1.0"
    assert set(old_style.to_dict()) == {
        "event_id",
        "event_type",
        "aggregate_type",
        "aggregate_id",
        "tenant_id",
        "occurred_at",
        "version",
        "payload",
        "schema_version",
    }


def test_legacy_event_type_map_is_immutable_and_targets_explicit_events() -> None:
    assert LEGACY_EVENT_TYPE_MAP[EventType.ENCOUNTER_CREATED] == (
        EventType.ENCOUNTER_STARTED,
    )
    assert LEGACY_EVENT_TYPE_MAP[EventType.DIAGNOSIS_RECORDED] == (
        EventType.DIAGNOSIS_RESOLVED,
    )
    with pytest.raises(TypeError):
        LEGACY_EVENT_TYPE_MAP[EventType.ENCOUNTER_CREATED] = ()  # type: ignore[index]


def test_canonical_mapping_disambiguates_reconstructed_legacy_encounter_event(
    clinical_slice: _ClinicalSlice,
) -> None:
    started = clinical_slice.of_type(EventType.ENCOUNTER_STARTED)[0]
    legacy = replace(started, event_type=EventType.ENCOUNTER_CREATED.value)
    assert canonical_event_type(legacy.event_type, payload=legacy.payload) is (
        EventType.ENCOUNTER_STARTED
    )
    assert canonical_event_type(legacy.event_type) is EventType.ENCOUNTER_CREATED
    assert canonical_event_type(started.event_type, payload=started.payload) is (
        EventType.ENCOUNTER_STARTED
    )


def test_canonical_mapping_disambiguates_reconstructed_legacy_diagnosis_event(
    clinical_slice: _ClinicalSlice,
) -> None:
    resolved = clinical_slice.of_type(EventType.DIAGNOSIS_RESOLVED)[0]
    legacy = replace(resolved, event_type=EventType.DIAGNOSIS_RECORDED.value)
    assert canonical_event_type(legacy.event_type, payload=legacy.payload) is (
        EventType.DIAGNOSIS_RESOLVED
    )
    assert canonical_event_type(legacy.event_type) is EventType.DIAGNOSIS_RECORDED
    assert canonical_event_type(resolved.event_type, payload=resolved.payload) is (
        EventType.DIAGNOSIS_RESOLVED
    )


def test_canonical_mapping_keeps_genuine_create_and_record_events(
    clinical_slice: _ClinicalSlice,
) -> None:
    created = clinical_slice.of_type(EventType.ENCOUNTER_CREATED)[0]
    recorded = clinical_slice.of_type(EventType.DIAGNOSIS_RECORDED)[0]
    assert canonical_event_type(created.event_type, payload=created.payload) is (
        EventType.ENCOUNTER_CREATED
    )
    assert canonical_event_type(recorded.event_type, payload=recorded.payload) is (
        EventType.DIAGNOSIS_RECORDED
    )


def test_canonical_mapping_fails_closed_on_unregistered_type() -> None:
    with pytest.raises(ValueError):
        canonical_event_type("unknown.event")


def test_event_ids_timestamps_and_records_are_synthetic_and_immutable(
    clinical_slice: _ClinicalSlice,
) -> None:
    events = clinical_slice.events()
    assert events
    for event in events:
        assert is_synthetic_id(event.event_id)
        assert is_synthetic_id(event.aggregate_id)
        assert is_synthetic_id(event.tenant_id)
        assert datetime.fromisoformat(event.occurred_at).tzinfo is not None
        assert event.occurred_at.endswith("+00:00")
    with pytest.raises(FrozenInstanceError):
        events[0].event_type = "unknown.event"
    with pytest.raises(ValueError, match="timezone-aware"):
        new_event(
            event_type=EventType.ENCOUNTER_STARTED.value,
            aggregate_type=AggregateType.ENCOUNTER.value,
            aggregate_id=new_synthetic_id("AGG"),
            tenant_id=new_synthetic_id("LAB"),
            occurred_at=datetime(2026, 1, 1),
        )


def _call_target(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def test_emit_validates_against_catalogue_before_appending_to_the_sink() -> None:
    """F-01 regression: the catalogue validator is wired into the producer.

    A definition-only ``validate_domain_event`` gives false assurance if no
    emitter calls it. This structural assertion fails if the call is removed or
    reordered after the append.
    """
    tree = ast.parse(CLINICAL_SERVICES_SOURCE.read_text(encoding="utf-8"))
    emit = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_emit"
    )
    calls = [node for node in ast.walk(emit) if isinstance(node, ast.Call)]
    validation = [call for call in calls if _call_target(call) == "validate_domain_event"]
    append = [call for call in calls if _call_target(call) == "append"]
    assert len(validation) == 1
    assert len(append) == 1
    assert validation[0].lineno < append[0].lineno


def test_is_synthetic_id_is_a_shape_check_and_strict_validation_is_separate() -> None:
    """I-1 regression: lock in the honest 'shape check, not proof of generation' claim.

    ``is_synthetic_id`` must accept concise hand-written fixture shapes but reject
    non-SYN values; strict per-type guarantees are provided by the dedicated
    validators, not by this cheap predicate. This prevents the overclaiming
    docstring from silently returning.
    """
    # Genuinely generated ids are accepted.
    assert is_synthetic_id(new_synthetic_id("PAT"))
    # Hand-written fixture shapes deliberately pass (this is the documented contract).
    assert is_synthetic_id("SYN-KEY-0001")
    assert is_synthetic_id("SYN-!!!!!!!!!")
    # Non-SYN / too-short values are rejected by the shape check.
    assert is_synthetic_id("12345678901") is False
    assert is_synthetic_id("SYN-OK") is False
    # Strict prefix validation is a separate boundary that DOES reject weak shapes.
    with pytest.raises(InvalidSyntheticReferenceError):
        require_synthetic_ref("SYN-KEY-0001", field="patient_ref", prefix="SYN-PAT-")
    # A correctly prefixed strict reference still passes.
    assert (
        require_synthetic_ref("SYN-PAT-0001", field="patient_ref", prefix="SYN-PAT-")
        == "SYN-PAT-0001"
    )
