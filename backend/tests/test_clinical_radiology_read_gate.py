from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.models.assignment import Assignment
from app.identity.models.legacy_account_link import LegacyAccountLink
from app.identity.models.policy import IdentityPolicy
from app.models.clinical_scope import ClinicalLabFacilityBinding
from app.radiology import clinical_read_gate as gate_module
from app.radiology import routes as routes_module
from app.radiology.clinical_read_gate import ClinicalRadiologyReadDenied, ClinicalRadiologyReadGate
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
        actions=["clinical.radiology.order.read"],
        resources=["clinical.radiology.order"],
        subjects={"role_ids": ["ROLE-RADIOLOGY"]},
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
            (gate_module.Account, "ACCOUNT-1"): account,
            (gate_module.IdentityRecord, "IDENTITY-1"): identity,
            (gate_module.Facility, 31): facility,
            (gate_module.Organization, 41): organization,
            (gate_module.Tenant, 51): tenant,
        },
    )


def _assignment(**overrides):
    values = {
        "id": "ASSIGNMENT-1",
        "status": "active",
        "is_active": True,
        "person_id": "PERSON-1",
        "role_id": "ROLE-RADIOLOGY",
        "clinical_organization_resource_id": 41,
        "clinical_facility_resource_id": 31,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _lab_user():
    return SimpleNamespace(id=14, lab_id=21, role="radiology")


def test_authorizes_only_a_complete_exactly_permitted_clinical_scope(monkeypatch):
    events = []
    monkeypatch.setattr(gate_module, "log_action", lambda _db, **payload: events.append(payload))
    context = ClinicalRadiologyReadGate().authorize(
        db=_session(policies=[_policy()], assignments=[_assignment()]),
        lab_user=_lab_user(),
    )

    assert context.facility_resource_id == 31
    assert context.organization_resource_id == 41
    assert context.assignment_id == "ASSIGNMENT-1"
    assert events[0]["action"] == "clinical.radiology.order.read.allowed"
    assert '"decision": "allowed"' in events[0]["details"]


def test_denies_when_the_exact_clinical_permission_is_not_allowed(monkeypatch):
    events = []
    monkeypatch.setattr(gate_module, "log_action", lambda _db, **payload: events.append(payload))

    with pytest.raises(ClinicalRadiologyReadDenied, match="permission_denied"):
        ClinicalRadiologyReadGate().authorize(
            db=_session(policies=[], assignments=[_assignment()]),
            lab_user=_lab_user(),
        )

    assert events[0]["action"] == "clinical.radiology.order.read.denied"
    assert '"reason": "permission_denied"' in events[0]["details"]


def test_denies_when_the_person_has_no_assignment_in_the_bound_facility(monkeypatch):
    events = []
    monkeypatch.setattr(gate_module, "log_action", lambda _db, **payload: events.append(payload))

    with pytest.raises(ClinicalRadiologyReadDenied, match="active_assignment_unavailable"):
        ClinicalRadiologyReadGate().authorize(
            db=_session(policies=[_policy()], assignments=[]),
            lab_user=_lab_user(),
        )

    assert '"reason": "active_assignment_unavailable"' in events[0]["details"]


def test_clinical_orders_route_reuses_existing_read_only_query_after_gate(monkeypatch):
    calls = []

    class _PermittedGate:
        def authorize(self, *, db, lab_user):
            calls.append((db, lab_user))

    expected = {"items": [{"id": "ORDER-1"}], "total": 1, "skip": 0, "limit": 50}
    monkeypatch.setattr(routes_module, "ClinicalRadiologyReadGate", _PermittedGate)
    monkeypatch.setattr(routes_module, "list_orders", lambda **kwargs: expected)

    result = routes_module.list_clinical_orders(db="db", current_user="user")

    assert result == expected
    assert calls == [("db", "user")]


def test_clinical_orders_route_returns_generic_forbidden_before_any_read(monkeypatch):
    class _DeniedGate:
        def authorize(self, *, db, lab_user):
            raise ClinicalRadiologyReadDenied("permission_denied")

    def _unexpected_query(**kwargs):
        raise AssertionError("The legacy laboratory query must not run after a denied clinical gate")

    monkeypatch.setattr(routes_module, "ClinicalRadiologyReadGate", _DeniedGate)
    monkeypatch.setattr(routes_module, "list_orders", _unexpected_query)

    with pytest.raises(HTTPException) as exc_info:
        routes_module.list_clinical_orders(db="db", current_user="user")

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Clinical radiology access is not permitted"
