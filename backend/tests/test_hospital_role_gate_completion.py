"""Hospital vertical slice, completion of the role-gate pass.

test_hospital_update_security.py fixed create_hospital/update_hospital/
deactivate_hospital/create_campus and explicitly documented (in its own
docstring) that "the entire hospital.py route surface still has no role
gates beyond these four" -- deliberately deferred at the time. This file
closes that deferral: the remaining 19 mutating routes in
app/routes/hospital.py had zero role check beyond bare authentication --
any authenticated LabUser of any role, including non-clinical staff,
could create hospital facility structure (buildings/floors/departments/
clinics/rooms/beds/units/operation-theaters/equipment/cost-centers), and
critically could assign/discharge/transfer a real patient to a bed,
change an operation theater's status, or complete a surgical safety
checklist -- a WHO-mandated patient-safety attestation.

Fixed with the same two-tier role convention already established in
this exact file (_HOSPITAL_ADMIN_ROLES for facility/administrative
master data) and already established elsewhere in this codebase for the
identical clinical-write shape (NHDW's _NHDW_ADMISSION_WRITE_ROLES,
Nursing's _NURSING_WRITE_ROLES) -- both reused verbatim as
_HOSPITAL_CLINICAL_WRITE_ROLES = {admin, master_admin, doctor, nurse}
for bed assign/discharge/transfer, OT status, surgical safety checklist,
and appointment creation. No new role vocabulary invented.

Schema note (not a new finding, re-confirmed this pass): 13 of Hospital's
14 tables have zero Alembic migration; the 14th
(hospital_surgical_safety_checklists) has a migration but it is itself
blocked in the alembic chain on a missing hospital_operation_theaters FK
target. Hospital is therefore SCHEMA-BLOCKED on a real Postgres
deployment (docs/architecture/LIVE_RUNTIME_SURFACE_MAP.md's
"ems-domain-discovery" finding). These tests use this repo's SQLite test
harness (HospitalBase.metadata is created via metadata.create_all() in
conftest.py, independent of Alembic) -- the same harness
test_hospital_update_security.py and test_hospital_service_log_action.py
already use for this exact file. The authorization fix is real and
proven at the code level; production exploitability is gated on the
separate, already-recorded, human-approval-required migration gap.
"""
from __future__ import annotations

import pytest

from app.models.patient import Patient
from app.services.hospital_service import HospitalService

from tests.conftest import auth_headers

STAFF_ROLE = "staff"


@pytest.fixture()
def tree(db, make_lab):
    """A full hospital hierarchy, built via direct service calls (setup
    only -- not the code path under test)."""
    lab = make_lab("Hospital Role Gate Lab")
    hospital = HospitalService.create_hospital(
        db, lab_id=lab.id, user_id=1,
        data={"code": "HRG", "name": "Role Gate Hospital", "hospital_type": "general"},
    )
    campus = HospitalService.create_campus(
        db, lab.id, 1, hospital.id, {"code": "C1", "name": "Main Campus"},
    )
    building = HospitalService.create_building(
        db, lab.id, 1, campus.id, {"code": "B1", "name": "Main Building"},
    )
    dept = HospitalService.create_department(
        db, lab.id, 1, hospital.id, {"code": "D1", "name": "Ward A"},
    )
    room = HospitalService.create_room(
        db, lab.id, 1, dept.id, {"code": "R1", "name": "Room 1", "room_type": "ward"},
    )
    bed = HospitalService.create_bed(db, lab.id, 1, room.id, {"bed_number": "B-101"})
    bed2 = HospitalService.create_bed(db, lab.id, 1, room.id, {"bed_number": "B-102"})
    unit = HospitalService.create_unit(
        db, lab.id, 1, hospital.id, {"code": "U1", "name": "ICU Unit", "unit_type": "icu"},
    )
    ot = HospitalService.create_ot(
        db, lab.id, 1, hospital.id, {"code": "OT1", "name": "Theater 1", "theater_type": "general"},
    )
    equip = HospitalService.create_equipment(
        db, lab.id, 1, hospital.id,
        {"equipment_code": "EQ1", "equipment_name": "Ventilator", "category": "life_support"},
    )
    cc = HospitalService.create_cost_center(
        db, lab.id, 1, hospital.id, {"code": "CC1", "name": "ICU Cost Center", "cost_center_type": "clinical"},
    )
    db.commit()
    return {
        "lab": lab, "hospital": hospital, "campus": campus, "building": building,
        "dept": dept, "room": room, "bed": bed, "bed2": bed2, "unit": unit,
        "ot": ot, "equip": equip, "cc": cc,
    }


@pytest.fixture()
def staff_headers(tree, make_lab_user):
    user = make_lab_user(tree["lab"].id, role=STAFF_ROLE)
    return auth_headers(user.id, tree["lab"].id, role=STAFF_ROLE)


# ── Facility/administrative-structure routes: staff denied (403) ────────────


