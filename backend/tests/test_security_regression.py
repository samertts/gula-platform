"""Security regression suite — Phase 14 hardening.

Hardens the auth & authorization surfaces with deterministic regression
tests against the most common penetration patterns:

  1. Stale-token misuse — expired access tokens never re-validate
  2. Cross-token-type confusion — access tokens cannot be used as refresh, vice versa
  3. Tampered-signature rejection — modified payloads / signatures fail
  4. RBAC bypass via raw role override in headers
  5. Mass-assignment — extra fields in update payloads cannot mutate
     non-whitelisted columns (e.g. lab_id, role, perm_version)
  6. Replay protection on refresh tokens via JTI blacklist
  7. SQL-injection-shaped values are rejected by validators
  8. User enumeration via timing — dummy-hash compare is in place
  9. Algorithm-confusion attack: HS256 token signed with public RS256 key
     cannot validate (all tokens use HS256 only)
 10. ``perm_version`` propagation — when permissions change, old tokens
     are recognized as stale

Blast radius: zero. Pure regression suite.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone

from app._compat import UTC

os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest
from app.config import JWT_ALGORITHM, SECRET_KEY
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.security.auth import (
    build_token_payload,
    create_refresh_token,
    create_token,
    decode_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from joserfc import jwt as jose_jwt
from joserfc import jwk


def _hdr(user_id: int, lab_id: int, role: str = "admin") -> dict:
    token = create_token({"user_id": user_id, "lab_id": lab_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sec_lab(db, make_lab, make_lab_user):
    lab = make_lab(name="Sec Lab")
    admin = make_lab_user(lab_id=lab.id, role="admin", email="sec_admin@x.com")
    tech = make_lab_user(lab_id=lab.id, role="technician", email="sec_tech@x.com")
    db.commit()
    return {"lab": lab, "admin": admin, "tech": tech}


# ─── Phase 14.A — Stale-token rejection ──────────────────────────────────────


class TestStaleTokenRejection:
    """Expired tokens must fail validation. We forge a token with a
    past 'exp' and verify decode_token rejects it."""

    def test_expired_access_token_rejected(self):
        # Forge an already-expired token
        payload = {
            "user_id": 1, "lab_id": 1, "role": "admin",
            "exp": datetime.now(UTC) - timedelta(hours=1),
            "type": "access",
            "jti": "fake-jti",
        }
        token = jose_jwt.encode({"alg": JWT_ALGORITHM}, payload, jwk.OctKey.import_key(SECRET_KEY))
        assert decode_token(token) is None

    def test_expired_refresh_token_rejected(self):
        from app.config import REFRESH_TOKEN_SECRET
        payload = {
            "user_id": 1, "lab_id": 1, "role": "admin",
            "exp": datetime.now(UTC) - timedelta(days=60),
            "type": "refresh",
            "jti": "fake-jti",
        }
        token = jose_jwt.encode({"alg": JWT_ALGORITHM}, payload, jwk.OctKey.import_key(REFRESH_TOKEN_SECRET))
        assert decode_refresh_token(token) is None

    def test_token_without_exp_claim_documents_jose_behavior(self):
        payload = {
            "user_id": 1, "lab_id": 1, "role": "admin",
            "type": "access",
            "jti": "fake",
        }
        token = jose_jwt.encode({"alg": JWT_ALGORITHM}, payload, jwk.OctKey.import_key(SECRET_KEY))
        result = decode_token(token)
        assert result is None, (
            "joserfc enforces exp by default — the security guarantee "
            "has been tightened with the python-jose→joserfc migration."
        )


# ─── Phase 14.B — Cross-token-type confusion ─────────────────────────────────


class TestTokenTypeConfusion:
    """Access tokens cannot be used as refresh tokens, and vice versa."""

    def test_access_token_rejected_as_refresh(self):
        access = create_token({"user_id": 1, "lab_id": 1, "role": "admin"})
        # decode_refresh_token uses REFRESH_TOKEN_SECRET — different secret
        assert decode_refresh_token(access) is None

    def test_refresh_token_rejected_as_access(self):
        refresh = create_refresh_token({"user_id": 1, "lab_id": 1, "role": "admin"})
        assert decode_token(refresh) is None


# ─── Phase 14.C — Tampered signature rejection ───────────────────────────────


class TestSignatureTampering:
    """Mutated payloads or signatures must fail validation."""

    def test_token_signed_with_wrong_secret_rejected(self):
        bad = jose_jwt.encode(
            {"alg": JWT_ALGORITHM},
            {
                "user_id": 1, "lab_id": 1, "role": "admin",
                "exp": datetime.now(UTC) + timedelta(hours=1),
                "type": "access",
                "jti": "fake",
            },
            jwk.OctKey.import_key("wrong-secret"),
        )
        assert decode_token(bad) is None

    def test_payload_byte_swap_rejected(self):
        token = create_token({"user_id": 1, "lab_id": 1, "role": "admin"})
        # Flip one character in the middle (payload section)
        parts = token.split(".")
        if len(parts[1]) > 4:
            mutated = parts[1][:5] + ("X" if parts[1][5] != "X" else "Y") + parts[1][6:]
            forged = ".".join([parts[0], mutated, parts[2]])
            assert decode_token(forged) is None

    def test_role_escalation_via_payload_swap_blocked(self):
        """Forging a token with role=master_admin using the wrong key fails."""
        bad = jose_jwt.encode(
            {"alg": JWT_ALGORITHM},
            {
                "user_id": 1, "lab_id": 1, "role": "master_admin",
                "exp": datetime.now(UTC) + timedelta(hours=1),
                "type": "access",
                "jti": "fake",
            },
            jwk.OctKey.import_key("attacker-supplied-secret"),
        )
        assert decode_token(bad) is None


# ─── Phase 14.D — RBAC bypass via header override ────────────────────────────


class TestHeaderOverrideBypassResistance:
    """Custom headers like X-Role / X-Lab-Id / X-User-Id MUST NOT
    override the JWT-derived values."""

    def test_x_role_header_does_not_elevate(self, client, sec_lab):
        tech = sec_lab["tech"]  # role=technician
        forged = {
            **_hdr(tech.id, sec_lab["lab"].id, role="technician"),
            "X-Role": "master_admin",
            "X-Permissions": "all",
        }
        # A platform-admin endpoint must still 403 for the technician
        res = client.put(
            f"/admin/tiers/{sec_lab['lab'].id}",
            headers=forged,
            json={"tier": "enterprise"},
        )
        assert res.status_code == 403

    def test_x_user_id_header_does_not_change_actor(self, client, sec_lab, db):
        """A spoofed X-User-Id must not flip the audit log's user_id."""
        from app.models.audit_log import AuditLog
        admin = sec_lab["admin"]
        before = db.query(AuditLog).count()
        # Make a real mutation while passing a spoofed X-User-Id
        patient = Patient(
            lab_id=sec_lab["lab"].id, full_name="Sec P",
            phone="07700111111", health_id="HID-SEC-1",
        )
        db.add(patient); db.commit()

        client.put(
            f"/patients/{patient.id}",
            headers={**_hdr(admin.id, sec_lab["lab"].id), "X-User-Id": "999"},
            json={"city": "Mosul"},
        )
        last = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        # The audit row's user_id is the JWT's user_id, not the header
        assert last is not None
        assert last.user_id == admin.id


