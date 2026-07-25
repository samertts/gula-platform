from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.governance.services.analytics_service import NationalAnalyticsService
from app.health_data.warehouse.service import WarehouseQuery, WarehouseService
from app.research_platform.kpi_engine import KPIEngine
from app.research_platform.population_health import PopulationAnalytics

logger = logging.getLogger("gula.research_platform.bi_dashboards")


@dataclass
class DashboardCard:
    title: str
    value: Any
    unit: str = ""
    trend: str = "stable"
    icon: str = ""
    color: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardSection:
    name: str
    cards: list[DashboardCard] = field(default_factory=list)
    charts: list[dict] = field(default_factory=list)
    tables: list[dict] = field(default_factory=list)


class ExecutiveDashboard:
    def __init__(
        self,
        analytics: NationalAnalyticsService | None = None,
        kpi: KPIEngine | None = None,
    ):
        self._analytics = analytics
        self._kpi = kpi

    def render(self, time_period: str = "quarterly") -> dict[str, Any]:
        return {
            "dashboard": "National Executive Dashboard",
            "scope": "national",
            "time_period": time_period,
            "generated_at": datetime.now(UTC).isoformat(),
            "sections": {
                "health_system_overview": self._health_system_overview(),
                "population_health": self._population_summary(),
                "financial": self._financial_summary(),
                "quality_safety": self._quality_summary(),
                "kpi_alerts": self._kpi_alerts(),
            },
        }

    def _health_system_overview(self) -> dict:
        data = {}
        if self._analytics:
            data = self._analytics.national_dashboard()
        return {
            "title": "Health System Overview",
            **data,
        }

    def _population_summary(self) -> dict:
        return {
            "title": "Population Health Summary",
            "indicators": [
                {"name": "Life Expectancy", "value": None, "status": "pending"},
                {"name": "Infant Mortality", "value": None, "status": "pending"},
                {"name": "Maternal Mortality", "value": None, "status": "pending"},
            ],
        }

    def _financial_summary(self) -> dict:
        return {
            "title": "Financial Summary",
            "note": "Requires Financial Engine integration (Phase B+)",
        }

    def _quality_summary(self) -> dict:
        data = {}
        if self._analytics:
            data = self._analytics.quality_indicators()
        return {"title": "Quality & Safety", **data}

    def _kpi_alerts(self) -> dict:
        alerts = []
        if self._kpi:
            results = self._kpi.evaluate_all()
            for r in results:
                if getattr(r, "status", "") == "below_target":
                    alerts.append({"kpi": r.name, "value": r.value, "target": r.target})
        return {"alerts": alerts}


class DirectorateDashboard:
    def __init__(
        self,
        analytics: NationalAnalyticsService | None = None,
        warehouse: WarehouseService | None = None,
    ):
        self._analytics = analytics
        self._warehouse = warehouse or WarehouseService()

    def render(self, directorate_id: str) -> dict[str, Any]:
        return {
            "dashboard": "Directorate Dashboard",
            "directorate_id": directorate_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "sections": {
                "facility_overview": self._facility_overview(directorate_id),
                "workforce": self._workforce_summary(directorate_id),
                "operations": self._operations_summary(directorate_id),
            },
        }

    def _facility_overview(self, directorate_id: str) -> dict:
        facilities = []
        if self._warehouse:
            dims = self._warehouse.get_dimension("hd_wh_dim_facility")
            facilities = [f for f in dims if f.get("facility_code", "").startswith(directorate_id)]
        return {
            "title": "Facility Overview",
            "total_facilities": len(facilities),
            "active_facilities": sum(1 for f in facilities if f.get("is_active")),
        }

    def _workforce_summary(self, directorate_id: str) -> dict:
        data = {}
        if self._analytics:
            data = self._analytics.workforce_statistics()
        return {"title": "Workforce Summary", **data}

    def _operations_summary(self, directorate_id: str) -> dict:
        return {"title": "Operations Summary", "total_orders": 0, "total_results": 0}


class HospitalDashboard:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def render(self, hospital_id: str) -> dict[str, Any]:
        query = WarehouseQuery(
            measures=["lab_order_count", "encounter_type"],
            filters={"facility_ulid": hospital_id},
            group_by=["encounter_type"],
        )
        self._warehouse.query(query)
        return {
            "dashboard": "Hospital Dashboard",
            "hospital_id": hospital_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "sections": {
                "census": self._census(hospital_id),
                "performance": self._performance(hospital_id),
                "quality": self._quality(hospital_id),
            },
        }

    def _census(self, hospital_id: str) -> dict:
        return {"title": "Hospital Census", "note": "Requires bed management integration"}

    def _performance(self, hospital_id: str) -> dict:
        return {"title": "Performance Metrics", "tat_compliance": None}

    def _quality(self, hospital_id: str) -> dict:
        return {"title": "Quality Indicators", "infection_rate": None, "readmission_rate": None}


