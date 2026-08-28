from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.identity.models import Account, IdentityRecord, Person
from fastapi.testclient import TestClient


def _headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key, "X-Request-ID": f"req-{key}"}


def _synthetic_grantee(db):
    person = Person(id=f"GRANTEE-PERSON-{uuid4().hex[:10]}", uuid=str(uuid4()), given_name="Synthetic", family_name="Reviewer", full_name_ar="مراجع اصطناعي", is_active=True)
    identity = IdentityRecord(id=f"GRANTEE-IDENTITY-{uuid4().hex[:9]}", uuid=str(uuid4()), person_id=person.id, identity_type="citizen", status="active", issued_at=datetime.now(UTC), is_active=True)
    account = Account(id=f"GRANTEE-ACCOUNT-{uuid4().hex[:9]}", uuid=str(uuid4()), identity_id=identity.id, status="active", is_active=True, is_locked=False, email=f"grantee-{uuid4().hex}@example.test")
    db.add_all([person, identity, account])
    db.flush()
    return account


def test_health_identity_synthetic_verification_issue_device_consent_recovery(client: TestClient, appointment_context: dict[str, object]):
    grantee = _synthetic_grantee(appointment_context["db"])
    initial = client.get("/api/v1/identity/health/status")
    assert initial.status_code == 200, initial.text
    assert initial.json()["health_id_issued"] is False

    requested = client.post("/api/v1/identity/health/verifications", headers=_headers("verify-request"), json={"method": "SYNTHETIC", "purpose": "Synthetic account verification"})
    assert requested.status_code == 201, requested.text
    operation_id = requested.json()["operation_id"]
    completed = client.post("/api/v1/identity/health/verifications/complete", headers=_headers("verify-complete"), json={"operation_id": operation_id, "proof": "SYNTHETIC-VERIFIED", "verified_attributes": {"name_match": True, "national_id": "must-not-persist"}})
    assert completed.status_code == 200, completed.text
    assert completed.json()["assurance_level"] == "L1"

    issued = client.post("/api/v1/identity/health/issue", headers=_headers("health-id-issue"), json={"verification_operation_id": operation_id})
    assert issued.status_code == 200, issued.text
    assert issued.json()["health_id"].startswith("GULA-SYN-")
    status = client.get("/api/v1/identity/health/status")
    assert status.json()["health_id_issued"] is True

    registered = client.post("/api/v1/identity/devices", headers=_headers("device-register"), json={"device_fingerprint": "synthetic-fingerprint-00000001", "device_name": "Synthetic Browser", "device_type": "web"})
    assert registered.status_code == 201, registered.text
    device_id = registered.json()["id"]
    trusted = client.post("/api/v1/identity/devices/trust", headers=_headers("device-trust"), json={"device_id": device_id, "verification_operation_id": operation_id})
    assert trusted.status_code == 200, trusted.text
    assert trusted.json()["trusted"] is True

    expires_at = (datetime.now(UTC) + timedelta(hours=24)).isoformat()
    consent = client.post("/api/v1/identity/consents", headers=_headers("consent-grant"), json={"grantee_account_id": grantee.id, "purpose": "synthetic review", "resource_domain": "clinical_record", "scope": {"sections": ["summary"]}, "expires_at": expires_at, "reason": "Synthetic test"})
    assert consent.status_code == 201, consent.text
    consent_id = consent.json()["id"]
    revoked = client.post("/api/v1/identity/consents/revoke", headers=_headers("consent-revoke"), json={"consent_id": consent_id, "reason": "Synthetic revoke"})
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["status"] == "REVOKED"

    recovery = client.post("/api/v1/identity/recovery", headers=_headers("recovery-request"), json={"purpose": "Synthetic recovery test"})
    assert recovery.status_code == 201, recovery.text
    recovery_done = client.post("/api/v1/identity/recovery/complete", headers=_headers("recovery-complete"), json={"operation_id": recovery.json()["operation_id"], "proof": "SYNTHETIC-RECOVERY-VERIFIED"})
    assert recovery_done.status_code == 200, recovery_done.text
    assert recovery_done.json()["status"] == "COMPLETED"


def test_health_identity_disconnected_verification_never_asserts_success(client: TestClient, appointment_context: dict[str, object]):
    requested = client.post("/api/v1/identity/health/verifications", headers=_headers("verify-ocr-request"), json={"method": "OCR", "purpose": "Synthetic OCR test"})
    assert requested.status_code == 201, requested.text
    response = client.post("/api/v1/identity/health/verifications/complete", headers=_headers("verify-ocr-complete"), json={"operation_id": requested.json()["operation_id"], "proof": "SYNTHETIC-VERIFIED"})
    assert response.status_code == 503, response.text
    assert response.json()["code"] == "VERIFICATION_PROVIDER_UNAVAILABLE"


def test_health_identity_rejects_self_consent(client: TestClient, appointment_context: dict[str, object]):
    response = client.post("/api/v1/identity/consents", headers=_headers("consent-self"), json={"grantee_account_id": appointment_context["account"].id, "purpose": "self", "resource_domain": "clinical_record", "scope": {"sections": ["summary"]}, "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat()})
    assert response.status_code == 422
    assert response.json()["code"] == "CONSENT_SELF_GRANT"


def test_health_identity_rejects_public_consent_scope(client: TestClient, appointment_context: dict[str, object]):
    response = client.post("/api/v1/identity/consents", headers=_headers("consent-public"), json={"grantee_account_id": appointment_context["account"].id, "purpose": "bad", "resource_domain": "clinical_record", "scope": {"public": True}, "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat()})
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
