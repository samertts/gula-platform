"""RFC 7662 / RFC 7009: introspection and revocation must authenticate the client.

``POST /oauth2/introspect`` and ``POST /oauth2/revoke`` answered an
unauthenticated request.  Introspection disclosed ``client_id``, ``user_id``,
``scope``, ``token_type`` and ``exp`` for any token value the caller supplied,
which is the "token scanning" attack RFC 7662 §2.1 names when it requires
authorization on that endpoint.  Revocation committed ``is_revoked`` for any
token value supplied, which is an unauthenticated, targeted denial of service
against any live session or grant.

The control already existed in the same module -- ``/token`` has always called
``_authenticate_client`` -- so this is a missing application of a present
control rather than a missing control.

Every assertion here is made against real PostgreSQL, and the revocation
assertions read ``is_revoked`` back with SQL rather than through the ORM,
because the claim being tested is about what was committed to the row.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest
from app._compat import UTC
from app.security.oauth2_provider import hash_token
from sqlalchemy import text

from tests.verification import harness

pytestmark = harness.requires_postgres()

_SECRET = "correct-horse-battery-staple"  # a fixture credential, not a real one


@pytest.fixture
def Session():
    factory = harness.session_factory()
    yield factory
    harness.dispose(factory)


def _seed_client(session, *, auth_method: str = "client_secret_post") -> str:
    """Insert one active confidential client and return its client_id."""
    from shared.auth.passwords import hash_password

    client_id = f"cid-{uuid.uuid4().hex[:16]}"
    session.execute(
        text(
            "INSERT INTO oauth2_clients "
            "(client_id, client_secret_hash, is_active, is_confidential, "
            " token_endpoint_auth_method) "
            "VALUES (:cid, :secret, true, true, :method)"
        ),
        {"cid": client_id, "secret": hash_password(_SECRET), "method": auth_method},
    )
    return client_id


def _seed_token(session, client_id: str, *, user_id: int = 4242) -> str:
    """Insert one live access token for ``client_id`` and return its raw value."""
    raw = f"tok-{uuid.uuid4().hex}"
    session.execute(
        text(
            "INSERT INTO oauth2_tokens "
            "(client_id, user_id, token_type, token_hash, scope, expires_at, is_revoked) "
            "VALUES (:cid, :uid, 'access_token', :hash, 'openid', :exp, false)"
        ),
        {
            "cid": client_id,
            "uid": user_id,
            "hash": hash_token(raw),
            "exp": datetime.now(UTC) + timedelta(hours=1),
        },
    )
    return raw


def _is_revoked(session, raw_token: str) -> bool:
    """Read ``is_revoked`` for ``raw_token`` with SQL, not the ORM."""
    return session.execute(
        text("SELECT is_revoked FROM oauth2_tokens WHERE token_hash = :h"),
        {"h": hash_token(raw_token)},
    ).scalar_one()


@pytest.fixture
def seeded(Session):
    """Two independent clients, each holding one live token.

    Two clients rather than one because the sharper half of this finding is
    cross-client: authenticating *some* client must not grant introspection or
    revocation of *another* client's tokens.
    """
    session = Session()
    try:
        client_a = _seed_client(session)
        client_b = _seed_client(session)
        token_a = _seed_token(session, client_a, user_id=111)
        token_b = _seed_token(session, client_b, user_id=222)
        session.commit()
        yield {
            "client_a": client_a,
            "client_b": client_b,
            "token_a": token_a,
            "token_b": token_b,
        }
    finally:
        # Archive-free cleanup: these are synthetic test fixtures in a
        # verification database, not platform business entities.
        for cid in (client_a, client_b):
            session.execute(
                text("DELETE FROM oauth2_tokens WHERE client_id = :c"), {"c": cid}
            )
            session.execute(
                text("DELETE FROM oauth2_clients WHERE client_id = :c"), {"c": cid}
            )
        session.commit()
        session.close()


# ---------------------------------------------------------------------------
# Unauthenticated callers
# ---------------------------------------------------------------------------


def test_introspect_refuses_an_unauthenticated_caller(Session, seeded):
    """A caller with a valid token value but no credentials gets 401, not data."""
    with harness.client(Session, None) as api:
        response = api.post("/oauth2/introspect", json={"token": seeded["token_a"]})

    assert response.status_code == 401, response.text
    # The body must not carry the token's metadata even alongside the rejection.
    assert "user_id" not in response.text


def test_revoke_refuses_an_unauthenticated_caller_and_commits_nothing(Session, seeded):
    """The denial of service is the point: the row must survive the attempt."""
    with harness.client(Session, None) as api:
        response = api.post("/oauth2/revoke", json={"token": seeded["token_a"]})

    assert response.status_code == 401, response.text

    session = Session()
    try:
        assert _is_revoked(session, seeded["token_a"]) is False
    finally:
        session.close()


def test_introspect_refuses_a_wrong_client_secret(Session, seeded):
    with harness.client(Session, None) as api:
        response = api.post(
            "/oauth2/introspect",
            json={
                "token": seeded["token_a"],
                "client_id": seeded["client_a"],
                "client_secret": "not-the-secret",
            },
        )

    assert response.status_code == 401, response.text


# ---------------------------------------------------------------------------
# The authenticated client keeps working -- the fix must not be a denial
# ---------------------------------------------------------------------------


def test_authenticated_client_introspects_its_own_token(Session, seeded):
    """Guarding the endpoint must not break its legitimate use."""
    with harness.client(Session, None) as api:
        response = api.post(
            "/oauth2/introspect",
            json={
                "token": seeded["token_a"],
                "client_id": seeded["client_a"],
                "client_secret": _SECRET,
            },
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["active"] is True
    assert body["client_id"] == seeded["client_a"]
    assert body["user_id"] == 111


def test_authenticated_client_revokes_its_own_token(Session, seeded):
    with harness.client(Session, None) as api:
        response = api.post(
            "/oauth2/revoke",
            json={
                "token": seeded["token_a"],
                "client_id": seeded["client_a"],
                "client_secret": _SECRET,
            },
        )

    assert response.status_code == 200, response.text

    session = Session()
    try:
        assert _is_revoked(session, seeded["token_a"]) is True
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Cross-client isolation
# ---------------------------------------------------------------------------


def test_client_cannot_introspect_another_clients_token(Session, seeded):
    """Client A authenticates correctly, then asks about client B's token.

    RFC 7662 says to answer ``active: false`` rather than an error, so the
    endpoint does not become an oracle for which tokens exist under some other
    client.  The assertion is therefore on the *absence of B's metadata*, not on
    a status code.
    """
    with harness.client(Session, None) as api:
        response = api.post(
            "/oauth2/introspect",
            json={
                "token": seeded["token_b"],
                "client_id": seeded["client_a"],
                "client_secret": _SECRET,
            },
        )

    assert response.status_code == 200, response.text
    assert response.json() == {"active": False}
    assert seeded["client_b"] not in response.text
    assert "222" not in response.text


def test_client_cannot_revoke_another_clients_token(Session, seeded):
    """RFC 7009 §2.2 answers 200 regardless -- so the row is the only evidence."""
    with harness.client(Session, None) as api:
        response = api.post(
            "/oauth2/revoke",
            json={
                "token": seeded["token_b"],
                "client_id": seeded["client_a"],
                "client_secret": _SECRET,
            },
        )

    assert response.status_code == 200, response.text

    session = Session()
    try:
        assert _is_revoked(session, seeded["token_b"]) is False
    finally:
        session.close()


# ---------------------------------------------------------------------------
# POST /oauth2/register -- client registration is a privileged operation
# ---------------------------------------------------------------------------
#
# PORTED finding (NR-067/NR-068). This route had only ``get_current_user``, so any
# authenticated user of any role could register an OAuth2 client with
# attacker-chosen ``redirect_uris``.  That client then receives real users'
# access, refresh and id tokens the moment anyone completes ``/authorize``
# against it -- token theft by registration, not by interception.
#
# ``OAuth2Client`` carries no tenant column at all, by design: the registry is
# platform-global.  That is precisely why the gate has to be a role check rather
# than a tenant scope.


def _register_payload(name: str) -> dict:
    return {
        "client_name": name,
        "redirect_uris": ["https://attacker.example/callback"],
        "allowed_scopes": ["openid"],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
    }


@harness.requires_postgres()
def test_a_non_admin_cannot_register_an_oauth2_client(Session):
    """A lab technician is authenticated, and that must not be enough."""
    actor = harness.Actor(user_id=1, lab_id=1, role="lab_technician")
    with harness.client(Session, actor) as api:
        response = api.post("/oauth2/register", json=_register_payload("Rogue Client"))

    assert response.status_code == 403, response.text
    # The secret must not leak alongside the refusal.
    assert "client_secret" not in response.text


@harness.requires_postgres()
def test_an_admin_can_still_register_and_the_registration_is_audited(Session):
    """The gate must not disable the capability, and must leave a trail."""
    actor = harness.Actor(user_id=1, lab_id=1, role="admin")
    with harness.client(Session, actor) as api:
        response = api.post("/oauth2/register", json=_register_payload("Legitimate Client"))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["client_id"]
    assert body["client_secret"]

    session = Session()
    try:
        row = session.execute(
            text(
                "SELECT user_id, user_role, resource_type, details "
                "FROM audit_logs WHERE action = 'oauth2.client.registered' "
                "ORDER BY id DESC LIMIT 1"
            )
        ).fetchone()
        assert row is not None, "registering a client wrote no audit row"
        user_id, user_role, resource_type, details = row
        assert user_id == 1
        assert user_role == "admin"
        assert resource_type == "oauth2_client"
        # The redirect_uris are the security-relevant part of the record.
        assert "attacker.example" in details
        # The plaintext secret must never reach the audit trail.
        assert body["client_secret"] not in (details or "")
    finally:
        # Archive rather than delete: deactivate the client this test created.
        session.execute(
            text("UPDATE oauth2_clients SET is_active = false WHERE client_id = :c"),
            {"c": body["client_id"]},
        )
        session.commit()
        session.close()
