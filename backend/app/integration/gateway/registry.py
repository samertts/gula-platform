from __future__ import annotations

import logging
from typing import Any

from backend.app.integration.gateway.base import MessageGateway

logger = logging.getLogger("gula.integration.gateway.registry")


class GatewayRegistry:
    _gateways: dict[str, MessageGateway] = {}

    @classmethod
    def register(cls, gateway: MessageGateway) -> None:
        cls._gateways[gateway.name] = gateway
        logger.info("Gateway registered: %s (%s)", gateway.name, type(gateway).__name__)

    @classmethod
    def get(cls, name: str) -> MessageGateway | None:
        return cls._gateways.get(name)

    @classmethod
    def list_all(cls) -> list[MessageGateway]:
        return list(cls._gateways.values())

    @classmethod
    def list_by_protocol(cls, protocol: str) -> list[MessageGateway]:
        return [g for g in cls._gateways.values() if type(g).__name__.lower().startswith(protocol.lower())]

    @classmethod
    def unregister(cls, name: str) -> bool:
        if name in cls._gateways:
            del cls._gateways[name]
            logger.info("Gateway unregistered: %s", name)
            return True
        return False

    @classmethod
    def health_all(cls) -> dict[str, Any]:
        return {name: {"connected": gw._connected} for name, gw in cls._gateways.items()}
