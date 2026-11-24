"""FHIR R4 adapter round-trip and shape conformance for every supported entity.

All fixtures are synthetic, frozen Health Core entities. No database, network,
router or national identity surface is involved.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from app.health_core.clinical.context import ClinicalContext
from app.health_core.clinical.entities import (
    Diagnosis,
    DiagnosisStatus,
    Encounter,
    EncounterStatus,
    Facility,
    FacilityType,
    Observation,
    Organization,
    Practitioner,
    PractitionerRole,
    Severity,
)
from app.health_core.common import new_synthetic_id
from app.health_core.fhir import (
    SUPPORTED_FHIR_RESOURCE_TYPES,
    UNSUPPORTED_FHIR_RESOURCE_TYPES,
    FhirR4Adapter,
    UnsupportedFhirResourceError,
)
from app.health_core.fhir.support import (
    IDENTIFIER_SYSTEM,
    PROFILE_BASE,
    REFERENCE_TARGET_PREFIXES,
    profile_for,
)
from app.health_core.identity.port import PatientRef
from app.health_core.identity.synthetic import SyntheticPatientRegistry
from app.health_core.lab.models import (
    LabOrder,
    LabOrderStatus,
    LabResult,
    Priority,
    ResultAmendment,
    Specimen,
    SpecimenStatus,
)
from app.health_core.lab.services import LabWorkflowService

ADAPTER = FhirR4Adapter()
TENANT = "SYN-LAB-0001"
PATIENT = PatientRef(ref="SYN-PAT-000000000001", tenant_id=TENANT, label="fixture-alpha")
MOMENT = "2026-01-01T00:00:00+00:00"
PRC = "SYN-PRC-000000000001"
ORG = "SYN-ORG-000000000001"
FAC = "SYN-FAC-000000000001"
ENC = "SYN-ENC-000000000001"
DIA = "SYN-DIA-000000000001"
OBS = "SYN-OBS-000000000001"
ORD = "SYN-ORD-000000000001"
SPC = "SYN-SPC-000000000001"
RES = "SYN-RES-000000000001"


def practitioner() -> Practitioner:
    """Build a frozen synthetic practitioner."""
    return Practitioner(
        practitioner_id=PRC,
        tenant_id=TENANT,
        role=PractitionerRole.PHYSICIAN,
        qualification="synthetic qualification",
        active=True,
    )


def organization() -> Organization:
    """Build a frozen synthetic organisation."""
    return Organization(organization_id=ORG, tenant_id=TENANT, label="Synthetic Org", active=True)


def facility() -> Facility:
    """Build a frozen synthetic facility."""
    return Facility(
        facility_id=FAC,
        tenant_id=TENANT,
        organization_id=ORG,
        label="Synthetic Hospital",
        facility_type=FacilityType.HOSPITAL,
        active=True,
    )


def encounter() -> Encounter:
    """Build a frozen synthetic encounter in a non-default lifecycle state."""
    return Encounter(
        encounter_id=ENC,
        tenant_id=TENANT,
        patient_ref=PATIENT.ref,
        practitioner_id=PRC,
        facility_id=FAC,
        status=EncounterStatus.ADMITTED,
        reason="synthetic review",
        version=3,
        created_at=MOMENT,
    )


def diagnosis() -> Diagnosis:
    """Build a frozen synthetic problem entry."""
    return Diagnosis(
        diagnosis_id=DIA,
        tenant_id=TENANT,
        patient_ref=PATIENT.ref,
        encounter_id=ENC,
        code="J18.9",
        description="Synthetic pneumonia",
        severity=Severity.MODERATE,
        status=DiagnosisStatus.ACTIVE,
        asserted_at=MOMENT,
        resolved_at=None,
        version=2,
    )


def observation() -> Observation:
    """Build a frozen synthetic coded observation."""
    return Observation(
        observation_id=OBS,
        tenant_id=TENANT,
        patient_ref=PATIENT.ref,
        encounter_id=ENC,
        code="8867-4",
        display="Heart rate",
        value=72.0,
        unit="bpm",
        recorded_at=MOMENT,
    )


def order() -> LabOrder:
    """Build a frozen synthetic lab order."""
    return LabOrder(
        order_id=ORD,
        idempotency_key="SYN-KEY-000000000001",
        patient=PATIENT,
        tenant_id=TENANT,
        test_codes=("GLU", "HBA1C"),
        priority=Priority.URGENT,
        status=LabOrderStatus.PLACED,
        created_at=MOMENT,
    )


def cancelled_order() -> LabOrder:
    """Build a cancelled order so cancellation extras are exercised."""
    return LabOrder(
        order_id=ORD,
        idempotency_key="SYN-KEY-000000000001",
        patient=PATIENT,
        tenant_id=TENANT,
        test_codes=("GLU",),
        priority=Priority.STAT,
        status=LabOrderStatus.CANCELLED,
        created_at=MOMENT,
        cancelled_at="2026-01-02T00:00:00+00:00",
        cancellation_reason="synthetic cancellation",
    )


def specimen() -> Specimen:
    """Build a frozen synthetic specimen."""
    return Specimen(
        specimen_id=SPC,
        barcode="SYN-BAR-000000000001",
        order_id=ORD,
        tenant_id=TENANT,
        patient=PATIENT,
        status=SpecimenStatus.RECEIVED,
        registered_at=MOMENT,
    )


def rejected_specimen() -> Specimen:
    """Build a rejected specimen so rejection extras are exercised."""
    return Specimen(
        specimen_id=SPC,
        barcode="SYN-BAR-000000000001",
        order_id=ORD,
        tenant_id=TENANT,
        patient=PATIENT,
        status=SpecimenStatus.REJECTED,
        registered_at=MOMENT,
        rejection_reason="synthetic rejection",
    )


def result() -> LabResult:
    """Build a frozen synthetic corrected result with an amendment."""
    amendment = ResultAmendment(
        amendment_id="SYN-AMD-000000000001",
        result_id=RES,
        tenant_id=TENANT,
        previous_value=90.0,
        new_value=92.0,
        reason="synthetic correction",
        actor_id=PRC,
        occurred_at=MOMENT,
        version=2,
    )
    return LabResult(
        result_id=RES,
        idempotency_key="SYN-KEY-000000000002",
        order_id=ORD,
        specimen_id=SPC,
        patient=PATIENT,
        tenant_id=TENANT,
        test_code="GLU",
        value=92.0,
        unit="mg/dL",
        reference_low=70.0,
        reference_high=99.0,
        critical_flag=False,
        recorded_at=MOMENT,
        version=2,
        amendments=(amendment,),
    )


CASES: tuple[tuple[str, Callable[[], object], str], ...] = (
    ("Practitioner", practitioner, PRC),
    ("Organization", organization, ORG),
    ("Location", facility, FAC),
    ("Encounter", encounter, ENC),
    ("Condition", diagnosis, DIA),
    ("Observation", observation, OBS),
    ("ServiceRequest", order, ORD),
    ("Specimen", specimen, SPC),
    ("DiagnosticReport", result, RES),
)


def _collect_references(value: object) -> list[str]:
    """Recursively collect every FHIR Reference.reference string."""
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "reference" and isinstance(item, str):
                found.append(item)
            else:
                found.extend(_collect_references(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_collect_references(item))
    return found


@pytest.mark.parametrize(("resource_type", "builder", "entity_id"), CASES)
def test_entity_fhir_entity_round_trip_is_field_equal(
    resource_type: str, builder: Callable[[], object], entity_id: str
) -> None:
    """Every supported frozen entity survives a real FHIR round-trip unchanged."""
    entity = builder()
    resource = ADAPTER.serialize(entity)
    restored = ADAPTER.deserialize(resource)
    assert resource["resourceType"] == resource_type
    assert resource["id"] == entity_id
    assert type(restored) is type(entity)
    assert restored == entity


@pytest.mark.parametrize(("resource_type", "builder", "entity_id"), CASES)
def test_serialized_resource_has_fhir_shape(
    resource_type: str, builder: Callable[[], object], entity_id: str
) -> None:
    """Each output has resourceType, id, a versioned synthetic profile and an id."""
    resource = ADAPTER.serialize(builder())
    assert resource["resourceType"] in SUPPORTED_FHIR_RESOURCE_TYPES
    assert resource["id"] == entity_id
    meta = resource["meta"]
    assert isinstance(meta, dict)
    assert meta["profile"] == [profile_for(resource_type)]
    assert str(meta["profile"][0]).startswith(PROFILE_BASE)
    assert isinstance(meta["versionId"], str) and str(meta["versionId"]).isdigit()
    identifiers = resource["identifier"]
    assert isinstance(identifiers, list)
    first = identifiers[0]
    assert isinstance(first, dict)
    assert first["system"] == IDENTIFIER_SYSTEM
    assert first["value"] == entity_id


@pytest.mark.parametrize(("resource_type", "builder", "entity_id"), CASES)
def test_resources_are_json_serialisable_and_use_only_synthetic_references(
    resource_type: str, builder: Callable[[], object], entity_id: str
) -> None:
    """No output contains a non-JSON value or a non-synthetic reference."""
    resource = ADAPTER.serialize(builder())
    encoded = json.dumps(resource, ensure_ascii=False)
    assert resource_type in encoded
    for reference in _collect_references(resource):
        target_type, identifier = reference.split("/", 1)
        assert target_type in REFERENCE_TARGET_PREFIXES
        assert identifier.startswith(REFERENCE_TARGET_PREFIXES[target_type])


@pytest.mark.parametrize(
    "builder",
    (cancelled_order, rejected_specimen),
)
def test_optional_synthetic_extensions_round_trip(builder: Callable[[], object]) -> None:
    """Cancellation and rejection details are preserved, not dropped."""
    entity = builder()
    assert ADAPTER.deserialize(ADAPTER.serialize(entity)) == entity


def test_supported_and_unsupported_resource_sets_are_explicit_and_disjoint() -> None:
    """The allow-list and documented deny-list are enumerated in code."""
    assert len(SUPPORTED_FHIR_RESOURCE_TYPES) == 9
    assert len(set(SUPPORTED_FHIR_RESOURCE_TYPES)) == 9
    assert not set(SUPPORTED_FHIR_RESOURCE_TYPES) & set(UNSUPPORTED_FHIR_RESOURCE_TYPES)
    for rejected in ("Patient", "MedicationRequest", "Bundle", "Claim"):
        assert rejected in UNSUPPORTED_FHIR_RESOURCE_TYPES
        assert rejected not in SUPPORTED_FHIR_RESOURCE_TYPES


def test_unsupported_entities_and_resources_are_rejected_not_coerced() -> None:
    """Neither direction silently converts an unlisted type."""
    with pytest.raises(UnsupportedFhirResourceError):
        ADAPTER.serialize(PATIENT)
    with pytest.raises(UnsupportedFhirResourceError):
        ADAPTER.deserialize({"resourceType": "MedicationRequest", "id": "SYN-MED-000001"})


def test_real_service_emitted_entities_round_trip(
    synthetic_registry: SyntheticPatientRegistry,
    synthetic_tenant: str,
    synthetic_patient: PatientRef,
) -> None:
    """Entities created by the real clinical/lab services fit the adapter."""
    context = ClinicalContext(identity=synthetic_registry)
    key = lambda name: new_synthetic_id(name)  # noqa: E731
    prc = context.practitioners.register(
        tenant_id=synthetic_tenant,
        idempotency_key=key("PRC"),
        role="physician",
        qualification="synthetic qualification",
    )
    org = context.organizations.register_organization(
        tenant_id=synthetic_tenant,
        idempotency_key=key("ORG"),
        label="Synthetic Org",
    )
    fac = context.organizations.register_facility(
        tenant_id=synthetic_tenant,
        idempotency_key=key("FAC"),
        organization_id=org.organization_id,
        label="Synthetic Facility",
        facility_type="clinic",
    )
    enc = context.encounters.create(
        tenant_id=synthetic_tenant,
        idempotency_key=key("ENC"),
        patient_ref=synthetic_patient.ref,
        practitioner_id=prc.practitioner_id,
        facility_id=fac.facility_id,
        reason="synthetic review",
    )
    dia = context.diagnoses.record(
        tenant_id=synthetic_tenant,
        idempotency_key=key("DIA"),
        patient_ref=synthetic_patient.ref,
        encounter_id=enc.encounter_id,
        code="J18.9",
        description="Synthetic finding",
        severity="low",
    )
    obs = context.observations.record(
        tenant_id=synthetic_tenant,
        idempotency_key=key("OBS"),
        patient_ref=synthetic_patient.ref,
        encounter_id=enc.encounter_id,
        code="8867-4",
        display="Heart rate",
        value=70.0,
        unit="bpm",
        recorded_at=datetime.now(UTC),
    )
    lab = LabWorkflowService(identity=synthetic_registry)
    lab_order = lab.place_order(
        tenant_id=synthetic_tenant,
        patient_ref=synthetic_patient.ref,
        test_codes=("GLU",),
        idempotency_key=key("ORD"),
        actor_id=prc.practitioner_id,
    )
    lab_specimen = lab.register_specimen(
        tenant_id=synthetic_tenant,
        order_id=lab_order.order_id,
        barcode=key("BAR"),
        actor_id=prc.practitioner_id,
    )
    emitted = (prc, org, fac, enc, dia, obs, lab_order, lab_specimen)
    for entity in emitted:
        resource: Any = ADAPTER.serialize(entity)
        assert ADAPTER.deserialize(resource) == entity
