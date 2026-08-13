from types import SimpleNamespace

import app.routes.national_identity as route
import pytest
from app.gateways.mode import AdapterMode
from fastapi import HTTPException


def test_production_rejects_stub_national_identity(monkeypatch):
    monkeypatch.setattr(route, "IS_PRODUCTION", True)
    monkeypatch.setattr(route, "DEMO_MODE", False)
    monkeypatch.setattr(
        route,
        "get_national_identity_gateway",
        lambda: SimpleNamespace(current_mode=lambda: AdapterMode.STUB),
    )

    with pytest.raises(HTTPException) as exc_info:
        route.verify(route.NationalIdRequest(national_id="123456789012"), current_user=None)

    assert exc_info.value.status_code == 503


def test_live_or_demo_path_can_return_gateway_result(monkeypatch):
    monkeypatch.setattr(route, "IS_PRODUCTION", True)
    monkeypatch.setattr(route, "DEMO_MODE", False)
    monkeypatch.setattr(
        route,
        "get_national_identity_gateway",
        lambda: SimpleNamespace(current_mode=lambda: AdapterMode.LIVE),
    )
    expected = {"valid": True, "source": "api"}
    monkeypatch.setattr(route, "verify_national_id", lambda _: expected)

    assert route.verify(route.NationalIdRequest(national_id="123456789012"), current_user=None) == expected


def test_demo_allows_stub_for_synthetic_testing(monkeypatch):
    monkeypatch.setattr(route, "IS_PRODUCTION", True)
    monkeypatch.setattr(route, "DEMO_MODE", True)
    monkeypatch.setattr(
        route,
        "get_national_identity_gateway",
        lambda: SimpleNamespace(current_mode=lambda: AdapterMode.STUB),
    )
    expected = {"valid": True, "source": "stub_local_validation"}
    monkeypatch.setattr(route, "verify_national_id", lambda _: expected)

    assert route.verify(route.NationalIdRequest(national_id="123456789012"), current_user=None) == expected
