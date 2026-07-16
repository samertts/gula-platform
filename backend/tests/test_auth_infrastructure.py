from __future__ import annotations

import json
import re

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.lab_user import LabUser
from shared.auth.passwords import hash_password

client = TestClient(app)


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(LabUser).filter(LabUser.email == "test@mfa.gula").first()
        if not user:
            user = LabUser(
                lab_id=1, email="test@mfa.gula", name="Test User",
                password_hash=hash_password("password123"),
                role="admin", is_active=True,
            )
            db.add(user)
            db.commit()
        yield
    finally:
        db.close()


@pytest.fixture
def token():
    resp = client.post("/login", data={"username": "test@mfa.gula", "password": "password123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


_AUTH_HEADER = {"Authorization": "Bearer {}"}


# ── MFA: TOTP ──


def test_totp_setup(token):
    resp = client.post(
        "/mfa/totp/setup",
        json={"device_name": "Test Authenticator"},
        headers=_AUTH_HEADER.format(token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "secret" in data
    assert "uri" in data
    assert "backup_codes" in data
    assert len(data["backup_codes"]) > 0
    assert data["uri"].startswith("otpauth://")


def test_totp_verify_invalid(token):
    resp = client.post(
        "/mfa/totp/verify",
        json={"token": "000000"},
        headers=_AUTH_HEADER.format(token),
    )
    assert resp.status_code == 400


def test_totp_setup_twice_updates_device(token):
    resp1 = client.post(
        "/mfa/totp/setup",
        json={"device_name": "App1"},
        headers=_AUTH_HEADER.format(token),
    )
    resp2 = client.post(
        "/mfa/totp/setup",
        json={"device_name": "App2"},
        headers=_AUTH_HEADER.format(token),
    )
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["device_id"] != resp2.json()["device_id"]


# ── MFA: Device Management ──


def test_list_devices_empty_before_setup(token):
    resp = client.get("/mfa/devices", headers=_AUTH_HEADER.format(token))
    assert resp.status_code == 200
    assert resp.json()["mfa_enabled"] is False


def test_list_devices_after_totp_setup(token):
    client.post("/mfa/totp/setup", json={}, headers=_AUTH_HEADER.format(token))
    resp = client.get("/mfa/devices", headers=_AUTH_HEADER.format(token))
    assert resp.status_code == 200
    assert resp.json()["mfa_enabled"] is True
    assert len(resp.json()["devices"]) >= 1


def test_remove_device(token):
    setup = client.post("/mfa/totp/setup", json={}, headers=_AUTH_HEADER.format(token))
    dev_id = setup.json()["device_id"]
    resp = client.delete(f"/mfa/devices/{dev_id}", headers=_AUTH_HEADER.format(token))
    assert resp.status_code == 200
    resp2 = client.get("/mfa/devices", headers=_AUTH_HEADER.format(token))
    assert all(d["id"] != dev_id for d in resp2.json()["devices"])


def test_remove_nonexistent_device_returns_404(token):
    resp = client.delete("/mfa/devices/99999", headers=_AUTH_HEADER.format(token))
    assert resp.status_code == 404


# ── MFA: Status ──


def test_mfa_status_no_device(token):
    resp = client.get("/mfa/status", headers=_AUTH_HEADER.format(token))
    assert resp.status_code == 200
    assert resp.json()["mfa_enabled"] is False


def test_mfa_status_with_device(token):
    client.post("/mfa/totp/setup", json={}, headers=_AUTH_HEADER.format(token))
    resp = client.get("/mfa/status", headers=_AUTH_HEADER.format(token))
    assert resp.status_code == 200
    assert resp.json()["mfa_enabled"] is True


# ── WebAuthn ──


def test_webauthn_register_begin(token):
    resp = client.post(
        "/mfa/webauthn/register/begin",
        headers=_AUTH_HEADER.format(token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "options" in data
    assert "rp" in data["options"] or "publicKey" in data["options"]


def test_webauthn_authenticate_begin_no_device(token):
    resp = client.post(
        "/mfa/webauthn/authenticate/begin",
        headers=_AUTH_HEADER.format(token),
    )
    assert resp.status_code == 200, resp.text


# ── Password Reset ──


def test_forgot_password_unknown_email(token):
    resp = client.post(
        "/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
        headers=_AUTH_HEADER.format(token),
    )
    assert resp.status_code == 200
    assert "message" in resp.json()


def test_forgot_password_known_email(token):
    resp = client.post(
        "/auth/forgot-password",
        json={"email": "test@mfa.gula"},
        headers=_AUTH_HEADER.format(token),
    )
    assert resp.status_code == 200


def test_reset_password_invalid_token(token):
    resp = client.post(
        "/auth/reset-password",
        json={"token": "invalid-token", "new_password": "NewPass123!"},
        headers=_AUTH_HEADER.format(token),
    )
    assert resp.status_code == 400


def test_change_password_wrong_current(token):
    resp = client.post(
        "/auth/change-password",
        json={"current_password": "wrongpassword", "new_password": "NewPass123!"},
        headers=_AUTH_HEADER.format(token),
    )
    assert resp.status_code == 400


def test_change_password_success(token):
    resp = client.post(
        "/auth/change-password",
        json={"current_password": "password123", "new_password": "NewPass123!"},
        headers=_AUTH_HEADER.format(token),
    )
    assert resp.status_code == 200


# ── OAuth2 Client Credentials ──


def test_oauth2_token_endpoint_no_auth():
    resp = client.post("/oauth2/token", data={})
    assert resp.status_code in (400, 401)


def test_oauth2_discovery():
    resp = client.get("/oauth2/.well-known/openid-configuration")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "issuer" in data
    assert "authorization_endpoint" in data
    assert "token_endpoint" in data
    assert "jwks_uri" in data


def test_oauth2_jwks():
    resp = client.get("/oauth2/jwks.json")
    assert resp.status_code == 200
    assert "keys" in resp.json()


# ── SAML ──


def test_saml_metadata():
    resp = client.get("/auth/saml/metadata")
    assert resp.status_code == 200
    assert "EntityDescriptor" in resp.text or resp.headers.get("content-type", "").startswith(
        "application/xml"
    ) or resp.headers.get("content-type", "").startswith("text/xml")


# ── Service Accounts ──


def test_create_service_account(token):
    resp = client.post(
        "/service-accounts",
        json={"name": "test-sa", "description": "Test", "roles": ["admin"], "scopes": ["patients:read"]},
        headers=_AUTH_HEADER.format(token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "api_key" in data
    assert data["api_key"].startswith("gula_")
    assert data["name"] == "test-sa"


def test_list_service_accounts(token):
    resp = client.get("/service-accounts", headers=_AUTH_HEADER.format(token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_rotate_api_key(token):
    create = client.post(
        "/service-accounts",
        json={"name": "rotate-sa", "description": "Rotate Test", "roles": ["viewer"], "scopes": ["patients:read"]},
        headers=_AUTH_HEADER.format(token),
    )
    sa_id = create.json()["id"]
    resp = client.post(f"/service-accounts/{sa_id}/rotate", headers=_AUTH_HEADER.format(token))
    assert resp.status_code == 200, resp.text
    assert "api_key" in resp.json()


def test_delete_service_account(token):
    create = client.post(
        "/service-accounts",
        json={"name": "delete-sa", "description": "Delete Test", "roles": ["viewer"], "scopes": ["patients:read"]},
        headers=_AUTH_HEADER.format(token),
    )
    sa_id = create.json()["id"]
    resp = client.delete(f"/service-accounts/{sa_id}", headers=_AUTH_HEADER.format(token))
    assert resp.status_code == 200


# ── Canonical Patient ──


def test_create_canonical_patient(token):
    resp = client.post(
        "/api/v1/canonical-patients",
        json={
            "full_name": "Test Citizen",
            "full_name_ar": "مواطن اختبار",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "phone": "+9647700000000",
        },
        headers=_AUTH_HEADER.format(token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["full_name"] == "Test Citizen"
    assert "id" in data


def test_get_canonical_patient(token):
    create = client.post(
        "/api/v1/canonical-patients",
        json={"full_name": "Get Test", "date_of_birth": "1990-01-01", "gender": "female"},
        headers=_AUTH_HEADER.format(token),
    )
    pid = create.json()["id"]
    resp = client.get(f"/api/v1/canonical-patients/{pid}", headers=_AUTH_HEADER.format(token))
    assert resp.status_code == 200
    assert resp.json()["id"] == pid


def test_search_canonical_patients(token):
    client.post(
        "/api/v1/canonical-patients",
        json={"full_name": "Searchable Person", "date_of_birth": "1985-05-05", "gender": "male"},
        headers=_AUTH_HEADER.format(token),
    )
    resp = client.get(
        "/api/v1/canonical-patients/search?q=Searchable",
        headers=_AUTH_HEADER.format(token),
    )
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    assert any("Searchable" in i.get("full_name", "") for i in items)


def test_merge_canonical_patients(token):
    a = client.post(
        "/api/v1/canonical-patients",
        json={"full_name": "Merge A", "date_of_birth": "1980-01-01", "gender": "male"},
        headers=_AUTH_HEADER.format(token),
    ).json()
    b = client.post(
        "/api/v1/canonical-patients",
        json={"full_name": "Merge B", "date_of_birth": "1980-01-01", "gender": "male"},
        headers=_AUTH_HEADER.format(token),
    ).json()
    resp = client.post(
        "/api/v1/canonical-patients/merge",
        json={"target_id": a["id"], "source_id": b["id"]},
        headers=_AUTH_HEADER.format(token),
    )
    assert resp.status_code == 200, resp.text


# ── Auth required on protected endpoints ──


def test_mfa_endpoints_require_auth():
    for path in ["/mfa/status", "/mfa/devices", "/mfa/totp/setup", "/mfa/webauthn/register/begin"]:
        resp = client.get(path) if path in ("/mfa/status", "/mfa/devices") else client.post(path, json={})
        assert resp.status_code == 401, f"{path} returned {resp.status_code}"


def test_password_reset_endpoints_require_auth():
    resp = client.post("/auth/change-password", json={"current_password": "x", "new_password": "y"})
    assert resp.status_code == 401
