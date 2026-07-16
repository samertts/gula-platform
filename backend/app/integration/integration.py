from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

from app.integration.monitoring import IntegrationMonitor
from app.integration.offline import OfflineSyncEngine
from app.integration.routes import configure as configure_routes
from app.integration.routes import router as integration_router
from app.integration.testing import IntegrationTestSuite
from app.integration.transformation import DataTransformer, SchemaMapper

logger = logging.getLogger("gula.integration")


class IntegrationPlatform:
    def __init__(
        self,
        monitor: IntegrationMonitor | None = None,
        offline: OfflineSyncEngine | None = None,
        test_suite: IntegrationTestSuite | None = None,
        transformer: DataTransformer | None = None,
        mapper: SchemaMapper | None = None,
    ) -> None:
        self.monitor = monitor or IntegrationMonitor()
        self.offline = offline or OfflineSyncEngine()
        self.test_suite = test_suite or IntegrationTestSuite()
        self.transformer = transformer or DataTransformer()
        self.mapper = mapper or SchemaMapper()
        self._initialized = False

    def register_routes(self, app: FastAPI, prefix: str = "/integration") -> None:
        configure_routes(
            monitor=self.monitor,
            offline=self.offline,
            test_suite=self.test_suite,
            transformer=self.transformer,
            mapper=self.mapper,
        )
        app.include_router(integration_router, prefix=prefix)
        logger.info("Integration routes registered at %s", prefix)

    async def initialize(self, app: FastAPI, prefix: str = "") -> None:
        if self._initialized:
            logger.warning("Integration platform already initialized")
            return
        self.register_routes(app, prefix)
        from app.integration.connectors.routes import router as connectors_router
        app.include_router(connectors_router)
        logger.info("Integration platform initialized")
        self._initialized = True

    async def shutdown(self) -> None:
        if not self._initialized:
            return
        self._initialized = False
        logger.info("Integration platform shut down")

    def get_status(self) -> dict[str, Any]:
        return {
            "initialized": self._initialized,
            "monitor": self.monitor.get_health_dashboard() if self._initialized else {},
            "offline": self.offline.get_status() if self._initialized else {},
        }
