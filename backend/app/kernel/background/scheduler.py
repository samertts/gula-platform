from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from backend.app.kernel.background.cron import CronEngine
from backend.app.kernel.background.task_queue import TaskQueue
from backend.app.kernel.background.worker_pool import WorkerPool
from backend.app.kernel.background.job_retry import JobRetry
from backend.app.kernel.background.distributed_locks import DistributedLockManager
from backend.app.kernel.background.priority_queue import PriorityQueue

if TYPE_CHECKING:
    from backend.app.kernel import Kernel

logger = logging.getLogger("gula.kernel.background")


class Scheduler:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.cron = CronEngine()
        self.task_queue = TaskQueue()
        self.worker_pool = WorkerPool()
        self.job_retry = JobRetry()
        self.distributed_locks = DistributedLockManager()
        self.priority_queue = PriorityQueue()
        self._running = False

    async def start(self) -> None:
        self._running = True
        self.worker_pool.start()

    async def stop(self) -> None:
        self._running = False
        self.worker_pool.stop()