class LaboratoryDashboard:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def render(self, lab_id: str) -> dict[str, Any]:
        order_query = WarehouseQuery(
            measures=["test_count", "turnaround_hours"],
            filters={"lab_id": int(lab_id) if lab_id.isdigit() else 0},
            group_by=["status"],
        )
        orders = self._warehouse.query(order_query)
        return {
            "dashboard": "Laboratory Dashboard",
            "lab_id": lab_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "sections": {
                "test_volume": orders,
                "tat": self._tat_analysis(lab_id),
                "quality_control": self._qc_summary(lab_id),
            },
        }

    def _tat_analysis(self, lab_id: str) -> dict:
        return {"title": "Turnaround Time Analysis", "average_tat": None}

    def _qc_summary(self, lab_id: str) -> dict:
        return {"title": "Quality Control", "in_control_rate": None}


class ClinicalDashboard:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def render(self, facility_id: str) -> dict[str, Any]:
        return {
            "dashboard": "Clinical Quality Dashboard",
            "facility_id": facility_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "sections": {
                "clinical_indicators": self._clinical_indicators(facility_id),
                "patient_safety": self._patient_safety(facility_id),
                "outcomes": self._clinical_outcomes(facility_id),
            },
        }

    def _clinical_indicators(self, facility_id: str) -> dict:
        return {
            "title": "Clinical Indicators",
            "note": "Requires clinical data warehouse integration",
        }

    def _patient_safety(self, facility_id: str) -> dict:
        return {"title": "Patient Safety", "adverse_events": None}

    def _clinical_outcomes(self, facility_id: str) -> dict:
        return {"title": "Clinical Outcomes", "mortality_rate": None, "complication_rate": None}


class FinanceDashboard:
    def __init__(self):
        self._data: dict[str, Any] = {}

    def render(self, scope: str = "national", entity_id: str = "") -> dict[str, Any]:
        return {
            "dashboard": "Financial Analytics Dashboard",
            "scope": scope,
            "generated_at": datetime.now(UTC).isoformat(),
            "sections": {
                "revenue": self._revenue_analytics(scope),
                "costs": self._cost_analytics(scope),
                "budget": self._budget_utilization(scope),
                "forecast": self._financial_forecast(),
            },
        }

    def _revenue_analytics(self, scope: str) -> dict:
        return {"title": "Revenue Analytics", "note": "Requires Financial Engine (Phase B+)"}

    def _cost_analytics(self, scope: str) -> dict:
        return {"title": "Cost Analytics", "note": "Requires Financial Engine (Phase B+)"}

    def _budget_utilization(self, scope: str) -> dict:
        return {"title": "Budget Utilization", "note": "Requires Financial Engine (Phase B+)"}

    def _financial_forecast(self) -> dict:
        return {"title": "Financial Forecast", "note": "Requires Financial Engine (Phase B+)"}


class PopulationDashboard:
    def __init__(
        self,
        population: PopulationAnalytics | None = None,
        warehouse: WarehouseService | None = None,
    ):
        self._population = population or PopulationAnalytics(warehouse)

    def render(self, region: str = "national") -> dict[str, Any]:
        return {
            "dashboard": "Population Health Dashboard",
            "region": region,
            "generated_at": datetime.now(UTC).isoformat(),
            "sections": {
                "demographics": self._demographics(region),
                "disease_burden": self._disease_burden(region),
                "maternal_child": self._maternal_child_health(region),
                "ncd": self._ncd_summary(region),
                "communicable": self._communicable_summary(region),
            },
        }

    def _demographics(self, region: str) -> dict:
        return self._population.demographic_analysis(region if region != "national" else None)

    def _disease_burden(self, region: str) -> dict:
        return self._population.disease_burden(governorate=region if region != "national" else None)

    def _maternal_child_health(self, region: str) -> dict:
        return {"title": "Maternal & Child Health", "note": "Requires maternal health registry"}

    def _ncd_summary(self, region: str) -> dict:
        return {"title": "Non-Communicable Diseases", "note": "Requires NCD registry"}

    def _communicable_summary(self, region: str) -> dict:
        return {"title": "Communicable Diseases", "note": "Requires surveillance data"}
