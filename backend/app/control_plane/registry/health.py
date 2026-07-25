from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.control_plane.registry.component import ComponentRegistry
from app.core.self_healing import health as self_heal_health

logger = logging.getLogger("gula.control_plane.registry.health")


@dataclass
class ComponentHealth:
    name: str
    status: str = "unknown"
    latency_ms: float = 0.0
    error: str | None = None
    last_checked: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    details: dict[str, Any] = field(default_factory=dict)


class HealthAggregator:
    def __init__(self, registry: ComponentRegistry):
        self._registry = registry
        self._health_cache: dict[str, ComponentHealth] = {}

    async def check_component(self, name: str) -> ComponentHealth:
        comp = self._registry.get(name)
        if not comp:
            return ComponentHealth(name=name, status="not_found", error="Component not registered")

        health = ComponentHealth(name=name)
        try:
            if comp.health_endpoint:
                import httpx

                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(comp.health_endpoint)
                    health.status = "healthy" if resp.is_success else "unhealthy"
                    health.details = resp.json() if resp.content else {}
            else:
                health.status = "registered"
        except Exception as e:
            health.status = "unreachable"
            health.error = str(e)

        health.last_checked = datetime.now(UTC).isoformat()
        self._health_cache[name] = health
        return health

    async def aggregate(self) -> dict[str, Any]:
        components = self._registry.list()
        results: list[ComponentHealth] = []
        for comp in components:
            cached = self._health_cache.get(comp.name)
            if cached:
                results.append(cached)
            else:
                results.append(ComponentHealth(name=comp.name, status=comp.status.value))

        circuit_health = self_heal_health.to_dict() if hasattr(self_heal_health, "to_dict") else {}

        total = len(results)
        healthy = sum(1 for r in results if r.status in ("healthy", "active", "registered"))
        degraded = sum(1 for r in results if r.status in ("degraded", "unhealthy", "unreachable"))

        return {
            "grade": "GREEN" if healthy == total else ("YELLOW" if degraded < total else "RED"),
            "total_components": total,
            "healthy": healthy,
            "degraded": degraded,
            "components": {
                r.name: {"status": r.status, "error": r.error, "last_checked": r.last_checked}
                for r in results
            },
            "circuit_breakers": circuit_health,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def get_health(self, name: str) -> ComponentHealth | None:
        return self._health_cache.get(name)

    def clear_cache(self) -> None:
        self._health_cache.clear()
