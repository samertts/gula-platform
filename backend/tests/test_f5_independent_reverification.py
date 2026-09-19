"""Independent re-verification of the F5 fix (commit c84171ea).

This does NOT assume c84171ea is correct because it passed the tests written
alongside it (test_rbac_tenant_scope.py). It re-derives the property matrix
from scratch and adds coverage that file did not have:

  - E/F: master_admin / ministry_admin cross-lab management must still be
    ALLOWED (the fix must not have over-corrected into a blanket lab check).
  - J: can_manage_user() is a pure function — call it directly with
    duck-typed actor/target objects, bypassing routes, DB sessions, and JWTs
    entirely. If the scope check ever moved into the route handler instead of
    the shared predicate, or depends on some route-only side channel, this
    catches it. This is the strongest form of "direct invocation cannot
    bypass the scope check": there is no HTTP layer here to bypass.

Route-level E/F also carry DB-state runtime proof (before/after), consistent
with the rest of the F5 evidence trail.
"""
from __future__ import annotations

from types import SimpleNamespace

from app.security.rbac import can_manage_user
from tests.conftest import auth_headers


# ── J: direct function invocation, no HTTP/DB layer at all ─────────────────

def _actor(role, lab_id=1, province_id=None):
    return SimpleNamespace(role=role, lab_id=lab_id, province_id=province_id)


def _target(role, lab_id=1, province_id=None):
    return SimpleNamespace(role=role, lab_id=lab_id, province_id=province_id)


def test_j_direct_admin_same_lab_allowed():
    actor = _actor("admin", lab_id=1)
    target = _target("staff", lab_id=1)
    assert can_manage_user(actor, target) is True


def test_j_direct_admin_cross_lab_denied():
    actor = _actor("admin", lab_id=1)
    target = _target("staff", lab_id=2)
    assert can_manage_user(actor, target) is False


def test_j_direct_lab_admin_cross_lab_denied():
    """lab_admin is the alias role that motivated the original F5 report."""
    actor = _actor("lab_admin", lab_id=1)
    target = _target("staff", lab_id=2)
    assert can_manage_user(actor, target) is False


def test_j_direct_province_admin_same_province_allowed_regardless_of_lab():
    """province_admin scope is by province, not lab — must not regress into
    an accidental lab check that would break legitimate multi-lab province
    administration."""
    actor = _actor("province_admin", lab_id=1, province_id=7)
    target = _target("admin", lab_id=999, province_id=7)
    assert can_manage_user(actor, target) is True


def test_j_direct_province_admin_different_province_denied():
    actor = _actor("province_admin", lab_id=1, province_id=7)
    target = _target("admin", lab_id=1, province_id=8)
    assert can_manage_user(actor, target) is False


def test_j_direct_master_admin_any_lab_allowed():
    actor = _actor("master_admin", lab_id=1)
    target = _target("province_admin", lab_id=999)
    assert can_manage_user(actor, target) is True


def test_j_direct_ministry_admin_any_lab_allowed():
    actor = _actor("ministry_admin", lab_id=1)
    target = _target("admin", lab_id=999)
    assert can_manage_user(actor, target) is True


def test_j_direct_missing_actor_lab_id_denied_not_treated_as_wildcard():
    """A malformed/incomplete actor object (lab_id missing/None) must be
    denied, never treated as 'no scope restriction'. Guards against a future
    refactor introducing `actor.lab_id == target.lab_id` where a None==None
    coincidence would silently grant cross-tenant access if both sides were
    unset."""
    actor = _actor("admin", lab_id=None)
    target = _target("staff", lab_id=None)
    assert can_manage_user(actor, target) is False


def test_j_hierarchy_still_enforced_within_same_lab():
    """The lab_id fix must not have weakened the pre-existing role-hierarchy
    gate: same-lab does not mean 'anything goes'."""
    actor = _actor("staff", lab_id=1)  # staff has no manage_users permission,
    target = _target("admin", lab_id=1)  # but even if it reached this
    assert can_manage_user(actor, target) is False  # function, hierarchy denies it


# ── E/F: route-level, master_admin / ministry_admin cross-lab must still work ─

def test_e_master_admin_can_toggle_user_in_any_lab(client, db, make_lab, make_lab_user):
    lab_a = make_lab()
    lab_b = make_lab()
    master = make_lab_user(lab_a.id, role="master_admin")
    target = make_lab_user(lab_b.id, role="admin", is_active=True)
    db.commit()
    before_active = target.is_active

    resp = client.put(
        f"/admin/users/{target.id}/toggle",
        headers=auth_headers(master.id, lab_a.id, role="master_admin"),
    )
    assert resp.status_code == 200

    db.expire(target)
    fresh = db.query(type(target)).filter(type(target).id == target.id).first()
    assert fresh.is_active != before_active  # actually toggled — proves ALLOWED, not silently ignored


def test_f_ministry_admin_can_change_role_in_any_lab(client, db, make_lab, make_lab_user):
    lab_a = make_lab()
    lab_b = make_lab()
    ministry = make_lab_user(lab_a.id, role="ministry_admin")
    target = make_lab_user(lab_b.id, role="admin")
    db.commit()

    resp = client.patch(
        f"/admin/users/{target.id}/role",
        json={"role": "technician"},
        headers=auth_headers(ministry.id, lab_a.id, role="ministry_admin"),
    )
    assert resp.status_code == 200

    db.expire(target)
    fresh = db.query(type(target)).filter(type(target).id == target.id).first()
    assert fresh.role == "technician"
