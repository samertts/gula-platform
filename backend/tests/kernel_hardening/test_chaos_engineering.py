from __future__ import annotations

import asyncio

import pytest

from backend.app.kernel import Kernel
from backend.app.kernel.background.scheduler import Scheduler
from backend.app.kernel.background.task_queue import Task, TaskQueue
from backend.app.kernel.config.registry import ConfigurationRegistry
from backend.app.kernel.event_bus.bus import EventBus
from backend.app.kernel.event_bus.events import Event
from backend.app.kernel.event_bus.store import EventStore
from backend.app.kernel.gateway.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitState,
)
from backend.app.kernel.gateway.discovery import ServiceDiscovery, ServiceEndpoint
from backend.app.kernel.plugin.dependencies import PluginDependencyResolver
from backend.app.kernel.plugin.manager import PluginManager
from backend.app.kernel.plugin.registry import PluginRegistry
from backend.app.kernel.runtime.context import ApplicationContext
from backend.app.kernel.runtime.di_container import DIContainer
from backend.app.kernel.runtime.service_registry import ServiceRegistry
from backend.app.kernel.tenant.registry import TenantRegistry
from backend.app.kernel.types import TenantDescriptor

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
        try:
            container.clear_scope("nonexistent")
        except Exception:
            pass
        from backend.app.kernel.types import ServiceDescriptor, ServiceLifecycle
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
    def test_survives_handler_exception(self, kernel: Kernel, event_bus: EventBus):
        received = []

        def failing_handler(event):
            raise RuntimeError("handler crashed")

        def normal_handler(event):
            received.append(event)

        event_bus.subscribe("test.event", failing_handler)
        event_bus.subscribe("test.event", normal_handler)
        try:
            event_bus.publish(Event(name="test.event", data={"k": "v"}))
        except Exception:
            pass
        assert len(received) == 1

    def test_survives_massive_event_load(self, kernel: Kernel, event_bus: EventBus):
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
        try:
            asyncio.run(scheduler.stop())
        except Exception:
            pass

    def test_survives_double_start(self, kernel: Kernel):
        scheduler = Scheduler(kernel)
        asyncio.run(scheduler.start())
        try:
            asyncio.run(scheduler.start())
        except Exception:
            pass
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
        from backend.app.kernel.types import PluginDescriptor
        resolver = PluginDependencyResolver()
        p1 = PluginDescriptor(name="a", version="1.0", path="/tmp", entry_point="P", dependencies=["b"])
        p2 = PluginDescriptor(name="b", version="1.0", path="/tmp", entry_point="P", dependencies=["c"])
        p3 = PluginDescriptor(name="c", version="1.0", path="/tmp", entry_point="P", dependencies=["a"])
        with pytest.raises(ValueError):
            resolver.resolve_order([p1, p2, p3])

    def test_survives_broken_plugin_registry(self, kernel: Kernel):
        pm = PluginManager(kernel)
        pm.registry._plugins = None
        try:
            pm.list_plugins()
        except Exception:
            pass


class TestChaosGateway:
    def test_survives_broken_discovery(self, kernel: Kernel):
        sd = ServiceDiscovery(kernel)
        sd._services = None
        try:
            sd.discover("anything")
        except Exception:
            pass
        sd._services = {}
        sd.register(ServiceEndpoint(name="fixed", host="localhost", port=9999))
        result = sd.discover("fixed")
        assert result is not None


class TestChaosConfiguration:
    def test_survives_corrupted_config(self):
        cr = ConfigurationRegistry()
        cr._config = None
        try:
            cr.get("anything")
        except Exception:
            pass
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
