from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Self

logger = logging.getLogger("gula.integration.connectors")


class ConnectorRegistry:
    _connectors: dict[str, type[BaseConnector]] = {}

    @classmethod
    def register(cls, name: str, connector_cls: type[BaseConnector]) -> None:
        cls._connectors[name] = connector_cls
        logger.info("Connector registered: %s (%s)", name, connector_cls.__name__)

    @classmethod
    def get(cls, name: str) -> type[BaseConnector]:
        if name not in cls._connectors:
            raise KeyError(f"Connector not found: {name}")
        return cls._connectors[name]

    @classmethod
    def list_connectors(cls) -> list[str]:
        return list(cls._connectors.keys())

    @classmethod
    def get_status_all(cls) -> list[dict[str, Any]]:
        return [
            {"name": name, "connector_class": cls_.__name__}
            for name, cls_ in cls._connectors.items()
        ]


class BaseConnector(ABC):
    name: str
    version: str
    config: dict[str, Any]

    def __init__(self, name: str, version: str = "1.0.0", config: dict[str, Any] | None = None) -> None:
        self.name = name
        self.version = version
        self.config = config or {}
        self._connected = False

    @abstractmethod
    async def connect(self) -> bool:
        ...

    @abstractmethod
    async def disconnect(self) -> bool:
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        ...

    @abstractmethod
    async def send(self, data: dict[str, Any]) -> dict[str, Any]:
        ...

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.disconnect()
