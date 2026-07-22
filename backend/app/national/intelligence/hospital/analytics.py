from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.national.intelligence.hospital")

_BED_TYPE_CAPACITY: dict[str, dict[str, Any]] = {
    "general_ward": {"baseline_capacity": 50, "surge_capacity": 75},
    "icu": {"baseline_capacity": 10, "surge_capacity": 15},
    "emergency": {"baseline_capacity": 20, "surge_capacity": 35},
    "maternity": {"baseline_capacity": 15, "surge_capacity": 25},
}

_SEASONAL_FACTORS: dict[str, float] = {
    "winter": 1.3,
    "spring": 1.0,
    "summer": 0.9,
    "fall": 1.1,
}

_DEPARTMENT_PEAK_HOURS: dict[str, list[int]] = {
    "emergency": [10, 11, 12, 14, 15, 16, 19, 20, 21],
    "cardiology": [8, 9, 10, 14, 15, 16],
    "pediatrics": [9, 10, 11, 15, 16, 17],
    "orthopedics": [8, 9, 10, 11, 14, 15],
}


@dataclass
class BedForecast:
    ward_id: str = ""
    date: float = 0.0
    predicted_occupancy: float = 0.0
    total_capacity: int = 0
    occupancy_rate: float = 0.0
    surge_needed: bool = False
    recommended_action: str = ""


@dataclass
class QueuePrediction:
    department_id: str = ""
    day_of_week: int = 0
    hour: int = 0
    predicted_queue_length: float = 0.0
    estimated_wait_minutes: float = 0.0
    recommended_staff: int = 0


@dataclass
class AdmissionTrend:
    date: str = ""
    admissions: int = 0
    discharge: int = 0
    net_change: int = 0
    primary_drivers: list[str] = field(default_factory=list)


class BedPredictor:
    def __init__(self) -> None:
        self._occupancy_history: dict[str, list[dict[str, Any]]] = {}

    def record_occupancy(self, ward_id: str, occupied: int, capacity: int) -> None:
        if ward_id not in self._occupancy_history:
            self._occupancy_history[ward_id] = []
        self._occupancy_history[ward_id].append({
            "occupied": occupied,
            "capacity": capacity,
            "rate": occupied / capacity if capacity > 0 else 0,
            "timestamp": time.time(),
        })

    def predict_occupancy(self, ward_id: str, days: int = 7) -> list[BedForecast]:
        forecasts: list[BedForecast] = []
        history = self._occupancy_history.get(ward_id, [])
        if not history:
            capacity = _BED_TYPE_CAPACITY.get("general_ward", {}).get("baseline_capacity", 50)
            for d in range(days):
                forecasts.append(BedForecast(
                    ward_id=ward_id,
                    date=time.time() + d * 86400,
                    predicted_occupancy=capacity * 0.7,
                    total_capacity=capacity,
                    occupancy_rate=0.7,
                ))
            return forecasts
        recent = [h["rate"] for h in history[-30:]]
        avg_rate = sum(recent) / len(recent) if recent else 0.7
        capacity = history[-1].get("capacity", 50)
        surge = _BED_TYPE_CAPACITY.get("general_ward", {}).get("surge_capacity", capacity)
        for d in range(days):
            hourly = 12 + d * 24
            time_of_day = (time.time() + hourly * 3600) % 86400
            hour_factor = 1.0 + 0.1 * math.sin(time_of_day / 3600 * math.pi / 12)
            seasonal = _SEASONAL_FACTORS.get("winter", 1.0)
            predicted = capacity * avg_rate * hour_factor * seasonal
            occupancy_rate = predicted / capacity if capacity > 0 else 0
            forecast = BedForecast(
                ward_id=ward_id,
                date=time.time() + d * 86400,
                predicted_occupancy=round(predicted, 1),
                total_capacity=capacity,
                occupancy_rate=round(min(occupancy_rate, 1.0), 3),
                surge_needed=predicted > surge,
                recommended_action="Activate surge capacity" if predicted > surge else "Monitor",
            )
            forecasts.append(forecast)
        return forecasts

    def get_bed_forecast(self, hospital_id: str, days: int = 7) -> dict[str, Any]:
        wards = [k for k in self._occupancy_history if k.startswith(hospital_id)]
        all_forecasts: list[BedForecast] = []
        for ward in wards or [f"{hospital_id}:general_ward"]:
            all_forecasts.extend(self.predict_occupancy(ward, days))
        peak_day = max(all_forecasts, key=lambda f: f.predicted_occupancy) if all_forecasts else None
        return {
            "hospital_id": hospital_id,
            "days_forecasted": days,
            "wards_analyzed": len(wards) or 1,
            "forecasts": [
                {"ward_id": f.ward_id, "date": f.date, "predicted_occupancy": f.predicted_occupancy, "occupancy_rate": f.occupancy_rate, "surge_needed": f.surge_needed}
                for f in all_forecasts
            ],
            "peak_predicted_occupancy": peak_day.predicted_occupancy if peak_day else 0,
            "surge_days": sum(1 for f in all_forecasts if f.surge_needed),
        }

    def recommend_capacity_adjustment(self, forecast: dict[str, Any]) -> list[str]:
        recommendations: list[str] = []
        surge_days = forecast.get("surge_days", 0)
        if surge_days > 3:
            recommendations.append("Activate surge capacity protocol")
            recommendations.append("Identify additional bed space in adjacent wards")
        if surge_days > 0:
            recommendations.append("Review elective admission schedule")
            recommendations.append("Coordinate with regional hospitals for load sharing")
        if not recommendations:
            recommendations.append("Current capacity adequate for forecasted demand")
        return recommendations


