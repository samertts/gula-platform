"""Regression guard: POST /oauth2/register requires an admin role.

OAuth2Client (app/models/oauth2_client.py) is a platform-global registry --
no lab_id/tenant column exists on the model at all, by design. Before this
fix, register_client had only get_current_user: any authenticated LabUser
of any role could register an OAuth2 client with attacker-chosen
redirect_uris, which then receives real users' access/refresh/id tokens
the moment any user completes /authorize against it -- a real-world
open-redirect / token-exfiltration vector on an internal medical platform.
Fixed by reusing this session's established "security configuration"
role-gate convention (service_accounts.py, hospital.py's
_HOSPITAL_ADMIN_ROLES), not a new vocabulary.
"""
from __future__ import annotations

from tests.conftest import auth_headers


def test_register_client_denies_non_admin_role(client, make_lab, make_lab_user):
    lab = make_lab("OAuth2 Register Lab 1")
    staff = make_lab_user(lab.id, role="staff")
    resp = client.post(
        "/oauth2/register",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={"client_name": "rogue-app", "redirect_uris": ["https://evil.example/callback"]},
    )
    assert resp.status_code == 403


def test_register_client_denies_unauthenticated(client):
    resp = client.post(
        "/oauth2/register",
        json={"client_name": "anon-app"},
    )
    assert resp.status_code == 401


def test_register_client_allows_admin_role(client, make_lab, make_lab_user):
    lab = make_lab("OAuth2 Register Lab 2")
    admin = make_lab_user(lab.id, role="admin")
    resp = client.post(
        "/oauth2/register",
        headers=auth_headers(admin.id, lab.id, role="admin"),
        json={"client_name": "legit-app", "redirect_uris": ["https://legit.example/callback"]},
    )
    assert resp.status_code == 200, resp.text
    assert "client_id" in resp.json()
    assert "client_secret" in resp.json()
