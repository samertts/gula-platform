from __future__ import annotations

import asyncio

import pytest

from app.kernel import Kernel, KernelConfig, KernelState

pytestmark = [pytest.mark.kernel, pytest.mark.integration]


class TestKernelIntegration:
    def test_full_kernel_integration(self):
        config = KernelConfig(
            name="integration-test",
            environment="test",
            enable_plugins=True,
            enable_event_bus=True,
            enable_background_processing=True,
            enable_feature_management=True,
            enable_config_engine=True,
            enable_multi_tenant=True,
            enable_internal_gateway=True,
        )
        kernel = Kernel(config=config)
        asyncio.run(kernel.boot())
        asyncio.run(kernel.start())
        assert kernel.is_running
        assert kernel.uptime > 0
        assert kernel.get_component("application_context") is not None
        assert kernel.get_component("di_container") is not None
        assert kernel.get_component("service_registry") is not None
        assert kernel.get_component("capability_registry") is not None
        assert kernel.get_component("lifecycle_manager") is not None
        assert kernel.get_component("module_loader") is not None
        assert kernel.get_component("plugin_manager") is not None
        assert kernel.get_component("event_bus") is not None
        assert kernel.get_component("scheduler") is not None
        assert kernel.get_component("config_registry") is not None
        assert kernel.get_component("tenant_registry") is not None
        assert kernel.get_component("service_discovery") is not None
        asyncio.run(kernel.stop())
        assert not kernel.is_running

    def test_integration_init(self):
        from app.kernel.integration import get_kernel, init_kernel, is_kernel_ready

        k = init_kernel()
        assert k is not None
        assert k is get_kernel()
        assert not is_kernel_ready()
        Kernel.reset_instance()

    def test_integration_get_before_init(self):
        import backend.app.kernel.integration as ki
        from app.kernel.integration import get_kernel
        original = ki._kernel_instance
        ki._kernel_instance = None
        try:
            get_kernel()
            pytest.fail("Expected RuntimeError")
        except RuntimeError:
            pass
        ki._kernel_instance = original

    def test_health_returns_relevant_fields(self):
        from app.kernel.integration import get_kernel_health, init_kernel

        k = init_kernel()
        asyncio.run(k.boot())
        asyncio.run(k.start())
        health = asyncio.run(get_kernel_health())
        assert "services" in health
        assert "capabilities" in health
        asyncio.run(k.stop())
        Kernel.reset_instance()

    def test_stop_without_start(self):
        from app.kernel.integration import stop_kernel

        res = asyncio.run(stop_kernel())
        assert res is None

    def test_warmup(self):
        from app.kernel.integration import init_kernel, warmup_kernel

        k = init_kernel()
        asyncio.run(k.boot())
        asyncio.run(k.start())
        res = asyncio.run(warmup_kernel())
        assert res is None
        asyncio.run(k.stop())
        Kernel.reset_instance()

    def test_get_kernel_config(self):
        from app.kernel.integration import get_kernel_config

        config = get_kernel_config()
        assert config.name == "gula-kernel"
        assert config.version == "2.1.0"
        assert config.environment == "production"

    def test_kill_switch_not_active(self):
        from app.kernel.integration import kernel_kill_switch_active

        result = kernel_kill_switch_active()
        assert not result

    def test_degraded_mode_not_active(self):
        from app.kernel.integration import kernel_degraded_mode

        result = kernel_degraded_mode()
        assert not result

    def test_all_components_after_boot(self):
        from app.kernel.integration import get_kernel, init_kernel

        k = init_kernel()
        asyncio.run(k.boot())
        assert k.get_component("application_context") is not None
        assert k.get_component("di_container") is not None
        assert k.get_component("service_registry") is not None
        assert k.get_component("capability_registry") is not None
        assert k.get_component("lifecycle_manager") is not None
        assert k.get_component("module_loader") is not None
        asyncio.run(k.stop())
        Kernel.reset_instance()
