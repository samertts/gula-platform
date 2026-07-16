from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.national.intelligence.public_health")

_DISEASE_BASELINES: dict[str, dict[str, float]] = {
    "influenza": {"expected_per_100k": 500.0, "baseline_std": 100.0, "r0": 1.5},
    "covid19": {"expected_per_100k": 200.0, "baseline_std": 80.0, "r0": 3.0},
    "dengue": {"expected_per_100k": 50.0, "baseline_std": 20.0, "r0": 1.8},
    "measles": {"expected_per_100k": 10.0, "baseline_std": 5.0, "r0": 15.0},
    "cholera": {"expected_per_100k": 5.0, "baseline_std": 3.0, "r0": 2.5},
    "malaria": {"expected_per_100k": 100.0, "baseline_std": 30.0, "r0": 1.6},
    "tuberculosis": {"expected_per_100k": 50.0, "baseline_std": 15.0, "r0": 1.3},
    "meningitis": {"expected_per_100k": 8.0, "baseline_std": 3.0, "r0": 1.2},
}


@dataclass
class SurveillanceReport:
    disease_code: str = ""
    region: str = ""
    period_days: int = 30
    reported_cases: int = 0
    expected_cases: float = 0.0
    anomaly_score: float = 0.0
    status: str = "normal"
    trend: str = "stable"
    recommendations: list[str] = field(default_factory=list)


@dataclass
class OutbreakAlert:
    outbreak_id: str = ""
    disease_code: str = ""
    region: str = ""
    cases: int = 0
    expected_baseline: float = 0.0
    r0_estimate: float = 0.0
    severity: str = "low"
    affected_population: int = 0
    start_date: float = 0.0
    recommendations: list[str] = field(default_factory=list)


@dataclass
class CoverageData:
    vaccine: str = ""
    region: str = ""
    coverage_percent: float = 0.0
    target_percent: float = 95.0
    population: int = 0
    vaccinated: int = 0


class DiseaseSurveillanceEngine:
    def __init__(self) -> None:
        self._case_reports: dict[str, list[dict[str, Any]]] = {}
        self._anomaly_threshold: float = 2.0

    def report_cases(self, disease_code: str, region: str, cases: int, population: int) -> None:
        key = f"{disease_code}:{region}"
        if key not in self._case_reports:
            self._case_reports[key] = []
        self._case_reports[key].append({
            "cases": cases,
            "population": population,
            "timestamp": time.time(),
        })

    def monitor_disease(self, disease_code: str, region: str, period: int = 30) -> SurveillanceReport:
        key = f"{disease_code}:{region}"
        reports = self._case_reports.get(key, [])
        cutoff = time.time() - period * 86400
        filtered = [r for r in reports if r["timestamp"] >= cutoff]
        total_cases = sum(r["cases"] for r in filtered)
        baseline = _DISEASE_BASELINES.get(disease_code, {"expected_per_100k": 10.0})
        latest_pop = filtered[-1]["population"] if filtered else 100000
        expected = baseline["expected_per_100k"] * (latest_pop / 100000) * (period / 30)
        anomaly = self.detect_anomaly(total_cases, expected)
        trend = "increasing"
        if len(filtered) >= 2:
            half = len(filtered) // 2
            recent = sum(r["cases"] for r in filtered[half:])
            early = sum(r["cases"] for r in filtered[:half])
            trend = "increasing" if recent > early * 1.2 else "decreasing" if recent < early * 0.8 else "stable"
        recommendations: list[str] = []
        if anomaly["is_anomaly"]:
            recommendations.append("Increase surveillance frequency")
            recommendations.append("Alert local health authorities")
            if anomaly["severity"] in ("high", "critical"):
                recommendations.append("Deploy rapid response team")
                recommendations.append("Activate emergency operations center")
        if trend == "increasing":
            recommendations.append("Monitor closely for accelerating trend")
        return SurveillanceReport(
            disease_code=disease_code,
            region=region,
            period_days=period,
            reported_cases=total_cases,
            expected_cases=round(expected, 1),
            anomaly_score=anomaly["score"],
            status=anomaly["severity"] if anomaly["is_anomaly"] else "normal",
            trend=trend,
            recommendations=recommendations,
        )

    def detect_anomaly(self, reported_cases: int, expected_baseline: float) -> dict[str, Any]:
        if expected_baseline <= 0:
            return {"is_anomaly": False, "score": 0.0, "severity": "none"}
        ratio = reported_cases / expected_baseline
        score = ratio - 1.0
        is_anomaly = ratio > self._anomaly_threshold
        severity: str = "none"
        if is_anomaly:
            if ratio > 5.0:
                severity = "critical"
            elif ratio > 3.0:
                severity = "high"
            else:
                severity = "medium"
        return {
            "is_anomaly": is_anomaly,
            "score": round(score, 2),
            "severity": severity,
            "ratio": round(ratio, 2),
        }

    def generate_surveillance_report(self, disease: str, region: str) -> dict[str, Any]:
        report = self.monitor_disease(disease, region, 30)
        return {
            "disease": report.disease_code,
            "region": report.region,
            "period_days": report.period_days,
            "reported_cases": report.reported_cases,
            "expected_cases": report.expected_cases,
            "anomaly_score": report.anomaly_score,
            "status": report.status,
            "trend": report.trend,
            "recommendations": report.recommendations,
            "generated_at": time.time(),
        }


