"""Device Registry — manages instrument connections and protocol routing."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("gula.lims.integration.device_registry")


@dataclass
class DeviceConnection:
    """Active instrument connection state."""

    instrument_id: int
    instrument_code: str
    protocol: str  # astm, hl7, fhir, rest
    host: str = ""
    port: int = 0
    connected: bool = False
    connected_at: datetime | None = None
    last_heartbeat: datetime | None = None
    error_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class DeviceRegistry:
    """Registry of connected instruments and their protocols.

    Maintains active connections and routes messages to the correct
    instrument handler.
    """

    def __init__(self):
        self._connections: dict[int, DeviceConnection] = {}

    def register(self, connection: DeviceConnection) -> None:
        self._connections[connection.instrument_id] = connection
        logger.info(
            "Device registered: %s (protocol=%s)", connection.instrument_code, connection.protocol,
        )

    def unregister(self, instrument_id: int) -> None:
        self._connections.pop(instrument_id, None)

    def get(self, instrument_id: int) -> DeviceConnection | None:
        return self._connections.get(instrument_id)

    def get_by_code(self, code: str) -> DeviceConnection | None:
        for conn in self._connections.values():
            if conn.instrument_code == code:
                return conn
        return None

    def list_active(self) -> list[DeviceConnection]:
        return [c for c in self._connections.values() if c.connected]

    def mark_heartbeat(self, instrument_id: int) -> None:
        conn = self._connections.get(instrument_id)
        if conn:
            conn.last_heartbeat = datetime.now(UTC)
            conn.connected = True

    def mark_disconnected(self, instrument_id: int) -> None:
        conn = self._connections.get(instrument_id)
        if conn:
            conn.connected = False

    def count(self) -> int:
        return len(self._connections)


# Singleton registry
device_registry = DeviceRegistry()
