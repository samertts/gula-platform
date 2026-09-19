"""F5 closure proof: can_manage_user() must not let a lab-scoped admin
(role="admin"/"lab_admin") reach users in another lab.

Runtime proof for properties A-J (per MUSTAFA_MILESTONE_VERIFICATION_LOG.md /
MUSTAFA_ACTIVE_REPAIR_QUEUE.md F5 entry). Every "denied" assertion inspects
database state before and after the request — a 403 alone is not accepted as
proof that no mutation occurred.
"""
from __future__ import annotations

from types import SimpleNamespace

from app.models.lab_user import LabUser
from app.security.rbac import can_manage_user

from tests.conftest import auth_headers


def _refresh(db, user: LabUser) -> LabUser:
    db.expire(user)
    return db.query(LabUser).filter(LabUser.id == user.id).first()


# ── A/B: toggle_user tenant scope ────────────────────────────────────────────

def test_a_admin_can_toggle_user_in_own_lab(client, db, make_lab, make_lab_user):
    lab_a = make_lab()
    admin_a = make_lab_user(lab_a.id, role="admin")
    target = make_lab_user(lab_a.id, role="staff", is_active=True)
    db.commit()

    resp = client.put(
        f"/admin/users/{target.id}/toggle",
        headers=auth_headers(admin_a.id, lab_a.id, role="admin"),
    )
    assert resp.status_code == 200

    fresh = _refresh(db, target)
    assert fresh.is_active is False


def test_b_admin_cannot_toggle_user_in_other_lab(client, db, make_lab, make_lab_user):
    lab_a = make_lab()
    lab_b = make_lab()
    admin_a = make_lab_user(lab_a.id, role="admin")
    target = make_lab_user(lab_b.id, role="staff", is_active=True)
    db.commit()

    resp = client.put(
        f"/admin/users/{target.id}/toggle",
        headers=auth_headers(admin_a.id, lab_a.id, role="admin"),
    )
    assert resp.status_code == 403

    # No side effect: target must still be active, unchanged.
    fresh = _refresh(db, target)
    assert fresh.is_active is True
    assert fresh.perm_version == 1


# ── C/D/E/F: change_user_role tenant scope + denial-before-mutation ─────────

def test_c_admin_can_change_role_in_own_lab(client, db, make_lab, make_lab_user):
    lab_a = make_lab()
    admin_a = make_lab_user(lab_a.id, role="admin")
    target = make_lab_user(lab_a.id, role="staff")
    db.commit()

    resp = client.patch(
        f"/admin/users/{target.id}/role",
        json={"role": "technician"},
        headers=auth_headers(admin_a.id, lab_a.id, role="admin"),
    )
    assert resp.status_code == 200

    fresh = _refresh(db, target)
    assert fresh.role == "technician"


def test_d_e_f_admin_cannot_change_role_in_other_lab_and_no_side_effect(
    client, db, make_lab, make_lab_user
):
    lab_a = make_lab()
    lab_b = make_lab()
    admin_a = make_lab_user(lab_a.id, role="admin")
    target = make_lab_user(lab_b.id, role="staff")
    db.commit()
    original_role = target.role
    original_perm_version = target.perm_version

    resp = client.patch(
        f"/admin/users/{target.id}/role",
        json={"role": "technician"},
        headers=auth_headers(admin_a.id, lab_a.id, role="admin"),
    )
    # D: denied
    assert resp.status_code == 403

    fresh = _refresh(db, target)
    # E: role unchanged
    assert fresh.role == original_role
    # F: sessions unchanged — perm_version was never bumped, so any token
    # issued to the target before this attempt is still valid.
    assert fresh.perm_version == original_perm_version

    still_valid = client.get(
        "/admin/audit-logs",
        headers=auth_headers(target.id, lab_b.id, role=fresh.role),
    )
    assert still_valid.status_code != 401


# ── G: province_admin scope reaches only permitted descendants ─────────────

def test_g_province_admin_scoped_to_own_province(client, db, make_lab, make_lab_user):
    lab_a = make_lab()
    lab_b = make_lab()
    prov_admin = make_lab_user(lab_a.id, role="province_admin")
    in_province = make_lab_user(lab_a.id, role="admin")
    out_of_province = make_lab_user(lab_b.id, role="admin")
    prov_admin.province_id = 1
    in_province.province_id = 1
    out_of_province.province_id = 2
    db.commit()

    ok = client.put(
        f"/admin/users/{in_province.id}/toggle",
        headers=auth_headers(prov_admin.id, lab_a.id, role="province_admin"),
    )
    assert ok.status_code == 200

    denied = client.put(
        f"/admin/users/{out_of_province.id}/toggle",
        headers=auth_headers(prov_admin.id, lab_a.id, role="province_admin"),
    )
    assert denied.status_code == 403
    fresh = _refresh(db, out_of_province)
    assert fresh.is_active is True