class OutbreakDetectionEngine:
    def __init__(self) -> None:
        self._outbreak_alerts: dict[str, OutbreakAlert] = {}
        self._spatial_data: dict[str, list[dict[str, Any]]] = {}

    def record_spatial_data(self, region: str, cases: list[dict[str, Any]]) -> None:
        self._spatial_data[region] = cases

    def analyze_clusters(
        self,
        cases: list[dict[str, Any]],
        spatial_data: list[dict[str, Any]] | None = None,
        temporal_data: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        clusters: list[dict[str, Any]] = []
        if len(cases) < 2:
            return clusters
        spatial = spatial_data or cases
        coordinates = [(c.get("lat", 0), c.get("lon", 0)) for c in spatial]
        for i in range(len(coordinates)):
            cluster_members = [i]
            for j in range(len(coordinates)):
                if i != j:
                    dist = math.sqrt(
                        (coordinates[i][0] - coordinates[j][0]) ** 2 +
                        (coordinates[i][1] - coordinates[j][1]) ** 2
                    )
                    if dist < 0.05:
                        cluster_members.append(j)
            if len(cluster_members) >= 3:
                cluster_id = f"cluster_{len(clusters) + 1}"
                clusters.append({
                    "cluster_id": cluster_id,
                    "size": len(cluster_members),
                    "centroid_lat": sum(coordinates[m][0] for m in cluster_members) / len(cluster_members),
                    "centroid_lon": sum(coordinates[m][1] for m in cluster_members) / len(cluster_members),
                    "member_indices": cluster_members,
                })
        return clusters

    def detect_outbreak(
        self,
        cases: list[dict[str, Any]],
        baseline: float = 0.0,
        threshold: float = 2.0,
    ) -> dict[str, Any]:
        n_cases = len(cases)
        if n_cases == 0:
            return {"outbreak_detected": False, "cases": 0, "baseline": baseline, "ratio": 0.0}
        ratio = n_cases / baseline if baseline > 0 else float("inf")
        detected = ratio >= threshold
        severity: str = "low"
        if detected:
            if ratio > 5.0:
                severity = "critical"
            elif ratio > 3.0:
                severity = "high"
            else:
                severity = "medium"
        return {
            "outbreak_detected": detected,
            "cases": n_cases,
            "baseline": baseline,
            "ratio": round(ratio, 2),
            "severity": severity,
            "recommendations": ["Activate outbreak response protocol"] if detected else [],
        }

    def calculate_r0(self, cases: list[dict[str, Any]], generation_time: float = 5.0) -> float:
        if len(cases) < 2:
            return 1.0
        times = [c.get("timestamp", c.get("date", 0)) for c in cases]
        sorted_times = sorted(times)
        if len(sorted_times) < 2:
            return 1.0
        serial_intervals = [
            (sorted_times[i] - sorted_times[i - 1]) / 86400
            for i in range(1, len(sorted_times))
        ]
        avg_interval = sum(serial_intervals) / len(serial_intervals) if serial_intervals else generation_time
        growth_rate = math.log(len(cases)) / avg_interval if avg_interval > 0 else 0.1
        r0 = round(1 + growth_rate * generation_time, 2)
        return max(0.5, min(r0, 20.0))

    def assess_outbreak_severity(self, outbreak: dict[str, Any]) -> dict[str, Any]:
        cases = outbreak.get("cases", 0)
        r0 = outbreak.get("r0_estimate", 1.0)
        severity_score = cases * 0.01 + r0 * 0.5
        if severity_score > 5.0:
            level = "critical"
        elif severity_score > 2.0:
            level = "high"
        elif severity_score > 0.5:
            level = "medium"
        else:
            level = "low"
        return {
            "severity_level": level,
            "severity_score": round(severity_score, 2),
            "cases": cases,
            "r0": r0,
            "requires_national_response": level in ("high", "critical"),
        }


class VaccinationCoverageEngine:
    def __init__(self) -> None:
        self._coverage_records: dict[str, list[CoverageData]] = {}

    def record_coverage(self, vaccine: str, region: str, vaccinated: int, population: int) -> None:
        key = f"{vaccine}:{region}"
        if key not in self._coverage_records:
            self._coverage_records[key] = []
        coverage_pct = (vaccinated / population * 100) if population > 0 else 0.0
        data = CoverageData(
            vaccine=vaccine,
            region=region,
            coverage_percent=round(coverage_pct, 1),
            population=population,
            vaccinated=vaccinated,
        )
        self._coverage_records[key].append(data)

    def calculate_coverage(self, vaccine: str, region: str, demographic: dict[str, Any] | None = None) -> CoverageData:
        key = f"{vaccine}:{region}"
        records = self._coverage_records.get(key, [])
        if not records:
            return CoverageData(
                vaccine=vaccine,
                region=region,
                coverage_percent=0.0,
                population=0,
                vaccinated=0,
            )
        latest = records[-1]
        if demographic:
            adjustment = demographic.get("access_factor", 1.0)
            adjusted_coverage = min(100.0, latest.coverage_percent * adjustment)
            return CoverageData(
                vaccine=vaccine,
                region=region,
                coverage_percent=round(adjusted_coverage, 1),
                target_percent=95.0,
                population=latest.population,
                vaccinated=int(latest.vaccinated * adjustment),
            )
        return latest

    def get_coverage_trends(self, vaccine: str, years: int = 5) -> list[dict[str, Any]]:
        trends: list[dict[str, Any]] = []
        for key, records in self._coverage_records.items():
            if not key.startswith(f"{vaccine}:"):
                continue
            for rec in records:
                trends.append({
                    "vaccine": rec.vaccine,
                    "region": rec.region,
                    "coverage_percent": rec.coverage_percent,
                    "target_percent": rec.target_percent,
                    "gap": round(max(0, rec.target_percent - rec.coverage_percent), 1),
                })
        return trends

    def identify_coverage_gaps(self, coverage_data: list[CoverageData]) -> list[dict[str, Any]]:
        gaps: list[dict[str, Any]] = []
        for data in coverage_data:
            gap = max(0, data.target_percent - data.coverage_percent)
            if gap > 0:
                gaps.append({
                    "vaccine": data.vaccine,
                    "region": data.region,
                    "current_coverage": data.coverage_percent,
                    "target": data.target_percent,
                    "gap": round(gap, 1),
                    "severity": "critical" if gap > 20 else "high" if gap > 10 else "medium",
                    "unvaccinated_population": int(data.population * gap / 100),
                })
        return sorted(gaps, key=lambda g: -g["gap"])


class PopulationRiskEngine:
    def __init__(self) -> None:
        self._risk_data: dict[str, dict[str, Any]] = {}

    def load_risk_data(self, region: str, data: dict[str, Any]) -> None:
        self._risk_data[region] = data

    def assess_population_risk(self, region: str, risk_factors: dict[str, Any] | None = None) -> dict[str, Any]:
        data = self._risk_data.get(region, {})
        factors = risk_factors or data.get("factors", {})
        scores: dict[str, float] = {}
        for factor, weight in factors.items():
            prevalence = data.get("prevalence", {}).get(factor, 0.5)
            scores[factor] = round(prevalence * weight, 3)
        overall = sum(scores.values()) / max(len(scores), 1) if scores else 0.0
        return {
            "region": region,
            "overall_risk_score": round(overall, 3),
            "risk_category": "high" if overall > 0.7 else "moderate" if overall > 0.4 else "low",
            "factor_scores": scores,
            "population": data.get("population", 0),
            "vulnerable_population": int(data.get("population", 0) * overall) if overall else 0,
        }

    def get_risk_map(self, risk_type: str = "overall") -> dict[str, Any]:
        regions: dict[str, Any] = {}
        for region, _data in self._risk_data.items():
            risk = self.assess_population_risk(region)
            regions[region] = {
                "risk_score": risk["overall_risk_score"],
                "risk_category": risk["risk_category"],
                "population": risk["population"],
            }
        return {
            "risk_type": risk_type,
            "regions": regions,
            "highest_risk_region": max(regions, key=lambda r: regions[r]["risk_score"]) if regions else None,
        }

    def identify_vulnerable_populations(self, risk_data: dict[str, Any]) -> list[dict[str, Any]]:
        factor_scores = risk_data.get("factor_scores", {})
        vulnerable: list[dict[str, Any]] = []
        for factor, score in sorted(factor_scores.items(), key=lambda x: -x[1]):
            if score > 0.5:
                vulnerable.append({
                    "factor": factor,
                    "risk_score": score,
                    "estimated_population": int(risk_data.get("population", 0) * score),
                    "recommendation": f"Targeted intervention for {factor}",
                })
        return vulnerable


class MortalityAnalyzer:
    def __init__(self) -> None:
        self._mortality_data: dict[str, list[dict[str, Any]]] = {}

    def record_mortality(self, region: str, deaths: int, population: int, cause: str = "all_cause") -> None:
        key = f"{region}:{cause}"
        if key not in self._mortality_data:
            self._mortality_data[key] = []
        self._mortality_data[key].append({
            "deaths": deaths,
            "population": population,
            "timestamp": time.time(),
        })

    def analyze_mortality(self, region: str, period: int = 365, causes: list[str] | None = None) -> dict[str, Any]:
        target_causes = causes or ["all_cause"]
        analysis: dict[str, Any] = {
            "region": region,
            "period_days": period,
            "causes": {},
        }
        for cause in target_causes:
            key = f"{region}:{cause}"
            records = self._mortality_data.get(key, [])
            cutoff = time.time() - period * 86400
            filtered = [r for r in records if r["timestamp"] >= cutoff]
            if not filtered:
                continue
            total_deaths = sum(r["deaths"] for r in filtered)
            latest_pop = filtered[-1]["population"]
            rate = self.calculate_mortality_rate(total_deaths, latest_pop)
            analysis["causes"][cause] = {
                "deaths": total_deaths,
                "population": latest_pop,
                "mortality_rate_per_100k": rate,
                "data_points": len(filtered),
            }
        return analysis

    def calculate_mortality_rate(self, deaths: int, population: int) -> float:
        if population <= 0:
            return 0.0
        return round((deaths / population) * 100000, 2)

    def get_mortality_trends(self, years: int = 10, cause: str = "all_cause") -> list[dict[str, Any]]:
        trends: list[dict[str, Any]] = []
        for key, records in self._mortality_data.items():
            if not key.endswith(f":{cause}"):
                continue
            region = key.split(":")[0]
            for rec in records:
                rate = self.calculate_mortality_rate(rec["deaths"], rec["population"])
                trends.append({
                    "region": region,
                    "cause": cause,
                    "deaths": rec["deaths"],
                    "population": rec["population"],
                    "mortality_rate_per_100k": rate,
                    "timestamp": rec["timestamp"],
                })
        return sorted(trends, key=lambda t: t["timestamp"])


class MaternalHealthEngine:
    def __init__(self) -> None:
        self._maternal_data: dict[str, list[dict[str, Any]]] = {}

    def record_maternal_data(self, region: str, deaths: int, live_births: int, anc_visits: int, expected_pregnancies: int) -> None:
        if region not in self._maternal_data:
            self._maternal_data[region] = []
        self._maternal_data[region].append({
            "deaths": deaths,
            "live_births": live_births,
            "anc_visits": anc_visits,
            "expected_pregnancies": expected_pregnancies,
            "timestamp": time.time(),
        })

    def track_maternal_indicators(self, region: str, period: int = 365) -> dict[str, Any]:
        records = self._maternal_data.get(region, [])
        cutoff = time.time() - period * 86400
        filtered = [r for r in records if r["timestamp"] >= cutoff]
        if not filtered:
            return {
                "region": region,
                "status": "insufficient_data",
                "message": "No maternal health data available",
            }
        total_deaths = sum(r["deaths"] for r in filtered)
        total_births = sum(r["live_births"] for r in filtered)
        sum(r["anc_visits"] for r in filtered)
        sum(r["expected_pregnancies"] for r in filtered)
        mmr = self.analyze_maternal_mortality(total_deaths, total_births)
        anc_coverage = self.get_antenatal_coverage(region)
        return {
            "region": region,
            "period_days": period,
            "maternal_mortality_ratio": mmr,
            "live_births": total_births,
            "maternal_deaths": total_deaths,
            "anc_coverage_percent": anc_coverage,
            "skilled_birth_attendance_percent": round(min(100, anc_coverage * 1.1), 1),
        }

    def analyze_maternal_mortality(self, deaths: int, births: int) -> float:
        if births <= 0:
            return 0.0
        return round((deaths / births) * 100000, 2)

    def get_antenatal_coverage(self, region: str) -> float:
        records = self._maternal_data.get(region, [])
        if not records:
            return 0.0
        latest = records[-1]
        if latest["expected_pregnancies"] <= 0:
            return 0.0
        return round(min(100, (latest["anc_visits"] / latest["expected_pregnancies"]) * 100), 1)


class ChildHealthEngine:
    def __init__(self) -> None:
        self._child_data: dict[str, list[dict[str, Any]]] = {}

    def record_child_data(self, region: str, deaths_under_5: int, live_births: int, immunized: int, target_population: int) -> None:
        if region not in self._child_data:
            self._child_data[region] = []
        self._child_data[region].append({
            "deaths_under_5": deaths_under_5,
            "live_births": live_births,
            "immunized": immunized,
            "target_population": target_population,
            "timestamp": time.time(),
        })

    def track_child_indicators(self, region: str, period: int = 365) -> dict[str, Any]:
        records = self._child_data.get(region, [])
        cutoff = time.time() - period * 86400
        filtered = [r for r in records if r["timestamp"] >= cutoff]
        if not filtered:
            return {
                "region": region,
                "status": "insufficient_data",
                "message": "No child health data available",
            }
        total_deaths = sum(r["deaths_under_5"] for r in filtered)
        total_births = sum(r["live_births"] for r in filtered)
        mortality_rate = self.analyze_child_mortality(total_deaths, total_births)
        immunization_coverage = self.calculate_immunization_coverage(region, "all")
        return {
            "region": region,
            "period_days": period,
            "under_5_mortality_rate_per_1000": mortality_rate,
            "under_5_deaths": total_deaths,
            "live_births": total_births,
            "immunization_coverage_percent": immunization_coverage,
        }

    def analyze_child_mortality(self, deaths: int, live_births: int) -> float:
        if live_births <= 0:
            return 0.0
        return round((deaths / live_births) * 1000, 2)

    def calculate_immunization_coverage(self, region: str, vaccine: str) -> float:
        records = self._child_data.get(region, [])
        if not records:
            return 0.0
        latest = records[-1]
        if latest["target_population"] <= 0:
            return 0.0
        return round((latest["immunized"] / latest["target_population"]) * 100, 1)
