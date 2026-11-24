"""Contract tests for the framework-agnostic synthetic API client fake."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from app.health_core.common import (
    DomainEvent,
    InvalidSyntheticReferenceError,
    TenantMismatchError,
    UnknownPatientError,
)
from app.health_core.identity import PatientRef
from app.health_core.integration import (
    ELIGIBLE_DOMAINS,
    DomainCode,
    InMemorySyntheticApiClient,
    SyntheticApiClient,
)

if TYPE_CHECKING:
    from app.health_core.identity import SyntheticPatientRegistry

DOMAIN_METHODS: dict[DomainCode, tuple[str, str]] = {
    DomainCode.PRACTITIONER: ("create_practitioner", "list_practitioners"),
    DomainCode.FACILITY: ("create_facility", "list_facilities"),
    DomainCode.MEDICAL_RECORD: ("create_medical_record", "list_medical_records"),
    DomainCode.ENCOUNTER: ("create_encounter", "list_encounters"),
    DomainCode.DIAGNOSIS: ("create_diagnosis", "list_diagnoses"),
    DomainCode.OBSERVATION: ("create_observation", "list_observations"),
    DomainCode.LAB_ORDER: ("create_lab_order", "list_lab_orders"),
    DomainCode.SPECIMEN: ("create_specimen", "list_specimens"),
    DomainCode.LAB_RESULT: ("create_lab_result", "list_lab_results"),
    DomainCode.RESULT_VERIFICATION: ("create_verification", "list_verifications"),
}


def test_fake_conforms_to_abstract_client(
    synthetic_registry: SyntheticPatientRegistry,
) -> None:
    client = InMemorySyntheticApiClient(synthetic_registry)
    assert isinstance(client, SyntheticApiClient)
    assert not getattr(client, "__abstractmethods__", set())


def test_abstract_client_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        SyntheticApiClient()  # type: ignore[abstract]


def test_all_ten_eligible_domains_have_create_and_list_methods(
    synthetic_registry: SyntheticPatientRegistry,
) -> None:
    assert len(ELIGIBLE_DOMAINS) == 10
    assert set(DOMAIN_METHODS) == set(ELIGIBLE_DOMAINS)
    client = InMemorySyntheticApiClient(synthetic_registry)
    for create_name, list_name in DOMAIN_METHODS.values():
        assert callable(getattr(client, create_name))
        assert callable(getattr(client, list_name))


def test_create_and_list_every_domain(
    synthetic_registry: SyntheticPatientRegistry,
    synthetic_tenant: str,
    synthetic_patient: PatientRef,
) -> None:
    client = InMemorySyntheticApiClient(synthetic_registry)
    for domain, (create_name, list_name) in DOMAIN_METHODS.items():
        create = getattr(client, create_name)
        list_records = getattr(client, list_name)
        record = create(
            tenant_id=synthetic_tenant,
            patient_ref=synthetic_patient,
            data={"fixture": domain.value},
        )
        assert record.domain is domain
        assert record.tenant_id == synthetic_tenant
        assert record.patient_ref == synthetic_patient.ref
        assert record.version == 1
        assert record.entity_id.startswith("SYN-")
        assert list_records(
            tenant_id=synthetic_tenant, patient_ref=synthetic_patient
        ) == (record,)


def test_every_create_emits_one_shared_domain_event(
    synthetic_registry: SyntheticPatientRegistry,
    synthetic_tenant: str,
    synthetic_patient: PatientRef,
) -> None:
    client = InMemorySyntheticApiClient(synthetic_registry)
    for create_name in (pair[0] for pair in DOMAIN_METHODS.values()):
        getattr(client, create_name)(
            tenant_id=synthetic_tenant, patient_ref=synthetic_patient, data={}
        )
    events = client.events
    assert len(events) == 10
    assert all(isinstance(event, DomainEvent) for event in events)
    assert len({event.event_id for event in events}) == 10
    assert all(event.tenant_id == synthetic_tenant for event in events)
    assert all(event.payload["patient_ref"] == synthetic_patient.ref for event in events)


def test_cross_tenant_access_is_refused(
    synthetic_registry: SyntheticPatientRegistry,
    synthetic_tenant: str,
    synthetic_patient: PatientRef,
) -> None:
    other_tenant = "SYN-LAB-9999"
    synthetic_registry.register_patient(tenant_id=other_tenant, label="other-tenant")
    client = InMemorySyntheticApiClient(synthetic_registry)
    client.create_practitioner(
        tenant_id=synthetic_tenant, patient_ref=synthetic_patient, data={"fixture": "a"}
    )
    with pytest.raises(TenantMismatchError) as exc:
        client.list_practitioners(tenant_id=other_tenant, patient_ref=synthetic_patient)
    assert exc.value.code == "TENANT_MISMATCH"


def test_unknown_synthetic_patient_fails_closed(
    synthetic_registry: SyntheticPatientRegistry, synthetic_tenant: str
) -> None:
    unknown = PatientRef(ref="SYN-PAT-ABSENT", tenant_id=synthetic_tenant)
    client = InMemorySyntheticApiClient(synthetic_registry)
    with pytest.raises(UnknownPatientError) as exc:
        client.create_lab_result(
            tenant_id=synthetic_tenant, patient_ref=unknown, data={"fixture": "x"}
        )
    assert exc.value.code == "UNKNOWN_PATIENT"


def test_non_synthetic_tenant_is_rejected(
    synthetic_registry: SyntheticPatientRegistry, synthetic_patient: PatientRef
) -> None:
    client = InMemorySyntheticApiClient(synthetic_registry)
    with pytest.raises(InvalidSyntheticReferenceError):
        client.create_encounter(
            tenant_id="LAB-0001", patient_ref=synthetic_patient, data={}
        )


def test_lists_are_scoped_to_one_synthetic_patient(
    synthetic_registry: SyntheticPatientRegistry,
    synthetic_tenant: str,
    synthetic_patient: PatientRef,
) -> None:
    second = synthetic_registry.register_patient(
        tenant_id=synthetic_tenant, label="fixture-bravo"
    )
    client = InMemorySyntheticApiClient(synthetic_registry)
    client.create_specimen(
        tenant_id=synthetic_tenant, patient_ref=synthetic_patient, data={"id": "a"}
    )
    client.create_specimen(
        tenant_id=synthetic_tenant, patient_ref=second, data={"id": "b"}
    )
    assert [
        record.data["id"]
        for record in client.list_specimens(
            tenant_id=synthetic_tenant, patient_ref=synthetic_patient
        )
    ] == ["a"]
    assert len(client.events) == 2


def test_result_data_is_immutable(
    synthetic_registry: SyntheticPatientRegistry,
    synthetic_tenant: str,
    synthetic_patient: PatientRef,
) -> None:
    client = InMemorySyntheticApiClient(synthetic_registry)
    record = client.create_diagnosis(
        tenant_id=synthetic_tenant, patient_ref=synthetic_patient, data={"code": "SYN-CODE"}
    )
    with pytest.raises(TypeError):
        record.data["code"] = "changed"  # type: ignore[index]
    assert record.to_dict()["data"] == {"code": "SYN-CODE"}
