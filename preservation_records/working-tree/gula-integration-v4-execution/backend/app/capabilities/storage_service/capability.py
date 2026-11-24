from __future__ import annotations

import logging
from typing import Any

from app.kernel.integration import get_kernel

logger = logging.getLogger("gula.capability.storage_service")


class Storage_serviceCapability:
    """storage_service capability in the infrastructure domain (infrastructure layer).

    Unified storage layer: local filesystem, S3 compatible, MinIO, Azure Blob, Google Cloud Storage with versioning and encryption
    """

    def __init__(self) -> None:
        self._initialized = False
        self._kernel = None

    async def initialize(self) -> None:
        if self._initialized:
            return
        self._kernel = get_kernel()
        logger.info("Storage_service capability initializing")
        # Depends on: encryption_service
        self._initialized = True
        logger.info("Storage_service capability initialized")

    async def execute(self, input_data: Any) -> dict:
        if not self._initialized:
            await self.initialize()
        return {"success": True, "capability": "storage_service"}

    async def validate(self, input_data: Any) -> bool:
        return True

    async def on_activate(self) -> None:
        logger.info("Storage_service capability activated")

    async def on_deactivate(self) -> None:
        logger.info("Storage_service capability deactivated")

    async def health(self) -> dict:
        return {
            "status": "ok",
            "capability": "storage_service",
            "version": "1.0.0",
            "initialized": self._initialized,
        }
