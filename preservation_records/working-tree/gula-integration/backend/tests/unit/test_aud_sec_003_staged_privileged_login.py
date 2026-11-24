"""AUD-SEC-003 — adversarial regression tests for staged privileged login.

The auditor found that privileged roles (master_admin / ministry_admin /
province_admin) received full access+refresh tokens from a password alone as
soon as *any* MFA device was enrolled — no factor was ever verified.

The fix: credentials yield only a short-lived, single-purpose mfa_pending
token; full tokens are minted exclusively after a real TOTP/WebAuthn factor is
verified, and the pending token is single-use.
"""
from __future__ import annotations

import pyotp
import pytest
from app.models.audit_log import AuditLog
from app.security.auth import decode_mfa_pending_token, decode_token


def _enroll_totp(db, user):
    from app.security.mfa_service import MFAService

    enrollment = MFAService(db).setup_totp(user.id, user.email or "admin@test.invalid")
    return pyotp.TOTP(enrollment["secret"]).now()


def _privileged(db, make_lab, make_lab_user, role="master_admin", with_mfa=True):
    lab = make_lab()
    user = make_lab_user(lab.id, role=role)
    code = _enroll_totp(db, user) if with_mfa else None
    return lab, user, code


def _login(client, user):
    return client.post("/login", json={"email": user.email, "password": "Testpass1"})


# ── Password-only must never produce tokens ───────────────────────────────────


class TestPasswordOnlyRejected:
    @pytest.mark.parametrize("role", ["master_admin", "ministry_admin", "province_admin"])
    def test_password_only_returns_pending_not_full_tokens(self, client, db, make_lab, make_lab_user, role):
        _, user, _ = _privileged(db, make_lab, make_lab_user, role=role)
        resp = _login(client, user)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body.get("mfa_required") is True
        assert body.get("mfa_pending_token")
        # The critical assertion: no usable credential material is returned.
        assert "access_token" not in body
        assert "token" not in body
        assert "refresh_token" not in body
        assert client.cookies.get("access_token") is None
        assert client.cookies.get("refresh_token") is None

    def test_pending_token_is_not_an_access_token(self, client, db, make_lab, make_lab_user):
        _, user, _ = _privileged(db, make_lab, make_lab_user)
        pending = _login(client, user).json()["mfa_pending_token"]
        assert decode_token(pending) is None, "pending token passed as a normal access token"
        assert decode_mfa_pending_token(pending) is not None

    def test_pending_token_cannot_access_protected_route(self, client, db, make_lab, make_lab_user):
        _, user, _ = _privileged(db, make_lab, make_lab_user)
        pending = _login(client, user).json()["mfa_pending_token"]
        resp = client.get("/session", headers={"Authorization": f"Bearer {pending}"})
        assert resp.status_code == 401, "pending token was accepted by a protected route"

    def test_privileged_without_mfa_enrollment_still_denied(self, client, db, make_lab, make_lab_user):
        _, user, _ = _privileged(db, make_lab, make_lab_user, with_mfa=False)
        resp = _login(client, user)
        assert resp.status_code == 403


# ── Real factor verification ──────────────────────────────────────────────────


class TestMFACompletion:
    def test_wrong_code_denied_and_no_tokens(self, client, db, make_lab, make_lab_user):
        _, user, _ = _privileged(db, make_lab, make_lab_user)
        pending = _login(client, user).json()["mfa_pending_token"]
        resp = client.post(
            "/login/mfa/verify",
            json={"mfa_pending_token": pending, "method": "totp", "code": "000000"},
        )
        assert resp.status_code == 401, resp.text
        assert "access_token" not in resp.json()
        assert client.cookies.get("access_token") is None

    def test_correct_code_issues_full_tokens(self, client, db, make_lab, make_lab_user):
        _, user, code = _privileged(db, make_lab, make_lab_user)
        pending = _login(client, user).json()["mfa_pending_token"]
        resp = client.post(
            "/login/mfa/verify",
            json={"mfa_pending_token": pending, "method": "totp", "code": code},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["access_token"] and body["refresh_token"]
        assert decode_token(body["access_token"]) is not None
        assert client.cookies.get("access_token")
        assert client.cookies.get("refresh_token")

    def test_pending_token_is_single_use(self, client, db, make_lab, make_lab_user):
        _, user, code = _privileged(db, make_lab, make_lab_user)
        pending = _login(client, user).json()["mfa_pending_token"]
        good = {"mfa_pending_token": pending, "method": "totp", "code": code}
        assert client.post("/login/mfa/verify", json=good).status_code == 200
        # Replaying the same challenge must be rejected (single-use).
        replay = client.post("/login/mfa/verify", json=good)
        assert replay.status_code == 401, "pending token replay succeeded"

    def test_forged_pending_token_rejected(self, client, db, make_lab, make_lab_user):
        _privileged(db, make_lab, make_lab_user)
        resp = client.post(
            "/login/mfa/verify",
            json={"mfa_pending_token": "not-a-jwt", "method": "totp", "code": "123456"},
        )
        assert resp.status_code == 401

    def test_access_token_cannot_be_used_to_complete_mfa(self, client, db, make_lab, make_lab_user):
        """A full token is not a pending token — type confusion must fail."""
        lab, _user, code = _privileged(db, make_lab, make_lab_user)
        # A normal (non-privileged) account gets a full token from /login.
        normal = make_lab_user(lab.id, role="staff")
        full = _login(client, normal).json()["access_token"]
        resp = client.post(
            "/login/mfa/verify",
            json={"mfa_pending_token": full, "method": "totp", "code": code},
        )
        assert resp.status_code == 401

    def test_mfa_failure_is_audited(self, client, db, make_lab, make_lab_user):
        _, user, _ = _privileged(db, make_lab, make_lab_user)
        pending = _login(client, user).json()["mfa_pending_token"]
        client.post(
            "/login/mfa/verify",
            json={"mfa_pending_token": pending, "method": "totp", "code": "000000"},
        )
        actions = [a.action for a in db.query(AuditLog).all()]
        assert "login_mfa_failed" in actions


# ── Backward compatibility ────────────────────────────────────────────────────


class TestBackwardCompatibility:
    def test_non_privileged_login_still_returns_full_tokens(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab.id, role="staff")
        resp = _login(client, user)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["access_token"] and body["refresh_token"]
        assert body.get("mfa_required") is not True
        assert client.cookies.get("access_token")
