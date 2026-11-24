"""Regression tests for national governance surface authorization (S-04).

Surfaces covered
----------------
* ``/lifecycle`` — national release / component governance
* ``/pilot-platform`` — national pilot deployment & readiness
* ``/certification`` — read-only engineering certification computation (S-10)
* ``/contracts`` — contract artifacts and filesystem export (S-11)

Before remediation every route on these routers was mounted with no
authentication or authorization dependency at all: anonymous callers could list
national releases, approve releases, register components and decide pilot
go/no-go gates.

Security properties under test
------------------------------
* anonymous                       → 401 on every read and write
* authenticated citizen           → 403 (authentication ≠ authorization)
* authenticated non-admin staff   → may read, may not write
* platform operator (master)      → may read and write
* reader cannot escalate to write → 403
* approval / assessment / deploy identity is derived server-side and a
  caller-supplied identity field is rejected with 400
* ``/lifecycle/health`` and ``/pilot-platform/health`` stay public (liveness)
"""
from __future__ import annotations

import pytest
from app.pilot_platform.infrastructure.models import DeploymentRecordModel
from app.security.platform_access import (
    require_governance_reader,
    require_governance_writer,
)
from fastapi import HTTPException

from tests.conftest import auth_headers

LIFECYCLE_READ = "/lifecycle/components"
LIFECYCLE_WRITE = "/lifecycle/components"
PILOT_READ = "/pilot-platform/pilots"
PILOT_WRITE = "/pilot-platform/pilots"
CERTIFICATION_READ = "/certification/dimensions"
CONTRACTS_READ = "/contracts/catalog"
CONTRACTS_WRITE = "/contracts/export"


def _headers(user, lab):
    return auth_headers(user.id, lab.id, role=user.role)


def _lifecycle_component_body(name: str) -> dict:
    return {"name": name, "component_type": "service"}


def _pilot_body(lab_id: int, module: str) -> dict:
    return {"module_name": module, "version": "1.0.0", "lab_id": lab_id}


# ── Anonymous: authentication required ───────────────────────────────────────


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("get", LIFECYCLE_READ, None),
        ("post", LIFECYCLE_WRITE, {"name": "anon-comp", "component_type": "service"}),
        ("get", PILOT_READ, None),
        ("post", PILOT_WRITE, {"module_name": "anon", "version": "1.0.0"}),
        ("get", CERTIFICATION_READ, None),
        ("get", CONTRACTS_READ, None),
        ("post", CONTRACTS_WRITE, {"output_dir": "anon-export"}),
    ],
)
def test_national_governance_rejects_anonymous(client, method, path, body):
    resp = getattr(client, method)(path, json=body) if body is not None else getattr(client, method)(path)
    assert resp.status_code == 401, resp.text


# ── Authenticated but unauthorized: citizen is not an operator ───────────────


def test_citizen_cannot_read_lifecycle(client, make_lab, make_lab_user):
    lab = make_lab()
    citizen = make_lab_user(lab.id, role="citizen")
    assert client.get(LIFECYCLE_READ, headers=_headers(citizen, lab)).status_code == 403


def test_citizen_cannot_write_lifecycle(client, make_lab, make_lab_user):
    lab = make_lab()
    citizen = make_lab_user(lab.id, role="citizen")
    resp = client.post(
        LIFECYCLE_WRITE,
        json=_lifecycle_component_body("citizen-comp"),
        headers=_headers(citizen, lab),
    )
    assert resp.status_code == 403


def test_citizen_cannot_read_pilot(client, make_lab, make_lab_user):
    lab = make_lab()
    citizen = make_lab_user(lab.id, role="citizen")
    assert client.get(PILOT_READ, headers=_headers(citizen, lab)).status_code == 403


def test_citizen_cannot_read_certification(client, make_lab, make_lab_user):
    lab = make_lab()
    citizen = make_lab_user(lab.id, role="citizen")
    assert client.get(CERTIFICATION_READ, headers=_headers(citizen, lab)).status_code == 403


