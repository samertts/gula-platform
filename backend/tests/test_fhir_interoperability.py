from __future__ import annotations

from app.models.user import User
from app.security.auth import hash_password
from tests.conftest import auth_headers


def _patient_payload(resource_id: str = "patient-001") -> dict:
    return {
        "resourceType": "Patient",
        "id": resource_id,
        "identifier": [{"system": "https://gula.example/patient", "value": resource_id}],
        "name": [{"family": "Synthetic", "given": ["Citizen"]}],
        "active": True,
    }


def test_fhir_resource_registry_is_tenant_scoped(client, make_lab, make_lab_user):
    lab_a = make_lab("FHIR Institution A")
    lab_b = make_lab("FHIR Institution B")
    user_a = make_lab_user(lab_a.id, role="admin")
    user_b = make_lab_user(lab_b.id, role="admin")
    headers_a = auth_headers(user_a.id, lab_a.id, "admin")
    headers_b = auth_headers(user_b.id, lab_b.id, "admin")

    created = client.post(
        "/fhir-interoperability/resources",
        json=_patient_payload(),
        headers=headers_a,
    )
    assert created.status_code == 201
    assert created.json()["resourceType"] == "Patient"
    assert created.json()["id"] == "patient-001"
    assert created.json()["resource"]["name"][0]["family"] == "Synthetic"

    own = client.get(
        "/fhir-interoperability/resources/Patient/patient-001",
        headers=headers_a,
    )
    assert own.status_code == 200

    hidden = client.get(
        "/fhir-interoperability/resources/Patient/patient-001",
        headers=headers_b,
    )
    assert hidden.status_code == 404

    own_search = client.get("/fhir-interoperability/resources/Patient", headers=headers_a)
    assert own_search.status_code == 200
    assert own_search.json()["total"] == 1
    other_search = client.get("/fhir-interoperability/resources/Patient", headers=headers_b)
    assert other_search.status_code == 200
    assert other_search.json()["total"] == 0

    same_id_in_other_lab = client.post(
        "/fhir-interoperability/resources",
        json=_patient_payload(),
        headers=headers_b,
    )
    assert same_id_in_other_lab.status_code == 201

    duplicate = client.post(
        "/fhir-interoperability/resources",
        json=_patient_payload(),
        headers=headers_a,
    )
    assert duplicate.status_code == 409


def test_fhir_registry_rejects_citizen_accounts(client, db):
    citizen = User(
        email="citizen-fhir@test.com",
        password_hash=hash_password("Testpass1"),
        full_name="Synthetic Citizen",
        role="citizen",
        lab_id=None,
        is_active=True,
        is_verified=True,
    )
    db.add(citizen)
    db.flush()
    headers = auth_headers(citizen.id, None, "citizen")

    read = client.get("/fhir-interoperability/resources/Patient", headers=headers)
    assert read.status_code == 403
    write = client.post(
        "/fhir-interoperability/resources",
        json=_patient_payload("citizen-denied"),
        headers=headers,
    )
    assert write.status_code == 403


def test_fhir_metadata_is_public_and_typed(client):
    response = client.get("/fhir-interoperability/metadata")
    assert response.status_code == 200
    body = response.json()
    assert body["resourceType"] == "CapabilityStatement"
    assert body["fhirVersion"] == "4.0.1"
    assert "Observation" in body["supportedResourceTypes"]
    assert body["simulationOnly"] is True


def test_synthetic_hl7_oru_is_converted_to_fhir_bundle(client, make_lab, make_lab_user):
    lab = make_lab("HL7 Synthetic Lab")
    user = make_lab_user(lab.id, role="admin")
    headers = auth_headers(user.id, lab.id, "admin")
    message = (
        "MSH|^~\\&|GULA-SIM|LAB-A|GULA|GULA|202608150900||ORU^R01|MSG-001|P|2.5\r"
        "PID|1||PAT-001||Synthetic^Patient\r"
        "OBR|1||ORD-001|CBC^Complete Blood Count|||202608150859\r"
        "OBX|1|NM|HB^Hemoglobin||13.2|g/dL|12-16|N|||F\r"
    )
    response = client.post(
        "/fhir-interoperability/hl7/convert",
        json={"message": message},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["messageType"] == "ORU^R01"
    assert body["simulationOnly"] is True
    assert body["bundle"]["resourceType"] == "Bundle"
    assert any(entry["resource"]["resourceType"] == "Observation" for entry in body["bundle"]["entry"])
    assert "raw_message" not in body

    invalid = client.post(
        "/fhir-interoperability/hl7/convert",
        json={"message": "MSH|^~\\&|GULA-SIM|LAB-A|GULA|GULA|202608150900||ADT^A01|MSG-002|P|2.5"},
        headers=headers,
    )
    assert invalid.status_code == 422