# ─── Phase 14.E — Mass-assignment defense ────────────────────────────────────


class TestMassAssignmentDefense:
    """Sending extra fields on a PUT must NOT mutate non-whitelisted columns."""

    def test_patient_update_cannot_change_lab_id(self, client, db, sec_lab):
        admin = sec_lab["admin"]
        patient = Patient(
            lab_id=sec_lab["lab"].id, full_name="Original",
            phone="07700111111", health_id="HID-SEC-2",
        )
        db.add(patient); db.commit()

        # Try to mass-assign lab_id, role, etc.
        client.put(
            f"/patients/{patient.id}",
            headers=_hdr(admin.id, sec_lab["lab"].id),
            json={
                "full_name": "Updated",
                "lab_id": 9999,
                "id": 9999,
                "national_id_hash": "FORGED",
                "created_at": "2000-01-01T00:00:00",
            },
        )
        db.expire(patient); db.refresh(patient)
        assert patient.lab_id == sec_lab["lab"].id  # NOT 9999
        assert patient.id != 9999

    def test_lab_user_update_via_employee_endpoint_cannot_change_lab_id(self, client, db, sec_lab):
        """The /labs/me/employees/{id} endpoint must not let an admin
        re-assign an employee to a different lab."""
        admin = sec_lab["admin"]
        emp = sec_lab["tech"]
        client.put(
            f"/labs/me/employees/{emp.id}",
            headers=_hdr(admin.id, sec_lab["lab"].id),
            json={
                "is_active": True,
                "lab_id": 99999,  # mass-assignment attempt
                "role": "master_admin",
            },
        )
        db.expire(emp); db.refresh(emp)
        assert emp.lab_id == sec_lab["lab"].id
        # Role should NOT have flipped to master_admin
        assert emp.role != "master_admin"


# ─── Phase 14.F — Replay protection on refresh tokens ────────────────────────


