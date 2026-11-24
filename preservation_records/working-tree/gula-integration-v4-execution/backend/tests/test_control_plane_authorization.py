"""Regression tests for Control Plane authorization (S-01) and the release
approval workflow (S-02).

Security properties under test
------------------------------
S-01 — every control-plane endpoint must *authorize*, not merely authenticate:
  * anonymous                     → 401 (never reaches the handler)
  * authenticated but unprivileged → 403
  * platform/national read roles   → allowed on read endpoints
  * platform operator only         → allowed on write endpoints

S-02 — release deployment must not trust caller-controlled identity:
  * caller-supplied ``user``/``approve_first``/``approved_by``/``deployed_by``
    are rejected with 400;
  * a release must be explicitly approved before deployment;
  * approval and deployment must be performed by different principals
    (two-person rule);
  * the recorded approver/deployer are derived from the authenticated actor.
"""
from __future__ import annotations

import pytest
from tests.conftest import auth_headers

READ_PATH = "/control-plane/registry/components"
# ``POST /policies/evaluate`` is a non-mutating evaluation and is classified as
# a read, so it exercises login without changing control-plane state.
POST_READ_PATH = "/control-plane/policies/evaluate"
WRITE_PATH = "/control-plane/releases"


def _headers(user, lab):
    return auth_headers(user.id, lab.id, role=user.role)


# ── S-01: anonymous access ────────────────────────────────────────────────────


def test_control_plane_read_anonymous_is_rejected(client):
    resp = client.get(READ_PATH)
    assert resp.status_code == 401


def test_control_plane_write_anonymous_is_rejected(client):
    resp = client.post("/control-plane/releases", json={"name": "x", "version": "1.0.0"})
    assert resp.status_code == 401


# ── S-01: authenticated but unauthorized ──────────────────────────────────────


def test_control_plane_read_citizen_is_forbidden(client, make_lab, make_lab_user):
    lab = make_lab()
    citizen = make_lab_user(lab.id, role="citizen")
    resp = client.get(READ_PATH, headers=_headers(citizen, lab))
    assert resp.status_code == 403


def test_control_plane_write_citizen_is_forbidden(client, make_lab, make_lab_user):
    lab = make_lab()
    citizen = make_lab_user(lab.id, role="citizen")
    resp = client.post(
        "/control-plane/releases",
        json={"name": "x", "version": "1.0.0"},
        headers=_headers(citizen, lab),
    )
    assert resp.status_code == 403


def test_control_plane_read_lab_admin_is_forbidden(client, make_lab, make_lab_user):
    """A laboratory administrator is not a platform operator."""
    lab = make_lab()
    admin = make_lab_user(lab.id, role="admin")
    resp = client.get(READ_PATH, headers=_headers(admin, lab))
    assert resp.status_code == 403


def test_control_plane_write_ministry_admin_is_forbidden(client, make_lab, make_lab_user):
    """National oversight may read the control plane but not mutate it."""
    lab = make_lab()
    ministry = make_lab_user(lab.id, role="ministry_admin")
    resp = client.post(
        WRITE_PATH,
        json={"name": "forbidden-write", "version": "1.0.0"},
        headers=_headers(ministry, lab),
    )
    assert resp.status_code == 403


# ── S-01: authorized actors ───────────────────────────────────────────────────


@pytest.mark.parametrize("role", ["master_admin", "ministry_admin"])
def test_control_plane_read_platform_roles_allowed(client, make_lab, make_lab_user, role):
    lab = make_lab()
    user = make_lab_user(lab.id, role=role)
    resp = client.get(READ_PATH, headers=_headers(user, lab))
    assert resp.status_code == 200


def test_control_plane_non_mutating_post_allowed_for_reader(client, make_lab, make_lab_user):
    lab = make_lab()
    ministry = make_lab_user(lab.id, role="ministry_admin")
    resp = client.post(
        POST_READ_PATH,
        json={"action": "anything", "context": {}},
        headers=_headers(ministry, lab),
    )
    assert resp.status_code == 200


