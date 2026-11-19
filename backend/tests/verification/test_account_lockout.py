"""Does repeated failed authentication actually lock the account?

WP-004 / NR-025.  ``failed_login_attempts`` and ``locked_until`` are declared by
both ``LabUser`` and ``User``, and were recorded as absent from **both** physical
tables.  That made INV-AUTHN-02 unanswerable rather than false: with nowhere for
the state to live, either the brute-force control was dead or every login that
touched it raised.  Which one was **UNKNOWN**, and the register kept it UNKNOWN
rather than guessing.

Two things changed.  The columns are present on a database built only by
migrations at canonical head, and the control is demonstrably wired: ``routes/login.py``
calls ``is_locked`` before deciding and ``register_failed_login`` after a failure.
So the question is now answerable by execution, which is what this module does.

The property worth proving is not "a counter increments".  It is that **a correct
password is refused while the lock window is open** — a lockout that yields to the
right credential stops no brute-force attack, and the attacker's next guess is the
one that matters.
"""

from __future__ import annotations

import datetime as dt
import os
import subprocess
import uuid
from typing import Any

import pytest
from sqlalchemy import text

from . import harness

pytestmark = harness.requires_postgres()

LAB_ID = 994401
USER_ID = 74401
EMAIL = "lockout.subject@example.test"
PASSWORD = "C0rrect-Horse-Battery!"
WRONG = "not-the-password"
ENDPOINT = "/login"

# ``login_protection`` reads these at import; the defaults are the contract.
THRESHOLD = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))

RESTART_GATE = "GULA_RECOVERY_ALLOW_DB_RESTART"
RESTART_CMD = ["sudo", "pg_ctlcluster", "16", "main", "restart"]


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


@pytest.fixture()
def Session() -> Any:
    S = harness.session_factory(pool_size=4)
    yield S
    harness.dispose(S)


def _purge(S: Any) -> None:
    with S() as s:
        s.execute(text("DELETE FROM lab_users WHERE lab_id = :lab"), {"lab": LAB_ID})
        s.execute(text("DELETE FROM labs WHERE id = :lab"), {"lab": LAB_ID})
        s.commit()


@pytest.fixture()
def account(Session: Any) -> Any:
    """One active lab user with a real bcrypt hash of a known password.

    A ``LabUser`` deliberately, not a citizen ``User``: the citizen path has a
    separate verification gate that would answer before the lockout branch and
    make the result ambiguous. The role is ``technician`` so the privileged-role
    MFA gate does not intercept the success case either.
    """
    from app.security.auth import hash_password

    _purge(Session)
    with Session() as s:
        s.execute(
            text("INSERT INTO labs (id, name, is_active) VALUES (:id, :n, true)"),
            {"id": LAB_ID, "n": "Lockout Proof Lab"},
        )
        s.execute(
            text(
                "INSERT INTO lab_users "
                "(id, lab_id, name, email, password_hash, role, is_active, "
                " failed_login_attempts, perm_version) "
                "VALUES (:id, :lab, :n, :e, :pw, 'technician', true, 0, 1)"
            ),
            {"id": USER_ID, "lab": LAB_ID, "n": "Lockout Subject", "e": EMAIL,
             "pw": hash_password(PASSWORD)},
        )
        s.commit()
    yield
    harness.clear_overrides()
    _purge(Session)


def _login(Session: Any, password: str) -> Any:
    """POST /login with the real authentication dependency in place.

    ``actor=None`` matters: overriding ``get_current_user`` would bypass the very
    code path under test. The ``with`` runs the app lifespan, without which
    ``ReadinessMiddleware`` answers 503 and nothing is proven.
    """
    try:
        with harness.client(Session, None) as client:
            return client.post(ENDPOINT, json={"email": EMAIL, "password": password})
    finally:
        harness.clear_overrides()


def _state(Session: Any) -> dict[str, Any]:
    rows = harness.committed(
        Session,
        "SELECT failed_login_attempts, locked_until FROM lab_users WHERE id = :id",
        id=USER_ID,
    )
    assert rows, "the seeded account disappeared"
    return rows[0]


def _audit_actions(Session: Any) -> list[str]:
    """Authentication audit rows for this subject, keyed by ``user_id``.

    Deliberately **not** filtered by ``lab_id``: these rows carry ``lab_id IS NULL``
    even though the subject belongs to a lab.  Measured, not assumed — see
    ``test_authentication_audit_rows_are_not_tenant_scoped``, which pins it.  A
    ``lab_id`` filter here silently returns nothing and makes the audit assertions
    pass vacuously, which is exactly what happened on the first run of this module.
    """
    return [
        r["action"]
        for r in harness.committed(
            Session,
            "SELECT action FROM audit_logs WHERE user_id = :uid AND action LIKE 'login%' "
            "ORDER BY id",
            uid=USER_ID,
        )
    ]


def test_authentication_audit_rows_are_not_tenant_scoped(Session: Any, account: Any) -> None:
    """Pin a fact found while writing this module, without calling it a defect.

    A failed login produces an audit row that records the user and their role but
    leaves ``lab_id`` NULL.  Whether that is right is a governance question this
    test does not answer: authentication happens before workspace resolution, so a
    platform-level event is defensible.  What is not defensible is *not knowing*.

    The consequence is concrete either way: a lab administrator querying their own
    tenant's audit trail sees no authentication events for their own staff, and any
    per-tenant brute-force report built on ``lab_id`` would read as silence.
    """
    assert _login(Session, WRONG).status_code == 401
    rows = harness.committed(
        Session,
        "SELECT lab_id, user_id, user_role, action FROM audit_logs "
        "WHERE user_id = :uid AND action LIKE 'login%' ORDER BY id",
        uid=USER_ID,
    )
    assert rows, "a failed login produced no audit row at all"
    assert all(r["lab_id"] is None for r in rows), (
        "authentication audit rows have become tenant-scoped — good, but the "
        f"finding recorded here is now stale and must be re-measured: {rows}"
    )
    assert all(r["user_id"] == USER_ID and r["user_role"] == "technician" for r in rows), (
        f"the actor is not identified on the audit row: {rows}"
    )


