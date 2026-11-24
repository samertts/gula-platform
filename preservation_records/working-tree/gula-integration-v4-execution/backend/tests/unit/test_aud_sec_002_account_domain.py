"""AUD-SEC-002 — adversarial regression tests for account-domain token separation.

LabUser.id and User.id are independent primary-key spaces. A token carrying a
bare ``user_id`` integer was previously resolved LabUser-first, then User, so
an account in one family could authenticate as a colliding account in the
other (privilege escalation / tenant impersonation). The fix binds every token
to a signed ``account_kind`` claim and resolves strictly within that domain.

These tests are falsification-first: they construct the *exact* collision the
auditor described and prove it can no longer be exploited, while proving legacy
lab_id-derived tokens still work.
"""
from __future__ import annotations

import pytest
from app.models.lab_user import LabUser
from app.models.user import User
from app.security import dependencies as deps
from app.security.auth import (
    ACCOUNT_KIND_LAB,
    ACCOUNT_KIND_NIAM,
    ACCOUNT_KIND_USER,
    account_kind_for_principal,
    build_token_payload,
    create_token,
    resolve_token_account_kind,
)
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

# A colliding primary key shared by both account families.
_COLLISION_ID = 9001


def _request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/", "headers": [], "query_string": b""})


def _creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


@pytest.fixture(autouse=True)
def _no_redis(monkeypatch):
    """Keep revocation checks local so the tests exercise resolution, not Redis."""
    monkeypatch.setattr(deps, "is_token_blacklisted", lambda jti: False)


def _seed_collision(db, make_lab):
    """Create a LabUser and a User sharing the same integer id."""
    lab = make_lab(name="Collision Lab")
    lab_user = LabUser(
        id=_COLLISION_ID,
        lab_id=lab.id,
        name="Privileged Lab Admin",
        email="collision-lab@test.com",
        password_hash="x",
        role="master_admin",
        is_active=True,
    )
    citizen = User(
        id=_COLLISION_ID,
        email="collision-citizen@test.com",
        password_hash="x",
        full_name="Ordinary Citizen",
        role="citizen",
        lab_id=None,
        is_active=True,
        is_verified=True,
    )
    db.add_all([lab_user, citizen])
    db.flush()
    return lab_user, citizen


# ── Payload emission ──────────────────────────────────────────────────────────


class TestTokenPayloadDomain:
    def test_real_lab_user_is_classified_lab(self, db, make_lab):
        lab_user, _ = _seed_collision(db, make_lab)
        assert account_kind_for_principal(lab_user) == ACCOUNT_KIND_LAB
        assert build_token_payload(lab_user)["account_kind"] == ACCOUNT_KIND_LAB

    def test_build_token_payload_marks_user_principal(self):
        class _UserLike:
            id = 1
            lab_id = None
            role = "citizen"
            perm_version = None

        assert build_token_payload(_UserLike())["account_kind"] == ACCOUNT_KIND_USER

    @pytest.mark.parametrize(
        "payload,expected",
        [
            ({"account_kind": ACCOUNT_KIND_LAB, "lab_id": 7}, ACCOUNT_KIND_LAB),
            ({"account_kind": ACCOUNT_KIND_USER, "lab_id": None}, ACCOUNT_KIND_USER),
            ({"lab_id": 7}, ACCOUNT_KIND_LAB),  # legacy lab token
            ({"lab_id": None}, ACCOUNT_KIND_USER),  # legacy citizen token
        ],
    )
    def test_resolve_account_kind(self, payload, expected):
        assert resolve_token_account_kind(payload) == expected

    @pytest.mark.parametrize("bad", ["niam_account", "admin", "", 0])
    def test_unknown_or_niam_account_kind_is_rejected(self, bad):
        # "niam_account" is a valid domain for identity-domain tokens but is
        # NOT a valid value for canonical user/lab access tokens. A *present*
        # but unknown value must fail closed; an absent (None) claim falls
        # back to legacy lab_id derivation and is covered separately.
        payload = {"account_kind": bad, "lab_id": 7}
        assert resolve_token_account_kind(payload) is None

    def test_absent_account_kind_falls_back_to_legacy(self):
        assert resolve_token_account_kind({"account_kind": None, "lab_id": 7}) == ACCOUNT_KIND_LAB


