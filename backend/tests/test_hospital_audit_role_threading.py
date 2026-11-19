"""Regression: Hospital bed/OT service-layer audit records the real actor role.

Five methods in app/services/hospital_service.py (assign_bed, discharge_bed,
transfer_bed, update_operation_theater_status,
complete_surgical_safety_checklist) previously hard-coded
user_role="hospital_staff" in every log_action call, the same systemic shape
found in app/lims/services.py (see test_lims_audit_role_threading.py).
Confirmed via git-stash negative proof: reverting hospital_service.py
reproduces "hospital_staff" in the audit record for every role below; with
the fix applied, the audit record matches the real, server-derived
current_user.role.

Note: Hospital's routes remain schema-blocked for real PostgreSQL deployment
(13/14 tables lack Alembic migrations, per docs/security/AUTHORIZATION_GAP_REGISTER.md) --
this fix is exercised here via the SQLite test harness, the same one used
throughout this program's prior Hospital vertical-slice work.
"""

from typing import Any

import pytest
from app.hospital.models import Bed, OperationTheater
from app.models.audit_log import AuditLog
from app.models.patient import Patient
from app.services.hospital_service import HospitalService


@pytest.mark.parametrize("role", ["nurse", "doctor", "admin", "lab_admin"])
class TestHospitalAuditRoleThreading:
    def test_assign_bed_records_real_role(self, db: Any, make_lab, role):
        lab = make_lab()
        patient = Patient(lab_id=lab.id, full_name="Test Patient", phone="07701234567")
        bed = Bed(lab_id=lab.id, room_id=1, bed_number=f"B-{role}", status="available")
        db.add_all([patient, bed])
        db.flush()

        HospitalService.assign_bed(
            db, lab.id, 101, role, bed.id, patient.id, expected_version=bed.version,
        )
        db.commit()

        entry = (
            db.query(AuditLog)
            .filter(AuditLog.action == "bed.assign", AuditLog.resource_id == str(bed.id))
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert entry is not None
        assert entry.user_role == role

    def test_discharge_bed_records_real_role(self, db: Any, make_lab, role):
        lab = make_lab()
        patient = Patient(lab_id=lab.id, full_name="Test Patient", phone="07701234567")
        bed = Bed(
            lab_id=lab.id, room_id=1, bed_number=f"D-{role}",
            status="occupied", current_patient_id=None,
        )
        db.add_all([patient, bed])
        db.flush()
        bed.current_patient_id = patient.id
        db.flush()

        HospitalService.discharge_bed(db, lab.id, 101, role, bed.id, expected_version=bed.version)
        db.commit()

        entry = (
            db.query(AuditLog)
            .filter(AuditLog.action == "bed.discharge", AuditLog.resource_id == str(bed.id))
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert entry is not None
        assert entry.user_role == role

    def test_ot_status_update_records_real_role(self, db: Any, make_lab, role):
        lab = make_lab()
        theater = OperationTheater(
            lab_id=lab.id, hospital_id=1, code=f"OT-{role}",
            name="Theater", theater_type="general", status="available",
        )
        db.add(theater)
        db.flush()

        HospitalService.complete_surgical_safety_checklist(
            db, lab.id, 101, role,
            {
                "operation_theater_id": theater.id,
                "surgery_id": 7001,
                "patient_id": 77,
                "procedure_name": "Test procedure",
                "procedure_site": "abdomen",
                "planned_laterality": "midline",
                "patient_identity_confirmed": True,
                "procedure_confirmed": True,
                "site_marked": True,
                "consent_verified": True,
                "anesthesia_assessment_complete": True,
                "allergy_reviewed": True,
                "antibiotic_prophylaxis_confirmed": True,
                "blood_products_confirmed": True,
                "imaging_reviewed": True,
                "team_time_out_completed": True,
            },
        )
        HospitalService.update_operation_theater_status(
            db, lab.id, 101, role, theater.id,
            expected_version=theater.version, next_status="in_use", surgery_id=7001,
        )
        db.commit()

        entry = (
            db.query(AuditLog)
            .filter(
                AuditLog.resource_type == "hospital_operation_theater",
                AuditLog.resource_id == str(theater.id),
            )
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert entry is not None
        assert entry.user_role == role
