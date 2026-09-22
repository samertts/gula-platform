"""Regression guard: /service-accounts route-level authorization.

app/routes/service_accounts.py (create/list/rotate/revoke) is gated by a
role check (master_admin/admin only) and, for non-master_admin callers,
a lab_id scope enforced inside app/security/service_accounts.py's
rotate_api_key/revoke_service_account (both filter the target row by
lab_id when the caller is not a master_admin). This was verified by
direct code read during Authorization Coverage Batch 3, but had no
route-level test proving the cross-tenant and role-denial cases (the
existing coverage in test_auth_infrastructure.py only exercises the
single-lab admin happy path). This file closes that specific evidence
gap -- no production code changed.
"""
from __future__ import annotations

import pytest

from app.security.auth import create_token

_AUTH = "Bearer {}"


@pytest.fixture()
def lab_a(make_lab):
    return make_lab(name="Lab A")


@pytest.fixture()
def lab_b(make_lab):
    return make_lab(name="Lab B")


@pytest.fixture()
def lab_a_admin_token(db, make_lab_user, lab_a):
    user = make_lab_user(lab_id=lab_a.id, role="admin")
    db.commit()
    return create_token({"user_id": user.id, "lab_id": user.lab_id, "role": "admin"})


@pytest.fixture()
def lab_a_tech_token(db, make_lab_user, lab_a):
    user = make_lab_user(lab_id=lab_a.id, role="lab_tech")
    db.commit()
    return create_token({"user_id": user.id, "lab_id": user.lab_id, "role": "lab_tech"})


@pytest.fixture()
def master_admin_token(db, make_lab_user, lab_a):
    # master_admin's own lab_id is irrelevant to its authority -- the route
    # bypasses lab scoping purely on role, never on this field being null.
    user = make_lab_user(lab_id=lab_a.id, role="master_admin")
    db.commit()
    return create_token({"user_id": user.id, "lab_id": user.lab_id, "role": "master_admin"})


def _create_sa(client, token, name="sa"):
    resp = client.post(
        "/service-accounts",
        json={"name": name, "description": "test", "roles": ["viewer"], "scopes": ["patients:read"]},
        headers={"Authorization": _AUTH.format(token)},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def test_non_admin_role_denied_create(client, lab_a_tech_token):
    resp = client.post(
        "/service-accounts",
        json={"name": "denied-sa", "roles": ["viewer"], "scopes": []},
        headers={"Authorization": _AUTH.format(lab_a_tech_token)},
    )
    assert resp.status_code == 403


def test_lab_admin_cannot_set_foreign_lab_id(client, lab_a_admin_token, lab_b):
    resp = client.post(
        "/service-accounts",
        json={"name": "spoofed-sa", "roles": ["viewer"], "scopes": [], "lab_id": lab_b.id},
        headers={"Authorization": _AUTH.format(lab_a_admin_token)},
    )
    assert resp.status_code == 403


def test_lab_a_admin_cannot_rotate_lab_b_service_account(
    client, db, lab_a_admin_token, make_lab_user, lab_b,
):
    lab_b_admin = make_lab_user(lab_id=lab_b.id, role="admin")
    db.commit()
    lab_b_admin_token = create_token(
        {"user_id": lab_b_admin.id, "lab_id": lab_b_admin.lab_id, "role": "admin"},
    )
    sa_id = _create_sa(client, lab_b_admin_token, name="lab-b-sa")

    resp = client.post(
        f"/service-accounts/{sa_id}/rotate",
        headers={"Authorization": _AUTH.format(lab_a_admin_token)},
    )
    assert resp.status_code == 404


def test_lab_a_admin_cannot_revoke_lab_b_service_account(
    client, db, lab_a_admin_token, make_lab_user, lab_b,
):
    lab_b_admin = make_lab_user(lab_id=lab_b.id, role="admin")
    db.commit()
    lab_b_admin_token = create_token(
        {"user_id": lab_b_admin.id, "lab_id": lab_b_admin.lab_id, "role": "admin"},
    )
    sa_id = _create_sa(client, lab_b_admin_token, name="lab-b-sa-2")

    resp = client.delete(
        f"/service-accounts/{sa_id}",
        headers={"Authorization": _AUTH.format(lab_a_admin_token)},
    )
    assert resp.status_code == 404


def test_master_admin_can_rotate_any_labs_service_account(
    client, db, lab_a_admin_token, master_admin_token,
):
    sa_id = _create_sa(client, lab_a_admin_token, name="lab-a-sa")

    resp = client.post(
        f"/service-accounts/{sa_id}/rotate",
        headers={"Authorization": _AUTH.format(master_admin_token)},
    )
    assert resp.status_code == 200, resp.text
    assert "api_key" in resp.json()


def test_unauthenticated_requests_rejected(client):
    assert client.get("/service-accounts").status_code == 401
    assert client.post("/service-accounts", json={"name": "x"}).status_code == 401
    assert client.delete("/service-accounts/1").status_code == 401
    assert client.post("/service-accounts/1/rotate").status_code == 401
