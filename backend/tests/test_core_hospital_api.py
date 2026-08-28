from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.clinical.encounters.models import CoreEncounter
from app.clinical.hospital.models import CoreHospitalBed, CoreHospitalRoom, CoreHospitalWard
from app.clinical.pharmacy.models import (
    CoreMedicationCatalog,
    CorePrescription,
    CorePrescriptionItem,
)
from app.identity.models import Permission, RolePermission
from fastapi.testclient import TestClient


def _id(prefix: str) -> str:
    return (prefix + uuid4().hex.upper())[:26]


@pytest.fixture()
def hospital_context(client: TestClient, appointment_context: dict[str, object], db):
    context = appointment_context
    account = context["account"]
    workspace = context["workspace"]
    facility = context["facility"]
    organization = context["organization"]
    role_assignment = context["db"].query(__import__("app.identity.models", fromlist=["RoleAssignment"]).RoleAssignment).filter_by(account_id=account.id).one()
    permission_keys = (
        "clinical.hospital.admission.create",
        "clinical.hospital.admission.transition",
        "clinical.hospital.bed.allocate",
        "clinical.hospital.task.write",
        "clinical.hospital.vitals.write",
        "clinical.hospital.emar.write",
        "clinical.hospital.transfer.write",
        "clinical.hospital.handover.write",
        "clinical.hospital.discharge.write",
        "clinical.hospital.discharge.sign",
        "clinical.hospital.bed.manage",
        "clinical.hospital.care_team.write",
    )
    permissions = []
    for key in permission_keys:
        permission = db.query(Permission).filter(Permission.permission_key == key).first()
        if permission is None:
            permission = Permission(id=_id("PERM"), uuid=str(uuid4()), permission_key=key, name=key, name_ar=key, resource="hospital", action=key.rsplit(".", 1)[-1], sensitivity="high", status="active")
            db.add(permission)
            db.flush()
        if db.query(RolePermission).filter(RolePermission.role_id == role_assignment.role_id, RolePermission.permission_id == permission.id).first() is None:
            db.add(RolePermission(id=_id("RP"), role_id=role_assignment.role_id, permission_id=permission.id, status="active"))
        permissions.append(permission)
    ward = CoreHospitalWard(id=_id("WARD"), facility_id=facility.id, organization_id=organization.id, code="SYN-W1", name="Synthetic Ward", status="ACTIVE", capacity=2, version=1)
    room = CoreHospitalRoom(id=_id("ROOM"), ward_id=ward.id, facility_id=facility.id, organization_id=organization.id, code="SYN-R1", name="Synthetic Room", capacity=2, status="ACTIVE", version=1)
    bed = CoreHospitalBed(id=_id("BED"), room_id=room.id, ward_id=ward.id, facility_id=facility.id, organization_id=organization.id, code="SYN-B1", bed_type="STANDARD", status="AVAILABLE", version=1)
    encounter = CoreEncounter(id=_id("ENC"), appointment_id=_id("APPT"), patient_person_id=context["person"].id, provider_account_id=account.id, organization_id=organization.id, facility_id=facility.id, workspace_id=workspace.id, status="IN_PROGRESS", version=1)
    db.add_all([ward, room, bed, encounter])
    db.flush()
    return {**context, "ward": ward, "room": room, "bed": bed, "encounter": encounter}


def _headers(key: str, version: int | None = None) -> dict[str, str]:
    result = {"Idempotency-Key": key, "X-Request-ID": f"req-{key}"}
    if version is not None:
        result["If-Match"] = f'"{version}"'
    return result


