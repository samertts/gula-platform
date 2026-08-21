from app.models.patient import Patient
from app.radiology.enums import CriticalFindingStatus, ExamStatus, ModalityType, ReportStatus
from app.radiology.models import (
    CriticalFinding,
    DICOMStorage,
    DICOMStudy,
    RadiologyExam,
    RadiologyOrder,
    RadiologyReport,
)

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


def _make_order(db, patient: Patient, suffix: str) -> RadiologyOrder:
    order = RadiologyOrder(
        patient_id=str(patient.id),
        order_number=f"ORD-TENANT-{suffix}",
        modality=ModalityType.CT,
        status="pending",
    )
    db.add(order)
    db.flush()
    return order


def _make_exam(db, patient: Patient, suffix: str) -> RadiologyExam:
    exam = RadiologyExam(
        patient_id=str(patient.id),
        accession_number=f"ACC-TENANT-{suffix}",
        modality=ModalityType.CT,
        status=ExamStatus.SCHEDULED,
    )
    db.add(exam)
    db.flush()
    return exam


def _make_study(db, patient: Patient, suffix: str) -> DICOMStudy:
    study = DICOMStudy(
        study_instance_uid=f"STUDY-TENANT-{suffix}",
        patient_id=str(patient.id),
        modality=ModalityType.CT,
        study_description=f"Study {suffix}",
    )
    db.add(study)
    db.flush()
    return study


def _make_storage(db, patient: Patient, study: DICOMStudy, suffix: str) -> DICOMStorage:
    storage = DICOMStorage(
        sop_instance_uid=f"SOP-TENANT-{suffix}",
        study_instance_uid=study.study_instance_uid,
        series_instance_uid=f"SERIES-TENANT-{suffix}",
        patient_id=str(patient.id),
        modality=ModalityType.CT,
        file_path=f"/data/dicom/{suffix}.dcm",
    )
    db.add(storage)
    db.flush()
    return storage


def _make_finding(db, exam: RadiologyExam, suffix: str) -> CriticalFinding:
    finding = CriticalFinding(
        exam_id=exam.id,
        finding_type="critical",
        finding_description=f"Finding {suffix}",
        status=CriticalFindingStatus.PENDING,
    )
    db.add(finding)
    db.flush()
    return finding


def _make_report(db, patient: Patient, suffix: str) -> RadiologyReport:
    report = RadiologyReport(
        exam_id=f"EXAM-TENANT-{suffix}",
        accession_number=f"ACC-TENANT-{suffix}",
        patient_id=str(patient.id),
        status=ReportStatus.DRAFT,
    )
    db.add(report)
    db.flush()
    return report


def test_radiology_orders_are_scoped_to_current_lab(
    client,
    db,
    make_lab,
    make_lab_user,
):
    lab_one = make_lab("Tenant One")
    lab_two = make_lab("Tenant Two")
    user_one = make_lab_user(lab_one.id, role="admin")
    patient_one = _make_patient(db, lab_one.id, "H-ONE")
    patient_two = _make_patient(db, lab_two.id, "H-TWO")
    order_one = _make_order(db, patient_one, "ONE")
    _make_order(db, patient_two, "TWO")

    headers = auth_headers(user_one.id, lab_one.id)
    response = client.get("/radiology/orders", headers=headers)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [order_one.id]

    foreign = client.get(
        "/radiology/orders",
        params={"patient_id": str(patient_two.id)},
        headers=headers,
    )
    assert foreign.status_code == 404


def test_radiology_reports_are_scoped_to_current_lab(
    client,
    db,
    make_lab,
    make_lab_user,
):
    lab_one = make_lab("Report Tenant One")
    lab_two = make_lab("Report Tenant Two")
    user_one = make_lab_user(lab_one.id, role="admin")
    patient_one = _make_patient(db, lab_one.id, "R-ONE")
    patient_two = _make_patient(db, lab_two.id, "R-TWO")
    report_one = _make_report(db, patient_one, "ONE")
    _make_report(db, patient_two, "TWO")

    headers = auth_headers(user_one.id, lab_one.id)
    response = client.get("/radiology/reports", headers=headers)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [report_one.id]

    foreign = client.get(
        "/radiology/reports/search",
        params={"patient_id": str(patient_two.id)},
        headers=headers,
    )
    assert foreign.status_code == 404

    direct = client.get(f"/radiology/reports/{report_one.id}", headers=headers)
    assert direct.status_code == 200
    assert direct.json()["patient_id"] == str(patient_one.id)