def test_update_campus_denies_staff(client, tree, staff_headers):
    resp = client.put(
        f"/hospital/campuses/{tree['campus'].id}",
        headers=staff_headers,
        json={"code": "C1", "name": "Hijacked"},
    )
    assert resp.status_code == 403


def test_create_building_denies_staff(client, tree, staff_headers):
    resp = client.post(
        f"/hospital/campuses/{tree['campus'].id}/buildings",
        headers=staff_headers,
        json={"code": "B2", "name": "Rogue Building"},
    )
    assert resp.status_code == 403


def test_create_floor_denies_staff(client, tree, staff_headers):
    resp = client.post(
        f"/hospital/buildings/{tree['building'].id}/floors",
        headers=staff_headers,
        json={"code": "F1", "name": "Floor 1", "floor_number": 1},
    )
    assert resp.status_code == 403


def test_create_department_denies_staff(client, tree, staff_headers):
    resp = client.post(
        f"/hospital/{tree['hospital'].id}/departments",
        headers=staff_headers,
        json={"code": "D2", "name": "Rogue Dept"},
    )
    assert resp.status_code == 403


def test_update_department_denies_staff(client, tree, staff_headers):
    resp = client.put(
        f"/hospital/departments/{tree['dept'].id}",
        headers=staff_headers,
        json={"code": "D1", "name": "Hijacked Dept"},
    )
    assert resp.status_code == 403


def test_create_clinic_denies_staff(client, tree, staff_headers):
    resp = client.post(
        f"/hospital/departments/{tree['dept'].id}/clinics",
        headers=staff_headers,
        json={"code": "CL1", "name": "Rogue Clinic"},
    )
    assert resp.status_code == 403


def test_create_room_denies_staff(client, tree, staff_headers):
    resp = client.post(
        f"/hospital/departments/{tree['dept'].id}/rooms",
        headers=staff_headers,
        json={"code": "R2", "name": "Rogue Room", "room_type": "ward"},
    )
    assert resp.status_code == 403


def test_create_bed_denies_staff(client, tree, staff_headers):
    resp = client.post(
        f"/hospital/rooms/{tree['room'].id}/beds",
        headers=staff_headers,
        json={"bed_number": "B-999"},
    )
    assert resp.status_code == 403


def test_create_unit_denies_staff(client, tree, staff_headers):
    resp = client.post(
        f"/hospital/{tree['hospital'].id}/units",
        headers=staff_headers,
        json={"code": "U2", "name": "Rogue Unit", "unit_type": "icu"},
    )
    assert resp.status_code == 403


def test_create_operation_theater_denies_staff(client, tree, staff_headers):
    resp = client.post(
        f"/hospital/{tree['hospital'].id}/operation-theaters",
        headers=staff_headers,
        json={"code": "OT2", "name": "Rogue Theater", "theater_type": "general"},
    )
    assert resp.status_code == 403


def test_create_equipment_denies_staff(client, tree, staff_headers):
    resp = client.post(
        f"/hospital/{tree['hospital'].id}/equipment",
        headers=staff_headers,
        json={"equipment_code": "EQ2", "equipment_name": "Rogue Device", "category": "diagnostic"},
    )
    assert resp.status_code == 403


def test_update_equipment_denies_staff(client, tree, staff_headers):
    resp = client.put(
        f"/hospital/equipment/{tree['equip'].id}",
        headers=staff_headers,
        json={"equipment_code": "EQ1", "equipment_name": "Hijacked", "category": "life_support"},
    )
    assert resp.status_code == 403


def test_create_cost_center_denies_staff(client, tree, staff_headers):
    resp = client.post(
        f"/hospital/{tree['hospital'].id}/cost-centers",
        headers=staff_headers,
        json={"code": "CC2", "name": "Rogue Cost Center", "cost_center_type": "administrative"},
    )
    assert resp.status_code == 403


# ── Clinical patient-safety routes: staff denied (403), before any
#    ClinicalCommandGuard header is even evaluated ───────────────────────────


def test_assign_bed_denies_staff(client, tree, staff_headers):
    resp = client.post(
        f"/hospital/beds/{tree['bed'].id}/assign",
        headers=staff_headers,
        json={"patient_id": 1},
    )
    assert resp.status_code == 403


def test_discharge_bed_denies_staff(client, tree, staff_headers):
    resp = client.post(
        f"/hospital/beds/{tree['bed'].id}/discharge",
        headers=staff_headers,
        json={},
    )
    assert resp.status_code == 403


def test_transfer_bed_denies_staff(client, tree, staff_headers):
    resp = client.post(
        f"/hospital/beds/{tree['bed'].id}/transfer",
        headers=staff_headers,
        json={"to_bed_id": tree["bed2"].id},
    )
    assert resp.status_code == 403


