"""Imaging vertical slice (Order -> Exam -> Report), authorization hardening.

Before this pass, the entire radiology module (app/radiology/routes.py,
app/radiology/services.py) had zero role-based authorization anywhere:
current_user.role was only ever read to attribute audit log entries
(actor_role=current_user.role), never compared against an allowed set. Any
authenticated LabUser of any role could create, draft-edit, finalize,
amend, or verify a clinical radiology report, or arbitrarily rewrite an
order's status with no state-transition guard at all
(services.py::update_order_status did `order.status = status` on any
client-supplied string, with no CAS).

Everything else in this module (report state machine, .with_for_update()
row locks, version-checked CAS, amendment history, critical-finding-
notification-before-finalize) was already mature and is left untouched —
this file proves only the authorization/state-machine/CAS gaps that were
actually missing, reusing the exact role tiers and CAS techniques already
established for Laboratory (services/order_service.py, routes/samples.py)
and for radiology's own report/exam handling (_locked_report,
update_exam_status).
"""
from __future__ import annotations

from app.models.patient import Patient
from app.radiology.enums import ExamStatus, ModalityType, ReportStatus
from app.radiology.models import RadiologyExam, RadiologyOrder, RadiologyReport

from tests.conftest import auth_headers


def _make_patient(db, lab_id: int, health_id: str) -> Patient:
    patient = Patient(
        lab_id=lab_id,
        health_id=health_id,
        full_name=f"Patient {health_id}",
        phone=f"0770{health_id[-7:]}",
    )
    db.add(patient)
    db.flush()
    return patient


def _make_order(db, patient: Patient, suffix: str, status: str = "pending") -> RadiologyOrder:
    order = RadiologyOrder(
        patient_id=str(patient.id),
        order_number=f"ORD-AUTHZ-{suffix}",
        modality=ModalityType.CT,
        status=status,
    )
    db.add(order)
    db.flush()
    return order


def _make_exam(db, patient: Patient, suffix: str, status=ExamStatus.SCHEDULED) -> RadiologyExam:
    exam = RadiologyExam(
        patient_id=str(patient.id),
        accession_number=f"ACC-AUTHZ-{suffix}",
        modality=ModalityType.CT,
        status=status,
    )
    db.add(exam)
    db.flush()
    return exam


def _make_report(db, patient: Patient, suffix: str, **kwargs) -> RadiologyReport:
    report = RadiologyReport(
        exam_id=f"EXAM-AUTHZ-{suffix}",
        accession_number=f"ACC-AUTHZ-{suffix}",
        patient_id=str(patient.id),
        status=kwargs.pop("status", ReportStatus.DRAFT),
        **kwargs,
    )
    db.add(report)
    db.flush()
    return report


# ─── create_report: role gate + radiologist_id ownership validation ────────


def test_create_report_requires_clinical_write_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Radiology Authz Lab 1")
    staff = make_lab_user(lab.id, role="staff")
    patient = _make_patient(db, lab.id, "H-RA-001")

    before = db.query(RadiologyReport).count()
    res = client.post(
        "/radiology/reports",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={
            "exam_id": "EXAM-X", "accession_number": "ACC-X",
            "patient_id": str(patient.id),
        },
    )
    assert res.status_code == 403
    assert db.query(RadiologyReport).count() == before


def test_create_report_allowed_for_doctor(client, db, make_lab, make_lab_user):
    lab = make_lab("Radiology Authz Lab 2")
    doctor = make_lab_user(lab.id, role="doctor")
    patient = _make_patient(db, lab.id, "H-RA-002")

    res = client.post(
        "/radiology/reports",
        headers=auth_headers(doctor.id, lab.id, role="doctor"),
        json={
            "exam_id": "EXAM-X", "accession_number": "ACC-X",
            "patient_id": str(patient.id),
        },
    )
    assert res.status_code == 201


def test_create_report_rejects_radiologist_id_in_another_lab(client, db, make_lab, make_lab_user):
    lab_one = make_lab("Radiology Authz Lab 3a")
    lab_two = make_lab("Radiology Authz Lab 3b")
    doctor = make_lab_user(lab_one.id, role="doctor")
    other_lab_doctor = make_lab_user(lab_two.id, role="doctor")
    patient = _make_patient(db, lab_one.id, "H-RA-003")

    before = db.query(RadiologyReport).count()
    res = client.post(
        "/radiology/reports",
        headers=auth_headers(doctor.id, lab_one.id, role="doctor"),
        json={
            "exam_id": "EXAM-X", "accession_number": "ACC-X",
            "patient_id": str(patient.id),
            "radiologist_id": str(other_lab_doctor.id),
        },
    )
    assert res.status_code == 400
    assert db.query(RadiologyReport).count() == before


