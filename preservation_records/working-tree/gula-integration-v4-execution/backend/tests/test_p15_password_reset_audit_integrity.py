"""P-15 / AUD-F17 — password-reset audit integrity regression tests.

Synthetic credentials only. All execution is in the isolated SQLite test DB;
no production identity store, real token, PHI or secret is used.

Required behaviour: credential-lifecycle audit rows are written in the same
transaction as the credential mutation and failures are observable (fail
closed), never silently swallowed after commit.
"""

from __future__ import annotations

import ast
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from app._compat import UTC
from app.models.audit_log import AuditLog
from app.routes import password_reset as reset_routes
from app.services.audit_service import verify_audit_chain

from shared.auth.passwords import hash_password

ROUTES_PATH = Path(__file__).resolve().parents[1] / "app" / "routes" / "password_reset.py"
RAW_TOKEN = "synthetic-reset-token-not-a-secret-7f3a"


def _is_suppress_context(expr: ast.expr) -> bool:
    return (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Attribute)
        and expr.func.attr == "suppress"
        and isinstance(expr.func.value, ast.Name)
        and expr.func.value.id == "contextlib"
    )


def _log_action_calls(source: str) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "log_action"
    ]


@pytest.fixture()
def user(db, make_lab_user):
    lab_user = make_lab_user(lab_id=1)
    db.flush()
    return lab_user


def _commit_spy(db, events: list[str]):
    original_commit = db.commit

    def _spy():
        events.append("commit")
        return original_commit()

    return _spy


def test_p15_no_contextlib_suppress_around_audit_calls():
    """AUD-F17: both audit writes were wrapped in a silent contextlib.suppress."""
    tree = ast.parse(ROUTES_PATH.read_text(encoding="utf-8"))
    suppressed = [
        with_node.lineno
        for with_node in ast.walk(tree)
        if isinstance(with_node, ast.With)
        and any(_is_suppress_context(item.context_expr) for item in with_node.items)
        and any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id == "log_action"
            for child in ast.walk(with_node)
        )
    ]
    assert suppressed == [], f"silently suppressed audit calls at lines {suppressed}"


async def test_p15_both_credential_audits_precede_commit(db, user, monkeypatch):
    """Audit flush must happen before the credential commit on both endpoints."""
    events: list[str] = []

    def _audit_spy(*args, **kwargs):
        events.append("audit")

    monkeypatch.setattr(reset_routes, "log_action", _audit_spy)
    monkeypatch.setattr(db, "commit", _commit_spy(db, events))

    await reset_routes.forgot_password(
        SimpleNamespace(email=user.email), db=db, _rate=None,
    )
    user.reset_token = hash_password(RAW_TOKEN)
    user.reset_token_expires = datetime.now(UTC) + timedelta(hours=1)
    db.flush()

    await reset_routes.reset_password(
        SimpleNamespace(token=RAW_TOKEN, new_password="SyntheticPass123!"), db=db, _rate=None,
    )

    assert events == ["audit", "commit", "audit", "commit"], events


async def test_p15_forgot_password_audit_failure_is_not_swallowed(db, user, monkeypatch):
    """A failed audit write must block the token mutation, not vanish."""
    events: list[str] = []

    def _failing_audit(*args, **kwargs):
        events.append("audit")
        raise RuntimeError("synthetic audit outage")

    monkeypatch.setattr(reset_routes, "log_action", _failing_audit)
    monkeypatch.setattr(db, "commit", _commit_spy(db, events))

    with pytest.raises(RuntimeError, match="synthetic audit outage"):
        await reset_routes.forgot_password(
            SimpleNamespace(email=user.email), db=db, _rate=None,
        )

    # The audit call raised and the commit spy never fired: the token mutation
    # is left uncommitted, so the request dependency rolls it back. This is the
    # deterministic fail-closed proof (no silent suppression, no commit).
    assert events == ["audit"], events
    db.rollback()


async def test_p15_reset_password_audit_failure_is_not_swallowed(db, user, monkeypatch):
    """Password mutation and token clearing must roll back on audit failure."""
    user.reset_token = hash_password(RAW_TOKEN)
    user.reset_token_expires = datetime.now(UTC) + timedelta(hours=1)
    db.flush()
    events: list[str] = []

    def _failing_audit(*args, **kwargs):
        events.append("audit")
        raise RuntimeError("synthetic audit outage")

    monkeypatch.setattr(reset_routes, "log_action", _failing_audit)
    monkeypatch.setattr(db, "commit", _commit_spy(db, events))

    with pytest.raises(RuntimeError, match="synthetic audit outage"):
        await reset_routes.reset_password(
            SimpleNamespace(token=RAW_TOKEN, new_password="SyntheticPass123!"), db=db, _rate=None,
        )

    # The audit call raised and the commit spy never fired: the password hash
    # change, token clearing and perm-version bump all remain uncommitted.
    assert events == ["audit"], events
    db.rollback()


async def test_p15_successful_resets_write_chained_audit_rows_without_secrets(db, user):
    """Success writes the two lifecycle rows; neither token nor password is logged."""
    await reset_routes.forgot_password(
        SimpleNamespace(email=user.email), db=db, _rate=None,
    )
    user.reset_token = hash_password(RAW_TOKEN)
    user.reset_token_expires = datetime.now(UTC) + timedelta(hours=1)
    db.flush()
    await reset_routes.reset_password(
        SimpleNamespace(token=RAW_TOKEN, new_password="SyntheticPass123!"), db=db, _rate=None,
    )

    for action in ("password_reset_requested", "password_reset_completed"):
        rows = db.query(AuditLog).filter_by(action=action).all()
        assert len(rows) == 1, (action, rows)
        assert rows[0].resource_type == "password_reset"
        assert rows[0].resource_id == user.id
        assert rows[0].user_id == user.id
        assert rows[0].details is None
    assert verify_audit_chain(db)["verified"] is True


def test_p15_audit_calls_do_not_reference_credentials():
    """Static guard: log_action arguments contain no token or password material."""
    calls = _log_action_calls(ROUTES_PATH.read_text(encoding="utf-8"))
    assert len(calls) == 2
    secret_names = {"token", "new_password", "password", "password_hash", "reset_token"}
    for call in calls:
        keywords = {kw.arg for kw in call.keywords}
        assert {"action", "resource_type", "user_id"} <= keywords
        assert call.args or "db" in keywords
        assert "details" not in keywords
        referenced = [
            node.attr if isinstance(node, ast.Attribute) else node.id
            for node in ast.walk(call)
            if isinstance(node, (ast.Attribute, ast.Name))
        ]
        assert secret_names.isdisjoint(referenced), referenced
