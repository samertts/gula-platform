from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import app.clinical_gateway.context as context_module
import app.clinical_gateway.service as service_module
import pytest
from app.clinical_gateway.context import ClinicalGatewayBlocked, ClinicalGatewayContextResolver
from app.clinical_gateway.contracts import ClinicalPageRequest
from app.clinical_gateway.rollout import ClinicalGatewayMode, ClinicalGatewayRollout
from app.clinical_gateway.service import ClinicalCursorCodec, ClinicalGatewayService
from app.identity.services.authorization_decision import AuthorizationDecision, AuthorizationReason
from app.services.clinical_legacy_read_scope import ClinicalLegacyReadScope


def _context():
    account = SimpleNamespace(id="account-1", identity_id="identity-1")
    session = SimpleNamespace(id="session-1", mfa_used=False)
    actor = SimpleNamespace(account=account, session=session)
    workspace = SimpleNamespace(id="workspace-1", department_id=None)
    membership = SimpleNamespace(id="membership-1")
    legacy_user = SimpleNamespace(id=11, lab_id=21, role="staff")
    scope = ClinicalLegacyReadScope(
        legacy_lab_id=21,
        legacy_lab_user_id=11,
        operational_facility_id=31,
        operational_organization_id=41,
        tenant_id=51,
        niam_organization_id="org-1",
        niam_facility_id="facility-1",
        niam_workspace_id="workspace-1",
        scope_mapping_version=3,
    )
    return SimpleNamespace(
        actor=actor,
        workspace=workspace,
        membership=membership,
        legacy_user=legacy_user,
        scope=scope,
    )


def test_cursor_is_signed_and_bound_to_resource_workspace_and_limit(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "a" * 48)
    codec = ClinicalCursorCodec()
    cursor = codec.encode(resource="patients", workspace_id="workspace-1", limit=50, offset=50)

    assert codec.decode(cursor=cursor, resource="patients", workspace_id="workspace-1", limit=50) == 50
    with pytest.raises(ValueError):
        codec.decode(cursor=cursor, resource="orders", workspace_id="workspace-1", limit=50)
    with pytest.raises(ValueError):
        codec.decode(cursor=f"{cursor[:-1]}0", resource="patients", workspace_id="workspace-1", limit=50)


def test_rollout_defaults_off_and_does_not_allow_browser_state(monkeypatch):
    monkeypatch.delenv("GULA_CLINICAL_GATEWAY_MODE", raising=False)
    monkeypatch.delenv("GULA_CLINICAL_GATEWAY_ACCOUNT_ALLOWLIST", raising=False)
    monkeypatch.delenv("GULA_CLINICAL_GATEWAY_ORGANIZATION_ALLOWLIST", raising=False)

    rollout = ClinicalGatewayRollout()

    assert rollout.mode is ClinicalGatewayMode.off
    assert not rollout.allows(account_id="account-1", organization_id="org-1")


def test_context_blocks_when_reviewed_niam_mapping_is_missing(monkeypatch):
    workspace_context = SimpleNamespace(session_id="session-1", account_id="account-1", workspace_id="workspace-1", is_active=True)
    workspace = SimpleNamespace(id="workspace-1", status="active", organization_id="org-1", facility_id="facility-1")
    organization = SimpleNamespace(is_active=True, status="active")
    facility = SimpleNamespace(is_active=True, status="active", organization_id="org-1")

    class Query:
        def __init__(self, value):
            self.value = value

        def filter(self, *_args):
            return self

        def one_or_none(self):
            return self.value

        def all(self):
            return self.value

    class DB:
        def query(self, model):
            if model.__name__ == "WorkspaceSessionContext":
                return Query(workspace_context)
            if model.__name__ == "Membership":
                return Query([SimpleNamespace(id="membership-1", facility_id=None, department_id=None, unit_id=None, workspace_id=None)])
            if model.__name__ == "LegacyAccountLink":
                return Query([SimpleNamespace(legacy_account_id=11)])
            if model.__name__ == "ClinicalLabFacilityBinding":
                return Query([])
            raise AssertionError(model)

        def get(self, model, key):
            if model.__name__ == "Workspace":
                return workspace
            if model.__name__ == "NIAMOrganization":
                return organization
            if model.__name__ == "NIAMAdminFacility":
                return facility
            if model.__name__ == "LabUser":
                return SimpleNamespace(id=11, lab_id=21, is_active=True)
            raise AssertionError(model)

    proof_called = False

    class Proof:
        def __init__(self, _session):
            pass

        async def resolve_for_legacy_lab_user(self, **_kwargs):
            nonlocal proof_called
            proof_called = True

    monkeypatch.setattr(context_module, "ClinicalAuthorizationContextService", Proof)
    actor = SimpleNamespace(account=SimpleNamespace(id="account-1"), session=SimpleNamespace(id="session-1"))

    with pytest.raises(ClinicalGatewayBlocked, match="facility_mapping_unavailable"):
        ClinicalGatewayContextResolver(DB()).resolve(actor)
    assert proof_called is False


