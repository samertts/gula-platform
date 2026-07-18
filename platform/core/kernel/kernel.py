import asyncio
import logging
import time
from enum import Enum
from typing import Any

from platform.core.kernel.lifecycle import LifecycleEvent, LifecycleListener
from platform.core.kernel.service_registry import ServiceRegistry
from platform.core.kernel.di_container import DIContainer
from platform.core.kernel.config_loader import ConfigLoader
from platform.core.kernel.health import HealthManager, HealthStatus
from platform.core.event_bus import EventBus


class KernelState(Enum):
    UNINITIALIZED = "uninitialized"
    BOOTING = "booting"
    CONFIGURING = "configuring"
    REGISTERING = "registering"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    RESUMING = "resuming"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class KernelConfig:
    def __init__(
        self,
        name: str = "gula-platform",
        version: str = "1.0.0",
        environment: str = "development",
        debug: bool = False,
        config_paths: list[str] | None = None,
        module_discovery_paths: list[str] | None = None,
        shutdown_timeout: float = 30.0,
        health_check_interval: float = 30.0,
        auto_recovery: bool = True,
    ):
        self.name = name
        self.version = version
        self.environment = environment
        self.debug = debug
        self.config_paths = config_paths or []
        self.module_discovery_paths = module_discovery_paths or []
        self.shutdown_timeout = shutdown_timeout
        self.health_check_interval = health_check_interval
        self.auto_recovery = auto_recovery


