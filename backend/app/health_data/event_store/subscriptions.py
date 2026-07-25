from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app._compat import UTC
from app.health_data.event_store.store import HealthEventStore, StoredEvent

logger = logging.getLogger("gula.health_data.event_store.subscriptions")


class SubscriptionType(Enum):
    CATCH_UP = "catch_up"
    PERSISTENT = "persistent"
    COMPETING_CONSUMER = "competing_consumer"


@dataclass
class Subscription:
    id: str
    event_types: list[str]
    handler: Callable[[StoredEvent], Any]
    sub_type: SubscriptionType = SubscriptionType.CATCH_UP
    last_processed_version: int = 0
    batch_size: int = 100
    max_retries: int = 3
    group: str | None = None
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class SubscriptionManager:
    def __init__(self, store: HealthEventStore):
        self.store = store
        self._subscriptions: dict[str, Subscription] = {}
        self._group_members: dict[str, list[str]] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}

    def register(self, sub: Subscription) -> None:
        self._subscriptions[sub.id] = sub
        if sub.group:
            self._group_members.setdefault(sub.group, []).append(sub.id)
        logger.info(
            "Subscription registered: %s (type=%s, events=%s)",
            sub.id,
            sub.sub_type.value,
            sub.event_types,
        )

    def unregister(self, sub_id: str) -> None:
        sub = self._subscriptions.pop(sub_id, None)
        if sub and sub.group:
            members = self._group_members.get(sub.group, [])
            if sub_id in members:
                members.remove(sub_id)
            logger.info("Subscription unregistered: %s", sub_id)

    def get(self, sub_id: str) -> Subscription | None:
        return self._subscriptions.get(sub_id)

    def list(self) -> list[Subscription]:
        return list(self._subscriptions.values())

    def pause(self, sub_id: str) -> None:
        sub = self._subscriptions.get(sub_id)
        if sub:
            sub.active = False
            logger.info("Subscription paused: %s", sub_id)

    def resume(self, sub_id: str) -> None:
        sub = self._subscriptions.get(sub_id)
        if sub:
            sub.active = True
            logger.info("Subscription resumed: %s", sub_id)

    async def process_catch_up(self, sub_id: str) -> int:
        sub = self._subscriptions.get(sub_id)
        if not sub or not sub.active:
            return 0

        events = self.store.replay_all(after_version=sub.last_processed_version)
        filtered = [e for e in events if e.event_name in sub.event_types]
        processed = 0

        for batch_start in range(0, len(filtered), sub.batch_size):
            batch = filtered[batch_start : batch_start + sub.batch_size]
            for event in batch:
                try:
                    await self._call_handler(sub, event)
                    sub.last_processed_version += 1
                    processed += 1
                except Exception as exc:
                    logger.error(
                        "Handler failed for subscription %s on event %s: %s",
                        sub_id,
                        event.event_id,
                        exc,
                    )
                    if sub.sub_type == SubscriptionType.PERSISTENT:
                        raise

        return processed

    async def process_competing(self, group: str, consumer_id: str) -> int:
        members = self._group_members.get(group, [])
        if not members:
            return 0

        events = self.store.replay_all()
        processed = 0

        for event in events:
            target_idx = hash(event.event_id) % len(members)
            target_id = members[target_idx]
            sub = self._subscriptions.get(target_id)

            if sub and sub.active and event.event_name in sub.event_types:
                try:
                    await self._call_handler(sub, event)
                    processed += 1
                except Exception as exc:
                    logger.error(
                        "Competing consumer %s failed on event %s: %s",
                        consumer_id,
                        event.event_id,
                        exc,
                    )

        return processed

    async def _call_handler(self, sub: Subscription, event: StoredEvent) -> None:
        for attempt in range(sub.max_retries):
            try:
                result = sub.handler(event)
                if asyncio.iscoroutine(result):
                    await result
                return
            except Exception as exc:
                logger.warning(
                    "Handler attempt %d/%d failed for %s: %s",
                    attempt + 1,
                    sub.max_retries,
                    sub.id,
                    exc,
                )
                if attempt < sub.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                else:
                    raise
