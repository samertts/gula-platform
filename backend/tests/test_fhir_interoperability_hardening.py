"""Integration coverage for the FHIR interoperability hardening wave."""
from __future__ import annotations

import json
from datetime import datetime
from types import SimpleNamespace

from app._compat import UTC
from app.fhir.terminology import observation_code
from app.models.audit_log import AuditLog
from app.routes.ehr_fhir import _clinical_note_to_composition
from app.services.audit_service import log_action
from tests.conftest import auth_headers


def _headers(lab, user):
    return auth_headers(user.id, lab.id)


def test_metadata_is_discoverable_as_fhir_json(client, db, make_lab, make_lab_user):
    lab = make_lab()
    user = make_lab_user(lab_id=lab.id)

    response = client.get("/fhir/metadata", headers=_headers(lab, user))

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/fhir+json")
    capability = response.json()
    assert capability["resourceType"] == "CapabilityStatement"
    types = {resource["type"] for resource in capability["rest"][0]["resource"]}
    assert "Provenance" in types
    assert any(operation["name"] == "everything" for operation in capability["rest"][0]["operation"])


def test_fhir_validation_errors_use_operation_outcome(client, db, make_lab, make_lab_user):
    lab = make_lab()
    user = make_lab_user(lab_id=lab.id)

    response = client.get("/fhir/Observation/not-an-integer", headers=_headers(lab, user))

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/fhir+json")
    assert response.json()["resourceType"] == "OperationOutcome"
    assert response.json()["issue"][0]["code"] == "invalid"


def test_loinc_enrichment_and_local_fallback_are_explicit():
    glucose = observation_code("Glucose")
    local = observation_code("Locally configured assay")

    assert glucose["coding"][0]["system"] == "http://loinc.org"
    assert glucose["coding"][0]["code"] == "2345-7"
    assert local["coding"][0]["system"] == "urn:gula:lab-test-name"


def test_composition_narrative_escapes_untrusted_markup():
    now = datetime.now(UTC)
    record = SimpleNamespace(
        id="note-1",
        content="<script>alert('unsafe')</script>",
        is_final=True,
        note_type="progress",
        title="Progress note",
        title_ar=None,
        patient_id="patient-1",
        encounter_id=None,
        authored_at=now,
        signed_at=None,
        author_id=None,
        signed_by=None,
        is_signed=False,
        version=1,
        updated_at=now,
    )

    composition = _clinical_note_to_composition(record)

    narrative = composition["section"][0]["text"]["div"]
    assert "<script>" not in narrative
    assert "&lt;script&gt;" in narrative


def test_provenance_is_tenant_scoped_and_hash_exposed(client, db, make_lab, make_lab_user):
    lab = make_lab()
    other_lab = make_lab(name="Other provenance lab")
    user = make_lab_user(lab_id=lab.id)
    target = "Condition/clinical-id"
    scoped = AuditLog(
        user_id=user.id,
        lab_id=lab.id,
        action="fhir.update",
        resource_type="FHIR",
        details=json.dumps({"fhir_resource_type": "Condition", "fhir_resource_id": "clinical-id"}),
        chain_hash="a" * 64,
    )
    other = AuditLog(
        user_id=user.id,
        lab_id=other_lab.id,
        action="fhir.update",
        resource_type="FHIR",
        details=json.dumps({"fhir_resource_type": "Condition", "fhir_resource_id": "clinical-id"}),
        chain_hash="b" * 64,
    )
    db.add_all([scoped, other])
    db.commit()

    response = client.get(f"/fhir/Provenance?target={target}", headers=_headers(lab, user))

    assert response.status_code == 200
    bundle = response.json()
    assert bundle["resourceType"] == "Bundle"
    assert bundle["total"] == 1
    provenance = bundle["entry"][0]["resource"]
    assert provenance["target"] == [{"reference": target}]
    assert provenance["extension"][0]["valueString"] == "a" * 64


def test_population_summary_is_aggregate_and_has_no_patient_data(client, db, make_lab, make_lab_user):
    lab = make_lab()
    user = make_lab_user(lab_id=lab.id)

    response = client.get("/fhir/analytics/population-summary", headers=_headers(lab, user))

    assert response.status_code == 200
    payload = response.json()
    assert payload["resourceType"] == "Parameters"
    assert {parameter["name"] for parameter in payload["parameter"]} >= {
        "testVolume", "criticalValueCount", "criticalValueRate",
    }
    assert "patient" not in json.dumps(payload).casefold()


def test_cds_hook_is_advisory_and_only_returns_source_marked_critical_values(
    client, db, make_lab, make_lab_user,
):
    lab = make_lab()
    user = make_lab_user(lab_id=lab.id)
    headers = _headers(lab, user)

    discovery = client.get("/cds-services", headers=headers)
    critical = client.post(
        "/cds-services/critical-value-alert",
        headers=headers,
        json={"context": {"observation": {"flag": "critical", "code": {"text": "Potassium"}}}},
    )
    normal = client.post(
        "/cds-services/critical-value-alert",
        headers=headers,
        json={"context": {"observation": {"flag": "normal", "code": {"text": "Potassium"}}}},
    )

    assert discovery.status_code == 200
    assert discovery.json()["services"][0]["id"] == "critical-value-alert"
    assert critical.json()["cards"][0]["indicator"] == "critical"
    assert "clinical review" in critical.json()["cards"][0]["detail"].casefold()
    assert normal.json() == {"cards": []}


def test_audit_log_persists_tenant_context_and_structured_details(db, make_lab, make_lab_user):
    lab = make_lab()
    user = make_lab_user(lab_id=lab.id)

    log_action(
        db,
        action="fhir.create",
        resource_type="FHIR",
        user_id=user.id,
        lab_id=lab.id,
        details={"fhir_resource_type": "Condition", "fhir_resource_id": "condition-1"},
    )
    db.commit()

    entry = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    assert entry.lab_id == lab.id
    assert json.loads(entry.details)["fhir_resource_id"] == "condition-1"
