from types import SimpleNamespace

import app.routes.national_identity as route
import pytest
from app.gateways.mode import AdapterMode
from fastapi import HTTPException


def _gateway(mode: AdapterMode) -> SimpleNamespace:
    return SimpleNamespace(current_mode=lambda: mode)


def test_stub_national_identity_is_fail_closed(monkeypatch):
    monkeypatch.setattr(route, "get_national_identity_gateway", lambda: _gateway(AdapterMode.STUB))

    with pytest.raises(HTTPException) as exc_info:
        route.verify(route.NationalIdRequest(national_id="123456789012"), current_user=None)

    assert exc_info.value.status_code == 503
    assert "authorized live provider" in str(exc_info.value.detail)


def test_shadow_national_identity_is_fail_closed(monkeypatch):
    monkeypatch.setattr(route, "get_national_identity_gateway", lambda: _gateway(AdapterMode.SHADOW))

    with pytest.raises(HTTPException) as exc_info:
        route.verify(route.NationalIdRequest(national_id="123456789012"), current_user=None)

    assert exc_info.value.status_code == 503


def test_live_provider_can_return_gateway_result(monkeypatch):
    monkeypatch.setattr(route, "get_national_identity_gateway", lambda: _gateway(AdapterMode.LIVE))
    expected = {"valid": True, "source": "api"}
    monkeypatch.setattr(route, "verify_national_id", lambda _: expected)

    assert route.verify(route.NationalIdRequest(national_id="123456789012"), current_user=None) == expected
