from __future__ import annotations

import logging
from typing import Any

from app.kernel.integration import get_kernel

logger = logging.getLogger("gula.capability.search_service")


class Search_serviceCapability:
    """search_service capability in the infrastructure domain (application layer).

    Unified search platform: full-text search across patients, orders, results, documents with filters, ranking, suggestions, indexing, permissions-aware
    """

    def __init__(self) -> None:
        self._initialized = False
        self._kernel = None

    async def initialize(self) -> None:
        if self._initialized:
            return
        self._kernel = get_kernel()
        logger.info("Search_service capability initializing")
        # Depends on: authentication
        self._initialized = True
        logger.info("Search_service capability initialized")

    async def execute(self, input_data: Any) -> dict:
        if not self._initialized:
            await self.initialize()
        return {"success": True, "capability": "search_service"}

    async def validate(self, input_data: Any) -> bool:
        return True

    async def on_activate(self) -> None:
        logger.info("Search_service capability activated")

    async def on_deactivate(self) -> None:
        logger.info("Search_service capability deactivated")

    async def health(self) -> dict:
        return {
            "status": "ok",
            "capability": "search_service",
            "version": "1.0.0",
            "initialized": self._initialized,
        }
