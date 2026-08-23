from __future__ import annotations

import time
from typing import Any

import pytest
from app.gateways import lab_device_gateway as gateway
from app.security.redis_client import cache


def _configure_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gateway, "_DEVICE_HMAC_KEY", "test-device-gateway-hmac-key")
    monkeypatch.setattr(gateway, "_ALLOWED_DEVICE_IDS", {"ANALYZER-001"})
    monkeypatch.setattr(gateway, "_REPLAY_WINDOW", 120)


def _signed_payload(nonce: str) -> dict[str, Any]:
    timestamp = int(time.time())
    signature = gateway._compute_signature(
        "ANALYZER-001",
        "SYNTHETIC-SAMPLE-001",
        "GLUCOSE",
        101.2,
        timestamp,
    )
    return {
        "sample_id": "SYNTHETIC-SAMPLE-001",
        "test": "GLUCOSE",
        "value": 101.2,
        "device_id": "ANALYZER-001",
        "signature": signature,
        "timestamp": timestamp,
        "nonce": nonce,
    }


def test_gateway_rejects_when_hmac_key_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gateway, "_DEVICE_HMAC_KEY", "")
    monkeypatch.setattr(gateway, "_ALLOWED_DEVICE_IDS", {"ANALYZER-001"})

    with pytest.raises(gateway.DeviceAuthError, match="authentication is unavailable"):
        gateway.receive_device_result(
            "SYNTHETIC-SAMPLE-001",
            "GLUCOSE",
            101.2,
        )


def test_gateway_rejects_when_allowlist_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gateway, "_DEVICE_HMAC_KEY", "test-device-gateway-hmac-key")
    monkeypatch.setattr(gateway, "_ALLOWED_DEVICE_IDS", set())

    with pytest.raises(gateway.DeviceAuthError, match="allowlist is unavailable"):
        gateway.receive_device_result(
            "SYNTHETIC-SAMPLE-001",
            "GLUCOSE",
            101.2,
        )


def test_gateway_rejects_when_replay_protection_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_gateway(monkeypatch)

    def unavailable(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise RuntimeError("synthetic replay store outage")

    monkeypatch.setattr(cache, "get", unavailable)
    payload = _signed_payload("nonce-replay-store-unavailable")

    with pytest.raises(gateway.DeviceAuthError, match="replay protection is unavailable"):
        gateway.receive_device_result(**payload)


def test_gateway_accepts_only_authenticated_non_replayed_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_gateway(monkeypatch)
    payload = _signed_payload("nonce-authenticated-envelope")

    accepted = gateway.receive_device_result(**payload)

    assert accepted["status"] == "received"
    assert accepted["device_id"] == "ANALYZER-001"

    with pytest.raises(gateway.DeviceAuthError, match="Replayed nonce"):
        gateway.receive_device_result(**payload)
