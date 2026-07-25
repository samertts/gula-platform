from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.national.intelligence.laboratory")

_MAINTENANCE_SCHEDULES: dict[str, list[dict[str, Any]]] = {
    "hematology_analyzer": [
        {"component": "optical_sensor", "interval_hours": 500, "action": "clean_calibrate"},
        {"component": "fluidics", "interval_hours": 1000, "action": "replace_tubing"},
        {"component": "laser", "interval_hours": 2000, "action": "replace_laser"},
    ],
    "chemistry_analyzer": [
        {"component": "reaction_cell", "interval_hours": 1000, "action": "replace_cells"},
        {"component": "pipettor", "interval_hours": 5000, "action": "replace_pipettor"},
        {"component": "detector", "interval_hours": 3000, "action": "calibrate_detector"},
    ],
    "immunoassay_analyzer": [
        {"component": "wash_system", "interval_hours": 500, "action": "clean_wash"},
        {"component": "optical_module", "interval_hours": 2000, "action": "calibrate_optics"},
    ],
}


@dataclass
class AnalyzerHealth:
    analyzer_id: str = ""
    health_score: float = 1.0
    status: str = "healthy"
    predicted_failure_days: float | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    last_maintenance: float = 0.0
    uptime_hours: float = 0.0


@dataclass
class QCTrend:
    test_code: str = ""
    mean: float = 0.0
    std: float = 0.0
    cv_percent: float = 0.0
    trend_direction: str = "stable"
    outliers: int = 0
    recommended_frequency: str = "daily"


@dataclass
class ReagentForecast:
    test_code: str = ""
    daily_usage: float = 0.0
    current_stock: float = 0.0
    days_until_reorder: float = 0.0
    recommended_order_date: float = 0.0
    forecasted_usage: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TATData:
    lab_id: str = ""
    test_code: str = ""
    period_days: int = 30
    avg_tat_minutes: float = 0.0
    p50_tat_minutes: float = 0.0
    p95_tat_minutes: float = 0.0
    bottlenecks: list[dict[str, Any]] = field(default_factory=list)


class AnalyzerHealthPredictor:
    def __init__(self) -> None:
        self._health_history: dict[str, list[dict[str, Any]]] = {}

    def record_metrics(self, analyzer_id: str, metrics: dict[str, float]) -> None:
        if analyzer_id not in self._health_history:
            self._health_history[analyzer_id] = []
        self._health_history[analyzer_id].append(
            {
                "metrics": metrics,
                "timestamp": time.time(),
            },
        )
        if len(self._health_history[analyzer_id]) > 1000:
            self._health_history[analyzer_id] = self._health_history[analyzer_id][-1000:]

    def predict_failure(self, analyzer_id: str, metrics: dict[str, float]) -> dict[str, Any]:
        health_score = self._compute_health_score(metrics)
        failure_probability = max(0.0, 1.0 - health_score)
        days_to_failure: float | None = None
        if failure_probability > 0.3:
            days_to_failure = round((1.0 - failure_probability) * 90, 1)
        return {
            "analyzer_id": analyzer_id,
            "health_score": round(health_score, 3),
            "failure_probability": round(failure_probability, 3),
            "predicted_days_to_failure": days_to_failure,
            "recommendations": self._generate_failure_recommendations(metrics, health_score),
        }

    def _compute_health_score(self, metrics: dict[str, float]) -> float:
        score = 1.0
        error_rate = metrics.get("error_rate", 0.0)
        score -= error_rate * 5.0
        calibration_deviation = metrics.get("calibration_deviation", 0.0)
        score -= calibration_deviation * 2.0
        temperature_deviation = metrics.get("temperature_deviation", 0.0)
        score -= temperature_deviation * 3.0
        vibration_level = metrics.get("vibration_level", 0.0)
        score -= vibration_level * 2.0
        return max(0.0, min(1.0, score))

    def _generate_failure_recommendations(
        self, metrics: dict[str, float], health_score: float,
    ) -> list[str]:
        recs = []
        if health_score < 0.3:
            recs.append("Immediate maintenance required")
            recs.append("Schedule emergency service call")
        elif health_score < 0.6:
            recs.append("Schedule preventive maintenance within 7 days")
            recs.append("Check calibration standards")
        if metrics.get("error_rate", 0) > 0.05:
            recs.append("Investigate recurring errors")
        if metrics.get("temperature_deviation", 0) > 2.0:
            recs.append("Check environmental temperature control")
        return recs

    def recommend_maintenance(
        self, analyzer_id: str, analyzer_type: str | None = None,
    ) -> list[dict[str, Any]]:
        upkeep: list[dict[str, Any]] = []
        schedule = _MAINTENANCE_SCHEDULES.get(analyzer_type or "chemistry_analyzer", [])
        history = self._health_history.get(analyzer_id, [])
        total_hours = 0.0
        if history:
            first = history[0]["timestamp"]
            total_hours = (time.time() - first) / 3600
        for item in schedule:
            hours_since_last = total_hours % item["interval_hours"]
            due_in_hours = item["interval_hours"] - hours_since_last
            upkeep.append(
                {
                    "component": item["component"],
                    "action": item["action"],
                    "interval_hours": item["interval_hours"],
                    "hours_since_last_maintenance": round(hours_since_last, 1),
                    "due_in_hours": round(due_in_hours, 1),
                    "due": due_in_hours < 24,
                },
            )
        return upkeep

    def get_health_score(self, analyzer_id: str, metrics: dict[str, float] | None = None) -> float:
        if metrics:
            return round(self._compute_health_score(metrics), 3)
        history = self._health_history.get(analyzer_id, [])
        if not history:
            return 1.0
        latest = history[-1]["metrics"]
        return round(self._compute_health_score(latest), 3)

    def get_historical_health(self, analyzer_id: str, days: int = 30) -> list[dict[str, Any]]:
        history = self._health_history.get(analyzer_id, [])
        cutoff = time.time() - days * 86400
        filtered = [h for h in history if h["timestamp"] >= cutoff]
        return [
            {
                "timestamp": h["timestamp"],
                "health_score": round(self._compute_health_score(h["metrics"]), 3),
                "metrics": h["metrics"],
            }
            for h in filtered
        ]