def test_control_plane_write_master_admin_allowed(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    resp = client.post(
        WRITE_PATH,
        json={"name": "operator-authorized-write", "version": "1.0.0"},
        headers=_headers(operator, lab),
    )
    assert resp.status_code == 200


# ── S-02: caller-controlled identity is rejected ─────────────────────────────


def _create_release(client, lab, operator, name):
    resp = client.post(
        "/control-plane/releases",
        json={"name": name, "version": "1.0.0", "component": name},
        headers=_headers(operator, lab),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["release_id"]


def test_deploy_rejects_caller_supplied_user(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    release_id = _create_release(client, lab, operator, "s02-user-field")
    resp = client.post(
        "/control-plane/releases/deploy",
        json={"release_id": release_id, "user": "attacker@example.com"},
        headers=_headers(operator, lab),
    )
    assert resp.status_code == 400
    assert "user" in resp.json()["detail"]


def test_deploy_rejects_approve_first_flag(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    release_id = _create_release(client, lab, operator, "s02-approve-first")
    resp = client.post(
        "/control-plane/releases/deploy",
        json={"release_id": release_id, "approve_first": True},
        headers=_headers(operator, lab),
    )
    assert resp.status_code == 400
    assert "approve_first" in resp.json()["detail"]


def test_deploy_unapproved_release_is_conflict(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    release_id = _create_release(client, lab, operator, "s02-unapproved")
    resp = client.post(
        "/control-plane/releases/deploy",
        json={"release_id": release_id},
        headers=_headers(operator, lab),
    )
    assert resp.status_code == 409


def test_deploy_missing_release_id_is_rejected(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    resp = client.post(
        "/control-plane/releases/deploy",
        json={},
        headers=_headers(operator, lab),
    )
    assert resp.status_code == 400


# ── S-02: approval workflow + two-person rule ────────────────────────────────


def test_approve_unknown_release_is_404(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    resp = client.post(
        "/control-plane/releases/does-not-exist/approve",
        headers=_headers(operator, lab),
    )
    assert resp.status_code == 404


def test_approve_anonymous_is_rejected(client):
    resp = client.post("/control-plane/releases/anything/approve")
    assert resp.status_code == 401


def test_approve_citizen_is_forbidden(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    citizen = make_lab_user(lab.id, role="citizen")
    release_id = _create_release(client, lab, operator, "s02-approve-citizen")
    resp = client.post(
        f"/control-plane/releases/{release_id}/approve",
        headers=_headers(citizen, lab),
    )
    assert resp.status_code == 403


def test_self_approval_then_self_deploy_is_blocked(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    release_id = _create_release(client, lab, operator, "s02-two-person")

    approved = client.post(
        f"/control-plane/releases/{release_id}/approve",
        headers=_headers(operator, lab),
    )
    assert approved.status_code == 200
    assert approved.json()["approved_by"] == operator.email

    # Same principal approving and deploying violates separation of duties.
    resp = client.post(
        "/control-plane/releases/deploy",
        json={"release_id": release_id},
        headers=_headers(operator, lab),
    )
    assert resp.status_code == 409
    assert "two-person" in resp.json()["detail"]


def test_independent_approver_then_deployer_succeeds(client, make_lab, make_lab_user):
    lab = make_lab()
    approver = make_lab_user(lab.id, role="master_admin")
    deployer = make_lab_user(lab.id, role="master_admin")
    release_id = _create_release(client, lab, approver, "s02-independent")

    approved = client.post(
        f"/control-plane/releases/{release_id}/approve",
        json={"user": "forged@example.com"},
        headers=_headers(approver, lab),
    )
    assert approved.status_code == 200
    # Body-supplied identity must never influence the recorded approver.
    assert approved.json()["approved_by"] == approver.email

    deployed = client.post(
        "/control-plane/releases/deploy",
        json={"release_id": release_id},
        headers=_headers(deployer, lab),
    )
    assert deployed.status_code == 200, deployed.text
    body = deployed.json()
    assert body["status"] == "deployed"
    assert body["approved_by"] == approver.email
    assert body["deployed_by"] == deployer.email


def test_reapproving_deployed_release_is_conflict(client, make_lab, make_lab_user):
    lab = make_lab()
    approver = make_lab_user(lab.id, role="master_admin")
    deployer = make_lab_user(lab.id, role="master_admin")
    release_id = _create_release(client, lab, approver, "s02-reapprove")

    client.post(
        f"/control-plane/releases/{release_id}/approve",
        headers=_headers(approver, lab),
    )
    deployed = client.post(
        "/control-plane/releases/deploy",
        json={"release_id": release_id},
        headers=_headers(deployer, lab),
    )
    assert deployed.status_code == 200

    resp = client.post(
        f"/control-plane/releases/{release_id}/approve",
        headers=_headers(approver, lab),
    )
    assert resp.status_code == 409


def test_unprivileged_actor_cannot_deploy(client, make_lab, make_lab_user):
    lab = make_lab()
    approver = make_lab_user(lab.id, role="master_admin")
    admin = make_lab_user(lab.id, role="admin")
    release_id = _create_release(client, lab, approver, "s02-unprivileged-deploy")
    client.post(
        f"/control-plane/releases/{release_id}/approve",
        headers=_headers(approver, lab),
    )
    resp = client.post(
        "/control-plane/releases/deploy",
        json={"release_id": release_id},
        headers=_headers(admin, lab),
    )
    assert resp.status_code == 403
