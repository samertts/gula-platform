"""NC013-C03 — gRPC gateway must fail closed and never echo request payloads."""

from __future__ import annotations

import asyncio
import builtins
import json

from app.integration.gateway.base import GatewayConfig, GatewayMessage
from app.integration.gateway.grpc_gateway import GRPCGateway


def test_connect_fails_closed_when_grpc_is_unavailable(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object):
        if name == "grpc":
            raise ImportError("simulated missing grpc")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    gateway = GRPCGateway(config=GatewayConfig(endpoint="localhost:50051"))

    assert asyncio.run(gateway.connect()) is False
    assert gateway._connected is False
    assert asyncio.run(gateway.health_check())["status"] == "disconnected"


def test_send_without_connection_returns_failure() -> None:
    gateway = GRPCGateway(config=GatewayConfig(endpoint="localhost:50051"))
    result = asyncio.run(gateway.send(GatewayMessage(payload={"patient": "synthetic"})))

    assert result.success is False
    assert result.data is None
    assert "not_connected" in (result.error or "")


def test_send_uses_real_channel_response_and_does_not_echo_payload() -> None:
    class FakeCall:
        def __init__(self, response: bytes) -> None:
            self.response = response
            self.captured: dict = {}

        def __call__(self, payload: bytes, **kwargs: object):
            async def respond() -> bytes:
                self.captured = {"payload": payload, **kwargs}
                return self.response

            return respond()

    class FakeChannel:
        def __init__(self, response: bytes) -> None:
            self.call = FakeCall(response)
            self.path: str | None = None
            self.closed = False

        def unary_unary(self, path: str) -> FakeCall:
            self.path = path
            return self.call

        async def close(self) -> None:
            self.closed = True

    expected_response = {"delivered": True, "echo": False}
    channel = FakeChannel(json.dumps(expected_response).encode())
    gateway = GRPCGateway(config=GatewayConfig(endpoint="localhost:50051"))
    gateway._connected = True
    gateway._channel = channel

    result = asyncio.run(
        gateway.send(
            GatewayMessage(
                payload={"ping": 1},
                destination="lab.service",
                headers={"method": "Submit"},
            ),
        ),
    )

    assert result.success is True
    assert result.data == expected_response
    assert channel.path == "/lab.service/Submit"
    assert channel.call.captured["payload"] == b'{"ping": 1}'
    assert channel.call.captured["payload"] != result.data
    assert asyncio.run(gateway.disconnect()) is True
    assert channel.closed is True