def test_hospital_admission_bed_task_vitals_and_discharge(client: TestClient, hospital_context: dict[str, object]):
    workspace = hospital_context["workspace"]
    ward = hospital_context["ward"]
    bed = hospital_context["bed"]
    encounter = hospital_context["encounter"]
    workspace_id = workspace.id

    admission_payload = {"admission_request_id": "synthetic-admission-001", "encounter_id": encounter.id, "workspace_id": workspace_id, "ward_id": ward.id, "admission_reason": "Synthetic observation", "admission_type": "OBSERVATION"}
    admission = client.post("/api/v1/hospital/admissions", headers=_headers("admission-1"), json=admission_payload)
    assert admission.status_code == 201, admission.text
    admission_body = admission.json()
    assert admission_body["status"] == "REQUESTED"
    replay = client.post("/api/v1/hospital/admissions", headers=_headers("admission-1"), json=admission_payload)
    assert replay.status_code == 201
    assert replay.json()["id"] == admission_body["id"]

    accepted = client.post(f"/api/v1/hospital/admissions/{admission_body['id']}/transition", headers=_headers("admission-accept", 1), json={"workspace_id": workspace_id, "target_status": "ACCEPTED"})
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "ACCEPTED"
    allocated = client.post("/api/v1/hospital/beds/allocate", headers=_headers("bed-1"), json={"admission_id": admission_body["id"], "bed_id": bed.id, "workspace_id": workspace_id})
    assert allocated.status_code == 201, allocated.text
    allocated_body = allocated.json()
    assert allocated_body["bed"]["status"] == "OCCUPIED"
    assert allocated_body["admission"]["status"] == "ADMITTED"

    in_care = client.post(f"/api/v1/hospital/admissions/{admission_body['id']}/transition", headers=_headers("admission-care", 3), json={"workspace_id": workspace_id, "target_status": "IN_CARE"})
    assert in_care.status_code == 200, in_care.text

    task = client.post("/api/v1/hospital/tasks", headers=_headers("task-1"), json={"admission_id": admission_body["id"], "workspace_id": workspace_id, "task_type": "hourly-round", "instructions": "Synthetic task"})
    assert task.status_code == 201, task.text
    task_body = task.json()
    claimed = client.post(f"/api/v1/hospital/tasks/{task_body['id']}/transition", headers=_headers("task-claim", 1), json={"workspace_id": workspace_id, "target_status": "CLAIMED"})
    assert claimed.status_code == 200, claimed.text
    stale = client.post(f"/api/v1/hospital/tasks/{task_body['id']}/transition", headers=_headers("task-stale", 1), json={"workspace_id": workspace_id, "target_status": "IN_PROGRESS"})
    assert stale.status_code == 409
    assert stale.json()["code"] == "VERSION_CONFLICT"

    vital = client.post("/api/v1/hospital/vitals", headers=_headers("vital-1"), json={"admission_id": admission_body["id"], "encounter_id": encounter.id, "workspace_id": workspace_id, "vital_type": "oxygen_saturation", "value_numeric": "88", "unit": "%", "method": "pulse-ox", "source": "MANUAL", "observed_at": "2030-01-01T10:00:00Z"})
    assert vital.status_code == 201, vital.text
    assert vital.json()["validation_status"] == "WARNING"
    assert vital.json()["warning_code"] == "OXYGEN_SATURATION_LOW"

    discharge = client.post("/api/v1/hospital/discharge", headers=_headers("discharge-1"), json={"discharge_request_id": "synthetic-discharge-001", "admission_id": admission_body["id"], "workspace_id": workspace_id, "disposition": "HOME"})
    assert discharge.status_code == 201, discharge.text
    discharge_body = discharge.json()
    ready = client.post(f"/api/v1/hospital/discharge/{discharge_body['id']}/readiness", headers=_headers("discharge-ready", 1), json={"workspace_id": workspace_id, "medication_reconciliation_complete": True, "pending_results_reviewed": True, "follow_up_plan": "Synthetic follow-up", "instructions": "Synthetic instructions"})
    assert ready.status_code == 200, ready.text
    summary = client.post(f"/api/v1/hospital/discharge/{discharge_body['id']}/summary", headers=_headers("summary-1"), json={"workspace_id": workspace_id, "admission_reason": "Synthetic observation", "diagnoses": ["synthetic-diagnosis"], "procedures": [], "treatment": "Synthetic treatment", "medications": [], "results": [], "condition": "stable", "follow_up": "Synthetic follow-up"})
    assert summary.status_code == 201, summary.text
    signed = client.post(f"/api/v1/hospital/discharge-summaries/{summary.json()['id']}/sign", headers=_headers("summary-sign", 1), json={"workspace_id": workspace_id})
    assert signed.status_code == 200, signed.text
    completed = client.post(f"/api/v1/hospital/discharge/{discharge_body['id']}/complete", headers=_headers("discharge-complete", 2), json={"workspace_id": workspace_id})
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "COMPLETED"