class QCPredictor:
    def __init__(self) -> None:
        self._qc_history: dict[str, list[dict[str, Any]]] = {}

    def record_qc_result(
        self, test_code: str, lot_number: str, instrument: str, value: float,
    ) -> None:
        key = f"{test_code}:{lot_number}:{instrument}"
        if key not in self._qc_history:
            self._qc_history[key] = []
        self._qc_history[key].append({"value": value, "timestamp": time.time()})

    def predict_qc_failure(
        self,
        test_code: str,
        lot_number: str,
        instrument: str,
    ) -> dict[str, Any]:
        key = f"{test_code}:{lot_number}:{instrument}"
        history = self._qc_history.get(key, [])
        if len(history) < 3:
            return {
                "test_code": test_code,
                "failure_probability": 0.0,
                "status": "insufficient_data",
                "message": "Need at least 3 QC measurements to predict failure",
            }
        values = [h["value"] for h in history]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(variance)
        cv = std / mean if mean > 0 else 0
        latest_values = values[-3:]
        drift = abs(latest_values[-1] - latest_values[0])
        failure_probability = min(1.0, (cv * 2.0) + (drift / mean if mean > 0 else 0))
        return {
            "test_code": test_code,
            "lot_number": lot_number,
            "instrument": instrument,
            "failure_probability": round(failure_probability, 3),
            "mean": round(mean, 4),
            "std": round(std, 4),
            "cv_percent": round(cv * 100, 2),
            "drift": round(drift, 4),
            "status": "critical"
            if failure_probability > 0.7
            else "warning"
            if failure_probability > 0.4
            else "stable",
        }

    def get_qc_trends(self, test_code: str, days: int = 30) -> list[QCTrend]:
        cutoff = time.time() - days * 86400
        trends: list[QCTrend] = []
        for key, history in self._qc_history.items():
            if not key.startswith(test_code):
                continue
            filtered = [h for h in history if h["timestamp"] >= cutoff]
            if len(filtered) < 2:
                continue
            values = [h["value"] for h in filtered]
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std = math.sqrt(variance)
            cv = std / mean if mean > 0 else 0
            half = len(values) // 2
            recent_mean = sum(values[half:]) / len(values[half:])
            early_mean = sum(values[:half]) / len(values[:half])
            direction = (
                "increasing"
                if recent_mean > early_mean * 1.05
                else "decreasing"
                if recent_mean < early_mean * 0.95
                else "stable"
            )
            outlier_count = sum(1 for v in values if abs(v - mean) > 2 * std)
            trends.append(
                QCTrend(
                    test_code=test_code,
                    mean=round(mean, 4),
                    std=round(std, 4),
                    cv_percent=round(cv * 100, 2),
                    trend_direction=direction,
                    outliers=outlier_count,
                ),
            )
        return trends

    def recommend_qc_frequency(self, test_code: str, volume: int) -> str:
        if volume > 500:
            return "daily"
        if volume > 100:
            return "weekly"
        return "monthly"


