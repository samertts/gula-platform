from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.ai_fabric.laboratory_intelligence")


@dataclass
class DeltaCheckResult:
    patient_id: str = ""
    test_name: str = ""
    current_value: float = 0.0
    previous_value: float = 0.0
    delta_pct: float = 0.0
    delta_abs: float = 0.0
    significant: bool = False
    flag: str = "normal"


@dataclass
class CriticalResult:
    test_name: str = ""
    value: float = 0.0
    unit: str = ""
    critical_low: float | None = None
    critical_high: float | None = None
    direction: str = ""
    severity: str = "panic"


@dataclass
class QCMetric:
    name: str = ""
    mean: float = 0.0
    sd: float = 0.0
    cv_pct: float = 0.0
    in_control: bool = True
    rules_violated: list[str] = field(default_factory=list)


@dataclass
class WorkloadPrediction:
    period: str = ""
    predicted_orders: int = 0
    predicted_tat_minutes: float = 0.0
    peak_hours: list[int] = field(default_factory=list)
    staff_needed: int = 0
    confidence: float = 0.0


class DeltaChecker:
    def __init__(self, significant_pct: float = 20.0, significant_abs: float = 0.0) -> None:
        self._significant_pct = significant_pct
        self._significant_abs = significant_abs

    def check(
        self,
        patient_id: str,
        test_name: str,
        current_value: float,
        previous_value: float | None = None,
    ) -> DeltaCheckResult:
        result = DeltaCheckResult(
            patient_id=patient_id,
            test_name=test_name,
            current_value=current_value,
        )
        if previous_value is not None:
            result.previous_value = previous_value
            result.delta_abs = abs(current_value - previous_value)
            if previous_value != 0:
                result.delta_pct = (result.delta_abs / abs(previous_value)) * 100
            else:
                result.delta_pct = result.delta_abs * 100

            is_significant = False
            if (self._significant_abs > 0 and result.delta_abs >= self._significant_abs) or (self._significant_pct > 0 and result.delta_pct >= self._significant_pct):
                is_significant = True

            result.significant = is_significant
            if is_significant:
                direction = "increase" if current_value > previous_value else "decrease"
                result.flag = f"significant_{direction}"
        return result

    def batch_check(
        self,
        patient_results: list[dict[str, Any]],
    ) -> list[DeltaCheckResult]:
        results: list[DeltaCheckResult] = []
        grouped: dict[str, list[dict]] = {}
        for r in patient_results:
            test = r.get("test_name", "")
            grouped.setdefault(test, []).append(r)

        for test_name, entries in grouped.items():
            sorted_entries = sorted(entries, key=lambda e: e.get("timestamp", 0))
            for i in range(1, len(sorted_entries)):
                prev = sorted_entries[i - 1]
                curr = sorted_entries[i]
                result = self.check(
                    patient_id=curr.get("patient_id", ""),
                    test_name=test_name,
                    current_value=float(curr.get("value", 0)),
                    previous_value=float(prev.get("value", 0)),
                )
                results.append(result)
        return results


class CriticalResultDetector:
    def __init__(self) -> None:
        self._thresholds: dict[str, dict[str, float]] = {}

    def set_threshold(self, test_name: str, critical_low: float, critical_high: float) -> None:
        self._thresholds[test_name] = {
            "critical_low": critical_low,
            "critical_high": critical_high,
        }

    def set_thresholds(self, thresholds: dict[str, dict[str, float]]) -> None:
        self._thresholds.update(thresholds)

    def detect(self, test_name: str, value: float, unit: str = "") -> CriticalResult | None:
        thresholds = self._thresholds.get(test_name)
        if not thresholds:
            return None
        if value <= thresholds["critical_low"]:
            return CriticalResult(
                test_name=test_name,
                value=value,
                unit=unit,
                critical_low=thresholds["critical_low"],
                critical_high=thresholds["critical_high"],
                direction="low",
                severity="panic",
            )
        if value >= thresholds["critical_high"]:
            return CriticalResult(
                test_name=test_name,
                value=value,
                unit=unit,
                critical_low=thresholds["critical_low"],
                critical_high=thresholds["critical_high"],
                direction="high",
                severity="panic",
            )
        return None

    def batch_detect(self, results: list[dict[str, Any]]) -> list[CriticalResult]:
        criticals: list[CriticalResult] = []
        for r in results:
            result = self.detect(
                test_name=r.get("test_name", ""),
                value=float(r.get("value", 0)),
                unit=r.get("unit", ""),
            )
            if result:
                criticals.append(result)
        return criticals


