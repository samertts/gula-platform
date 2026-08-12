from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.control_plane.digital_twin.models import (
    ApplicationTwin,
    HospitalTwin,
    InfrastructureTwin,
    LaboratoryTwin,
    OperationsStateTwin,
    SecurityStateTwin,
    ServiceTwin,
)
from app.control_plane.enums import PlatformComponent
from app.control_plane.fleet.manager import FleetManager
from app.control_plane.registry.component import ComponentRegistry
from app.control_plane.registry.health import HealthAggregator

logger = logging.getLogger("gula.control_plane.digital_twin.engine")


class DigitalTwinEngine:
    def __init__(self, registry: ComponentRegistry, fleet: FleetManager, health: HealthAggregator):
        self._registry = registry
        self._fleet = fleet
        self._health = health
        self._infra: InfrastructureTwin = InfrastructureTwin()
        self._services: dict[str, ServiceTwin] = {}
        self._applications: dict[str, ApplicationTwin] = {}
        self._hospitals: dict[str, HospitalTwin] = {}
        self._laboratories: dict[str, LaboratoryTwin] = {}
        self._security: SecurityStateTwin = SecurityStateTwin()
        self._operations: OperationsStateTwin = OperationsStateTwin()

    async def sync(self) -> None:
        fleet_summary = self._fleet.summary()
        self._infra = InfrastructureTwin(
            nodes=fleet_summary.get("nodes", 0),
            containers=fleet_summary.get("containers", 0),
            edge_devices=fleet_summary.get("edge_devices", 0),
            services=[],
            resources={},
        )

        for svc in self._registry.list():
            twin = ServiceTwin(
                name=svc.name,
                version=svc.version,
                status=svc.status.value,
                dependencies=list(svc.dependencies),
            )
            self._services[svc.name] = twin

        health_data = await self._health.aggregate()
        self._operations = OperationsStateTwin(
            health_grade=health_data.get("grade", "GREEN"),
            active_alerts=health_data.get("degraded", 0),
            degraded_components=health_data.get("degraded", 0),
        )

        logger.debug("Digital twin synced at %s", datetime.now(UTC).isoformat())

    def get_infrastructure(self) -> InfrastructureTwin:
        return self._infra

    def get_service(self, name: str) -> ServiceTwin | None:
        return self._services.get(name)

    def get_application(self, name: str) -> ApplicationTwin | None:
        return self._applications.get(name)

    def get_hospital(self, hospital_id: str) -> HospitalTwin | None:
        return self._hospitals.get(hospital_id)

    def get_laboratory(self, lab_id: str) -> LaboratoryTwin | None:
        return self._laboratories.get(lab_id)

    def get_security(self) -> SecurityStateTwin:
        return self._security

    def get_operations(self) -> OperationsStateTwin:
        return self._operations

    def get_by_component_type(self, component_type: str) -> list[dict[str, Any]]:
        mapping = {
            PlatformComponent.SERVICE: lambda: [{"name": k, "version": v.version, "status": v.status} for k, v in self._services.items()],
            PlatformComponent.PROJECT: lambda: [{"name": k, "version": v.version} for k, v in self._applications.items()],
        }
        converter = mapping.get(component_type)
        if converter:
            return converter()
        return []

    def to_dict(self) -> dict[str, Any]:
        return {
            "infrastructure": {
                "nodes": self._infra.nodes,
                "containers": self._infra.containers,
                "edge_devices": self._infra.edge_devices,
            },
            "services": {k: {"version": v.version, "status": v.status, "dependencies": v.dependencies} for k, v in self._services.items()},
            "operations": {
                "health_grade": self._operations.health_grade,
                "active_alerts": self._operations.active_alerts,
                "degraded_components": self._operations.degraded_components,
            },
            "updated_at": datetime.now(UTC).isoformat(),
        }
