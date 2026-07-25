from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.kernel.event_bus.bus import EventBus
from app.kernel.event_bus.events import Event

logger = logging.getLogger("gula.health_data.streaming.pipeline")


class StreamSource(ABC):
    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def read(self) -> list[dict[str, Any]]: ...


class EventBusSource(StreamSource):
    def __init__(self, bus: EventBus, event_names: list[str] | None = None):
        self._bus = bus
        self._event_names = event_names
        self._buffer: list[dict] = []

    async def start(self) -> None:
        for name in self._event_names or []:
            self._bus.subscribe(name, self._on_event)

    async def stop(self) -> None:
        for name in self._event_names or []:
            self._bus.unsubscribe(name, self._on_event)

    async def read(self) -> list[dict[str, Any]]:
        batch = list(self._buffer)
        self._buffer.clear()
        return batch

    def _on_event(self, event: Event) -> None:
        self._buffer.append(
            {
                "event_id": event.id,
                "event_name": event.name,
                "data": event.data,
                "version": event.version,
                "timestamp": event.timestamp,
                "correlation_id": event.correlation_id,
                "source": event.source,
            }
        )


class StreamProcessor(ABC):
    @abstractmethod
    async def process(self, record: dict[str, Any]) -> dict[str, Any] | None: ...


class StreamFilter(StreamProcessor):
    def __init__(self, condition: Callable[[dict], bool]):
        self._condition = condition

    async def process(self, record: dict[str, Any]) -> dict[str, Any] | None:
        return record if self._condition(record) else None


class StreamTransform(StreamProcessor):
    def __init__(self, transformer: Callable[[dict], dict]):
        self._transformer = transformer

    async def process(self, record: dict[str, Any]) -> dict[str, Any] | None:
        return self._transformer(record)


class StreamRouter(StreamProcessor):
    def __init__(self, routes: dict[str, list[Callable]]):
        self._routes = routes

    async def process(self, record: dict[str, Any]) -> dict[str, Any] | None:
        event_name = record.get("event_name", "")
        handlers = self._routes.get(event_name, [])
        result = record
        for handler in handlers:
            result = handler(result)
            if result is None:
                return None
        return result


@dataclass
class StreamPipeline:
    name: str
    source: StreamSource
    processors: list[StreamProcessor] = field(default_factory=list)
    sinks: list[Any] = field(default_factory=list)
    batch_size: int = 100
    poll_interval_s: float = 1.0
    running: bool = False

    async def start(self) -> None:
        self.running = True
        await self.source.start()
        logger.info("Stream pipeline started: %s", self.name)

    async def stop(self) -> None:
        self.running = False
        await self.source.stop()
        logger.info("Stream pipeline stopped: %s", self.name)

    def add_processor(self, processor: StreamProcessor) -> None:
        self.processors.append(processor)

    def add_sink(self, sink: Any) -> None:
        self.sinks.append(sink)

    async def run_loop(self) -> None:
        while self.running:
            try:
                records = await self.source.read()
                if not records:
                    await asyncio.sleep(self.poll_interval_s)
                    continue

                processed: list[dict] = []
                for record in records:
                    current = record
                    for processor in self.processors:
                        current = await processor.process(current)
                        if current is None:
                            break
                    if current is not None:
                        processed.append(current)

                for batch_start in range(0, len(processed), self.batch_size):
                    batch = processed[batch_start : batch_start + self.batch_size]
                    for sink in self.sinks:
                        try:
                            await sink.write(batch)
                        except Exception as exc:
                            logger.error("Sink %s write failed: %s", sink.__class__.__name__, exc)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Stream pipeline %s error: %s", self.name, exc)
                await asyncio.sleep(self.poll_interval_s)
