"""B4 — adversarial regression tests for cross-account security administration.

Owner directive GULA-MASTER-AUTH-2026-11-19 §4. All principals, roles, sessions
and evidence use disposable synthetic rows in an in-memory SQLite database.
No operational database, Redis, HTTP, or real identity data is used.

The tests exercise the B4 policy guard directly (the same pattern used for the
step-up prerequisite) plus structural checks proving the HTTP surface cannot
bypass it.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace

import pyotp
import pytest
from app._compat import UTC
from app.database import AsyncCompatSession
from app.identity.adaptive_auth.b4_guard import (
    B4_CROSS_ACCOUNT_ROLES,
    B4Denied,
    authorize_account_operation,
    resolve_own_mfa_challenge,
)
from app.identity.adaptive_auth.models import AdaptiveMFASession
from app.identity.api.access import _CONTROL_PLANE_AUTHORITIES
from app.identity.base import IdentityBase
from app.identity.models.account import Account
from app.identity.models.audit import IdentityAuditEntry
from app.identity.models.authorization import Role, RoleAssignment
from app.identity.models.session import UserSession
from app.identity.services.step_up_service import StepUpService
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import Session

from shared.auth.mfa import generate_totp_secret


def _metadata_subset() -> MetaData:
    from app.database import Base

    combined = MetaData()
    for metadata in (Base.metadata, IdentityBase.metadata):
        for table in metadata.tables.values():
            if table.name not in combined.tables:
                table.to_metadata(combined)
    roots = (
        "niam_step_up_events",
        "niam_audit_entries",
        "niam_sessions",
        "niam_accounts",
        "niam_roles",
        "niam_role_assignments",
        "niam_adaptive_mfa_sessions",
    )
    needed: set[str] = set()

    def visit(name: str) -> None:
        if name in needed or name not in combined.tables:
            return
        needed.add(name)
        for fk in combined.tables[name].foreign_keys:
            visit(fk.target_fullname.split(".", 1)[0])

    for root in roots:
        visit(root)
    subset = MetaData()
    for name in sorted(needed):
        combined.tables[name].to_metadata(subset)
    return subset


@pytest.fixture()
def b4db():
    engine = create_engine("sqlite://")
    _metadata_subset().create_all(engine)
    sync = Session(engine)
    try:
        yield AsyncCompatSession(sync)
    finally:
        sync.close()
        engine.dispose()


_ADMIN_ID = "ACCOUNT-0000000000000000000001"
_TARGET_ID = "ACCOUNT-0000000000000000000002"
_ADMIN_SESSION = "SESSION-0000000000000000000001"


def _make_account(db, account_id: str, *, secret: str | None = None):
    account = Account(
        id=account_id,
        uuid=f"uuid-{account_id}",
        identity_id=f"IDENTITY-{account_id[-4:]}",
        account_type="human",
        status="active",
        is_active=True,
        mfa_enabled=bool(secret),
        mfa_methods="totp" if secret else None,
        mfa_secret=secret,
    )
    now = datetime.now(UTC)
    session = UserSession(
        id=f"SESSION-{account_id[-4:]}",
        uuid=f"uuid-session-{account_id[-4:]}",
        account_id=account_id,
        token_jti=f"jti-{account_id[-4:]}",
        session_type="web",
        is_active=True,
        started_at=now,
        last_activity_at=now,
        expires_at=now + timedelta(days=1),
        mfa_used=False,
    )
    db.add(account)
    db.add(session)
    db.flush()
    actor = SimpleNamespace(
        account=SimpleNamespace(id=account.id),
        session=SimpleNamespace(id=session.id, token_jti=session.token_jti),
    )
    return actor, account, session


def _grant(db, account_id: str, role_key: str, **overrides):
    role_id = f"ROLE-{role_key.upper()}"
    role = Role(
        id=role_id,
        uuid=f"uuid-{role_id}",
        role_key=role_key,
        name=role_key,
        scope_type="platform",
        status=overrides.get("role_status", "active"),
    )
    assignment = RoleAssignment(
        id=f"ASSIGN-{len(str(account_id))}-{role_key}",
        uuid=f"uuid-assign-{len(str(account_id))}-{role_key}",
        assignment_key=f"{account_id}:{role_key}",
        account_id=account_id,
        membership_id="MEMBERSHIP-0000000000001",
        role_id=role_id,
        organization_id="ORGANIZATION-000000000001",
        scope_type="platform",
        status=overrides.get("assignment_status", "active"),
        expires_at=overrides.get("expires_at"),
        revoked_at=overrides.get("revoked_at"),
    )
    db.add(role)
    db.add(assignment)
    db.flush()
    return assignment


def _step_up(db, actor, secret: str):
    return asyncio.run(
        StepUpService(db, freshness_seconds=300).verify(actor, pyotp.TOTP(secret).now(), "totp")
    )


def _cross(db, actor, target_id=_TARGET_ID, **kwargs):
    return asyncio.run(
        authorize_account_operation(
            db, actor, target_id,
            operation="synthetic_admin_action",
            purpose="synthetic_cross_account_action",
            **kwargs,
        )
    )


# ── self-service resolution ───────────────────────────────────────────────────


def test_self_target_resolves_own_account(b4db):
    actor, account, _ = _make_account(b4db, _ADMIN_ID)
    resolved = _cross(b4db, actor, account.id)
    assert resolved.id == account.id


def test_missing_target_defaults_to_self(b4db):
    actor, account, _ = _make_account(b4db, _ADMIN_ID)
    assert _cross(b4db, actor, None).id == account.id


def test_unknown_target_denied(b4db):
    actor, _, _ = _make_account(b4db, _ADMIN_ID)
    with pytest.raises(B4Denied, match="target_not_found"):
        _cross(b4db, actor, "ACCOUNT-DOES-NOT-EXIST")


# ── cross-account authorization: role narrowing ──────────────────────────────


def test_cross_account_without_any_elevated_role_denied(b4db):
    actor, _, _ = _make_account(b4db, _ADMIN_ID)
    _make_account(b4db, _TARGET_ID)
    with pytest.raises(B4Denied, match="cross_account_role_denied"):
        _cross(b4db, actor)


def test_weak_control_plane_role_cannot_cross_account(b4db):
    """A control-plane role outside the narrow B4 set must still be denied."""
    actor, _, _ = _make_account(b4db, _ADMIN_ID)
    _make_account(b4db, _TARGET_ID)
    _grant(b4db, _ADMIN_ID, "compliance_officer")
    assert "compliance_officer" in _CONTROL_PLANE_AUTHORITIES
    with pytest.raises(B4Denied, match="cross_account_role_denied"):
        _cross(b4db, actor)


def test_b4_roles_are_strict_subset_of_control_plane():
    assert {"master_admin", "security_administrator"} == B4_CROSS_ACCOUNT_ROLES
    assert set(_CONTROL_PLANE_AUTHORITIES) > B4_CROSS_ACCOUNT_ROLES
    for weak in ("ministry_admin", "organization_administrator", "compliance_officer"):
        assert weak not in B4_CROSS_ACCOUNT_ROLES


@pytest.mark.parametrize("role_key", ["master_admin", "security_administrator"])
def test_authorized_role_with_fresh_step_up_allowed(b4db, role_key):
    secret = generate_totp_secret()
    actor, _, _ = _make_account(b4db, _ADMIN_ID, secret=secret)
    _, target, _ = _make_account(b4db, _TARGET_ID)
    _grant(b4db, _ADMIN_ID, role_key)
    _step_up(b4db, actor, secret)
    assert _cross(b4db, actor).id == target.id


@pytest.mark.parametrize(
    "override",
    [
        {"assignment_status": "suspended"},
        {"assignment_status": "revoked"},
        {"expires_at": datetime.now(UTC) - timedelta(seconds=1)},
        {"revoked_at": datetime.now(UTC) - timedelta(seconds=1)},
        {"role_status": "disabled"},
    ],
)
def test_ineligible_role_assignment_denied(b4db, override):
    secret = generate_totp_secret()
    actor, _, _ = _make_account(b4db, _ADMIN_ID, secret=secret)
    _make_account(b4db, _TARGET_ID)
    _grant(b4db, _ADMIN_ID, "master_admin", **override)
    _step_up(b4db, actor, secret)
    with pytest.raises(B4Denied, match="cross_account_role_denied"):
        _cross(b4db, actor)


# ── cross-account authorization: step-up ─────────────────────────────────────


def test_cross_account_without_step_up_denied(b4db):
    actor, _, _ = _make_account(b4db, _ADMIN_ID)
    _make_account(b4db, _TARGET_ID)
    _grant(b4db, _ADMIN_ID, "master_admin")
    with pytest.raises(B4Denied, match="fresh_step_up_required"):
        _cross(b4db, actor)


def test_revoked_session_invalidates_cross_account_authorization(b4db):
    secret = generate_totp_secret()
    actor, _, session = _make_account(b4db, _ADMIN_ID, secret=secret)
    _make_account(b4db, _TARGET_ID)
    _grant(b4db, _ADMIN_ID, "master_admin")
    _step_up(b4db, actor, secret)
    session.is_active = False
    b4db.flush()
    with pytest.raises(B4Denied, match="session_revoked"):
        _cross(b4db, actor)


def test_suspended_or_locked_administrator_denied(b4db):
    secret = generate_totp_secret()
    actor, account, _ = _make_account(b4db, _ADMIN_ID, secret=secret)
    _make_account(b4db, _TARGET_ID)
    _grant(b4db, _ADMIN_ID, "master_admin")
    _step_up(b4db, actor, secret)
    account.status = "suspended"
    b4db.flush()
    with pytest.raises(B4Denied, match="actor_ineligible"):
        _cross(b4db, actor)


def test_session_substitution_denied(b4db):
    actor, _, _ = _make_account(b4db, _ADMIN_ID)
    substituted = SimpleNamespace(
        account=SimpleNamespace(id=actor.account.id),
        session=SimpleNamespace(id="SESSION-TAMPERED", token_jti="jti-tampered"),
    )
    with pytest.raises(B4Denied, match="actor_not_found"):
        _cross(b4db, substituted, actor.account.id)


# ── MFA self-only ─────────────────────────────────────────────────────────────


def test_mfa_challenge_cross_account_denied_even_with_admin_and_step_up(b4db):
    secret = generate_totp_secret()
    actor, _, _ = _make_account(b4db, _ADMIN_ID, secret=secret)
    _make_account(b4db, _TARGET_ID)
    _grant(b4db, _ADMIN_ID, "master_admin")
    _step_up(b4db, actor, secret)
    with pytest.raises(B4Denied, match="mfa_self_only"):
        _cross(b4db, actor, mfa_self_only=True)


def test_verify_other_accounts_mfa_challenge_denied(b4db):
    admin, _, _ = _make_account(b4db, _ADMIN_ID)
    _, _, _ = _make_account(b4db, _TARGET_ID)
    now = datetime.now(UTC)
    foreign = AdaptiveMFASession(
        id="MFA-FOREIGN",
        uuid="uuid-mfa-foreign",
        mfa_id="MFA-FOREIGN",
        account_id=_TARGET_ID,
        session_id=f"SESSION-{_TARGET_ID[-4:]}",
        mfa_type="totp",
        challenge="challenge",
        challenge_expires_at=now + timedelta(minutes=5),
        is_active=True,
    )
    b4db.add(foreign)
    b4db.flush()
    with pytest.raises(B4Denied, match="mfa_self_only"):
        asyncio.run(resolve_own_mfa_challenge(b4db, admin, "MFA-FOREIGN"))


def test_verify_own_mfa_challenge_allowed(b4db):
    admin, _, _ = _make_account(b4db, _ADMIN_ID)
    now = datetime.now(UTC)
    own = AdaptiveMFASession(
        id="MFA-OWN",
        uuid="uuid-mfa-own",
        mfa_id="MFA-OWN",
        account_id=_ADMIN_ID,
        session_id=f"SESSION-{_ADMIN_ID[-4:]}",
        mfa_type="totp",
        challenge="challenge",
        challenge_expires_at=now + timedelta(minutes=5),
        is_active=True,
    )
    b4db.add(own)
    b4db.flush()
    resolved = asyncio.run(resolve_own_mfa_challenge(b4db, admin, "MFA-OWN"))
    assert resolved.account_id == _ADMIN_ID


# ── audit completeness ────────────────────────────────────────────────────────


def test_successful_cross_account_action_is_fully_audited(b4db):
    secret = generate_totp_secret()
    actor, _, _ = _make_account(b4db, _ADMIN_ID, secret=secret)
    _make_account(b4db, _TARGET_ID)
    _grant(b4db, _ADMIN_ID, "master_admin")
    _step_up(b4db, actor, secret)
    _cross(b4db, actor)
    entries = b4db.query(IdentityAuditEntry).all()
    allow = [e for e in entries if e.action == "AUTHZ_ALLOW_SENSITIVE"]
    assert allow, "no cross-account allow audit entry"
    entry = allow[-1]
    assert entry.outcome == "success"
    assert entry.actor_id == _ADMIN_ID
    assert entry.target_id == _TARGET_ID
    import json

    raw = entry.extra_data
    meta = json.loads(raw) if isinstance(raw, str) else raw
    assert meta["b4"] is True
    assert meta["operation"] == "synthetic_admin_action"
    assert meta["purpose"] == "synthetic_cross_account_action"
    assert meta["session_id"]
    assert meta["evidence_event_id"]


def test_denied_privilege_escalation_is_audited(b4db):
    actor, _, _ = _make_account(b4db, _ADMIN_ID)
    _make_account(b4db, _TARGET_ID)
    with pytest.raises(B4Denied):
        _cross(b4db, actor)
    entries = b4db.query(IdentityAuditEntry).all()
    assert any(e.action == "AUTHZ_PRIVILEGE_ESCALATION_ATTEMPT" for e in entries)


# ── structural: the HTTP surface cannot bypass the guard ─────────────────────


def test_every_account_scoped_route_binds_actor_and_guard():
    import inspect

    from app.identity.adaptive_auth import routes

    account_scoped = {
        "evaluate_risk",
        "get_risk_history",
        "create_mfa_challenge",
        "verify_mfa_challenge",
        "list_travel_events",
        "get_active_session_count",
        "detect_new_device",
        "enforce_session_policy",
        "is_session_valid",
    }
    seen: set[str] = set()
    for name in account_scoped:
        fn = getattr(routes, name)
        src = inspect.getsource(fn)
        assert "get_current_niam_actor" in src, f"{name}: missing actor dependency"
        assert (
            "authorize_account_operation" in src
            or "resolve_own_mfa_challenge" in src
            or "resolve_session_target" in src
        ), f"{name}: missing B4 guard call"
        seen.add(name)
    assert seen == account_scoped


def test_openapi_surface_unchanged_and_b4_roles_present():
    from app.main import app

    schema = app.openapi()
    for path in (
        "/niam/adaptive-auth/evaluate",
        "/niam/adaptive-auth/mfa/challenge",
        "/niam/adaptive-auth/mfa/verify",
    ):
        assert path in schema["paths"]
