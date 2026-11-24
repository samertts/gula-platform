"""Regression tests for national audit-event actor derivation (S-05).

Finding
-------
``POST /governance/audit-events`` was mounted with no authentication and took
``actor_id`` verbatim from the caller. Any anonymous request could therefore
plant an audit record attributed to an arbitrary principal
(CWE-778 insufficient logging / CWE-306 missing authentication).

Policy under test
-----------------
* anonymous                     → 401
* operational non-admin (doctor,
  lab_admin, citizen)           → 403 (national audit writes are operator-only)
* platform operators            → 200, ``actor_id``/``actor_role`` derived from
  (master_admin, ministry_admin,   the authenticated principal
  national_admin)
* caller-supplied ``actor_id``
  that disagrees with the
  principal                     → 403, nothing persisted
* caller-supplied ``actor_id``
  that matches the principal    → accepted (supplying it grants no trust)
"""
from __future__ import annotations

import pytest

from tests.conftest import auth_headers

AUDIT_EVENTS = "/governance/audit-events"


def _headers(user, lab):
    return auth_headers(user.id, lab.id, role=user.role)


def _log(client, headers, event_type="s05.audit", action="s05-action", **params):
    return client.post(
        AUDIT_EVENTS,
        params={"event_type": event_type, "action": action, **params},
        headers=headers,
    )


def _readback(client, headers, event_type="s05.audit"):
    # S-08: reading national audit events is itself an authenticated governance
    # read, so the readback must present the operator credentials.
    return client.get(AUDIT_EVENTS, params={"event_type": event_type, "limit": 200}, headers=headers)


# ── Anonymous: authentication required ───────────────────────────────────────


def test_anonymous_cannot_log_audit_event(client):
    resp = client.post(
        AUDIT_EVENTS,
        params={"event_type": "s05.anon", "action": "forged", "actor_id": "master_admin"},
    )
    assert resp.status_code == 401, resp.text


# ── Authenticated but unauthorized ───────────────────────────────────────────


@pytest.mark.parametrize("role", ["citizen", "doctor", "lab_admin", "lab_staff", "technician"])
def test_non_operator_cannot_log_audit_event(client, make_lab, make_lab_user, role):
    lab = make_lab()
    user = make_lab_user(lab.id, role=role)
    # Authorized reader used only to prove nothing was persisted.
    operator = make_lab_user(lab.id, role="master_admin")
    resp = _log(client, _headers(user, lab), event_type=f"s05.{role}")
    assert resp.status_code == 403, resp.text
    assert _readback(client, _headers(operator, lab), event_type=f"s05.{role}").json() == []


# ── Operator: legitimate workflow works and identity is server-derived ──────


def test_master_admin_logs_event_with_server_derived_actor(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")

    resp = _log(client, _headers(operator, lab), action="policy.updated")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["actor_id"] == operator.email
    assert body["actor_role"] == "master_admin"
    assert body["action"] == "policy.updated"

    rows = _readback(client, _headers(operator, lab)).json()
    assert len(rows) == 1
    assert rows[0]["actor_id"] == operator.email


@pytest.mark.parametrize("role", ["ministry_admin", "national_admin"])
def test_other_platform_operators_can_log_audit_event(client, make_lab, make_lab_user, role):
    lab = make_lab()
    operator = make_lab_user(lab.id, role=role)

    resp = _log(client, _headers(operator, lab), event_type=f"s05.{role}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["actor_id"] == operator.email
    assert resp.json()["actor_role"] == role


# ── Forged actor identity is rejected and not persisted ─────────────────────


def test_forged_actor_id_is_rejected_and_not_persisted(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")

    forged = _log(
        client,
        _headers(operator, lab),
        event_type="s05.forged",
        action="release.approved",
        actor_id="master_admin@national.gov",
    )
    assert forged.status_code == 403, forged.text
    assert "actor_id" in forged.json()["detail"]
    assert _readback(client, _headers(operator, lab), event_type="s05.forged").json() == []


def test_matching_actor_id_is_accepted_without_gaining_trust(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")

    resp = _log(
        client,
        _headers(operator, lab),
        event_type="s05.match",
        actor_id=operator.email,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["actor_id"] == operator.email