def test_create_report_rejects_radiologist_id_with_wrong_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Radiology Authz Lab 4")
    doctor = make_lab_user(lab.id, role="doctor")
    staff = make_lab_user(lab.id, role="staff")
    patient = _make_patient(db, lab.id, "H-RA-004")

    res = client.post(
        "/radiology/reports",
        headers=auth_headers(doctor.id, lab.id, role="doctor"),
        json={
            "exam_id": "EXAM-X", "accession_number": "ACC-X",
            "patient_id": str(patient.id),
            "radiologist_id": str(staff.id),
        },
    )
    assert res.status_code == 400


def test_create_report_accepts_valid_same_lab_radiologist_id(client, db, make_lab, make_lab_user):
    lab = make_lab("Radiology Authz Lab 5")
    doctor = make_lab_user(lab.id, role="doctor")
    radiologist = make_lab_user(lab.id, role="doctor")
    patient = _make_patient(db, lab.id, "H-RA-005")

    res = client.post(
        "/radiology/reports",
        headers=auth_headers(doctor.id, lab.id, role="doctor"),
        json={
            "exam_id": "EXAM-X", "accession_number": "ACC-X",
            "patient_id": str(patient.id),
            "radiologist_id": str(radiologist.id),
        },
    )
    assert res.status_code == 201
    assert res.json()["radiologist_id"] == str(radiologist.id)


# ─── save_report_draft / finalize / amend / verify: role gates ─────────────


def test_save_report_draft_requires_clinical_write_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Radiology Authz Lab 6")
    staff = make_lab_user(lab.id, role="staff")
    patient = _make_patient(db, lab.id, "H-RA-006")
    report = _make_report(db, patient, "006")
    db.commit()

    res = client.put(
        f"/radiology/reports/{report.id}/draft",
        headers={
            **auth_headers(staff.id, lab.id, role="staff"),
            "If-Match": str(report.version), "Idempotency-Key": "k-006",
        },
        json={"findings": "should not be saved"},
    )
    assert res.status_code == 403

    db.expire_all()
    report_db = db.query(RadiologyReport).filter(RadiologyReport.id == report.id).first()
    assert report_db.findings is None


def test_finalize_report_requires_signoff_role(client, db, make_lab, make_lab_user):
    """technician is a valid clinical-write role (can draft) but not a
    signoff role — finalizing/amending/verifying a report is a narrower,
    physician-tier act, matching validate_order's narrower tier relative to
    update_result in the Laboratory slice."""
    lab = make_lab("Radiology Authz Lab 7")
    tech = make_lab_user(lab.id, role="technician")
    patient = _make_patient(db, lab.id, "H-RA-007")
    report = _make_report(db, patient, "007", findings="abnormality noted")
    db.commit()

    res = client.put(
        f"/radiology/reports/{report.id}/finalize",
        headers={
            **auth_headers(tech.id, lab.id, role="technician"),
            "If-Match": str(report.version), "Idempotency-Key": "k-007",
        },
        json={},
    )
    assert res.status_code == 403

    db.expire_all()
    report_db = db.query(RadiologyReport).filter(RadiologyReport.id == report.id).first()
    assert report_db.status == ReportStatus.DRAFT


def test_finalize_report_allowed_for_doctor(client, db, make_lab, make_lab_user):
    lab = make_lab("Radiology Authz Lab 8")
    doctor = make_lab_user(lab.id, role="doctor")
    patient = _make_patient(db, lab.id, "H-RA-008")
    report = _make_report(db, patient, "008", findings="abnormality noted")
    db.commit()

    res = client.put(
        f"/radiology/reports/{report.id}/finalize",
        headers={
            **auth_headers(doctor.id, lab.id, role="doctor"),
            "If-Match": str(report.version), "Idempotency-Key": "k-008",
        },
        json={},
    )
    assert res.status_code == 200
    assert res.json()["status"] == ReportStatus.FINAL.value


def test_amend_report_requires_signoff_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Radiology Authz Lab 9")
    tech = make_lab_user(lab.id, role="technician")
    patient = _make_patient(db, lab.id, "H-RA-009")
    report = _make_report(
        db, patient, "009", status=ReportStatus.FINAL,
        findings="f", impression="i",
    )
    db.commit()

    res = client.put(
        f"/radiology/reports/{report.id}/amend",
        headers={
            **auth_headers(tech.id, lab.id, role="technician"),
            "If-Match": str(report.version), "Idempotency-Key": "k-009",
        },
        json={"findings": "new findings", "impression": "new impression", "reason": "correction"},
    )
    assert res.status_code == 403

    db.expire_all()
    report_db = db.query(RadiologyReport).filter(RadiologyReport.id == report.id).first()
    assert report_db.status == ReportStatus.FINAL
    assert report_db.findings == "f"


