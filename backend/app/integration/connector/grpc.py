from __future__ import annotations

import logging
from typing import Any

from backend.app.integration.connector.spec import (
    ConnectorSpec,
    ConnectorStatus,
    ConnectorType,
)

logger = logging.getLogger("gula.integration.connector.grpc")


class GrpcConnector:
    def __init__(self, spec: ConnectorSpec):
        if spec.connector_type != ConnectorType.GRPC:
            raise ValueError(
                f"GrpcConnector requires type GRPC, got {spec.connector_type.name}",
            )
        self.spec = spec
        self._channel = None
        self._stubs: dict[str, Any] = {}

    async def connect(self) -> bool:
        try:
            import grpc
        except ImportError:
            logger.error("grpc library not installed")
            self.spec.status = ConnectorStatus.FAILED
            return False

        try:
            target = self.spec.endpoints[0].url if self.spec.endpoints else ""
            self._channel = grpc.aio.insecure_channel(target)
            self.spec.status = ConnectorStatus.CONNECTED
            logger.info("gRPC connected: %s", target)
            return True
        except Exception as exc:
            self.spec.status = ConnectorStatus.FAILED
            self.spec.health.error = str(exc)
            logger.error("gRPC connection failed: %s", exc)
            return False

    async def disconnect(self) -> None:
        if self._channel:
            await self._channel.close()
            self._channel = None
        self.spec.status = ConnectorStatus.DISCONNECTED

    def register_stub(self, name: str, stub) -> None:
        self._stubs[name] = stub

    def get_stub(self, name: str):
        return self._stubs.get(name)
