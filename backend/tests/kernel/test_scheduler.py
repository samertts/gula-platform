from __future__ import annotations

import asyncio

import pytest

from backend.app.kernel import Kernel
from backend.app.kernel.background.scheduler import Scheduler


class TestScheduler:
    def test_start_and_stop(self, kernel: Kernel):
        scheduler = Scheduler(kernel)
        asyncio.run(scheduler.start())
        asyncio.run(scheduler.stop())

    def test_cron_job_defaults(self):
        from backend.app.kernel.background.cron import CronJob
        job = CronJob(name="test", schedule="* * * * *", handler=lambda: None)
        assert job.enabled

    def test_retry_policy_defaults(self):
        from backend.app.kernel.background.job_retry import RetryPolicy
        rp = RetryPolicy()
        assert rp.max_retries == 3
        assert rp.backoff_base == 1.0
        assert rp.backoff_multiplier == 2.0

    def test_task_defaults(self):
        from backend.app.kernel.background.task_queue import Task
        task = Task(id="t1", name="test", handler=lambda: None)
        assert task.id == "t1"
        assert task.created_at > 0
        assert task.status == "pending"
        assert task.priority == 0