# ── Authorized reads for operational staff ───────────────────────────────────


@pytest.mark.parametrize(
    "path",
    [LIFECYCLE_READ, PILOT_READ, CERTIFICATION_READ, CONTRACTS_READ],
)
def test_doctor_may_read_governance_surfaces(client, make_lab, make_lab_user, path):
    lab = make_lab()
    doctor = make_lab_user(lab.id, role="doctor")
    assert client.get(path, headers=_headers(doctor, lab)).status_code == 200


# ── Privilege escalation: readers cannot write ───────────────────────────────


def test_doctor_cannot_write_lifecycle(client, make_lab, make_lab_user):
    lab = make_lab()
    doctor = make_lab_user(lab.id, role="doctor")
    resp = client.post(
        LIFECYCLE_WRITE,
        json=_lifecycle_component_body("doctor-comp"),
        headers=_headers(doctor, lab),
    )
    assert resp.status_code == 403


def test_doctor_cannot_write_pilot(client, make_lab, make_lab_user):
    lab = make_lab()
    doctor = make_lab_user(lab.id, role="doctor")
    resp = client.post(
        PILOT_WRITE,
        json=_pilot_body(lab.id, "doctor-pilot"),
        headers=_headers(doctor, lab),
    )
    assert resp.status_code == 403


def test_doctor_cannot_export_contracts(client, make_lab, make_lab_user):
    lab = make_lab()
    doctor = make_lab_user(lab.id, role="doctor")
    resp = client.post(
        CONTRACTS_WRITE,
        json={"output_dir": "doctor-export"},
        headers=_headers(doctor, lab),
    )
    assert resp.status_code == 403


# ── Operator: legitimate workflows still work ────────────────────────────────


