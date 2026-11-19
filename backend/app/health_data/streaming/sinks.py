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


#: IA-072. Three of the four sinks below reported a write they never performed.
#: ``PostgresSink``, ``ClickHouseSink`` and ``ObjectStoreSink`` each logged
#: "writing N records to <destination>" and then ``return len(records)``. The
#: record count IS this interface's success value -- ``Sink.write`` is annotated
#: ``-> int`` and ``WebSocketSink`` returns the number actually delivered -- so
#: returning ``len(records)`` claimed full delivery of a batch that went
#: nowhere. None of the three ever used the connection string, host or bucket
#: it was constructed with.
#:
#: ``ObjectStoreSink`` was the most deceptive: it built a real filename,
#: serialised the batch with ``json.dumps`` and logged the exact byte count, so
#: its log line read as evidence of a completed upload.
#:
#: ``WebSocketSink`` is left exactly as it was. It genuinely iterates its
#: registered connections, awaits ``conn.send``, drops the ones that fail and
#: returns the number actually delivered. It is the one real sink here.
#:
#: Reachability: latent. Nothing outside ``app/health_data/streaming``
#: constructs any of these -- the package ``__init__`` re-exports them and no
#: other module in backend/ or services/ imports them. So this is an exported
#: surface that would have lost its first consumer's data silently, repaired
#: now rather than after someone wires a health-data stream to it.

STREAM_SINK_UNAVAILABLE = (
    "this sink is declared but not implemented: it never connected to its "
    "destination and reported the record count as if it had. See IA-072."
)


class StreamSinkUnavailable(RuntimeError):
    """Raised instead of returning a delivery count for records never delivered."""


class PostgresSink(Sink):
    def __init__(self, connection_string: str = "", table_name: str = "stream_events"):
        self._connection_string = connection_string
        self._table_name = table_name

    async def write(self, records: list[dict[str, Any]]) -> int:
        raise StreamSinkUnavailable(
            f"PostgresSink.write cannot deliver {len(records)} record(s) to "
            f"{self._table_name!r}: {STREAM_SINK_UNAVAILABLE}",
        )

    async def close(self) -> None:
        pass


class ClickHouseSink(Sink):
    def __init__(self, host: str = "localhost", port: int = 9000, table: str = "stream_events"):
        self._host = host
        self._port = port
        self._table = table

    async def write(self, records: list[dict[str, Any]]) -> int:
        raise StreamSinkUnavailable(
            f"ClickHouseSink.write cannot deliver {len(records)} record(s) to "
            f"{self._table!r} on {self._host}:{self._port}: {STREAM_SINK_UNAVAILABLE}",
        )

    async def close(self) -> None:
        pass


class ObjectStoreSink(Sink):
    def __init__(self, bucket: str = "streaming", prefix: str = "events"):
        self._bucket = bucket
        self._prefix = prefix

    async def write(self, records: list[dict[str, Any]]) -> int:
        # The previous body serialised the batch and logged its byte count
        # before returning the count, which made the log read like proof of a
        # write. Nothing was ever uploaded.
        raise StreamSinkUnavailable(
            f"ObjectStoreSink.write cannot deliver {len(records)} record(s) to "
            f"{self._bucket}/{self._prefix}: {STREAM_SINK_UNAVAILABLE}",
        )

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
