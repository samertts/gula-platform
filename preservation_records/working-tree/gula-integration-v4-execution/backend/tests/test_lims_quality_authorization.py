"""Regression tests for anonymous access to ISO 15189 quality indicators (S-12).

Finding
-------
Two ``/lims`` quality-indicator routes ran without authentication (CWE-306):

* ``GET  /lims/quality/indicators``                     — indicator catalogue
* ``POST /lims/quality/indicators/{indicator_id}/evaluate`` — pure computation

Neither reads or writes tenant data, so the impact was informational/compute
disclosure rather than data loss. The fix is the same authentication contract
used by every other ``/lims`` route: a valid ``LabUser`` principal.

Policy under test
-----------------
* Anonymous → 401 on both routes.
* An authenticated lab user keeps access and receives the real payload → 200.
* Unknown indicator still resolves to 404 for an authenticated caller (the
  authorization guard must not change the handler's own error semantics).
"""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers

INDICATORS_GET = "/lims/quality/indicators"
INDICATORS_EVALUATE = "/lims/quality/indicators/specimen_rejection_rate/evaluate"


def _headers(user, lab):
    return auth_headers(user.id, lab.id, role=user.role)


# ── Anonymous: authentication required ──────────────────────────────────────


def test_anonymous_quality_indicators_require_authentication(client):
    get_resp = client.get(INDICATORS_GET)
    assert get_resp.status_code == 401, f"GET -> {get_resp.status_code}: {get_resp.text[:200]}"

    post_resp = client.post(INDICATORS_EVALUATE, params={"value": 1.5})
    assert post_resp.status_code == 401, f"POST -> {post_resp.status_code}: {post_resp.text[:200]}"


# ── Legitimate workflow: authenticated lab users keep access ────────────────


@pytest.mark.parametrize("role", ["technician", "doctor", "lab_admin"])
def test_authenticated_lab_user_can_read_and_evaluate(client, make_lab, make_lab_user, role):
    lab = make_lab()
    user = make_lab_user(lab.id, role=role)
    headers = _headers(user, lab)

    listed = client.get(INDICATORS_GET, headers=headers)
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert "iso_15189" in body and "cap" in body
    assert any(i["id"] == "specimen_rejection_rate" for i in body["iso_15189"])

    evaluated = client.post(INDICATORS_EVALUATE, params={"value": 1.5}, headers=headers)
    assert evaluated.status_code == 200, evaluated.text
    result = evaluated.json()
    assert result["indicator_id"] == "specimen_rejection_rate"
    assert result["status"] == "passed"  # 1.5% < 2% target


def test_unknown_indicator_still_returns_404_for_authenticated_caller(client, make_lab, make_lab_user):
    lab = make_lab()
    user = make_lab_user(lab.id, role="technician")
    headers = _headers(user, lab)

    resp = client.post("/lims/quality/indicators/not_a_real_indicator/evaluate", params={"value": 1.0}, headers=headers)
    assert resp.status_code == 404, resp.text
