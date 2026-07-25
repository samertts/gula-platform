from __future__ import annotations

import json
import logging
import math
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

from security.modules.threat_detection.models import SecurityMetric, ThreatEvent

logger = logging.getLogger(__name__)

SECURITY_KPI_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "auth_failure_rate": {
        "name": "Authentication Failure Rate",
        "description": "Rate of failed authentication attempts per hour",
        "unit": "failures/hour",
        "higher_is_better": False,
        "threshold_warning": 10.0,
        "threshold_critical": 50.0,
    },
    "permission_denial_rate": {
        "name": "Permission Denial Rate",
        "description": "Rate of authorization denied events per hour",
        "unit": "denials/hour",
        "higher_is_better": False,
        "threshold_warning": 5.0,
        "threshold_critical": 20.0,
    },
    "encryption_coverage": {
        "name": "Encryption Coverage",
        "description": "Percentage of data encrypted at rest and in transit",
        "unit": "percent",
        "higher_is_better": True,
        "threshold_warning": 85.0,
        "threshold_critical": 70.0,
    },
    "scan_coverage": {
        "name": "Security Scan Coverage",
        "description": "Percentage of systems covered by vulnerability scanning",
        "unit": "percent",
        "higher_is_better": True,
        "threshold_warning": 80.0,
        "threshold_critical": 60.0,
    },
    "vulnerability_density": {
        "name": "Vulnerability Density",
        "description": "Number of open vulnerabilities per 100 dependencies",
        "unit": "vulns/100",
        "higher_is_better": False,
        "threshold_warning": 5.0,
        "threshold_critical": 15.0,
    },
    "mfa_adoption_rate": {
        "name": "MFA Adoption Rate",
        "description": "Percentage of users with MFA enabled",
        "unit": "percent",
        "higher_is_better": True,
        "threshold_warning": 70.0,
        "threshold_critical": 50.0,
    },
    "incident_response_time": {
        "name": "Incident Response Time",
        "description": "Average time to respond to security incidents",
        "unit": "minutes",
        "higher_is_better": False,
        "threshold_warning": 60.0,
        "threshold_critical": 180.0,
    },
    "patch_latency": {
        "name": "Patch Latency",
        "description": "Average time to apply security patches",
        "unit": "days",
        "higher_is_better": False,
        "threshold_warning": 7.0,
        "threshold_critical": 30.0,
    },
    "risk_score_avg": {
        "name": "Average Risk Score",
        "description": "Mean risk score across all monitored entities",
        "unit": "score",
        "higher_is_better": False,
        "threshold_warning": 30.0,
        "threshold_critical": 60.0,
    },
    "audit_log_coverage": {
        "name": "Audit Log Coverage",
        "description": "Percentage of required events being logged",
        "unit": "percent",
        "higher_is_better": True,
        "threshold_warning": 90.0,
        "threshold_critical": 80.0,
    },
}


class KpiResult(BaseModel):
    metric_name: str
    value: float
    unit: str
    status: str = "healthy"
    threshold_warning: float = 0.0
    threshold_critical: float = 0.0
    trend: str = "stable"


class SecurityHealthScore(BaseModel):
    overall_score: float = 0.0
    kpis: Dict[str, KpiResult] = Field(default_factory=dict)
    assessment: str = ""
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class MetricsTimeSeries(BaseModel):
    metric_name: str
    data_points: List[Dict[str, Any]] = Field(default_factory=list)
    unit: str = "count"


