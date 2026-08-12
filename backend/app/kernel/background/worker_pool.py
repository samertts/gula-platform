from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger("gula.kernel.background.worker")


class WorkerPool:
    def __init__(self, size: int = 4):
        self._size = size
        self._workers: list[asyncio.Task] = []
        self._running = False

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    @property
    def size(self) -> int:
        return self._size
