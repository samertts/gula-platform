from datetime import UTC, datetime
from typing import Any

import pytest
from app.devices.models import DeviceInboxMessage
from app.devices.service import (
    DeviceIngressReplayError,
    DeviceIngressValidationError,
    activate_trusted_device_identity,
    quarantine_device_envelope,
    register_trusted_device_identity,
)
from app.models.lab_result import LabResult


def _digest(character: str) -> str:
    return character * 64


def test_trusted_identity_is_pending_and_disabled_until_explicit_activation(
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    lab = make_lab("Trusted Device Inbox Lab")
    approver = make_lab_user(lab.id, role="admin")
    identity = register_trusted_device_identity(
        db,
        lab_id=lab.id,
        device_uid="ANALYZER-TRUST-001",
        certificate_fingerprint=_digest("a"),
        protocol="ASTM",
        hmac_secret_ref="secret-manager://labs/1/device/1",
    )

    assert identity.status == "pending"
    assert identity.enabled is False

    with pytest.raises(PermissionError, match="not active"):
        quarantine_device_envelope(
            db,
            lab_id=lab.id,
            device_uid=identity.device_uid,
            certificate_fingerprint=identity.certificate_fingerprint,
            message_id="message-001",
            nonce_digest=_digest("b"),
            payload_digest=_digest("c"),
            protocol="ASTM",
            occurred_at=datetime.now(UTC),
            correlation_id="corr-device-001",
        )

    activate_trusted_device_identity(
        db,
        lab_id=lab.id,
        device_uid=identity.device_uid,
        approver_user_id=approver.id,
    )

    assert identity.status == "active"
    assert identity.enabled is True
    assert identity.approved_by == approver.id


def test_quarantined_envelope_is_idempotent_and_never_creates_clinical_result(
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    lab = make_lab("Device Inbox Idempotency Lab")
    approver = make_lab_user(lab.id, role="admin")
    identity = register_trusted_device_identity(
        db,
        lab_id=lab.id,
        device_uid="ANALYZER-TRUST-002",
        certificate_fingerprint=_digest("d"),
        protocol="HL7v2_MLLP",
    )
    activate_trusted_device_identity(
        db,
        lab_id=lab.id,
        device_uid=identity.device_uid,
        approver_user_id=approver.id,
    )

    envelope = {
        "lab_id": lab.id,
        "device_uid": identity.device_uid,
        "certificate_fingerprint": identity.certificate_fingerprint,
        "message_id": "message-002",
        "nonce_digest": _digest("e"),
        "payload_digest": _digest("f"),
        "protocol": "HL7v2_MLLP",
        "occurred_at": datetime.now(UTC),
        "correlation_id": "corr-device-002",
        "safe_metadata": {"transport": "mllp", "raw_payload_stored": False},
    }

    created = quarantine_device_envelope(db, **envelope)
    redelivery = quarantine_device_envelope(db, **envelope)

    assert created.created is True
    assert created.message.status == "quarantined"
    assert redelivery.created is False
    assert redelivery.message.id == created.message.id
    assert db.query(DeviceInboxMessage).count() == 1
    assert db.query(LabResult).count() == 0


def test_changed_message_or_reused_nonce_is_rejected_as_replay(
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    lab = make_lab("Device Inbox Replay Lab")
    approver = make_lab_user(lab.id, role="admin")
    identity = register_trusted_device_identity(
        db,
        lab_id=lab.id,
        device_uid="ANALYZER-TRUST-003",
        certificate_fingerprint=_digest("1"),
        protocol="ASTM",
    )
    activate_trusted_device_identity(
        db,
        lab_id=lab.id,
        device_uid=identity.device_uid,
        approver_user_id=approver.id,
    )
    base = {
        "lab_id": lab.id,
        "device_uid": identity.device_uid,
        "certificate_fingerprint": identity.certificate_fingerprint,
        "message_id": "message-003",
        "nonce_digest": _digest("2"),
        "payload_digest": _digest("3"),
        "protocol": "ASTM",
        "occurred_at": datetime.now(UTC),
        "correlation_id": "corr-device-003",
    }
    quarantine_device_envelope(db, **base)

    with pytest.raises(DeviceIngressReplayError, match="message_id"):
        quarantine_device_envelope(
            db,
            **{**base, "payload_digest": _digest("4")},
        )
    with pytest.raises(DeviceIngressReplayError, match="nonce"):
        quarantine_device_envelope(
            db,
            **{
                **base,
                "message_id": "message-004",
                "payload_digest": _digest("4"),
            },
        )


def test_device_identity_rejects_invalid_certificate_fingerprint(
    db: Any,
    make_lab: Any,
) -> None:
    lab = make_lab("Device Inbox Validation Lab")

    with pytest.raises(DeviceIngressValidationError, match="certificate_fingerprint"):
        register_trusted_device_identity(
            db,
            lab_id=lab.id,
            device_uid="ANALYZER-TRUST-004",
            certificate_fingerprint="not-a-sha256-digest",
            protocol="ASTM",
        )
