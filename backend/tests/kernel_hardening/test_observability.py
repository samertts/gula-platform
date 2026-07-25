from __future__ import annotations

import asyncio

import pytest
from app.kernel import Kernel, KernelConfig
from app.kernel.integration import get_kernel, get_kernel_health, init_kernel, is_kernel_ready


class TestObservabilityHealth:
    def test_kernel_health_returns_expected_keys(self):
        config = KernelConfig(environment="test")
        init_kernel(config=config)
        kernel = get_kernel()
        asyncio.run(kernel.boot())
        asyncio.run(kernel.start())
        health = asyncio.run(get_kernel_health())
        assert "services" in health or "uptime" in str(health)
        asyncio.run(kernel.stop())

    def test_is_ready_after_boot(self):
        import app.kernel.integration as kintegration
        from app.kernel.integration import _kernel_instance as ki
        kintegration._kernel_instance = None
        config = KernelConfig(environment="test")
        kernel = init_kernel(config=config)
        asyncio.run(kernel.boot())
        asyncio.run(kernel.start())
        assert is_kernel_ready()
        asyncio.run(kernel.stop())
        assert not is_kernel_ready()

    def test_kernel_state_reflects_lifecycle(self):
        kernel = Kernel()
        assert kernel.state.name == "CREATED"
        asyncio.run(kernel.boot())
        assert kernel.state.name == "BOOTING"
        asyncio.run(kernel.start())
        assert kernel.state.name == "RUNNING"
        assert kernel.is_running
        asyncio.run(kernel.stop())
        assert kernel.state.name == "STOPPED"
        assert not kernel.is_running


class TestObservabilityLiveness:
    def test_uptime_increases(self):
        import time
        kernel = Kernel()
        assert kernel.uptime == 0.0
        asyncio.run(kernel.boot())
        time.sleep(0.01)
        assert kernel.uptime > 0
        asyncio.run(kernel.start())
        time.sleep(0.01)
        assert kernel.uptime > 0.01


class TestObservabilityKernelConfig:
    def test_config_exposes_all_settings(self):
        config = KernelConfig(
            name="observability-test",
            environment="staging",
            debug=True,
            enable_plugins=False,
            enable_event_bus=False,
        )
        kernel = Kernel(config=config)
        assert kernel.config.name == "observability-test"
        assert kernel.config.environment == "staging"
        assert kernel.config.debug
        assert not kernel.config.enable_plugins
        assert not kernel.config.enable_event_bus


class TestObservabilityComponents:
    def test_all_components_registered_after_boot(self):
        kernel = Kernel()
        asyncio.run(kernel.boot())
        expected = [
            "application_context", "di_container", "service_registry",
            "capability_registry", "lifecycle_manager", "module_loader",
            "plugin_manager", "event_bus", "scheduler", "config_registry",
            "tenant_registry", "service_discovery",
        ]
        for comp in expected:
            assert kernel.get_component(comp) is not None, f"Missing component: {comp}"
        asyncio.run(kernel.stop())