def test_update_ot_status_denies_staff(client, tree, staff_headers):
    resp = client.put(
        f"/hospital/operation-theaters/{tree['ot'].id}/status",
        headers=staff_headers,
        json={"status": "in_use"},
    )
    assert resp.status_code == 403


def test_complete_surgical_safety_checklist_denies_staff(client, tree, staff_headers):
    resp = client.post(
        f"/hospital/operation-theaters/{tree['ot'].id}/surgical-safety-checklists",
        headers=staff_headers,
        json={
            "surgery_id": 1, "patient_id": 1, "procedure_name": "Appendectomy",
            "procedure_site": "abdomen", "patient_identity_confirmed": True,
            "procedure_confirmed": True, "site_marked": True, "consent_verified": True,
            "anesthesia_assessment_complete": True, "allergy_reviewed": True,
            "antibiotic_prophylaxis_confirmed": True, "blood_products_confirmed": True,
            "imaging_reviewed": True, "team_time_out_completed": True,
        },
    )
    assert resp.status_code == 403


def test_create_appointment_denies_staff(client, tree, staff_headers):
    resp = client.post(
        "/hospital/appointments",
        headers=staff_headers,
        json={"patient_id": 1, "appointment_type": "consult", "scheduled_date": "2027-01-01T10:00:00"},
    )
    assert resp.status_code == 403


# ── Correct-role positive path: fix does not break legitimate use ───────────


def test_admin_can_create_department(client, tree, make_lab_user):
    admin = make_lab_user(tree["lab"].id, role="admin")
    resp = client.post(
        f"/hospital/{tree['hospital'].id}/departments",
        headers=auth_headers(admin.id, tree["lab"].id, role="admin"),
        json={"code": "D9", "name": "Legit Dept"},
    )
    assert resp.status_code == 201, resp.text


def test_nurse_can_assign_bed(client, db, tree, make_lab_user):
    nurse = make_lab_user(tree["lab"].id, role="nurse")
    patient = Patient(lab_id=tree["lab"].id, full_name="Test Patient", phone="0770000000")
    db.add(patient)
    db.commit()
    resp = client.post(
        f"/hospital/beds/{tree['bed'].id}/assign",
        headers={
            **auth_headers(nurse.id, tree["lab"].id, role="nurse"),
            "If-Match": str(tree["bed"].version),
            "Idempotency-Key": "test-assign-bed-nurse-1",
        },
        json={"patient_id": patient.id},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "occupied"


def test_doctor_can_complete_surgical_safety_checklist(client, tree, make_lab_user):
    doctor = make_lab_user(tree["lab"].id, role="doctor")
    resp = client.post(
        f"/hospital/operation-theaters/{tree['ot'].id}/surgical-safety-checklists",
        headers={
            **auth_headers(doctor.id, tree["lab"].id, role="doctor"),
            "If-Match": str(tree["ot"].version),
            "Idempotency-Key": "test-checklist-doctor-1",
        },
        json={
            "surgery_id": 1, "patient_id": 1, "procedure_name": "Appendectomy",
            "procedure_site": "abdomen", "patient_identity_confirmed": True,
            "procedure_confirmed": True, "site_marked": True, "consent_verified": True,
            "anesthesia_assessment_complete": True, "allergy_reviewed": True,
            "antibiotic_prophylaxis_confirmed": True, "blood_products_confirmed": True,
            "imaging_reviewed": True, "team_time_out_completed": True,
        },
    )
    assert resp.status_code == 201, resp.text


# ── Tenant isolation: cross-lab target is rejected, not silently scoped ─────


def test_cross_tenant_bed_assign_is_rejected(client, tree, make_lab, make_lab_user):
    other_lab = make_lab("Hospital Role Gate Lab (Other Tenant)")
    other_admin = make_lab_user(other_lab.id, role="admin")
    resp = client.post(
        f"/hospital/beds/{tree['bed'].id}/assign",
        headers={
            **auth_headers(other_admin.id, other_lab.id, role="admin"),
            "If-Match": str(tree["bed"].version),
            "Idempotency-Key": "test-cross-tenant-assign-1",
        },
        json={"patient_id": 1},
    )
    assert resp.status_code == 404


def test_cross_tenant_department_update_is_rejected(client, tree, make_lab, make_lab_user):
    other_lab = make_lab("Hospital Role Gate Lab (Other Tenant 2)")
    other_admin = make_lab_user(other_lab.id, role="admin")
    resp = client.put(
        f"/hospital/departments/{tree['dept'].id}",
        headers=auth_headers(other_admin.id, other_lab.id, role="admin"),
        json={"code": "D1", "name": "Cross-Tenant Hijack"},
    )
    assert resp.status_code == 404


def test_unauthenticated_requests_rejected(client):
    """Sanity: every route in this file still requires authentication at all
    (the pre-existing baseline the role gate builds on top of)."""
    assert client.post("/hospital/1/departments", json={}).status_code == 401
    assert client.post("/hospital/beds/1/assign", json={"patient_id": 1}).status_code == 401
