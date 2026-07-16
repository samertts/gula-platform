"""GULA Platform Foundation — standardized reusable modules for all platforms."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("gula.platform")


class PlatformRegistry:
    """Central registry for all platform modules.

    Every platform module registers itself at import time so the
    platform can enumerate capabilities, health, and module metadata.
    """

    _modules: dict[str, Any] = {}
    _capabilities: dict[str, list[dict]] = {}

    @classmethod
    def register(cls, name: str, module, capabilities: list[dict] | None = None) -> None:
        cls._modules[name] = module
        if capabilities:
            cls._capabilities[name] = capabilities
        logger.debug("[PLATFORM] Registered module: %s", name)

    @classmethod
    def get(cls, name: str) -> Any:
        return cls._modules.get(name)

    @classmethod
    def list_modules(cls) -> list[str]:
        return list(cls._modules.keys())

    @classmethod
    def get_capabilities(cls) -> list[dict]:
        result = []
        for name, caps in cls._capabilities.items():
            for cap in caps:
                cap["module"] = name
                result.append(cap)
        return result

    @classmethod
    def health(cls) -> dict[str, str]:
        return dict.fromkeys(cls._modules, "registered")


import logging

logger = logging.getLogger("gula.platform")