class QueuePredictor:
    def __init__(self) -> None:
        self._queue_history: dict[str, list[dict[str, Any]]] = {}

    def record_queue(self, department_id: str, queue_length: int, wait_minutes: float) -> None:
        if department_id not in self._queue_history:
            self._queue_history[department_id] = []
        self._queue_history[department_id].append({
            "queue_length": queue_length,
            "wait_minutes": wait_minutes,
            "timestamp": time.time(),
        })

    def predict_queue_length(self, department_id: str, day: int, hour: int) -> float:
        history = self._queue_history.get(department_id, [])
        if not history:
            return 5.0
        matching = [
            h for h in history
            if abs(h["timestamp"] % (7 * 86400) - day * 86400) < 86400
        ]
        if not matching:
            matching = history[-30:]
        if not matching:
            return 5.0
        lengths = [h["queue_length"] for h in matching]
        avg = sum(lengths) / len(lengths)
        peak_hours = _DEPARTMENT_PEAK_HOURS.get(department_id, [])
        hour_factor = 1.5 if hour in peak_hours else 1.0
        return round(avg * hour_factor, 1)

    def get_estimated_wait_time(self, department: str, triage_category: str = "routine") -> float:
        base_waits: dict[str, float] = {
            "emergency": 15.0,
            "urgent": 30.0,
            "routine": 60.0,
            "follow_up": 45.0,
        }
        triage_factor: dict[str, float] = {
            "resuscitation": 0.3,
            "emergent": 0.6,
            "urgent": 0.8,
            "semi_urgent": 1.0,
            "non_urgent": 1.5,
        }
        base = base_waits.get(department, 45.0)
        factor = triage_factor.get(triage_category, 1.0)
        return round(base * factor, 1)

    def recommend_staffing(self, queue_prediction: dict[str, Any]) -> list[dict[str, Any]]:
        expected_queue = queue_prediction.get("predicted_queue_length", 10)
        recommendations: list[dict[str, Any]] = []
        if expected_queue > 30:
            recommendations.append({
                "role": "physician",
                "additional_staff": 2,
                "reason": "High queue volume predicted",
            })
            recommendations.append({
                "role": "nurse",
                "additional_staff": 3,
                "reason": "Support high patient throughput",
            })
        elif expected_queue > 15:
            recommendations.append({
                "role": "nurse",
                "additional_staff": 1,
                "reason": "Moderate queue volume predicted",
            })
        return recommendations


