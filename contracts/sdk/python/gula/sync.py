from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from .client import GulaClient
from .exceptions import ConflictError, GulaError

logger = logging.getLogger("gula.sync")


@dataclass
class SyncEntry:
    id: str
    method: str
    path: str
    body: Optional[dict] = None
    created_at: float = field(default_factory=time.time)
    retries: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None


class SyncQueue:
    def __init__(self, file_path: str = "sync_queue.json"):
        self._file_path = file_path
        self._entries: list[SyncEntry] = []
        self._dirty = False
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._file_path):
            return
        try:
            with open(self._file_path) as f:
                data = json.load(f)
            for item in data:
                entry = SyncEntry(**item)
                self._entries.append(entry)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load sync queue: %s", e)

    def _save(self) -> None:
        if not self._dirty:
            return
        try:
            data = [
                {
                    "id": e.id,
                    "method": e.method,
                    "path": e.path,
                    "body": e.body,
                    "created_at": e.created_at,
                    "retries": e.retries,
                    "max_retries": e.max_retries,
                    "last_error": e.last_error,
                }
                for e in self._entries
            ]
            with open(self._file_path, "w") as f:
                json.dump(data, f)
            self._dirty = False
        except OSError as e:
            logger.error("Failed to save sync queue: %s", e)

    def enqueue(self, method: str, path: str, body: Optional[dict] = None) -> str:
        entry_id = str(uuid.uuid4())
        entry = SyncEntry(id=entry_id, method=method, path=path, body=body)
        self._entries.append(entry)
        self._dirty = True
        self._save()
        logger.info("Enqueued %s %s (id=%s)", method.upper(), path, entry_id)
        return entry_id

    def dequeue(self) -> Optional[SyncEntry]:
        if not self._entries:
            return None
        expired = [e for e in self._entries if e.retries >= e.max_retries]
        for e in expired:
            logger.warning("Dropping expired entry %s after %d retries", e.id, e.retries)
            self._entries.remove(e)
            self._dirty = True
        if not self._entries:
            return None
        entry = self._entries.pop(0)
        self._dirty = True
        return entry

    def requeue(self, entry: SyncEntry) -> None:
        entry.retries += 1
        if entry.retries >= entry.max_retries:
            logger.error("Entry %s exceeded max retries (%d), dropping", entry.id, entry.max_retries)
            self._dirty = True
            self._save()
            return
        self._entries.append(entry)
        self._dirty = True
        self._save()

    @property
    def pending_count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        self._dirty = True
        self._save()


class ConflictResolver:
    STRATEGY_CLIENT_WINS = "client_wins"
    STRATEGY_SERVER_WINS = "server_wins"
    STRATEGY_MERGE = "merge"

    def __init__(self, strategy: str = STRATEGY_CLIENT_WINS):
        if strategy not in (self.STRATEGY_CLIENT_WINS, self.STRATEGY_SERVER_WINS, self.STRATEGY_MERGE):
            raise ValueError(f"Invalid strategy: {strategy}")
        self._strategy = strategy
        self._merge_fn: Optional[Callable[[dict, dict], dict]] = None

    def set_merge_fn(self, fn: Callable[[dict, dict], dict]) -> None:
        self._merge_fn = fn

    def resolve(self, client_data: dict, server_data: dict) -> dict:
        if self._strategy == self.STRATEGY_CLIENT_WINS:
            return client_data
        if self._strategy == self.STRATEGY_SERVER_WINS:
            return server_data
        if self._merge_fn:
            return self._merge_fn(client_data, server_data)
        return client_data


class SyncEngine:
    def __init__(
        self,
        client: GulaClient,
        queue: Optional[SyncQueue] = None,
        conflict_resolver: Optional[ConflictResolver] = None,
        poll_interval: float = 5.0,
    ):
        self._client = client
        self._queue = queue or SyncQueue()
        self._resolver = conflict_resolver or ConflictResolver()
        self._poll_interval = poll_interval
        self._running = False

    @property
    def queue(self) -> SyncQueue:
        return self._queue

    def enqueue(self, method: str, path: str, body: Optional[dict] = None) -> str:
        return self._queue.enqueue(method, path, body)

    async def process_once(self) -> int:
        processed = 0
        while True:
            entry = self._queue.dequeue()
            if entry is None:
                break
            try:
                await self._client._request(entry.method, entry.path, body=entry.body)
                logger.info("Synced %s %s (id=%s)", entry.method.upper(), entry.path, entry.id)
                processed += 1
            except ConflictError as e:
                logger.warning("Conflict on %s %s: %s", entry.method, entry.path, e)
                self._queue.requeue(entry)
            except GulaError as e:
                if e.status_code and 400 <= e.status_code < 500 and e.status_code not in (409, 429):
                    logger.error("Non-retryable error %d for %s %s, dropping", e.status_code, entry.method, entry.path)
                else:
                    self._queue.requeue(entry)
            except Exception as e:
                logger.warning("Sync error for %s %s: %s — requeueing", entry.method, entry.path, e)
                self._queue.requeue(entry)
        return processed

    async def run_forever(self) -> None:
        self._running = True
        logger.info("SyncEngine started (poll interval=%ss)", self._poll_interval)
        while self._running:
            try:
                processed = await self.process_once()
                if processed == 0:
                    await asyncio.sleep(self._poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("SyncEngine error: %s", e)
                await asyncio.sleep(self._poll_interval * 2)
        logger.info("SyncEngine stopped")

    async def stop(self) -> None:
        self._running = False
