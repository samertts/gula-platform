import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from platform.api.routes.health import router as health_router
from platform.api.routes.patients import router as patients_router
from platform.api.routes.orders import router as orders_router
from platform.api.routes.results import router as results_router
from platform.api.routes.labs import router as labs_router
from platform.api.routes.auth import router as auth_router
from platform.api.routes.metrics import router as metrics_router
from platform.api.middleware.platform import PlatformMiddleware
from platform.apps.bootstrap import PlatformBootstrap


class PlatformAPI:
    def __init__(self, config: dict[str, Any] | None = None):
        self._config = config or {}
        self._bootstrap = PlatformBootstrap()
        self._app: FastAPI | None = None

    @property
    def bootstrap(self) -> PlatformBootstrap:
        return self._bootstrap

    @property
    def app(self) -> FastAPI:
        if self._app is None:
            raise RuntimeError("App not created. Call create() first.")
        return self._app

    def create(self) -> FastAPI:
        @asynccontextmanager
        async def lifespan(application: FastAPI):
            await self._bootstrap.bootstrap(config=self._config)
            yield
            await self._bootstrap.shutdown()

        self._app = FastAPI(
            title=self._config.get("title", "GULA Platform API"),
            version=self._config.get("version", "1.0.0"),
            lifespan=lifespan,
            docs_url="/docs" if self._config.get("environment") != "production" else None,
            redoc_url="/redoc" if self._config.get("environment") != "production" else None,
        )

        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=self._config.get("cors_origins", ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._app.add_middleware(PlatformMiddleware)

        self._app.include_router(health_router, prefix="/health", tags=["health"])
        self._app.include_router(patients_router, prefix="/api/v1/patients", tags=["patients"])
        self._app.include_router(orders_router, prefix="/api/v1/orders", tags=["orders"])
        self._app.include_router(results_router, prefix="/api/v1/results", tags=["results"])
        self._app.include_router(labs_router, prefix="/api/v1/labs", tags=["labs"])
        self._app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
        self._app.include_router(metrics_router, prefix="/metrics", tags=["metrics"])

        return self._app


def create_app(config: dict[str, Any] | None = None) -> FastAPI:
    api = PlatformAPI(config)
    return api.create()
