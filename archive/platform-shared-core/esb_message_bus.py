from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from app.integration.esb.dead_letter import DeadLetterService
from app.integration.esb.idempotency import IdempotencyService
from app.integration.esb.priority import PriorityService
from app.integration.esb.router import ESBRouter
from app.integration.esb.types import ESBMessage

logger = logging.getLogger("gula.integration.esb.message_bus")


class ESBMessageBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
        self._router = ESBRouter()
        self._dead_letter = DeadLetterService()
        self._priority = PriorityService()
        self._idempotency = IdempotencyService()
        self._queue: list[ESBMessage] = []
        self._processing = False
        self._message_history: dict[str, ESBMessage] = {}
        self._max_queue_size = 10000

    @property
    def router(self) -> ESBRouter:
        return self._router

    @property
    def dead_letter(self) -> DeadLetterService:
        return self._dead_letter

    @property
    def priority_service(self) -> PriorityService:
        return self._priority

    @property
    def idempotency_service(self) -> IdempotencyService:
        return self._idempotency

    def publish(self, message: ESBMessage) -> str:
        if len(self._queue) >= self._max_queue_size:
            logger.warning("Message bus queue full, dropping message: %s", message.id)
            return ""

        self._priority.enqueue(message)
        self._message_history[message.id] = message
        logger.info("Message published: %s (%s)", message.id, message.event_name)
        return message.id

    def subscribe(self, event_name: str, handler: Callable) -> None:
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)
        self._router.register_route(event_name, handler.__name__)
        logger.info("Subscriber registered for event: %s", event_name)

    def unsubscribe(self, event_name: str, handler: Callable) -> None:
        handlers = self._subscribers.get(event_name, [])
        if handler in handlers:
            handlers.remove(handler)
            logger.info("Subscriber unregistered for event: %s", event_name)

    async def process_next(self) -> bool:
        message = self._priority.dequeue()
        if not message:
            return False

        if self._idempotency.is_duplicate(message.id):
            logger.info("Duplicate message skipped: %s", message.id)
            return True

        self._idempotency.mark_processed(message.id)
        handlers = self._subscribers.get(message.event_name, [])
        if not handlers:
            routed = self._router.route(message)
            if not routed:
                logger.warning("No handlers for message: %s", message.event_name)
                return True

        for handler in handlers:
            try:
                result = handler(message)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:
                logger.error("Handler failed for message %s: %s", message.id, exc)
                self._dead_letter.send(message, str(exc))

        return True

    async def process_all(self, max_messages: int = 100) -> int:
        count = 0
        for _ in range(min(max_messages, self._priority.size())):
            if await self.process_next():
                count += 1
        return count

    def get_message(self, message_id: str) -> ESBMessage | None:
        return self._message_history.get(message_id)

    def queue_size(self) -> int:
        return self._priority.size()

    def clear(self) -> None:
        self._queue.clear()
        self._message_history.clear()
        logger.info("Message bus cleared")