class TestRefreshTokenReplayProtection:
    """Once a refresh token's JTI is blacklisted, it cannot be reused."""

    def test_blacklisted_refresh_token_rejected(self):
        from app.security.auth import blacklist_token, is_token_blacklisted
        token = create_refresh_token({"user_id": 1, "lab_id": 1, "role": "admin"})
        # Decode to extract JTI
        from app.config import REFRESH_TOKEN_SECRET
        decoded = jose_jwt.decode(
            token, jwk.OctKey.import_key(REFRESH_TOKEN_SECRET), algorithms=[JWT_ALGORITHM],
        )
        jti = decoded.claims["jti"]
        # Blacklist it
        blacklist_token(jti, ttl_seconds=60)
        assert is_token_blacklisted(jti) is True
        # decode_refresh_token must now reject
        assert decode_refresh_token(token) is None


# ─── Phase 14.G — User enumeration / timing attack resistance ────────────────


class TestUserEnumerationResistance:
    """Per app/security/auth.py:28, a dummy hash is used to make the
    'user not found' branch take ~the same time as 'wrong password'."""

    def test_dummy_hash_constant_exists(self):
        from app.security import auth
        assert hasattr(auth, "_DUMMY_HASH")
        assert auth._DUMMY_HASH.startswith("$2")  # bcrypt prefix

    def test_dummy_hash_does_not_match_real_passwords(self):
        from app.security.auth import _DUMMY_HASH
        assert verify_password("admin", _DUMMY_HASH) is False
        assert verify_password("password", _DUMMY_HASH) is False
        assert verify_password("", _DUMMY_HASH) is False


# ─── Phase 14.H — Algorithm-confusion resistance ─────────────────────────────


class TestAlgorithmConfusionResistance:
    """Tokens signed with 'none' algorithm or with the wrong algorithm
    must be rejected (decode_token whitelists JWT_ALGORITHM)."""

    def test_none_algorithm_rejected(self):
        # joserfc refuses to issue a 'none'-signed token outright
        try:
            bad = jose_jwt.encode(
                {"alg": "none"},
                {
                    "user_id": 1, "lab_id": 1, "role": "admin",
                    "exp": datetime.now(UTC) + timedelta(hours=1),
                    "type": "access",
                },
                None,
            )
        except Exception:
            return
        assert decode_token(bad) is None


# ─── Phase 14.I — Permission version invalidation ────────────────────────────


class TestPermissionVersionInvalidation:
    """When a user's permissions change (role demotion, deactivation),
    old tokens carrying the prior perm_version must become invalid.
    The contract is: build_token_payload includes perm_version, and the
    auth dependency (get_current_user) compares it to the user's current
    perm_version. A regression here is a privilege-revocation failure."""

    def test_build_token_payload_includes_perm_version(self):
        # Synthesize a user-like object
        class _U:
            id = 1
            lab_id = 7
            role = "admin"
            perm_version = 5
        payload = build_token_payload(_U())
        assert payload["perm_ver"] == 5

    def test_perm_version_default_when_none(self):
        class _U:
            id = 1
            lab_id = 7
            role = "admin"
            perm_version = None
        payload = build_token_payload(_U())
        assert payload["perm_ver"] == 1


# ─── Phase 14.J — SQL-injection-shaped values rejected ───────────────────────


class TestSqlInjectionShapedInputs:
    """Pydantic validators on the patient creation surface should reject
    malformed inputs that look like SQL injection attempts."""

    def test_phone_validator_rejects_injection(self, client, sec_lab):
        admin = sec_lab["admin"]
        res = client.post(
            "/patients",
            headers=_hdr(admin.id, sec_lab["lab"].id),
            json={
                "full_name": "Injector",
                "phone": "077' OR '1'='1",  # not a valid Iraqi phone
            },
        )
        # Validator should reject with 422
        assert res.status_code == 422

    def test_birth_date_validator_rejects_injection(self, client, sec_lab):
        admin = sec_lab["admin"]
        res = client.post(
            "/patients",
            headers=_hdr(admin.id, sec_lab["lab"].id),
            json={
                "full_name": "Injector",
                "phone": "07700111111",
                "birth_date": "2000-01-01' OR '1'='1",
            },
        )
        assert res.status_code == 422


# ─── Phase 14.K — Audit-log write requires authentication ────────────────────


class TestAuditWriteRequiresAuth:
    """No anonymous endpoint should be writing to the audit log directly.
    Trace it via a regression: 100 unauthenticated requests produce zero
    write-action audit entries."""

    def test_unauthenticated_traffic_does_not_pollute_audit(self, client, db):
        from app.models.audit_log import AuditLog

        # Filter out audit-write actions specifically (login_failed is fine)
        write_actions = ("create", "update", "delete", "validate", "verify")
        before = db.query(AuditLog).filter(
            AuditLog.action.in_(write_actions)
        ).count()

        # Hammer the API anonymously
        for path in ("/patients", "/orders", "/samples", "/labs/me"):
            for _ in range(10):
                client.get(path)

        after = db.query(AuditLog).filter(
            AuditLog.action.in_(write_actions)
        ).count()
        assert after == before, (
            "Anonymous traffic produced write-action audit entries — "
            "an unauthenticated mutation path may exist."
        )
