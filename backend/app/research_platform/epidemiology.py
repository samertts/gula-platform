from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from app._compat import UTC
from app.health_data.warehouse.service import WarehouseQuery, WarehouseService

logger = logging.getLogger("gula.research_platform.epidemiology")


@dataclass
class SurveillanceAlert:
    alert_id: str
    disease: str
    region: str
    severity: str
    signal: float
    threshold: float
    observed_cases: int
    expected_cases: float
    detected_at: datetime
    message: str = ""
    recommendations: list[str] = field(default_factory=list)


class RealTimeSurveillance:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()
        self._alerts: list[SurveillanceAlert] = []

    def monitor_disease(
        self,
        disease: str,
        region: str = "",
        window_days: int = 7,
        threshold: float = 2.0,
    ) -> dict[str, Any]:
        date_from = date.today() - timedelta(days=window_days)
        query = WarehouseQuery(
            dimensions=["encounter_type"],
            measures=["diagnosis_count"],
            filters={"encounter_type": disease},
            group_by=["encounter_type"],
            date_from=date_from,
        )
        if region:
            query.filters["governorate"] = region
        result = self._warehouse.query(query)
        observed = result.get("total_rows", 0)
        expected = self._compute_expected_cases(disease, region)
        signal = observed / expected if expected > 0 else 0
        alert = SurveillanceAlert(
            alert_id=f"surv_{disease}_{region}_{datetime.now(UTC).timestamp():.0f}",
            disease=disease,
            region=region,
            severity="high" if signal > threshold else "normal",
            signal=round(signal, 2),
            threshold=threshold,
            observed_cases=observed,
            expected_cases=round(expected, 1),
            detected_at=datetime.now(UTC),
        )
        self._alerts.append(alert)
        return {
            "disease": disease,
            "region": region,
            "window_days": window_days,
            "observed_cases": observed,
            "expected_cases": round(expected, 1),
            "signal_strength": round(signal, 2),
            "threshold": threshold,
            "alert": alert.severity,
        }

    def _compute_expected_cases(self, disease: str, region: str = "") -> float:
        historical_days = 28
        date_from = date.today() - timedelta(days=historical_days + 7)
        date_to = date.today() - timedelta(days=7)
        query = WarehouseQuery(
            dimensions=["encounter_type"],
            measures=["diagnosis_count"],
            filters={"encounter_type": disease},
            group_by=["encounter_type"],
            date_from=date_from,
            date_to=date_to,
        )
        if region:
            query.filters["governorate"] = region
        result = self._warehouse.query(query)
        total = result.get("total_rows", 0)
        return total / (historical_days / 7) if historical_days > 0 else 0

    def get_alerts(self, severity: str | None = None) -> list[SurveillanceAlert]:
        if severity:
            return [a for a in self._alerts if a.severity == severity]
        return list(self._alerts)


