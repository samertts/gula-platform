from __future__ import annotations

import pytest
from app.kernel.event_bus.events import Event
from app.kernel.event_bus.recovery import RecoveryEngine, RecoveryStrategy


class TestRecoveryEngine:
    def test_create_job(self):
        engine = RecoveryEngine()
        events = [Event(name="test.event", data={"k": "v"})]
        job = engine.create_job("source", "target", events)
        assert job.source == "source"
        assert job.target == "target"
        assert len(job.events) == 1

    def test_register_handler(self):
        engine = RecoveryEngine()
        results = []

        def handler(event, job):
            results.append(event.name)

        engine.register_handler("test.event", handler)
        events = [Event(name="test.event", data={})]
        job = engine.create_job("src", "tgt", events)
        assert len(engine._recovery_handlers["test.event"]) == 1

    def test_multiple_jobs(self):
        engine = RecoveryEngine()
        job1 = engine.create_job("a", "b", [Event(name="e1", data={})])
        job2 = engine.create_job("a", "b", [Event(name="e2", data={})])
        assert len(engine.list_jobs()) == 2
        assert len(engine.list_jobs("pending")) == 2

    def test_cancel_job(self):
        engine = RecoveryEngine()
        job = engine.create_job("a", "b", [Event(name="e", data={})])
        job.status = "running"
        assert engine.cancel_job(job.id) is True
        assert engine.get_job(job.id).status == "cancelled"

    def test_clear_completed(self):
        engine = RecoveryEngine()
        job = engine.create_job("a", "b", [Event(name="e", data={})])
        job.status = "completed"
        assert engine.clear_completed() == 1
        assert len(engine.list_jobs()) == 0

    def test_job_properties(self):
        from app.kernel.event_bus.recovery import RecoveryJob
        job = RecoveryJob()
        assert job.is_complete is False
        assert job.status == "pending"
        job.status = "completed"
        assert job.is_complete is True
