from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.ehr import clinical_read_gate as gate_module
from app.ehr.clinical_read_gate import ClinicalEhrReadDenied, ClinicalEhrReadGate
from app.routes import ehr as routes_module
from app.identity.models.assignment import Assignment
from app.identity.models.legacy_account_link import LegacyAccountLink
from app.identity.models.policy import IdentityPolicy
from app.models.clinical_scope import ClinicalEhrFacilityBinding, ClinicalLabFacilityBinding
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
        actions=["clinical.ehr.record.read"],
        resources=["clinical.ehr.record"],
        subjects={"role_ids": ["ROLE-DOCTOR"]},
        conditions={
            "clinical_organization_resource_ids": ["41"],
            "clinical_facility_resource_ids": [31],
        },
    )


def _assignment(**overrides):
    values = {
        "id": "ASSIGNMENT-1",
        "status": "active",
        "is_active": True,
        "person_id": "PERSON-1",
        "role_id": "ROLE-DOCTOR",
        "clinical_organization_resource_id": 41,
        "clinical_facility_resource_id": 31,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _session(*, policies, assignments, ehr_facility_resource_id=31):
    link = SimpleNamespace(canonical_account_id="ACCOUNT-1")
    account = SimpleNamespace(id="ACCOUNT-1", identity_id="IDENTITY-1", status="active", is_active=True, is_locked=False)
    identity = SimpleNamespace(id="IDENTITY-1", person_id="PERSON-1", status="active", is_active=True)
    lab_binding = SimpleNamespace(facility_resource_id=31, mapping_version=7)
    ehr_binding = SimpleNamespace(facility_resource_id=ehr_facility_resource_id, mapping_version=9)
    facility = SimpleNamespace(id=31, organization_id=41, is_active=True)
    organization = SimpleNamespace(id=41, tenant_id=51, is_active=True)
    tenant = SimpleNamespace(id=51, is_active=True)
    return _Session(
        queried={
            LegacyAccountLink: [link],
            ClinicalLabFacilityBinding: [lab_binding],
            ClinicalEhrFacilityBinding: [ehr_binding],
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


def _lab_user():
    return SimpleNamespace(id=14, lab_id=21, role="doctor")


def test_authorizes_only_when_the_two_reviewed_facility_bridges_match(monkeypatch):
    events = []
    monkeypatch.setattr(gate_module, "log_action", lambda _db, **payload: events.append(payload))

    context = ClinicalEhrReadGate().authorize(
        db=_session(policies=[_policy()], assignments=[_assignment()]),
        lab_user=_lab_user(),
        national_facility_id="NATIONAL-FACILITY-1",
    )

    assert context.facility_resource_id == 31
    assert context.national_facility_id == "NATIONAL-FACILITY-1"
    assert context.ehr_mapping_version == 9
    assert events[0]["action"] == "clinical.ehr.record.read.allowed"


def test_denies_when_the_ehr_bridge_points_to_a_different_operational_facility(monkeypatch):
    events = []
    monkeypatch.setattr(gate_module, "log_action", lambda _db, **payload: events.append(payload))

    with pytest.raises(ClinicalEhrReadDenied, match="facility_scope_mismatch"):
        ClinicalEhrReadGate().authorize(
            db=_session(policies=[_policy()], assignments=[_assignment()], ehr_facility_resource_id=32),
            lab_user=_lab_user(),
            national_facility_id="NATIONAL-FACILITY-1",
        )

    assert '"reason": "facility_scope_mismatch"' in events[0]["details"]


def test_denies_when_the_exact_ehr_permission_is_not_allowed(monkeypatch):
    monkeypatch.setattr(gate_module, "log_action", lambda *_args, **_kwargs: None)

    with pytest.raises(ClinicalEhrReadDenied, match="permission_denied"):
        ClinicalEhrReadGate().authorize(
            db=_session(policies=[], assignments=[_assignment()]),
            lab_user=_lab_user(),
            national_facility_id="NATIONAL-FACILITY-1",
        )


def test_clinical_note_route_queries_only_after_the_gate_accepts(monkeypatch):
    calls = []

    class _PermittedGate:
        def authorize(self, *, db, lab_user, national_facility_id):
            calls.append((db, lab_user, national_facility_id))

    expected = SimpleNamespace(to_dict=lambda: {"id": "NOTE-1"})
    monkeypatch.setattr(routes_module, "ClinicalEhrReadGate", _PermittedGate)
    monkeypatch.setattr(routes_module.ehr_service, "get_clinical_note_for_verified_facility", lambda *args: expected)

    result = routes_module.get_clinical_note_for_verified_facility(
        national_facility_id="NATIONAL-FACILITY-1",
        note_id="NOTE-1",
        db="db",
        current_user="user",
    )

    assert result == {"id": "NOTE-1"}
    assert calls == [("db", "user", "NATIONAL-FACILITY-1")]


def test_clinical_note_route_returns_generic_forbidden_before_any_query(monkeypatch):
    class _DeniedGate:
        def authorize(self, *, db, lab_user, national_facility_id):
            raise ClinicalEhrReadDenied("permission_denied")

    def _unexpected_query(*_args):
        raise AssertionError("The EHR query must not run after a denied clinical gate")

    monkeypatch.setattr(routes_module, "ClinicalEhrReadGate", _DeniedGate)
    monkeypatch.setattr(routes_module.ehr_service, "get_clinical_note_for_verified_facility", _unexpected_query)

    with pytest.raises(HTTPException) as exc_info:
        routes_module.get_clinical_note_for_verified_facility(
            national_facility_id="NATIONAL-FACILITY-1",
            note_id="NOTE-1",
            db="db",
            current_user="user",
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Clinical EHR access is not permitted"
