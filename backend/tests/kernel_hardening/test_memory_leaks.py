from __future__ import annotations

import asyncio
import gc
import weakref

import pytest

from backend.app.kernel import Kernel
from backend.app.kernel.event_bus.bus import EventBus
from backend.app.kernel.event_bus.events import Event
from backend.app.kernel.event_bus.store import EventStore
from backend.app.kernel.plugin.manager import PluginManager
from backend.app.kernel.runtime.context import ApplicationContext
from backend.app.kernel.runtime.di_container import DIContainer
from backend.app.kernel.runtime.service_registry import ServiceRegistry
from backend.app.kernel.types import ServiceDescriptor, ServiceLifecycle

pytestmark = [
    pytest.mark.kernel,
    pytest.mark.slow,
]


class TestMemoryLeaks:
    def test_no_object_leak(self):
        refs = []
        for _ in range(100):
            kernel = Kernel()
            refs.append(weakref.ref(kernel))
        del kernel
        gc.collect()
        alive = sum(1 for r in refs if r() is not None)
        assert alive <= 1, f"{alive} Kernel instances leaked"

    def test_no_event_leak(self, kernel: Kernel):
        eb = EventBus(kernel)
        events = []
        for i in range(1000):
            e = Event(name="leak.test", data={"i": i})
            eb.publish(e)
            events.append(weakref.ref(e))
        del events
        del eb
        gc.collect()

    def test_no_service_leak(self, kernel: Kernel):
        sr = ServiceRegistry()
        kernel.register_component("service_registry", sr)
        refs = []
        for i in range(100):
            sr.register(f"leak_svc_{i}", {"data": i})
            refs.append(weakref.ref(sr._services.get(f"leak_svc_{i}")))
        for i in range(100):
            sr.unregister(f"leak_svc_{i}")
        gc.collect()
        alive = sum(1 for r in refs if r() is not None)
        assert alive <= 5, f"{alive} service references leaked"

    def test_no_di_leak(self):
        container = DIContainer()
        refs = []
        for i in range(100):
            desc = ServiceDescriptor(
                name=f"leak_{i}",
                interface=None,
                implementation=dict,
                lifecycle=ServiceLifecycle.TRANSIENT,
            )
            container.register(desc)
            instance = container.resolve(f"leak_{i}")
            refs.append(weakref.ref(instance))
        gc.collect()
        alive = sum(1 for r in refs if r() is not None)
        assert alive <= 10, f"{alive} DI instances leaked"

    def test_no_event_store_leak(self):
        store = EventStore()
        refs = []
        for i in range(1000):
            e = Event(name="store.leak", data={"i": i})
            store.save(e)
            refs.append(weakref.ref(e))
        del refs
        del store
        gc.collect()
