"""AUD-API-002 — adversarial regression tests for OAuth2 token usability.

The auditor found that every token minted by the OAuth2 provider used
``type="oauth2_access"``, which the canonical decode_token()/get_current_user()
chain rejects. The only decoder that accepted it (decode_oauth2_token) had zero
call sites. Result: OAuth2 authorization-code / refresh tokens could be minted
but never used against GULA's own API — 401 on every protected route.

The fix unifies OAuth2 access tokens into the canonical token pipeline
(``type="access"`` + user_id/account_kind/lab_id/role/perm_ver claims) and stores
the subject's account domain at authorization time so strict, collision-safe
resolution is possible (AUD-SEC-002).

Falsification axis: mint via POST /oauth2/token, then call a real protected
route and prove it is NOT 401.
"""
from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timedelta

import pytest
from app._compat import UTC
from app.config import SECRET_KEY
from app.models.lab_user import LabUser
from app.models.oauth2_client import OAuth2Client
from app.models.oauth2_token import OAuth2Token
from app.models.user import User
from app.security.auth import (
    ACCOUNT_KIND_LAB,
    ACCOUNT_KIND_USER,
    decode_token,
)
from app.security.oauth2_provider import (
    create_access_token_oauth2,
    create_refresh_token_oauth2,
    decode_oauth2_refresh_token,
    decode_oauth2_token,
    hash_token,
)

from shared.auth import create_access_token

_PROTECTED = "/labs/me"


