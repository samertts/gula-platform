"""Plugin system for the GULA Communication Platform Core.

Providers are plugins. Plugins register, activate, deactivate and expose
health — without the Core ever knowing their implementation. Adding or
removing a provider is a configuration/deployment act, never a Core change
(Open/Closed Principle).
"""

from __future__ import annotations

import importlib.metadata
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .providers import ChannelProvider, ProviderHealth

logger = logging.getLogger("gula.communication.plugins")

# Entry point group used for automatic provider discovery.
ENTRY_POINT_GROUP = "gula.communication.providers"


@dataclass(frozen=True)
class PluginMetadata:
    id: str
    version: str = "0.1.0"
    description: str = ""
    entry_point: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "description": self.description,
            "entry_point": self.entry_point,
        }


@dataclass
class PluginState:
    """Runtime state of a registered plugin."""

    metadata: PluginMetadata
    provider: ChannelProvider
    instance: ProviderPlugin | None = None
    active: bool = False
    activation_error: str | None = None
    health: ProviderHealth = ProviderHealth.OK

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "provider_name": self.provider.name,
            "channel": self.provider.channel,
            "active": self.active,
            "activation_error": self.activation_error,
            "health": self.health.value,
        }


class ProviderPlugin(ABC):
    """Base class every provider plugin implements."""

    metadata: PluginMetadata

    @abstractmethod
    def create_provider(self) -> ChannelProvider:
        """Instantiate the provider with its own (env-only) configuration."""

    @abstractmethod
    def activate(self, context: dict[str, Any] | None = None) -> None:
        """Hook run when the plugin is activated."""

    @abstractmethod
    def deactivate(self) -> None:
        """Hook run when the plugin is deactivated."""


class PluginManager:
    """Registry + lifecycle manager for communication provider plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, PluginState] = {}
        self._lock = threading.Lock()

    def register(self, plugin: ProviderPlugin) -> PluginState:
        if not isinstance(plugin, ProviderPlugin):
            raise TypeError("plugin must implement ProviderPlugin")
        with self._lock:
            pid = plugin.metadata.id
            if pid in self._plugins:
                raise ValueError(f"plugin already registered: {pid}")
            provider = plugin.create_provider()
            state = PluginState(
                metadata=plugin.metadata,
                provider=provider,
                instance=plugin,
            )
            self._plugins[pid] = state
            logger.info(
                "communication_plugin_registered id=%s channel=%s",
                pid,
                provider.channel,
            )
            return state

    def activate(self, plugin_id: str, context: dict[str, Any] | None = None) -> bool:
        with self._lock:
            state = self._plugins.get(plugin_id)
            if state is None:
                raise KeyError(f"unknown plugin: {plugin_id}")
            if state.active:
                return True
            try:
                state.instance.activate(context)
                state.active = True
                state.activation_error = None
                state.health = ProviderHealth.OK
                logger.info("communication_plugin_activated id=%s", plugin_id)
                return True
            except Exception as exc:
                state.active = False
                state.activation_error = str(exc)
                state.health = ProviderHealth.DOWN
                logger.error(
                    "communication_plugin_activation_failed id=%s error_type=%s",
                    plugin_id,
                    type(exc).__name__,
                )
                return False

    def deactivate(self, plugin_id: str) -> bool:
        with self._lock:
            state = self._plugins.get(plugin_id)
            if state is None:
                return False
            if not state.active:
                return True
            try:
                state.instance.deactivate()
            except Exception:
                logger.exception("communication_plugin_deactivation_failed id=%s", plugin_id)
            state.active = False
            state.health = ProviderHealth.DOWN
            logger.info("communication_plugin_deactivated id=%s", plugin_id)
            return True

    def get_state(self, plugin_id: str) -> PluginState | None:
        with self._lock:
            return self._plugins.get(plugin_id)

    def states(self) -> list[PluginState]:
        with self._lock:
            return list(self._plugins.values())

    def providers(self) -> list[ChannelProvider]:
        with self._lock:
            return [s.provider for s in self._plugins.values() if s.active]

    def provider_count(self) -> int:
        with self._lock:
            return sum(1 for s in self._plugins.values() if s.active)

    def discover(self, entry_point_group: str = ENTRY_POINT_GROUP) -> list[PluginMetadata]:
        """Discover plugins installed under the entry point group.

        Uses only ``importlib.metadata`` (stdlib). Loaded entry points are
        validated but NOT activated — activation happens explicitly.
        """
        discovered: list[PluginMetadata] = []
        try:
            eps = importlib.metadata.entry_points()
            matches = eps.select(group=entry_point_group) if hasattr(eps, "select") else []
            for ep in matches:
                try:
                    obj = ep.load()
                    plugin = obj() if isinstance(obj, type) else obj
                    if not isinstance(plugin, ProviderPlugin):
                        logger.warning(
                            "communication_discovery_skipped ep=%s not a ProviderPlugin",
                            ep.name,
                        )
                        continue
                    discovered.append(
                        PluginMetadata(
                            id=plugin.metadata.id,
                            version=plugin.metadata.version,
                            description=plugin.metadata.description,
                            entry_point=str(ep.value),
                        ),
                    )
                except Exception:
                    logger.exception("communication_discovery_failed ep=%s", ep.name)
        except Exception:
            logger.exception("communication_discovery_error group=%s", entry_point_group)
        return discovered


__all__ = [
    "ENTRY_POINT_GROUP",
    "PluginManager",
    "PluginMetadata",
    "PluginState",
    "ProviderPlugin",
]
