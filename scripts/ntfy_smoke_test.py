from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import httpx


class BaseConnector:
    def __init__(self, name: str, version: str = "1.0.0", config: dict | None = None) -> None:
        self.name = name
        self.version = version
        self.config = config or {}
        self._connected = False


class ConnectorRegistry:
    registered: dict[str, type] = {}

    @classmethod
    def register(cls, name: str, connector_cls: type) -> None:
        cls.registered[name] = connector_cls


# Load only the connector module, avoiding the full app package's DB startup.
connectors_stub = types.ModuleType("backend.app.integration.connectors")
connectors_stub.BaseConnector = BaseConnector
connectors_stub.ConnectorRegistry = ConnectorRegistry
sys.modules["backend.app.integration.connectors"] = connectors_stub

module_path = Path(__file__).resolve().parents[1] / "backend/app/integration/connectors/ntfy.py"
spec = importlib.util.spec_from_file_location("gula_ntfy_connector", module_path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
NtfyConnector = module.NtfyConnector


async def main() -> None:
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.content
        seen["headers"] = dict(request.headers)
        return httpx.Response(200, json={"id": "smoke-test"})

    transport = httpx.MockTransport(handler)
    connector = NtfyConnector(
        config={"base_url": "https://ntfy.example.test", "topic": "gula-ops"},
    )
    connector._client = httpx.AsyncClient(transport=transport)
    connector._connected = True
    result = await connector.send(
        {"title": "smoke", "message": "incident=api_latency status=degraded", "priority": "high"},
    )
    await connector.disconnect()

    assert result["success"] is True, result
    assert seen["url"] == "https://ntfy.example.test/gula-ops"
    assert seen["body"] == b"incident=api_latency status=degraded"
    assert seen["headers"]["title"] == "smoke"
    assert seen["headers"]["priority"] == "high"
    assert ConnectorRegistry.registered["ntfy"] is NtfyConnector
    print("ntfy smoke test passed")


if __name__ == "__main__":
    asyncio.run(main())
