from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.control_plane.enums import ConfigurationScope
from app.kernel.config.registry import ConfigurationRegistry
from app.kernel.integration import get_kernel

logger = logging.getLogger("gula.control_plane.config.manager")


class CentralConfigManager:
    def __init__(self):
        self._kernel_registry: ConfigurationRegistry | None = None
        self._hierarchical: dict[str, dict[str, dict[str, Any]]] = {}
        self._profiles: dict[str, dict[str, Any]] = {}

    def _get_registry(self) -> ConfigurationRegistry:
        if self._kernel_registry is None:
            kernel = get_kernel()
            reg = kernel.get_component("config_registry")
            if reg is None:
                from app.kernel.config.registry import ConfigurationRegistry
                reg = ConfigurationRegistry()
                kernel.register_component("config_registry", reg)
            self._kernel_registry = reg
        return self._kernel_registry

    def set(
        self,
        key: str,
        value: Any,
        scope: ConfigurationScope = ConfigurationScope.GLOBAL,
        component: str = "",
        tenant: str = "",
    ) -> None:
        reg = self._get_registry()
        scope_key = self._scope_key(scope, component, tenant)
        if scope_key not in self._hierarchical:
            self._hierarchical[scope_key] = {}
        self._hierarchical[scope_key][key] = value
        reg.set(f"{scope_key}.{key}", value)
        logger.debug("Config set: %s = %s [scope=%s]", key, value, scope.value)

    def get(
        self,
        key: str,
        default: Any = None,
        scope: ConfigurationScope = ConfigurationScope.GLOBAL,
        component: str = "",
        tenant: str = "",
    ) -> Any:
        reg = self._get_registry()
        resolution_order = self._resolution_order(scope, component, tenant)
        for scope_key in resolution_order:
            scope_config = self._hierarchical.get(scope_key, {})
            if key in scope_config:
                return scope_config[key]
            stored = reg.get(f"{scope_key}.{key}")
            if stored is not None:
                return stored
        return default

    def get_scope(self, scope: ConfigurationScope, component: str = "", tenant: str = "") -> dict[str, Any]:
        scope_key = self._scope_key(scope, component, tenant)
        return dict(self._hierarchical.get(scope_key, {}))

    def _scope_key(self, scope: ConfigurationScope, component: str = "", tenant: str = "") -> str:
        parts = [scope.value]
        if scope == ConfigurationScope.TENANT and tenant:
            parts.append(tenant)
        elif (scope == ConfigurationScope.COMPONENT and component) or (scope == ConfigurationScope.ENVIRONMENT and component):
            parts.append(component)
        return ".".join(parts)

    def _resolution_order(self, scope: ConfigurationScope, component: str = "", tenant: str = "") -> list[str]:
        base = [self._scope_key(ConfigurationScope.ENVIRONMENT, component=component)]
        if scope in (ConfigurationScope.COMPONENT, ConfigurationScope.TENANT):
            base.insert(0, self._scope_key(ConfigurationScope.GLOBAL))
            base.insert(1, self._scope_key(scope, component=component, tenant=tenant))
        else:
            base.insert(0, self._scope_key(ConfigurationScope.GLOBAL))
            base.append(self._scope_key(scope, component=component, tenant=tenant))
        return base

    def reload_config(self) -> dict[str, Any]:
        reg = self._get_registry()
        if hasattr(reg, "reloader") and reg.reloader:
            reg.reloader.reload()
        logger.info("Configuration reloaded from all sources")
        return {"status": "reloaded", "timestamp": datetime.now(UTC).isoformat()}

    def register_profile(self, name: str, config: dict[str, Any]) -> None:
        self._profiles[name] = config
        for key, value in config.items():
            self.set(key, value, scope=ConfigurationScope.ENVIRONMENT, component=name)
        logger.info("Config profile registered: %s (%d keys)", name, len(config))

    def apply_profile(self, name: str) -> dict[str, Any]:
        profile = self._profiles.get(name)
        if not profile:
            raise KeyError(f"Profile not found: {name}")
        for key, value in profile.items():
            self.set(key, value, scope=ConfigurationScope.ENVIRONMENT, component=name)
        return {"profile": name, "applied": True}

    def list_profiles(self) -> list[str]:
        return list(self._profiles.keys())

    def all(self) -> dict[str, Any]:
        reg = self._get_registry()
        return reg.all()
