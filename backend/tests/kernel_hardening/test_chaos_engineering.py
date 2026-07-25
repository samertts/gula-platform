from __future__ import annotations

import asyncio
import contextlib

import pytest
from app.kernel import Kernel
from app.kernel.background.scheduler import Scheduler
from app.kernel.background.task_queue import Task, TaskQueue
from app.kernel.config.registry import ConfigurationRegistry
from app.kernel.event_bus.bus import EventBus
from app.kernel.event_bus.events import Event
from app.kernel.event_bus.store import EventStore
from app.kernel.gateway.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitState,
)
from app.kernel.gateway.discovery import ServiceDiscovery, ServiceEndpoint
from app.kernel.plugin.dependencies import PluginDependencyResolver
from app.kernel.plugin.manager import PluginManager
from app.kernel.plugin.registry import PluginRegistry
from app.kernel.runtime.context import ApplicationContext
from app.kernel.runtime.di_container import DIContainer
from app.kernel.runtime.service_registry import ServiceRegistry
from app.kernel.tenant.registry import TenantRegistry
from app.kernel.types import TenantDescriptor

pytestmark = [
    pytest.mark.kernel,
    pytest.mark.integration,
    pytest.mark.stress,
]


class TestChaosServiceRegistry:
    def test_survives_corrupted_registry(self, kernel: Kernel):
        sr = ServiceRegistry()
        kernel.register_component("service_registry", sr)
        sr.register("critical", {"data": "important"})
        sr._services["critical"] = None
        assert sr.get("critical") is None
        sr.register("critical", {"data": "restored"})
        assert sr.get("critical")["data"] == "restored"

    def test_survives_concurrent_unregister(self, kernel: Kernel):
        sr = ServiceRegistry()
        kernel.register_component("service_registry", sr)
        for i in range(100):
            sr.register(f"svc_{i}", {"id": i})
        for i in range(100):
            sr.unregister(f"svc_{i}")
        assert not sr.has("svc_0")


class TestChaosDIContainer:
    def test_survives_corrupted_scope(self, kernel: Kernel):
        container = DIContainer()
        kernel.register_component("di_container", container)
        container._scopes = None
        with contextlib.suppress(Exception):
            container.clear_scope("nonexistent")
        from app.kernel.types import ServiceDescriptor, ServiceLifecycle

        desc = ServiceDescriptor(
            name="resilient",
            interface=None,
            implementation=dict,
            lifecycle=ServiceLifecycle.SINGLETON,
        )
        container.register(desc)
        result = container.resolve("resilient")
        assert result is not None


class TestChaosEventBus:
    def test_survives_handler_exception(self, kernel: Kernel):
        event_bus = EventBus(kernel)
        received = []

        def failing_handler(event):
            raise RuntimeError("handler crashed")

        def normal_handler(event):
            received.append(event)

        event_bus.subscribe("test.event", failing_handler)
        event_bus.subscribe("test.event", normal_handler)
        with contextlib.suppress(Exception):
            event_bus.publish(Event(name="test.event", data={"k": "v"}))
        assert len(received) == 1

    def test_survives_massive_event_load(self, kernel: Kernel):
        event_bus = EventBus(kernel)
        count = 0

        def handler(event):
            nonlocal count
            count += 1

        event_bus.subscribe("load.test", handler)
        for i in range(1000):
            event_bus.publish(Event(name="load.test", data={"i": i}))
        assert count == 1000

    def test_event_store_survives_duplicate_ids(self):
        store = EventStore()
        event = Event(name="dup", data={"k": "v"})
        store.save(event)
        store.save(event)
        assert store.count() == 1


class TestChaosScheduler:
    def test_survives_stop_without_start(self, kernel: Kernel):
        scheduler = Scheduler(kernel)
        with contextlib.suppress(Exception):
            asyncio.run(scheduler.stop())

    def test_survives_double_start(self, kernel: Kernel):
        scheduler = Scheduler(kernel)
        asyncio.run(scheduler.start())
        with contextlib.suppress(Exception):
            asyncio.run(scheduler.start())
        asyncio.run(scheduler.stop())


class TestChaosTaskQueue:
    def test_survives_corrupted_task(self):
        tq = TaskQueue()
        tq.enqueue(Task(id="t1", name="corrupted", handler="not_callable"))
        assert tq.size() == 1


class TestChaosCircuitBreaker:
    def test_recovers_after_open(self):
        cb = CircuitBreaker("test_svc", failure_threshold=2, recovery_timeout=0.01)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        import time

        time.sleep(0.02)
        assert cb.can_proceed()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_manager_survives_missing_service(self):
        cbm = CircuitBreakerManager()
        assert cbm.can_proceed("nonexistent")
        cbm.record_failure("nonexistent")
        cbm.record_failure("nonexistent")
        assert cbm.can_proceed("nonexistent")


class TestChaosPlugin:
    def test_survives_circular_dependencies(self):
        from app.kernel.types import PluginDescriptor

        resolver = PluginDependencyResolver()
        p1 = PluginDescriptor(
            name="a", version="1.0", path="/tmp", entry_point="P", dependencies=["b"]
        )
        p2 = PluginDescriptor(
            name="b", version="1.0", path="/tmp", entry_point="P", dependencies=["c"]
        )
        p3 = PluginDescriptor(
            name="c", version="1.0", path="/tmp", entry_point="P", dependencies=["a"]
        )
        with pytest.raises(ValueError):
            resolver.resolve_order([p1, p2, p3])

    def test_survives_broken_plugin_registry(self, kernel: Kernel):
        pm = PluginManager(kernel)
        pm.registry._plugins = None
        with contextlib.suppress(Exception):
            pm.list_plugins()


class TestChaosGateway:
    def test_survives_broken_discovery(self, kernel: Kernel):
        sd = ServiceDiscovery(kernel)
        sd._services = None
        with contextlib.suppress(Exception):
            sd.discover("anything")
        sd._services = {}
        sd.register(ServiceEndpoint(name="fixed", host="localhost", port=9999))
        result = sd.discover("fixed")
        assert result is not None


class TestChaosConfiguration:
    def test_survives_corrupted_config(self):
        cr = ConfigurationRegistry()
        cr._config = None
        with contextlib.suppress(Exception):
            cr.get("anything")
        cr._config = {}
        cr.set("key", "value")
        assert cr.get("key") == "value"


class TestChaosTenant:
    def test_survives_duplicate_registration(self):
        tr = TenantRegistry()
        desc = TenantDescriptor(id="t1", name="T1", slug="t1")
        tr.register(desc)
        tr.register(desc)
        assert len(tr.list_tenants()) == 1
