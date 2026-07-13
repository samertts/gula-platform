from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.app.kernel import Kernel

logger = logging.getLogger("gula.kernel.bootloader")


class Bootloader:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self._boot_sequence: list[tuple[str, Any]] = []
        self._start_time: float = 0.0

    async def execute(self) -> None:
        self._start_time = time.monotonic()
        logger.info("Bootloader executing boot sequence")

        await self._phase_validate_environment()
        await self._phase_initialize_core_components()
        await self._phase_register_core_services()
        await self._phase_initialize_config()
        await self._phase_initialize_plugins()
        await self._phase_initialize_modules()
        await self._phase_initialize_event_bus()
        await self._phase_initialize_background()
        await self._phase_initialize_tenant()
        await self._phase_initialize_gateway()

        elapsed = time.monotonic() - self._start_time
        logger.info(
            "Boot sequence complete",
            extra={"phases": len(self._boot_sequence), "elapsed_ms": round(elapsed * 1000)},
        )

    async def _phase_validate_environment(self) -> None:
        logger.info("Boot phase: validate environment")
        self._start_time = time.monotonic()

        self._boot_sequence.append(("validate_environment", time.monotonic()))

    async def _phase_initialize_core_components(self) -> None:
        logger.info("Boot phase: initialize core components")
        from backend.app.kernel.runtime.capability_registry import CapabilityRegistry
        from backend.app.kernel.runtime.context import ApplicationContext
        from backend.app.kernel.runtime.di_container import DIContainer
        from backend.app.kernel.runtime.lifecycle import LifecycleManager
        from backend.app.kernel.runtime.service_registry import ServiceRegistry

        context = ApplicationContext(self.kernel)
        self.kernel.register_component("application_context", context)

        di = DIContainer()
        self.kernel.register_component("di_container", di)

        service_registry = ServiceRegistry()
        self.kernel.register_component("service_registry", service_registry)

        capability_registry = CapabilityRegistry()
        self.kernel.register_component("capability_registry", capability_registry)

        lifecycle = LifecycleManager()
        self.kernel.register_component("lifecycle_manager", lifecycle)

        self._boot_sequence.append(("core_components", time.monotonic()))

    async def _phase_register_core_services(self) -> None:
        logger.info("Boot phase: register core services")
        sr = self.kernel.get_component("service_registry")
        if sr:
            sr.register("kernel", self.kernel, singleton=True)
            sr.register("config", self.kernel.config, singleton=True)
        self._boot_sequence.append(("register_core_services", time.monotonic()))

    async def _phase_initialize_config(self) -> None:
        logger.info("Boot phase: initialize configuration")
        if self.kernel.config.enable_config_engine:
            from backend.app.kernel.config.registry import ConfigurationRegistry

            config_registry = ConfigurationRegistry()
            self.kernel.register_component("config_registry", config_registry)
        self._boot_sequence.append(("initialize_config", time.monotonic()))

    async def _phase_initialize_plugins(self) -> None:
        logger.info("Boot phase: initialize plugins")
        if self.kernel.config.enable_plugins:
            from backend.app.kernel.plugin.manager import PluginManager

            pm = PluginManager(self.kernel)
            self.kernel.register_component("plugin_manager", pm)
        self._boot_sequence.append(("initialize_plugins", time.monotonic()))

    async def _phase_initialize_modules(self) -> None:
        logger.info("Boot phase: initialize modules")
        from backend.app.kernel.module.loader import ModuleLoader

        ml = ModuleLoader(self.kernel)
        self.kernel.register_component("module_loader", ml)
        self._boot_sequence.append(("initialize_modules", time.monotonic()))

    async def _phase_initialize_event_bus(self) -> None:
        logger.info("Boot phase: initialize event bus")
        if self.kernel.config.enable_event_bus:
            from backend.app.kernel.event_bus.bus import EventBus

            eb = EventBus(self.kernel)
            self.kernel.register_component("event_bus", eb)
        self._boot_sequence.append(("initialize_event_bus", time.monotonic()))

    async def _phase_initialize_background(self) -> None:
        logger.info("Boot phase: initialize background processing")
        if self.kernel.config.enable_background_processing:
            from backend.app.kernel.background.scheduler import Scheduler

            scheduler = Scheduler(self.kernel)
            self.kernel.register_component("scheduler", scheduler)
        self._boot_sequence.append(("initialize_background", time.monotonic()))

    async def _phase_initialize_tenant(self) -> None:
        logger.info("Boot phase: initialize multi-tenant engine")
        if self.kernel.config.enable_multi_tenant:
            from backend.app.kernel.tenant.registry import TenantRegistry

            tr = TenantRegistry()
            self.kernel.register_component("tenant_registry", tr)
        self._boot_sequence.append(("initialize_tenant", time.monotonic()))

    async def _phase_initialize_gateway(self) -> None:
        logger.info("Boot phase: initialize internal gateway")
        if self.kernel.config.enable_internal_gateway:
            from backend.app.kernel.gateway.discovery import ServiceDiscovery

            sd = ServiceDiscovery(self.kernel)
            self.kernel.register_component("service_discovery", sd)
        self._boot_sequence.append(("initialize_gateway", time.monotonic()))
