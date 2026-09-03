from __future__ import annotations

from uuid import uuid4

import pytest
from app.identity.models import Permission, RoleAssignment, RolePermission
from fastapi.testclient import TestClient


def _id(prefix: str) -> str:
    return (prefix + uuid4().hex.upper())[:26]


def _headers(key: str, version: int | None = None) -> dict[str, str]:
    result = {"Idempotency-Key": key, "X-Request-ID": f"req-{key}"}
    if version is not None:
        result["If-Match"] = f'"{version}"'
    return result


@pytest.fixture()
def emergency_context(client: TestClient, appointment_context: dict[str, object], db):
    role_assignment = db.query(RoleAssignment).filter(RoleAssignment.account_id == appointment_context["account"].id).one()
    keys = (
        "clinical.emergency.subject.write",
        "clinical.emergency.incident.write",
        "clinical.emergency.triage.write",
        "clinical.emergency.dispatch.write",
        "clinical.emergency.treatment.write",
        "clinical.emergency.prealert.write",
        "clinical.emergency.handover.write",
        "clinical.emergency.epcr.write",
        "clinical.emergency.epcr.sign",
        "clinical.emergency.break_glass.write",
        "clinical.emergency.break_glass.activate",
        "clinical.emergency.break_glass.revoke",
    )
    for key in keys:
        permission = db.query(Permission).filter(Permission.permission_key == key).first()
        if permission is None:
            permission = Permission(id=_id("PERM"), uuid=str(uuid4()), permission_key=key, name=key, name_ar=key, resource="emergency", action=key.rsplit(".", 1)[-1], sensitivity="high", status="active")
            db.add(permission)
            db.flush()
        if db.query(RolePermission).filter(RolePermission.role_id == role_assignment.role_id, RolePermission.permission_id == permission.id).first() is None:
            db.add(RolePermission(id=_id("RP"), role_id=role_assignment.role_id, permission_id=permission.id, status="active"))
    db.flush()
    return appointment_context


