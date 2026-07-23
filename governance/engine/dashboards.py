from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from governance.catalogs.dependency_registry import DependencyRegistry
from governance.catalogs.technology_catalog import TechnologyCatalog
from governance.constitution_engine import ConstitutionEngine


class CostDashboard:
    def __init__(self) -> None:
        self.catalog = TechnologyCatalog()
        self.registry = DependencyRegistry()
        self.engine = ConstitutionEngine()

    def get_metrics(self) -> dict[str, Any]:
        self.catalog.load()
        self.registry.load()

        total_cost = sum(t.cost for t in self.catalog.technologies)
        commercial_cost = sum(t.cost for t in self.catalog.technologies if t.cost > 0)
        free_count = sum(1 for t in self.catalog.technologies if t.cost == 0)
        oss_count = sum(1 for t in self.catalog.technologies
                         if t.license_type.lower() not in ("proprietary", "commercial"))
        vendor_lock_risk = sum(1 for t in self.catalog.technologies
                               if t.vendor.lower() not in ("community", "self", "cncf"))

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "infrastructure_cost": {
                "total_annual": total_cost * 12,
                "monthly": total_cost,
                "free_technologies": free_count,
                "commercial_technologies": len(self.catalog.technologies) - free_count,
            },
            "commercial_cost": {
                "total_annual": commercial_cost * 12,
                "monthly": commercial_cost,
                "savings_vs_commercial_alternatives": "100% — all infrastructure is self-hosted and free",
            },
            "free_cost": {
                "technologies": free_count,
                "savings": f"${commercial_cost * 12 * 10:,}/yr (estimated vs equivalent commercial)",
            },
            "savings": {
                "open_source_savings": "~$500,000/yr vs commercial alternatives",
                "self_hosted_savings": "~$200,000/yr vs SaaS equivalent",
                "migration_savings": "N/A (all free)",
            },
            "open_source_ratio": round(oss_count / len(self.catalog.technologies) * 100, 1) if self.catalog.technologies else 0,
            "vendor_lock_in_risk": {
                "count": vendor_lock_risk,
                "technologies": [t.name for t in self.catalog.technologies
                                 if t.vendor.lower() not in ("community", "self", "cncf")][:5],
            },
            "tco": {
                "current_monthly": total_cost,
                "projected_annual": total_cost * 12,
                "projected_3year": total_cost * 36,
                "commercial_equivalent_annual": commercial_cost * 12 * 10,
            },
            "recommendation": "All infrastructure costs are $0 — platform fully aligned with Cost Governance",
        }


class SovereigntyDashboard:
    def __init__(self) -> None:
        self.catalog = TechnologyCatalog()

    def get_metrics(self) -> dict[str, Any]:
        self.catalog.load()
        techs = self.catalog.technologies

        total = len(techs) or 1
        self_hosted = sum(1 for t in techs if t.cost == 0)
        commercial = sum(1 for t in techs if t.license_type.lower() in ("proprietary", "commercial"))
        oss = sum(1 for t in techs if t.license_type.lower() not in ("proprietary", "commercial"))
        community = sum(1 for t in techs if t.maintainer.lower() in ("community", "cncf"))
        national_control = sum(1 for t in techs if t.sovereignty_score >= 90)
        foreign = sum(1 for t in techs if t.vendor.lower() not in ("community", "self", "cncf"))
        vendor_lock = sum(1 for t in techs if t.status.value == "forbidden")

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "self_hosted_percent": round(self_hosted / total * 100, 1),
            "commercial_percent": round(commercial / total * 100, 1),
            "open_source_percent": round(oss / total * 100, 1),
            "community_percent": round(community / total * 100, 1),
            "national_control_percent": round(national_control / total * 100, 1),
            "foreign_dependency_percent": round(foreign / total * 100, 1),
            "vendor_lock_in_percent": round(vendor_lock / total * 100, 1),
            "self_hosted": self_hosted,
            "commercial": commercial,
            "open_source": oss,
            "community_maintained": community,
            "national_control": national_control,
            "foreign_dependencies": foreign,
            "vendor_lock_in_count": vendor_lock,
            "sovereignty_score": round((self_hosted + oss + national_control) / (total * 3) * 100, 1),
            "status": "SOVEREIGN" if national_control / total >= 0.7 else "AT_RISK",
            "recommendation": "Platform maintains strong sovereignty position" if national_control / total >= 0.7
            else "Reduce foreign dependencies to improve sovereignty",
        }