def test_radiology_critical_findings_are_scoped_to_current_lab(
    client,
    db,
    make_lab,
    make_lab_user,
):
    lab_one = make_lab("Finding Tenant One")
    lab_two = make_lab("Finding Tenant Two")
    user_one = make_lab_user(lab_one.id, role="admin")
    patient_one = _make_patient(db, lab_one.id, "F-ONE")
    patient_two = _make_patient(db, lab_two.id, "F-TWO")
    exam_one = _make_exam(db, patient_one, "ONE")
    exam_two = _make_exam(db, patient_two, "TWO")
    finding_one = _make_finding(db, exam_one, "ONE")
    _make_finding(db, exam_two, "TWO")

    headers = auth_headers(user_one.id, lab_one.id)
    response = client.get("/radiology/critical-findings", headers=headers)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [finding_one.id]

    foreign_list = client.get(
        "/radiology/critical-findings",
        params={"exam_id": exam_two.id},
        headers=headers,
    )
    assert foreign_list.status_code == 404

    foreign_ack = client.put(
        f"/radiology/critical-findings/{_make_finding(db, exam_two, 'THREE').id}/acknowledge",
        json={"acknowledged_by": "user-1"},
        headers=headers,
    )
    assert foreign_ack.status_code == 404


def test_radiology_dashboard_analytics_are_scoped_to_current_lab(
    client,
    db,
    make_lab,
    make_lab_user,
):
    lab_one = make_lab("Analytics Tenant One")
    lab_two = make_lab("Analytics Tenant Two")
    user_one = make_lab_user(lab_one.id, role="admin")
    patient_one = _make_patient(db, lab_one.id, "A-ONE")
    patient_two = _make_patient(db, lab_two.id, "A-TWO")
    _make_exam(db, patient_one, "ANALYTICS-ONE")
    _make_exam(db, patient_two, "ANALYTICS-TWO")

    headers = auth_headers(user_one.id, lab_one.id)
    response = client.get(
        "/radiology/dashboard",
        params={
            "date_from": "2000-01-01T00:00:00+00:00",
            "date_to": "2100-01-01T00:00:00+00:00",
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["exam_volume"]["total"] == 1
    assert response.json()["exam_volume"]["by_modality"]["ct"] == 1


def test_radiology_pacs_and_citizen_images_are_scoped_to_current_lab(
    client,
    db,
    make_lab,
    make_lab_user,
):
    lab_one = make_lab("PACS Tenant One")
    lab_two = make_lab("PACS Tenant Two")
    user_one = make_lab_user(lab_one.id, role="admin")
    patient_one = _make_patient(db, lab_one.id, "P-ONE")
    patient_two = _make_patient(db, lab_two.id, "P-TWO")
    study_one = _make_study(db, patient_one, "ONE")
    study_two = _make_study(db, patient_two, "TWO")
    storage_one = _make_storage(db, patient_one, study_one, "ONE")
    storage_two = _make_storage(db, patient_two, study_two, "TWO")

    headers = auth_headers(user_one.id, lab_one.id)
    search = client.get("/radiology/studies/search", headers=headers)
    assert search.status_code == 200
    assert [item["study_instance_uid"] for item in search.json()["items"]] == [study_one.study_instance_uid]

    foreign_study = client.get(f"/radiology/studies/{study_two.study_instance_uid}", headers=headers)
    assert foreign_study.status_code == 404

    foreign_images = client.get(
        "/radiology/citizen/images",
        params={"patient_id": str(patient_two.id)},
        headers=headers,
    )
    assert foreign_images.status_code == 404

    foreign_download = client.get(
        f"/radiology/images/{storage_two.sop_instance_uid}/download",
        headers=headers,
    )
    assert foreign_download.status_code == 404

    foreign_share = client.post(
        "/radiology/citizen/share",
        json={"study_uid": study_two.study_instance_uid, "share_type": "link"},
        headers=headers,
    )
    assert foreign_share.status_code == 404

    own_download = client.get(
        f"/radiology/images/{storage_one.sop_instance_uid}/download",
        headers=headers,
    )
    assert own_download.status_code == 200