def test_emergency_temporary_subject_dispatch_prealert_handover_epcr(client: TestClient, emergency_context: dict[str, object]):
    workspace = emergency_context["workspace"]
    workspace_id = workspace.id

    subject = client.post("/api/v1/emergency/temporary-subjects", headers=_headers("subject-1"), json={"workspace_id": workspace_id, "synthetic_label": "Synthetic unidentified subject"})
    assert subject.status_code == 201, subject.text
    subject_body = subject.json()
    replay = client.post("/api/v1/emergency/temporary-subjects", headers=_headers("subject-1"), json={"workspace_id": workspace_id, "synthetic_label": "Synthetic unidentified subject"})
    assert replay.status_code == 201
    assert replay.json()["id"] == subject_body["id"]

    incident = client.post("/api/v1/emergency/incidents", headers=_headers("incident-1"), json={"incident_id": "synthetic-incident-001", "workspace_id": workspace_id, "temporary_subject_id": subject_body["id"], "chief_complaint": "Synthetic acute complaint", "priority": "STAT", "location_summary": "Synthetic location"})
    assert incident.status_code == 201, incident.text
    incident_body = incident.json()
    triage = client.post("/api/v1/emergency/triage", headers=_headers("triage-1"), json={"workspace_id": workspace_id, "triage_id": "synthetic-triage-001", "incident_id": incident_body["id"], "category": "IMMEDIATE", "clinician_summary": "Synthetic triage", "vital_snapshot": {"oxygen_saturation": 87, "gcs": 12, "private_phi": "must-not-persist"}})
    assert triage.status_code == 201, triage.text
    assert "private_phi" not in triage.json()["vital_snapshot"]

    dispatch = client.post("/api/v1/emergency/dispatches", headers=_headers("dispatch-1"), json={"workspace_id": workspace_id, "dispatch_request_id": "synthetic-dispatch-001", "incident_id": incident_body["id"], "ambulance_reference": "SYN-AMB-01", "crew_references": ["SYN-CREW-1"], "dispatch_notes": "Synthetic dispatch"})
    assert dispatch.status_code == 201, dispatch.text
    dispatch_body = dispatch.json()
    en_route = client.post(f"/api/v1/emergency/dispatches/{dispatch_body['id']}/transition", headers=_headers("dispatch-en-route", 1), json={"workspace_id": workspace_id, "target_status": "EN_ROUTE"})
    assert en_route.status_code == 200, en_route.text
    on_scene = client.post(f"/api/v1/emergency/dispatches/{dispatch_body['id']}/transition", headers=_headers("dispatch-on-scene", 2), json={"workspace_id": workspace_id, "target_status": "ON_SCENE"})
    assert on_scene.status_code == 200, on_scene.text

    prealert = client.post("/api/v1/emergency/prealerts", headers=_headers("prealert-1"), json={"workspace_id": workspace_id, "prealert_request_id": "synthetic-prealert-001", "incident_id": incident_body["id"], "destination_facility_reference": "SYN-FAC-DEST", "acuity": "STAT", "estimated_arrival_minutes": 12, "minimal_payload": {"chief_complaint": "Synthetic acute complaint", "vital_summary": {"gcs": 12}, "raw_document": "must-not-persist"}})
    assert prealert.status_code == 201, prealert.text
    assert "raw_document" not in prealert.json()["minimal_payload"]
    prealert_ack = client.post(f"/api/v1/emergency/prealerts/{prealert.json()['id']}/ack", headers=_headers("prealert-ack", 1), json={"workspace_id": workspace_id, "target_status": "ACKNOWLEDGED"})
    assert prealert_ack.status_code == 200, prealert_ack.text

    transporting = client.post(f"/api/v1/emergency/dispatches/{dispatch_body['id']}/transition", headers=_headers("dispatch-transporting", 3), json={"workspace_id": workspace_id, "target_status": "TRANSPORTING"})
    assert transporting.status_code == 200, transporting.text
    handover = client.post("/api/v1/emergency/handovers", headers=_headers("handover-1"), json={"workspace_id": workspace_id, "handover_request_id": "synthetic-handover-001", "incident_id": incident_body["id"], "receiving_facility_reference": "SYN-FAC-DEST", "minimal_summary": {"diagnosis_context": "Synthetic", "vital_summary": {"gcs": 12}, "risks": ["synthetic"], "raw_phi": "must-not-persist"}})
    assert handover.status_code == 201, handover.text
    assert "raw_phi" not in handover.json()["minimal_summary"]
    handover_body = handover.json()
    handover_ack = client.post(f"/api/v1/emergency/handovers/{handover_body['id']}/ack", headers=_headers("handover-ack", 1), json={"workspace_id": workspace_id, "target_status": "ACKNOWLEDGED"})
    assert handover_ack.status_code == 200, handover_ack.text
    assert handover_ack.json()["status"] == "ACKNOWLEDGED"
    handover_amend = client.post(f"/api/v1/emergency/handovers/{handover_body['id']}/amend", headers=_headers("handover-amend", 2), json={"workspace_id": workspace_id, "handover_request_id": "synthetic-handover-002", "receiving_facility_reference": "SYN-FAC-DEST", "minimal_summary": {"diagnosis_context": "Synthetic amendment", "pending_actions": ["synthetic follow-up"], "raw_phi": "must-not-persist"}, "amendment_reason": "Synthetic correction"})
    assert handover_amend.status_code == 201, handover_amend.text
    assert handover_amend.json()["supersedes_id"] == handover_body["id"]
    assert "raw_phi" not in handover_amend.json()["minimal_summary"]

    epcr = client.post("/api/v1/emergency/epcr", headers=_headers("epcr-1"), json={"workspace_id": workspace_id, "epcr_id": "synthetic-epcr-001", "incident_id": incident_body["id"], "chief_complaint": "Synthetic complaint", "narrative": "Synthetic narrative", "interventions": [{"type": "synthetic-observation"}], "destination_facility_reference": "SYN-FAC-DEST", "signature_evidence": {"method": "synthetic-test-signature"}})
    assert epcr.status_code == 201, epcr.text
    signed = client.post(f"/api/v1/emergency/epcr/{epcr.json()['id']}/sign", headers=_headers("epcr-sign", 1), json={"workspace_id": workspace_id})
    assert signed.status_code == 200, signed.text
    assert signed.json()["status"] == "SIGNED"
    epcr_amend = client.post(f"/api/v1/emergency/epcr/{epcr.json()['id']}/amend", headers=_headers("epcr-amend", 2), json={"workspace_id": workspace_id, "epcr_id": "synthetic-epcr-001", "chief_complaint": "Synthetic amended complaint", "narrative": "Synthetic amended narrative", "interventions": [{"type": "synthetic-correction"}], "destination_facility_reference": "SYN-FAC-DEST", "amendment_reason": "Synthetic correction"})
    assert epcr_amend.status_code == 201, epcr_amend.text
    assert epcr_amend.json()["version"] == 3
    amended_signed = client.post(f"/api/v1/emergency/epcr/{epcr_amend.json()['id']}/sign", headers=_headers("epcr-amend-sign", 3), json={"workspace_id": workspace_id, "signature_evidence": {"method": "synthetic-amendment-signature"}})
    assert amended_signed.status_code == 200, amended_signed.text
    assert amended_signed.json()["status"] == "SIGNED"


