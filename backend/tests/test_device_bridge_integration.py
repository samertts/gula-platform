from app.models.lab_order import LabOrder
from app.models.patient import Patient
from app.models.sample import Sample
from tests.conftest import auth_headers


def _create_device_fixture(db, lab_id: int, barcode: str) -> tuple[LabOrder, Sample]:
    patient = Patient(
        lab_id=lab_id,
        full_name="Synthetic Device Patient",
        phone="07700000001",
        health_id=f"DEVICE-{barcode}",
    )
    db.add(patient)
    db.flush()

    order = LabOrder(lab_id=lab_id, patient_id=patient.id, status="pending")
    db.add(order)
    db.flush()

    sample = Sample(
        order_id=order.id,
        sample_type="blood",
        barcode=barcode,
        status="collected",
    )
    db.add(sample)
    db.commit()
    db.refresh(order)
    db.refresh(sample)
    return order, sample


def test_device_bridge_payload_is_accepted_and_updates_clinical_state(
    client, db, make_lab, make_lab_user
):
    lab = make_lab("Device Bridge Contract Lab")
    user = make_lab_user(lab.id, role="admin")
    order, sample = _create_device_fixture(db, lab.id, "SAMPLE-DEVICE-001")

    response = client.post(
        "/device/results",
        headers=auth_headers(user.id, lab.id, "admin"),
        json={
            "barcode": sample.barcode,
            "device_id": "CBC-01",
            "results": [
                {"test_name": "HEMOGLOBIN", "value": 13.5, "unit": "g/dL"},
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["order_id"] == order.id
    assert response.json()["barcode"] == sample.barcode
    assert len(response.json()["results"]) == 1

    db.refresh(order)
    db.refresh(sample)
    assert order.status == "completed"
    assert sample.status == "analyzed"


def test_device_bridge_cannot_submit_to_another_lab_sample(
    client, db, make_lab, make_lab_user
):
    owner_lab = make_lab("Device Owner Lab")
    other_lab = make_lab("Device Other Lab")
    other_user = make_lab_user(other_lab.id, role="admin")
    order, sample = _create_device_fixture(db, owner_lab.id, "SAMPLE-DEVICE-TENANT-001")

    response = client.post(
        "/device/results",
        headers=auth_headers(other_user.id, other_lab.id, "admin"),
        json={
            "barcode": sample.barcode,
            "device_id": "CBC-CROSS-TENANT",
            "results": [{"test_name": "GLUCOSE", "value": 95.0, "unit": "mg/dL"}],
        },
    )

    assert response.status_code == 404
    db.refresh(order)
    db.refresh(sample)
    assert order.status == "pending"
    assert sample.status == "collected"