class ReagentPredictor:
    def __init__(self) -> None:
        self._usage_history: dict[str, list[dict[str, Any]]] = {}
        self._inventory: dict[str, dict[str, Any]] = {}

    def record_usage(self, test_code: str, quantity: float) -> None:
        if test_code not in self._usage_history:
            self._usage_history[test_code] = []
        self._usage_history[test_code].append(
            {
                "quantity": quantity,
                "timestamp": time.time(),
            },
        )

    def set_inventory(
        self, reagent_id: str, current_stock: float, reorder_point: float = 0.0,
    ) -> None:
        self._inventory[reagent_id] = {
            "current_stock": current_stock,
            "reorder_point": reorder_point,
            "updated_at": time.time(),
        }

    def predict_reagent_usage(
        self, test_code: str, historical_volume: float | None = None,
    ) -> dict[str, Any]:
        history = self._usage_history.get(test_code, [])
        if not history and historical_volume is None:
            return {
                "test_code": test_code,
                "predicted_daily_usage": 0.0,
                "confidence": 0.0,
                "message": "No historical data available",
            }
        if history:
            quantities = [h["quantity"] for h in history[-90:]]
            daily_usage = sum(quantities) / max(len(quantities), 1)
        else:
            daily_usage = historical_volume / 30.0 if historical_volume else 0.0
        recent = history[-30:] if len(history) >= 30 else history
        trend = 1.0
        if len(recent) >= 10:
            half = len(recent) // 2
            recent_avg = sum(h["quantity"] for h in recent[half:]) / max(len(recent[half:]), 1)
            early_avg = sum(h["quantity"] for h in recent[:half]) / max(len(recent[:half]), 1)
            if early_avg > 0:
                trend = recent_avg / early_avg
        projected = daily_usage * trend
        return {
            "test_code": test_code,
            "predicted_daily_usage": round(projected, 2),
            "daily_trend_factor": round(trend, 3),
            "confidence": round(min(1.0, len(history) / 90), 2) if history else 0.3,
            "data_points": len(history),
        }

    def estimate_reorder_date(
        self,
        reagent: str,
        current_stock: float,
        usage_rate: float,
    ) -> dict[str, Any]:
        if usage_rate <= 0:
            return {
                "reagent": reagent,
                "days_until_depleted": float("inf"),
                "recommended_reorder_date": None,
                "urgent": False,
            }
        days_until_depleted = current_stock / usage_rate
        safety_days = 7
        reorder_in_days = max(0, days_until_depleted - safety_days)
        return {
            "reagent": reagent,
            "current_stock": current_stock,
            "daily_usage_rate": usage_rate,
            "days_until_depleted": round(days_until_depleted, 1),
            "recommended_reorder_in_days": round(reorder_in_days, 1),
            "recommended_reorder_date": time.time() + reorder_in_days * 86400,
            "urgent": days_until_depleted <= safety_days,
        }

    def get_reagent_forecast(self, lab_id: str, days: int = 90) -> list[ReagentForecast]:
        forecasts: list[ReagentForecast] = []
        for test_code, history in self._usage_history.items():
            quantities = [h["quantity"] for h in history[-days:]]
            if not quantities:
                continue
            daily_usage = sum(quantities) / max(len(quantities), 1)
            inventory = self._inventory.get(test_code, {})
            current_stock = inventory.get("current_stock", 0)
            days_until_reorder = current_stock / daily_usage if daily_usage > 0 else float("inf")
            forecast = ReagentForecast(
                test_code=test_code,
                daily_usage=round(daily_usage, 2),
                current_stock=current_stock,
                days_until_reorder=round(days_until_reorder, 1),
                recommended_order_date=time.time() + max(0, days_until_reorder - 7) * 86400,
            )
            forecasts.append(forecast)
        return forecasts


