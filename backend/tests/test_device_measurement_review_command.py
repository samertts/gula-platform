from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.devices.models import InstrumentMeasurement
from app.devices.service import (
    activate_trusted_device_identity,
    quarantine_device_envelope,
    quarantine_instrument_measurement,
    register_trusted_device_identity,
)
from app.models.audit_log import AuditLog
from app.models.clinical_command import ClinicalCommandReceipt
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.models.patient import Patient
from app.models.sample import Sample
from app.models.subscription import FeatureFlag

from tests.conftest import auth_headers


def _digest(character: str) -> str:
    return character * 64


def _reviewable_measurement(db: Any, lab_id: int, approver_id: int) -> InstrumentMeasurement:
    identity = register_trusted_device_identity(
        db,
        lab_id=lab_id,
        device_uid=f"REVIEW-ANALYZER-{lab_id}",
        certificate_fingerprint=_digest("a"),
        protocol="ASTM",
    )
    activate_trusted_device_identity(
        db,
        lab_id=lab_id,
        device_uid=identity.device_uid,
        approver_user_id=approver_id,
    )
    inbox = quarantine_device_envelope(
        db,
        lab_id=lab_id,
        device_uid=identity.device_uid,
        certificate_fingerprint=identity.certificate_fingerprint,
        message_id=f"review-message-{lab_id}",
        nonce_digest=_digest("b"),
        payload_digest=_digest("c"),
        protocol="ASTM",
        occurred_at=datetime.now(UTC),
        correlation_id=f"review-correlation-{lab_id}",
    ).message
    patient = Patient(
        lab_id=lab_id,
        full_name="Synthetic Review Patient",
        phone=f"+964711000{lab_id:04d}",
    )
    db.add(patient)
    db.flush()
    order = LabOrder(lab_id=lab_id, patient_id=patient.id, status="pending")
    db.add(order)
    db.flush()
    sample = Sample(order_id=order.id, sample_type="blood", status="received")
    db.add(sample)
    db.flush()
    return quarantine_instrument_measurement(
        db,
        lab_id=lab_id,
        device_inbox_message_id=inbox.id,
        sample_id=sample.id,
        sequence_index=0,
        test_code="glucose",
        value=101.2,
        unit="mg/dl",
        captured_at=datetime.now(UTC),
    )


def _review_headers(user_id: int, lab_id: int, *, key: str, version: int = 1) -> dict[str, str]:
    headers = {
        str(header): str(value)
        for header, value in auth_headers(user_id, lab_id, "lab_admin").items()
    }
    headers["If-Match"] = str(version)
    headers["Idempotency-Key"] = key
    return headers


def test_measurement_review_is_default_deny_until_explicit_flag_enabled(
    client: Any,
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    lab = make_lab("Device Review Default Deny Lab")
    reviewer = make_lab_user(lab.id, role="lab_admin")
    measurement = _reviewable_measurement(db, lab.id, reviewer.id)

    response = client.put(
        f"/device-integration/measurements/{measurement.id}/review",
        json={"target_status": "pending_review"},
        headers=_review_headers(reviewer.id, lab.id, key="device-review-default-deny"),
    )

    assert response.status_code == 403
    db.refresh(measurement)
    assert measurement.status == "quarantined"
    assert measurement.version == 1


def test_authorized_review_uses_guard_and_never_creates_lab_result(
    client: Any,
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    lab = make_lab("Device Review Enabled Lab")
    reviewer = make_lab_user(lab.id, role="lab_admin")
    db.add(
        FeatureFlag(
            lab_id=lab.id,
            feature_key="device_quarantine_review",
            is_enabled=True,
            set_by=reviewer.id,
            reason="synthetic review command test",
        )
    )
    db.flush()
    measurement = _reviewable_measurement(db, lab.id, reviewer.id)
    headers = _review_headers(reviewer.id, lab.id, key="device-review-enabled")

    response = client.put(
        f"/device-integration/measurements/{measurement.id}/review",
        json={"target_status": "pending_review"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pending_review"
    assert response.json()["version"] == 2
    assert response.json()["reviewed_by"] == reviewer.id
    assert db.query(LabResult).count() == 0
    receipt = (
        db.query(ClinicalCommandReceipt)
        .filter(ClinicalCommandReceipt.operation == "device_measurement.review")
        .one()
    )
    assert receipt.status == "completed"
    audit = db.query(AuditLog).filter(AuditLog.action == "clinical.device_measurement.review").one()
    assert audit.user_id == reviewer.id
    assert audit.lab_id == lab.id

    repeated = client.put(
        f"/device-integration/measurements/{measurement.id}/review",
        json={"target_status": "pending_review"},
        headers=headers,
    )
    assert repeated.status_code == 409

    rejected = client.put(
        f"/device-integration/measurements/{measurement.id}/review",
        json={"target_status": "rejected", "rejection_code": "quality_control"},
        headers=_review_headers(
            reviewer.id,
            lab.id,
            key="device-review-authorized-rejection",
            version=2,
        ),
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["rejection_code"] == "quality_control"
    assert db.query(LabResult).count() == 0


def test_review_requires_if_match_and_rejects_stale_version(
    client: Any,
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    lab = make_lab("Device Review Version Lab")
    reviewer = make_lab_user(lab.id, role="lab_admin")
    db.add(FeatureFlag(lab_id=lab.id, feature_key="device_quarantine_review", is_enabled=True))
    db.flush()
    measurement = _reviewable_measurement(db, lab.id, reviewer.id)
    base_headers = auth_headers(reviewer.id, lab.id, "lab_admin")

    missing = client.put(
        f"/device-integration/measurements/{measurement.id}/review",
        json={"target_status": "pending_review"},
        headers={**base_headers, "Idempotency-Key": "device-review-missing-if-match"},
    )
    assert missing.status_code == 428

    stale = client.put(
        f"/device-integration/measurements/{measurement.id}/review",
        json={"target_status": "pending_review"},
        headers={
            **base_headers,
            "If-Match": "2",
            "Idempotency-Key": "device-review-stale-version",
        },
    )
    assert stale.status_code == 409
    db.refresh(measurement)
    assert measurement.status == "quarantined"
    assert measurement.version == 1


def test_rejection_requires_reason_code_and_keeps_measurement_non_clinical(
    client: Any,
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    lab = make_lab("Device Review Rejection Lab")
    reviewer = make_lab_user(lab.id, role="lab_admin")
    db.add(FeatureFlag(lab_id=lab.id, feature_key="device_quarantine_review", is_enabled=True))
    db.flush()
    measurement = _reviewable_measurement(db, lab.id, reviewer.id)

    missing_reason = client.put(
        f"/device-integration/measurements/{measurement.id}/review",
        json={"target_status": "rejected"},
        headers=_review_headers(reviewer.id, lab.id, key="device-review-missing-reason"),
    )
    assert missing_reason.status_code == 422
