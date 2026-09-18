"""NR-046 — an expired NIAM session still authenticated.

`get_current_niam_actor` in app/identity/api/workspaces.py is the canonical
actor dependency: it guards every `/niam/*` route and the clinical gateway. Its
filter checked Account.status, Account.is_active, Account.is_locked,
UserSession.token_jti and UserSession.is_active -- and never
UserSession.expires_at, which is NOT NULL and set at login.

Nothing reaps `is_active` when a session expires, so the row stays
is_active=True indefinitely. Executed against real PostgreSQL before the fix: a
session whose expires_at was thirty days in the past authenticated.

This was a CONTROL COVERAGE gap rather than a missing control. Two other call
sites already enforced the same rule:

    authentication_service.py:118   not session.is_active or session.expires_at <  now
    authorization_decision.py:220   not session.is_active or session.expires_at <= now

The one place that did not was the one guarding the whole router. That is the
inverse pattern the operating brief names: a correct mechanism that is not
applied at every reachable entry point.

A note on how this was proved, because it nearly went the other way. The first
probe reported all three sessions rejected -- including the valid control --
which would have read as "expired sessions are already refused, no defect". The
cause was the probe, not the code: `create_token` mints its own `jti` and
overwrites any passed in, so the session row never matched the token. Without a
valid-session control in the same run, the wrong conclusion would have been
recorded as evidence. Both directions are asserted below for that reason.
"""

from __future__ import annotations

import ast
import pathlib
import uuid as _uuid
from datetime import datetime, timedelta

import pytest
from app._compat import UTC
from app.identity.api import workspaces as ws
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

_SOURCE = pathlib.Path(ws.__file__)


def _actor_filter_source() -> str:
    """The text of get_current_niam_actor's query filter."""
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "get_current_niam_actor":
            return ast.unparse(node)
    raise AssertionError("get_current_niam_actor not found")


def test_the_actor_dependency_constrains_session_expiry():
    """Structural: the filter must name expires_at at all."""
    src = _actor_filter_source()
    assert "expires_at" in src, (
        "get_current_niam_actor does not constrain UserSession.expires_at, so a "
        "session row that expired long ago still authenticates for as long as "
        "the bearer token lives. Nothing reaps is_active on expiry."
    )


def test_the_expiry_comparison_is_against_now_not_a_constant():
    src = _actor_filter_source()
    assert "UserSession.expires_at >" in src, (
        "the expiry constraint must require expires_at to be in the FUTURE; "
        f"found no `UserSession.expires_at >` in:\n{src}"
    )
    assert "datetime.now(UTC)" in src, (
        "the comparison must be against the current time in UTC"
    )


#: The call sites that enforce session expiry. MAY GROW; must never shrink --
#: an entry disappearing means a path stopped checking that a session is live.
DECLARED_EXPIRY_ENFORCERS = {
    "app/identity/api/workspaces.py",
    "app/identity/services/authentication_service.py",
    "app/identity/services/authorization_decision.py",
}

_APP = pathlib.Path(ws.__file__).resolve().parent.parent.parent


def _files_constraining_session_expiry() -> set[str]:
    found: set[str] = set()
    files = sorted(_APP.rglob("*.py"))
    assert len(files) > 400, f"source scan looks vacuous ({len(files)} files)"
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if "expires_at" not in text or "session" not in text.lower():
            continue
        if "UserSession.expires_at" in text or "session.expires_at" in text:
            found.add(str(path.relative_to(_APP.parent)))
    return found


def test_no_path_stops_enforcing_session_expiry():
    current = _files_constraining_session_expiry()
    lost = DECLARED_EXPIRY_ENFORCERS - current
    assert not lost, (
        "these files no longer constrain session expiry — a live-session check "
        "was removed:\n  " + "\n  ".join(sorted(lost))
    )


# ── behavioural, against whatever database the suite is configured with ───────


@pytest.fixture
def identity_fixture():
    """An active account with no session yet. Rolled back; leaves no rows.

    Builds its own engine from MIGRATION_DATABASE_URL/DATABASE_URL rather than
    using app.database.SessionLocal, because the suite's conftest pins that to
    an in-memory SQLite where the niam_* tables do not exist. These two tests
    therefore run in the PostgreSQL migration job, and are deselected by the
    unit job's `-m "not integration"`.
    """
    import os

    pytest.importorskip("psycopg2")
    url = os.getenv("MIGRATION_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
    if not url.startswith(("postgresql://", "postgresql+psycopg2://")):
        pytest.skip("needs PostgreSQL; the niam_* tables are not built on SQLite")

    from app.identity.models.account import Account
    from app.identity.models.identity import IdentityRecord
    from app.identity.models.person import Person
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(url.replace("postgresql://", "postgresql+psycopg2://", 1))
    db = sessionmaker(bind=engine)()
    try:
        now = datetime.now(UTC)
        person = Person(uuid=str(_uuid.uuid4()))
        for attr, val in (("full_name", "Guard"), ("given_name", "G"),
                          ("family_name", "Guard"), ("person_type", "citizen"),
                          ("status", "active"), ("is_active", True)):
            if hasattr(person, attr):
                setattr(person, attr, val)
        db.add(person)
        db.flush()
        identity = IdentityRecord(
            uuid=str(_uuid.uuid4()), person_id=person.id, identity_type="human",
            status="active", issued_at=now, is_active=True,
        )
        db.add(identity)
        db.flush()
        account = Account(
            uuid=str(_uuid.uuid4()), identity_id=identity.id,
            email=f"guard-{_uuid.uuid4().hex[:8]}@invalid.test", status="active",
            is_active=True, is_locked=False, password_hash="x",
            username=f"g{_uuid.uuid4().hex[:8]}",
        )
        db.add(account)
        db.flush()
        yield db, account, now
    finally:
        db.rollback()
        db.close()
        engine.dispose()


def _authenticate_with_session(db, account, expires_at) -> str:
    """Mint a token, attach a session with the given expiry, call the dependency."""
    from app.identity.models.session import UserSession
    from app.security.auth import create_token, decode_token

    token = create_token({"account_uuid": account.uuid, "sub": str(account.id)})
    # create_token mints its OWN jti and discards any passed in; read it back
    # rather than assuming, which is what made the first probe of this defect
    # report a false negative.
    jti = decode_token(token)["jti"]
    db.add(UserSession(uuid=str(_uuid.uuid4()), account_id=account.id,
                       token_jti=jti, is_active=True, expires_at=expires_at))
    db.flush()

    class _Req:
        headers: dict = {}
        cookies: dict = {}

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    try:
        ws.get_current_niam_actor(_Req(), creds, db)
        return "authenticated"
    except HTTPException as exc:
        return f"rejected:{exc.status_code}"


@pytest.mark.integration
def test_an_expired_session_does_not_authenticate(identity_fixture):
    db, account, now = identity_fixture
    assert _authenticate_with_session(db, account, now - timedelta(days=30)) == "rejected:401"
    assert _authenticate_with_session(db, account, now - timedelta(seconds=1)) == "rejected:401"


@pytest.mark.integration
def test_a_live_session_still_authenticates(identity_fixture):
    """The control. Without it, a probe that rejects everything reads as a pass."""
    db, account, now = identity_fixture
    assert _authenticate_with_session(db, account, now + timedelta(hours=1)) == "authenticated"
    assert _authenticate_with_session(db, account, now + timedelta(seconds=30)) == "authenticated"
