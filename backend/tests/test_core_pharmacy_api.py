from __future__ import annotations

from datetime import date, timedelta

import pytest
from app.clinical.pharmacy.models import CoreMedicationBatch, CorePrescription
from app.identity.api.workspaces import get_current_niam_actor_sync
from app.main import app

from tests.test_core_lab_result_access_api import (
    _create_visit,
    _grant_permissions,
    _provision_second_actor,
    _set_actor,
)

PHARMACY_PERMISSIONS = (
    "clinical.medication.catalog_manage",
    "clinical.medication.prescribe",
    "clinical.medication.sign",
    "clinical.medication.amend",
    "clinical.medication.inventory",
    "clinical.medication.dispense",
    "clinical.medication.read",
)


@pytest.fixture()
def context(request):
    return request.getfixturevalue("appointment_context")


def _setup(context, client):
    _grant_permissions(context, PHARMACY_PERMISSIONS)
    encounter_id = _create_visit(client, context)
    medication = client.post(
        "/api/v1/clinical/medications",
        headers={"Idempotency-Key": "pharmacy-medication-1"},
        json={"workspace_id": context["workspace"].id, "code": "SYN-AMOX-001", "generic_name": "Synthetic Amoxicillin", "strength_value": "500", "strength_unit": "mg", "dosage_form": "capsule", "route": "oral"},
    )
    assert medication.status_code == 201, medication.text
    return encounter_id, medication.json()


