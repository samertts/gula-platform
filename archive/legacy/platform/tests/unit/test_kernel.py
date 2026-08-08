import pytest


class TestKernel:
    def test_kernel_singleton(self, test_kernel):
        from platform.core.kernel import Kernel
        instance = Kernel.instance()
        assert instance is test_kernel

    def test_kernel_state_uninitialized(self, test_kernel):
        from platform.core.kernel import KernelState
        assert test_kernel.state == KernelState.UNINITIALIZED

    def test_kernel_boot(self, test_kernel):
        with pytest.raises(Exception):
            pass

    def test_kernel_properties(self, test_kernel):
        assert test_kernel.config.name == "test-kernel"
        assert test_kernel.config.version == "1.0.0"
        assert test_kernel.config.environment == "test"

    def test_kernel_has_event_bus(self, test_kernel):
        from platform.core.event_bus import EventBus
        assert isinstance(test_kernel.event_bus, EventBus)

    def test_kernel_container(self, test_kernel):
        container = test_kernel.container()
        from platform.core.kernel import DIContainer
        assert isinstance(container, DIContainer)

    def test_kernel_module_registry(self, test_kernel):
        modules = test_kernel.module_registry()
        assert isinstance(modules, dict)

    def test_kernel_services(self, test_kernel):
        services = test_kernel.services
        from platform.core.kernel import ServiceRegistry
        assert isinstance(services, ServiceRegistry)

    def test_kernel_not_running_initially(self, test_kernel):
        assert not test_kernel.is_running()

    def test_kernel_uptime_zero_initially(self, test_kernel):
        assert test_kernel.uptime == 0.0


class TestHealthManager:
    def test_health_register_component(self, test_kernel):
        health = test_kernel.health
        comp = health.register("test_db")
        assert comp.name == "test_db"

    def test_health_aggregate_unknown_when_empty(self, test_kernel):
        health = test_kernel.health
        from platform.core.kernel import HealthStatus
        assert health.get_aggregate_status() == HealthStatus.UNKNOWN

    def test_health_system_not_ready_initially(self, test_kernel):
        assert not test_kernel.health.is_system_ready()

    def test_health_diagnostics_structure(self, test_kernel):
        diag = test_kernel.health.get_diagnostics()
        assert "system_ready" in diag
        assert "aggregate_status" in diag
        assert "components" in diag


class TestDIContainer:
    def test_register_and_resolve(self, test_kernel):
        container = test_kernel.container()
        container.register_instance("my_service", {"key": "value"})
        result = container.resolve("my_service")
        assert result["key"] == "value"

    def test_resolve_missing_raises(self, test_kernel):
        container = test_kernel.container()
        with pytest.raises(KeyError):
            container.resolve("does_not_exist")

    def test_get_with_default(self, test_kernel):
        container = test_kernel.container()
        result = container.get("missing", "fallback")
        assert result == "fallback"

    def test_factory_singleton(self, test_kernel):
        container = test_kernel.container()
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return {"count": call_count}

        container.register_factory("counter", factory, singleton=True)
        r1 = container.resolve("counter")
        r2 = container.resolve("counter")
        assert r1["count"] == 1
        assert r2["count"] == 1

    def test_clear_container(self, test_kernel):
        container = test_kernel.container()
        container.register_instance("svc", 42)
        container.clear()
        assert container.get("svc") is None


class TestServiceRegistry:
    def test_register_and_resolve(self, test_kernel):
        registry = test_kernel.services
        registry.register("db", {"connected": True})
        result = registry.resolve("db")
        assert result["connected"] is True

    def test_has_service(self, test_kernel):
        registry = test_kernel.services
        registry.register("cache", {})
        assert registry.has("cache") is True
        assert registry.has("missing") is False

    def test_unregister(self, test_kernel):
        registry = test_kernel.services
        registry.register("tmp", 1)
        registry.unregister("tmp")
        assert registry.has("tmp") is False

    def test_list_services(self, test_kernel):
        registry = test_kernel.services
        names = registry.list()
        assert "kernel.config" in names
