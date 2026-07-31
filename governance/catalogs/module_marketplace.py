from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from governance.catalogs.component_registry import NationalComponentRegistry
from governance.compiler.models import ModuleStatus


class ModuleMarketplace:
    def __init__(self) -> None:
        self.registry = NationalComponentRegistry()

    def get_quality_score(self, name: str) -> dict[str, Any]:
        comp = self.registry.get_by_name(name)
        if not comp:
            return {"error": f"Component '{name}' not found"}
        score = 0
        status_scores = {
            ModuleStatus.CERTIFIED: 100,
            ModuleStatus.APPROVED: 80,
            ModuleStatus.STABLE: 70,
            ModuleStatus.EXPERIMENTAL: 40,
            ModuleStatus.DEPRECATED: 20,
            ModuleStatus.RETIRED: 0,
        }
        score += status_scores.get(comp.status, 50) * 0.4
        score += min(len(comp.documentation) * 5, 100) * 0.2
        score += min(len(comp.api_endpoints) * 10, 100) * 0.2
        score += min(len(comp.compatibility) * 10, 100) * 0.2
        return {
            "component": comp.name,
            "overall": round(score, 1),
            "status_weight": round(status_scores.get(comp.status, 50) * 0.4, 1),
            "documentation_weight": round(min(len(comp.documentation) * 5, 100) * 0.2, 1),
            "api_weight": round(min(len(comp.api_endpoints) * 10, 100) * 0.2, 1),
            "compatibility_weight": round(min(len(comp.compatibility) * 10, 100) * 0.2, 1),
        }

    def get_reuse_score(self, name: str) -> dict[str, Any]:
        comp = self.registry.get_by_name(name)
        if not comp:
            return {"error": f"Component '{name}' not found"}
        reuse_score = 60
        if comp.api_endpoints:
            reuse_score += 20
        if comp.reuse_guide:
            reuse_score += 10
        if comp.status in (ModuleStatus.CERTIFIED, ModuleStatus.APPROVED):
            reuse_score += 10
        return {
            "component": comp.name,
            "reuse_score": min(reuse_score, 100),
            "has_api": bool(comp.api_endpoints),
            "has_reuse_guide": bool(comp.reuse_guide),
            "status": comp.status.value,
        }

    def get_maintenance_score(self, name: str) -> dict[str, Any]:
        comp = self.registry.get_by_name(name)
        if not comp:
            return {"error": f"Component '{name}' not found"}
        maintenance_scores = {
            ModuleStatus.CERTIFIED: 100,
            ModuleStatus.APPROVED: 85,
            ModuleStatus.STABLE: 70,
            ModuleStatus.EXPERIMENTAL: 40,
            ModuleStatus.DEPRECATED: 15,
            ModuleStatus.RETIRED: 0,
        }
        return {
            "component": comp.name,
            "maintenance_score": maintenance_scores.get(comp.status, 50),
            "status": comp.status.value,
        }

    def get_all_scores(self) -> dict[str, Any]:
        scores = {}
        for comp in self.registry.components:
            scores[comp.name] = {
                "quality": self.get_quality_score(comp.name),
                "reuse": self.get_reuse_score(comp.name),
                "maintenance": self.get_maintenance_score(comp.name),
            }
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "total_components": len(self.registry.components),
            "scores": scores,
        }

    def list_by_status(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for comp in self.registry.components:
            s = comp.status.value
            if s not in result:
                result[s] = []
            result[s].append(comp.name)
        return result