def _prescribe(context, client, encounter_id, medication_id, quantity=5):
    workspace_id = context["workspace"].id
    response = client.post(
        "/api/v1/clinical/prescriptions",
        headers={"Idempotency-Key": "pharmacy-rx-create-1"},
        json={"workspace_id": workspace_id, "encounter_id": encounter_id, "purpose": "treatment", "items": [{"medication_catalog_id": medication_id, "dose_value": "500", "dose_unit": "mg", "frequency": "twice daily", "route": "oral", "duration_days": 5, "quantity": quantity, "quantity_unit": "capsule", "substitution_allowed": False}]},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_prescription_is_signed_immutable_and_amendment_is_new_version(client, context):
    encounter_id, medication = _setup(context, client)
    rx = _prescribe(context, client, encounter_id, medication["id"])
    workspace_id = context["workspace"].id
    signed = client.post(f"/api/v1/clinical/prescriptions/{rx['id']}/sign", headers={"Idempotency-Key": "pharmacy-rx-sign-1", "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert signed.status_code == 200, signed.text
    assert signed.json()["status"] == "SIGNED"
    assert signed.json()["version"] == 2
    fhir_request = client.get(f"/api/v1/clinical/prescriptions/{rx['id']}/fhir?workspace_id={workspace_id}")
    assert fhir_request.status_code == 200, fhir_request.text
    assert fhir_request.json()["resourceType"] == "MedicationRequest"
    assert fhir_request.json()["status"] == "active"

    stale = client.post(f"/api/v1/clinical/prescriptions/{rx['id']}/sign", headers={"Idempotency-Key": "pharmacy-rx-sign-stale", "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert stale.status_code == 409
    assert stale.json()["code"] == "VERSION_CONFLICT"

    amended = client.post(
        f"/api/v1/clinical/prescriptions/{rx['id']}/amend",
        headers={"Idempotency-Key": "pharmacy-rx-amend-1", "If-Match": '"2"'},
        json={"workspace_id": workspace_id, "reason": "Synthetic dose correction", "items": [{"medication_catalog_id": medication["id"], "dose_value": "500", "dose_unit": "mg", "frequency": "once daily", "route": "oral", "duration_days": 5, "quantity": 5, "quantity_unit": "capsule", "substitution_allowed": False}]},
    )
    assert amended.status_code == 200, amended.text
    body = amended.json()
    assert body["status"] == "DRAFT"
    assert body["supersedes_id"] == rx["id"]
    assert body["version"] == 3
    original = context["db"].query(CorePrescription).filter(CorePrescription.id == rx["id"]).one()
    assert original.status == "AMENDED"


def test_dispensing_locks_stock_and_rejects_overdose_expiry_and_same_actor_verification(client, context):
    encounter_id, medication = _setup(context, client)
    rx = _prescribe(context, client, encounter_id, medication["id"], quantity=5)
    workspace_id = context["workspace"].id
    signed = client.post(f"/api/v1/clinical/prescriptions/{rx['id']}/sign", headers={"Idempotency-Key": "pharmacy-dispense-sign", "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert signed.status_code == 200, signed.text
    item_id = signed.json()["items"][0]["id"]
    batch = client.post(
        "/api/v1/clinical/medication-batches",
        headers={"Idempotency-Key": "pharmacy-batch-1"},
        json={"workspace_id": workspace_id, "medication_catalog_id": medication["id"], "batch_number": "SYN-BATCH-001", "expiry_date": (date.today() + timedelta(days=30)).isoformat(), "quantity_received": 3},
    )
    assert batch.status_code == 201, batch.text
    prepared = client.post(
        "/api/v1/clinical/dispenses",
        headers={"Idempotency-Key": "pharmacy-dispense-prepare-1"},
        json={"workspace_id": workspace_id, "prescription_row_id": signed.json()["id"], "prescription_item_id": item_id, "batch_id": batch.json()["id"], "quantity": 2},
    )
    assert prepared.status_code == 201, prepared.text

    same_actor = client.post(f"/api/v1/clinical/dispenses/{prepared.json()['id']}/complete", headers={"Idempotency-Key": "pharmacy-dispense-same-actor", "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert same_actor.status_code == 403
    assert same_actor.json()["code"] == "SEPARATION_OF_DUTIES_REQUIRED"

    reviewer_account, reviewer_session, _ = _provision_second_actor(context)
    _set_actor(reviewer_account, reviewer_session)
    completed = client.post(f"/api/v1/clinical/dispenses/{prepared.json()['id']}/complete", headers={"Idempotency-Key": "pharmacy-dispense-complete-1", "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "PARTIAL"
    fhir_dispense = client.get(f"/api/v1/clinical/dispenses/{prepared.json()['id']}/fhir?workspace_id={workspace_id}")
    assert fhir_dispense.status_code == 200, fhir_dispense.text
    assert fhir_dispense.json()["resourceType"] == "MedicationDispense"
    assert fhir_dispense.json()["status"] == "completed"
    assert context["db"].query(CoreMedicationBatch).filter(CoreMedicationBatch.id == batch.json()["id"]).one().quantity_available == 1

    over = client.post(
        "/api/v1/clinical/dispenses",
        headers={"Idempotency-Key": "pharmacy-dispense-over-1"},
        json={"workspace_id": workspace_id, "prescription_row_id": signed.json()["id"], "prescription_item_id": item_id, "batch_id": batch.json()["id"], "quantity": 3},
    )
    assert over.status_code == 409
    assert over.json()["code"] == "INVENTORY_CONFLICT"

    batch_two = client.post(
        "/api/v1/clinical/medication-batches",
        headers={"Idempotency-Key": "pharmacy-batch-2"},
        json={"workspace_id": workspace_id, "medication_catalog_id": medication["id"], "batch_number": "SYN-BATCH-002", "expiry_date": (date.today() + timedelta(days=30)).isoformat(), "quantity_received": 10},
    )
    assert batch_two.status_code == 201, batch_two.text
    over_prescription = client.post(
        "/api/v1/clinical/dispenses",
        headers={"Idempotency-Key": "pharmacy-dispense-over-prescription"},
        json={"workspace_id": workspace_id, "prescription_row_id": signed.json()["id"], "prescription_item_id": item_id, "batch_id": batch_two.json()["id"], "quantity": 4},
    )
    assert over_prescription.status_code == 409
    assert over_prescription.json()["code"] == "OVER_DISPENSE"

    expired = context["db"].query(CoreMedicationBatch).filter(CoreMedicationBatch.id == batch.json()["id"]).one()
    expired.expiry_date = date.today() - timedelta(days=1)
    context["db"].flush()
    expired_prepare = client.post(
        "/api/v1/clinical/dispenses",
        headers={"Idempotency-Key": "pharmacy-dispense-expired"},
        json={"workspace_id": workspace_id, "prescription_row_id": signed.json()["id"], "prescription_item_id": item_id, "batch_id": batch.json()["id"], "quantity": 1},
    )
    assert expired_prepare.status_code == 409
    assert expired_prepare.json()["code"] == "EXPIRED_MEDICATION"
    app.dependency_overrides.pop(get_current_niam_actor_sync, None)