class ICUCapacityPredictor:
    def __init__(self) -> None:
        self._icu_history: dict[str, list[dict[str, Any]]] = {}

    def record_icu_data(self, hospital_id: str, occupied: int, capacity: int, admissions: int, discharges: int) -> None:
        if hospital_id not in self._icu_history:
            self._icu_history[hospital_id] = []
        self._icu_history[hospital_id].append({
            "occupied": occupied,
            "capacity": capacity,
            "admissions": admissions,
            "discharges": discharges,
            "timestamp": time.time(),
        })

    def predict_icu_demand(self, hospital_id: str, season: str = "winter", trends: dict[str, Any] | None = None) -> dict[str, Any]:
        history = self._icu_history.get(hospital_id, [])
        seasonal_factor = _SEASONAL_FACTORS.get(season, 1.0)
        if not history:
            baseline = _BED_TYPE_CAPACITY.get("icu", {}).get("baseline_capacity", 10)
            predicted = baseline * seasonal_factor
            return {
                "hospital_id": hospital_id,
                "predicted_daily_demand": round(predicted, 1),
                "baseline_capacity": baseline,
                "seasonal_factor": seasonal_factor,
                "surge_capacity": _BED_TYPE_CAPACITY["icu"]["surge_capacity"],
                "overcapacity_risk": predicted > baseline * 1.2,
            }
        recent = [h["occupied"] for h in history[-60:]]
        avg_occupancy = sum(recent) / len(recent)
        trend = trends.get("icu_growth", 0.05) if trends else 0.05
        predicted = avg_occupancy * (1 + trend) * seasonal_factor
        capacity = history[-1]["capacity"]
        return {
            "hospital_id": hospital_id,
            "predicted_daily_demand": round(predicted, 1),
            "current_avg_occupancy": round(avg_occupancy, 1),
            "total_capacity": capacity,
            "seasonal_factor": seasonal_factor,
            "surge_capacity": _BED_TYPE_CAPACITY["icu"]["surge_capacity"],
            "overcapacity_risk": predicted > capacity * 1.2,
        }

    def get_icu_bed_forecast(self, days: int = 14) -> list[dict[str, Any]]:
        forecasts: list[dict[str, Any]] = []
        for hospital_id in self._icu_history:
            history = self._icu_history[hospital_id]
            if not history:
                continue
            recent = [h["occupied"] for h in history[-30:]]
            avg = sum(recent) / len(recent) if recent else 0
            capacity = history[-1]["capacity"]
            for d in range(days):
                daily_var = 0.1 * math.sin(2 * math.pi * d / 7)
                predicted = avg * (1 + daily_var)
                forecasts.append({
                    "hospital_id": hospital_id,
                    "day": d + 1,
                    "predicted_occupancy": round(predicted, 1),
                    "capacity": capacity,
                    "overcapacity": predicted > capacity,
                })
        return forecasts

    def alert_overcapacity(self, forecast: dict[str, Any]) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        if forecast.get("overcapacity_risk"):
            alerts.append({
                "type": "critical",
                "message": f"ICU overcapacity predicted for {forecast.get('hospital_id')}",
                "recommendation": "Activate surge plan and coordinate transfers",
            })
        return alerts


class EmergencyLoadPredictor:
    def __init__(self) -> None:
        self._volume_history: dict[str, list[dict[str, Any]]] = {}

    def record_volume(self, hospital_id: str, day: int, hour: int, volume: int) -> None:
        if hospital_id not in self._volume_history:
            self._volume_history[hospital_id] = []
        self._volume_history[hospital_id].append({
            "day": day,
            "hour": hour,
            "volume": volume,
            "timestamp": time.time(),
        })

    def predict_emergency_volume(self, hospital_id: str, day: int, hour: int, season: str = "winter") -> float:
        history = self._volume_history.get(hospital_id, [])
        seasonal = _SEASONAL_FACTORS.get(season, 1.0)
        if not history:
            return round(10.0 * seasonal, 1)
        matching = [h["volume"] for h in history if h["day"] == day and h["hour"] == hour]
        if matching:
            avg = sum(matching) / len(matching)
        else:
            hour_matches = [h["volume"] for h in history if h["hour"] == hour]
            avg = sum(hour_matches) / len(hour_matches) if hour_matches else 10.0
        day_factor = 1.2 if day in (4, 5) else 1.0
        return round(avg * seasonal * day_factor, 1)

    def get_peak_hours(self, hospital_id: str) -> list[dict[str, Any]]:
        history = self._volume_history.get(hospital_id, [])
        hourly_volumes: dict[int, list[int]] = {}
        for h in history:
            hour = h["hour"]
            if hour not in hourly_volumes:
                hourly_volumes[hour] = []
            hourly_volumes[hour].append(h["volume"])
        peaks: list[dict[str, Any]] = []
        for hour, volumes in hourly_volumes.items():
            avg = sum(volumes) / len(volumes)
            peaks.append({"hour": hour, "average_volume": round(avg, 1)})
        peaks.sort(key=lambda x: -x["average_volume"])
        return peaks[:5]

    def recommend_staffing(self, volume_prediction: dict[str, Any]) -> list[dict[str, Any]]:
        predicted_volume = volume_prediction.get("predicted_volume", 10)
        recommendations: list[dict[str, Any]] = []
        if predicted_volume > 30:
            recommendations.append({"role": "physician", "count": 3, "reason": "High volume"})
            recommendations.append({"role": "nurse", "count": 5, "reason": "High volume"})
            recommendations.append({"role": "triage", "count": 2, "reason": "High volume"})
        elif predicted_volume > 20:
            recommendations.append({"role": "physician", "count": 2, "reason": "Moderate volume"})
            recommendations.append({"role": "nurse", "count": 3, "reason": "Moderate volume"})
        else:
            recommendations.append({"role": "physician", "count": 1, "reason": "Normal volume"})
            recommendations.append({"role": "nurse", "count": 2, "reason": "Normal volume"})
        return recommendations


