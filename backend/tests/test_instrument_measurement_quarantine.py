from datetime import UTC, datetime
from typing import Any

import pytest
from app.devices.models import DeviceInboxMessage, InstrumentMeasurement
from app.devices.service import (
    DeviceIngressReplayError,
    DeviceIngressValidationError,
    activate_trusted_device_identity,
    quarantine_device_envelope,
    quarantine_instrument_measurement,
    register_trusted_device_identity,
)
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.models.patient import Patient
from app.models.sample import Sample


def _digest(character: str) -> str:
    return character * 64


def _quarantined_inbox(db: Any, lab_id: int, approver_id: int) -> DeviceInboxMessage:
    identity = register_trusted_device_identity(
        db,
        lab_id=lab_id,
        device_uid=f"ANALYZER-MEASUREMENT-{lab_id}",
        certificate_fingerprint=_digest("a"),
        protocol="ASTM",
    )
    activate_trusted_device_identity(
        db,
        lab_id=lab_id,
        device_uid=identity.device_uid,
        approver_user_id=approver_id,
    )
    return quarantine_device_envelope(
        db,
        lab_id=lab_id,
        device_uid=identity.device_uid,
        certificate_fingerprint=identity.certificate_fingerprint,
        message_id=f"measurement-message-{lab_id}",
        nonce_digest=_digest("b"),
        payload_digest=_digest("c"),
        protocol="ASTM",
        occurred_at=datetime.now(UTC),
        correlation_id=f"measurement-correlation-{lab_id}",
    ).message


def _sample_for_lab(db: Any, lab_id: int, *, status: str = "received") -> tuple[LabOrder, Sample]:
    patient = Patient(
        lab_id=lab_id,
        full_name="Synthetic Device Test Patient",
        phone=f"+964700000{lab_id:04d}",
    )
    db.add(patient)
    db.flush()
    order = LabOrder(lab_id=lab_id, patient_id=patient.id, status="pending")
    db.add(order)
    db.flush()
    sample = Sample(order_id=order.id, sample_type="blood", status=status)
    db.add(sample)
    db.flush()
    return order, sample


def test_quarantined_measurement_does_not_create_result_or_change_clinical_state(
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    lab = make_lab("Instrument Measurement Quarantine Lab")
    approver = make_lab_user(lab.id, role="admin")
    inbox = _quarantined_inbox(db, lab.id, approver.id)
    order, sample = _sample_for_lab(db, lab.id)

    measurement = quarantine_instrument_measurement(
        db,
        lab_id=lab.id,
        device_inbox_message_id=inbox.id,
        sample_id=sample.id,
        sequence_index=0,
        test_code="glucose",
        value=101.2,
        unit="mg/dl",
        captured_at=datetime.now(UTC),
        safe_metadata={"raw_payload_stored": False},
    )

    assert measurement.status == "quarantined"
    assert measurement.test_code == "GLUCOSE"
    assert measurement.unit == "MG/DL"
    assert db.query(InstrumentMeasurement).count() == 1
    assert db.query(LabResult).count() == 0
    assert sample.status == "received"
    assert order.status == "pending"


def test_measurement_is_idempotent_and_changed_sequence_is_rejected(
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    lab = make_lab("Instrument Measurement Replay Lab")
    approver = make_lab_user(lab.id, role="admin")
    inbox = _quarantined_inbox(db, lab.id, approver.id)
    _, sample = _sample_for_lab(db, lab.id)
    base = {
        "lab_id": lab.id,
        "device_inbox_message_id": inbox.id,
        "sample_id": sample.id,
        "sequence_index": 0,
        "test_code": "K",
        "value": 4.5,
        "unit": "mmol/l",
        "captured_at": datetime.now(UTC),
    }

    first = quarantine_instrument_measurement(db, **base)
    repeated = quarantine_instrument_measurement(db, **base)

    assert repeated.id == first.id
    assert db.query(InstrumentMeasurement).count() == 1

    with pytest.raises(DeviceIngressReplayError, match="sequence"):
        quarantine_instrument_measurement(
            db,
            **{**base, "value": 4.7},
        )


def test_measurement_rejects_other_lab_sample_and_rejected_sample(
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    lab = make_lab("Instrument Measurement Isolation Lab")
    other_lab = make_lab("Other Instrument Measurement Lab")
    approver = make_lab_user(lab.id, role="admin")
    inbox = _quarantined_inbox(db, lab.id, approver.id)
    _, other_sample = _sample_for_lab(db, other_lab.id)
    _, rejected_sample = _sample_for_lab(db, lab.id, status="rejected")
    base = {
        "lab_id": lab.id,
        "device_inbox_message_id": inbox.id,
        "sequence_index": 0,
        "test_code": "CRP",
        "value": 1.0,
        "unit": "mg/l",
        "captured_at": datetime.now(UTC),
    }

    with pytest.raises(LookupError, match="sample not found"):
        quarantine_instrument_measurement(db, **{**base, "sample_id": other_sample.id})
    with pytest.raises(DeviceIngressValidationError, match="rejected samples"):
        quarantine_instrument_measurement(db, **{**base, "sample_id": rejected_sample.id})
