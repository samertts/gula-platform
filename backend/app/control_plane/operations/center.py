from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.control_plane.registry.component import ComponentRegistry
from app.control_plane.registry.health import HealthAggregator
from app.core.self_healing import health as self_heal_health

logger = logging.getLogger("gula.control_plane.operations.center")


@dataclass
class DashboardSnapshot:
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    infrastructure: dict[str, Any] = field(default_factory=dict)
    clinical: dict[str, Any] = field(default_factory=dict)
    security: dict[str, Any] = field(default_factory=dict)
    ai: dict[str, Any] = field(default_factory=dict)
    performance: dict[str, Any] = field(default_factory=dict)
    capacity: dict[str, Any] = field(default_factory=dict)
    compliance: dict[str, Any] = field(default_factory=dict)


class OperationsCenter:
    def __init__(self, registry: ComponentRegistry, health: HealthAggregator):
        self._registry = registry
        self._health = health

    async def dashboard(self) -> DashboardSnapshot:
        health_data = await self._health.aggregate()
        circuits = {}
        if hasattr(self_heal_health, "to_dict"):
            circuits = self_heal_health.to_dict()

        return DashboardSnapshot(
            infrastructure={
                "components": self._registry.count(),
                "by_type": {
                    t.value: len(self._registry.list(t))
                    for t in __import__(
                        "app.control_plane.enums", fromlist=["PlatformComponent"],
                    ).PlatformComponent
                },
                "circuit_breakers": circuits,
                "health_grade": health_data.get("grade", "UNKNOWN"),
            },
            clinical={
                "status": "operational",
                "note": "Clinical operations delegated to governance layer",
            },
            security={
                "note": "Security status delegated to shared security modules",
            },
            ai={
                "note": "AI operations delegated to AI governance layer",
            },
            performance={
                "healthy_components": health_data.get("healthy", 0),
                "total_components": health_data.get("total_components", 0),
            },
            capacity={
                "registered_components": self._registry.count(),
            },
            compliance={
                "note": "Compliance status delegated to governance layer",
            },
        )