class OutbreakDetection:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()
        self._baselines: dict[str, dict] = {}

    def cusum_alert(
        self,
        disease: str,
        region: str = "",
        window_days: int = 14,
        k: float = 0.5,
        h: float = 4.0,
    ) -> dict[str, Any]:
        date_from = date.today() - timedelta(days=window_days)
        query = WarehouseQuery(
            dimensions=["encounter_type"],
            measures=["diagnosis_count"],
            filters={"encounter_type": disease},
            group_by=["encounter_type"],
            date_from=date_from,
        )
        if region:
            query.filters["governorate"] = region
        result = self._warehouse.query(query)
        observed = result.get("total_rows", 0)
        baseline = self._get_baseline(disease, region)
        cusum_stat = max(0, observed - baseline - k)
        alert = cusum_stat > h
        return {
            "disease": disease,
            "region": region,
            "method": "cusum",
            "observed": observed,
            "baseline": round(baseline, 1),
            "k": k,
            "h": h,
            "cusum_statistic": round(cusum_stat, 2),
            "alert_triggered": alert,
            "severity": "high" if alert else "normal",
        }

    def moving_average_alert(
        self,
        disease: str,
        region: str = "",
        window: int = 7,
        threshold_std: float = 2.0,
    ) -> dict[str, Any]:
        date_from = date.today() - timedelta(days=window * 3)
        query = WarehouseQuery(
            dimensions=["encounter_type"],
            measures=["diagnosis_count"],
            filters={"encounter_type": disease},
            group_by=["encounter_type"],
            date_from=date_from,
        )
        if region:
            query.filters["governorate"] = region
        rows = query.get("rows", [])
        values = [r.get("diagnosis_count", 0) or 0 for r in rows]
        if len(values) < window:
            return {"disease": disease, "error": "insufficient data"}
        ma = sum(values[-window:]) / window
        recent = values[-1] if values else 0
        std = self._compute_std(values[-window:], ma)
        z_score = (recent - ma) / std if std > 0 else 0
        return {
            "disease": disease,
            "region": region,
            "method": "moving_average",
            "window": window,
            "moving_average": round(ma, 1),
            "current_value": recent,
            "z_score": round(z_score, 2),
            "threshold_std": threshold_std,
            "alert_triggered": abs(z_score) > threshold_std,
        }

    def _get_baseline(self, disease: str, region: str) -> float:
        key = f"{disease}:{region}"
        if key in self._baselines:
            return self._baselines[key].get("mean", 0)
        historical_days = 28
        date_from = date.today() - timedelta(days=historical_days)
        query = WarehouseQuery(
            dimensions=["encounter_type"],
            measures=["diagnosis_count"],
            filters={"encounter_type": disease},
            group_by=["encounter_type"],
            date_from=date_from,
        )
        if region:
            query.filters["governorate"] = region
        result = self._warehouse.query(query)
        total = result.get("total_rows", 0)
        mean = total / (historical_days / 7) if historical_days > 0 else 0
        self._baselines[key] = {"mean": mean}
        return mean

    @staticmethod
    def _compute_std(values: list[float], mean: float) -> float:
        variance = sum((v - mean) ** 2 for v in values) / max(len(values) - 1, 1)
        return math.sqrt(variance) if variance > 0 else 0.001


class ClusterDetector:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def geographic_clusters(
        self,
        disease: str,
        min_cases: int = 5,
        radius_km: float = 10.0,
    ) -> dict[str, Any]:
        query = WarehouseQuery(
            dimensions=["facility_ulid", "encounter_type"],
            measures=["diagnosis_count"],
            filters={"encounter_type": disease},
            group_by=["facility_ulid", "encounter_type"],
        )
        self._warehouse.query(query)
        return {
            "disease": disease,
            "min_cases": min_cases,
            "radius_km": radius_km,
            "clusters": [],
            "note": "Requires GIS coordinates for geographic clustering",
        }

    def temporal_clusters(
        self,
        disease: str,
        time_window_days: int = 7,
        min_cases: int = 3,
    ) -> dict[str, Any]:
        date_from = date.today() - timedelta(days=30)
        query = WarehouseQuery(
            dimensions=["encounter_type"],
            measures=["diagnosis_count"],
            filters={"encounter_type": disease},
            group_by=["encounter_type"],
            date_from=date_from,
        )
        result = self._warehouse.query(query)
        return {
            "disease": disease,
            "time_window_days": time_window_days,
            "min_cases": min_cases,
            "total_cases": result.get("total_rows", 0),
            "temporal_clusters": [],
            "note": "Requires daily case counts for temporal scan statistics",
        }

    def spacetime_clusters(self, disease: str) -> dict[str, Any]:
        return {
            "disease": disease,
            "note": "Requires both geographic and temporal data integration",
        }


class TrendAnalyzer:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def time_series(
        self,
        metric: str,
        disease: str | None = None,
        region: str = "",
        granularity: str = "weekly",
        periods: int = 12,
    ) -> dict[str, Any]:
        date_from = date.today() - timedelta(days=periods * 7 if granularity == "weekly" else periods * 30)
        query = WarehouseQuery(
            dimensions=["encounter_type"] if disease else [],
            measures=["diagnosis_count"],
            date_from=date_from,
        )
        if disease:
            query.filters["encounter_type"] = disease
        if region:
            query.filters["governorate"] = region
        result = self._warehouse.query(query)
        return {
            "metric": metric,
            "disease": disease,
            "region": region,
            "granularity": granularity,
            "periods": periods,
            "values": result,
        }

    def trend_direction(self, values: list[float]) -> str:
        if len(values) < 3:
            return "insufficient_data"
        recent = values[-3:]
        older = values[:-3] or [0]
        if sum(recent) / 3 > sum(older) / 3 * 1.1:
            return "increasing"
        if sum(recent) / 3 < sum(older) / 3 * 0.9:
            return "decreasing"
        return "stable"

    def seasonal_patterns(self, disease: str, years: int = 3) -> dict[str, Any]:
        return {
            "disease": disease,
            "years": years,
            "note": "Requires multi-year data for seasonal decomposition",
        }