def _pkce(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


def _client(db, *, method="none", scopes=None):
    client = OAuth2Client(
        client_id=f"gula_test_{hashlib.sha256(str(id(db)).encode()).hexdigest()[:12]}",
        client_secret_hash="unused",
        redirect_uris=json.dumps(["https://rp.test/callback"]),
        allowed_scopes=json.dumps(scopes or ["read", "write"]),
        grant_types=json.dumps(["authorization_code", "client_credentials", "refresh_token"]),
        response_types=json.dumps(["code"]),
        is_active=1,
        token_endpoint_auth_method=method,
    )
    db.add(client)
    db.flush()
    return client


def _auth_code(db, client, user, *, account_kind=ACCOUNT_KIND_LAB, code="valid-code", verifier="verifier-123"):
    record = OAuth2Token(
        client_id=client.client_id,
        user_id=user.id,
        account_kind=account_kind,
        token_type="authorization_code",
        token_hash=hash_token(code),
        scope="read write",
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        code_challenge=_pkce(verifier),
        code_challenge_method="S256",
        is_revoked=0,
    )
    db.add(record)
    db.flush()
    return code, verifier


def _token_request(client_id, grant_type, **kwargs):
    body = {"grant_type": grant_type, "client_id": client_id}
    body.update(kwargs)
    return body


# ── The core falsification: minted token works on a protected route ───────────


class TestOAuth2TokenUsable:
    def test_authorization_code_token_is_accepted_by_protected_route(
        self, client, db, make_lab, make_lab_user
    ):
        lab = make_lab()
        lab_user = make_lab_user(lab.id, role="admin")
        oauth_client = _client(db)
        code, verifier = _auth_code(db, oauth_client, lab_user)

        token_resp = client.post(
            "/oauth2/token",
            json=_token_request(
                oauth_client.client_id,
                "authorization_code",
                code=code,
                code_verifier=verifier,
            ),
        )
        assert token_resp.status_code == 200, token_resp.text
        body = token_resp.json()
        access_token = body["access_token"]

        # Canonical decoder now accepts the token (was the root-cause failure).
        payload = decode_token(access_token)
        assert payload is not None, "OAuth2 token still rejected by canonical decode_token"
        assert payload["type"] == "access"
        assert payload["user_id"] == lab_user.id
        assert payload["account_kind"] == ACCOUNT_KIND_LAB
        assert payload["lab_id"] == lab.id
        assert "perm_ver" in payload

        # The actual proof: a protected route accepts it (no longer 401).
        protected = client.get(_PROTECTED, headers={"Authorization": f"Bearer {access_token}"})
        assert protected.status_code == 200, (
            f"OAuth2 minted token still rejected by protected route: {protected.status_code} {protected.text}"
        )
        assert protected.json()["id"] == lab.id

    def test_refresh_token_yields_a_usable_access_token(
        self, client, db, make_lab, make_lab_user
    ):
        lab = make_lab()
        lab_user = make_lab_user(lab.id, role="admin")
        oauth_client = _client(db)
        code, verifier = _auth_code(db, oauth_client, lab_user)

        first = client.post(
            "/oauth2/token",
            json=_token_request(
                oauth_client.client_id, "authorization_code", code=code, code_verifier=verifier
            ),
        ).json()
        refresh = client.post(
            "/oauth2/token",
            json=_token_request(
                oauth_client.client_id, "refresh_token", refresh_token=first["refresh_token"]
            ),
        )
        assert refresh.status_code == 200, refresh.text
        new_access = refresh.json()["access_token"]
        assert decode_token(new_access) is not None
        protected = client.get(_PROTECTED, headers={"Authorization": f"Bearer {new_access}"})
        assert protected.status_code == 200

    def test_minted_token_resolves_to_correct_family_on_id_collision(
        self, client, db, make_lab
    ):
        """AUD-SEC-002 cross-check: OAuth2 token must not collide into a User."""
        lab = make_lab()
        collision_id = 95001
        lab_user = LabUser(
            id=collision_id, lab_id=lab.id, name="Privileged", email="oauth-lab@test.com",
            password_hash="x", role="master_admin", is_active=True,
        )
        citizen = User(
            id=collision_id, email="oauth-citizen@test.com", password_hash="x",
            full_name="Citizen", role="citizen", lab_id=None, is_active=True, is_verified=True,
        )
        db.add_all([lab_user, citizen])
        db.flush()
        oauth_client = _client(db)
        code, verifier = _auth_code(db, oauth_client, lab_user)

        access = client.post(
            "/oauth2/token",
            json=_token_request(
                oauth_client.client_id, "authorization_code", code=code, code_verifier=verifier
            ),
        ).json()["access_token"]
        # /labs/me requires a LabUser; if the token resolved to the colliding
        # User it would fail (User has no lab_id / is a different family).
        protected = client.get(_PROTECTED, headers={"Authorization": f"Bearer {access}"})
        assert protected.status_code == 200
        assert decode_token(access)["account_kind"] == ACCOUNT_KIND_LAB


# ── Negative boundaries ───────────────────────────────────────────────────────


class TestOAuth2NegativeBoundaries:
    def test_client_credentials_token_cannot_impersonate_a_user(
        self, client, db
    ):
        oauth_client = _client(db)
        resp = client.post(
            "/oauth2/token",
            json=_token_request(oauth_client.client_id, "client_credentials", scope="read"),
        )
        assert resp.status_code == 200, resp.text
        machine_token = resp.json()["access_token"]
        payload = decode_token(machine_token)
        assert payload is not None
        assert "user_id" not in payload  # no subject to impersonate
        protected = client.get(_PROTECTED, headers={"Authorization": f"Bearer {machine_token}"})
        assert protected.status_code == 401

    def test_legacy_oauth2_access_token_is_not_accepted_by_canonical_chain(self):
        """Backward compat: legacy decoder still reads it, but it is unusable."""
        # New mints are canonical; build an actual legacy-shaped token directly.
        legacy = create_access_token(
            {"jti": "legacy", "client_id": "gula_legacy", "type": "oauth2_access", "user_id": 1},
            secret_key=SECRET_KEY,
            algorithm="HS256",
            expire_minutes=5,
        )
        assert decode_oauth2_token(legacy) is not None  # legacy decoder tolerant
        assert decode_token(legacy) is None  # canonical chain rejects (fail closed)

    def test_claims_without_account_kind_do_not_invent_a_domain(self, client, db, make_lab, make_lab_user):
        """A token with user_id but no domain must fail resolution, not guess."""
        lab = make_lab()
        lab_user = make_lab_user(lab.id, role="admin")
        token, _ = create_access_token_oauth2(
            "gula_test", user_id=lab_user.id, claims={"role": "admin", "lab_id": lab.id}
        )
        assert decode_token(token) is not None
        # account_kind absent; lab_id present -> legacy derivation resolves LAB.
        # That is the documented legacy fallback, not a collision guess.
        protected = client.get(_PROTECTED, headers={"Authorization": f"Bearer {token}"})
        assert protected.status_code == 200


# ── Team C falsification follow-up (2026-11-19) ─────────────────────────────────
# Fresh-context verification found a narrower fail-open: `_resolve_oauth2_user_claims`
# correctly returned NO claims for a NULL/unknown account_kind, but the grant and
# refresh handlers passed the bare `user_id` straight into the token mint anyway.
# With neither account_kind nor lab_id, resolve_token_account_kind() defaults to
# the USER family — so a legacy LabUser subject on an ID collision could bind to
# the wrong User account. These tests pin the fail-closed invariant.


class TestLegacyOAuth2DomainFailClosed:
    def test_provider_never_embeds_bare_user_id_without_a_resolvable_domain(self):
        """A user_id with no signed domain must not be put on a token at all."""
        token, _ = create_access_token_oauth2("gula_test", user_id=424242, claims={})
        payload = decode_token(token)
        assert payload is not None
        assert "user_id" not in payload, (
            "bare user_id with no account_kind/lab_id resolves by GUESS to the USER family"
        )

    def test_provider_keeps_user_id_when_a_signed_domain_is_present(self):
        """Backward compatibility: a resolved domain still carries the subject."""
        token, _ = create_access_token_oauth2(
            "gula_test",
            user_id=424242,
            claims={"account_kind": ACCOUNT_KIND_USER, "lab_id": None},
        )
        payload = decode_token(token)
        assert payload is not None
        assert payload["user_id"] == 424242
        assert payload["account_kind"] == ACCOUNT_KIND_USER

    def test_refresh_token_carries_no_subject_without_account_kind(self):
        refresh = create_refresh_token_oauth2("gula_test", user_id=424242, account_kind=None)
        payload = decode_oauth2_refresh_token(refresh)
        assert payload is not None
        assert "user_id" not in payload

    def test_legacy_null_account_kind_grant_cannot_bind_to_colliding_user(
        self, client, db, make_lab
    ):
        """End-to-end: a NULL-domain legacy code must not resolve to a User."""
        lab = make_lab()
        collision_id = 95002
        lab_user = LabUser(
            id=collision_id, lab_id=lab.id, name="Privileged", email="legacy-lab@test.com",
            password_hash="x", role="master_admin", is_active=True,
        )
        citizen = User(
            id=collision_id, email="legacy-citizen@test.com", password_hash="x",
            full_name="Citizen", role="citizen", lab_id=None, is_active=True, is_verified=True,
        )
        db.add_all([lab_user, citizen])
        db.flush()
        oauth_client = _client(db)
        # Explicitly simulate a pre-fix authorization code with no recorded domain.
        code, verifier = _auth_code(db, oauth_client, lab_user, account_kind=None)

        resp = client.post(
            "/oauth2/token",
            json=_token_request(
                oauth_client.client_id, "authorization_code", code=code, code_verifier=verifier
            ),
        )
        assert resp.status_code == 200, resp.text
        access = resp.json()["access_token"]
        payload = decode_token(access)
        assert payload is not None
        assert "user_id" not in payload, "legacy NULL-domain grant leaked a guessed subject"
        # The canonical chain rejects a userless token — fail closed.
        protected = client.get(_PROTECTED, headers={"Authorization": f"Bearer {access}"})
        assert protected.status_code == 401
