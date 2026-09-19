"""Authorization-sweep finding: /authz delegation, break-glass, and role-
assignment endpoints (backend/app/routes/authorization.py) had a
role-hierarchy-shaped gap — no gap at all, in fact: they required nothing
beyond Depends(get_current_user), so ANY authenticated account of ANY role
could revoke ANY OTHER user's delegation, deactivate ANY OTHER user's
active break-glass session, or grant/revoke ANY role assignment for ANY
user, purely by guessing/enumerating a small sequential integer id.

Surfaced by scripts/security/detect_missing_tenant_scope.py's Mission-2
sweep (see docs/engineering/MUSTAFA_ACTIVE_REPAIR_QUEUE.md, entry
"authz-ownership"). Confirmed non-exploitable for real privilege
escalation TODAY only as a side effect: neither RoleAssignment nor
BreakGlassSession is consulted anywhere in the live JWT/RBAC enforcement
path (get_current_user, require_permission, has_permission) — this table
is written-and-read-back only within authorization_service.py itself. That
does not make the missing check acceptable: it still lets any user write
misattributed governance/audit records for another user today, and would
become an instant, unrestricted privilege-escalation and emergency-access-
tampering vulnerability the moment anything starts consulting these
tables — which the surrounding identity/governance package structure
strongly suggests is the intended direction.

Fix reuses the same "own the resource, or hold a platform permission"
pattern already established elsewhere in this codebase (require_own_lab,
F5's can_manage_user fix) rather than inventing new authorization
architecture:
  - revoke_delegation: caller must be the delegator, the delegate, or hold
    platform:manage_users.
  - deactivate_break_glass: caller must own the session or hold
    platform:manage_users.
  - assign_role / revoke_role_assignment: caller must hold
    platform:manage_users unconditionally (granting/revoking roles has no
    legitimate "self" case).
"""
from __future__ import annotations

from app.models.authorization import BreakGlassSession, Delegation
from app.security.auth import hash_password
from app.models.user import User
from tests.conftest import auth_headers


_user_counter = [0]


def _make_user(db, role="citizen", **overrides):
    _user_counter[0] += 1
    user = User(
        email=overrides.get("email", f"user-{_user_counter[0]}@test.com"),
        password_hash=hash_password("Testpass1"),
        full_name=overrides.get("full_name", "Test User"),
        role=role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()
    return user


# ── revoke_delegation ────────────────────────────────────────────────────────

def test_delegator_can_revoke_their_own_delegation(client, db):
    delegator = _make_user(db, role="citizen")
    delegate = _make_user(db, role="citizen")
    from datetime import datetime, timedelta

    delegation = Delegation(
        delegator_id=delegator.id,
        delegate_id=delegate.id,
        role_id="staff",
        delegation_type="temporary",
        starts_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=1),
        status="active",
    )
    db.add(delegation)
    db.commit()

    resp = client.delete(
        f"/authz/delegations/{delegation.id}",
        headers=auth_headers(delegator.id, 0, role="citizen"),
    )
    assert resp.status_code == 204


def test_unrelated_user_cannot_revoke_someone_elses_delegation(client, db):
    delegator = _make_user(db, role="citizen")
    delegate = _make_user(db, role="citizen")
    attacker = _make_user(db, role="citizen")
    from datetime import datetime, timedelta

    delegation = Delegation(
        delegator_id=delegator.id,
        delegate_id=delegate.id,
        role_id="staff",
        delegation_type="temporary",
        starts_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=1),
        status="active",
    )
    db.add(delegation)
    db.commit()
    delegation_id = delegation.id

    resp = client.delete(
        f"/authz/delegations/{delegation_id}",
        headers=auth_headers(attacker.id, 0, role="citizen"),
    )
    assert resp.status_code == 403

    db.expire(delegation)
    fresh = db.query(Delegation).filter(Delegation.id == delegation_id).first()
    assert fresh.status == "active"  # unchanged: denied before mutation