# ── H: client-supplied identifiers cannot expand authority ──────────────────

def test_h_client_supplied_province_id_cannot_expand_authority(
    client, db, make_lab, make_lab_user
):
    lab_a = make_lab()
    lab_b = make_lab()
    admin_a = make_lab_user(lab_a.id, role="admin")
    target = make_lab_user(lab_b.id, role="staff")
    db.commit()

    # Attacker tries to smuggle an unrelated client-controlled field into the
    # body hoping it influences server-side scoping. The route model only
    # accepts `role` and `province_id`; neither is ever used to decide tenant
    # scope (that comes solely from server-loaded actor/target lab_id).
    resp = client.patch(
        f"/admin/users/{target.id}/role",
        json={"role": "technician", "province_id": 999},
        headers=auth_headers(admin_a.id, lab_a.id, role="admin"),
    )
    assert resp.status_code == 403
    fresh = _refresh(db, target)
    assert fresh.role == "staff"
    assert fresh.province_id != 999


# ── I: missing/invalid actor context cannot grant authority ─────────────────

def test_i_missing_auth_context_is_denied(client, db, make_lab, make_lab_user):
    lab_a = make_lab()
    target = make_lab_user(lab_a.id, role="staff", is_active=True)
    db.commit()

    resp = client.put(f"/admin/users/{target.id}/toggle")
    assert resp.status_code in (401, 403)

    fresh = _refresh(db, target)
    assert fresh.is_active is True


# ── J: URL/object id cannot be used to escape tenant scope (IDOR) ───────────

def test_j_idor_via_path_user_id_is_denied(client, db, make_lab, make_lab_user):
    lab_a = make_lab()
    lab_b = make_lab()
    admin_a = make_lab_user(lab_a.id, role="admin")
    victim = make_lab_user(lab_b.id, role="staff", is_active=True)
    db.commit()

    for candidate_id in (victim.id, victim.id + 999999):
        resp = client.put(
            f"/admin/users/{candidate_id}/toggle",
            headers=auth_headers(admin_a.id, lab_a.id, role="admin"),
        )
        assert resp.status_code in (403, 404)

    fresh = _refresh(db, victim)
    assert fresh.is_active is True


# ── Added on independent verification of the ported fix ──────────────────────
# The eight properties above all pass with the `is not None` guard removed from
# can_manage_user, so that guard was carrying no test weight. Without it the
# comparison becomes None == None, and an actor holding no lab at all matches
# any target that also holds none. The guard is the difference between "same
# lab" and "neither has a lab", which is not the same statement.



def test_an_actor_with_no_lab_cannot_manage_a_user_with_no_lab():
    actor = SimpleNamespace(role="admin", lab_id=None, province_id=None)
    target = SimpleNamespace(role="lab_tech", lab_id=None, province_id=None)
    assert can_manage_user(actor, target) is False, (
        "two users who merely both lack a lab are not in the same lab; without "
        "the `is not None` guard this is None == None and returns True"
    )


def test_an_actor_with_no_lab_cannot_manage_a_user_in_a_lab():
    actor = SimpleNamespace(role="admin", lab_id=None, province_id=None)
    target = SimpleNamespace(role="lab_tech", lab_id=7, province_id=None)
    assert can_manage_user(actor, target) is False


def test_an_actor_in_a_lab_cannot_manage_a_user_with_no_lab():
    actor = SimpleNamespace(role="admin", lab_id=7, province_id=None)
    target = SimpleNamespace(role="lab_tech", lab_id=None, province_id=None)
    assert can_manage_user(actor, target) is False


def test_same_lab_still_allowed_positive_control():
    """Without this the three denials above could pass for the wrong reason."""
    actor = SimpleNamespace(role="admin", lab_id=7, province_id=None)
    target = SimpleNamespace(role="lab_tech", lab_id=7, province_id=None)
    assert can_manage_user(actor, target) is True


def test_platform_roles_keep_their_elevated_scope():
    target = SimpleNamespace(role="lab_tech", lab_id=7, province_id=3)
    for role in ("master_admin", "ministry_admin"):
        actor = SimpleNamespace(role=role, lab_id=None, province_id=None)
        assert can_manage_user(actor, target) is True, (
            f"{role} must keep cross-lab reach; the lab check must not narrow it"
        )
