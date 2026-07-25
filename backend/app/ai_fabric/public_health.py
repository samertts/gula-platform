from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from app._compat import StrEnum

logger = logging.getLogger("gula.ai_fabric.public_health")


class AlertLevel(StrEnum):
    INFORMATION = "information"
    SURVEILLANCE = "surveillance"
    WARNING = "warning"
    OUTBREAK = "outbreak"
    CRITICAL = "critical"


class TrendDirection(StrEnum):
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    UNKNOWN = "unknown"


@dataclass
class SurveillanceSignal:
    id: str = ""
    disease: str = ""
    location: str = ""
    case_count: int = 0
    expected_count: int = 0
    threshold: float = 0.0
    z_score: float = 0.0
    alert_level: AlertLevel = AlertLevel.INFORMATION
    detected_at: float = 0.0
    recommendation: str = ""


@dataclass
class OutbreakAlert:
    id: str = ""
    disease: str = ""
    region: str = ""
    confirmed_cases: int = 0
    suspected_cases: int = 0
    transmission_type: str = ""
    severity: str = "moderate"
    status: str = "monitoring"
    first_detected: float = 0.0
    recommendation: str = ""


@dataclass
class PopulationTrend:
    metric: str = ""
    value: float = 0.0
    previous_value: float = 0.0
    change_pct: float = 0.0
    direction: TrendDirection = TrendDirection.UNKNOWN
    population: str = ""
    period: str = ""


class DiseaseSurveillance:
    def __init__(self) -> None:
        self._baselines: dict[str, dict[str, float]] = {}
        self._signals: list[SurveillanceSignal] = []

    def set_baseline(
        self,
        disease: str,
        location: str,
        expected_daily: float,
        threshold_z: float = 2.0,
    ) -> None:
        key = f"{disease}:{location}"
        self._baselines[key] = {
            "expected_daily": expected_daily,
            "threshold_z": threshold_z,
            "standard_deviation": max(expected_daily * 0.3, 1.0),
        }

    def analyze(self, disease: str, location: str, case_count: int) -> SurveillanceSignal:
        key = f"{disease}:{location}"
        baseline = self._baselines.get(key)

        signal = SurveillanceSignal(
            disease=disease,
            location=location,
            case_count=case_count,
            detected_at=time.time(),
        )

        if not baseline:
            signal.recommendation = "Establish baseline for this disease-location pair"
            return signal

        signal.expected_count = int(baseline["expected_daily"])
        signal.threshold = baseline["threshold_z"]

        if baseline["standard_deviation"] > 0:
            signal.z_score = (case_count - baseline["expected_daily"]) / baseline[
                "standard_deviation"
            ]

        if signal.z_score >= 5.0:
            signal.alert_level = AlertLevel.CRITICAL
            signal.recommendation = "IMMEDIATE INVESTIGATION REQUIRED"
        elif signal.z_score >= 3.0:
            signal.alert_level = AlertLevel.OUTBREAK
            signal.recommendation = "Initiate outbreak response protocol"
        elif signal.z_score >= 2.0:
            signal.alert_level = AlertLevel.WARNING
            signal.recommendation = "Increased surveillance required"
        elif signal.z_score >= 1.5:
            signal.alert_level = AlertLevel.SURVEILLANCE
            signal.recommendation = "Monitor closely"
        else:
            signal.alert_level = AlertLevel.INFORMATION
            signal.recommendation = "Within expected range"

        self._signals.append(signal)
        return signal

    def get_recent_alerts(
        self, min_level: AlertLevel = AlertLevel.WARNING,
    ) -> list[SurveillanceSignal]:
        levels = {
            AlertLevel.INFORMATION: 0,
            AlertLevel.SURVEILLANCE: 1,
            AlertLevel.WARNING: 2,
            AlertLevel.OUTBREAK: 3,
            AlertLevel.CRITICAL: 4,
        }
        min_val = levels.get(min_level, 0)
        return [s for s in self._signals if levels.get(s.alert_level, 0) >= min_val]

    def get_statistics(self) -> dict[str, Any]:
        by_level: dict[str, int] = {}
        for s in self._signals:
            by_level[s.alert_level.value] = by_level.get(s.alert_level.value, 0) + 1
        return {
            "total_signals": len(self._signals),
            "by_alert_level": by_level,
            "baselines_configured": len(self._baselines),
        }


