from __future__ import annotations

import importlib


def load_module():
    return importlib.import_module("services.health_exchange.api_security")


def test_missing_key_fails_closed(monkeypatch):
    monkeypatch.delenv("LAB_PLATFORM_API_KEY", raising=False)
    module = importlib.reload(load_module())

    assert module.API_KEY is None
    assert module.verify_key("any-value") is False


def test_configured_key_uses_exact_match(monkeypatch):
    monkeypatch.setenv("LAB_PLATFORM_API_KEY", "test-health-exchange-key")
    module = importlib.reload(load_module())

    assert module.verify_key("test-health-exchange-key") is True
    assert module.verify_key("test-health-exchange-key-extra") is False
