"""Regression tests for NIAM identity-registry authorization (S-03).

Before remediation ``/niam/persons``, ``/niam/sessions`` and ``/niam/devices``
had no guard at all: anonymous callers could create/read person PII, terminate
sessions and register/trust/revoke devices.

The tests below cover the four required cases:

* anonymous              → 401
* authenticated, no right → 403
* privilege escalation    → 403 (reader role cannot mutate; machine identity is
  not implicitly trusted)
* authorized              → dependency-level allow (HTTP handlers require the
  ``niam_*`` schema, which is intentionally absent from the reduced test DB)

The retired ``/niam/accounts`` routes must keep returning 410 and stay exactly
as they were (no new authentication wall in front of a retired surface).
"""
from __future__ import annotations

import pytest
from app.identity.api.access import (
    require_niam_registry_reader,
    require_niam_registry_writer,
)
from app.identity.models.account import Account
from fastapi import HTTPException
from tests.conftest import auth_headers

PERSON_GET = "/niam/persons/00000000-0000-0000-0000-000000000000"
PERSON_CREATE = "/niam/persons/?given_name=A&family_name=B"
SESSION_LIST = "/niam/sessions/account/acc-1"
SESSION_TERMINATE = "/niam/sessions/ses-1/terminate?reason=manual"
SESSION_TERMINATE_ALL = "/niam/sessions/account/acc-1/terminate-all?reason=manual"
DEVICE_REGISTER = "/niam/devices/register?person_uuid=p-1&device_fingerprint=fp-1"
DEVICE_TRUST = "/niam/devices/dev-1/trust"
DEVICE_REVOKE = "/niam/devices/dev-1/revoke"


def _headers(user, lab):
    return auth_headers(user.id, lab.id, role=user.role)


# ── Anonymous: authentication is now required ────────────────────────────────


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", PERSON_GET),
        ("post", PERSON_CREATE),
        ("get", SESSION_LIST),
        ("post", SESSION_TERMINATE),
        ("post", SESSION_TERMINATE_ALL),
        ("post", DEVICE_REGISTER),
        ("post", DEVICE_TRUST),
        ("post", DEVICE_REVOKE),
    ],
)
def test_identity_registry_routes_reject_anonymous(client, method, path):
    resp = getattr(client, method)(path)
    assert resp.status_code == 401, resp.text


# ── Authenticated but unauthorized ───────────────────────────────────────────


def test_citizen_cannot_read_person(client, make_lab, make_lab_user):
    lab = make_lab()
    citizen = make_lab_user(lab.id, role="citizen")
    resp = client.get(PERSON_GET, headers=_headers(citizen, lab))
    assert resp.status_code == 403


def test_citizen_cannot_terminate_session(client, make_lab, make_lab_user):
    lab = make_lab()
    citizen = make_lab_user(lab.id, role="citizen")
    resp = client.post(SESSION_TERMINATE, headers=_headers(citizen, lab))
    assert resp.status_code == 403


def test_lab_admin_cannot_read_person(client, make_lab, make_lab_user):
    """A laboratory administrator is not a national identity operator."""
    lab = make_lab()
    admin = make_lab_user(lab.id, role="admin")
    resp = client.get(PERSON_GET, headers=_headers(admin, lab))
    assert resp.status_code == 403


def test_lab_admin_cannot_trust_device(client, make_lab, make_lab_user):
    lab = make_lab()
    admin = make_lab_user(lab.id, role="admin")
    resp = client.post(DEVICE_TRUST, headers=_headers(admin, lab))
    assert resp.status_code == 403


# ── Privilege escalation: reader must not be able to mutate ──────────────────


def test_ministry_admin_cannot_create_person(client, make_lab, make_lab_user):
    lab = make_lab()
    ministry = make_lab_user(lab.id, role="ministry_admin")
    resp = client.post(PERSON_CREATE, headers=_headers(ministry, lab))
    assert resp.status_code == 403


def test_ministry_admin_cannot_terminate_session(client, make_lab, make_lab_user):
    lab = make_lab()
    ministry = make_lab_user(lab.id, role="ministry_admin")
    resp = client.post(SESSION_TERMINATE_ALL, headers=_headers(ministry, lab))
    assert resp.status_code == 403


def test_ministry_admin_cannot_register_device(client, make_lab, make_lab_user):
    lab = make_lab()
    ministry = make_lab_user(lab.id, role="ministry_admin")
    resp = client.post(DEVICE_REGISTER, headers=_headers(ministry, lab))
    assert resp.status_code == 403


async def test_niam_human_account_has_no_implicit_registry_access():
    """NIAM accounts carry no registry-admin role yet → fail closed."""
    account = Account(account_type="human")
    with pytest.raises(HTTPException) as exc:
        await require_niam_registry_reader(account)
    assert exc.value.status_code == 403


async def test_niam_system_account_is_not_implicitly_trusted():
    """A machine/service identity does not inherit national PII access."""
    account = Account(account_type="system")
    with pytest.raises(HTTPException) as exc:
        await require_niam_registry_writer(account)
    assert exc.value.status_code == 403


# ── Authorized: dependency-level allow ───────────────────────────────────────


async def test_master_admin_is_authorized_reader(make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    assert await require_niam_registry_reader(operator) is operator


async def test_master_admin_is_authorized_writer(make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    assert await require_niam_registry_writer(operator) is operator


async def test_ministry_admin_is_authorized_reader_but_not_writer(make_lab, make_lab_user):
    lab = make_lab()
    ministry = make_lab_user(lab.id, role="ministry_admin")
    assert await require_niam_registry_reader(ministry) is ministry
    with pytest.raises(HTTPException) as exc:
        await require_niam_registry_writer(ministry)
    assert exc.value.status_code == 403


# ── Retired surfaces stay unchanged ──────────────────────────────────────────


def test_retired_account_creation_still_returns_410_anonymously(client):
    resp = client.post("/niam/accounts/")
    assert resp.status_code == 410
