"""P0 regression tests for non-bypassable clinical command safety controls."""
from __future__ import annotations

import pytest
from app.clinical.command_guard import ClinicalCommandGuard
from app.models.clinical_command import ClinicalCommandReceipt
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.security.auth import hash_password
from fastapi import HTTPException


def _actor(db) -> LabUser:
    lab = Lab(
        name="P0 Safety Lab",
        license_number="LIC-P0-GUARD",
        lab_type="private",
        city="Baghdad",
        is_active=True,
    )
    db.add(lab)
    db.flush()
    actor = LabUser(
        lab_id=lab.id,
        name="Safety Admin",
        email="p0-safety-admin@example.test",
        password_hash=hash_password("Pa55word"),
        role="lab_admin",
        is_active=True,
    )
    db.add(actor)
    db.flush()
    return actor


def test_clinical_command_requires_both_transport_guards():
    with pytest.raises(HTTPException) as missing_key:
        ClinicalCommandGuard.require_idempotency_key(None)
    assert missing_key.value.status_code == 400

    with pytest.raises(HTTPException) as missing_version:
        ClinicalCommandGuard.require_expected_version(None, current_version=1, resource_name="result")
    assert missing_version.value.status_code == 428

    with pytest.raises(HTTPException) as stale_version:
        ClinicalCommandGuard.require_expected_version("2", current_version=1, resource_name="result")
    assert stale_version.value.status_code == 409


def test_duplicate_clinical_command_never_repeats_side_effect(db):
    actor = _actor(db)
    guard = ClinicalCommandGuard(
        db,
        actor_user_id=actor.id,
        lab_id=actor.lab_id,
        actor_role=actor.role,
    )
    receipt = guard.claim(
        operation="result.validate",
        resource_type="lims_result",
        resource_id=42,
        idempotency_key="p0-unique-key",
        payload={"action": "validate", "signature_hash": "signature"},
    )
    guard.complete(
        receipt,
        resource_type="lims_result",
        resource_id=42,
        state_before="pending",
        state_after="validated",
        version_before=1,
        version_after=2,
    )
    db.commit()

    stored = db.query(ClinicalCommandReceipt).one()
    assert stored.status == "completed"
    assert stored.resource_id == 42

    with pytest.raises(HTTPException) as replay:
        guard.claim(
            operation="result.validate",
            resource_type="lims_result",
            resource_id=42,
            idempotency_key="p0-unique-key",
            payload={"action": "validate", "signature_hash": "signature"},
        )
    assert replay.value.status_code == 409
    assert db.query(ClinicalCommandReceipt).count() == 1


def test_public_phone_history_is_disabled_by_default(client):
    response = client.get("/history/07700000000?name=Example%20Patient")
    assert response.status_code == 410
    # The central error contract intentionally redacts route-specific details;
    # the 410 response itself is the non-bypassable privacy enforcement gate.
    assert response.json()["code"] == "HTTP_ERROR"


def test_result_service_requires_signature_and_validated_state():
    from app.lims.models import Result
    from app.lims.services import ResultService

    result = Result(validation_status="pending", version=1)
    with pytest.raises(ValueError, match="signature"):
        ResultService.validate_manually(None, result, user_id=1)

    result.validation_status = "pending"
    with pytest.raises(ValueError, match="validated"):
        ResultService.release(None, result, user_id=1)
