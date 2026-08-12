from __future__ import annotations

import pytest

from app.kernel.background.cron import CronEngine, CronJob


class TestCronEngine:
    def test_register_and_unregister(self):
        engine = CronEngine()
        called = []

        def handler():
            called.append(True)

        job = CronJob(name="hourly", schedule="0 * * * *", handler=handler)
        engine.register(job)
        assert len(engine.list_jobs()) == 1
        engine.unregister("hourly")
        assert len(engine.list_jobs()) == 0

    def test_list(self):
        engine = CronEngine()
        engine.register(CronJob(name="j1", schedule="* * * * *", handler=lambda: None))
        engine.register(CronJob(name="j2", schedule="*/5 * * * *", handler=lambda: None))
        assert len(engine.list_jobs()) == 2

    def test_cron_job_defaults(self):
        job = CronJob(name="test", schedule="* * * * *", handler=lambda: None)
        assert job.enabled
