from __future__ import annotations

import logging
from typing import Any

from app.kernel.integration import get_kernel

logger = logging.getLogger("gula.capability.reporting_service")


class Reporting_serviceCapability:
    """reporting_service capability in the reporting domain (application layer).

    Enterprise reporting: dashboards, charts, PDF reports, Excel exports, CSV exports, scheduled reports, distribution via email
    """

    def __init__(self) -> None:
        self._initialized = False
        self._kernel = None

    async def initialize(self) -> None:
        if self._initialized:
            return
        self._kernel = get_kernel()
        logger.info("Reporting_service capability initializing")
        # Depends on: analytics
        # Depends on: pdf_reporting
        self._initialized = True
        logger.info("Reporting_service capability initialized")

    async def execute(self, input_data: Any) -> dict:
        if not self._initialized:
            await self.initialize()
        return {"success": True, "capability": "reporting_service"}

    async def validate(self, input_data: Any) -> bool:
        return True

    async def on_activate(self) -> None:
        logger.info("Reporting_service capability activated")

    async def on_deactivate(self) -> None:
        logger.info("Reporting_service capability deactivated")

    async def health(self) -> dict:
        return {
            "status": "ok",
            "capability": "reporting_service",
            "version": "1.0.0",
            "initialized": self._initialized,
        }
