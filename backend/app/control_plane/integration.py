from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.control_plane import ControlPlane

if TYPE_CHECKING:
    from app.kernel import Kernel

logger = logging.getLogger("gula.control_plane.integration")

_control_plane_instance: ControlPlane | None = None


def init_control_plane() -> ControlPlane:
    global _control_plane_instance
    if _control_plane_instance is None:
        _control_plane_instance = ControlPlane.get_instance()
        logger.info("ControlPlane instance created")
    return _control_plane_instance


def get_control_plane() -> ControlPlane:
    if _control_plane_instance is None:
        raise RuntimeError("ControlPlane not initialized. Call init_control_plane() first.")
    return _control_plane_instance


async def boot_control_plane() -> None:
    cp = init_control_plane()
    logger.info("Booting ControlPlane")
    await cp.initialize()
    logger.info("ControlPlane booted successfully")


async def stop_control_plane() -> None:
    if _control_plane_instance:
        await _control_plane_instance.shutdown()
        logger.info("ControlPlane stopped")


def connect_to_kernel(kernel: Kernel) -> None:
    cp = init_control_plane()
    sr = kernel.get_component("service_registry")
    if sr:
        sr.register(
            "control_plane",
            cp,
            singleton=True,
            metadata={
                "version": "1.0.0",
                "description": "Enterprise Control Plane",
            },
        )
        logger.info("ControlPlane registered with kernel service registry")

    sdk = cp.sdk
    feature_mgr = kernel.get_component("feature_flag_manager")
    if feature_mgr and sdk.features:
        logger.info("ControlPlane connected to kernel feature management")


async def boot_control_plane_with_kernel(kernel: Kernel) -> None:
    await boot_control_plane()
    connect_to_kernel(kernel)
