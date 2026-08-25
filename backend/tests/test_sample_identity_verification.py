from __future__ import annotations

from typing import Any

from app.models.audit_log import AuditLog
from app.models.clinical_command import ClinicalCommandReceipt
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.models.patient import Patient
from app.models.sample import Sample
from app.models.subscription import FeatureFlag

from tests.conftest import auth_headers

FEATURE_KEY = "sample_identity_verification"
METHOD = "manual_identity_container_match"


def _sample_pending_verification(db: Any, lab_id: int) -> tuple[LabOrder, Sample]:
    patient = Patient(
        lab_id=lab_id,
        full_name="Synthetic Verification Patient",
        phone=f"+964751000{lab_id:04d}",
    )
    db.add(patient)
    db.flush()
    order = LabOrder(lab_id=lab_id, patient_id=patient.id, status="pending")
    db.add(order)
    db.flush()
    sample = Sample(order_id=order.id, sample_type="blood", status="received")
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return order, sample


def _headers(user_id: int, lab_id: int, *, version: int, key: str) -> dict[str, str]:
    headers = {
        str(header): str(value)
        for header, value in auth_headers(user_id, lab_id, "lab_admin").items()
    }
    headers["If-Match"] = str(version)
    headers["Idempotency-Key"] = key
    return headers


def _enable_feature(db: Any, lab_id: int, user_id: int) -> None:
    db.add(
        FeatureFlag(
            lab_id=lab_id,
            feature_key=FEATURE_KEY,
            is_enabled=True,
            set_by=user_id,
            reason="synthetic-test-only",
        )
    )
    db.commit()


def test_sample_identity_verification_is_default_deny(
    client: Any,
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    lab = make_lab("Sample Verification Default Deny Lab")
    verifier = make_lab_user(lab.id, role="lab_admin")
    _, sample = _sample_pending_verification(db, lab.id)

    response = client.put(
        f"/samples/{sample.barcode}/verify-identity",
        json={"verification_method": METHOD},
        headers=_headers(verifier.id, lab.id, version=1, key="sample-verify-default-deny"),
    )

    assert response.status_code == 403
    db.refresh(sample)
    assert sample.status == "received"
    assert sample.version == 1
    assert sample.verified_by is None
    assert db.query(LabResult).count() == 0
    assert (
        db.query(AuditLog)
        .filter(AuditLog.action == "clinical.sample.identity.verify.rejected")
        .count()
        == 1
    )


def test_sample_identity_verification_records_guarded_human_decision_only(
    client: Any,
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    lab = make_lab("Sample Verification Guarded Lab")
    verifier = make_lab_user(lab.id, role="lab_admin")
    order, sample = _sample_pending_verification(db, lab.id)
    _enable_feature(db, lab.id, verifier.id)

    response = client.put(
        f"/samples/{sample.barcode}/verify-identity",
        json={"verification_method": METHOD},
        headers=_headers(verifier.id, lab.id, version=1, key="sample-verify-success"),
    )

    assert response.status_code == 200
    assert response.json()["sample"]["status"] == "verified"
    assert response.json()["sample"]["version"] == 2
    db.refresh(sample)
    db.refresh(order)
    assert sample.status == "verified"
    assert sample.version == 2
    assert sample.verified_by == verifier.id
    assert sample.verified_at is not None
    assert sample.verification_method == METHOD
    assert order.status == "pending"
    assert order.version == 1
    assert db.query(LabResult).count() == 0
    receipt = (
        db.query(ClinicalCommandReceipt)
        .filter(ClinicalCommandReceipt.operation == "sample.identity.verify")
        .one()
    )
    assert receipt.status == "completed"
    assert receipt.resource_id == str(sample.id)
    assert (
        db.query(AuditLog)
        .filter(AuditLog.action == "clinical.sample.identity.verify")
        .count()
        == 1
    )


def test_sample_identity_verification_rejects_stale_and_replayed_commands(
    client: Any,
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    lab = make_lab("Sample Verification Idempotency Lab")
    verifier = make_lab_user(lab.id, role="lab_admin")
    _, sample = _sample_pending_verification(db, lab.id)
    _enable_feature(db, lab.id, verifier.id)
    key = "sample-verify-single-effect"

    accepted = client.put(
        f"/samples/{sample.barcode}/verify-identity",
        json={"verification_method": METHOD},
        headers=_headers(verifier.id, lab.id, version=1, key=key),
    )
    stale = client.put(
        f"/samples/{sample.barcode}/verify-identity",
        json={"verification_method": METHOD},
        headers=_headers(verifier.id, lab.id, version=1, key="sample-verify-stale"),
    )
    replay = client.put(
        f"/samples/{sample.barcode}/verify-identity",
        json={"verification_method": METHOD},
        headers=_headers(verifier.id, lab.id, version=2, key=key),
    )

    assert accepted.status_code == 200
    assert stale.status_code == 409
    assert replay.status_code == 409
    db.refresh(sample)
    assert sample.status == "verified"
    assert sample.version == 2
    assert db.query(ClinicalCommandReceipt).count() == 1
    assert db.query(LabResult).count() == 0


def test_sample_identity_verification_rejects_non_received_or_locked_samples(
    client: Any,
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    lab = make_lab("Sample Verification State Guard Lab")
    verifier = make_lab_user(lab.id, role="lab_admin")
    order, sample = _sample_pending_verification(db, lab.id)
    _enable_feature(db, lab.id, verifier.id)
    sample.status = "rejected"
    sample.rejection_reason = "synthetic rejection"
    db.commit()

    rejected_sample = client.put(
        f"/samples/{sample.barcode}/verify-identity",
        json={"verification_method": METHOD},
        headers=_headers(verifier.id, lab.id, version=1, key="sample-verify-rejected"),
    )

    sample.status = "received"
    sample.version = 1
    order.locked_at = order.created_at
    db.commit()
    locked_order = client.put(
        f"/samples/{sample.barcode}/verify-identity",
        json={"verification_method": METHOD},
        headers=_headers(verifier.id, lab.id, version=1, key="sample-verify-locked"),
    )

    assert rejected_sample.status_code == 409
    assert locked_order.status_code == 409
    db.refresh(sample)
    assert sample.status == "received"
    assert sample.verified_at is None
    assert db.query(LabResult).count() == 0
