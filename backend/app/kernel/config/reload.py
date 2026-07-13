from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

if TYPE_CHECKING:
    from backend.app.kernel.config.registry import ConfigurationRegistry

logger = logging.getLogger("gula.kernel.config.reload")


class RuntimeReloader:
    def __init__(self, registry: ConfigurationRegistry):
        self.registry = registry
        self._hooks: list[Callable] = []

    def on_reload(self, hook: Callable) -> None:
        self._hooks.append(hook)

    async def reload(self) -> None:
        for hook in self._hooks:
            try:
                result = hook()
                if hasattr(result, "__await__"):
                    await result
            except Exception as e:
                logger.error("Config reload hook failed", extra={"error": str(e)})