class TurnaroundOptimizer:
    def __init__(self) -> None:
        self._tat_records: dict[str, list[dict[str, Any]]] = {}

    def record_tat(self, lab_id: str, test_code: str, tat_minutes: float) -> None:
        key = f"{lab_id}:{test_code}"
        if key not in self._tat_records:
            self._tat_records[key] = []
        self._tat_records[key].append({"tat": tat_minutes, "timestamp": time.time()})

    def analyze_tat(self, lab_id: str, test_code: str, period: int = 30) -> TATData:
        key = f"{lab_id}:{test_code}"
        records = self._tat_records.get(key, [])
        cutoff = time.time() - period * 86400
        filtered = [r for r in records if r["timestamp"] >= cutoff]
        if not filtered:
            return TATData(
                lab_id=lab_id,
                test_code=test_code,
                period_days=period,
                avg_tat_minutes=0.0,
                p50_tat_minutes=0.0,
                p95_tat_minutes=0.0,
            )
        tats = sorted(r["tat"] for r in filtered)
        n = len(tats)
        avg = sum(tats) / n
        p50 = tats[n // 2]
        p95_idx = int(n * 0.95)
        p95 = tats[min(p95_idx, n - 1)]
        bottlenecks = self.identify_bottlenecks(
            {
                "avg_tat_minutes": avg,
                "p50_tat_minutes": p50,
                "p95_tat_minutes": p95,
                "sample_count": n,
            },
        )
        return TATData(
            lab_id=lab_id,
            test_code=test_code,
            period_days=period,
            avg_tat_minutes=round(avg, 1),
            p50_tat_minutes=round(p50, 1),
            p95_tat_minutes=round(p95, 1),
            bottlenecks=bottlenecks,
        )

    def identify_bottlenecks(self, tat_data: dict[str, Any]) -> list[dict[str, Any]]:
        bottlenecks: list[dict[str, Any]] = []
        p95 = tat_data.get("p95_tat_minutes", 0)
        avg = tat_data.get("avg_tat_minutes", 0)
        if p95 > 120:
            bottlenecks.append(
                {
                    "stage": "overall",
                    "severity": "critical",
                    "metric": f"p95={p95}m",
                    "target": "< 120m",
                    "gap": round(p95 - 120, 1),
                },
            )
        elif p95 > 60:
            bottlenecks.append(
                {
                    "stage": "overall",
                    "severity": "warning",
                    "metric": f"p95={p95}m",
                    "target": "< 60m",
                    "gap": round(p95 - 60, 1),
                },
            )
        if avg > 0 and p95 > avg * 3:
            bottlenecks.append(
                {
                    "stage": "variability",
                    "severity": "warning",
                    "metric": f"p95/avg ratio={round(p95 / avg, 1)}",
                    "target": "< 3.0",
                },
            )
        return bottlenecks

    def recommend_optimizations(self, bottlenecks: list[dict[str, Any]]) -> list[str]:
        recommendations: list[str] = []
        for b in bottlenecks:
            if b.get("stage") == "overall" and b.get("severity") == "critical":
                recommendations.append("Implement priority queuing for STAT orders")
                recommendations.append("Add dedicated processing during peak hours")
            elif b.get("stage") == "overall" and b.get("severity") == "warning":
                recommendations.append("Review pre-analytical processing workflow")
                recommendations.append("Consider additional staffing during high-volume periods")
            if b.get("stage") == "variability":
                recommendations.append("Standardize processing protocols to reduce variability")
        return recommendations


class WorkloadDistributor:
    def analyze_workload(
        self, analyzers: list[dict[str, Any]], queued_tests: list[dict[str, Any]],
    ) -> dict[str, Any]:
        analysis: dict[str, Any] = {
            "total_analyzers": len(analyzers),
            "total_queued_tests": len(queued_tests),
            "analyzer_load": [],
            "estimated_completion_time": 0.0,
        }
        for analyzer in analyzers:
            capacity = analyzer.get("hourly_capacity", 10)
            current_load = analyzer.get("current_queue", 0) + sum(
                1 for t in queued_tests if t.get("preferred_analyzer") == analyzer.get("id")
            )
            load_percent = (current_load / capacity) * 100 if capacity > 0 else 100
            analysis["analyzer_load"].append(
                {
                    "analyzer_id": analyzer.get("id"),
                    "name": analyzer.get("name", ""),
                    "current_queue": current_load,
                    "hourly_capacity": capacity,
                    "load_percent": round(load_percent, 1),
                    "status": "overloaded"
                    if load_percent > 80
                    else "optimal"
                    if load_percent > 50
                    else "underutilized",
                },
            )
        loads = [a["load_percent"] for a in analysis["analyzer_load"]]
        analysis["average_load_percent"] = round(sum(loads) / len(loads), 1) if loads else 0.0
        return analysis

    def suggest_distribution(
        self,
        analyzers: list[dict[str, Any]],
        tests: list[dict[str, Any]],
        priorities: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        assignments: list[dict[str, Any]] = []
        analyzer_queue = {
            a["id"]: {"load": a.get("current_queue", 0), "capacity": a.get("hourly_capacity", 10)}
            for a in analyzers
        }
        sorted_tests = sorted(
            tests,
            key=lambda t: -(priorities or {}).get(t.get("id", ""), 0),
        )
        for test in sorted_tests:
            best_analyzer = min(
                analyzer_queue.keys(),
                key=lambda aid: (
                    analyzer_queue[aid]["load"] / max(analyzer_queue[aid]["capacity"], 1)
                ),
            )
            assignments.append(
                {
                    "test_id": test.get("id", ""),
                    "test_name": test.get("name", ""),
                    "assigned_analyzer": best_analyzer,
                    "priority": (priorities or {}).get(test.get("id", ""), 0),
                    "estimated_queue_time": analyzer_queue[best_analyzer]["load"],
                },
            )
            analyzer_queue[best_analyzer]["load"] += 1
        return assignments

    def balance_workload(self, assignments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        analyzer_counts: dict[str, int] = {}
        for a in assignments:
            aid = a["assigned_analyzer"]
            analyzer_counts[aid] = analyzer_counts.get(aid, 0) + 1
        if not analyzer_counts:
            return assignments
        target = sum(analyzer_counts.values()) / len(analyzer_counts)
        overloaded = [aid for aid, count in analyzer_counts.items() if count > target * 1.2]
        underloaded = [aid for aid, count in analyzer_counts.items() if count < target * 0.8]
        for test in assignments:
            if test["assigned_analyzer"] in overloaded and underloaded:
                new_analyzer = underloaded.pop(0)
                analyzer_counts[test["assigned_analyzer"]] -= 1
                analyzer_counts[new_analyzer] = analyzer_counts.get(new_analyzer, 0) + 1
                test["assigned_analyzer"] = new_analyzer
                test["rebalanced"] = True
        return assignments


class DeltaCheckEngine:
    def __init__(self) -> None:
        self._thresholds: dict[str, dict[str, float]] = {}
        self._patient_history: dict[str, list[dict[str, Any]]] = {}

    def set_delta_threshold(
        self, test_code: str, absolute_change: float, percent_change: float,
    ) -> None:
        self._thresholds[test_code] = {
            "absolute_change": absolute_change,
            "percent_change": percent_change,
        }

    def get_delta_threshold(self, test_code: str) -> dict[str, float]:
        return self._thresholds.get(test_code, {"absolute_change": 0.0, "percent_change": 0.0})

    def record_result(self, patient_id: str, test_code: str, value: float) -> None:
        key = f"{patient_id}:{test_code}"
        if key not in self._patient_history:
            self._patient_history[key] = []
        self._patient_history[key].append(
            {
                "value": value,
                "timestamp": time.time(),
            },
        )

    def evaluate_delta(
        self,
        patient_id: str,
        test_code: str,
        current_value: float,
        previous_value: float | None = None,
    ) -> dict[str, Any]:
        thresholds = self.get_delta_threshold(test_code)
        if previous_value is None:
            key = f"{patient_id}:{test_code}"
            history = self._patient_history.get(key, [])
            if len(history) >= 1:
                previous_value = history[-1]["value"]
            else:
                return {
                    "patient_id": patient_id,
                    "test_code": test_code,
                    "delta": 0.0,
                    "delta_percent": 0.0,
                    "significant": False,
                    "message": "No previous result for comparison",
                }
        absolute_delta = current_value - previous_value
        percent_delta = (absolute_delta / previous_value * 100) if previous_value != 0 else 0.0
        abs_threshold = thresholds.get("absolute_change", float("inf"))
        pct_threshold = thresholds.get("percent_change", float("inf"))
        significant = abs(absolute_delta) > abs_threshold or abs(percent_delta) > pct_threshold
        return {
            "patient_id": patient_id,
            "test_code": test_code,
            "previous_value": previous_value,
            "current_value": current_value,
            "delta": round(absolute_delta, 4),
            "delta_percent": round(percent_delta, 2),
            "significant": significant,
            "message": "Significant change detected"
            if significant
            else "Within expected variation",
        }

    def flag_significant_delta(self, delta: dict[str, Any]) -> dict[str, Any]:
        if delta.get("significant"):
            return {
                "flagged": True,
                "test_code": delta.get("test_code"),
                "patient_id": delta.get("patient_id"),
                "delta": delta.get("delta"),
                "delta_percent": delta.get("delta_percent"),
                "severity": "critical" if abs(delta.get("delta_percent", 0)) > 50 else "warning",
                "requires_review": True,
            }
        return {"flagged": False, "message": "No significant delta"}
