"""Builtin provider plugin catalog + registration (PROGRAM-COMM-002).

Providers self-register: the catalog lists every plugin class shipped with
this package, and :func:`register_builtin_plugins` wires them into the
Communication Core's :class:`~shared.communication.plugins.PluginManager`
and :class:`~shared.communication.providers.ProviderRegistry` — the Core
itself is never modified. Entry-point discovery (``importlib.metadata``)
supplements the catalog for third-party plugins installed into the
environment.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from shared.communication.plugins import ENTRY_POINT_GROUP, PluginManager
from shared.communication.providers import ProviderRegistry

from .discord import DiscordPlugin
from .inapp import InAppPlugin
from .push import NoopPushPlugin
from .resend import ResendPlugin
from .slack import SlackPlugin
from .sms import NoopSmsPlugin
from .teams import TeamsPlugin
from .telegram import TelegramPlugin
from .webhook import WebhookPlugin

logger = logging.getLogger("gula.communication.providers.plugins")

#: Every provider shipped with the GULA Communication Provider Layer.
BUILTIN_PLUGIN_CLASSES: tuple[type, ...] = (
    ResendPlugin,
    TelegramPlugin,
    NoopPushPlugin,
    DiscordPlugin,
    SlackPlugin,
    TeamsPlugin,
    NoopSmsPlugin,
    WebhookPlugin,
    InAppPlugin,
)


def provider_enabled(plugin_id: str) -> bool:
    """Master + per-provider enable flags (env only)."""
    if not _env_flag("COMMUNICATION_PROVIDERS_ENABLED", True):
        return False
    return _env_flag(f"COMMUNICATION_PROVIDER_{plugin_id.upper()}_ENABLED", True)


def register_builtin_plugins(
    manager: PluginManager,
    context: dict[str, Any] | None = None,
) -> list[str]:
    """Register every enabled builtin plugin; returns active plugin ids.

    Plugins register (provider instance created), then activate. Providers
    whose secrets are missing simply report ``DOWN`` health — registration
    is unconditional so auto-discovery always lists them.
    """
    registered: list[str] = []
    for plugin_cls in BUILTIN_PLUGIN_CLASSES:
        plugin = plugin_cls()
        if not provider_enabled(plugin.metadata.id):
            logger.info("communication_provider_disabled id=%s", plugin.metadata.id)
            continue
        try:
            manager.register(plugin)
        except (TypeError, ValueError) as exc:
            logger.warning(
                "communication_provider_register_failed id=%s error=%s", plugin.metadata.id, exc
            )
            continue
        manager.activate(plugin.metadata.id, context)
        registered.append(plugin.metadata.id)
    return registered


def load_provider_plugins(
    manager: PluginManager | None = None,
    registry: ProviderRegistry | None = None,
    *,
    include_entry_points: bool = True,
    context: dict[str, Any] | None = None,
) -> PluginManager:
    """Composition helper: register + activate + publish providers.

    Entry points first (third-party plugins), then the builtin catalog.
    Published providers land in ``registry`` (a fresh one when omitted).
    """
    manager = manager or PluginManager()
    if include_entry_points:
        try:
            discovered = manager.discover(ENTRY_POINT_GROUP)
            for metadata in discovered:
                logger.info(
                    "communication_provider_discovered id=%s ep=%s",
                    metadata.id,
                    metadata.entry_point,
                )
        except Exception:
            logger.exception("communication_provider_discovery_failed")
    register_builtin_plugins(manager, context)
    target = registry or ProviderRegistry()
    for state in manager.states():
        if state.active:
            try:
                target.register(state.provider)
            except ValueError as exc:
                logger.warning(
                    "communication_provider_publish_failed id=%s error=%s",
                    state.metadata.id,
                    exc,
                )
    return manager


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name, "")
    if value == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


__all__ = [
    "BUILTIN_PLUGIN_CLASSES",
    "load_provider_plugins",
    "provider_enabled",
    "register_builtin_plugins",
]
