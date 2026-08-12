from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.control_plane.registry.component import ComponentRegistry
from app.control_plane.registry.health import HealthAggregator
from app.kernel.integration import get_kernel

logger = logging.getLogger("gula.control_plane.analytics")


class EnterpriseAnalytics:
    def __init__(self, registry: ComponentRegistry, health: HealthAggregator):
        self._registry = registry
        self._health = health

    async def operational_kpis(self) -> dict[str, Any]:
        health = await self._health.aggregate()
        return {
            "category": "operational",
            "total_components": self._registry.count(),
            "healthy_components": health.get("healthy", 0),
            "degraded_components": health.get("degraded", 0),
            "health_grade": health.get("grade", "UNKNOWN"),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def clinical_kpis(self) -> dict[str, Any]:
        return {
            "category": "clinical",
            "status": "delegated",
            "note": "Clinical KPIs delegated to governance analytics service",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def laboratory_kpis(self) -> dict[str, Any]:
        return {
            "category": "laboratory",
            "status": "delegated",
            "note": "Laboratory KPIs delegated to governance analytics service",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def security_kpis(self) -> dict[str, Any]:
        return {
            "category": "security",
            "note": "Security KPIs delegated to shared security modules",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def performance_kpis(self) -> dict[str, Any]:
        health = await self._health.aggregate()
        components_health = health.get("components", {})
        return {
            "category": "performance",
            "total_components": self._registry.count(),
            "responsive": sum(1 for c in components_health.values() if c.get("status") in ("healthy", "active")),
            "unreachable": sum(1 for c in components_health.values() if c.get("status") == "unreachable"),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def reliability_kpis(self) -> dict[str, Any]:
        return {
            "category": "reliability",
            "circuit_breakers": "delegated_to_self_healing",
            "uptime": "delegated_to_kernel",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def availability_kpis(self) -> dict[str, Any]:
        health = await self._health.aggregate()
        total = health.get("total_components", 0)
        healthy = health.get("healthy", 0)
        availability = round((healthy / total * 100), 2) if total > 0 else 0.0
        return {
            "category": "availability",
            "percentage": availability,
            "healthy": healthy,
            "total": total,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def engineering_kpis(self) -> dict[str, Any]:
        kernel = get_kernel()
        sr = kernel.get_component("service_registry")
        services = sr.list_services() if sr else []
        return {
            "category": "engineering",
            "services_count": len(services),
            "registered_components": self._registry.count(),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def all_kpis(self) -> dict[str, Any]:
        operational, performance, availability, engineering = await self._gather(
            self.operational_kpis(),
            self.performance_kpis(),
            self.availability_kpis(),
            self.engineering_kpis(),
        )
        return {
            "operational": operational,
            "performance": performance,
            "availability": availability,
            "engineering": engineering,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def _gather(self, *coros) -> tuple:
        import asyncio
        return await asyncio.gather(*coros)
