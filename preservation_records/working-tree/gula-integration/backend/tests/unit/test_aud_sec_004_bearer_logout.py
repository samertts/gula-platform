"""AUD-SEC-004 — logout must revoke Bearer (mobile) tokens, not just cookies.

The auditor found ``logout`` read the access/refresh tokens ONLY from
``request.cookies``. A Bearer-only client has no cookies, so logout blacklisted
nothing, derived no user_id, bumped no perm_version — and the very token the
client tried to log out with remained fully usable on every protected route.

Falsification axes:
1. A Bearer-only logout must make that exact token receive 401 afterwards (e2e).
2. The Bearer JTI must be blacklisted.
3. Cookie-based (web) logout still works (no functional regression).
4. The handler uses the shared ``_extract_token`` helper (no future drift).
"""
from __future__ import annotations

import inspect

import pytest
from app.routes import login as login_route
from app.security.auth import decode_token, is_token_blacklisted


def _login(client, user):
    return client.post("/login", json={"email": user.email, "password": "Testpass1"})


class TestBearerLogoutRevocation:
    def test_bearer_only_logout_makes_token_unusable(self, client, db, make_lab, make_lab_user):
        """The exact auditor falsification: Bearer token gets 401 after logout."""
        lab = make_lab()
        user = make_lab_user(lab.id, role="technician")
        access = _login(client, user).json()["access_token"]
        header = {"Authorization": f"Bearer {access}"}

        # Precondition: the Bearer token works on a protected route.
        assert client.get("/session", headers=header).status_code == 200

        # Bearer-only mobile client: no cookies accompany the logout call.
        client.cookies.clear()
        out = client.post("/logout", headers=header)
        assert out.status_code == 200, out.text

        # The token that was logged out must now be rejected.
        assert client.get("/session", headers=header).status_code == 401, (
            "Bearer token remained usable after a Bearer-only logout"
        )

    def test_bearer_logout_blacklists_jti(self, client, db, make_lab, make_lab_user):
        """The Bearer token's JTI is added to the revocation store."""
        lab = make_lab()
        user = make_lab_user(lab.id, role="technician")
        access = _login(client, user).json()["access_token"]
        jti = decode_token(access)["jti"]
        assert is_token_blacklisted(jti) is False

        client.cookies.clear()
        assert client.post("/logout", headers={"Authorization": f"Bearer {access}"}).status_code == 200
        assert is_token_blacklisted(jti) is True, "Bearer JTI was not blacklisted on logout"

    def test_cookie_logout_still_works(self, client, db, make_lab, make_lab_user):
        """Regression guard: web (cookie) logout remains functional."""
        lab = make_lab()
        user = make_lab_user(lab.id, role="technician")
        access = _login(client, user).json()["access_token"]
        assert client.get("/session", headers={"Authorization": f"Bearer {access}"}).status_code == 200
        # No Origin header + cookie present is the normal web-app case here because
        # the TestClient UA is not a browser; CSRF middleware lets it through.
        assert client.post("/logout").status_code == 200
        assert client.get("/session", headers={"Authorization": f"Bearer {access}"}).status_code == 401

    def test_logout_uses_shared_extraction_helper(self):
        """Static guard: the shared Bearer-or-cookie extractor must be used."""
        assert "_extract_token" in inspect.getsource(login_route.logout)
        assert "HTTPAuthorizationCredentials" in inspect.getsource(login_route.logout)

    def test_invalid_bearer_does_not_shadow_valid_access_cookie(self, client, db, make_lab, make_lab_user):
        """R-SEC-004-A (Team C): a stale Bearer header must not silently no-op logout.

        _extract_token gives the Bearer header precedence. With an invalid Bearer
        and a valid access cookie, the original fix decoded nothing, blacklisted
        nothing and bumped no perm_version — yet returned 200. Both presented
        credentials must now be revoked independently.
        """
        lab = make_lab()
        user = make_lab_user(lab.id, role="technician")
        access = _login(client, user).json()["access_token"]
        jti = decode_token(access)["jti"]
        assert is_token_blacklisted(jti) is False

        # Web client with a valid access cookie, but a stale/invalid Bearer header.
        client.cookies.clear()
        client.cookies.set("access_token", access)
        out = client.post("/logout", headers={"Authorization": "Bearer not-a-jwt"})
        assert out.status_code == 200, out.text
        assert is_token_blacklisted(jti) is True, "valid cookie token was shadowed by invalid Bearer"

        # Re-arm the same cookie: the session must no longer be usable.
        client.cookies.set("access_token", access)
        assert client.get("/session").status_code == 401
