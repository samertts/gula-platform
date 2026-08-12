from app.models.patient import Patient
from app.radiology.enums import ModalityType, ReportStatus
from app.radiology.models import RadiologyOrder, RadiologyReport
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
