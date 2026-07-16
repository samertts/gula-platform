from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.kernel.event_bus.events import Event

logger = logging.getLogger("gula.kernel.event_bus.recovery")


class RecoveryStrategy:
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    BATCHED = "batched"


@dataclass
class RecoveryJob:
    id: str = ""
    source: str = ""
    target: str = ""
    strategy: str = RecoveryStrategy.SEQUENTIAL
    events: list[Event] = field(default_factory=list)
    status: str = "pending"
    progress: int = 0
    total: int = 0
    failed: int = 0
    succeeded: int = 0
    started_at: float = 0.0
    completed_at: float | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4())
        if not self.started_at:
            self.started_at = time.time()
        self.total = len(self.events)

    @property
    def duration(self) -> float:
        if self.completed_at:
            return self.completed_at - self.started_at
        return time.time() - self.started_at

    @property
    def is_complete(self) -> bool:
        return self.status in ("completed", "failed", "cancelled")


class RecoveryEngine:
    def __init__(self):
        self._jobs: dict[str, RecoveryJob] = {}
        self._recovery_handlers: dict[str, list[Callable]] = {}
        self._max_retries = 3
        self._batch_size = 100

    def register_handler(
        self, event_name: str, handler: Callable
    ) -> None:
        if event_name not in self._recovery_handlers:
            self._recovery_handlers[event_name] = []
        self._recovery_handlers[event_name].append(handler)

    def create_job(
        self,
        source: str,
        target: str,
        events: list[Event],
        strategy: str = RecoveryStrategy.SEQUENTIAL,
        metadata: dict[str, Any] | None = None,
    ) -> RecoveryJob:
        job = RecoveryJob(
            source=source,
            target=target,
            strategy=strategy,
            events=events,
            metadata=metadata or {},
        )
        self._jobs[job.id] = job
        logger.info(
            "Recovery job %s created: %d events from %s to %s",
            job.id,
            len(events),
            source,
            target,
        )
        return job

    async def execute_job(self, job_id: str) -> RecoveryJob:
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Recovery job {job_id} not found")

        job.status = "running"
        job.started_at = time.time()

        try:
            if job.strategy == RecoveryStrategy.SEQUENTIAL:
                await self._execute_sequential(job)
            elif job.strategy == RecoveryStrategy.PARALLEL:
                await self._execute_parallel(job)
            elif job.strategy == RecoveryStrategy.BATCHED:
                await self._execute_batched(job)

            job.status = "completed" if job.failed == 0 else "completed_with_errors"
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
            logger.error("Recovery job %s failed: %s", job_id, exc)

        job.completed_at = time.time()
        logger.info(
            "Recovery job %s finished: %d/%d succeeded, %d failed in %.2fs",
            job_id,
            job.succeeded,
            job.total,
            job.failed,
            job.duration,
        )
        return job

    async def _execute_sequential(self, job: RecoveryJob) -> None:
        for event in job.events:
            success = await self._replay_event(event, job)
            if success:
                job.succeeded += 1
            else:
                job.failed += 1
            job.progress += 1

    async def _execute_parallel(self, job: RecoveryJob) -> None:
        import asyncio
        tasks = [self._replay_event(event, job) for event in job.events]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if result is True:
                job.succeeded += 1
            else:
                job.failed += 1
            job.progress += 1

    async def _execute_batched(self, job: RecoveryJob) -> None:
        import asyncio
        for i in range(0, len(job.events), self._batch_size):
            batch = job.events[i : i + self._batch_size]
            tasks = [self._replay_event(event, job) for event in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if result is True:
                    job.succeeded += 1
                else:
                    job.failed += 1
                job.progress += 1

    async def _replay_event(self, event: Event, job: RecoveryJob) -> bool:
        handlers = self._recovery_handlers.get(event.name, [])
        if not handlers:
            logger.warning(
                "No recovery handler for event %s in job %s",
                event.name,
                job.id,
            )
            return False

        for attempt in range(self._max_retries):
            try:
                for handler in handlers:
                    result = handler(event, job)
                    if hasattr(result, "__await__"):
                        await result
                return True
            except Exception as exc:
                logger.warning(
                    "Recovery attempt %d/%d failed for event %s: %s",
                    attempt + 1,
                    self._max_retries,
                    event.id,
                    exc,
                )
                if attempt < self._max_retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
        return False

    def get_job(self, job_id: str) -> RecoveryJob | None:
        return self._jobs.get(job_id)

    def list_jobs(self, status: str | None = None) -> list[RecoveryJob]:
        if status:
            return [j for j in self._jobs.values() if j.status == status]
        return list(self._jobs.values())

    def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job and job.status == "running":
            job.status = "cancelled"
            logger.info("Recovery job %s cancelled", job_id)
            return True
        return False

    def clear_completed(self) -> int:
        count = 0
        for jid in list(self._jobs.keys()):
            job = self._jobs[jid]
            if job.is_complete:
                del self._jobs[jid]
                count += 1
        return count
