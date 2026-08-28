from __future__ import annotations

import pytest

from tests.test_core_appointment_api import appointment_context
from tests.test_core_lab_result_access_api import (
    _create_order_and_specimen,
    _create_visit,
    _grant_permissions,
    _provision_second_actor,
    _set_actor,
    _walk_specimen,
)


@pytest.fixture()
def context(request):
    return request.getfixturevalue("appointment_context")


ADVANCED_PERMISSIONS = (
    "clinical.laboratory.analyzer.manage",
    "clinical.laboratory.analyzer.ingest",
    "clinical.laboratory.qc.write",
)


def _grant_advanced(context):
    _grant_permissions(context, (*ADVANCED_PERMISSIONS, "clinical.lab_order.create", "clinical.lab_order.read", "clinical.lab_order.verify", "clinical.specimen.manage", "clinical.result.write", "clinical.result.read", "clinical.result.validate_technical", "clinical.result.validate_clinical", "clinical.result.release", "clinical.result.amend", "clinical.critical.acknowledge"))


def test_lis_analyzer_message_replay_and_qc_release_gate(client, context):
    _grant_advanced(context)
    workspace_id = context["workspace"].id
    encounter_id = _create_visit(client, context)
    _order, specimen = _create_order_and_specimen(client, context, encounter_id)
    assert _walk_specimen(client, context, specimen["id"]) == 6

    catalog = client.post("/api/v1/clinical/lab/test-catalog", headers={"Idempotency-Key": "catalog-create-1"}, json={"workspace_id": workspace_id, "canonical_code": "CBC", "name": "Complete Blood Count", "system": "LOINC-SYNTHETIC", "specimen_type": "WHOLE_BLOOD", "unit_ucum": "10^9/L"})
    assert catalog.status_code == 201, catalog.text
    catalog_v2 = client.post("/api/v1/clinical/lab/test-catalog", headers={"Idempotency-Key": "catalog-create-2"}, json={"workspace_id": workspace_id, "canonical_code": "CBC", "name": "Complete Blood Count v2", "system": "LOINC-SYNTHETIC", "specimen_type": "WHOLE_BLOOD", "unit_ucum": "10^9/L"})
    assert catalog_v2.status_code == 201 and catalog_v2.json()["version"] == 2
    catalog_list = client.get("/api/v1/clinical/lab/test-catalog", params={"workspace_id": workspace_id, "canonical_code": "CBC"})
    assert catalog_list.status_code == 200 and len(catalog_list.json()["items"]) == 2

    analyzer = client.post("/api/v1/clinical/lab/analyzers", headers={"Idempotency-Key": "analyzer-create-1"}, json={"workspace_id": workspace_id, "section": "Hematology", "manufacturer": "Synthetic Instruments", "model": "SYN-CBC-1", "serial_fingerprint": "synthetic-serial-fingerprint-0001", "protocol": "SYNTHETIC"})
    assert analyzer.status_code == 201, analyzer.text
    analyzer_id = analyzer.json()["id"]
    validated = client.post(f"/api/v1/clinical/lab/analyzers/{analyzer_id}/transition", headers={"Idempotency-Key": "analyzer-validate-1", "If-Match": "1"}, json={"workspace_id": workspace_id, "target_status": "VALIDATED"})
    assert validated.status_code == 200 and validated.json()["status"] == "VALIDATED"
    active = client.post(f"/api/v1/clinical/lab/analyzers/{analyzer_id}/transition", headers={"Idempotency-Key": "analyzer-active-1", "If-Match": "2"}, json={"workspace_id": workspace_id, "target_status": "ACTIVE"})
    assert active.status_code == 200 and active.json()["status"] == "ACTIVE"

    message_payload = {"workspace_id": workspace_id, "message_id": "synthetic-analyzer-message-001", "analyzer_id": analyzer_id, "specimen_id": specimen["id"], "test_code": "CBC", "payload_hash": "a" * 64, "quality_flags": {"qc": "pass"}, "source": "SYNTHETIC"}
    message = client.post("/api/v1/clinical/lab/analyzer-messages", headers={"Idempotency-Key": "analyzer-message-1"}, json=message_payload)
    assert message.status_code == 201, message.text
    replay = client.post("/api/v1/clinical/lab/analyzer-messages", headers={"Idempotency-Key": "analyzer-message-replay"}, json=message_payload)
    assert replay.status_code == 201 and replay.json()["id"] == message.json()["id"]
    conflict_payload = {**message_payload, "payload_hash": "b" * 64}
    conflict = client.post("/api/v1/clinical/lab/analyzer-messages", headers={"Idempotency-Key": "analyzer-message-conflict"}, json=conflict_payload)
    assert conflict.status_code == 409 and conflict.json()["code"] == "ANALYZER_MESSAGE_CONFLICT"

    result = client.post("/api/v1/clinical/results", headers={"Idempotency-Key": "lis-result-1"}, json={"workspace_id": workspace_id, "specimen_id": specimen["id"], "value_numeric": 5.2, "unit": "10^9/L", "reference_low": 4.0, "reference_high": 10.0, "source_message_id": message.json()["message_id"], "provenance_type": "IMPORTED_SYNTHETIC"})
    assert result.status_code == 201, result.text
    result_id = result.json()["id"]
    technical = client.post(f"/api/v1/clinical/results/{result_id}/validate-technical", headers={"Idempotency-Key": "lis-result-tech-1", "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert technical.status_code == 200, technical.text
    reviewer_account, reviewer_session, _ = _provision_second_actor(context)
    _set_actor(reviewer_account, reviewer_session)
    clinical = client.post(f"/api/v1/clinical/results/{result_id}/validate-clinical", headers={"Idempotency-Key": "lis-result-clinical-1", "If-Match": '"2"'}, json={"workspace_id": workspace_id})
    assert clinical.status_code == 200, clinical.text
    blocked = client.post(f"/api/v1/clinical/results/{result_id}/release", headers={"Idempotency-Key": "lis-result-release-blocked", "If-Match": '"3"'}, json={"workspace_id": workspace_id})
    assert blocked.status_code == 409 and blocked.json()["code"] == "QC_FAILED"

    _set_actor(context["account"], context["session"])
    quarantine = client.post(f"/api/v1/clinical/lab/analyzers/{analyzer_id}/transition", headers={"Idempotency-Key": "analyzer-quarantine-1", "If-Match": "3"}, json={"workspace_id": workspace_id, "target_status": "QUARANTINED"})
    assert quarantine.status_code == 200 and quarantine.json()["status"] == "QUARANTINED"
    rejected = client.post("/api/v1/clinical/lab/analyzer-messages", headers={"Idempotency-Key": "analyzer-message-quarantine"}, json={**message_payload, "message_id": "synthetic-analyzer-message-quarantine"})
    assert rejected.status_code == 409 and rejected.json()["code"] == "ANALYZER_UNTRUSTED"
    reactivated = client.post(f"/api/v1/clinical/lab/analyzers/{analyzer_id}/transition", headers={"Idempotency-Key": "analyzer-reactivate-1", "If-Match": "4"}, json={"workspace_id": workspace_id, "target_status": "VALIDATED"})
    assert reactivated.status_code == 200
    active_again = client.post(f"/api/v1/clinical/lab/analyzers/{analyzer_id}/transition", headers={"Idempotency-Key": "analyzer-active-2", "If-Match": "5"}, json={"workspace_id": workspace_id, "target_status": "ACTIVE"})
    assert active_again.status_code == 200
    qc = client.post("/api/v1/clinical/lab/qc", headers={"Idempotency-Key": "lis-qc-1", "If-Match": '"3"'}, json={"workspace_id": workspace_id, "result_id": result_id, "analyzer_id": analyzer_id, "status": "PASS"})
    assert qc.status_code == 201, qc.text
    released = client.post(f"/api/v1/clinical/results/{result_id}/release", headers={"Idempotency-Key": "lis-result-release-1", "If-Match": '"3"'}, json={"workspace_id": workspace_id})
    assert released.status_code == 200 and released.json()["status"] == "RELEASED"
