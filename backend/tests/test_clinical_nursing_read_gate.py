from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.models.assignment import Assignment
from app.identity.models.legacy_account_link import LegacyAccountLink
from app.identity.models.policy import IdentityPolicy
from app.models.clinical_scope import ClinicalLabFacilityBinding
from app.nursing import routes as routes_module
from app.nursing.clinical_read_gate import ClinicalNursingTaskReadDenied, ClinicalNursingTaskReadGate
from app.radiology import clinical_read_gate as base_gate_module
from fastapi import HTTPException


class _Query:
    def __init__(self, values):
        self.values = values

    def filter(self, *_conditions):
        return self

    def all(self):
        return list(self.values)


class _Session:
    def __init__(self, *, queried, fetched):
        self.queried = queried
        self.fetched = fetched

    def query(self, model):
        return _Query(self.queried.get(model, []))

    def get(self, model, key):
        return self.fetched.get((model, key))


def _policy(effect="allow"):
    return SimpleNamespace(
        effect=effect,
        actions=["clinical.nursing.task.read"],
        resources=["clinical.nursing.task"],
        subjects={"role_ids": ["ROLE-NURSING"]},
        conditions={
            "clinical_organization_resource_ids": ["41"],
            "clinical_facility_resource_ids": [31],
        },
    )


def _session(*, policies, assignments):
    link = SimpleNamespace(canonical_account_id="ACCOUNT-1")
    account = SimpleNamespace(id="ACCOUNT-1", identity_id="IDENTITY-1", status="active", is_active=True, is_locked=False)
    identity = SimpleNamespace(id="IDENTITY-1", person_id="PERSON-1", status="active", is_active=True)
    binding = SimpleNamespace(facility_resource_id=31, mapping_version=7)
    facility = SimpleNamespace(id=31, organization_id=41, is_active=True)
    organization = SimpleNamespace(id=41, tenant_id=51, is_active=True)
    tenant = SimpleNamespace(id=51, is_active=True)
    return _Session(
        queried={
            LegacyAccountLink: [link],
            ClinicalLabFacilityBinding: [binding],
            Assignment: assignments,
            IdentityPolicy: policies,
        },
        fetched={
            (base_gate_module.Account, "ACCOUNT-1"): account,
            (base_gate_module.IdentityRecord, "IDENTITY-1"): identity,
            (base_gate_module.Facility, 31): facility,
            (base_gate_module.Organization, 41): organization,
            (base_gate_module.Tenant, 51): tenant,
        },
    )


def _assignment(**overrides):
    values = {
        "id": "ASSIGNMENT-1",
        "status": "active",
        "is_active": True,
        "person_id": "PERSON-1",
        "role_id": "ROLE-NURSING",
        "clinical_organization_resource_id": 41,
        "clinical_facility_resource_id": 31,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _lab_user():
    return SimpleNamespace(id=14, lab_id=21, role="nursing")


def test_nursing_gate_requires_the_exact_nursing_permission_and_audits(monkeypatch):
    events = []
    monkeypatch.setattr(base_gate_module, "log_action", lambda _db, **payload: events.append(payload))

    context = ClinicalNursingTaskReadGate().authorize(
        db=_session(policies=[_policy()], assignments=[_assignment()]),
        lab_user=_lab_user(),
    )

    assert context.facility_resource_id == 31
    assert events[0]["action"] == "clinical.nursing.task.read.allowed"
    assert events[0]["resource_type"] == "clinical_nursing_task_read"


def test_nursing_gate_denies_before_a_task_query_when_permission_is_missing(monkeypatch):
    monkeypatch.setattr(base_gate_module, "log_action", lambda *_args, **_kwargs: None)

    with pytest.raises(ClinicalNursingTaskReadDenied, match="permission_denied"):
        ClinicalNursingTaskReadGate().authorize(
            db=_session(policies=[], assignments=[_assignment()]),
            lab_user=_lab_user(),
        )


def test_clinical_my_tasks_route_queries_only_the_current_nurse_after_the_gate(monkeypatch):
    calls = []

    class _PermittedGate:
        def authorize(self, *, db, lab_user):
            calls.append(("gate", db, lab_user))

    def _get_tasks(*, db, lab_id, nurse_id, limit):
        calls.append(("tasks", db, lab_id, nurse_id, limit))
        return []

    monkeypatch.setattr(routes_module, "ClinicalNursingTaskReadGate", _PermittedGate)
    monkeypatch.setattr(routes_module.NursingService, "get_tasks", _get_tasks)

    result = routes_module.list_clinical_my_tasks(db="db", current_user=_lab_user())

    assert result == {"items": [], "total": 0, "skip": 0, "limit": 50}
    # nurse_id reaches the query as an integer: nursing_tasks.assigned_to is
    # INTEGER, and the route used to hand the service str(current_user.id).
    assert calls == [("gate", "db", _lab_user()), ("tasks", "db", 21, 14, 50)]


def test_clinical_my_tasks_route_returns_403_before_any_task_query(monkeypatch):
    class _DeniedGate:
        def authorize(self, *, db, lab_user):
            raise ClinicalNursingTaskReadDenied("permission_denied")

    def _unexpected_query(**_kwargs):
        raise AssertionError("The nursing task query must not run after a denied clinical gate")

    monkeypatch.setattr(routes_module, "ClinicalNursingTaskReadGate", _DeniedGate)
    monkeypatch.setattr(routes_module.NursingService, "get_tasks", _unexpected_query)

    with pytest.raises(HTTPException) as exc_info:
        routes_module.list_clinical_my_tasks(db="db", current_user=_lab_user())

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Clinical nursing access is not permitted"
