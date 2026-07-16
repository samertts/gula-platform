from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.kernel import Kernel

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
        await self._phase_initialize_feature_management()
        await self._phase_populate_capabilities()

        elapsed = time.monotonic() - self._start_time
        logger.info(
            "Boot sequence complete",
            extra={"phases": len(self._boot_sequence), "elapsed_ms": round(elapsed * 1000)},
        )

    async def _phase_validate_environment(self) -> None:
        logger.info("Boot phase: validate environment")
        self._start_time = time.monotonic()

        required_dirs = [
            self.kernel.config.data_dir,
            self.kernel.config.plugin_dir,
            self.kernel.config.module_dir,
        ]
        for d in required_dirs:
            if d and not __import__("os").path.exists(d):
                logger.warning("Kernel directory does not exist: %s", d)

        self._boot_sequence.append(("validate_environment", time.monotonic()))

    async def _phase_initialize_core_components(self) -> None:
        logger.info("Boot phase: initialize core components")
        from app.kernel.runtime.capability_registry import CapabilityRegistry
        from app.kernel.runtime.context import ApplicationContext
        from app.kernel.runtime.di_container import DIContainer
        from app.kernel.runtime.lifecycle import LifecycleManager
        from app.kernel.runtime.service_registry import ServiceRegistry

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

        from app.kernel.runtime.shutdown import ShutdownManager
        from app.kernel.runtime.startup import StartupManager

        startup_manager = StartupManager()
        self.kernel.register_component("startup_manager", startup_manager)

        shutdown_manager = ShutdownManager()
        self.kernel.register_component("shutdown_manager", shutdown_manager)

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
            from app.kernel.config.registry import ConfigurationRegistry

            config_registry = ConfigurationRegistry()
            self.kernel.register_component("config_registry", config_registry)
        self._boot_sequence.append(("initialize_config", time.monotonic()))

    async def _phase_initialize_plugins(self) -> None:
        logger.info("Boot phase: initialize plugins")
        if self.kernel.config.enable_plugins:
            from app.kernel.plugin.manager import PluginManager

            pm = PluginManager(self.kernel)
            self.kernel.register_component("plugin_manager", pm)
        self._boot_sequence.append(("initialize_plugins", time.monotonic()))

    async def _phase_initialize_modules(self) -> None:
        logger.info("Boot phase: initialize modules")
        if self.kernel.config.enable_modules:
            from app.kernel.module.loader import ModuleLoader

            ml = ModuleLoader(self.kernel)
            self.kernel.register_component("module_loader", ml)
        self._boot_sequence.append(("initialize_modules", time.monotonic()))

    async def _phase_initialize_event_bus(self) -> None:
        logger.info("Boot phase: initialize event bus")
        if self.kernel.config.enable_event_bus:
            from app.kernel.event_bus.bus import EventBus

            eb = EventBus(self.kernel)
            self.kernel.register_component("event_bus", eb)
        self._boot_sequence.append(("initialize_event_bus", time.monotonic()))

    async def _phase_initialize_background(self) -> None:
        logger.info("Boot phase: initialize background processing")
        if self.kernel.config.enable_background_processing:
            from app.kernel.background.scheduler import Scheduler

            scheduler = Scheduler(self.kernel)
            self.kernel.register_component("scheduler", scheduler)
        self._boot_sequence.append(("initialize_background", time.monotonic()))

    async def _phase_initialize_tenant(self) -> None:
        logger.info("Boot phase: initialize multi-tenant engine")
        if self.kernel.config.enable_multi_tenant:
            from app.kernel.tenant.registry import TenantRegistry

            tr = TenantRegistry()
            self.kernel.register_component("tenant_registry", tr)
        self._boot_sequence.append(("initialize_tenant", time.monotonic()))

    async def _phase_initialize_gateway(self) -> None:
        logger.info("Boot phase: initialize internal gateway")
        if self.kernel.config.enable_internal_gateway:
            from app.kernel.gateway.discovery import ServiceDiscovery

            sd = ServiceDiscovery(self.kernel)
            self.kernel.register_component("service_discovery", sd)
        self._boot_sequence.append(("initialize_gateway", time.monotonic()))

    async def _phase_initialize_feature_management(self) -> None:
        logger.info("Boot phase: initialize feature management")
        if self.kernel.config.enable_feature_management:
            from app.kernel.features.capabilities import CapabilityFlagManager
            from app.kernel.features.flags import FeatureFlagManager

            ffm = FeatureFlagManager(self.kernel)
            self.kernel.register_component("feature_flag_manager", ffm)

            cr = self.kernel.get_component("capability_registry")
            cfm = CapabilityFlagManager(registry=cr)
            self.kernel.register_component("capability_flag_manager", cfm)
            logger.info("Feature flag manager initialized")
        self._boot_sequence.append(("initialize_feature_management", time.monotonic()))

    async def _phase_populate_capabilities(self) -> None:
        logger.info("Boot phase: populate capability registry")
        cr = self.kernel.get_component("capability_registry")
        if cr:
            from app.kernel.capabilities_registry_populator import populate_registry

            count = populate_registry(cr)
            logger.info(
                "Capability registry populated",
                extra={"count": count},
            )

            cfm = self.kernel.get_component("capability_flag_manager")
            if cfm:
                synced = cfm.sync_from_registry()
                logger.info(
                    "Capability flag manager synced",
                    extra={"synced": synced},
                )
        self._boot_sequence.append(("populate_capabilities", time.monotonic()))