class SecurityMetricsCollector:
    def __init__(self):
        self._metrics: Dict[str, List[SecurityMetric]] = defaultdict(list)
        self._event_sources: Dict[str, Callable] = {}
        self._time_series: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._metric_collectors: Dict[str, Callable] = {}

    def record_metric(self, metric: SecurityMetric) -> None:
        self._metrics[metric.metric_name].append(metric)
        self._time_series[metric.metric_name].append({
            "timestamp": metric.timestamp.isoformat() if metric.timestamp else datetime.now(timezone.utc).isoformat(),
            "value": metric.value,
            "labels": metric.labels,
        })

        if len(self._time_series[metric.metric_name]) > 1000:
            self._time_series[metric.metric_name] = self._time_series[metric.metric_name][-1000:]

    def register_metric_source(self, metric_name: str, collector: Callable) -> None:
        self._metric_collectors[metric_name] = collector

    def collect_all_metrics(self) -> Dict[str, float]:
        results: Dict[str, float] = {}
        for name, collector in self._metric_collectors.items():
            try:
                value = collector()
                results[name] = value
                self.record_metric(SecurityMetric(
                    metric_name=name,
                    value=value,
                    unit=SECURITY_KPI_DEFINITIONS.get(name, {}).get("unit", "count"),
                    source_module="collector",
                ))
            except Exception as e:
                logger.error(f"Metric collection failed for '{name}': {e}")
        return results

    def get_metric(self, metric_name: str, aggregation: str = "avg") -> Optional[float]:
        metrics = self._metrics.get(metric_name, [])
        if not metrics:
            return None

        values = [m.value for m in metrics]
        if aggregation == "avg":
            return sum(values) / len(values)
        elif aggregation == "sum":
            return sum(values)
        elif aggregation == "max":
            return max(values)
        elif aggregation == "min":
            return min(values)
        elif aggregation == "latest":
            return values[-1]
        return values[-1]

    def get_time_series(self, metric_name: str, hours: int = 24) -> MetricsTimeSeries:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        points = self._time_series.get(metric_name, [])
        filtered = [p for p in points if p.get("timestamp", "") >= cutoff.isoformat()]
        definition = SECURITY_KPI_DEFINITIONS.get(metric_name, {})

        return MetricsTimeSeries(
            metric_name=metric_name,
            data_points=filtered,
            unit=definition.get("unit", "count"),
        )

    def calculate_kpis(self, event_data: Optional[Dict[str, Any]] = None) -> Dict[str, KpiResult]:
        kpis: Dict[str, KpiResult] = {}
        data = event_data or {}

        kpi_calculators = {
            "auth_failure_rate": lambda: data.get("auth_failures", 0) / max(data.get("total_hours", 1), 1),
            "permission_denial_rate": lambda: data.get("permission_denials", 0) / max(data.get("total_hours", 1), 1),
            "encryption_coverage": lambda: data.get("encrypted_assets", 0) / max(data.get("total_assets", 1), 1) * 100,
            "scan_coverage": lambda: data.get("scanned_systems", 0) / max(data.get("total_systems", 1), 1) * 100,
            "vulnerability_density": lambda: data.get("vulnerabilities", 0) / max(data.get("dependencies", 1) / 100, 1),
            "mfa_adoption_rate": lambda: data.get("mfa_users", 0) / max(data.get("total_users", 1), 1) * 100,
            "incident_response_time": lambda: data.get("incident_response_mins", 0),
            "patch_latency": lambda: data.get("patch_days", 0),
            "risk_score_avg": lambda: data.get("average_risk_score", 0),
            "audit_log_coverage": lambda: data.get("audit_event_count", 0) / max(data.get("required_events", 1), 1) * 100,
        }

        for name, definition in SECURITY_KPI_DEFINITIONS.items():
            calculator = kpi_calculators.get(name)
            if calculator:
                try:
                    value = calculator()
                except Exception:
                    value = 0.0
            else:
                metric_val = self.get_metric(name, "latest")
                value = metric_val if metric_val is not None else 0.0

            threshold_warning = definition["threshold_warning"]
            threshold_critical = definition["threshold_critical"]
            higher_is_better = definition["higher_is_better"]

            status = "healthy"
            if higher_is_better:
                if value < threshold_critical:
                    status = "critical"
                elif value < threshold_warning:
                    status = "warning"
            else:
                if value > threshold_critical:
                    status = "critical"
                elif value > threshold_warning:
                    status = "warning"

            trend = self._calculate_trend(name)

            kpis[name] = KpiResult(
                metric_name=name,
                value=round(value, 2),
                unit=definition["unit"],
                status=status,
                threshold_warning=threshold_warning,
                threshold_critical=threshold_critical,
                trend=trend,
            )

        return kpis

    def _calculate_trend(self, metric_name: str) -> str:
        points = self._time_series.get(metric_name, [])
        if len(points) < 5:
            return "stable"

        recent = points[-5:]
        if len(recent) >= 2:
            values = [p["value"] for p in recent]
            if values[-1] > values[0] * 1.1:
                return "increasing"
            elif values[-1] < values[0] * 0.9:
                return "decreasing"
        return "stable"

    def calculate_health_score(self, event_data: Optional[Dict[str, Any]] = None) -> SecurityHealthScore:
        kpis = self.calculate_kpis(event_data)
        if not kpis:
            return SecurityHealthScore(overall_score=0.0, kpis={}, assessment="No data available")

        kpi_weight = 100.0 / len(kpis)
        total_score = 0.0
        status_counts = {"healthy": 0, "warning": 0, "critical": 0}

        for name, kpi in kpis.items():
            higher_is_better = SECURITY_KPI_DEFINITIONS.get(name, {}).get("higher_is_better", True)
            if kpi.status == "healthy":
                kpi_score = 100.0
                status_counts["healthy"] += 1
            elif kpi.status == "warning":
                if higher_is_better:
                    kpi_score = (kpi.value / kpi.threshold_warning) * 100
                else:
                    kpi_score = (1 - (kpi.value - kpi.threshold_warning) / (kpi.threshold_critical - kpi.threshold_warning)) * 50 + 50
                kpi_score = max(30, min(70, kpi_score))
                status_counts["warning"] += 1
            else:
                if higher_is_better:
                    kpi_score = (kpi.value / kpi.threshold_critical) * 50
                else:
                    kpi_score = max(0, 50 - (kpi.value / kpi.threshold_critical) * 50)
                kpi_score = max(0, min(40, kpi_score))
                status_counts["critical"] += 1

            total_score += kpi_score * (kpi_weight / 100.0)

        overall_score = round(total_score, 1)

        if status_counts["critical"] > 0:
            assessment = "Critical security issues detected - immediate action required"
        elif status_counts["warning"] > len(kpis) / 3:
            assessment = "Security posture needs improvement - address warnings"
        elif overall_score >= 85:
            assessment = "Good security posture"
        else:
            assessment = "Adequate security posture with room for improvement"

        return SecurityHealthScore(
            overall_score=overall_score,
            kpis=kpis,
            assessment=assessment,
        )

    def to_prometheus_format(self) -> str:
        lines: List[str] = []
        for metric_name, metrics in self._metrics.items():
            if not metrics:
                continue

            last = metrics[-1]
            prom_name = f"gsf_{metric_name}".replace(" ", "_").replace("-", "_").lower()

            label_str = ",".join(f'{k}="{v}"' for k, v in last.labels.items())
            if label_str:
                lines.append(f"# HELP {prom_name} {SECURITY_KPI_DEFINITIONS.get(metric_name, {}).get('description', '')}")
                lines.append(f"# TYPE {prom_name} gauge")
                lines.append(f"{prom_name}{{{label_str}}} {last.value}")
            else:
                lines.append(f"# HELP {prom_name} {SECURITY_KPI_DEFINITIONS.get(metric_name, {}).get('description', '')}")
                lines.append(f"# TYPE {prom_name} gauge")
                lines.append(f"{prom_name} {last.value}")

        return "\n".join(lines)

    def get_dashboard_data(self) -> Dict[str, Any]:
        kpis = self.calculate_kpis()
        health = self.calculate_health_score()

        return {
            "health_score": health.model_dump(mode="json"),
            "kpis": {k: v.model_dump(mode="json") for k, v in kpis.items()},
            "time_series": {
                name: self.get_time_series(name).model_dump(mode="json")
                for name in SECURITY_KPI_DEFINITIONS
            },
            "metrics_summary": {
                name: {
                    "count": len(metrics),
                    "latest": metrics[-1].value if metrics else None,
                    "avg": sum(m.value for m in metrics) / len(metrics) if metrics else None,
                }
                for name, metrics in self._metrics.items()
            },
        }

    def trend_analysis(self, metric_name: str, hours: int = 168) -> Dict[str, Any]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        metrics = [m for m in self._metrics.get(metric_name, []) if m.timestamp >= cutoff]

        if len(metrics) < 2:
            return {"metric": metric_name, "data_points": len(metrics), "trend": "insufficient_data"}

        values = [m.value for m in metrics]
        timestamps = [m.timestamp.isoformat() for m in metrics]

        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0.0

        slope = (values[-1] - values[0]) / max(len(values), 1)

        trend_direction = "stable"
        if slope > mean * 0.1:
            trend_direction = "increasing"
        elif slope < -mean * 0.1:
            trend_direction = "decreasing"

        return {
            "metric": metric_name,
            "data_points": len(metrics),
            "mean": round(mean, 2),
            "std": round(std, 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "latest": round(values[-1], 2),
            "trend": trend_direction,
            "slope": round(slope, 4),
            "volatility": round(std / max(mean, 0.01), 2),
        }
