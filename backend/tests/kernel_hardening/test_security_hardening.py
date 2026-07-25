from __future__ import annotations

import pytest
from app.kernel import Kernel
from app.kernel.plugin.permissions import PluginPermissionManager
from app.kernel.plugin.registry import PluginRegistry
from app.kernel.plugin.sandbox import PluginSandbox
from app.kernel.types import PluginDescriptor


class TestSecurityPluginIsolation:
    def test_sandbox_blocks_dangerous_modules(self):
        sandbox = PluginSandbox()
        assert not sandbox.is_module_allowed("os")
        assert not sandbox.is_module_allowed("subprocess")
        assert not sandbox.is_module_allowed("socket")
        assert not sandbox.is_module_allowed("ctypes")
        assert not sandbox.is_module_allowed("shutil")
        assert sandbox.is_module_allowed("json")
        assert sandbox.is_module_allowed("logging")
        assert sandbox.is_module_allowed("datetime")

    def test_unregistered_plugin_has_no_permissions(self):
        ppm = PluginPermissionManager()
        assert not ppm.has_permission("unregistered", "anything")


class TestSecurityUnauthorizedAccess:
    def test_service_registry_requires_known_service(self, kernel: Kernel):
        from app.kernel.exceptions import ServiceNotFoundError
        from app.kernel.runtime.service_registry import ServiceRegistry

        sr = ServiceRegistry()
        kernel.register_component("service_registry", sr)
        with pytest.raises(ServiceNotFoundError):
            sr.get_required("unauthorized_service")

    def test_tenant_cannot_access_other_tenant_data(self):
        from app.kernel.tenant.isolation import TenantIsolation

        ti = TenantIsolation()
        ti.isolate("tenant_a")
        assert ti.is_isolated("tenant_a")
        assert not ti.is_isolated("tenant_b")


class TestSecurityPrivilegeEscalation:
    def test_plugin_permissions_are_checked(self):
        ppm = PluginPermissionManager()
        desc = PluginDescriptor(
            name="malicious",
            version="1.0",
            path="/tmp",
            entry_point="Plugin",
            permissions=["config.read"],
        )
        ppm.check(desc)
        assert ppm.has_permission("malicious", "config.read")
        assert not ppm.has_permission("malicious", "db.write")
        assert not ppm.has_permission("malicious", "admin.access")


class TestSecurityConfigurationTampering:
    def test_config_validator_rejects_type_mismatch(self):
        from app.kernel.config.validation import ConfigurationValidator

        cv = ConfigurationValidator()
        cv.register_schema("port", {"type": "int"})
        cv.validate("port", 8080)
        with pytest.raises(TypeError):
            cv.validate("port", "malicious_string")

    def test_secrets_loader_requires_env_var(self):
        import os

        from app.kernel.config.secrets import SecretsLoader

        if "MALICIOUS_SECRET" in os.environ:
            del os.environ["MALICIOUS_SECRET"]
        sl = SecretsLoader()
        sl.load_from_env(prefix="MALICIOUS_")
        with pytest.raises(KeyError):
            sl.get_required("MALICIOUS_SECRET")


class TestSecurityRateLimiting:
    def test_rate_limiter_prevents_abuse(self):
        from app.kernel.gateway.rate_limiting import RateLimiter

        rl = RateLimiter()
        rl.set_limit("api_key", 3, 60)
        assert rl.check("api_key")
        assert rl.check("api_key")
        assert rl.check("api_key")
        assert not rl.check("api_key")

    def test_different_keys_have_independent_limits(self):
        from app.kernel.gateway.rate_limiting import RateLimiter

        rl = RateLimiter()
        rl.set_limit("key_a", 2, 60)
        rl.set_limit("key_b", 5, 60)
        assert rl.check("key_a")
        assert rl.check("key_a")
        assert not rl.check("key_a")
        assert rl.check("key_b")


class TestSecurityCircuitBreaker:
    def test_circuit_breaker_prevents_cascading_failures(self):
        from app.kernel.gateway.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker("downstream", failure_threshold=2, recovery_timeout=30)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_half_open_allows_probe(self):
        import time

        from app.kernel.gateway.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker("probe", failure_threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.02)
        assert cb.can_proceed()
        assert cb.state == CircuitState.HALF_OPEN
