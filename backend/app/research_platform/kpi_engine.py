from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.health_data.warehouse.service import WarehouseQuery, WarehouseService
from app.research_platform.enums import KpiCategory

logger = logging.getLogger("gula.research_platform.kpi_engine")


@dataclass
class KPIDefinition:
    code: str
    name: str
    name_ar: str = ""
    description: str = ""
    category: KpiCategory = KpiCategory.CLINICAL
    unit: str = ""
    target: float | None = None
    threshold_warning: float | None = None
    threshold_critical: float | None = None
    direction: str = "higher_is_better"
    source: str = ""
    formula: str = ""
    frequency: str = "monthly"
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KPIResult:
    code: str
    name: str
    value: float | None
    target: float | None = None
    unit: str = ""
    status: str = "unknown"
    period: str = ""
    category: str = ""
    direction: str = "higher_is_better"
    trend: str = "stable"
    deviation: float | None = None
    calculated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


class KpiRegistry:
    def __init__(self):
        self._kpis: dict[str, KPIDefinition] = {}

    def register(self, kpi: KPIDefinition) -> None:
        self._kpis[kpi.code] = kpi
        logger.info("KPI registered: %s (%s)", kpi.code, kpi.name)

    def register_batch(self, kpis: list[KPIDefinition]) -> None:
        for kpi in kpis:
            self.register(kpi)

    def get(self, code: str) -> KPIDefinition | None:
        return self._kpis.get(code)

    def list(self, category: KpiCategory | None = None) -> list[KPIDefinition]:
        if category:
            return [k for k in self._kpis.values() if k.category == category]
        return list(self._kpis.values())

    def search(self, query: str) -> list[KPIDefinition]:
        q = query.lower()
        return [
            k for k in self._kpis.values()
            if q in k.code.lower() or q in k.name.lower() or q in (k.name_ar or "").lower()
        ]

    def remove(self, code: str) -> bool:
        if code in self._kpis:
            del self._kpis[code]
            return True
        return False

    def count_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for kpi in self._kpis.values():
            counts[kpi.category.value] = counts.get(kpi.category.value, 0) + 1
        return counts


class KpiCalculator:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def calculate(self, kpi: KPIDefinition, period: str = "") -> KPIResult:
        result = KPIResult(
            code=kpi.code,
            name=kpi.name,
            value=None,
            target=kpi.target,
            unit=kpi.unit,
            category=kpi.category.value,
            direction=kpi.direction,
            period=period,
        )

        try:
            value = self._compute(kpi)
            result.value = round(value, 2) if value is not None else None
            if result.value is not None and kpi.target is not None:
                result.deviation = round(result.value - kpi.target, 2)
                if kpi.direction == "higher_is_better":
                    if result.value >= kpi.target:
                        result.status = "on_target"
                    elif kpi.threshold_warning and result.value < kpi.threshold_warning:
                        result.status = "below_target"
                    else:
                        result.status = "near_target"
                elif result.value <= kpi.target:
                    result.status = "on_target"
                elif kpi.threshold_warning and result.value > kpi.threshold_warning:
                    result.status = "above_target"
                else:
                    result.status = "near_target"
        except Exception as exc:
            logger.warning("KPI %s calculation failed: %s", kpi.code, exc)
            result.status = "error"

        return result

    def _compute(self, kpi: KPIDefinition) -> float | None:
        category_handlers: dict[KpiCategory, Callable] = {
            KpiCategory.CLINICAL: self._clinical_kpi,
            KpiCategory.LAB: self._lab_kpi,
            KpiCategory.OPERATIONAL: self._operational_kpi,
            KpiCategory.FINANCIAL: self._financial_kpi,
            KpiCategory.POPULATION: self._population_kpi,
            KpiCategory.QUALITY: self._quality_kpi,
            KpiCategory.SECURITY: self._security_kpi,
        }
        handler = category_handlers.get(kpi.category)
        if handler:
            return handler(kpi)
        return None

    def _clinical_kpi(self, kpi: KPIDefinition) -> float | None:
        return 0.0

    def _lab_kpi(self, kpi: KPIDefinition) -> float | None:
        query = WarehouseQuery(
            measures=["turnaround_hours"],
            limit=1,
        )
        result = self._warehouse.query(query)
        rows = result.get("rows", [])
        if rows and rows[0].get("turnaround_hours") is not None:
            return float(rows[0]["turnaround_hours"])
        return None

    def _operational_kpi(self, kpi: KPIDefinition) -> float | None:
        query = WarehouseQuery(
            measures=["lab_order_count"],
            limit=1,
        )
        result = self._warehouse.query(query)
        return float(result.get("total_rows", 0))

    def _financial_kpi(self, kpi: KPIDefinition) -> float | None:
        return None

    def _population_kpi(self, kpi: KPIDefinition) -> float | None:
        return None

    def _quality_kpi(self, kpi: KPIDefinition) -> float | None:
        query = WarehouseQuery(
            measures=["is_abnormal"],
            limit=1,
        )
        result = self._warehouse.query(query)
        rows = result.get("rows", [])
        if rows:
            abnormal = sum(1 for r in rows if r.get("is_abnormal"))
            total = len(rows)
            return (abnormal / total * 100) if total > 0 else None
        return None

    def _security_kpi(self, kpi: KPIDefinition) -> float | None:
        return None

    def calculate_batch(
        self,
        kpis: list[KPIDefinition],
        period: str = "",
    ) -> list[KPIResult]:
        return [self.calculate(kpi, period) for kpi in kpis]