def test_denied_authorization_never_executes_patient_query(monkeypatch):
    service = ClinicalGatewayService(SimpleNamespace())
    context = _context()
    query_called = False

    async def deny(_self, _actor, _request):
        return AuthorizationDecision.deny(AuthorizationReason.permission_missing)

    def no_query(*_args, **_kwargs):
        nonlocal query_called
        query_called = True
        raise AssertionError("clinical query executed after authorization denial")

    monkeypatch.setattr(service_module.AuthorizationDecisionService, "authorize", deny)
    monkeypatch.setattr(service, "_audit", lambda **_kwargs: None)
    monkeypatch.setattr(service_module, "list_patients", no_query)

    with pytest.raises(ClinicalGatewayBlocked, match="permission_denied"):
        service.list_patients(
            context=context,
            request_id=uuid4(),
            correlation_id=uuid4(),
            params=ClinicalPageRequest(),
        )
    assert query_called is False


def test_allowed_patient_read_maps_minimal_fields_and_excludes_legacy_fields(monkeypatch):
    service = ClinicalGatewayService(SimpleNamespace())
    context = _context()

    async def allow(_self, _actor, _request):
        return AuthorizationDecision.allow()

    monkeypatch.setattr(service_module.AuthorizationDecisionService, "authorize", allow)
    monkeypatch.setattr(service, "_audit", lambda **_kwargs: None)
    monkeypatch.setattr(
        service_module,
        "list_patients",
        lambda *_args, **_kwargs: {
            "total": 1,
            "patients": [
                {
                    "id": 7,
                    "full_name": "Ali Hassan",
                    "phone": "+9647000000000",
                    "national_id_hash": "secret-hash",
                    "lab_id": 21,
                    "birth_date": "1990-01-01",
                    "gender": "M",
                    "created_at": datetime(2026, 1, 1),
                },
            ],
        },
    )

    response = service.list_patients(
        context=context,
        request_id=uuid4(),
        correlation_id=uuid4(),
        params=ClinicalPageRequest(),
    )

    payload = response.model_dump()
    assert payload["items"] == [
        {
            "id": "7",
            "display_name": "Ali Hassan",
            "birth_date": "1990-01-01",
            "gender": "M",
            "created_at": datetime(2026, 1, 1),
        },
    ]
    assert "phone" not in payload["items"][0]
    assert "lab_id" not in payload["items"][0]
    assert "national_id_hash" not in payload["items"][0]


def test_allowed_result_read_maps_minimal_fields_and_excludes_share_fields(monkeypatch):
    service = ClinicalGatewayService(SimpleNamespace())
    context = _context()

    async def allow(_self, _actor, _request):
        return AuthorizationDecision.allow()

    monkeypatch.setattr(service_module.AuthorizationDecisionService, "authorize", allow)
    monkeypatch.setattr(service, "_audit", lambda **_kwargs: None)
    monkeypatch.setattr(
        service_module,
        "get_order_by_id",
        lambda **_kwargs: {
            "results": [
                {
                    "id": 9,
                    "test_name": "Glucose",
                    "value": 5.2,
                    "value_text": None,
                    "unit": "mmol/L",
                    "normal_range_low": 3.9,
                    "normal_range_high": 6.1,
                    "flag": "normal",
                    "result_token": "secret",
                    "result_link": "/r/secret",
                    "interpretation": "normal",
                    "created_at": datetime(2026, 1, 1),
                },
            ],
        },
    )

    response = service.list_results(
        context=context,
        request_id=uuid4(),
        correlation_id=uuid4(),
        order_id=7,
    )

    payload = response.model_dump()
    assert payload["items"] == [
        {
            "id": "9",
            "order_id": "7",
            "test_name": "Glucose",
            "value": 5.2,
            "value_text": None,
            "unit": "mmol/L",
            "normal_range_low": 3.9,
            "normal_range_high": 6.1,
            "flag": "normal",
            "interpretation": "normal",
            "created_at": datetime(2026, 1, 1),
        },
    ]
    assert "result_token" not in payload["items"][0]
    assert "result_link" not in payload["items"][0]
    assert payload["total"] == 1
    assert payload["limit"] == 1
