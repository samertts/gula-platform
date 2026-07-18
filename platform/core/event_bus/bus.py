import asyncio
import logging
from typing import Any, Callable

from platform.core.event_bus.event import Event, Topic


class EventBus:
    def __init__(self):
        self._logger = logging.getLogger("gula.event_bus")
        self._topics: dict[str, Topic] = {}
        self._global_subscribers: list[Callable[[Event], Any]] = []
        self._dead_letter_queue: list[dict[str, Any]] = []
        self._retry_policy = {"max_retries": 3, "base_delay": 1.0, "max_delay": 30.0}

    def create_topic(self, name: str, description: str = "") -> Topic:
        if name in self._topics:
            raise ValueError(f"Topic '{name}' already exists")
        topic = Topic(name, description)
        self._topics[name] = topic
        self._logger.debug("Topic created: %s", name)
        return topic

    def get_topic(self, name: str) -> Topic | None:
        return self._topics.get(name)

    def topic(self, name: str) -> Topic:
        t = self._topics.get(name)
        if t is None:
            t = self.create_topic(name)
        return t

    def subscribe(self, topic: str, handler: Callable[[Event], Any]) -> None:
        t = self.topic(topic)
        t.subscribe(handler)
        self._logger.debug("Subscriber added to topic '%s'", topic)

    def unsubscribe(self, topic: str, handler: Callable[[Event], Any]) -> None:
        t = self._topics.get(topic)
        if t:
            t.unsubscribe(handler)

    def add_global_subscriber(self, handler: Callable[[Event], Any]) -> None:
        self._global_subscribers.append(handler)

    async def publish(self, topic: str, event: Event) -> list[Any]:
        t = self._topics.get(topic)
        if not t:
            self._logger.warning("Publishing to unknown topic '%s', creating", topic)
            t = self.create_topic(topic)
        results = await t.publish(event)
        for gs in self._global_subscribers:
            try:
                result = gs(event)
                if hasattr(result, "__await__"):
                    await result
            except Exception as e:
                self._logger.error("Global subscriber error: %s", e)
        return results

    async def publish_with_retry(self, topic: str, event: Event) -> list[Any]:
        last_error = None
        for attempt in range(self._retry_policy["max_retries"]):
            try:
                return await self.publish(topic, event)
            except Exception as e:
                last_error = e
                delay = min(
                    self._retry_policy["base_delay"] * (2 ** attempt),
                    self._retry_policy["max_delay"],
                )
                self._logger.warning("Retry %d/%d for topic '%s' in %.1fs", attempt + 1, self._retry_policy["max_retries"], topic, delay)
                await asyncio.sleep(delay)
        self._dead_letter_queue.append({
            "topic": topic,
            "event_id": event.event_id,
            "error": str(last_error),
            "event": event,
        })
        self._logger.error("Event moved to DLQ: %s on topic %s", event.event_id, topic)
        raise last_error

    def get_dead_letter_queue(self) -> list[dict[str, Any]]:
        return list(self._dead_letter_queue)

    def replay_dead_letter(self, max_items: int = 10) -> list[str]:
        replayed = []
        remaining = []
        for item in self._dead_letter_queue:
            if len(replayed) < max_items:
                replayed.append(item["event_id"])
            else:
                remaining.append(item)
        self._dead_letter_queue = remaining
        return replayed

    def clear_dead_letter(self) -> None:
        self._dead_letter_queue.clear()

    def topic_count(self) -> int:
        return len(self._topics)

    def subscriber_count(self) -> int:
        return sum(len(t.subscribers) for t in self._topics.values())

    def get_metrics(self) -> dict[str, Any]:
        return {
            "topics": self.topic_count(),
            "subscribers": self.subscriber_count(),
            "dead_letter_queue_size": len(self._dead_letter_queue),
        }
