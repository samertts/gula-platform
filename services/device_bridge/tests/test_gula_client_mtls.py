from __future__ import annotations

import asyncio

import pytest
from app.integration.gula_client import DeviceBridgeTransportConfigurationError, GulaClient


def test_disabled_client_never_forwards_results() -> None:
    client = GulaClient(base_url=None, lab_id="LAB001", enabled=False)

    response = asyncio.run(client.send_results([]))

    assert response == {"status": "failed", "error": "device_bridge_forwarding_disabled"}


def test_enabled_client_rejects_http_backend() -> None:
    with pytest.raises(DeviceBridgeTransportConfigurationError, match="HTTPS"):
        GulaClient(
            base_url="http://gula.local",
            lab_id="LAB001",
            enabled=True,
            ca_bundle_path="/run/secrets/bridge-ca.pem",
            client_cert_path="/run/secrets/bridge-client.pem",
            client_key_path="/run/secrets/bridge-client.key",
        )


def test_enabled_client_rejects_missing_mutual_tls_material() -> None:
    with pytest.raises(
        DeviceBridgeTransportConfigurationError, match="CA, client certificate, and client key"
    ):
        GulaClient(base_url="https://gula.local", lab_id="LAB001", enabled=True)


def test_enabled_client_fails_closed_when_certificate_files_are_unavailable() -> None:
    client = GulaClient(
        base_url="https://gula.local",
        lab_id="LAB001",
        enabled=True,
        ca_bundle_path="/missing/bridge-ca.pem",
        client_cert_path="/missing/bridge-client.pem",
        client_key_path="/missing/bridge-client.key",
    )

    response = asyncio.run(client.send_results([]))

    assert response == {"status": "failed", "error": "device_bridge_mtls_unavailable"}
