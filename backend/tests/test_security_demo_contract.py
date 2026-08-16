from __future__ import annotations

import pytest
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.user import User

from shared.auth.passwords import hash_password


def test_failed_login_is_a_safe_401(client):
    response = client.post("/login", json={"email": "nobody@example.com", "password": "wrong-password"})
    assert response.status_code == 401
    assert "traceback" not in response.text.lower()


def test_user_verification_round_trip(client, db):
    user = User(
        email="citizen@example.com",
        phone="+9647701111111",
        password_hash=hash_password("CitizenPassword123!"),
        full_name="Demo Citizen",
        role="citizen",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()

    requested = client.post("/auth/verification/request", json={"identifier": user.email})
    assert requested.status_code == 202
    code = requested.json().get("demo_code")
    assert code and len(code) == 6

    confirmed = client.post(
        "/auth/verification/confirm",
        json={"identifier": user.email, "code": code},
    )
    assert confirmed.status_code == 200
    db.refresh(user)
    assert user.is_verified is True

    logged_in = client.post(
        "/login",
        json={"email": user.email, "password": "CitizenPassword123!"},
    )
    assert logged_in.status_code == 200
    assert logged_in.cookies.get("access_token")


def test_verification_resend_is_throttled_and_code_is_single_use(client, db):
    user = User(
        email="citizen-verification-replay@example.com",
        phone="+9647701111122",
        password_hash=hash_password("CitizenPassword123!"),
        full_name="Replay Citizen",
        role="citizen",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()

    first = client.post(
        "/auth/verification/request",
        json={"identifier": user.email},
    )
    code = first.json().get("demo_code")
    assert first.status_code == 202
    assert code and len(code) == 6

    resend = client.post(
        "/auth/verification/request",
        json={"identifier": user.email},
    )
    assert resend.status_code == 202
    assert "demo_code" not in resend.json()

    confirmed = client.post(
        "/auth/verification/confirm",
        json={"identifier": user.email, "code": code},
    )
    assert confirmed.status_code == 200

    replay = client.post(
        "/auth/verification/confirm",
        json={"identifier": user.email, "code": code},
    )
    assert replay.status_code == 400


def test_verification_provider_failure_never_succeeds(client, db, monkeypatch):
    user = User(
        email="citizen-verification-provider@example.com",
        phone="+9647701111144",
        password_hash=hash_password("CitizenPassword123!"),
        full_name="Provider Failure Citizen",
        role="citizen",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()

    class _FailureService:
        def send_email(self, *_args, **_kwargs):
            return type("Delivery", (), {"success": False})()

        def send_sms(self, *_args, **_kwargs):
            return type("Delivery", (), {"success": False})()

    monkeypatch.setattr(
        "app.notifications.service.get_service",
        lambda: _FailureService(),
    )
    response = client.post(
        "/auth/verification/request",
        json={"identifier": user.email},
    )

    assert response.status_code == 202
    assert "demo_code" not in response.json()
    db.refresh(user)
    assert user.is_verified is False


def test_verification_attempt_limit_is_server_authoritative(client, db):
    user = User(
        email="citizen-verification-attempts@example.com",
        phone="+9647701111133",
        password_hash=hash_password("CitizenPassword123!"),
        full_name="Attempt Citizen",
        role="citizen",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()

    requested = client.post(
        "/auth/verification/request",
        json={"identifier": user.email},
    )
    assert requested.status_code == 202
    wrong_code = "000001" if requested.json().get("demo_code") != "000001" else "999999"

    for _ in range(5):
        failed = client.post(
            "/auth/verification/confirm",
            json={"identifier": user.email, "code": wrong_code},
        )
        assert failed.status_code == 400

    blocked = client.post(
        "/auth/verification/confirm",
        json={"identifier": user.email, "code": wrong_code},
    )
    assert blocked.status_code == 429
    db.refresh(user)
    assert user.is_verified is False


def test_verification_request_does_not_enumerate_unknown_identifier(client):
    response = client.post(
        "/auth/verification/request",
        json={"identifier": "unknown-verification@example.com"},
    )
    assert response.status_code == 202
    assert response.json() == {
        "message": "If the account exists, a verification code has been sent."
    }


def test_cross_origin_cookie_write_is_rejected(client, db):
    lab = Lab(name="CSRF Lab", is_active=True)
    db.add(lab)
    db.flush()
    user = LabUser(
        lab_id=lab.id,
        name="CSRF Admin",
        email="csrf-admin@example.com",
        password_hash=hash_password("AdminPassword123!"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()

    logged_in = client.post(
        "/login",
        json={"email": user.email, "password": "AdminPassword123!"},
    )
    assert logged_in.status_code == 200
    rejected = client.post("/logout", headers={"Origin": "https://evil.example"})
    assert rejected.status_code == 403


def test_demo_access_is_disabled_by_default(client):
    response = client.post("/demo/access")
    assert response.status_code == 404