# ── The core collision boundary ───────────────────────────────────────────────


class TestCollisionResolution:
    def test_user_token_never_resolves_to_colliding_labuser(self, db, make_lab):
        _seed_collision(db, make_lab)
        token = create_token(
            {"user_id": _COLLISION_ID, "lab_id": None, "role": "citizen", "account_kind": ACCOUNT_KIND_USER}
        )
        resolved = deps.get_current_user(_request(), _creds(token), db)
        assert isinstance(resolved, User), "user-domain token resolved to a LabUser — collision not fixed"
        assert resolved.role == "citizen"

    def test_lab_token_never_resolves_to_colliding_user(self, db, make_lab):
        _seed_collision(db, make_lab)
        token = create_token(
            {"user_id": _COLLISION_ID, "lab_id": 7, "role": "master_admin", "account_kind": ACCOUNT_KIND_LAB}
        )
        resolved = deps.get_current_user(_request(), _creds(token), db)
        assert isinstance(resolved, LabUser), "lab-domain token resolved to a User — collision not fixed"
        assert resolved.role == "master_admin"

    def test_unknown_account_kind_rejected(self, db, make_lab):
        _seed_collision(db, make_lab)
        token = create_token(
            {"user_id": _COLLISION_ID, "lab_id": 7, "account_kind": "superadmin"}
        )
        with pytest.raises(HTTPException) as exc:
            deps.get_current_user(_request(), _creds(token), db)
        assert exc.value.status_code == 401

    def test_niam_token_rejected_by_canonical_dependency(self, db, make_lab):
        """An identity-domain token must not be usable as a lab/citizen token."""
        _seed_collision(db, make_lab)
        token = create_token(
            {"jti": "niam-1", "account_uuid": "u", "account_kind": ACCOUNT_KIND_NIAM, "user_id": _COLLISION_ID}
        )
        with pytest.raises(HTTPException) as exc:
            deps.get_current_user(_request(), _creds(token), db)
        assert exc.value.status_code == 401

    def test_lab_domain_token_cannot_select_nonexistent_labuser_even_if_user_exists(self, db, make_lab):
        """No colliding LabUser row: token must fail closed, not fall back to User."""
        lab = make_lab(name="Lab Without Admin")
        db.add(
            User(
                id=_COLLISION_ID,
                email="solo-citizen@test.com",
                password_hash="x",
                full_name="Solo Citizen",
                role="citizen",
                lab_id=None,
                is_active=True,
                is_verified=True,
            )
        )
        db.flush()
        assert lab.id is not None
        token = create_token(
            {"user_id": _COLLISION_ID, "lab_id": lab.id, "role": "admin", "account_kind": ACCOUNT_KIND_LAB}
        )
        with pytest.raises(HTTPException) as exc:
            deps.get_current_user(_request(), _creds(token), db)
        assert exc.value.status_code == 401


# ── Backward compatibility: legacy tokens without account_kind ────────────────


class TestLegacyTokenCompatibility:
    def test_legacy_lab_token_still_resolves_labuser(self, db, make_lab):
        lab_user, _ = _seed_collision(db, make_lab)
        from app.security.auth import decode_token

        token = create_token({"user_id": _COLLISION_ID, "lab_id": lab_user.lab_id, "role": "master_admin"})
        payload = decode_token(token)
        assert payload is not None and "account_kind" not in payload
        resolved = deps.get_current_user(_request(), _creds(token), db)
        assert isinstance(resolved, LabUser)

    def test_legacy_citizen_token_still_resolves_user(self, db, make_lab):
        _seed_collision(db, make_lab)
        token = create_token({"user_id": _COLLISION_ID, "lab_id": None, "role": "citizen"})
        resolved = deps.get_current_user(_request(), _creds(token), db)
        assert isinstance(resolved, User)
        assert resolved.role == "citizen"
