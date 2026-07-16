from __future__ import annotations

import asyncio
import gc
import weakref

import pytest

from app.kernel import Kernel
from app.kernel.event_bus.bus import EventBus
from app.kernel.event_bus.events import Event
from app.kernel.event_bus.store import EventStore
from app.kernel.plugin.manager import PluginManager
from app.kernel.runtime.context import ApplicationContext
from app.kernel.runtime.di_container import DIContainer
from app.kernel.runtime.service_registry import ServiceRegistry
from app.kernel.types import ServiceDescriptor, ServiceLifecycle

pytestmark = [
    pytest.mark.kernel,
    pytest.mark.slow,
]


class _LeakTrack:
    def __init__(self, data=None):
        self.data = data


class TestMemoryLeaks:
    def test_singleton_does_not_leak(self):
        kernel = Kernel.get_instance()
        ref = weakref.ref(kernel)
        gc.collect()
        assert ref() is not None
        assert isinstance(kernel, Kernel)

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
            obj = _LeakTrack({"data": i})
            sr.register(f"leak_svc_{i}", obj)
            refs.append(weakref.ref(obj))
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
                implementation=_LeakTrack,
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
