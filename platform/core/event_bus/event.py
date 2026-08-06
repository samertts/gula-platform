import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class Event:
    topic: str
    data: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = ""
    causation_id: str = ""
    aggregate_id: str = ""
    aggregate_type: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return type(self).__name__


class Topic:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.subscribers: list[callable] = []

    def subscribe(self, handler: callable) -> None:
        self.subscribers.append(handler)

    def unsubscribe(self, handler: callable) -> None:
        if handler in self.subscribers:
            self.subscribers.remove(handler)

    async def publish(self, event: Event) -> list[Any]:
        results = []
        for subscriber in self.subscribers:
            try:
                result = subscriber(event)
                if hasattr(result, "__await__"):
                    result = await result
                results.append(result)
            except Exception:
                results.append(None)
        return results
