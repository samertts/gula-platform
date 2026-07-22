from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BatchJob:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    items: list[Any] = field(default_factory=list)
    status: str = "pending"
    total: int = 0
    completed: int = 0
    failed: int = 0
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None


class BatchProcessor:
    def __init__(self, batch_size: int = 50, max_concurrent_batches: int = 5):
        self._batch_size = batch_size
        self._semaphore = asyncio.Semaphore(max_concurrent_batches)
        self._jobs: dict[str, BatchJob] = {}

    async def process_batch(
        self,
        items: list[Any],
        processor: Callable,
        job_id: str | None = None,
    ) -> BatchJob:
        job = BatchJob(
            id=job_id or str(uuid.uuid4()),
            items=items,
            total=len(items),
        )
        self._jobs[job.id] = job

        batches = [
            items[i : i + self._batch_size]
            for i in range(0, len(items), self._batch_size)
        ]

        async def _process_batch(batch: list[Any]):
            async with self._semaphore:
                results = []
                for item in batch:
                    try:
                        result = await processor(item)
                        results.append(result)
                        job.completed += 1
                    except Exception as e:
                        logger.exception("Batch item failed: %s", e)
                        job.failed += 1
                        results.append(None)
                return results

        tasks = [asyncio.create_task(_process_batch(b)) for b in batches]
        await asyncio.gather(*tasks)

        job.status = "completed"
        job.completed_at = time.time()
        return job

    def get_job(self, job_id: str) -> BatchJob | None:
        return self._jobs.get(job_id)

    def all_jobs(self) -> list[BatchJob]:
        return list(self._jobs.values())
