import logging
from typing import Any

from platform.core.kernel import Kernel
from platform.core.modules.registrar import get_registered_modules
from platform.core.observability import MetricsCollector
from platform.domain.services import (
    AuditService, NotificationService,
    PatientService, OrderService, ResultService, LabService, AuthService,
)
from platform.integration.bridge import IntegrationBridge, BridgeConfig
from platform.migration.bridge import ServiceBridge, MigrationState


class PlatformBootstrap:
    def __init__(self, integration_bridge: IntegrationBridge | None = None):
        self._logger = logging.getLogger("gula.bootstrap")
        self._kernel = Kernel.instance()
        self._bridge = integration_bridge or IntegrationBridge()
        self._service_bridge = ServiceBridge()

    async def bootstrap(self, config: dict[str, Any] | None = None) -> Kernel:
        self._logger.info("Platform bootstrap starting")

        bridge_cfg = BridgeConfig(
            database_url=(config or {}).get("database_url", ""),
            redis_url=(config or {}).get("redis_url", ""),
            enable_monolith=(config or {}).get("enable_monolith", False),
            enable_database=(config or {}).get("enable_database", True),
            enable_redis=(config or {}).get("enable_redis", True),
            enable_http=(config or {}).get("enable_http", True),
        )
        self._bridge = IntegrationBridge(bridge_cfg)

        if not self._kernel.is_running():
            await self._kernel.boot(configs={
                "app_name": (config or {}).get("app_name", "gula-platform"),
                "version": (config or {}).get("version", "1.0.0"),
                "environment": (config or {}).get("environment", "development"),
            })

        await self._bootstrap_integration()
        self._register_domain_services()
        await self._register_modules()
        self._register_migration_bridge()

        self._logger.info("Platform bootstrap complete")
        return self._kernel

    async def _bootstrap_integration(self) -> None:
        await self._bridge.bootstrap()
        self._kernel.container().register_instance("integration_bridge", self._bridge)
        if self._bridge.db:
            self._kernel.container().register_instance("db", self._bridge.db)
        if self._bridge.redis:
            self._kernel.container().register_instance("redis", self._bridge.redis)
        if self._bridge.monolith:
            self._kernel.container().register_instance("monolith", self._bridge.monolith)

    def _register_domain_services(self) -> None:
        db = self._bridge.db
        monolith = self._bridge.monolith
        event_bus = self._kernel.event_bus

        metrics = MetricsCollector()
        self._kernel.container().register_instance("metrics_collector", metrics)

        audit = AuditService(db_adapter=db, monolith_adapter=monolith)
        notifications = NotificationService(db_adapter=db, event_bus=event_bus)
        self._kernel.container().register_instance("audit_service", audit)
        self._kernel.container().register_instance("notification_service", notifications)

        services = {
            "patient_service": PatientService(db_adapter=db, monolith_adapter=monolith),
            "order_service": OrderService(db_adapter=db, monolith_adapter=monolith, event_bus=event_bus),
            "result_service": ResultService(db_adapter=db, monolith_adapter=monolith),
            "lab_service": LabService(db_adapter=db, monolith_adapter=monolith),
            "auth_service": AuthService(monolith_adapter=monolith),
        }
        for name, svc in services.items():
            self._kernel.container().register_instance(name, svc)

    async def _register_modules(self) -> None:
        for module_name, module_class in get_registered_modules().items():
            deps = self._resolve_module_deps(module_name)
            instance = module_class(**deps)
            self._kernel.module_registry()[module_name] = instance
            await instance.initialize()
            self._logger.info("Module initialized: %s", module_name)

        for module_name, instance in self._kernel.module_registry().items():
            await instance.start()
            self._logger.info("Module started: %s", module_name)

    def _resolve_module_deps(self, module_name: str) -> dict[str, Any]:
        container = self._kernel.container()
        mapping = {
            "gula.patient": {"patient_service": "patient_service", "audit_service": "audit_service"},
            "gula.order": {"order_service": "order_service", "audit_service": "audit_service", "notification_service": "notification_service"},
            "gula.result": {"result_service": "result_service", "audit_service": "audit_service"},
            "gula.lab": {"lab_service": "lab_service", "audit_service": "audit_service"},
            "gula.user": {"auth_service": "auth_service", "audit_service": "audit_service"},
            "gula.report": {},
        }
        deps = {}
        for param, service_name in mapping.get(module_name, {}).items():
            svc = container.get(service_name)
            if svc:
                deps[param] = svc
        return deps

    def _register_migration_bridge(self) -> None:
        self._service_bridge.register("patient", monolith_impl=self._bridge.monolith, native_impl=self._kernel.container().get("patient_service"), state=MigrationState.BRIDGE)
        self._service_bridge.register("order", monolith_impl=self._bridge.monolith, native_impl=self._kernel.container().get("order_service"), state=MigrationState.BRIDGE)
        self._service_bridge.register("result", monolith_impl=self._bridge.monolith, native_impl=self._kernel.container().get("result_service"), state=MigrationState.BRIDGE)
        self._service_bridge.register("lab", monolith_impl=self._bridge.monolith, native_impl=self._kernel.container().get("lab_service"), state=MigrationState.BRIDGE)
        self._service_bridge.register("auth", monolith_impl=self._bridge.monolith, native_impl=self._kernel.container().get("auth_service"), state=MigrationState.MONOLITH)
        self._kernel.container().register_instance("service_bridge", self._service_bridge)

    async def shutdown(self) -> None:
        self._logger.info("Platform shutdown starting")
        for module_name, instance in reversed(list(self._kernel.module_registry().items())):
            await instance.stop()
            self._logger.info("Module stopped: %s", module_name)
        await self._bridge.shutdown()
        if self._kernel.is_running():
            self._kernel.shutdown()
        self._logger.info("Platform shutdown complete")

    @property
    def kernel(self) -> Kernel:
        return self._kernel

    @property
    def service_bridge(self) -> ServiceBridge:
        return self._service_bridge
