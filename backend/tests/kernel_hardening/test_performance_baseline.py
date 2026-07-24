from __future__ import annotations

import asyncio
import time

import pytest
from app.kernel import Kernel, KernelConfig
from app.kernel.background.scheduler import Scheduler
from app.kernel.config.registry import ConfigurationRegistry
from app.kernel.event_bus.bus import EventBus
from app.kernel.event_bus.events import Event
from app.kernel.runtime.context import ApplicationContext
from app.kernel.runtime.di_container import DIContainer
from app.kernel.runtime.service_registry import ServiceRegistry
from app.kernel.types import ServiceDescriptor, ServiceLifecycle

pytestmark = [
    pytest.mark.kernel,
    pytest.mark.performance,
    pytest.mark.slow,
]


class TestPerformanceBaseline:
    def test_cold_start(self):
        start = time.monotonic()
        Kernel.reset_instance()
        kernel = Kernel()
        asyncio.run(kernel.boot())
        cold_time = (time.monotonic() - start) * 1000
        assert cold_time < 5000, f"Cold start took {cold_time:.1f}ms (limit 5000ms)"

    def test_warm_start(self):
        Kernel.reset_instance()
        k1 = Kernel()
        asyncio.run(k1.boot())
        Kernel.reset_instance()
        start = time.monotonic()
        k2 = Kernel()
        asyncio.run(k2.boot())
        warm_time = (time.monotonic() - start) * 1000
        assert warm_time < 3000, f"Warm start took {warm_time:.1f}ms (limit 3000ms)"

    def test_shutdown(self):
        kernel = Kernel()
        asyncio.run(kernel.boot())
        asyncio.run(kernel.start())
        start = time.monotonic()
        asyncio.run(kernel.stop())
        shutdown_time = (time.monotonic() - start) * 1000
        assert shutdown_time < 2000, f"Shutdown took {shutdown_time:.1f}ms (limit 2000ms)"

    def test_service_lookup(self):
        sr = ServiceRegistry()
        sr.register("svc", {"data": 42})
        start = time.monotonic()
        for _ in range(10_000):
            sr.get("svc")
        elapsed = (time.monotonic() - start) * 1000
        assert elapsed < 200, f"10k lookups took {elapsed:.1f}ms (limit 200ms)"

    def test_di_lookup(self):
        container = DIContainer()
        desc = ServiceDescriptor(
            name="svc", interface=None, implementation=dict,
            lifecycle=ServiceLifecycle.SINGLETON,
        )
        container.register(desc)
        container.resolve("svc")
        start = time.monotonic()
        for _ in range(10_000):
            container.resolve("svc")
        elapsed = (time.monotonic() - start) * 1000
        assert elapsed < 300, f"10k DI lookups took {elapsed:.1f}ms (limit 300ms)"

    def test_event_dispatch(self, kernel: Kernel):
        eb = EventBus(kernel)

        def handler(event):
            pass

        eb.subscribe("perf.test", handler)
        start = time.monotonic()
        for _ in range(10_000):
            eb.publish(Event(name="perf.test", data={}))
        elapsed = (time.monotonic() - start) * 1000
        assert elapsed < 1000, f"10k dispatches took {elapsed:.1f}ms (limit 1000ms)"

    def test_config_lookup(self):
        cr = ConfigurationRegistry()
        cr.set("key", "value")
        start = time.monotonic()
        for _ in range(100_000):
            cr.get("key")
        elapsed = (time.monotonic() - start) * 1000
        assert elapsed < 500, f"100k config lookups took {elapsed:.1f}ms (limit 500ms)"

    def test_scheduler_latency(self, kernel: Kernel):
        scheduler = Scheduler(kernel)
        asyncio.run(scheduler.start())
        start = time.monotonic()
        asyncio.run(scheduler.stop())
        elapsed = (time.monotonic() - start) * 1000
        assert elapsed < 1000, f"Scheduler start/stop took {elapsed:.1f}ms (limit 1000ms)"
