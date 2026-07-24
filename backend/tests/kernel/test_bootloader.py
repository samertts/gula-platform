from __future__ import annotations

import asyncio

import pytest
from app.kernel import Kernel, KernelConfig
from app.kernel.runtime.bootloader import Bootloader


class TestBootloaderPhases:
    def test_all_phases_enabled(self):
        kernel = Kernel()
        asyncio.run(kernel.boot())
        assert kernel.get_component("application_context") is not None
        assert kernel.get_component("di_container") is not None
        assert kernel.get_component("service_registry") is not None
        assert kernel.get_component("capability_registry") is not None
        assert kernel.get_component("lifecycle_manager") is not None
        assert kernel.get_component("module_loader") is not None

    def test_disabled_plugins(self):
        config = KernelConfig(enable_plugins=False)
        kernel = Kernel(config=config)
        asyncio.run(kernel.boot())
        assert kernel.get_component("plugin_manager") is None

    def test_disabled_event_bus(self):
        config = KernelConfig(enable_event_bus=False)
        kernel = Kernel(config=config)
        asyncio.run(kernel.boot())
        assert kernel.get_component("event_bus") is None

    def test_disabled_background(self):
        config = KernelConfig(enable_background_processing=False)
        kernel = Kernel(config=config)
        asyncio.run(kernel.boot())
        assert kernel.get_component("scheduler") is None

    def test_disabled_tenant(self):
        config = KernelConfig(enable_multi_tenant=False)
        kernel = Kernel(config=config)
        asyncio.run(kernel.boot())
        assert kernel.get_component("tenant_registry") is None

    def test_disabled_gateway(self):
        config = KernelConfig(enable_internal_gateway=False)
        kernel = Kernel(config=config)
        asyncio.run(kernel.boot())
        assert kernel.get_component("service_discovery") is None

    def test_disabled_config(self):
        config = KernelConfig(enable_config_engine=False)
        kernel = Kernel(config=config)
        asyncio.run(kernel.boot())
        assert kernel.get_component("config_registry") is None

    def test_enabled_config_engine(self):
        config = KernelConfig(enable_config_engine=True)
        kernel = Kernel(config=config)
        asyncio.run(kernel.boot())
        assert kernel.get_component("config_registry") is not None

    def test_enabled_event_bus(self):
        config = KernelConfig(enable_event_bus=True)
        kernel = Kernel(config=config)
        asyncio.run(kernel.boot())
        assert kernel.get_component("event_bus") is not None

    def test_enabled_background(self):
        config = KernelConfig(enable_background_processing=True)
        kernel = Kernel(config=config)
        asyncio.run(kernel.boot())
        assert kernel.get_component("scheduler") is not None

    def test_enabled_tenant(self):
        config = KernelConfig(enable_multi_tenant=True)
        kernel = Kernel(config=config)
        asyncio.run(kernel.boot())
        assert kernel.get_component("tenant_registry") is not None

    def test_enabled_gateway(self):
        config = KernelConfig(enable_internal_gateway=True)
        kernel = Kernel(config=config)
        asyncio.run(kernel.boot())
        assert kernel.get_component("service_discovery") is not None

    def test_enabled_plugins(self):
        config = KernelConfig(enable_plugins=True)
        kernel = Kernel(config=config)
        asyncio.run(kernel.boot())
        assert kernel.get_component("plugin_manager") is not None
