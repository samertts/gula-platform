"""Wave 03 — synthetic patient journey over the shared integration contracts.

This file is test-only evidence. It connects the existing registration,
encounter and referral workflow engines with the canonical event envelope,
event registry, FHIR R4 profiles and the read-only synthetic FHIR exchange.
No production service, external gateway, national identity authority,
public-health policy or clinical AI behavior is activated.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from app._compat import UTC
from app.contracts.events import EVENT_REGISTRY, get_asyncapi_spec, get_event_catalog
from app.contracts.fhir import get_capability_statement, get_fhir_profiles
from app.contracts.integration import (
    CORRELATION_ID_HEADER,
    REQUEST_ID_HEADER,
    TRACEPARENT_HEADER,
    IntegrationEventEnvelope,
    correlation_id_from_headers,
    normalize_correlation_id,
)
from app.identity.services.consent_service_v2 import NiamConsentService
from app.integration.fhir_r4_exchange import (
    FHIRExchangeBlocked,
    InMemoryAuditRecorder,
    SyntheticFHIRReadOnlyExchange,
    synthetic_bundle,
    validate_synthetic_bundle,
)
from app.national.domain.citizen import Citizen
from app.national.domain.patient import Patient
from app.national.enums import Gender
from app.national.fhir.patient import FHIRPatientMapper
from app.national.workflows import (
    EncounterWorkflow,
    PatientRegistrationWorkflow,
    ReferralWorkflow,
    WorkflowContext,
    WorkflowState,
    WorkflowStepStatus,
)

_CORRELATION = "WAVE03-JOURNEY-0001"
_ORG = "ORG-SYNTHETIC"
_TENANT = "TENANT-SYNTHETIC"
_T0 = datetime(2026, 11, 24, 8, 0, tzinfo=UTC)


def _envelope(
    *,
    event_type: str,
    entity_id: str,
    source_service: str,
    sequence: int,
    payload: dict,
) -> IntegrationEventEnvelope:
    return IntegrationEventEnvelope(
        event_id=f"wave03-event-{sequence:03d}",
        event_type=event_type,
        schema_version=1,
        source_service=source_service,
        tenant_id=_TENANT,
        occurred_at=_T0 + timedelta(minutes=sequence),
        actor_id="ACCOUNT-SYNTHETIC",
        entity_id=entity_id,
        correlation_id=_CORRELATION,
        idempotency_key=f"wave03-journey-step-{sequence:03d}",
        payload=payload,
    )


def _registry_payload(event_name: str, **values) -> dict:
    """Build a minimal payload that satisfies the registered schema."""
    definition = EVENT_REGISTRY[event_name]
    payload = {field: values[field] for field in definition["payload"]["required"]}
    payload.update(values)
    correlation_field = definition["correlation_id"]
    assert correlation_field in payload
    return payload


@pytest.mark.asyncio
async def test_synthetic_patient_journey_uses_one_correlation_contract() -> None:
    registration = PatientRegistrationWorkflow()
    encounter = EncounterWorkflow()
    referral = ReferralWorkflow()

    registration_context = await registration.execute(
        WorkflowContext(workflow_id="W3-REG-1", workflow_type="patient_registration"),
        {"identity_type": "standard", "organization_id": _ORG},
    )
    encounter_context = await encounter.execute(
        WorkflowContext(workflow_id="W3-ENC-1", workflow_type="encounter"),
        {"encounter_type": "outpatient", "organization_id": _ORG},
    )
    referral_context = await referral.execute(
        WorkflowContext(workflow_id="W3-REF-1", workflow_type="referral"),
        {"destination_facility_id": "FACILITY-SYNTHETIC-B", "organization_id": _ORG},
    )

    for context, engine in (
        (registration_context, registration),
        (encounter_context, encounter),
        (referral_context, referral),
    ):
        assert context.state is WorkflowState.COMPLETED
        assert context.errors == []
        assert [step.status for step in engine._steps] == [WorkflowStepStatus.SUCCEEDED] * len(engine._steps)
        assert [step.name for step in engine._steps]

    # Registration → identity verification → encounter → assessment/orders →
    # diagnostics → results → treatment → prescription → follow-up. Envelopes
    # carry a single correlation ID while source services identify the program.
    journey_events = [
        _envelope(
            event_type="patient.created",
            entity_id="PATIENT-SYN-0001",
            source_service="prg-01-identity",
            sequence=1,
            payload=_registry_payload(
                "PatientCreated",
                patient_id=1,
                lab_id=1,
                full_name="Synthetic Patient",
                phone="0000000000",
                health_id="SYN-HEALTH-0001",
                created_at=_T0.isoformat(),
            ),
        ),
        _envelope(
            event_type="patient.identity-verified",
            entity_id="PATIENT-SYN-0001",
            source_service="prg-01-identity",
            sequence=2,
            payload={"identity_status": "verified", "verification_mode": "synthetic"},
        ),
        _envelope(
            event_type="encounter.recorded",
            entity_id="ENCOUNTER-SYN-0001",
            source_service="prg-02-encounter",
            sequence=3,
            payload={"encounter_type": "outpatient", "patient_id": 1, "facility_id": "FACILITY-SYN-0001"},
        ),
        _envelope(
            event_type="order.created",
            entity_id="ORDER-SYN-0001",
            source_service="prg-03-orders",
            sequence=4,
            payload=_registry_payload(
                "OrderCreated",
                order_id=1,
                patient_id=1,
                lab_id=1,
                status="pending",
                test_types=["synthetic-panel"],
            ),
        ),
        _envelope(
            event_type="sample.collected",
            entity_id="SAMPLE-SYN-0001",
            source_service="prg-03-orders",
            sequence=5,
            payload=_registry_payload(
                "SampleCollected", sample_id=1, order_id=1, barcode="SYN-BARCODE-1",
                sample_type="synthetic", collection_time=_T0.isoformat(),
            ),
        ),
        _envelope(
            event_type="result.published",
            entity_id="RESULT-SYN-0001",
            source_service="prg-04-results",
            sequence=6,
            payload=_registry_payload(
                "ResultPublished",
                result_id=1,
                order_id=1,
                test_name="synthetic-panel",
                lab_id=1,
                patient_id=1,
                flag="normal",
                published_at=_T0.isoformat(),
            ),
        ),
        _envelope(
            event_type="treatment.recorded",
            entity_id="TREATMENT-SYN-0001",
            source_service="prg-02-encounter",
            sequence=7,
            payload={"patient_id": 1, "encounter_id": 1, "plan": "synthetic"},
        ),
        _envelope(
            event_type="prescription.recorded",
            entity_id="PRESCRIPTION-SYN-0001",
            source_service="prg-02-encounter",
            sequence=8,
            payload={"patient_id": 1, "encounter_id": 1, "issuer_role": "synthetic_physician"},
        ),
        _envelope(
            event_type="followup.scheduled",
            entity_id="FOLLOWUP-SYN-0001",
            source_service="prg-02-encounter",
            sequence=9,
            payload={"patient_id": 1, "encounter_id": 1, "channel": "synthetic"},
        ),
    ]

    assert len(journey_events) == 9
    assert {event.correlation_id for event in journey_events} == {_CORRELATION}
    assert len({event.idempotency_key for event in journey_events}) == 9
    assert [event.occurred_at for event in journey_events] == sorted(event.occurred_at for event in journey_events)
    assert {event.source_service for event in journey_events} == {
        "prg-01-identity", "prg-02-encounter", "prg-03-orders", "prg-04-results"
    }
    assert CORRELATION_ID_HEADER == "X-Correlation-ID"
    assert correlation_id_from_headers(
        {CORRELATION_ID_HEADER: _CORRELATION, TRACEPARENT_HEADER: "ignored"},
        fallback=REQUEST_ID_HEADER,
    ) == _CORRELATION
    assert normalize_correlation_id(None, fallback="bad id") != "bad id"


def test_synthetic_fhir_patient_mapper_never_emits_raw_national_identifier() -> None:
    citizen = Citizen(
        id="CITIZEN-SYN-0001",
        health_number="SYN-HEALTH-0001",
        first_name="Synthetic",
        last_name="Patient",
        date_of_birth=date(2015, 5, 20),
        gender=Gender.FEMALE,
        national_id_hash="synthetic-hash-value",
        national_id_verified=True,
        governorate="SYNTHETIC",
    )
    patient = Patient(
        id="PATIENT-SYN-0001",
        health_number="SYN-HEALTH-0001",
        first_name="Synthetic",
        last_name="Patient",
        date_of_birth=date(2015, 5, 20),
        gender=Gender.FEMALE,
        lab_id=1,
        citizen_id=citizen.id,
    )

    resource = FHIRPatientMapper.from_patient(patient, citizen)

    assert resource["resourceType"] == "Patient"
    assert resource["id"] == patient.id
    assert resource["birthDate"] == "2015-05-20"
    assert resource["gender"] == "female"
    assert resource["managingOrganization"] == [{"reference": "Organization/1"}]
    assert resource["identifier"][0]["value"] == "SYN-HEALTH-0001"
    assert resource["identifier"][1]["value"].startswith("hash:")
    assert "synthetic-hash-value" not in str(resource)
    assert "123456789012" not in str(resource)


def test_fhir_r4_contracts_are_profile_backed_and_read_only() -> None:
    profile_types = {profile["type"] for profile in get_fhir_profiles()}
    assert {"Patient", "Observation", "DiagnosticReport", "ServiceRequest", "Encounter"} <= profile_types
    capability = get_capability_statement()
    assert capability["fhirVersion"] == "4.0.1"
    resources = capability["rest"][0]["resource"]
    assert all(
        {"read", "search-type"} <= {item["code"] for item in resource["interaction"]}
        for resource in resources
    )
    assert all(
        not ({"delete", "patch", "vread", "history-instance"} & {item["code"] for item in resource["interaction"]})
        for resource in resources
    )

    audit = InMemoryAuditRecorder()
    blocked_exchange = SyntheticFHIRReadOnlyExchange(audit=audit)
    with pytest.raises(FHIRExchangeBlocked):
        blocked_exchange.read_bundle()
    assert audit.decisions[-1].outcome == "denied"

    enabled_exchange = SyntheticFHIRReadOnlyExchange(enabled=True, audit=audit)
    assert validate_synthetic_bundle(synthetic_bundle()) == []
    assert enabled_exchange.read_bundle()["resourceType"] == "Bundle"
    assert audit.decisions[-1].outcome == "allowed"
    with pytest.raises(FHIRExchangeBlocked):
        enabled_exchange.write({"resourceType": "Observation"})


def test_prg05_dependencies_are_prepared_without_policy_activation() -> None:
    # The deps needed by a future, separately authorized public-health program
    # are present as contracts only; no policy event or recipient is activated.
    required_events = {"PatientCreated", "ResultPublished", "ConsentChanged", "AuditLogWritten"}
    assert required_events <= set(EVENT_REGISTRY)
    catalog = get_event_catalog()
    assert len(catalog) == len(EVENT_REGISTRY)
    assert all(entry["correlation_id"] for entry in catalog)
    assert len(get_asyncapi_spec()["channels"]) == len(EVENT_REGISTRY)
    assert not [name for name in EVENT_REGISTRY if any(
        token in name.lower() for token in ("surveillance", "publichealth", "dhis2", "mandatoryreport")
    )]

    assert NiamConsentService._validate_scope({"purpose": "TREATMENT"}) == {"purpose": "TREATMENT"}
    assert set(EVENT_REGISTRY["ConsentChanged"]["payload"]["required"])


def test_envelope_is_fail_closed_for_malformed_cross_program_events() -> None:
    def envelope(**overrides):
        values = dict(
            event_id="wave03-event-invalid",
            event_type="patient.created",
            schema_version=1,
            source_service="prg-01-identity",
            tenant_id=_TENANT,
            occurred_at=_T0,
            actor_id="ACCOUNT-SYNTHETIC",
            entity_id="PATIENT-SYN-0001",
            correlation_id=_CORRELATION,
            idempotency_key="wave03-invalid-event",
            payload={"patient_id": 1},
        )
        values.update(overrides)
        return IntegrationEventEnvelope(**values)

    with pytest.raises(ValueError):
        envelope(tenant_id="")
    with pytest.raises(ValueError):
        envelope(occurred_at=datetime(2026, 11, 24, 8, 0))
    with pytest.raises(ValueError):
        envelope(unexpected_field="forbidden")
    with pytest.raises(ValueError):
        envelope(event_type="not a valid event type")
    with pytest.raises(ValueError):
        envelope(schema_version=0)
