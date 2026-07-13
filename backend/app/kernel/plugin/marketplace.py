from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("gula.kernel.plugin.marketplace")


@dataclass
class MarketplacePlugin:
    id: str
    name: str
    version: str
    description: str
    author: str
    downloads: int = 0
    rating: float = 0.0
    tags: list[str] = field(default_factory=list)
    verified: bool = False


class PluginMarketplaceInterface:
    def __init__(self):
        self._available: dict[str, MarketplacePlugin] = {}

    def register_available(self, plugin: MarketplacePlugin) -> None:
        self._available[plugin.id] = plugin

    def search(self, query: str) -> list[MarketplacePlugin]:
        return [
            p
            for p in self._available.values()
            if query.lower() in p.name.lower() or query.lower() in p.description.lower()
        ]

    def get_available(self, plugin_id: str) -> MarketplacePlugin | None:
        return self._available.get(plugin_id)

    def list_available(self) -> list[MarketplacePlugin]:
        return list(self._available.values())
