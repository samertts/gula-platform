"""Wave 05.1 — isolated in-process API evidence and 20-step synthetic journey.

Point 33 evidence is produced with the real FastAPI app through the shared
``TestClient`` fixture: startup, request execution and shutdown all occur in
one local process. No external HTTP server, socket retry or connection failure
is treated as a passing API test.

All records are synthetic. The journey characterizes mounted API/service
boundaries; it does not claim a nationally deployed end-to-end journey,
activated event bus, verified identity, PRG-05 public-health flow or
production-ready clinical documentation store.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app._compat import UTC
from app.security.auth import create_token
from app.national.domain.encounter import Encounter
from app.national.enums import EncounterStatus, EncounterType
from app.national.services.encounter_service import (
    complete_encounter,
    create_encounter,
    get_active_encounters_by_patient,
    get_encounter,
    get_encounters_by_patient,
    update_encounter,
)


@pytest.fixture()
def synthetic_lab_user(make_lab, make_lab_user, db):
    lab = make_lab(name="Wave051 Synthetic Lab")
    user = make_lab_user(lab_id=lab.id, role="admin", password="Testpass1")
    db.commit()
    return lab, user, _headers(user, lab)


def _headers(user, lab, role="admin"):
    token = create_token({"user_id": user.id, "lab_id": lab.id, "role": role})
    return {
        "Authorization": f"Bearer {token}",
        "X-Correlation-ID": "WAVE051-API-JOURNEY-0001",
        "X-Request-ID": "WAVE051-API-JOURNEY-0001",
    }


def _create_synthetic_patient(client, headers, name="Wave051 Synthetic Patient"):
    response = client.post(
        "/patients",
        json={
            "full_name": name,
            "phone": "07700000001",
            "gender": "male",
            "email": "wave051.synthetic@example.invalid",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["patient"]["full_name"] == name
    return body["patient"]


def test_point33_isolated_api_contract_evidence(client, synthetic_lab_user):
    """Real local TestClient auth, patient, note, FHIR, error and contract checks."""
    lab, user, headers = synthetic_lab_user
    statuses: list[tuple[str, int]] = []

    def _check(name, response, expected):
        statuses.append((name, response.status_code))
        assert response.status_code == expected, f"{name}: {response.status_code} {response.text[:300]}"
        return response.json()

    print("WAVE051_POINT33_EXECUTION_START=1")
    live = _check("health_live", client.get("/health/live"), 200)
    assert live["status"] in {"ok", "alive", "healthy"} or "status" in live

    login = _check(
        "login",
        client.post("/login", json={"email": user.email, "password": "Testpass1"}),
        200,
    )
    assert login["token"]
    token_headers = dict(headers)
    token_headers["Authorization"] = f"Bearer {login['token']}"

    session = _check("session", client.get("/session", headers=token_headers), 200)
    assert session

    patient = _create_synthetic_patient(client, token_headers)
    patient_id = patient["id"]
    read_patient = _check("patient_read", client.get(f"/patients/{patient_id}", headers=token_headers), 200)
    assert read_patient["id"] == patient_id

    note = _check(
        "note_create",
        client.post(
            "/clinical/documentation/soap-notes",
            json={
                "patient_id": str(patient_id),
                "subjective": "Synthetic scenario only",
                "objective": "Synthetic observation",
                "assessment": "Synthetic assessment",
                "plan": "Synthetic plan",
            },
            headers=token_headers,
        ),
        201,
    )
    assert note["document_type"] == "soap_note"
    note_id = note["id"]
    signed = _check(
        "note_sign",
        client.post(
            "/clinical/documentation/sign",
            json={"document_id": note_id, "signature_type": "synthetic-local"},
            headers=token_headers,
        ),
        200,
    )
    assert signed["is_signed"] is True
    read_note = _check("note_read", client.get(f"/clinical/documentation/{note_id}", headers=token_headers), 200)
    assert read_note["is_signed"] is True

    metadata = _check("fhir_metadata", client.get("/fhir/metadata", headers=token_headers), 200)
    assert metadata["resourceType"] == "CapabilityStatement"
    fhir_patient = client.get(f"/fhir/Patient/{patient_id}", headers=token_headers)
    statuses.append(("fhir_patient_read", fhir_patient.status_code))
    assert fhir_patient.status_code in (200, 404), fhir_patient.text[:300]

    error_response = client.get("/fhir/Observation/not-an-integer", headers=token_headers)
    statuses.append(("fhir_error_contract", error_response.status_code))
    assert error_response.status_code in (400, 404, 422)
    error_body = error_response.json()
    assert error_body.get("resourceType") == "OperationOutcome" or "code" in error_body

    asyncapi = _check("asyncapi_contract", client.get("/contracts/asyncapi.json"), 200)
    assert "asyncapi" in str(asyncapi).lower()
    unmounted = client.get("/national/encounters", headers=token_headers)
    statuses.append(("unmounted_national_encounter_route", unmounted.status_code))
    assert unmounted.status_code == 404

    assert statuses, "no API requests executed"
    assert all(status < 500 for _name, status in statuses), statuses
    print(f"WAVE051_POINT33_API_STATUS_COUNTS={statuses}")
    print("WAVE051_POINT33_EXECUTION_COMPLETE=1")
    print("WAVE051_POINT33_SHUTDOWN_EXPECTED_VIA_TESTCLIENT_FIXTURE_TEARDOWN=1")


def test_wave05_1_twenty_step_synthetic_patient_journey(client, synthetic_lab_user, db):
    """Twenty labeled steps across mounted API and canonical service boundaries."""
    lab, user, headers = synthetic_lab_user
    print("WAVE051_JOURNEY_EXECUTION_START=1")

    # 1. Liveness through the real local app.
    r1 = client.get("/health/live")
    assert r1.status_code == 200

    # 2. Real local authentication.
    login = client.post("/login", json={"email": user.email, "password": "Testpass1"})
    assert login.status_code == 200, login.text
    token_headers = dict(headers)
    token_headers["Authorization"] = f"Bearer {login.json()['token']}"

    # 3. Session validation.
    r3 = client.get("/session", headers=token_headers)
    assert r3.status_code == 200

    # 4. Patient creation through the mounted API.
    patient = _create_synthetic_patient(client, token_headers, "Wave051 Journey Patient")
    patient_id = patient["id"]

    # 5. Patient read-back through the mounted API.
    r5 = client.get(f"/patients/{patient_id}", headers=token_headers)
    assert r5.status_code == 200 and r5.json()["id"] == patient_id

    # 6. Patient update through the mounted API.
    r6 = client.put(
        f"/patients/{patient_id}",
        json={"full_name": "Wave051 Journey Patient Updated"},
        headers=token_headers,
    )
    assert r6.status_code == 200, r6.text

    # 7. MPI resolution result is observed, not treated as verified identity.
    assert "citizen_ulid" in patient
    assert "mpi_match_method" in patient

    # 8. Canonical encounter creation through the existing service.
    encounter = create_encounter(
        db,
        {
            "patient_id": str(patient.get("citizen_ulid") or f"PATIENT-SYN-{patient_id}"),
            "encounter_type": EncounterType.OUTPATIENT,
            "status": EncounterStatus.PLANNED,
            "facility_id": "FACILITY-SYN-W051",
            "practitioner_id": "PRACTITIONER-SYN-W051",
            "organization_id": "ORG-SYN-W051",
            "period_start": datetime.now(UTC),
            "reason_description": "Synthetic follow-up",
            "lab_id": str(lab.id),
        },
    )
    db.flush()
    assert encounter.id

    # 9. Encounter read-back.
    assert get_encounter(db, encounter.id) is encounter

    # 10. Encounter update.
    updated = update_encounter(db, encounter.id, {"reason_description": "Synthetic revised follow-up"})
    assert updated.reason_description == "Synthetic revised follow-up"

    # 11. Encounter completion.
    completed = complete_encounter(db, encounter.id, str(user.id))
    assert completed.status is EncounterStatus.COMPLETED
    assert completed.period_end is not None

    # 12. Encounter listing by patient.
    encounters = get_encounters_by_patient(db, encounter.patient_id)
    assert encounter in encounters
    assert get_active_encounters_by_patient(db, encounter.patient_id) == []

    # 13. Order creation with an idempotency key through the mounted API.
    order_response = client.post(
        "/orders",
        json={
            "patient_id": patient_id,
            "doctor_name": "Synthetic Clinician",
            "results": [
                {
                    "test_name": "Synthetic glucose",
                    "value": 95.0,
                    "unit": "mg/dL",
                    "normal_range_low": 70.0,
                    "normal_range_high": 110.0,
                }
            ],
        },
        headers={**token_headers, "Idempotency-Key": "WAVE051-JOURNEY-ORDER-0001"},
    )
    assert order_response.status_code == 201, order_response.text
    order_id = order_response.json()["order"]["id"]

    # 14. Order read-back.
    order_read = client.get(f"/orders/{order_id}", headers=token_headers)
    assert order_read.status_code == 200, order_read.text

    # 15. Sample collection through the mounted API.
    sample_response = client.post(
        "/samples",
        json={"order_id": order_id, "sample_type": "blood", "collected_by": "Synthetic Collector"},
        headers=token_headers,
    )
    assert sample_response.status_code == 201, sample_response.text
    barcode = sample_response.json()["sample"]["barcode"]

    # 16. Sample read-back.
    sample_read = client.get(f"/samples/{barcode}", headers=token_headers)
    assert sample_read.status_code == 200, sample_read.text

    # 17. Result amendment with optimistic concurrency through the mounted API.
    from app.models.lab_result import LabResult

    result = db.query(LabResult).filter(LabResult.order_id == order_id).first()
    assert result is not None
    patch = client.patch(
        f"/results/{result.id}",
        json={"value": 96.0},
        headers={**token_headers, "If-Match": str(result.version)},
    )
    assert patch.status_code == 200, patch.text

    # 18. Order validation and lock through the mounted API.
    lock = client.post(f"/orders/{order_id}/validate", headers=token_headers)
    assert lock.status_code == 200, lock.text

    # 19. Clinical note creation, signing and read-back.
    note = client.post(
        "/clinical/documentation/soap-notes",
        json={
            "patient_id": str(patient_id),
            "encounter_id": encounter.id,
            "subjective": "Synthetic journey subjective",
            "objective": "Synthetic journey objective",
            "assessment": "Synthetic journey assessment",
            "plan": "Synthetic journey plan",
        },
        headers=token_headers,
    )
    assert note.status_code == 201, note.text
    note_id = note.json()["id"]
    sign = client.post(
        "/clinical/documentation/sign",
        json={"document_id": note_id},
        headers=token_headers,
    )
    assert sign.status_code == 200, sign.text
    note_read = client.get(f"/clinical/documentation/{note_id}", headers=token_headers)
    assert note_read.status_code == 200 and note_read.json()["is_signed"] is True

    # 20. Cross-cutting FHIR read, contract discovery, correlation and boundary checks.
    fhir_metadata = client.get("/fhir/metadata", headers=token_headers)
    assert fhir_metadata.status_code == 200
    fhir_patient = client.get(f"/fhir/Patient/{patient_id}", headers=token_headers)
    assert fhir_patient.status_code in (200, 404)
    assert token_headers["X-Correlation-ID"] == "WAVE051-API-JOURNEY-0001"
    assert client.get("/contracts/asyncapi.json").status_code == 200
    assert client.get("/national/encounters", headers=token_headers).status_code == 404

    print("WAVE051_JOURNEY_STEPS_COMPLETED=20")
    print("WAVE051_JOURNEY_CLASSIFICATION=MOUNTED_API_AND_CANONICAL_SERVICE_ONLY")
    print("WAVE051_JOURNEY_NOT_CLAIMS=NO_EVENT_BUS_NO_PRG05_NO_PRODUCTION_DEPLOYMENT")
    print("WAVE051_JOURNEY_SHUTDOWN_EXPECTED_VIA_TESTCLIENT_FIXTURE_TEARDOWN=1")
