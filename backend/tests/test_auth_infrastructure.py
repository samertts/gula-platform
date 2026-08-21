from __future__ import annotations

import json
import re

import pyotp
import pytest
from fastapi.testclient import TestClient

from shared.auth.passwords import hash_password


@pytest.fixture(autouse=True)
def _setup_db(db):
    from app.models.lab import Lab
    from app.models.lab_user import LabUser

    lab = db.query(Lab).filter(Lab.id == 1).first()
    if not lab:
        lab = Lab(id=1, name="Test Lab", license_number="LIC-0001", lab_type="private", city="Baghdad", is_active=True)
        db.add(lab)
        db.flush()
    user = db.query(LabUser).filter(LabUser.email == "test@mfa.gula").first()
    if not user:
        user = LabUser(
            lab_id=lab.id, email="test@mfa.gula", name="Test User",
            password_hash=hash_password("password123"),
            role="admin", is_active=True,
        )
        db.add(user)
        db.commit()


@pytest.fixture
def token(client):
    resp = client.post("/login", json={"email": "test@mfa.gula", "password": "password123"})
    assert resp.status_code == 200, resp.text
    token = resp.cookies.get("access_token")
    assert token
    return token


_AUTH_HEADER_TEMPLATE = "Bearer {}"


# ── MFA: TOTP ──


def test_totp_setup(client, token):
    resp = client.post(
        "/mfa/totp/setup",
        json={"device_name": "Test Authenticator"},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "secret" in data
    assert "uri" in data
    assert "backup_codes" in data
    assert len(data["backup_codes"]) > 0
    assert data["uri"].startswith("otpauth://")


def test_totp_verify_invalid(client, token):
    resp = client.post(
        "/mfa/totp/verify",
        json={"token": "000000"},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code == 400


def test_totp_setup_twice_updates_device(client, token):
    resp1 = client.post(
        "/mfa/totp/setup",
        json={"device_name": "App1"},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    resp2 = client.post(
        "/mfa/totp/setup",
        json={"device_name": "App2"},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["device_id"] != resp2.json()["device_id"]


# ── MFA: Device Management ──


def test_list_devices_empty_before_setup(client, token):
    resp = client.get("/mfa/devices", headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)})
    assert resp.status_code == 200
    assert resp.json()["mfa_enabled"] is False


def test_list_devices_after_totp_setup(client, token):
    client.post("/mfa/totp/setup", json={}, headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)})
    resp = client.get("/mfa/devices", headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)})
    assert resp.status_code == 200
    assert resp.json()["mfa_enabled"] is True
    assert len(resp.json()["devices"]) >= 1


def test_remove_device_requires_recent_mfa_step_up(client, token):
    setup = client.post("/mfa/totp/setup", json={}, headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)})
    dev_id = setup.json()["device_id"]
    denied = client.request(
        "DELETE",
        f"/mfa/devices/{dev_id}",
        json={},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert denied.status_code in (403, 422)

    verified = client.post(
        "/mfa/totp/verify",
        json={"token": pyotp.TOTP(setup.json()["secret"]).now()},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert verified.status_code == 200, verified.text
    step_up = verified.json()["mfa_session_token"]
    resp = client.request(
        "DELETE",
        f"/mfa/devices/{dev_id}",
        json={"session_token": step_up},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code == 200
    resp2 = client.get("/mfa/devices", headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)})
    assert resp2.status_code == 401


def test_remove_nonexistent_device_requires_step_up(client, token):
    resp = client.request(
        "DELETE",
        "/mfa/devices/99999",
        json={},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code in (403, 404, 422)


# ── MFA: Status ──


def test_mfa_status_no_device(client, token):
    resp = client.get("/mfa/status", headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)})
    assert resp.status_code == 200
    assert resp.json()["mfa_enabled"] is False


def test_mfa_status_with_device(client, token):
    client.post("/mfa/totp/setup", json={}, headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)})
    resp = client.get("/mfa/status", headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)})
    assert resp.status_code == 200
    assert resp.json()["mfa_enabled"] is True


# ── WebAuthn ──


