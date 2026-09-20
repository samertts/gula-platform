"""Hospital service: log_action argument-order fix (systemic pattern
generalized from NHDW's original finding, see
scripts/log_action_arg_order_guard.py).

app/services/hospital_service.py::create_hospital/update_hospital/
deactivate_hospital/create_campus/create_appointment used
log_action(db, action, resource_id, lab_id, user_id, data) -- the exact
RULE_A shape as NHDW's original bug: the resource's own id landed in
resource_type, lab_id landed in resource_id, and (for the 4 calls with a
details dict) that dict landed in user_role, which no DBAPI can bind.
lab_id was never recorded on any of these audit entries. This is the
third independent domain this exact systemic pattern was found and
fixed in this session (NHDW, Nursing/LIMS, now Hospital) -- see
scripts/log_action_arg_order_guard.py and docs/engineering/
MUSTAFA_ACTIVE_REPAIR_QUEUE.md for the full cross-domain record.

This file also shares NHDW's already-documented, NOT-fixed-here
migration gap: HospitalMaster/Campus/etc. (app/hospital/models) have no
migration for their tables anywhere in this repo (pinned by
test_nhdw_admission_lifecycle.py::test_hospital_structure_tables_have_no_migration,
which is not domain-specific -- it already covers this file's
dependency too). These tests use this repo's SQLite test harness (which
builds tables via metadata.create_all() across every declarative Base,
not Alembic), so they prove the Python-level fix is correct without
contradicting that separate, already-recorded production blocker.

create_appointment is additionally, independently latent: `Appointment`
is imported from app.national.domain.appointment, already documented
this session (ems-domain-discovery finding) as LATENT (no migration for
national_appointments) -- not re-verified here, reusing that evidence.
Its log_action call is fixed for correctness (ready the moment that
table exists) but not exercised via a real db.flush() in these tests.
"""
from __future__ import annotations

from app.models.audit_log import AuditLog
from app.services.hospital_service import HospitalService


def test_create_hospital_audits_with_correct_lab_id_and_resource_type(db, make_lab):
    lab = make_lab("Hospital Service Audit Lab 1")
    hospital = HospitalService.create_hospital(
        db, lab_id=lab.id, user_id=1, data={"code": "H1", "name": "Test Hospital", "hospital_type": "general"},
    )

    entry = db.query(AuditLog).filter(AuditLog.action == "hospital.create").order_by(AuditLog.id.desc()).first()
    assert entry is not None
    assert entry.lab_id == lab.id
    assert entry.resource_type == "hospital"
    assert entry.resource_id == hospital.id
    assert entry.user_id == 1
    assert "H1" in (entry.details or "")


def test_update_hospital_audits_with_correct_lab_id(db, make_lab):
    lab = make_lab("Hospital Service Audit Lab 2")
    hospital = HospitalService.create_hospital(
        db, lab_id=lab.id, user_id=1, data={"code": "H2", "name": "Test Hospital 2", "hospital_type": "general"},
    )

    HospitalService.update_hospital(db, hospital_id=hospital.id, lab_id=lab.id, user_id=2, data={"name": "Renamed"})

    entry = db.query(AuditLog).filter(AuditLog.action == "hospital.update").order_by(AuditLog.id.desc()).first()
    assert entry is not None
    assert entry.lab_id == lab.id
    assert entry.resource_type == "hospital"
    assert entry.resource_id == hospital.id


def test_deactivate_hospital_audits_without_a_details_payload(db, make_lab):
    lab = make_lab("Hospital Service Audit Lab 3")
    hospital = HospitalService.create_hospital(
        db, lab_id=lab.id, user_id=1, data={"code": "H3", "name": "Test Hospital 3", "hospital_type": "general"},
    )

    HospitalService.deactivate_hospital(db, hospital_id=hospital.id, lab_id=lab.id, user_id=1)

    entry = db.query(AuditLog).filter(AuditLog.action == "hospital.deactivate").order_by(AuditLog.id.desc()).first()
    assert entry is not None
    assert entry.lab_id == lab.id
    assert entry.resource_type == "hospital"
    assert entry.resource_id == hospital.id


def test_create_campus_audits_with_correct_lab_id_and_resource_type(db, make_lab):
    lab = make_lab("Hospital Service Audit Lab 4")
    hospital = HospitalService.create_hospital(
        db, lab_id=lab.id, user_id=1, data={"code": "H4", "name": "Test Hospital 4", "hospital_type": "general"},
    )

    campus = HospitalService.create_campus(
        db, lab_id=lab.id, user_id=1, hospital_id=hospital.id, data={"code": "C1", "name": "Main Campus"},
    )

    entry = db.query(AuditLog).filter(AuditLog.action == "campus.create").order_by(AuditLog.id.desc()).first()
    assert entry is not None
    assert entry.lab_id == lab.id
    assert entry.resource_type == "campus"
    assert entry.resource_id == campus.id
