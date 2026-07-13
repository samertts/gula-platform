"""
GULA Platform Kernel — Permanent Runtime Foundation
====================================================

The Kernel is the mandatory runtime foundation for every future platform
module. Nothing should bypass the Kernel.

Architecture
------------
Kernel (singleton)
├── Bootloader        — 10-phase boot sequence
├── LifecycleManager  — component start/stop lifecycle
├── ServiceRegistry   — named service locator
├── CapabilityRegistry— feature capability registration
├── DIContainer       — dependency injection (singleton/scoped/transient)
├── ApplicationContext— per-request context (request_id, tenant_id)
├── StartupManager    — ordered startup task execution
├── ShutdownManager   — priority-ordered shutdown handlers
│
├── PluginSystem      — sandboxed plugin loading with permission model
├── ModuleSystem      — module discovery and dependency resolution
├── EventBus          — internal pub/sub with outbox, inbox, DLQ, replay
├── BackgroundProcessing— scheduler, cron, task queue, worker pool, locks
├── FeatureManagement — feature flags, kill switch, regional/tenant features
├── ConfigEngine      — validated config, secrets, runtime reload, versioning
├── MultiTenantEngine — tenant registry, quotas, isolation
└── InternalGateway   — service discovery, routing, circuit breakers, rate limiting

Usage
-----
    from backend.app.kernel import Kernel, KernelConfig

    config = KernelConfig(environment="production")
    kernel = Kernel(config=config)

    await kernel.boot()
    await kernel.start()
    # ... system is running ...
    await kernel.stop()

Integration
-----------
The Kernel is automatically booted during platform startup inside
run_startup_guard() (backend/app/core/startup_guard.py) as Step 5 of the
startup validation chain, after DB/migrations/seed data are confirmed ready.

Access the Kernel from anywhere:
    from backend.app.kernel.integration import get_kernel
    kernel = get_kernel()
    kernel.register_service("my_service", instance)
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from backend.app.kernel.background.scheduler import Scheduler
from backend.app.kernel.config.registry import ConfigurationRegistry
from backend.app.kernel.event_bus.bus import EventBus
from backend.app.kernel.features.flags import FeatureFlagManager
from backend.app.kernel.gateway.discovery import ServiceDiscovery
from backend.app.kernel.module.loader import ModuleLoader
from backend.app.kernel.plugin.manager import PluginManager
from backend.app.kernel.runtime.bootloader import Bootloader
from backend.app.kernel.runtime.capability_registry import CapabilityRegistry
from backend.app.kernel.runtime.context import ApplicationContext
from backend.app.kernel.runtime.di_container import DIContainer
from backend.app.kernel.runtime.lifecycle import LifecycleManager
from backend.app.kernel.runtime.service_registry import ServiceRegistry
from backend.app.kernel.tenant.registry import TenantRegistry

logger = logging.getLogger("gula.kernel")


class KernelState(Enum):
    CREATED = auto()
    BOOTING = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    FAILED = auto()


@dataclass
class KernelConfig:
    name: str = "gula-kernel"
    version: str = "2.1.0"
    environment: str = "production"
    debug: bool = False
    boot_timeout: float = 30.0
    shutdown_timeout: float = 30.0
    enable_plugins: bool = True
    enable_event_bus: bool = True
    enable_background_processing: bool = True
    enable_feature_management: bool = True
    enable_config_engine: bool = True
    enable_multi_tenant: bool = True
    enable_internal_gateway: bool = True
    data_dir: str = "/var/lib/gula/kernel"
    plugin_dir: str = "/var/lib/gula/plugins"
    module_dir: str = "/var/lib/gula/modules"


class Kernel:
    _instance: Kernel | None = None

    def __init__(self, config: KernelConfig | None = None):
        if Kernel._instance is not None:
            raise RuntimeError("Kernel is a singleton. Use Kernel.get_instance()")
        self.config = config or KernelConfig()
        self.state = KernelState.CREATED
        self._services: dict[str, Any] = {}
        self._start_time: float = 0.0
        self._components: dict[str, Any] = {}
        Kernel._instance = self

    @classmethod
    def get_instance(cls) -> Kernel:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None

    async def boot(self) -> None:
        self.state = KernelState.BOOTING
        self._start_time = time.monotonic()
        logger.info("Kernel booting", extra={"version": self.config.version})

        bootloader = Bootloader(self)
        await bootloader.execute()

    async def start(self) -> None:
        self.state = KernelState.STARTING
        logger.info("Kernel starting")

        lifecycle = self.get_component("lifecycle_manager")
        if lifecycle:
            await lifecycle.start_all()

        self.state = KernelState.RUNNING
        logger.info(
            "Kernel running",
            extra={
                "boot_time_ms": round((time.monotonic() - self._start_time) * 1000),
            },
        )

    async def stop(self) -> None:
        self.state = KernelState.STOPPING
        logger.info("Kernel stopping")

        lifecycle = self.get_component("lifecycle_manager")
        if lifecycle:
            await lifecycle.stop_all()

        self.state = KernelState.STOPPED
        logger.info("Kernel stopped")

    def register_service(self, name: str, service: Any) -> None:
        self._services[name] = service

    def get_service(self, name: str) -> Any | None:
        return self._services.get(name)

    def register_component(self, name: str, component: Any) -> None:
        self._components[name] = component

    def get_component(self, name: str) -> Any | None:
        return self._components.get(name)

    @property
    def uptime(self) -> float:
        if self._start_time == 0:
            return 0.0
        return time.monotonic() - self._start_time

    @property
    def is_running(self) -> bool:
        return self.state == KernelState.RUNNING
