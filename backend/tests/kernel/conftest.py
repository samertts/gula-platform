from __future__ import annotations

import asyncio

import pytest
from app.kernel import Kernel, KernelConfig
from app.kernel.event_bus.bus import EventBus
from app.kernel.event_bus.events import Event
from app.kernel.types import (
    CapabilityDescriptor,
    ModuleDescriptor,
    PluginDescriptor,
    ServiceDescriptor,
    ServiceLifecycle,
    TenantDescriptor,
)

pytestmark = [
    pytest.mark.kernel,
    pytest.mark.unit,
]


@pytest.fixture(autouse=True)
def reset_kernel():
    Kernel.reset_instance()
    yield
    Kernel.reset_instance()


@pytest.fixture()
def kernel() -> Kernel:
    config = KernelConfig(environment="test", debug=True)
    return Kernel(config=config)


@pytest.fixture()
def booted_kernel(kernel: Kernel) -> Kernel:
    asyncio.run(kernel.boot())
    return kernel


@pytest.fixture()
def running_kernel(booted_kernel: Kernel) -> Kernel:
    asyncio.run(booted_kernel.start())
    return booted_kernel


@pytest.fixture()
def event_bus(kernel: Kernel) -> EventBus:
    return EventBus(kernel)


@pytest.fixture()
def sample_event() -> Event:
    return Event(name="test.event", data={"key": "value"})


@pytest.fixture()
def service_descriptor() -> ServiceDescriptor:
    return ServiceDescriptor(
        name="test_service",
        interface=None,
        implementation=dict,
        lifecycle=ServiceLifecycle.SINGLETON,
    )


@pytest.fixture()
def capability_descriptor() -> CapabilityDescriptor:
    return CapabilityDescriptor(name="test_cap", version="1.0", description="Test capability")


@pytest.fixture()
def plugin_descriptor() -> PluginDescriptor:
    return PluginDescriptor(
        name="test_plugin",
        version="1.0",
        path="/tmp",
        entry_point="Plugin",
        permissions=["config.read"],
    )


@pytest.fixture()
def module_descriptor() -> ModuleDescriptor:
    return ModuleDescriptor(name="test_module", version="1.0", path="/tmp")


@pytest.fixture()
def tenant_descriptor() -> TenantDescriptor:
    return TenantDescriptor(
        id="tenant_1",
        name="Test Lab",
        slug="test-lab",
        plan="professional",
        features={"premium": True},
        quotas={"patients": 1000},
    )
