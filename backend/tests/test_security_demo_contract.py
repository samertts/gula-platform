from __future__ import annotations

import pytest
from shared.auth.passwords import hash_password

from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.user import User


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