class Kernel:
    _instance: "Kernel | None" = None

    def __init__(self, config: KernelConfig | None = None):
        if Kernel._instance is not None:
            raise RuntimeError("Kernel is a singleton. Use Kernel.instance() to access.")
        self._config = config or KernelConfig()
        self._state = KernelState.UNINITIALIZED
        self._start_time: float = 0.0
        self._logger = logging.getLogger(f"gula.kernel.{self._config.name}")
        self._service_registry = ServiceRegistry()
        self._di_container = DIContainer()
        self._config_loader = ConfigLoader(self._config.config_paths)
        self._health_manager = HealthManager(check_interval=self._config.health_check_interval)
        self._event_bus = EventBus()
        self._lifecycle_listeners: list[LifecycleListener] = []
        self._modules: dict[str, Any] = {}
        self._background_tasks: list[asyncio.Task] = []
        self._running = False
        Kernel._instance = self

    @classmethod
    def instance(cls) -> "Kernel":
        if cls._instance is None:
            raise RuntimeError("Kernel not initialized. Call Kernel(config).boot() first.")
        return cls._instance

    @property
    def state(self) -> KernelState:
        return self._state

    @property
    def config(self) -> KernelConfig:
        return self._config

    @property
    def services(self) -> ServiceRegistry:
        return self._service_registry

    @property
    def di(self) -> DIContainer:
        return self._di_container

    def container(self) -> DIContainer:
        return self._di_container

    def module_registry(self) -> dict[str, Any]:
        return self._modules

    @property
    def config_loader(self) -> ConfigLoader:
        return self._config_loader

    @property
    def health(self) -> HealthManager:
        return self._health_manager

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def uptime(self) -> float:
        if self._start_time == 0:
            return 0.0
        return time.monotonic() - self._start_time

    def add_lifecycle_listener(self, listener: LifecycleListener) -> None:
        self._lifecycle_listeners.append(listener)

    def _emit_lifecycle_event(self, event: LifecycleEvent) -> None:
        for listener in self._lifecycle_listeners:
            try:
                listener.on_lifecycle_event(event)
            except Exception as e:
                self._logger.error("Lifecycle listener error: %s", e)

    async def boot(self, configs: dict[str, Any] | None = None) -> None:
        boot_start = time.monotonic()
        if configs:
            self._config.name = configs.get("app_name", self._config.name)
            self._config.version = configs.get("version", self._config.version)
            self._config.environment = configs.get("environment", self._config.environment)
        self._logger.info("Kernel booting — v%s, env=%s", self._config.version, self._config.environment)
        try:
            self._set_state(KernelState.BOOTING)
            self._emit_lifecycle_event(LifecycleEvent.BOOTING)

            self._set_state(KernelState.CONFIGURING)
            await self._load_configuration()
            self._emit_lifecycle_event(LifecycleEvent.CONFIGURED)

            self._set_state(KernelState.REGISTERING)
            await self._register_core_services()
            self._emit_lifecycle_event(LifecycleEvent.REGISTERED)

            self._set_state(KernelState.STARTING)
            await self._start_core_services()
            self._emit_lifecycle_event(LifecycleEvent.STARTED)

            self._start_time = time.monotonic()
            self._set_state(KernelState.RUNNING)
            self._running = True
            self._emit_lifecycle_event(LifecycleEvent.READY)

            boot_time = time.monotonic() - boot_start
            self._logger.info("Kernel ready — boot time: %.2fs, state: %s", boot_time, self._state.value)
            self._health_manager.set_system_ready(True)
        except Exception as e:
            self._logger.critical("Kernel boot failed: %s", e, exc_info=True)
            self._set_state(KernelState.FAILED)
            self._emit_lifecycle_event(LifecycleEvent.FAILED)
            raise

    async def _load_configuration(self) -> None:
        self._logger.debug("Loading configuration from %d paths", len(self._config.config_paths))
        await self._config_loader.load()

    async def _register_core_services(self) -> None:
        self._service_registry.register("kernel.config", self._config_loader)
        self._service_registry.register("kernel.health", self._health_manager)
        self._service_registry.register("kernel.di", self._di_container)
        self._service_registry.register("kernel.services", self._service_registry)
        self._logger.debug("Core services registered")

    async def _start_core_services(self) -> None:
        self._di_container.register_instance("kernel", self)
        self._di_container.register_instance("config_loader", self._config_loader)
        self._di_container.register_instance("service_registry", self._service_registry)
        self._di_container.register_instance("health_manager", self._health_manager)
        self._logger.debug("Core services initialized in DI container")

    async def register_module(self, name: str, module: Any) -> None:
        if name in self._modules:
            self._logger.warning("Module '%s' already registered, skipping", name)
            return
        self._modules[name] = module
        self._service_registry.register(f"module.{name}", module)
        self._logger.info("Module registered: %s", name)

    async def discover_modules(self) -> list[str]:
        discovered = []
        for path in self._config.module_discovery_paths:
            self._logger.debug("Discovering modules in: %s", path)
        return discovered

    async def pause(self) -> None:
        self._logger.info("Kernel pausing")
        self._emit_lifecycle_event(LifecycleEvent.PAUSING)
        self._set_state(KernelState.PAUSED)
        self._emit_lifecycle_event(LifecycleEvent.PAUSED)

    async def resume(self) -> None:
        self._logger.info("Kernel resuming")
        self._emit_lifecycle_event(LifecycleEvent.RESUMING)
        self._set_state(KernelState.RUNNING)
        self._emit_lifecycle_event(LifecycleEvent.RESUMED)

    async def shutdown(self) -> None:
        self._logger.info("Kernel shutting down")
        self._emit_lifecycle_event(LifecycleEvent.STOPPING)
        self._set_state(KernelState.STOPPING)
        self._running = False

        for task in self._background_tasks:
            task.cancel()
        if self._background_tasks:
            await asyncio.wait(self._background_tasks, timeout=self._config.shutdown_timeout)

        self._health_manager.set_system_ready(False)
        self._set_state(KernelState.STOPPED)
        self._emit_lifecycle_event(LifecycleEvent.STOPPED)
        self._logger.info("Kernel stopped")

    async def restart(self) -> None:
        self._logger.info("Kernel restarting")
        await self.shutdown()
        await self.boot()

    def _set_state(self, state: KernelState) -> None:
        old_state = self._state
        self._state = state
        self._logger.debug("Kernel state: %s → %s", old_state.value, state.value)

    def is_running(self) -> bool:
        return self._running and self._state == KernelState.RUNNING

    def get_metrics(self) -> dict[str, Any]:
        return {
            "state": self._state.value,
            "uptime": self.uptime,
            "version": self._config.version,
            "environment": self._config.environment,
            "module_count": len(self._modules),
            "services_count": len(self._service_registry._services),
            "health": self._health_manager.get_aggregate_status().value,
        }
