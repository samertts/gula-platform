"""Regression tests for anonymous access to national governance surfaces (S-08).

Finding
-------
The ``/governance`` router exposed confidential national governance data — the
ministry hierarchy, healthcare-worker personnel records, health-number
identities, laboratory registry/statistics, clinical policies, the national test
catalogue and national audit events — with **no authentication at all**
(CWE-306 missing authentication for critical function / CWE-200 exposure of
sensitive information).

Three worker sub-resource writes (``trainings``, ``competencies``,
``productivity``) were also anonymous, allowing anyone to inject personnel
records into the national workforce registry.

Policy under test
-----------------
* Confidential **reads** → any authenticated operational role
  (``require_governance_reader``); a ``citizen`` is not an operator and is
  denied explicitly; anonymous → 401.
* Worker sub-resource **writes** → ``elevated_dep`` (master / ministry /
  national / directorate admin); operational readers → 403; anonymous → 401.
* ``GET /governance/health`` stays public: it is a liveness probe with static
  content.

Assertions are made per surface inside a single test (rather than one test per
surface) because each test boots the full application kernel; failures still
report the offending path, status and body.
"""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers

# (path, query params) for every confidential read on the governance router.
GOVERNANCE_READS: list[tuple[str, dict[str, str]]] = [
    ("/governance/nodes/1", {}),
    ("/governance/nodes/1/subtree", {}),
    ("/governance/nodes/1/path", {}),
    ("/governance/nodes/1/children", {}),
    ("/governance/nodes/by-type/laboratory", {}),
    ("/governance/health-numbers/HN-0001", {}),
    ("/governance/health-numbers/HN-0001/history", {}),
    ("/governance/connectors", {}),
    ("/governance/workers/1", {}),
    ("/governance/workers/by-node/1", {}),
    ("/governance/workers/1/productivity", {}),
    (
        "/governance/workers/ranking",
        {"period": "monthly", "period_start": "2026-01-01", "period_end": "2026-01-31"},
    ),
    ("/governance/workers/1/stats", {}),
    ("/governance/laboratories", {}),
    ("/governance/laboratories/1", {}),
    ("/governance/laboratories/1/stats", {}),
    ("/governance/laboratories/1/low-stock", {}),
    ("/governance/national-tests", {}),
    ("/governance/clinical-policies", {}),
    ("/governance/audit-events", {}),
    ("/governance/interop-protocols", {}),
    (
        "/governance/terminology-mappings",
        {"source_system": "LOINC", "source_code": "1234-5"},
    ),
    ("/governance/ai/risk/gemini-2.0-flash", {}),
    ("/governance/policy/evaluate", {"action": "create_node"}),
]

GOVERNANCE_WRITES: list[tuple[str, dict[str, str]]] = [
    (
        "/governance/workers/1/trainings",
        {"training_name": "Infection control", "training_type": "internal"},
    ),
    (
        "/governance/workers/1/competencies",
        {"competency_name": "Phlebotomy", "level": "advanced"},
    ),
    (
        "/governance/workers/1/productivity",
        {"period": "monthly", "period_start": "2026-01-01", "period_end": "2026-01-31"},
    ),
]


def _headers(user, lab):
    return auth_headers(user.id, lab.id, role=user.role)


# ── Anonymous: authentication required on every confidential surface ────────


def test_anonymous_governance_reads_require_authentication(client):
    failures = []
    for path, params in GOVERNANCE_READS:
        resp = client.get(path, params=params)
        if resp.status_code != 401:
            failures.append(f"GET {path} -> {resp.status_code}: {resp.text[:160]}")
    assert not failures, "Anonymous governance reads were not rejected:\n" + "\n".join(failures)


def test_anonymous_governance_writes_require_authentication(client):
    failures = []
    for path, params in GOVERNANCE_WRITES:
        resp = client.post(path, params=params)
        if resp.status_code != 401:
            failures.append(f"POST {path} -> {resp.status_code}: {resp.text[:160]}")
    assert not failures, "Anonymous governance writes were not rejected:\n" + "\n".join(failures)


# ── Authenticated but unauthorized: citizen is not an operator ──────────────


def test_citizen_cannot_read_confidential_governance_data(client, make_lab, make_lab_user):
    lab = make_lab()
    citizen = make_lab_user(lab.id, role="citizen")
    headers = _headers(citizen, lab)

    failures = []
    for path, params in GOVERNANCE_READS:
        resp = client.get(path, params=params, headers=headers)
        if resp.status_code != 403:
            failures.append(f"GET {path} -> {resp.status_code}: {resp.text[:160]}")
    assert not failures, "Citizen read access was not denied:\n" + "\n".join(failures)


def test_citizen_cannot_write_worker_records(client, make_lab, make_lab_user):
    lab = make_lab()
    citizen = make_lab_user(lab.id, role="citizen")
    headers = _headers(citizen, lab)

    failures = []
    for path, params in GOVERNANCE_WRITES:
        resp = client.post(path, params=params, headers=headers)
        if resp.status_code != 403:
            failures.append(f"POST {path} -> {resp.status_code}: {resp.text[:160]}")
    assert not failures, "Citizen write access was not denied:\n" + "\n".join(failures)


# ── Legitimate workflow: operational readers keep read access ───────────────


def test_operational_reader_can_read_governance_data(client, make_lab, make_lab_user):
    lab = make_lab()
    reader = make_lab_user(lab.id, role="doctor")
    headers = _headers(reader, lab)

    failures = []
    for path, params in GOVERNANCE_READS:
        resp = client.get(path, params=params, headers=headers)
        # Authorization must pass; the resource itself may legitimately be absent.
        if resp.status_code in (401, 403):
            failures.append(f"GET {path} -> {resp.status_code}: {resp.text[:160]}")
    assert not failures, "Operational reader lost governance read access:\n" + "\n".join(failures)

    # DB-free catalogue endpoints must still return their real payload, proving
    # the guard did not merely short-circuit the handler.
    for path, params in [
        ("/governance/connectors", {}),
        ("/governance/national-tests", {}),
        ("/governance/policy/evaluate", {"action": "create_node"}),
    ]:
        resp = client.get(path, params=params, headers=headers)
        assert resp.status_code == 200, f"GET {path} -> {resp.status_code}: {resp.text[:160]}"


# ── Writes are operator-only (no privilege escalation from read access) ─────


def test_operational_reader_cannot_write_worker_records(client, make_lab, make_lab_user):
    lab = make_lab()
    reader = make_lab_user(lab.id, role="doctor")
    headers = _headers(reader, lab)

    failures = []
    for path, params in GOVERNANCE_WRITES:
        resp = client.post(path, params=params, headers=headers)
        if resp.status_code != 403:
            failures.append(f"POST {path} -> {resp.status_code}: {resp.text[:160]}")
    assert not failures, "Read access escalated to worker writes:\n" + "\n".join(failures)


def test_elevated_operator_can_write_worker_records(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="directorate_admin")
    headers = _headers(operator, lab)

    failures = []
    for path, params in GOVERNANCE_WRITES:
        resp = client.post(path, params=params, headers=headers)
        # Authorization must pass; the worker may not exist in the fixture DB.
        if resp.status_code in (401, 403):
            failures.append(f"POST {path} -> {resp.status_code}: {resp.text[:160]}")
    assert not failures, "Elevated operator lost worker-write access:\n" + "\n".join(failures)


# ── Genuinely public: liveness probe stays reachable ────────────────────────


def test_governance_health_is_public(client):
    resp = client.get("/governance/health")
    assert resp.status_code == 200, resp.text
    assert resp.json()["layer"] == "national_governance"