def test_verify_report_requires_signoff_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Radiology Authz Lab 10")
    tech = make_lab_user(lab.id, role="technician")
    patient = _make_patient(db, lab.id, "H-RA-010")
    report = _make_report(
        db, patient, "010", status=ReportStatus.FINAL,
        findings="f", impression="i", radiologist_id="999999",
    )
    db.commit()

    res = client.put(
        f"/radiology/reports/{report.id}/verify",
        headers={
            **auth_headers(tech.id, lab.id, role="technician"),
            "If-Match": str(report.version), "Idempotency-Key": "k-010",
        },
    )
    assert res.status_code == 403

    db.expire_all()
    report_db = db.query(RadiologyReport).filter(RadiologyReport.id == report.id).first()
    assert report_db.verified_at is None


# ─── update_order_status: role gate + transition guard + CAS ───────────────


def test_update_order_status_requires_write_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Radiology Authz Lab 11")
    staff = make_lab_user(lab.id, role="staff")
    patient = _make_patient(db, lab.id, "H-RA-011")
    order = _make_order(db, patient, "011")
    db.commit()
    version_before = order.version

    res = client.put(
        f"/radiology/orders/{order.id}/status",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={"status": "scheduled"},
    )
    assert res.status_code == 403

    db.expire_all()
    order_db = db.query(RadiologyOrder).filter(RadiologyOrder.id == order.id).first()
    assert order_db.status == "pending"
    assert order_db.version == version_before


def test_update_order_status_illegal_transition_rejected(client, db, make_lab, make_lab_user):
    """pending -> completed skips scheduled/in_progress entirely — must be
    refused, not silently accepted as the pre-fix code did for any string."""
    lab = make_lab("Radiology Authz Lab 12")
    admin = make_lab_user(lab.id, role="admin")
    patient = _make_patient(db, lab.id, "H-RA-012")
    order = _make_order(db, patient, "012")
    db.commit()
    version_before = order.version

    res = client.put(
        f"/radiology/orders/{order.id}/status",
        headers=auth_headers(admin.id, lab.id, role="admin"),
        json={"status": "completed"},
    )
    assert res.status_code == 409

    db.expire_all()
    order_db = db.query(RadiologyOrder).filter(RadiologyOrder.id == order.id).first()
    assert order_db.status == "pending"
    assert order_db.version == version_before


def test_update_order_status_legal_transition_succeeds(client, db, make_lab, make_lab_user):
    lab = make_lab("Radiology Authz Lab 13")
    admin = make_lab_user(lab.id, role="admin")
    patient = _make_patient(db, lab.id, "H-RA-013")
    order = _make_order(db, patient, "013")
    db.commit()
    version_before = order.version

    res = client.put(
        f"/radiology/orders/{order.id}/status",
        headers=auth_headers(admin.id, lab.id, role="admin"),
        json={"status": "scheduled"},
    )
    assert res.status_code == 200

    db.expire_all()
    order_db = db.query(RadiologyOrder).filter(RadiologyOrder.id == order.id).first()
    assert order_db.status == "scheduled"
    assert order_db.version == version_before + 1


def test_update_order_status_cancelled_is_terminal(client, db, make_lab, make_lab_user):
    lab = make_lab("Radiology Authz Lab 14")
    admin = make_lab_user(lab.id, role="admin")
    patient = _make_patient(db, lab.id, "H-RA-014")
    order = _make_order(db, patient, "014", status="cancelled")
    db.commit()

    res = client.put(
        f"/radiology/orders/{order.id}/status",
        headers=auth_headers(admin.id, lab.id, role="admin"),
        json={"status": "scheduled"},
    )
    assert res.status_code == 409

    db.expire_all()
    order_db = db.query(RadiologyOrder).filter(RadiologyOrder.id == order.id).first()
    assert order_db.status == "cancelled"


# ─── update_exam_status: role gate ──────────────────────────────────────────


def test_update_exam_status_requires_write_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Radiology Authz Lab 15")
    staff = make_lab_user(lab.id, role="staff")
    patient = _make_patient(db, lab.id, "H-RA-015")
    exam = _make_exam(db, patient, "015")
    db.commit()
    version_before = exam.version

    res = client.put(
        f"/radiology/exams/{exam.id}/status",
        headers={
            **auth_headers(staff.id, lab.id, role="staff"),
            "If-Match": str(version_before), "Idempotency-Key": "k-015",
        },
        json={"status": "checked_in"},
    )
    assert res.status_code == 403

    db.expire_all()
    exam_db = db.query(RadiologyExam).filter(RadiologyExam.id == exam.id).first()
    assert exam_db.status == ExamStatus.SCHEDULED
    assert exam_db.version == version_before
