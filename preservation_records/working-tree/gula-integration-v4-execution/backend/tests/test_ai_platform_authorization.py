"""Regression tests for anonymous access to AI platform internals (S-09).

Finding
-------
Three ``/api/ai`` reads exposed platform internals to anonymous callers
(CWE-200 exposure of sensitive information):

* ``GET /api/ai/operations``   — sandbox operation catalogue
* ``GET /api/ai/providers``    — provider reachability, base URLs, model names
  (also makes the server issue an outbound probe to the configured Ollama host)
* ``GET /api/ai/dataset/status`` — dataset feature-flag state

Policy under test
-----------------
* All three require an authenticated **AI operator**
  (``require_ai_operator``: clinician + administrator roles). Anonymous → 401.
* A ``citizen`` is not an operator → 403.
* A non-clinical operational role (``technician``) is also denied → 403, proving
  the guard is not merely "any authenticated user".
* A ``doctor`` keeps access and receives the real payload → 200.
* ``GET /api/ai/interpret/{token}`` stays public by design (the result token is
  the proof of access) — the change must not over-guard it.
"""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers

# Every guarded AI-internals read.
AI_INTERNALS: list[str] = [
    "/api/ai/operations",
    "/api/ai/providers",
    "/api/ai/dataset/status",
]

# Payload keys that prove the handler actually ran (not short-circuited).
PAYLOAD_KEYS: dict[str, str] = {
    "/api/ai/operations": "whitelisted_operations",
    "/api/ai/providers": "providers",
    "/api/ai/dataset/status": "ai_dataset_enabled",
}


def _headers(user, lab):
    return auth_headers(user.id, lab.id, role=user.role)


# ── Anonymous: authentication required on every AI-internals surface ────────


def test_anonymous_ai_internals_require_authentication(client):
    failures = []
    for path in AI_INTERNALS:
        resp = client.get(path)
        if resp.status_code != 401:
            failures.append(f"GET {path} -> {resp.status_code}: {resp.text[:160]}")
    assert not failures, "Anonymous AI-internals reads were not rejected:\n" + "\n".join(failures)


# ── Authenticated but unauthorized: citizen / non-clinical operator ─────────


@pytest.mark.parametrize("role", ["citizen", "technician", "staff"])
def test_non_ai_operator_cannot_read_ai_internals(client, make_lab, make_lab_user, role):
    lab = make_lab()
    user = make_lab_user(lab.id, role=role)
    headers = _headers(user, lab)

    failures = []
    for path in AI_INTERNALS:
        resp = client.get(path, headers=headers)
        if resp.status_code != 403:
            failures.append(f"GET {path} -> {resp.status_code}: {resp.text[:160]}")
    assert not failures, f"Role {role!r} was not denied AI internals:\n" + "\n".join(failures)


# ── Legitimate workflow: clinicians/administrators keep access ──────────────


@pytest.mark.parametrize("role", ["doctor", "lab_admin", "ministry_admin"])
def test_ai_operator_can_read_ai_internals(client, make_lab, make_lab_user, role):
    lab = make_lab()
    operator = make_lab_user(lab.id, role=role)
    headers = _headers(operator, lab)

    for path in AI_INTERNALS:
        resp = client.get(path, headers=headers)
        assert resp.status_code == 200, f"GET {path} -> {resp.status_code}: {resp.text[:200]}"
        body = resp.json()
        key = PAYLOAD_KEYS[path]
        assert key in body, f"GET {path} missing {key!r}: {body}"


# ── No over-guarding: token-addressed patient route stays public ────────────


def test_patient_interpret_route_stays_public():
    # Structural guarantee (no kernel boot needed): the patient interpretation
    # route is intentionally anonymous — the result token is the proof of access.
    # It must not have acquired a router/dependency guard from this change.
    from app.routes import ai as ai_routes

    route = next(
        r
        for r in ai_routes.router.routes
        if getattr(r, "path", "") == "/api/ai/interpret/{token}"
    )
    assert not route.dependencies, route.dependencies
