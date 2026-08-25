from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from app.config import APP_VERSION
from app.kernel import Kernel, KernelConfig
from app.kernel.runtime.shutdown import ShutdownHandler

if TYPE_CHECKING:
    from fastapi import Request

logger = logging.getLogger("gula.kernel.integration")

_kernel_instance: Kernel | None = None


def get_kernel_config() -> KernelConfig:
    return KernelConfig(
        name=os.getenv("KERNEL_NAME", "gula-kernel"),
        version=os.getenv("APP_VERSION", APP_VERSION),
        environment=os.getenv("RUNTIME_ENV", "production"),
        debug=os.getenv("KERNEL_DEBUG", "false").lower() == "true",
        boot_timeout=float(os.getenv("KERNEL_BOOT_TIMEOUT", "30")),
        shutdown_timeout=float(os.getenv("KERNEL_SHUTDOWN_TIMEOUT", "30")),
        enable_plugins=os.getenv("KERNEL_ENABLE_PLUGINS", "true").lower() == "true",
        enable_event_bus=os.getenv("KERNEL_ENABLE_EVENT_BUS", "true").lower() == "true",
        enable_background_processing=os.getenv("KERNEL_ENABLE_BACKGROUND", "true").lower()
        == "true",
        enable_feature_management=os.getenv("KERNEL_ENABLE_FEATURES", "true").lower() == "true",
        enable_config_engine=os.getenv("KERNEL_ENABLE_CONFIG", "true").lower() == "true",
        enable_multi_tenant=os.getenv("KERNEL_ENABLE_TENANT", "true").lower() == "true",
        enable_internal_gateway=os.getenv("KERNEL_ENABLE_GATEWAY", "true").lower() == "true",
        data_dir=os.getenv("KERNEL_DATA_DIR", "/var/lib/gula/kernel"),
        plugin_dir=os.getenv("KERNEL_PLUGIN_DIR", "/var/lib/gula/plugins"),
        module_dir=os.getenv("KERNEL_MODULE_DIR", "/var/lib/gula/modules"),
    )


def init_kernel() -> Kernel:
    global _kernel_instance
    if _kernel_instance is not None:
        return _kernel_instance
    config = get_kernel_config()
    _kernel_instance = Kernel(config=config)
    return _kernel_instance


def get_kernel() -> Kernel:
    if _kernel_instance is None:
        raise RuntimeError("Kernel not initialized. Call init_kernel() first.")
    return _kernel_instance


def is_kernel_ready() -> bool:
    return _kernel_instance is not None and _kernel_instance.is_running


async def boot_kernel() -> None:
    try:
        kernel = init_kernel()
        logger.info("Booting kernel")
        await kernel.boot()
        logger.info("Kernel booted successfully")
    except Exception as e:
        logger.error("Kernel boot failed", extra={"error": str(e)})
        raise


async def start_kernel() -> None:
    global _kernel_ready
    try:
        kernel = get_kernel()
        await kernel.start()
        _kernel_ready = True
        logger.info("Kernel started successfully")
    except Exception as e:
        logger.error("Kernel start failed", extra={"error": str(e)})
        raise


async def stop_kernel() -> None:
    global _kernel_ready
    try:
        kernel = get_kernel()
        await kernel.stop()
        _kernel_ready = False
        logger.info("Kernel stopped successfully")
    except Exception as e:
        logger.error("Kernel stop failed", extra={"error": str(e)})


async def warmup_kernel() -> None:
    import time

    logger.info("Warming up kernel")
    kernel = get_kernel()
    sr = kernel.get_component("service_registry")
    if sr:
        _ = sr.list_services()
    context = kernel.get_component("application_context")
    if context:
        context.set("warmup_time", time.time())
    logger.info("Kernel warmup complete")


def register_kernel_shutdown(handler_list: list) -> None:
    kernel = get_kernel()
    sm = kernel.get_component("shutdown_manager")
    if not sm:
        return
    sm.register(ShutdownHandler(name="kernel", handler=stop_kernel, priority=10, timeout=30.0))


def kernel_kill_switch_active() -> bool:
    if os.getenv("KERNEL_KILL_SWITCH", "false").lower() == "true":
        return True
    kernel = get_kernel()
    kill_switch = kernel.get_component("emergency_kill_switch")
    if kill_switch:
        return kill_switch.is_active
    return False


def kernel_degraded_mode() -> bool:
    return os.getenv("KERNEL_DEGRADED", "false").lower() == "true"


async def get_kernel_health() -> dict:
    kernel = get_kernel()
    health = {
        "status": "ok" if is_kernel_ready() else "not_ready",
        "uptime_seconds": round(kernel.uptime, 2),
        "state": str(kernel.state),
        "components": {},
    }
    for name in ["application_context", "di_container", "service_registry", "capability_registry"]:
        comp = kernel.get_component(name)
        health["components"][name] = comp is not None
    if is_kernel_ready():
        sr = kernel.get_component("service_registry")
        if sr:
            health["services"] = len(sr.list_services())
        cr = kernel.get_component("capability_registry")
        if cr:
            health["capabilities"] = len(cr.list_capabilities())
    return health


async def kernel_middleware(request: Request, call_next):
    if not is_kernel_ready():
        return await call_next(request)
    kernel = get_kernel()
    ctx = kernel.get_component("application_context")
    if ctx:
        request_id = request.headers.get("X-Request-ID", "")
        if request_id:
            ctx.set_request_id(request_id)
    try:
        response = await call_next(request)
        if ctx:
            response.headers["X-Kernel-Version"] = kernel.config.version
            if kernel_kill_switch_active():
                response.headers["X-Kernel-Kill-Switch"] = "active"
        return response
    finally:
        if ctx:
            ctx.clear()