class OutbreakDetector:
    def __init__(self) -> None:
        self._alerts: list[OutbreakAlert] = []
        self._cluster_threshold: int = 5

    def set_cluster_threshold(self, threshold: int) -> None:
        self._cluster_threshold = threshold

    def detect_cluster(
        self,
        disease: str,
        region: str,
        cases: list[dict[str, Any]],
    ) -> OutbreakAlert | None:
        recent_cases = [c for c in cases if self._is_recent(c.get("date", ""))]
        if len(recent_cases) < self._cluster_threshold:
            return None

        confirmed = sum(1 for c in recent_cases if c.get("confirmed", False))
        suspected = len(recent_cases) - confirmed

        alert = OutbreakAlert(
            disease=disease,
            region=region,
            confirmed_cases=confirmed,
            suspected_cases=suspected,
            severity="high" if confirmed >= 10 else "moderate",
            status="investigating",
            first_detected=time.time(),
            recommendation=self._generate_recommendation(disease, region, confirmed),
        )
        self._alerts.append(alert)
        return alert

    def detect_geographic_spread(
        self,
        disease: str,
        location_cases: dict[str, int],
    ) -> list[OutbreakAlert]:
        alerts: list[OutbreakAlert] = []
        for location, count in location_cases.items():
            if count >= self._cluster_threshold:
                alert = OutbreakAlert(
                    disease=disease,
                    region=location,
                    confirmed_cases=count,
                    severity="moderate",
                    status="monitoring",
                    first_detected=time.time(),
                    recommendation=f"Investigate increase in {location}",
                )
                alerts.append(alert)
                self._alerts.append(alert)
        return alerts

    def get_active_alerts(self) -> list[OutbreakAlert]:
        return [a for a in self._alerts if a.status in ("monitoring", "investigating")]

    def _is_recent(self, date_str: str) -> bool:
        return True

    def _generate_recommendation(self, disease: str, region: str, cases: int) -> str:
        return (
            f"Cluster of {cases} {disease} cases detected in {region}. "
            "Notify public health authorities. Initiate contact tracing."
        )


class PopulationHealthAnalytics:
    def __init__(self) -> None:
        self._trends: list[PopulationTrend] = []

    def analyze_trend(
        self,
        metric: str,
        current_value: float,
        previous_value: float,
        population: str = "",
        period: str = "",
    ) -> PopulationTrend:
        change_pct = 0.0
        if previous_value != 0:
            change_pct = ((current_value - previous_value) / abs(previous_value)) * 100

        direction = TrendDirection.UNKNOWN
        if change_pct > 5:
            direction = TrendDirection.RISING
        elif change_pct < -5:
            direction = TrendDirection.FALLING
        else:
            direction = TrendDirection.STABLE

        trend = PopulationTrend(
            metric=metric,
            value=current_value,
            previous_value=previous_value,
            change_pct=round(change_pct, 2),
            direction=direction,
            population=population,
            period=period,
        )
        self._trends.append(trend)
        return trend

    def disease_prevalence(
        self,
        disease: str,
        region: str,
        total_population: int,
        diagnosed_cases: int,
    ) -> dict[str, Any]:
        prevalence_rate = (diagnosed_cases / total_population) * 100000 if total_population else 0
        return {
            "disease": disease,
            "region": region,
            "total_population": total_population,
            "diagnosed_cases": diagnosed_cases,
            "prevalence_per_100k": round(prevalence_rate, 2),
            "severity": "high"
            if prevalence_rate > 1000
            else "moderate"
            if prevalence_rate > 100
            else "low",
        }

    def immunization_coverage(
        self,
        vaccine: str,
        eligible_population: int,
        vaccinated: int,
    ) -> dict[str, Any]:
        coverage_pct = (vaccinated / eligible_population) * 100 if eligible_population else 0
        return {
            "vaccine": vaccine,
            "eligible": eligible_population,
            "vaccinated": vaccinated,
            "coverage_pct": round(coverage_pct, 2),
            "status": "adequate" if coverage_pct >= 95 else "below_target",
            "gap": max(0, round(95 - coverage_pct, 2)),
        }