# ---------------------------------------------------------------------------
# The schema question NR-025 left open
# ---------------------------------------------------------------------------


def test_the_lockout_columns_exist_in_the_migrated_database(Session: Any) -> None:
    """Read from the database, not from the ORM's opinion of it.

    This is the assertion that turns NR-025 from UNKNOWN into answerable: with the
    columns absent, everything below could only have produced a 500.
    """
    for table in ("lab_users", "users"):
        columns = harness.physical_columns(Session, table)
        missing = {"failed_login_attempts", "locked_until"} - columns
        assert missing == set(), f"{table} still lacks {sorted(missing)}"


# ---------------------------------------------------------------------------
# INV-AUTHN-02
# ---------------------------------------------------------------------------


def test_repeated_failed_logins_lock_the_account(Session: Any, account: Any) -> None:
    """The counter rises and the deadline is set once the threshold is reached."""
    for attempt in range(1, THRESHOLD + 1):
        response = _login(Session, WRONG)
        assert response.status_code == 401, (
            f"attempt {attempt} answered {response.status_code}: {response.text}"
        )

    state = _state(Session)
    assert state["failed_login_attempts"] >= THRESHOLD, state
    assert state["locked_until"] is not None, "the threshold was reached but no lock was set"
    assert state["locked_until"] > _now(), (
        f"the lock deadline is already in the past: {state['locked_until']}"
    )
    assert "login_lockout_started" in _audit_actions(Session), (
        f"the lockout was not audited; actions were {_audit_actions(Session)}"
    )


def test_the_correct_password_is_refused_while_the_lock_window_is_open(
    Session: Any, account: Any
) -> None:
    """The property that makes a lockout worth having.

    A control that still accepts the right password during the window stops no
    brute-force attack — the attacker's next guess is exactly the one that must
    not be honoured.
    """
    for _ in range(THRESHOLD):
        assert _login(Session, WRONG).status_code == 401
    assert _state(Session)["locked_until"] > _now()

    denied = _login(Session, PASSWORD)
    assert denied.status_code == 401, (
        f"the correct password was accepted while locked: {denied.status_code} {denied.text}"
    )
    # Indistinguishable from a wrong password, so the lock does not leak that the
    # credential was in fact correct.
    assert denied.json().get("detail") == _login(Session, WRONG).json().get("detail"), (
        "the lockout response differs from the wrong-password response, which tells "
        "an attacker they guessed correctly"
    )
    assert "login_denied_lockout" in _audit_actions(Session)


def test_when_the_window_expires_the_correct_password_is_accepted_again(
    Session: Any, account: Any
) -> None:
    """Expiry is enforced, and a successful login clears the counter.

    The passage of time is simulated by moving the stored deadline into the past.
    What is under test is whether the deadline is *enforced*, not whether the clock
    advances — waiting fifteen real minutes would test the clock and nothing else.
    """
    for _ in range(THRESHOLD):
        assert _login(Session, WRONG).status_code == 401
    assert _state(Session)["locked_until"] > _now()

    with Session() as s:
        s.execute(
            text("UPDATE lab_users SET locked_until = :past WHERE id = :id"),
            {"past": _now() - dt.timedelta(minutes=1), "id": USER_ID},
        )
        s.commit()

    response = _login(Session, PASSWORD)
    assert response.status_code != 401, (
        f"the correct password was still refused after the window closed: "
        f"{response.status_code} {response.text}"
    )
    assert _state(Session)["failed_login_attempts"] == 0, (
        "a successful login left the failure counter standing, so the next few "
        "wrong guesses would relock the account immediately"
    )


@pytest.mark.skipif(
    os.environ.get(RESTART_GATE) != "1",
    reason=(
        f"{RESTART_GATE}=1 not set. This test restarts the PostgreSQL cluster, which is "
        "destructive to every database on the instance, so it never runs by default. "
        "A skip here is NOT evidence that the lock survives a restart."
    ),
)
def test_the_lock_survives_a_database_restart(Session: Any, account: Any) -> None:
    """INV-AUTHN-02 says the lock survives a restart; this is that clause.

    An in-memory lock would evaporate with the process, handing an attacker a
    clean slate for the cost of one outage.
    """
    for _ in range(THRESHOLD):
        assert _login(Session, WRONG).status_code == 401
    before = _state(Session)
    assert before["locked_until"] > _now()

    harness.dispose(Session)
    subprocess.run(RESTART_CMD, check=True, capture_output=True, timeout=120)

    After = harness.session_factory(pool_size=4)
    try:
        assert After().execute(text("SELECT 1")).scalar_one() == 1
        after = _state(After)
        assert after == before, f"the lock state changed across the restart: {before} -> {after}"
        denied = _login(After, PASSWORD)
        assert denied.status_code == 401, (
            f"after the restart the lock no longer held: {denied.status_code}"
        )
    finally:
        harness.clear_overrides()
        harness.dispose(After)
