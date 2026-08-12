from __future__ import annotations

import logging

from app.control_plane.sdk import ControlPlaneSDK

logger = logging.getLogger("gula.control_plane")


class ControlPlane:
    _instance: ControlPlane | None = None

    def __init__(self):
        if ControlPlane._instance is not None:
            raise RuntimeError("ControlPlane is a singleton. Use ControlPlane.get_instance()")
        self._sdk = ControlPlaneSDK.get_instance()
        self._initialized = False
        ControlPlane._instance = self

    @classmethod
    def get_instance(cls) -> ControlPlane:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def sdk(self) -> ControlPlaneSDK:
        return self._sdk

    @property
    def initialized(self) -> bool:
        return self._initialized

    async def initialize(self) -> None:
        if self._initialized:
            logger.warning("ControlPlane already initialized")
            return
        logger.info("ControlPlane initializing")
        await self._sdk.digital_twin.sync()
        self._initialized = True
        logger.info("ControlPlane initialized")

    async def shutdown(self) -> None:
        logger.info("ControlPlane shutting down")
        self._initialized = False
