from __future__ import annotations


class KernelError(Exception):
    pass


class KernelNotBootedError(KernelError):
    pass


class KernelAlreadyBootedError(KernelError):
    pass


class ServiceNotFoundError(KernelError):
    def __init__(self, name: str):
        self.service_name = name
        super().__init__(f"Service not found: {name}")


class ServiceAlreadyRegisteredError(KernelError):
    def __init__(self, name: str):
        self.service_name = name
        super().__init__(f"Service already registered: {name}")


class CircularDependencyError(KernelError):
    def __init__(self, chain: list[str]):
        self.chain = chain
        super().__init__(f"Circular dependency detected: {' -> '.join(chain)}")


class PluginLoadError(KernelError):
    def __init__(self, name: str, reason: str):
        self.plugin_name = name
        super().__init__(f"Failed to load plugin '{name}': {reason}")


class PluginPermissionDenied(KernelError):
    def __init__(self, plugin: str, permission: str):
        super().__init__(f"Plugin '{plugin}' denied permission: {permission}")


class ModuleLoadError(KernelError):
    def __init__(self, name: str, reason: str):
        self.module_name = name
        super().__init__(f"Failed to load module '{name}': {reason}")


class ModuleVersionConflict(KernelError):
    def __init__(self, name: str, required: str, found: str):
        super().__init__(
            f"Module '{name}' requires version {required}, found {found}"
        )


class EventPublishError(KernelError):
    def __init__(self, event: str, reason: str):
        super().__init__(f"Failed to publish event '{event}': {reason}")


class ConfigurationError(KernelError):
    def __init__(self, key: str, reason: str):
        self.config_key = key
        super().__init__(f"Configuration error for '{key}': {reason}")


class TenantNotFoundError(KernelError):
    def __init__(self, tenant_id: str):
        super().__init__(f"Tenant not found: {tenant_id}")


class QuotaExceededError(KernelError):
    def __init__(self, tenant_id: str, resource: str, limit: int):
        super().__init__(
            f"Tenant '{tenant_id}' exceeded quota for '{resource}': {limit}"
        )


class CircuitBreakerOpenError(KernelError):
    def __init__(self, service: str):
        super().__init__(f"Circuit breaker open for service: {service}")


class RateLimitExceededError(KernelError):
    def __init__(self, key: str, limit: int, window: int):
        super().__init__(f"Rate limit exceeded for '{key}': {limit}/{window}s")