def test_hospital_emar_enforces_prescription_identity_and_reason(client: TestClient, hospital_context: dict[str, object], db):
    workspace = hospital_context["workspace"]
    encounter = hospital_context["encounter"]
    account = hospital_context["account"]
    medication = CoreMedicationCatalog(id=_id("MED"), code="SYN-MED-001", code_system="SYNTHETIC", generic_name="Synthetic medicine", is_controlled=0, is_active=1)
    prescription = CorePrescription(id=_id("RX"), prescription_id=_id("RXID"), prescription_number="SYN-RX-001", version=1, encounter_id=encounter.id, patient_person_id=hospital_context["person"].id, prescriber_account_id=account.id, organization_id=workspace.organization_id, facility_id=workspace.facility_id, workspace_id=workspace.id, status="SIGNED", purpose="treatment", controlled_policy_status="NOT_CONTROLLED", signed_by_account_id=account.id, signed_at=datetime.now(UTC))
    item = CorePrescriptionItem(id=_id("ITEM"), prescription_row_id=prescription.id, medication_catalog_id=medication.id, medication_code=medication.code, medication_name=medication.generic_name, dose_value="1", dose_unit="tablet", frequency="once", route="oral", duration_days=1, quantity=1, quantity_unit="tablet", substitution_allowed=0)
    db.add_all([medication, prescription, item])
    db.flush()
    payload = {"admission_id": hospital_context.get("admission_id", "missing"), "prescription_id": prescription.id, "prescription_item_id": item.id, "workspace_id": workspace.id, "administration_key": "synthetic-emar-001", "dose_value": "1", "dose_unit": "tablet", "route": "oral"}
    # Create an admission through the API so the test does not invent an admission owner.
    ward = hospital_context["ward"]
    admission = client.post("/api/v1/hospital/admissions", headers=_headers("emar-admission"), json={"admission_request_id": "synthetic-emar-admission", "encounter_id": encounter.id, "workspace_id": workspace.id, "ward_id": ward.id, "admission_reason": "Synthetic eMAR", "admission_type": "OBSERVATION"})
    assert admission.status_code == 201, admission.text
    accepted = client.post(f"/api/v1/hospital/admissions/{admission.json()['id']}/transition", headers=_headers("emar-admission-accept", 1), json={"workspace_id": workspace.id, "target_status": "ACCEPTED"})
    assert accepted.status_code == 200, accepted.text
    payload["admission_id"] = admission.json()["id"]
    emar = client.post("/api/v1/hospital/medications", headers=_headers("emar-create"), json=payload)
    assert emar.status_code == 201, emar.text
    emar_body = emar.json()
    held_without_reason = client.post(f"/api/v1/hospital/medications/{emar_body['id']}/transition", headers=_headers("emar-held", 1), json={"workspace_id": workspace.id, "target_status": "HELD"})
    assert held_without_reason.status_code == 422
    assert held_without_reason.json()["code"] == "VALIDATION_ERROR"


def test_hospital_provisions_bed_hierarchy_and_care_team_member(client: TestClient, hospital_context: dict[str, object]):
    workspace_id = hospital_context["workspace"].id
    ward = client.post("/api/v1/hospital/wards", headers=_headers("provision-ward"), json={"workspace_id": workspace_id, "code": "SYN-W2", "name": "Synthetic Ward 2", "capacity": 1})
    assert ward.status_code == 201, ward.text
    room = client.post("/api/v1/hospital/rooms", headers=_headers("provision-room"), json={"workspace_id": workspace_id, "ward_id": ward.json()["id"], "code": "SYN-R2", "name": "Synthetic Room 2", "capacity": 1})
    assert room.status_code == 201, room.text
    bed = client.post("/api/v1/hospital/beds", headers=_headers("provision-bed"), json={"workspace_id": workspace_id, "room_id": room.json()["id"], "code": "SYN-B2", "bed_type": "STANDARD"})
    assert bed.status_code == 201, bed.text
    bed_replay = client.post("/api/v1/hospital/beds", headers=_headers("provision-bed"), json={"workspace_id": workspace_id, "room_id": room.json()["id"], "code": "SYN-B2", "bed_type": "STANDARD"})
    assert bed_replay.status_code == 201
    assert bed_replay.json()["id"] == bed.json()["id"]

    encounter = hospital_context["encounter"]
    admission = client.post("/api/v1/hospital/admissions", headers=_headers("care-team-admission"), json={"admission_request_id": "synthetic-care-admission", "encounter_id": encounter.id, "workspace_id": workspace_id, "ward_id": hospital_context["ward"].id, "admission_reason": "Synthetic care team", "admission_type": "OBSERVATION"})
    assert admission.status_code == 201, admission.text
    team = client.post("/api/v1/hospital/care-team", headers=_headers("care-team-add"), json={"workspace_id": workspace_id, "admission_id": admission.json()["id"], "account_id": hospital_context["account"].id, "role": "physician", "scope": "care-plan", "purpose": "Synthetic treatment coordination"})
    assert team.status_code == 201, team.text
    assert team.json()["scope"] == "care-plan"


def test_hospital_denies_wrong_workspace(client: TestClient, hospital_context: dict[str, object]):
    encounter = hospital_context["encounter"]
    ward = hospital_context["ward"]
    response = client.post("/api/v1/hospital/admissions", headers=_headers("wrong-workspace"), json={"admission_request_id": "synthetic-wrong-workspace", "encounter_id": encounter.id, "workspace_id": "Z" * 26, "ward_id": ward.id, "admission_reason": "Synthetic", "admission_type": "OBSERVATION"})
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"