def test_webauthn_register_begin(client, token):
    resp = client.post(
        "/mfa/webauthn/register/begin",
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "options" in data
    assert "rp" in data["options"] or "publicKey" in data["options"]


def test_webauthn_authenticate_begin_no_device(client, token):
    resp = client.post(
        "/mfa/webauthn/authenticate/begin",
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code == 200, resp.text


# ── Password Reset ──


def test_forgot_password_unknown_email(client, token):
    resp = client.post(
        "/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code == 200
    assert "message" in resp.json()


def test_forgot_password_known_email(client, token):
    resp = client.post(
        "/auth/forgot-password",
        json={"email": "test@mfa.gula"},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code == 200


def test_reset_password_invalid_token(client, token):
    resp = client.post(
        "/auth/reset-password",
        json={"token": "invalid-token", "new_password": "NewPass123!"},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code == 400


def test_change_password_wrong_current(client, token):
    resp = client.post(
        "/auth/change-password",
        json={"current_password": "wrongpassword", "new_password": "NewPass123!"},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code == 400


def test_change_password_success(client, token):
    resp = client.post(
        "/auth/change-password",
        json={"current_password": "password123", "new_password": "NewPass123!"},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code == 200


# ── OAuth2 Client Credentials ──


def test_oauth2_token_endpoint_no_auth(client):
    resp = client.post("/oauth2/token", data={})
    # Returns 422 when no auth is provided (Pydantic validation catches empty form)
    assert resp.status_code in (400, 401, 422)


def test_oauth2_discovery(client):
    resp = client.get("/oauth2/.well-known/openid-configuration")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "issuer" in data
    assert "authorization_endpoint" in data
    assert "token_endpoint" in data
    assert "jwks_uri" in data


def test_oauth2_jwks(client):
    resp = client.get("/oauth2/jwks.json")
    assert resp.status_code == 200
    assert "keys" in resp.json()


# ── SAML ──


def test_saml_metadata(client):
    resp = client.get("/auth/saml/metadata")
    assert resp.status_code == 200
    assert "EntityDescriptor" in resp.text or resp.headers.get("content-type", "").startswith(
        "application/xml"
    ) or resp.headers.get("content-type", "").startswith("text/xml")


# ── Service Accounts ──


def test_create_service_account(client, token):
    resp = client.post(
        "/service-accounts",
        json={"name": "test-sa", "description": "Test", "roles": ["admin"], "scopes": ["patients:read"]},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "api_key" in data
    assert data["api_key"].startswith("gula_")
    assert data["name"] == "test-sa"


def test_list_service_accounts(client, token):
    resp = client.get("/service-accounts", headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_rotate_api_key(client, token):
    create = client.post(
        "/service-accounts",
        json={"name": "rotate-sa", "description": "Rotate Test", "roles": ["viewer"], "scopes": ["patients:read"]},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    sa_id = create.json()["id"]
    resp = client.post(f"/service-accounts/{sa_id}/rotate", headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)})
    assert resp.status_code == 200, resp.text
    assert "api_key" in resp.json()


def test_delete_service_account(client, token):
    create = client.post(
        "/service-accounts",
        json={"name": "delete-sa", "description": "Delete Test", "roles": ["viewer"], "scopes": ["patients:read"]},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    sa_id = create.json()["id"]
    resp = client.delete(f"/service-accounts/{sa_id}", headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)})
    assert resp.status_code == 200


# ── Canonical Patient ──


def test_create_canonical_patient(client, token):
    resp = client.post(
        "/api/v1/canonical-patients",
        json={
            "full_name": "Test Citizen",
            "full_name_ar": "مواطن اختبار",
            "date_of_birth": "1990-01-01",
            "gender": "M",
            "phone": "+9647700000000",
        },
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["full_name"] == "Test Citizen"
    assert "id" in data


def test_get_canonical_patient(client, token):
    create = client.post(
        "/api/v1/canonical-patients",
        json={"full_name": "Get Test", "date_of_birth": "1990-01-01", "gender": "F"},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert create.status_code == 201, create.text
    pid = create.json()["id"]
    resp = client.get(f"/api/v1/canonical-patients/{pid}", headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)})
    assert resp.status_code == 200
    assert resp.json()["id"] == pid


def test_search_canonical_patients(client, token):
    client.post(
        "/api/v1/canonical-patients",
        json={"full_name": "Searchable Person", "date_of_birth": "1985-05-05", "gender": "M"},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    resp = client.get(
        "/api/v1/canonical-patients?q=Searchable",
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["total"] >= 1
    assert any("Searchable" in i.get("full_name", "") for i in body["items"])


def test_merge_canonical_patients(client, token):
    a = client.post(
        "/api/v1/canonical-patients",
        json={"full_name": "Merge A", "date_of_birth": "1980-01-01", "gender": "M"},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert a.status_code == 201, a.text
    a_data = a.json()
    b = client.post(
        "/api/v1/canonical-patients",
        json={"full_name": "Merge B", "date_of_birth": "1980-01-01", "gender": "M"},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert b.status_code == 201, b.text
    b_data = b.json()
    resp = client.post(
        "/api/v1/canonical-patients/merge",
        json={"target_id": a_data["id"], "source_id": b_data["id"]},
        headers={"Authorization": _AUTH_HEADER_TEMPLATE.format(token)},
    )
    assert resp.status_code == 200, resp.text


# ── Auth required on protected endpoints ──


def test_mfa_endpoints_require_auth(client):
    for path in ["/mfa/status", "/mfa/devices", "/mfa/totp/setup", "/mfa/webauthn/register/begin"]:
        resp = client.get(path) if path in ("/mfa/status", "/mfa/devices") else client.post(path, json={})
        assert resp.status_code == 401, f"{path} returned {resp.status_code}"


def test_password_reset_endpoints_require_auth(client):
    resp = client.post("/auth/change-password", json={"current_password": "x", "new_password": "y"})
    assert resp.status_code == 401