def test_master_admin_can_register_component(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    resp = client.post(
        LIFECYCLE_WRITE,
        json=_lifecycle_component_body("operator-comp"),
        headers=_headers(operator, lab),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["name"] == "operator-comp"


def test_master_admin_can_create_pilot(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    resp = client.post(
        PILOT_WRITE,
        json=_pilot_body(lab.id, "operator-pilot"),
        headers=_headers(operator, lab),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["module_name"] == "operator-pilot"


# ── Approval identity is server-derived ──────────────────────────────────────


def test_lifecycle_approval_derives_actor_and_rejects_forgery(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    headers = _headers(operator, lab)

    component = client.post(
        LIFECYCLE_WRITE,
        json=_lifecycle_component_body("approval-comp"),
        headers=headers,
    )
    assert component.status_code == 201, component.text
    component_id = component.json()["id"]

    release = client.post(
        "/lifecycle/releases",
        json={"component_id": component_id, "version": "1.0.0"},
        headers=headers,
    )
    assert release.status_code == 201, release.text
    release_id = release.json()["id"]

    forged = client.post(
        f"/lifecycle/releases/{release_id}/approve",
        json={"approved_by": "attacker@example.com"},
        headers=headers,
    )
    assert forged.status_code == 400
    assert "approved_by" in forged.json()["detail"]

    approved = client.post(
        f"/lifecycle/releases/{release_id}/approve",
        json={"certification_level": "gold"},
        headers=headers,
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["approved_by"] == operator.email
    assert approved.json()["status"] == "approved"


def test_pilot_gate_derives_approver_and_rejects_forgery(client, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    headers = _headers(operator, lab)

    pilot = client.post(PILOT_WRITE, json=_pilot_body(lab.id, "gate-pilot"), headers=headers)
    assert pilot.status_code == 201, pilot.text
    pilot_id = pilot.json()["id"]

    forged = client.post(
        "/pilot-platform/gates",
        json={
            "pilot_id": pilot_id,
            "gate_name": "go-live",
            "result": "passed",
            "approver": "attacker@example.com",
            "lab_id": lab.id,
        },
        headers=headers,
    )
    assert forged.status_code == 400
    assert "approver" in forged.json()["detail"]

    gate = client.post(
        "/pilot-platform/gates",
        json={
            "pilot_id": pilot_id,
            "gate_name": "go-live",
            "result": "passed",
            "lab_id": lab.id,
        },
        headers=headers,
    )
    assert gate.status_code == 201, gate.text
    assert gate.json()["approver"] == operator.email


def test_pilot_readiness_rejects_forged_assessor(client, make_lab, make_lab_user):
    """The route rejects a caller-controlled ``assessed_by`` before any write.

    The readiness service currently persists ``lab_id`` only through the
    national tenant context, which the reduced test schema does not provide;
    therefore this test asserts the security boundary (rejecting forgery)
    rather than the persistence success path.
    """
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    headers = _headers(operator, lab)

    pilot = client.post(PILOT_WRITE, json=_pilot_body(lab.id, "readiness-pilot"), headers=headers)
    assert pilot.status_code == 201, pilot.text
    pilot_id = pilot.json()["id"]

    forged = client.post(
        "/pilot-platform/readiness",
        json={
            "pilot_id": pilot_id,
            "facility_id": "fac-1",
            "items": [],
            "assessed_by": "attacker",
            "lab_id": lab.id,
        },
        headers=headers,
    )
    assert forged.status_code == 400
    assert "assessed_by" in forged.json()["detail"]


def test_pilot_deployment_derives_deployer(client, db, make_lab, make_lab_user):
    lab = make_lab()
    operator = make_lab_user(lab.id, role="master_admin")
    headers = _headers(operator, lab)

    pilot = client.post(PILOT_WRITE, json=_pilot_body(lab.id, "deploy-pilot"), headers=headers)
    assert pilot.status_code == 201, pilot.text
    pilot_id = pilot.json()["id"]

    forged = client.post(
        "/pilot-platform/deployments",
        json={"pilot_id": pilot_id, "module": "m", "deployed_by": "attacker", "lab_id": lab.id},
        headers=headers,
    )
    assert forged.status_code == 400
    assert "deployed_by" in forged.json()["detail"]

    deployment = client.post(
        "/pilot-platform/deployments",
        json={"pilot_id": pilot_id, "module": "m", "lab_id": lab.id},
        headers=headers,
    )
    assert deployment.status_code == 201, deployment.text

    stored = db.query(DeploymentRecordModel).filter_by(id=deployment.json()["id"]).one()
    assert stored.deployed_by == operator.email


# ── Liveness endpoints stay public ───────────────────────────────────────────


@pytest.mark.parametrize("path", ["/lifecycle/health", "/pilot-platform/health"])
def test_health_endpoints_remain_public(client, path):
    assert client.get(path).status_code == 200


# ── Dependency-level policy ──────────────────────────────────────────────────


def test_governance_reader_allows_master_and_ministry(make_lab, make_lab_user):
    lab = make_lab()
    master = make_lab_user(lab.id, role="master_admin")
    ministry = make_lab_user(lab.id, role="ministry_admin")
    assert require_governance_reader(master) is master
    assert require_governance_reader(ministry) is ministry


def test_governance_reader_denies_citizen(make_lab, make_lab_user):
    lab = make_lab()
    citizen = make_lab_user(lab.id, role="citizen")
    with pytest.raises(HTTPException) as exc:
        require_governance_reader(citizen)
    assert exc.value.status_code == 403


def test_governance_writer_allows_master_only(make_lab, make_lab_user):
    lab = make_lab()
    master = make_lab_user(lab.id, role="master_admin")
    ministry = make_lab_user(lab.id, role="ministry_admin")
    assert require_governance_writer(master) is master
    with pytest.raises(HTTPException) as exc:
        require_governance_writer(ministry)
    assert exc.value.status_code == 403
