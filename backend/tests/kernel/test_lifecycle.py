from __future__ import annotations

import asyncio

import pytest

from app.kernel.runtime.lifecycle import LifecycleComponent, LifecycleManager
from app.kernel.runtime.shutdown import ShutdownHandler, ShutdownManager
from app.kernel.runtime.startup import StartupManager, StartupTask


class TestLifecycleManager:
    def test_start_all(self):
        lm = LifecycleManager()
        comp = LifecycleComponent("test_comp")
        started = []

        async def on_start():
            started.append(True)

        comp.on_start(on_start)
        lm.register(comp)
        asyncio.run(lm.start_all())
        assert len(started) == 1

    def test_component_health(self):
        comp = LifecycleComponent("test")
        health = comp.health()
        assert "state" in health

    def test_manager_health(self):
        lm = LifecycleManager()
        comp = LifecycleComponent("test")
        lm.register(comp)
        health = lm.health()
        assert "test" in health


class TestStartupManager:
    def test_execute_all(self):
        sm = StartupManager()
        called = []

        async def task():
            called.append(True)

        sm.register(StartupTask(name="test", handler=task))
        results = asyncio.run(sm.execute_all())
        assert len(called) == 1
        assert results[0]["completed"]

    def test_task_defaults(self):
        def handler():
            pass

        task = StartupTask(name="test", handler=handler)
        assert task.required
        assert task.timeout == 30.0
        assert task.dependencies == []


class TestShutdownManager:
    def test_shutdown_all(self):
        sm = ShutdownManager()
        called = []

        async def handler():
            called.append(True)

        sm.register(ShutdownHandler(name="test", handler=handler))
        results = asyncio.run(sm.shutdown_all())
        assert len(called) == 1
        assert results[0]["success"]

    def test_handler_defaults(self):
        def handler():
            pass

        sh = ShutdownHandler(name="test", handler=handler)
        assert sh.priority == 100
        assert sh.timeout == 30.0