class AdmissionForecaster:
    def __init__(self) -> None:
        self._admission_history: dict[str, list[dict[str, Any]]] = {}

    def record_admission(self, hospital_id: str, date: str, count: int, discharges: int = 0) -> None:
        if hospital_id not in self._admission_history:
            self._admission_history[hospital_id] = []
        self._admission_history[hospital_id].append({
            "date": date,
            "admissions": count,
            "discharges": discharges,
            "timestamp": time.time(),
        })

    def predict_admissions(self, hospital_id: str, days: int = 30, factors: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        history = self._admission_history.get(hospital_id, [])
        season = (factors or {}).get("season", "winter")
        seasonal = _SEASONAL_FACTORS.get(season, 1.0)
        if not history:
            baseline = 20
            predictions = []
            for d in range(days):
                day_factor = 1.3 if datetime.fromtimestamp(time.time() + d * 86400).weekday() >= 5 else 1.0
                predicted = baseline * seasonal * day_factor
                predictions.append({
                    "day": d + 1,
                    "predicted_admissions": round(predicted, 1),
                    "confidence": "low",
                })
            return predictions
        recent = [h["admissions"] for h in history[-90:]]
        avg = sum(recent) / len(recent) if recent else 20
        predictions = []
        for d in range(days):
            day_of_week = datetime.fromtimestamp(time.time() + d * 86400).weekday()
            day_factor = 1.3 if day_of_week >= 5 else 1.0
            predicted = avg * seasonal * day_factor
            confidence = "high" if len(recent) > 60 else "medium"
            predictions.append({
                "day": d + 1,
                "predicted_admissions": round(predicted, 1),
                "confidence": confidence,
            })
        return predictions

    def get_admission_trends(self, months: int = 12) -> list[AdmissionTrend]:
        trends: list[AdmissionTrend] = []
        for _hospital_id, history in self._admission_history.items():
            cutoff = time.time() - months * 30 * 86400
            filtered = [h for h in history if h["timestamp"] >= cutoff]
            monthly: dict[str, dict[str, int]] = {}
            for h in filtered:
                month_key = h["date"][:7]
                if month_key not in monthly:
                    monthly[month_key] = {"admissions": 0, "discharges": 0}
                monthly[month_key]["admissions"] += h.get("admissions", 0)
                monthly[month_key]["discharges"] += h.get("discharges", 0)
            for month_key, counts in sorted(monthly.items()):
                trends.append(AdmissionTrend(
                    date=month_key,
                    admissions=counts["admissions"],
                    discharge=counts["discharges"],
                    net_change=counts["admissions"] - counts["discharges"],
                    primary_drivers=["seasonal_illness"],
                ))
        return trends

    def identify_admission_drivers(self, trends: list[AdmissionTrend]) -> list[dict[str, Any]]:
        total_admissions = sum(t.admissions for t in trends)
        if total_admissions == 0:
            return [{"driver": "insufficient_data", "impact": 0}]
        drivers: list[dict[str, Any]] = []
        monthly_admissions: dict[str, int] = {}
        for t in trends:
            month = t.date
            monthly_admissions[month] = monthly_admissions.get(month, 0) + t.admissions
        months = sorted(monthly_admissions.keys())
        if len(months) >= 3:
            recent = sum(monthly_admissions.get(m, 0) for m in months[-3:])
            earlier = sum(monthly_admissions.get(m, 0) for m in months[:-3])
            if earlier > 0 and recent > earlier * 1.2:
                drivers.append({"driver": "seasonal_increase", "impact": round((recent - earlier) / earlier * 100, 1)})
        drivers.append({"driver": "baseline_demand", "impact": 100})
        return drivers


from datetime import datetime


class DischargePredictor:
    def predict_discharge_readiness(self, patient_id: str, clinical_data: dict[str, Any] | None = None) -> dict[str, Any]:
        data = clinical_data or {}
        vitals_stable = data.get("vitals_stable", False)
        lab_trends_improving = data.get("lab_trends_improving", False)
        pain_controlled = data.get("pain_controlled", False)
        ambulatory = data.get("ambulatory", False)
        readiness_score = sum([vitals_stable, lab_trends_improving, pain_controlled, ambulatory]) / 4.0
        barriers: list[str] = []
        if not vitals_stable:
            barriers.append("Unstable vital signs")
        if not lab_trends_improving:
            barriers.append("Lab trends not improving")
        if not pain_controlled:
            barriers.append("Pain not adequately controlled")
        if not ambulatory:
            barriers.append("Not yet ambulatory")
        return {
            "patient_id": patient_id,
            "readiness_score": round(readiness_score, 2),
            "ready_for_discharge": readiness_score >= 0.75,
            "estimated_days_to_discharge": max(0, int((1 - readiness_score) * 5)),
            "barriers": barriers,
        }

    def estimate_length_of_stay(self, patient_id: str, diagnosis: str) -> dict[str, Any]:
        los_estimates: dict[str, dict[str, float]] = {
            "myocardial_infarction": {"min": 3, "avg": 5, "max": 10},
            "pneumonia": {"min": 2, "avg": 4, "max": 8},
            "appendicitis": {"min": 1, "avg": 3, "max": 5},
            "stroke": {"min": 5, "avg": 8, "max": 21},
            "hip_fracture": {"min": 3, "avg": 7, "max": 14},
            "diabetic_ketoacidosis": {"min": 2, "avg": 4, "max": 7},
        }
        estimates = los_estimates.get(diagnosis, {"min": 1, "avg": 3, "max": 7})
        return {
            "patient_id": patient_id,
            "diagnosis": diagnosis,
            "estimated_los_days": {
                "minimum": estimates["min"],
                "average": estimates["avg"],
                "maximum": estimates["max"],
            },
            "confidence": "medium",
        }

    def identify_discharge_barriers(self, patient: dict[str, Any]) -> list[str]:
        barriers: list[str] = []
        if not patient.get("has_caregiver", True):
            barriers.append("No caregiver available at home")
        if not patient.get("home_ready", True):
            barriers.append("Home environment not prepared")
        if patient.get("requires_home_care", False) and not patient.get("home_care_arranged", False):
            barriers.append("Home care services not arranged")
        if patient.get("medication_education", False) is False:
            barriers.append("Medication education not completed")
        return barriers


class ResourceUtilizationEngine:
    def __init__(self) -> None:
        self._utilization_data: dict[str, list[dict[str, Any]]] = {}

    def record_utilization(self, resource_type: str, department: str, used: int, available: int) -> None:
        key = f"{resource_type}:{department}"
        if key not in self._utilization_data:
            self._utilization_data[key] = []
        self._utilization_data[key].append({
            "used": used,
            "available": available,
            "rate": used / available if available > 0 else 0,
            "timestamp": time.time(),
        })

    def analyze_utilization(self, resource_type: str, department: str, period: int = 30) -> dict[str, Any]:
        key = f"{resource_type}:{department}"
        records = self._utilization_data.get(key, [])
        cutoff = time.time() - period * 86400
        filtered = [r for r in records if r["timestamp"] >= cutoff]
        if not filtered:
            return {
                "resource_type": resource_type,
                "department": department,
                "average_utilization": 0.0,
                "peak_utilization": 0.0,
                "status": "no_data",
            }
        rates = [r["rate"] for r in filtered]
        avg = sum(rates) / len(rates)
        peak = max(rates)
        return {
            "resource_type": resource_type,
            "department": department,
            "period_days": period,
            "average_utilization": round(avg * 100, 1),
            "peak_utilization": round(peak * 100, 1),
            "data_points": len(filtered),
            "status": "overutilized" if avg > 0.85 else "optimal" if avg > 0.5 else "underutilized",
        }

    def get_efficiency_score(self, utilization: dict[str, Any]) -> float:
        avg_util = utilization.get("average_utilization", 0) / 100.0
        if avg_util == 0:
            return 0.5
        if 0.5 <= avg_util <= 0.85:
            return round(1.0 - abs(avg_util - 0.675) * 2, 3)
        if avg_util < 0.5:
            return round(avg_util / 0.5 * 0.7, 3)
        return round(max(0.0, 1.0 - (avg_util - 0.85) * 3), 3)

    def recommend_optimization(self, analysis: dict[str, Any]) -> list[str]:
        recommendations: list[str] = []
        status = analysis.get("status", "")
        if status == "overutilized":
            recommendations.append("Increase resource capacity by 20%")
            recommendations.append("Implement priority-based allocation")
            recommendations.append("Review scheduling to reduce peak demand")
        elif status == "underutilized":
            recommendations.append("Reduce resource allocation")
            recommendations.append("Consolidate with other departments")
            recommendations.append("Review operational hours")
        else:
            recommendations.append("Current utilization is optimal")
        return recommendations
