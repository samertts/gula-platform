from __future__ import annotations

from datetime import date, timedelta

import pytest
from app.clinical.pharmacy.models import CoreMedicationBatch, CoreMedicationStockLedger

from tests.test_core_appointment_api import appointment_context
from tests.test_core_pharmacy_api import (
    PHARMACY_PERMISSIONS,
    _prescribe,
    _provision_second_actor,
    _set_actor,
    _setup,
)


@pytest.fixture()
def context(request):
    return request.getfixturevalue("appointment_context")


def test_controlled_policy_requires_separate_approval_and_fefo_recall_are_safe(client, context):
    from tests.test_core_lab_result_access_api import _grant_permissions

    _grant_permissions(context, (*PHARMACY_PERMISSIONS, "clinical.medication.controlled_approve"))
    encounter_id, medication = _setup(context, client)
    workspace_id = context["workspace"].id

    controlled = client.post("/api/v1/clinical/medications", headers={"Idempotency-Key": "pharm-controlled-med"}, json={"workspace_id": workspace_id, "code": "SYN-CONTROLLED-001", "generic_name": "Synthetic controlled medicine", "is_controlled": True})
    assert controlled.status_code == 201, controlled.text
    rx = _prescribe(context, client, encounter_id, controlled.json()["id"], quantity=2)
    self_sign = client.post(f"/api/v1/clinical/prescriptions/{rx['id']}/sign", headers={"Idempotency-Key": "pharm-controlled-self-sign", "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert self_sign.status_code == 422 and self_sign.json()["code"] == "CONTROLLED_MEDICATION_POLICY_REQUIRED"

    reviewer_account, reviewer_session, _ = _provision_second_actor(context)
    _set_actor(reviewer_account, reviewer_session)
    approved = client.post(f"/api/v1/clinical/prescriptions/{rx['id']}/controlled-policy/approve", headers={"Idempotency-Key": "pharm-controlled-approve", "If-Match": '"1"'}, json={"workspace_id": workspace_id, "reason": "Synthetic policy review approved"})
    assert approved.status_code == 200, approved.text
    assert approved.json()["version"] == 2
    assert approved.json()["controlled_policy_status"] == "APPROVED_BY_POLICY"
    assert approved.json()["controlled_policy_approved_by_account_id"] == reviewer_account.id
    _set_actor(context["account"], context["session"])
    signed = client.post(f"/api/v1/clinical/prescriptions/{rx['id']}/sign", headers={"Idempotency-Key": "pharm-controlled-sign", "If-Match": '"2"'}, json={"workspace_id": workspace_id})
    assert signed.status_code == 200, signed.text

    normal_rx_response = client.post("/api/v1/clinical/prescriptions", headers={"Idempotency-Key": "pharm-normal-rx-create"}, json={"workspace_id": workspace_id, "encounter_id": encounter_id, "purpose": "treatment", "items": [{"medication_catalog_id": medication["id"], "dose_value": "500", "dose_unit": "mg", "frequency": "twice daily", "route": "oral", "duration_days": 5, "quantity": 4, "quantity_unit": "capsule", "substitution_allowed": False}]})
    assert normal_rx_response.status_code == 201, normal_rx_response.text
    normal_rx = normal_rx_response.json()
    signed_normal = client.post(f"/api/v1/clinical/prescriptions/{normal_rx['id']}/sign", headers={"Idempotency-Key": "pharm-fefo-sign", "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert signed_normal.status_code == 200, signed_normal.text
    item_id = signed_normal.json()["items"][0]["id"]
    later = client.post("/api/v1/clinical/medication-batches", headers={"Idempotency-Key": "pharm-fefo-later"}, json={"workspace_id": workspace_id, "medication_catalog_id": medication["id"], "batch_number": "SYN-FEFO-LATER", "expiry_date": (date.today() + timedelta(days=60)).isoformat(), "quantity_received": 4})
    earlier = client.post("/api/v1/clinical/medication-batches", headers={"Idempotency-Key": "pharm-fefo-earlier"}, json={"workspace_id": workspace_id, "medication_catalog_id": medication["id"], "batch_number": "SYN-FEFO-EARLIER", "expiry_date": (date.today() + timedelta(days=20)).isoformat(), "quantity_received": 4})
    assert later.status_code == 201 and earlier.status_code == 201
    prepared = client.post("/api/v1/clinical/dispenses/fefo", headers={"Idempotency-Key": "pharm-fefo-prepare"}, json={"workspace_id": workspace_id, "prescription_row_id": signed_normal.json()["id"], "prescription_item_id": item_id, "quantity": 2})
    assert prepared.status_code == 201, prepared.text
    assert prepared.json()["batch_id"] == earlier.json()["id"]

    recalled = client.post(f"/api/v1/clinical/medication-batches/{later.json()['id']}/recall", headers={"Idempotency-Key": "pharm-recall-1", "If-Match": '"1"'}, json={"workspace_id": workspace_id, "reason": "Synthetic recall simulation"})
    assert recalled.status_code == 200 and recalled.json()["quarantined"] in (1, True)
    assert recalled.json()["version"] == 2 and recalled.json()["recall_id"]
    recall_replay = client.post(f"/api/v1/clinical/medication-batches/{later.json()['id']}/recall", headers={"Idempotency-Key": "pharm-recall-1", "If-Match": '"1"'}, json={"workspace_id": workspace_id, "reason": "Synthetic recall simulation"})
    assert recall_replay.status_code == 200 and recall_replay.json()["recall_id"] == recalled.json()["recall_id"]
    blocked = client.post("/api/v1/clinical/dispenses", headers={"Idempotency-Key": "pharm-recalled-prepare"}, json={"workspace_id": workspace_id, "prescription_row_id": signed_normal.json()["id"], "prescription_item_id": item_id, "batch_id": later.json()["id"], "quantity": 1})
    assert blocked.status_code == 409 and blocked.json()["code"] == "EXPIRED_MEDICATION"

    adjusted = client.post(f"/api/v1/clinical/medication-batches/{earlier.json()['id']}/adjust", headers={"Idempotency-Key": "pharm-waste-1", "If-Match": '"1"'}, json={"workspace_id": workspace_id, "quantity_delta": -1, "kind": "WASTE", "reason": "Synthetic damaged stock"})
    assert adjusted.status_code == 200, adjusted.text
    assert context["db"].query(CoreMedicationStockLedger).filter(CoreMedicationStockLedger.reference_type == "waste").count() == 1
    assert context["db"].query(CoreMedicationBatch).filter(CoreMedicationBatch.id == earlier.json()["id"]).one().quantity_available == 3
    assert context["db"].query(CoreMedicationBatch).filter(CoreMedicationBatch.id == earlier.json()["id"]).one().version == 2
