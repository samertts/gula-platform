from __future__ import annotations

import hashlib
from collections import deque
from collections.abc import Iterable
from typing import Any


def content_key(device_id: str, results: Iterable[Any]) -> str:
    """Stable id for a failed-delivery batch, derived from its content.

    Used as the downstream sync-engine item_id so that staging the same
    failed batch more than once collapses onto one entry instead of piling
    up duplicates (the sync engine dedupes by item_id, so the id must be
    deterministic — a fresh random id per attempt defeats that dedup).
    """
    digest = hashlib.sha256()
    digest.update(device_id.encode())
    for result in results:
        digest.update(
            "|".join(
                [
                    str(getattr(result, "patient_id", "")),
                    str(getattr(result, "test_code", "")),
                    str(getattr(result, "value", "")),
                    str(getattr(result, "timestamp", "")),
                ]
            ).encode()
        )
        digest.update(b"\x00")
    return digest.hexdigest()


class RetryQueue:
    """Simple in-memory queue for offline/failed upstream deliveries."""

    def __init__(self) -> None:
        self._items: deque[dict[str, Any]] = deque()

    def enqueue(self, item: dict[str, Any]) -> None:
        self._items.append(item)

    def dequeue(self) -> dict[str, Any] | None:
        if not self._items:
            return None
        return self._items.popleft()

    def size(self) -> int:
        return len(self._items)

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._items)

    def drain(self) -> list[dict[str, Any]]:
        """Atomically return and remove every currently-queued item.

        Use this (not list_all()) for any consumer that acts on queued
        items — list_all() never removes anything, so a caller that reads
        it on every request would re-process the same historical items
        forever.
        """
        items = list(self._items)
        self._items.clear()
        return items