class ForecastingEngine:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def simple_forecast(
        self,
        disease: str,
        region: str = "",
        horizon_weeks: int = 4,
    ) -> dict[str, Any]:
        date_from = date.today() - timedelta(days=56)
        query = WarehouseQuery(
            dimensions=["encounter_type"],
            measures=["diagnosis_count"],
            filters={"encounter_type": disease},
            group_by=["encounter_type"],
            date_from=date_from,
        )
        if region:
            query.filters["governorate"] = region
        result = self._warehouse.query(query)
        total = result.get("total_rows", 0)
        weekly_avg = total / 8 if total > 0 else 0
        forecast = [round(weekly_avg * (1 + 0.02 * i), 1) for i in range(horizon_weeks)]
        return {
            "disease": disease,
            "region": region,
            "horizon_weeks": horizon_weeks,
            "forecast": forecast,
            "weekly_baseline": round(weekly_avg, 1),
            "model": "moving_average",
            "confidence": "low",
        }

    def arima_forecast(self, disease: str) -> dict[str, Any]:
        return {
            "disease": disease,
            "note": "ARIMA requires statistical library integration (statsmodels)",
            "available": False,
        }


class RiskModeler:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def population_risk(
        self,
        disease: str,
        region: str = "",
        risk_factors: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "disease": disease,
            "region": region,
            "risk_factors": risk_factors or [],
            "risk_score": None,
            "note": "Requires risk factor prevalence data and model calibration",
        }

    def vulnerability_index(self, region: str) -> dict[str, Any]:
        return {
            "region": region,
            "social_vulnerability": None,
            "health_system_capacity": None,
            "environmental_risk": None,
            "composite_index": None,
            "note": "Requires multi-domain data integration for composite scoring",
        }


class EarlyWarningSystem:
    def __init__(
        self,
        surveillance: RealTimeSurveillance | None = None,
        outbreak: OutbreakDetection | None = None,
    ):
        self._surveillance = surveillance or RealTimeSurveillance()
        self._outbreak = outbreak or OutbreakDetection()
        self._warnings: list[dict] = []

    def evaluate(
        self,
        disease: str,
        region: str = "",
    ) -> dict[str, Any]:
        surveillance = self._surveillance.monitor_disease(disease, region)
        cusum = self._outbreak.cusum_alert(disease, region)
        ma = self._outbreak.moving_average_alert(disease, region)
        signals = [surveillance.get("alert"), cusum.get("severity")]
        alert_count = sum(1 for s in signals if s == "high")
        overall_severity = "high" if alert_count >= 2 else "watch" if alert_count == 1 else "normal"
        warning = {
            "disease": disease,
            "region": region,
            "overall_severity": overall_severity,
            "surveillance_signal": surveillance.get("alert"),
            "cusum_signal": cusum.get("alert_triggered"),
            "moving_average_signal": ma.get("alert_triggered"),
            "timestamp": datetime.now(UTC).isoformat(),
            "recommendations": self._recommendations(overall_severity),
        }
        self._warnings.append(warning)
        return warning

    def _recommendations(self, severity: str) -> list[str]:
        if severity == "high":
            return [
                "Notify public health authorities immediately",
                "Deploy rapid response team",
                "Enhance surveillance in surrounding regions",
                "Activate emergency preparedness plan",
            ]
        if severity == "watch":
            return [
                "Increase monitoring frequency",
                "Alert regional health directorates",
                "Prepare response resources",
            ]
        return ["Continue routine surveillance"]

    def get_warnings(self, severity: str | None = None) -> list[dict]:
        if severity:
            return [w for w in self._warnings if w.get("overall_severity") == severity]
        return list(self._warnings)