class QCAnalyzer:
    def __init__(self) -> None:
        self._westgard_rules: list[str] = ["1_2s", "1_3s", "2_2s", "r_4s", "4_1s", "10x"]

    def analyze(self, control_values: list[float], mean: float, sd: float) -> QCMetric:
        if not control_values:
            return QCMetric(name="QC Analysis", in_control=True)

        cv = (sd / mean * 100) if mean != 0 else 0.0
        metric = QCMetric(name="QC Analysis", mean=mean, sd=sd, cv_pct=round(cv, 2))

        for rule in self._westgard_rules:
            violations = self._check_rule(rule, control_values, mean, sd)
            metric.rules_violated.extend(violations)

        metric.in_control = len(metric.rules_violated) == 0
        return metric

    def _check_rule(self, rule: str, values: list[float], mean: float, sd: float) -> list[str]:
        violations: list[str] = []
        n = len(values)
        if n == 0:
            return violations

        if rule == "1_3s":
            for v in values:
                if abs(v - mean) > 3 * sd:
                    violations.append(f"1-3s: value {v:.2f} exceeds 3 SD")

        elif rule == "1_2s":
            for v in values:
                if abs(v - mean) > 2 * sd:
                    violations.append(f"1-2s: value {v:.2f} exceeds 2 SD (warning)")

        elif rule == "2_2s":
            count = sum(1 for v in values if abs(v - mean) > 2 * sd)
            if count >= 2:
                violations.append(f"2-2s: {count} values exceed 2 SD on same side")

        elif rule == "r_4s" and n >= 2:
            diffs = [abs(values[i] - values[i - 1]) for i in range(1, n)]
            max_diff = max(diffs) if diffs else 0
            if max_diff > 4 * sd:
                violations.append(f"R-4s: range exceeds 4 SD (diff={max_diff:.2f})")

        elif rule == "4_1s" and n >= 4:
            for i in range(n - 3):
                window = values[i:i + 4]
                same_side = all((v - mean) > sd for v in window) or all((mean - v) > sd for v in window)
                if same_side:
                    violations.append("4-1s: 4 consecutive values exceed 1 SD on same side")

        elif rule == "10x" and n >= 10:
            for i in range(n - 9):
                window = values[i:i + 10]
                if all(v >= mean for v in window) or all(v <= mean for v in window):
                    violations.append("10x: 10 consecutive values on same side of mean")
                    break

        return violations

    def calculate_statistics(self, values: list[float]) -> dict[str, float]:
        if len(values) < 2:
            return {"mean": 0.0, "sd": 0.0, "cv_pct": 0.0}
        m = statistics.mean(values)
        s = statistics.stdev(values)
        cv = (s / m * 100) if m != 0 else 0.0
        return {"mean": round(m, 4), "sd": round(s, 4), "cv_pct": round(cv, 2)}


class WorkloadPredictor:
    def __init__(self, history_window_days: int = 90) -> None:
        self._history_window = history_window_days
        self._historical_data: list[dict] = []

    def load_history(self, data: list[dict[str, Any]]) -> None:
        self._historical_data = data

    def predict_daily(self, date: str | None = None) -> WorkloadPrediction:
        avg_orders = 0
        if self._historical_data:
            values = [d.get("order_count", 0) for d in self._historical_data if d.get("order_count")]
            avg_orders = int(statistics.mean(values)) if values else 0
        return WorkloadPrediction(
            period=date or "today",
            predicted_orders=avg_orders,
            predicted_tat_minutes=120.0,
            peak_hours=[9, 10, 11, 14, 15, 16],
            staff_needed=max(1, avg_orders // 50),
            confidence=0.7,
        )

    def predict_tat(
        self,
        order_type: str,
        priority: str = "routine",
        current_backlog: int = 0,
    ) -> dict[str, Any]:
        base_tat = 60.0 if priority == "stat" else 240.0
        backlog_factor = 1 + (current_backlog * 0.01)
        return {
            "order_type": order_type,
            "priority": priority,
            "predicted_tat_minutes": round(base_tat * backlog_factor, 1),
            "confidence": 0.75,
        }

    def peak_hour_analysis(self) -> dict[str, Any]:
        return {
            "peak_hours": [9, 10, 11],
            "peak_load_pct": 35.0,
            "off_peak_hours": [22, 23, 0, 1, 2, 3, 4, 5],
            "recommendation": "Increase staffing during 9-11 AM peak",
        }