def test_platform_manager_can_revoke_any_delegation(client, db):
    delegator = _make_user(db, role="citizen")
    delegate = _make_user(db, role="citizen")
    manager = _make_user(db, role="master_admin")
    from datetime import datetime, timedelta

    delegation = Delegation(
        delegator_id=delegator.id,
        delegate_id=delegate.id,
        role_id="staff",
        delegation_type="temporary",
        starts_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=1),
        status="active",
    )
    db.add(delegation)
    db.commit()

    resp = client.delete(
        f"/authz/delegations/{delegation.id}",
        headers=auth_headers(manager.id, 0, role="master_admin"),
    )
    assert resp.status_code == 204


# ── deactivate_break_glass ───────────────────────────────────────────────────

def test_session_owner_can_deactivate_their_own_break_glass_session(client, db):
    from datetime import datetime, timedelta

    holder = _make_user(db, role="doctor")
    session = BreakGlassSession(
        user_id=holder.id,
        emergency_category="cardiac_arrest",
        justification="test",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        status="active",
    )
    db.add(session)
    db.commit()

    resp = client.post(
        f"/authz/break-glass/{session.id}/deactivate",
        headers=auth_headers(holder.id, 0, role="doctor"),
    )
    assert resp.status_code == 200


def test_unrelated_user_cannot_deactivate_someone_elses_break_glass_session(client, db):
    from datetime import datetime, timedelta

    holder = _make_user(db, role="doctor")
    attacker = _make_user(db, role="doctor")
    session = BreakGlassSession(
        user_id=holder.id,
        emergency_category="cardiac_arrest",
        justification="test",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        status="active",
    )
    db.add(session)
    db.commit()
    session_id = session.id

    resp = client.post(
        f"/authz/break-glass/{session_id}/deactivate",
        headers=auth_headers(attacker.id, 0, role="doctor"),
    )
    assert resp.status_code == 403

    db.expire(session)
    fresh = db.query(BreakGlassSession).filter(BreakGlassSession.id == session_id).first()
    assert fresh.status == "active"  # unchanged: denied before mutation


# ── assign_role / revoke_role_assignment ────────────────────────────────────

def test_ordinary_user_cannot_self_assign_a_role(client, db):
    attacker = _make_user(db, role="citizen")
    db.commit()

    resp = client.post(
        "/authz/assignments",
        json={"user_id": attacker.id, "role_id": "master_admin"},
        headers=auth_headers(attacker.id, 0, role="citizen"),
    )
    assert resp.status_code == 403

    from app.models.authorization import RoleAssignment

    assert (
        db.query(RoleAssignment)
        .filter(RoleAssignment.user_id == attacker.id, RoleAssignment.role_id == "master_admin")
        .first()
        is None
    )


def test_platform_manager_can_assign_a_role(client, db):
    manager = _make_user(db, role="master_admin")
    target = _make_user(db, role="citizen")
    db.commit()

    resp = client.post(
        "/authz/assignments",
        json={"user_id": target.id, "role_id": "staff"},
        headers=auth_headers(manager.id, 0, role="master_admin"),
    )
    assert resp.status_code == 201


def test_ordinary_user_cannot_revoke_anothers_role_assignment(client, db):
    from app.models.authorization import RoleAssignment

    target = _make_user(db, role="citizen")
    attacker = _make_user(db, role="citizen")
    assignment = RoleAssignment(user_id=target.id, role_id="staff", status="active")
    db.add(assignment)
    db.commit()

    resp = client.delete(
        f"/authz/assignments/{target.id}/staff",
        headers=auth_headers(attacker.id, 0, role="citizen"),
    )
    assert resp.status_code == 403

    db.expire(assignment)
    fresh = db.query(RoleAssignment).filter(RoleAssignment.id == assignment.id).first()
    assert fresh.status == "active"  # unchanged: denied before mutation
