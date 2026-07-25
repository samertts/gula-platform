from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger("gula.health_data.streaming.sinks")


class Sink(ABC):
    @abstractmethod
    async def write(self, records: list[dict[str, Any]]) -> int: ...

    @abstractmethod
    async def close(self) -> None: ...


class SinkRegistry:
    def __init__(self):
        self._sinks: dict[str, Sink] = {}

    def register(self, name: str, sink: Sink) -> None:
        self._sinks[name] = sink
        logger.info("Sink registered: %s (%s)", name, sink.__class__.__name__)

    def unregister(self, name: str) -> None:
        self._sinks.pop(name, None)

    def get(self, name: str) -> Sink | None:
        return self._sinks.get(name)

    def list(self) -> list[str]:
        return list(self._sinks.keys())


class PostgresSink(Sink):
    def __init__(self, connection_string: str = "", table_name: str = "stream_events"):
        self._connection_string = connection_string
        self._table_name = table_name

    async def write(self, records: list[dict[str, Any]]) -> int:
        logger.info("PostgresSink: writing %d records to %s", len(records), self._table_name)
        return len(records)

    async def close(self) -> None:
        pass


class ClickHouseSink(Sink):
    def __init__(self, host: str = "localhost", port: int = 9000, table: str = "stream_events"):
        self._host = host
        self._port = port
        self._table = table

    async def write(self, records: list[dict[str, Any]]) -> int:
        logger.info(
            "ClickHouseSink: writing %d records to %s@%s:%d",
            len(records),
            self._table,
            self._host,
            self._port,
        )
        return len(records)

    async def close(self) -> None:
        pass


class ObjectStoreSink(Sink):
    def __init__(self, bucket: str = "streaming", prefix: str = "events"):
        self._bucket = bucket
        self._prefix = prefix

    async def write(self, records: list[dict[str, Any]]) -> int:
        import time

        filename = f"{self._prefix}/batch_{int(time.time())}_{len(records)}.json"
        payload = json.dumps(records, default=str, ensure_ascii=False)
        logger.info(
            "ObjectStoreSink: writing %d records to %s/%s (%d bytes)",
            len(records),
            self._bucket,
            filename,
            len(payload),
        )
        return len(records)

    async def close(self) -> None:
        pass


class WebSocketSink(Sink):
    def __init__(self):
        self._connections: list[Any] = []

    async def register_connection(self, connection: Any) -> None:
        self._connections.append(connection)

    async def unregister_connection(self, connection: Any) -> None:
        if connection in self._connections:
            self._connections.remove(connection)

    async def write(self, records: list[dict[str, Any]]) -> int:
        delivered = 0
        disconnected = []
        for conn in self._connections:
            try:
                for record in records:
                    await conn.send(json.dumps(record, default=str))
                delivered += len(records)
            except Exception as exc:
                logger.warning("WebSocket connection lost: %s", exc)
                disconnected.append(conn)

        for conn in disconnected:
            await self.unregister_connection(conn)

        return delivered

    async def close(self) -> None:
        self._connections.clear()
