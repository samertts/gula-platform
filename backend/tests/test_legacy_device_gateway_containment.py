from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

GATEWAY_PATH = Path(__file__).resolve().parents[1] / "gateway" / "device_gateway.py"


def _load_gateway() -> ModuleType:
    spec = importlib.util.spec_from_file_location("legacy_device_gateway", GATEWAY_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_legacy_device_gateway_is_fail_closed_and_has_no_transport_defaults() -> None:
    gateway = _load_gateway()

    for operation, argument in (
        (gateway.parse_message, "1|2|synthetic"),
        (gateway.send_result, {"synthetic": "value"}),
        (gateway.run_server, None),
    ):
        with pytest.raises(gateway.LegacyDeviceGatewayDisabledError):
            if argument is None:
                operation()
            else:
                operation(argument)

    source = GATEWAY_PATH.read_text(encoding="utf-8")
    assert "import socket" not in source
    assert "import requests" not in source
    assert "http://" not in source
    assert "devicesecret" not in source
