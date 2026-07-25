from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GatewayConfig:
    endpoint: str = ""
    timeout: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    headers: dict[str, str] = field(default_factory=lambda: {"Content-Type": "application/json"})
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class GatewayMessage:
    id: str = ""
    payload: Any = None
    content_type: str = "application/json"
    headers: dict[str, str] = field(default_factory=dict)
    correlation_id: str = ""
    source: str = ""
    destination: str = ""


@dataclass
class GatewayResult:
    success: bool = False
    status_code: int = 0
    data: Any = None
    error: str | None = None
    latency_ms: float = 0.0
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


class MessageGateway(ABC):
    def __init__(self, name: str, config: GatewayConfig | None = None):
        self.name = name
        self.config = config or GatewayConfig()
        self._connected = False

    @abstractmethod
    async def connect(self) -> bool: ...

    @abstractmethod
    async def disconnect(self) -> bool: ...

    @abstractmethod
    async def send(self, message: GatewayMessage) -> GatewayResult: ...

    @abstractmethod
    async def receive(self) -> GatewayMessage | None: ...

    @abstractmethod
    async def transform(self, message: GatewayMessage) -> GatewayMessage: ...

    async def health_check(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "connected": self._connected,
            "status": "healthy" if self._connected else "disconnected",
        }

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.disconnect()