def test_break_glass_is_scoped_expiring_and_revocable(client: TestClient, emergency_context: dict[str, object]):
    workspace_id = emergency_context["workspace"].id
    request = client.post("/api/v1/emergency/break-glass", headers=_headers("break-glass-request"), json={"request_id": "synthetic-bg-001", "workspace_id": workspace_id, "patient_person_id": emergency_context["person"].id, "reason": "Synthetic immediate safety review", "purpose": "Emergency clinical access", "resource_scope": {"resources": ["emergency_summary"]}, "duration_minutes": 15})
    assert request.status_code == 201, request.text
    body = request.json()
    assert body["status"] == "REQUESTED"
    activated = client.post(f"/api/v1/emergency/break-glass/{body['id']}/activate", headers=_headers("break-glass-activate", 1), json={"workspace_id": workspace_id})
    assert activated.status_code == 200, activated.text
    assert activated.json()["status"] == "ACTIVE"
    stale = client.post(f"/api/v1/emergency/break-glass/{body['id']}/revoke", headers=_headers("break-glass-stale", 1), json={"workspace_id": workspace_id})
    assert stale.status_code == 409
    revoked = client.post(f"/api/v1/emergency/break-glass/{body['id']}/revoke", headers=_headers("break-glass-revoke", 2), json={"workspace_id": workspace_id})
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["status"] == "REVOKED"


def test_emergency_manual_reconciliation_requires_explicit_match_and_blocks_wrong_patient(client: TestClient, emergency_context: dict[str, object]):
    workspace_id = emergency_context["workspace"].id
    subject = client.post("/api/v1/emergency/temporary-subjects", headers=_headers("subject-reconcile"), json={"workspace_id": workspace_id, "synthetic_label": "Synthetic reconciliation subject"})
    assert subject.status_code == 201, subject.text
    subject_id = subject.json()["id"]
    missing_person = client.post(f"/api/v1/emergency/temporary-subjects/{subject_id}/reconcile", headers=_headers("reconcile-missing", 1), json={"workspace_id": workspace_id, "resolution": "MATCHED", "reason": "Synthetic match without person"})
    assert missing_person.status_code == 422
    assert missing_person.json()["code"] == "RECONCILIATION_PERSON_REQUIRED"
    review = client.post(f"/api/v1/emergency/temporary-subjects/{subject_id}/reconcile", headers=_headers("reconcile-review", 1), json={"workspace_id": workspace_id, "resolution": "REQUIRES_REVIEW", "reason": "Synthetic ambiguous evidence"})
    assert review.status_code == 200, review.text
    matched = client.post(f"/api/v1/emergency/temporary-subjects/{subject_id}/reconcile", headers=_headers("reconcile-match", 2), json={"workspace_id": workspace_id, "resolution": "MATCHED", "person_id": emergency_context["person"].id, "reason": "Synthetic human-approved match"})
    assert matched.status_code == 200, matched.text
    wrong_person = client.post(f"/api/v1/emergency/temporary-subjects/{subject_id}/reconcile", headers=_headers("reconcile-wrong", 3), json={"workspace_id": workspace_id, "resolution": "MATCHED", "person_id": "Z" * 26, "reason": "Synthetic wrong-patient attempt"})
    assert wrong_person.status_code == 409
    assert wrong_person.json()["code"] == "RECONCILIATION_ALREADY_FINAL"


def test_emergency_wrong_subject_reference_is_rejected(client: TestClient, emergency_context: dict[str, object]):
    response = client.post("/api/v1/emergency/incidents", headers=_headers("incident-invalid-subject"), json={"incident_id": "synthetic-invalid-incident", "workspace_id": emergency_context["workspace"].id, "chief_complaint": "Synthetic", "patient_person_id": emergency_context["person"].id, "temporary_subject_id": "Z" * 26})
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
