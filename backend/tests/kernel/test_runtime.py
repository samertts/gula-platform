from __future__ import annotations

import asyncio

import pytest
from app.kernel import Kernel, KernelConfig, KernelState
from app.kernel.exceptions import ServiceNotFoundError
from app.kernel.runtime.di_container import DIContainer
from app.kernel.types import ServiceDescriptor, ServiceLifecycle


class TestKernelSingleton:
    def test_singleton(self):
        k1 = Kernel()
        k2 = Kernel.get_instance()
        assert k1 is k2

    def test_double_instance(self):
        Kernel()
        with pytest.raises(RuntimeError, match="singleton"):
            Kernel()

    def test_boot_and_start(self):
        kernel = Kernel()
        asyncio.run(kernel.boot())
        assert kernel.state == KernelState.BOOTING
        asyncio.run(kernel.start())
        assert kernel.state == KernelState.RUNNING
        asyncio.run(kernel.stop())
        assert kernel.state == KernelState.STOPPED

    def test_full_lifecycle(self):
        kernel = Kernel()
        asyncio.run(kernel.boot())
        asyncio.run(kernel.start())
        assert kernel.is_running
        assert kernel.uptime > 0
        asyncio.run(kernel.stop())
        assert not kernel.is_running

    def test_config(self):
        config = KernelConfig(name="test-kernel", environment="test")
        kernel = Kernel(config=config)
        assert kernel.config.name == "test-kernel"
        assert kernel.config.environment == "test"

    def test_service_registration(self):
        kernel = Kernel()
        kernel.register_service("my_service", {"data": 42})
        assert kernel.get_service("my_service") == {"data": 42}
        assert kernel.get_service("nonexistent") is None

    def test_component_registration(self):
        kernel = Kernel()
        kernel.register_component("my_component", {"data": 42})
        assert kernel.get_component("my_component") == {"data": 42}
        assert kernel.get_component("nonexistent") is None

    def test_config_defaults(self):
        config = KernelConfig()
        assert config.name == "gula-kernel"
        assert config.version == "2.1.0"
        assert config.environment == "production"
        assert not config.debug
        assert config.boot_timeout == 30.0
        assert config.shutdown_timeout == 30.0
        assert config.enable_plugins
        assert config.enable_event_bus
        assert config.enable_background_processing
        assert config.enable_feature_management
        assert config.enable_config_engine
        assert config.enable_multi_tenant
        assert config.enable_internal_gateway


class TestDIContainer:
    def test_scoped_resolution(self):
        container = DIContainer()
        desc = ServiceDescriptor(
            name="scoped_service",
            interface=None,
            implementation=dict,
            lifecycle=ServiceLifecycle.SCOPED,
        )
        container.register(desc)
        s1 = container.resolve("scoped_service", scope_id="scope_1")
        s2 = container.resolve("scoped_service", scope_id="scope_1")
        s3 = container.resolve("scoped_service", scope_id="scope_2")
        assert s1 is s2
        assert s1 is not s3
        container.clear_scope("scope_1")
        s4 = container.resolve("scoped_service", scope_id="scope_1")

    def test_transient(self):
        container = DIContainer()
        desc = ServiceDescriptor(
            name="transient",
            interface=None,
            implementation=dict,
            lifecycle=ServiceLifecycle.TRANSIENT,
        )
        container.register(desc)
        t1 = container.resolve("transient")
        t2 = container.resolve("transient")
        assert t1 is not t2

    def test_not_found(self):
        container = DIContainer()
        with pytest.raises(ServiceNotFoundError):
            container.resolve("nonexistent")


class TestDescriptorDefaults:
    def test_service_descriptor(self):
        desc = ServiceDescriptor(name="test", interface=None, implementation=dict)
        assert desc.lifecycle == ServiceLifecycle.SINGLETON
        assert desc.version == "1.0.0"
        assert not desc.lazy

    def test_capability_descriptor(self):
        from app.kernel.types import CapabilityDescriptor

        desc = CapabilityDescriptor(name="test", version="1.0", description="test")
        assert not desc.required
        assert desc.enabled
