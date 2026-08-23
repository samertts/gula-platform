from typing import Any

from app.models.audit_log import AuditLog
from app.models.lab_result import LabResult

from tests.conftest import auth_headers


def test_legacy_direct_device_result_ingress_is_quarantined(
    client: Any,
    db: Any,
    make_lab: Any,
    make_lab_user: Any,
) -> None:
    """A device payload must not create a clinical result or alter clinical state."""
    lab = make_lab("Direct Ingress Containment Lab")
    user = make_lab_user(lab.id, role="admin")

    response = client.post(
        "/device/results",
        headers=auth_headers(user.id, lab.id, "admin"),
        json={
            "barcode": "SYNTHETIC-SPECIMEN-001",
            "device_id": "SYNTHETIC-ANALYZER-001",
            "results": [
                {
                    "test_name": "GLUCOSE",
                    "value": 101.2,
                    "unit": "mg/dL",
                    "normal_range_low": 70.0,
                    "normal_range_high": 110.0,
                },
            ],
        },
    )

    assert response.status_code == 503
    assert isinstance(response.json()["detail"], str)
    assert db.query(LabResult).count() == 0

    audit = (
        db.query(AuditLog)
        .filter(
            AuditLog.lab_id == lab.id,
            AuditLog.action == "device_direct_ingestion_rejected",
        )
        .one()
    )
    assert audit.details == '{"reason":"legacy_direct_clinical_write_disabled"}'
    assert "SYNTHETIC-SPECIMEN-001" not in audit.details
    assert "SYNTHETIC-ANALYZER-001" not in audit.details


def test_legacy_direct_device_result_ingress_rejects_without_authenticated_user(
    client: Any,
) -> None:
    response = client.post(
        "/device/results",
        json={
            "barcode": "SYNTHETIC-SPECIMEN-001",
            "results": [],
        },
    )

    assert response.status_code == 401