class KPIEngine:
    def __init__(
        self,
        registry: KpiRegistry | None = None,
        calculator: KpiCalculator | None = None,
    ):
        self.registry = registry or KpiRegistry()
        self.calculator = calculator or KpiCalculator()
        self._results: dict[str, KPIResult] = {}

    def evaluate(self, kpi_code: str, period: str = "") -> KPIResult:
        kpi = self.registry.get(kpi_code)
        if not kpi:
            raise ValueError(f"KPI not found: {kpi_code}")
        result = self.calculator.calculate(kpi, period)
        self._results[kpi_code] = result
        return result

    def evaluate_all(self, period: str = "") -> list[KPIResult]:
        results = []
        for kpi in self.registry.list():
            result = self.calculator.calculate(kpi, period)
            self._results[kpi.code] = result
            results.append(result)
        return results

    def evaluate_category(self, category: KpiCategory, period: str = "") -> list[KPIResult]:
        kpis = self.registry.list(category)
        return self.calculator.calculate_batch(kpis, period)

    def get_result(self, kpi_code: str) -> KPIResult | None:
        return self._results.get(kpi_code)

    def get_alerts(self) -> list[KPIResult]:
        return [
            r for r in self._results.values()
            if r.status in ("below_target", "above_target", "error")
        ]

    def dashboard(self, category: KpiCategory | None = None) -> dict[str, Any]:
        results = self.evaluate_all()
        if category:
            results = [r for r in results if r.category == category.value]
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "total_kpis": len(results),
            "on_target": sum(1 for r in results if r.status == "on_target"),
            "near_target": sum(1 for r in results if r.status == "near_target"),
            "below_target": sum(1 for r in results if r.status == "below_target"),
            "above_target": sum(1 for r in results if r.status == "above_target"),
            "errors": sum(1 for r in results if r.status == "error"),
            "results": [
                {
                    "code": r.code,
                    "name": r.name,
                    "value": r.value,
                    "target": r.target,
                    "unit": r.unit,
                    "status": r.status,
                    "deviation": r.deviation,
                    "category": r.category,
                }
                for r in results
            ],
        }


class KpiDashboard:
    def __init__(self, engine: KPIEngine | None = None):
        self._engine = engine or KPIEngine()

    def render(self, category: KpiCategory | None = None) -> dict[str, Any]:
        return self._engine.dashboard(category)

    def report(self, period: str = "monthly") -> dict[str, Any]:
        results = self._engine.evaluate_all(period)
        return {
            "report": "National KPI Report",
            "period": period,
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "total": len(results),
                "on_target": sum(1 for r in results if r.status == "on_target"),
                "off_target": sum(1 for r in results if r.status not in ("on_target", "unknown")),
            },
            "details": [
                {
                    "code": r.code,
                    "value": r.value,
                    "target": r.target,
                    "status": r.status,
                    "deviation": r.deviation,
                }
                for r in results
            ],
        }

    def export_csv(self, period: str = "monthly") -> str:
        import csv
        import io

        results = self._engine.evaluate_all(period)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Code", "Name", "Value", "Target", "Unit", "Status", "Deviation"])
        for r in results:
            writer.writerow([r.code, r.name, r.value, r.target, r.unit, r.status, r.deviation])
        return buf.getvalue()
