"""Regression tests for self-service verification of professional accounts (S-13).

Finding
-------
``POST /auth/verification/confirm`` sets ``is_verified = True`` on any ``User``
matched by email/phone. ``POST /register/doctor`` creates a ``User`` with
``role="doctor"`` and advertises that a ministry/province administrator must
verify the medical licence before the account is activated. Because the
self-service code is delivered to the registrant's own email/phone, a
self-declared "doctor" could verify the account themselves and obtain the
``doctor`` role's API privileges without any licence review — a
privilege-escalation path (CWE-863 incorrect authorization).

Policy under test
-----------------
* Self-service code verification is limited to roles without clinical
  privileges (``citizen``); it must not activate a professional account.
* The doctor onboarding path is unchanged: registration → pending → a
  ministry/province administrator approves the licence
  (``PUT /admin/doctors/{id}/approve``) → login succeeds.
* The response for a doctor identifier is indistinguishable from an unknown
  identifier (no account-existence oracle).
"""

from __future__ import annotations

import pytest
from shared.auth.passwords import hash_password

from app.models.user import User
from tests.conftest import auth_headers

DOCTOR_PASSWORD = "DoctorPassword123!"
DOCTOR_EMAIL = "self-declared-doctor@example.com"


def _make_doctor(db) -> User:
    doctor = User(
        email=DOCTOR_EMAIL,
        phone="+9647702222222",
        password_hash=hash_password(DOCTOR_PASSWORD),
        full_name="Self Declared Doctor",
        role="doctor",
        license_number="IQ-LIC-0001",
        specialty="Internal Medicine",
        is_active=True,
        is_verified=False,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


# ── The bypass is closed ────────────────────────────────────────────────────


def test_doctor_cannot_self_verify_and_login_stays_blocked(client, db):
    doctor = _make_doctor(db)

    requested = client.post("/auth/verification/request", json={"identifier": doctor.email})
    assert requested.status_code == 202
    # No code is issued for a professional account, even in non-production.
    assert "demo_code" not in requested.json()

    confirmed = client.post(
        "/auth/verification/confirm",
        json={"identifier": doctor.email, "code": "123456"},
    )
    assert confirmed.status_code == 400, confirmed.text

    db.refresh(doctor)
    assert doctor.is_verified is False

    login = client.post("/login", json={"email": doctor.email, "password": DOCTOR_PASSWORD})
    assert login.status_code == 403, login.text


def test_doctor_identifier_is_indistinguishable_from_unknown(client, db):
    _make_doctor(db)

    doctor_resp = client.post("/auth/verification/request", json={"identifier": DOCTOR_EMAIL})
    unknown_resp = client.post(
        "/auth/verification/request", json={"identifier": "nobody-here@example.com"},
    )

    assert doctor_resp.status_code == unknown_resp.status_code == 202
    assert doctor_resp.json() == unknown_resp.json()


# ── The legitimate administrative workflow still works ─────────────────────


def test_admin_approval_activates_doctor_and_login_succeeds(client, db, make_lab, make_lab_user):
    doctor = _make_doctor(db)
    lab = make_lab()
    approver = make_lab_user(lab.id, role="ministry_admin")

    blocked = client.post("/login", json={"email": doctor.email, "password": DOCTOR_PASSWORD})
    assert blocked.status_code == 403

    approved = client.put(
        f"/admin/doctors/{doctor.id}/approve",
        headers=auth_headers(approver.id, lab.id, role=approver.role),
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["is_verified"] is True

    login = client.post("/login", json={"email": doctor.email, "password": DOCTOR_PASSWORD})
    assert login.status_code == 200, login.text
    assert login.cookies.get("access_token")


# ── No over-restriction: citizen self-service verification is intact ───────


def test_citizen_self_verification_still_works(client, db):
    citizen = User(
        email="citizen-selfverify@example.com",
        phone="+9647703333333",
        password_hash=hash_password("CitizenPassword123!"),
        full_name="Demo Citizen",
        role="citizen",
        is_active=True,
        is_verified=False,
    )
    db.add(citizen)
    db.commit()

    requested = client.post("/auth/verification/request", json={"identifier": citizen.email})
    assert requested.status_code == 202
    code = requested.json().get("demo_code")
    assert code and len(code) == 6

    confirmed = client.post(
        "/auth/verification/confirm",
        json={"identifier": citizen.email, "code": code},
    )
    assert confirmed.status_code == 200, confirmed.text
    db.refresh(citizen)
    assert citizen.is_verified is True


@pytest.mark.parametrize("role", ["doctor", "lab_admin", "ministry_admin"])
def test_non_citizen_roles_never_self_verify(client, db, role):
    """Any professional/privileged role is excluded, not just ``doctor``."""
    user = User(
        email=f"{role}-selfverify@example.com",
        phone="+9647704444444",
        password_hash=hash_password("RolePassword123!"),
        full_name="Professional Account",
        role=role,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()

    requested = client.post("/auth/verification/request", json={"identifier": user.email})
    assert requested.status_code == 202
    assert "demo_code" not in requested.json()
    assert client.post(
        "/auth/verification/confirm",
        json={"identifier": user.email, "code": "123456"},
    ).status_code == 400
    db.refresh(user)
    assert user.is_verified is False
