"""Digital Twin Engine — core simulation and prediction logic.

Supports four twin types:
  - HOSPITAL        (patient flow, bed occupancy, resource utilization)
  - LABORATORY      (test volume, TAT, equipment utilization)
  - DIRECTORATE     (multi-facility coordination, disease scenarios)
  - NATIONAL_HEALTH (population-level outbreak modeling, health metrics)
"""

import math
import random
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean, stdev

from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC

from ..models.lab import Lab
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.patient import Patient
from .models import (
    CapacityPlan,
    DigitalTwin,
    Prediction,
    Simulation,
    SimulationSnapshot,
    SimulationStatus,
    TwinType,
)

# ── Statistical helpers ────────────────────────────────────────────────────────


def _sma(values: list[float], window: int) -> list[float]:
    """Simple moving average — smooths a time series."""
    if not values or window <= 0:
        return []
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        result.append(sum(values[start : i + 1]) / (i - start + 1))
    return result


def _ema(values: list[float], alpha: float = 0.3) -> list[float]:
    """Exponential moving average — more weight on recent observations."""
    if not values:
        return []
    result = [values[0]]
    for v in values[1:]:
        result.append(alpha * v + (1 - alpha) * result[-1])
    return result


def _linear_trend(values: list[float]) -> tuple[float, float]:
    """Return (slope, intercept) of a simple linear regression."""
    n = len(values)
    if n < 2:
        return 0.0, (values[0] if values else 0.0)
    xs = list(range(n))
    x_mean = mean(xs)
    y_mean = mean(values)
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values, strict=False))
    den = sum((x - x_mean) ** 2 for x in xs)
    slope = num / den if den != 0 else 0.0
    intercept = y_mean - slope * x_mean
    return slope, intercept


def _project(values: list[float], steps: int) -> list[float]:
    """Project forward using linear trend."""
    if not values:
        return [0.0] * steps
    slope, intercept = _linear_trend(values)
    n = len(values)
    return [slope * (n + i) + intercept for i in range(steps)]


def _random_walk(base: float, volatility: float, steps: int) -> list[float]:
    """Generate a random walk series around a base value."""
    result = []
    current = base
    for _ in range(steps):
        current += random.gauss(0, volatility * current)
        current = max(0, current)
        result.append(current)
    return result


def _sir_model(
    population: int,
    infected: int,
    recovered: int,
    r0: float,
    recovery_days: float = 14.0,
    days: int = 90,
) -> dict:
    """SIR compartmental model for infectious disease spread.

    Returns daily S/I/R arrays plus peak metrics.
    """
    beta = r0 / recovery_days
    gamma = 1.0 / recovery_days
    susceptible = population - infected - recovered

    s_curve, i_curve, r_curve = [susceptible], [infected], [recovered]
    s, i, r = float(susceptible), float(infected), float(recovered)

    for _ in range(days):
        new_infections = beta * s * i / population
        new_recoveries = gamma * i
        s -= new_infections
        i += new_infections - new_recoveries
        r += new_recoveries
        s = max(s, 0)
        i = max(i, 0)
        r = max(r, 0)
        s_curve.append(s)
        i_curve.append(i)
        r_curve.append(r)

    peak_infected = max(i_curve)
    peak_day = i_curve.index(peak_infected)
    total_infected = i_curve[-1] + r_curve[-1]

    return {
        "population": population,
        "r0": r0,
        "recovery_days": recovery_days,
        "susceptible": [round(v) for v in s_curve],
        "infected": [round(v) for v in i_curve],
        "recovered": [round(v) for v in r_curve],
        "peak_infected": round(peak_infected),
        "peak_day": peak_day,
        "total_infected": round(total_infected),
        "attack_rate": round(total_infected / population * 100, 2) if population else 0,
    }


def _herd_immunity_threshold(r0: float) -> float:
    """Fraction needed for herd immunity: 1 - 1/R0."""
    if r0 <= 1:
        return 0.0
    return 1.0 - 1.0 / r0


def _seasonal_factor(now: datetime | None = None) -> float:
    """Return a seasonal multiplier [0.7, 1.3] based on time of year.

    Northern hemisphere: winter peak (~1.3), summer trough (~0.7).
    """
    now = now or datetime.now(UTC)
    day_of_year = now.timetuple().tm_yday
    angle = 2 * math.pi * (day_of_year - 1) / 365.0
    return 1.0 + 0.3 * math.cos(angle)


# ── Engine ─────────────────────────────────────────────────────────────────────


class DigitalTwinEngine:
    """Orchestrates digital twins for hospitals, labs, directorates, and the national system."""

    def __init__(self, db: Session):
        self.db = db

    async def get_or_create_twin(
        self, twin_type: TwinType, entity_id: int, entity_type: str,
    ) -> DigitalTwin:
        twin = (
            self.db.query(DigitalTwin)
            .filter(
                DigitalTwin.twin_type == twin_type,
                DigitalTwin.entity_id == entity_id,
                DigitalTwin.entity_type == entity_type,
                DigitalTwin.is_active.is_(True),
            )
            .first()
        )
        if twin:
            return twin

        name = self._resolve_entity_name(twin_type, entity_id, entity_type)
        twin = DigitalTwin(
            twin_type=twin_type,
            entity_id=entity_id,
            entity_type=entity_type,
            name=name,
            config={},
            state=self._bootstrap_state(twin_type, entity_id, entity_type),
            metrics=self._bootstrap_metrics(twin_type, entity_id, entity_type),
            version=1,
            is_active=True,
        )
        self.db.add(twin)
        self.db.commit()
        self.db.refresh(twin)
        return twin

    async def update_twin_state(self, twin_id: int, state: dict) -> DigitalTwin:
        twin = self.db.query(DigitalTwin).filter(DigitalTwin.id == twin_id).first()
        if not twin:
            raise ValueError(f"DigitalTwin {twin_id} not found")
        current = twin.state or {}
        current.update(state)
        twin.state = current
        twin.version += 1
        twin.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(twin)
        return twin

    async def run_simulation(
        self,
        twin_id: int,
        simulation_type: str,
        parameters: dict | None = None,
        triggered_by: int | None = None,
    ) -> Simulation:
        twin = self.db.query(DigitalTwin).filter(DigitalTwin.id == twin_id).first()
        if not twin:
            raise ValueError(f"DigitalTwin {twin_id} not found")

        sim = Simulation(
            twin_id=twin_id,
            name=f"{simulation_type}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            simulation_type=simulation_type,
            parameters=parameters or {},
            status=SimulationStatus.RUNNING,
            started_at=datetime.now(UTC),
            triggered_by=triggered_by,
        )
        self.db.add(sim)
        self.db.commit()
        self.db.refresh(sim)

        try:
            simulator = self._get_simulator(twin)
            result = await simulator.run(simulation_type, parameters or {})
            sim.result = result
            sim.status = SimulationStatus.COMPLETED
            sim.completed_at = datetime.now(UTC)

            snap = SimulationSnapshot(
                simulation_id=sim.id,
                state_snapshot=twin.state,
                metrics_snapshot=twin.metrics,
            )
            self.db.add(snap)
        except Exception as exc:
            sim.status = SimulationStatus.FAILED
            sim.error = str(exc)
            sim.completed_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(sim)
        return sim

    async def predict_capacity(
        self,
        twin_id: int,
        metric: str,
        horizon_days: int = 30,
    ) -> Prediction:
        twin = self.db.query(DigitalTwin).filter(DigitalTwin.id == twin_id).first()
        if not twin:
            raise ValueError(f"DigitalTwin {twin_id} not found")

        target_date = datetime.now(UTC) + timedelta(days=horizon_days)
        predicted_value, confidence, features = self._forecast(twin, metric, horizon_days)

        prediction = Prediction(
            twin_id=twin_id,
            prediction_type=f"capacity_{metric}",
            target_date=target_date,
            predicted_value=predicted_value,
            confidence=confidence,
            model_name="linear_trend_ensemble",
            features_used=features,
        )
        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)

        self._create_capacity_plan(twin, metric, predicted_value, horizon_days)

        return prediction

    async def get_twin_health(self, twin_id: int) -> dict:
        twin = self.db.query(DigitalTwin).filter(DigitalTwin.id == twin_id).first()
        if not twin:
            raise ValueError(f"DigitalTwin {twin_id} not found")

        metrics = twin.metrics or {}

        recency = datetime.now(UTC) - (twin.updated_at or twin.created_at)
        staleness_hours = recency.total_seconds() / 3600
        data_freshness = "current" if staleness_hours < 24 else "stale"

        simulation_count = (
            self.db.query(func.count(Simulation.id))
            .filter(Simulation.twin_id == twin_id)
            .scalar()
            or 0
        )
        failed_simulations = (
            self.db.query(func.count(Simulation.id))
            .filter(
                Simulation.twin_id == twin_id,
                Simulation.status == SimulationStatus.FAILED,
            )
            .scalar()
            or 0
        )

        prediction_count = (
            self.db.query(func.count(Prediction.id))
            .filter(Prediction.twin_id == twin_id)
            .scalar()
            or 0
        )

        accuracy = 0.0
        if prediction_count > 0:
            resolved = (
                self.db.query(Prediction)
                .filter(
                    Prediction.twin_id == twin_id,
                    Prediction.actual_value.isnot(None),
                )
                .all()
            )
            if resolved:
                errors = []
                for p in resolved:
                    pred_val = p.predicted_value or {}
                    act_val = p.actual_value or {}
                    for key in set(list(pred_val.keys()) + list(act_val.keys())):
                        pv = pred_val.get(key, 0)
                        av = act_val.get(key, 0)
                        if isinstance(pv, (int, float)) and isinstance(av, (int, float)):
                            if av != 0:
                                errors.append(abs(pv - av) / max(abs(av), 0.01))
                if errors:
                    mape = mean(errors)
                    accuracy = max(0.0, 1.0 - mape)

        score = 100.0
        if staleness_hours > 48:
            score -= 20
        if failed_simulations > 5:
            score -= 15
        if accuracy < 0.5 and prediction_count > 2:
            score -= 10
        score = max(0.0, min(100.0, score))

        return {
            "twin_id": twin_id,
            "name": twin.name,
            "twin_type": twin.twin_type.value,
            "status": "healthy" if score >= 70 else "degraded" if score >= 40 else "unhealthy",
            "score": round(score, 1),
            "data_freshness": data_freshness,
            "staleness_hours": round(staleness_hours, 1),
            "simulations": simulation_count,
            "failed_simulations": failed_simulations,
            "predictions": prediction_count,
            "prediction_accuracy": round(accuracy, 4),
            "metrics": metrics,
            "last_updated": twin.updated_at.isoformat() if twin.updated_at else None,
        }

    # ── Private helpers ────────────────────────────────────────────────────────

    def _resolve_entity_name(
        self, twin_type: TwinType, entity_id: int, entity_type: str,
    ) -> str:
        if entity_type == "lab":
            lab = self.db.query(Lab).filter(Lab.id == entity_id).first()
            if lab:
                return lab.name or f"Lab #{entity_id}"
        return f"{twin_type.value.title()} #{entity_id}"

    def _bootstrap_state(self, twin_type: TwinType, entity_id: int, entity_type: str) -> dict:
        now = datetime.now(UTC)
        if twin_type == TwinType.LABORATORY and entity_type == "lab":
            total_orders = (
                self.db.query(func.count(LabOrder.id))
                .filter(LabOrder.lab_id == entity_id)
                .scalar()
                or 0
            )
            total_patients = (
                self.db.query(func.count(Patient.id))
                .filter(Patient.lab_id == entity_id)
                .scalar()
                or 0
            )
            return {
                "total_orders": total_orders,
                "total_patients": total_patients,
                "active_tests": 0,
                "avg_tat_hours": 0.0,
                "last_calibration": None,
                "status": "operational",
                "last_updated": now.isoformat(),
            }
        return {
            "status": "initialized",
            "last_updated": now.isoformat(),
        }

    def _bootstrap_metrics(self, twin_type: TwinType, entity_id: int, entity_type: str) -> dict:
        if twin_type == TwinType.LABORATORY and entity_type == "lab":
            return {
                "daily_test_volume": [],
                "daily_tat_hours": [],
                "equipment_uptime": 1.0,
                "error_rate": 0.0,
                "throughput_per_hour": 0.0,
            }
        return {}

    def _get_simulator(self, twin: DigitalTwin):
        sim_map = {
            TwinType.HOSPITAL: HospitalTwin,
            TwinType.LABORATORY: LaboratoryTwin,
            TwinType.DIRECTORATE: DirectorateTwin,
            TwinType.NATIONAL_HEALTH: NationalHealthTwin,
        }
        cls = sim_map.get(twin.twin_type)
        if not cls:
            raise ValueError(f"Unsupported twin type: {twin.twin_type}")
        return cls(twin, self.db)

    def _forecast(
        self, twin: DigitalTwin, metric: str, horizon_days: int,
    ) -> tuple[dict, float, dict]:
        features = {"metric": metric, "horizon_days": horizon_days, "method": "linear_trend"}

        metrics_list = (twin.metrics or {}).get(f"daily_{metric}", [])
        if not metrics_list:
            metrics_list = [0.0] * 30

        if isinstance(metrics_list, list) and metrics_list:
            numeric = [float(v) if v is not None else 0.0 for v in metrics_list]
            projected = _project(numeric, horizon_days)
            _ema(numeric[-30:]) if len(numeric) >= 30 else numeric
            volatility = (
                stdev(numeric[-14:]) / max(mean(numeric[-14:]), 1)
                if len(numeric) >= 14
                else 0.3
            )
            confidence = max(0.1, 1.0 - volatility)
            features["volatility"] = round(volatility, 4)
            features["data_points"] = len(numeric)

            return {
                "metric": metric,
                "current_value": numeric[-1] if numeric else 0.0,
                "projected_values": [round(v, 2) for v in projected],
                "trend_direction": "up" if projected[-1] > numeric[-1] else "down",
                "peak_demand": round(max(projected), 2),
                "peak_day": projected.index(max(projected)) + 1,
            }, round(confidence, 4), features

        return {
            "metric": metric,
            "current_value": 0.0,
            "projected_values": [0.0] * horizon_days,
            "trend_direction": "stable",
            "peak_demand": 0.0,
            "peak_day": 0,
        }, 0.1, features

    def _create_capacity_plan(
        self, twin: DigitalTwin, metric: str, predicted_value: dict, horizon_days: int,
    ) -> None:
        current = predicted_value.get("current_value", 0)
        peak = predicted_value.get("peak_demand", 0)
        predicted_value.get("projected_values", [])

        if peak > current * 1.2:
            priority = "high"
            recommended = peak * 1.15
        elif peak > current * 1.1:
            priority = "medium"
            recommended = peak * 1.05
        else:
            priority = "low"
            recommended = current * 1.02

        plan_date = datetime.now(UTC) + timedelta(days=horizon_days)
        plan = CapacityPlan(
            twin_id=twin.id,
            plan_date=plan_date,
            metric=metric,
            predicted_demand=round(peak, 2),
            current_capacity=round(current, 2),
            recommended_capacity=round(recommended, 2),
            priority=priority,
        )
        self.db.add(plan)
        self.db.commit()


# ── Twin Simulators ────────────────────────────────────────────────────────────


class HospitalTwin:
    """Digital twin for a hospital — patient flow, bed occupancy, resource utilization."""

    def __init__(self, twin: DigitalTwin, db: Session):
        self.twin = twin
        self.db = db

    async def run(self, simulation_type: str, parameters: dict) -> dict:
        sim_map = {
            "patient_flow": self.simulate_patient_flow,
            "bed_occupancy": self._run_bed_occupancy,
            "utilization": lambda: self.calculate_utilization(),
        }
        simulator = sim_map.get(simulation_type)
        if not simulator:
            raise ValueError(f"Unknown simulation type: {simulation_type}")
        if simulation_type in ("patient_flow",):
            return await simulator(parameters.get("admission_rate_change", 0.0))
        return await simulator(parameters)

    async def simulate_patient_flow(self, admission_rate_change: float = 0.0) -> dict:
        entity_id = self.twin.entity_id
        entity_type = self.twin.entity_type
        lab_id = entity_id if entity_type == "lab" else None

        seven_days_ago = datetime.now(UTC) - timedelta(days=7)

        # Base rates from historical data
        base_admissions = 0

        if lab_id:
            base_admissions = (
                self.db.query(func.count(LabOrder.id))
                .filter(
                    LabOrder.lab_id == lab_id,
                    LabOrder.created_at >= seven_days_ago,
                )
                .scalar()
                or 0
            )

        seasonal = _seasonal_factor()
        new_rate = 1.0 + admission_rate_change

        daily_admissions = max(1, int(base_admissions / 7 * new_rate * seasonal))
        daily_discharges = max(1, int(base_admissions / 7 * 0.85 * new_rate))

        project_days = 14
        admission_series = _random_walk(daily_admissions, 0.15, project_days)
        discharge_series = _random_walk(daily_discharges, 0.12, project_days)

        cumulative = 0
        bed_occupancy = []
        for adm, dis in zip(admission_series, discharge_series, strict=False):
            cumulative += adm - dis
            cumulative = max(0, cumulative)
            bed_occupancy.append(round(cumulative))

        avg_los = 3.5 * seasonal  # average length of stay in days

        # Update twin state
        state_update = {
            "current_admissions": int(daily_admissions),
            "avg_length_of_stay": round(avg_los, 1),
            "bed_occupancy_trend": bed_occupancy,
            "status": "simulated",
            "last_simulation": datetime.now(UTC).isoformat(),
        }
        current = self.twin.state or {}
        current.update(state_update)
        self.twin.state = current
        self.twin.updated_at = datetime.now(UTC)
        self.db.commit()

        return {
            "simulation": "patient_flow",
            "admission_rate_change": admission_rate_change,
            "seasonal_factor": round(seasonal, 3),
            "daily_admissions_base": int(base_admissions / 7) if base_admissions else 0,
            "projected_daily_admissions": [round(a, 1) for a in admission_series],
            "projected_daily_discharges": [round(d, 1) for d in discharge_series],
            "bed_occupancy_14day": bed_occupancy,
            "avg_length_of_stay_days": round(avg_los, 1),
            "peak_occupancy": max(bed_occupancy) if bed_occupancy else 0,
        }

    async def _run_bed_occupancy(self, parameters: dict) -> dict:
        return await self.predict_bed_occupancy(parameters.get("days", 7))

    async def predict_bed_occupancy(self, days: int = 7) -> list[dict]:
        entity_id = self.twin.entity_id
        entity_type = self.twin.entity_type
        lab_id = entity_id if entity_type == "lab" else None

        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

        total_beds = 100
        historical_orders = []
        if lab_id:
            historical_orders = (
                self.db.query(LabOrder)
                .filter(
                    LabOrder.lab_id == lab_id,
                    LabOrder.created_at >= thirty_days_ago,
                )
                .order_by(LabOrder.created_at)
                .all()
            )

        daily_volume = defaultdict(int)
        for o in historical_orders:
            day_key = o.created_at.date().isoformat()
            daily_volume[day_key] += 1

        volumes = list(daily_volume.values()) if daily_volume else [5] * 30
        projected = _project(volumes, days)
        smoothed = _ema(projected, alpha=0.4)

        results = []
        for i, pv in enumerate(smoothed):
            occupancy_pct = min(100, max(10, (pv / max(volumes[-1] if volumes else 5, 1)) * 50 + 20 + random.gauss(0, 5)))
            occupied_beds = round(total_beds * occupancy_pct / 100)
            results.append({
                "day": i + 1,
                "date": (datetime.now(UTC) + timedelta(days=i)).date().isoformat(),
                "predicted_occupancy_pct": round(occupancy_pct, 1),
                "occupied_beds": occupied_beds,
                "total_beds": total_beds,
                "available_beds": total_beds - occupied_beds,
            })

        occupancy_values = [r["predicted_occupancy_pct"] for r in results]
        self.twin.metrics = self.twin.metrics or {}
        self.twin.metrics["bed_occupancy_forecast"] = occupancy_values
        self.twin.updated_at = datetime.now(UTC)
        self.db.commit()

        return results

    async def calculate_utilization(self) -> dict:
        entity_id = self.twin.entity_id
        entity_type = self.twin.entity_type
        lab_id = entity_id if entity_type == "lab" else None

        today = datetime.now(UTC)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        if lab_id:
            orders_week = (
                self.db.query(func.count(LabOrder.id))
                .filter(
                    LabOrder.lab_id == lab_id,
                    LabOrder.created_at >= week_ago,
                )
                .scalar()
                or 0
            )
            orders_month = (
                self.db.query(func.count(LabOrder.id))
                .filter(
                    LabOrder.lab_id == lab_id,
                    LabOrder.created_at >= month_ago,
                )
                .scalar()
                or 0
            )
            unique_patients = (
                self.db.query(func.count(func.distinct(LabOrder.patient_id)))
                .filter(
                    LabOrder.lab_id == lab_id,
                    LabOrder.created_at >= month_ago,
                )
                .scalar()
                or 0
            )
        else:
            orders_week = 10
            orders_month = 40
            unique_patients = 20

        seasonal = _seasonal_factor()
        bed_utilization = min(100, (orders_week / 50) * 100 * seasonal * random.uniform(0.9, 1.1))
        staff_utilization = min(100, (unique_patients / 30) * 100 * seasonal * random.uniform(0.85, 1.05))

        self.twin.metrics = self.twin.metrics or {}
        self.twin.metrics.update({
            "bed_utilization_pct": round(bed_utilization, 1),
            "staff_utilization_pct": round(staff_utilization, 1),
            "orders_per_week": orders_week,
            "orders_per_month": orders_month,
            "unique_patients_month": unique_patients,
            "last_calculated": today.isoformat(),
        })
        self.twin.updated_at = datetime.now(UTC)
        self.db.commit()

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "bed_utilization_pct": round(bed_utilization, 1),
            "staff_utilization_pct": round(staff_utilization, 1),
            "orders_per_week": orders_week,
            "orders_per_month": orders_month,
            "unique_patients_month": unique_patients,
            "seasonal_factor": round(seasonal, 3),
            "status": "operational" if bed_utilization < 90 and staff_utilization < 90 else "stressed",
        }


class LaboratoryTwin:
    """Digital twin for a laboratory — test volume, TAT, equipment utilization."""

    def __init__(self, twin: DigitalTwin, db: Session):
        self.twin = twin
        self.db = db

    async def run(self, simulation_type: str, parameters: dict) -> dict:
        sim_map = {
            "test_volume": self.simulate_test_volume,
            "tat_prediction": self._run_tat,
            "utilization": lambda: self.calculate_utilization(),
        }
        simulator = sim_map.get(simulation_type)
        if not simulator:
            raise ValueError(f"Unknown simulation type: {simulation_type}")
        if simulation_type in ("test_volume",):
            return await simulator(parameters.get("volume_change", 0.0))
        return await simulator()

    async def simulate_test_volume(self, volume_change: float = 0.0) -> dict:
        entity_id = self.twin.entity_id
        entity_type = self.twin.entity_type
        lab_id = entity_id if entity_type == "lab" else None

        ninety_days_ago = datetime.now(UTC) - timedelta(days=90)

        daily_volume = defaultdict(int)
        if lab_id:
            results = (
                self.db.query(LabResult)
                .join(LabOrder)
                .filter(
                    LabOrder.lab_id == lab_id,
                    LabResult.created_at >= ninety_days_ago,
                )
                .order_by(LabResult.created_at)
                .all()
            )
            for r in results:
                day_key = r.created_at.date().isoformat()
                daily_volume[day_key] += 1

        if daily_volume:
            volumes = [daily_volume[k] for k in sorted(daily_volume.keys())]
        else:
            volumes = [random.randint(20, 50) for _ in range(90)]

        seasonal = _seasonal_factor()
        new_rate = 1.0 + volume_change

        projected = _project(volumes[-30:] if len(volumes) >= 30 else volumes, 30)
        adjusted = [v * new_rate * seasonal for v in projected]
        smoothed = _ema(adjusted, alpha=0.35)

        current_avg = mean(volumes[-7:]) if len(volumes) >= 7 else mean(volumes) if volumes else 0
        future_avg = mean(smoothed) if smoothed else 0
        peak_day_val = max(smoothed) if smoothed else 0

        metrics_list = self.twin.metrics or {}
        daily_key = metrics_list.get("daily_test_volume", [])
        daily_key = (daily_key + [round(v, 1) for v in smoothed])[-365:]
        metrics_list["daily_test_volume"] = daily_key
        self.twin.metrics = metrics_list
        self.twin.state = self.twin.state or {}
        self.twin.state.update({
            "avg_daily_volume": round(current_avg, 1),
            "projected_avg_daily_volume": round(future_avg, 1),
            "status": "simulated",
            "last_simulation": datetime.now(UTC).isoformat(),
        })
        self.twin.updated_at = datetime.now(UTC)
        self.db.commit()

        return {
            "simulation": "test_volume",
            "volume_change_pct": volume_change * 100,
            "seasonal_factor": round(seasonal, 3),
            "historical_avg_daily": round(current_avg, 1),
            "projected_daily_volume_30day": [round(v, 1) for v in smoothed],
            "projected_avg_daily": round(future_avg, 1),
            "peak_daily_volume": round(peak_day_val, 1),
            "peak_day": smoothed.index(peak_day_val) + 1 if smoothed else 0,
            "total_projected_month": round(sum(smoothed)),
        }

    async def _run_tat(self) -> dict:
        return await self.predict_tat(7)

    async def predict_tat(self, days: int = 7) -> list[dict]:
        entity_id = self.twin.entity_id
        entity_type = self.twin.entity_type
        lab_id = entity_id if entity_type == "lab" else None

        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

        historical_tats = []
        if lab_id:
            results = (
                self.db.query(LabResult)
                .join(LabOrder)
                .filter(
                    LabOrder.lab_id == lab_id,
                    LabResult.created_at >= thirty_days_ago,
                )
                .all()
            )
            for r in results:
                if r.order and r.order.created_at:
                    tat = (r.created_at - r.order.created_at).total_seconds() / 3600
                    historical_tats.append(tat)

        if historical_tats:
            base_tat = mean(historical_tats)
            tat_volatility = stdev(historical_tats) / max(base_tat, 0.01)
        else:
            base_tat = 4.0
            tat_volatility = 0.3

        seasonal = _seasonal_factor()
        projected_tats = []
        for i in range(days):
            factor = 1.0 + 0.1 * math.sin(2 * math.pi * i / 7)
            tat = base_tat * factor * seasonal * random.uniform(1 - tat_volatility, 1 + tat_volatility)
            projected_tats.append(max(0.5, round(tat, 2)))

        results_list = []
        for i, tat in enumerate(projected_tats):
            date = (datetime.now(UTC) + timedelta(days=i)).date().isoformat()
            status = "normal" if tat <= 6 else "warning" if tat <= 12 else "critical"
            results_list.append({
                "day": i + 1,
                "date": date,
                "predicted_tat_hours": tat,
                "status": status,
            })

        self.twin.metrics = self.twin.metrics or {}
        self.twin.metrics["daily_tat_hours"] = projected_tats
        self.twin.metrics["avg_tat_hours"] = round(mean(projected_tats), 2)
        self.twin.state = self.twin.state or {}
        self.twin.state["avg_tat_hours"] = round(mean(projected_tats), 2)
        self.twin.updated_at = datetime.now(UTC)
        self.db.commit()

        return results_list

    async def calculate_utilization(self) -> dict:
        entity_id = self.twin.entity_id
        entity_type = self.twin.entity_type
        lab_id = entity_id if entity_type == "lab" else None

        today = datetime.now(UTC)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        if lab_id:
            results_week = (
                self.db.query(func.count(LabResult.id))
                .join(LabOrder)
                .filter(
                    LabOrder.lab_id == lab_id,
                    LabResult.created_at >= week_ago,
                )
                .scalar()
                or 0
            )
            results_month = (
                self.db.query(func.count(LabResult.id))
                .join(LabOrder)
                .filter(
                    LabOrder.lab_id == lab_id,
                    LabResult.created_at >= month_ago,
                )
                .scalar()
                or 0
            )
            total_tests_all = (
                self.db.query(func.count(LabResult.id))
                .join(LabOrder)
                .filter(LabOrder.lab_id == lab_id)
                .scalar()
                or 0
            )
        else:
            results_week = 50
            results_month = 200
            total_tests_all = 1000

        seasonal = _seasonal_factor()
        daily_capacity = max(1, int(results_week / 7 * 1.5))
        throughput = min(100, (results_week / (daily_capacity * 7)) * 100 * seasonal * 100)

        equipment_uptime = random.uniform(0.92, 0.99)
        error_rate = random.uniform(0.001, 0.03)

        self.twin.metrics = self.twin.metrics or {}
        self.twin.metrics.update({
            "equipment_uptime": round(equipment_uptime, 4),
            "error_rate": round(error_rate, 4),
            "throughput_per_hour": round(results_week / (7 * 8), 1),
            "results_per_week": results_week,
            "results_per_month": results_month,
            "total_tests": total_tests_all,
            "last_calculated": today.isoformat(),
        })
        self.twin.updated_at = datetime.now(UTC)
        self.db.commit()

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "equipment_uptime": round(equipment_uptime, 4),
            "error_rate": round(error_rate, 4),
            "throughput_per_hour": round(results_week / (7 * 8), 1),
            "capacity_utilization_pct": round(throughput, 1),
            "results_per_week": results_week,
            "results_per_month": results_month,
            "total_tests_processed": total_tests_all,
            "seasonal_factor": round(seasonal, 3),
            "status": "operational" if throughput < 90 else "at_capacity",
        }


class DirectorateTwin:
    """Digital twin for a health directorate — coordinates multiple facilities."""

    def __init__(self, twin: DigitalTwin, db: Session):
        self.twin = twin
        self.db = db

    async def run(self, simulation_type: str, parameters: dict) -> dict:
        sim_map = {
            "disease_scenario": self.simulate_disease_scenario,
            "resource_demand": self._run_resource_demand,
        }
        simulator = sim_map.get(simulation_type)
        if not simulator:
            raise ValueError(f"Unknown simulation type: {simulation_type}")
        if simulation_type == "disease_scenario":
            return await simulator(
                parameters.get("disease", "influenza"),
                parameters.get("r0", 1.5),
            )
        return await simulator(parameters.get("days", 30))

    async def simulate_disease_scenario(self, disease: str, r0: float = 1.5) -> dict:
        entity_type = self.twin.entity_type

        population = 500000
        if entity_type == "province":
            population = 2000000
        elif entity_type == "district":
            population = 250000

        initial_infected = max(1, int(population * 0.0001))
        initial_recovered = 0

        sir = _sir_model(
            population=population,
            infected=initial_infected,
            recovered=initial_recovered,
            r0=r0,
            recovery_days=14.0,
            days=90,
        )

        herd_immunity = _herd_immunity_threshold(r0)

        disease_profiles = {
            "influenza": {"name": "Influenza", "r0_range": (1.2, 2.0), "hospitalization_rate": 0.02},
            "covid19": {"name": "COVID-19", "r0_range": (2.0, 3.5), "hospitalization_rate": 0.05},
            "measles": {"name": "Measles", "r0_range": (12.0, 18.0), "hospitalization_rate": 0.1},
            "cholera": {"name": "Cholera", "r0_range": (1.5, 4.0), "hospitalization_rate": 0.15},
            "dengue": {"name": "Dengue", "r0_range": (1.5, 5.0), "hospitalization_rate": 0.05},
        }
        profile = disease_profiles.get(disease, disease_profiles["influenza"])

        total_infected = sir["total_infected"]
        hospitalizations = int(total_infected * profile["hospitalization_rate"])
        severe = int(hospitalizations * 0.25)
        fatalities = int(severe * 0.3)

        mitigation_scenarios = {}
        for label, reduction in [("moderate", 0.5), ("strong", 0.75), ("lockdown", 0.9)]:
            reduced_r0 = r0 * (1 - reduction)
            if reduced_r0 <= 1:
                mitigation_scenarios[label] = {
                    "effective_r0": round(reduced_r0, 2),
                    "total_infected": int(population * 0.02),
                    "peak_day": 30,
                }
            else:
                m_sir = _sir_model(
                    population=population,
                    infected=initial_infected,
                    recovered=initial_recovered,
                    r0=reduced_r0,
                    recovery_days=14.0,
                    days=180,
                )
                mitigation_scenarios[label] = {
                    "effective_r0": round(reduced_r0, 2),
                    "total_infected": m_sir["total_infected"],
                    "peak_day": m_sir["peak_day"],
                }

        self.twin.state = self.twin.state or {}
        self.twin.state.update({
            "last_disease_scenario": disease,
            "last_r0": r0,
            "attack_rate": sir["attack_rate"],
            "herd_immunity_threshold": round(herd_immunity, 4),
            "last_simulation": datetime.now(UTC).isoformat(),
        })
        self.twin.updated_at = datetime.now(UTC)
        self.db.commit()

        return {
            "simulation": "disease_scenario",
            "disease": profile["name"],
            "r0": r0,
            "population": population,
            "sir_curve": {
                "susceptible": sir["susceptible"][:90],
                "infected": sir["infected"][:90],
                "recovered": sir["recovered"][:90],
            },
            "peak": {
                "infected_at_peak": sir["peak_infected"],
                "peak_day": sir["peak_day"],
                "total_infected": sir["total_infected"],
                "attack_rate_pct": sir["attack_rate"],
            },
            "healthcare_impact": {
                "estimated_hospitalizations": hospitalizations,
                "estimated_severe": severe,
                "estimated_fatalities": fatalities,
            },
            "herd_immunity_threshold_pct": round(herd_immunity * 100, 1),
            "mitigation_scenarios": mitigation_scenarios,
        }

    async def _run_resource_demand(self, days: int = 30) -> dict:
        return await self.predict_resource_demand(days)

    async def predict_resource_demand(self, days: int = 30) -> dict:
        entity_type = self.twin.entity_type

        population = 500000
        if entity_type == "province":
            population = 2000000
        elif entity_type == "district":
            population = 250000

        seasonal = _seasonal_factor()

        # Baseline resource needs per 100k population per day
        base_bed_need = 2.5 * seasonal
        base_staff_need = 1.8 * seasonal
        base_ventilator_need = 0.3 * seasonal
        base_vaccine_need = 50 * seasonal

        scale = population / 100000
        bed_series = _random_walk(base_bed_need * scale, 0.1, days)
        staff_series = _random_walk(base_staff_need * scale, 0.08, days)
        vent_series = _random_walk(base_ventilator_need * scale, 0.12, days)
        vaccine_series = _random_walk(base_vaccine_need * scale, 0.15, days)

        self.twin.state = self.twin.state or {}
        self.twin.state.update({
            "resource_demand_calculated": datetime.now(UTC).isoformat(),
            "population": population,
        })
        self.twin.updated_at = datetime.now(UTC)
        self.db.commit()

        return {
            "simulation": "resource_demand",
            "population": population,
            "seasonal_factor": round(seasonal, 3),
            "projected_daily_demand": {
                "beds": [round(b, 1) for b in bed_series],
                "staff": [round(s, 1) for s in staff_series],
                "ventilators": [round(v, 1) for v in vent_series],
                "vaccine_doses": [round(v, 1) for v in vaccine_series],
            },
            "peak_daily_demand": {
                "beds": round(max(bed_series), 1),
                "staff": round(max(staff_series), 1),
                "ventilators": round(max(vent_series), 1),
                "vaccine_doses": round(max(vaccine_series), 1),
            },
            "total_demand_{days}day": {
                "beds": round(sum(bed_series)),
                "staff_hours": round(sum(staff_series) * 8),
                "ventilator_days": round(sum(vent_series)),
                "vaccine_doses": round(sum(vaccine_series)),
            },
        }


class NationalHealthTwin:
    """Digital twin for the national health system — population-level modeling."""

    def __init__(self, twin: DigitalTwin, db: Session):
        self.twin = twin
        self.db = db

    async def run(self, simulation_type: str, parameters: dict) -> dict:
        sim_map = {
            "outbreak": self.simulate_outbreak_scenario,
            "population_health": self._run_population_health,
        }
        simulator = sim_map.get(simulation_type)
        if not simulator:
            raise ValueError(f"Unknown simulation type: {simulation_type}")
        if simulation_type == "outbreak":
            return await simulator(
                parameters.get("pathogen", "general"),
                parameters.get("parameters", {}),
            )
        return await simulator(parameters.get("metrics", []))

    async def simulate_outbreak_scenario(
        self, pathogen: str, parameters: dict | None = None,
    ) -> dict:
        params = parameters or {}
        population = params.get("population", 40000000)  # Iraq ~40M
        r0 = params.get("r0", 2.5)
        initial_infected = params.get("initial_infected", 100)
        recovery_days = params.get("recovery_days", 14.0)
        mortality_rate = params.get("mortality_rate", 0.01)
        incubation_days = params.get("incubation_days", 5.0)
        intervention_day = params.get("intervention_day", 30)
        intervention_effectiveness = params.get("intervention_effectiveness", 0.3)

        sir = _sir_model(
            population=population,
            infected=initial_infected,
            recovered=0,
            r0=r0,
            recovery_days=recovery_days,
            days=180,
        )

        # Intervention scenario
        delayed_sir = dict(sir)
        if intervention_day < 180:
            delayed_r0 = r0 * (1 - intervention_effectiveness)
            if delayed_r0 > 1:
                # Shift the SIR to start at intervention day with current values
                delayed_sir = _sir_model(
                    population=population - sir["total_infected"],
                    infected=sir["infected"][intervention_day],
                    recovered=sir["recovered"][intervention_day],
                    r0=delayed_r0,
                    recovery_days=recovery_days,
                    days=180 - intervention_day,
                )

        estimated_fatalities = int(sir["total_infected"] * mortality_rate)
        delayed_fatalities = int(delayed_sir.get("total_infected", 0) * mortality_rate)
        fatalities_averted = estimated_fatalities - delayed_fatalities

        pathogen_profiles = {
            "influenza_pandemic": {"name": "Influenza Pandemic", "typical_r0": 1.8},
            "sars_cov2": {"name": "SARS-CoV-2", "typical_r0": 3.0},
            "measles": {"name": "Measles", "typical_r0": 15.0},
            "novel_pathogen": {"name": "Novel Pathogen", "typical_r0": r0},
        }
        profile = pathogen_profiles.get(pathogen, {"name": pathogen, "typical_r0": r0})

        self.twin.state = self.twin.state or {}
        self.twin.state.update({
            "last_outbreak_scenario": pathogen,
            "last_r0": r0,
            "estimated_fatalities": estimated_fatalities,
            "attack_rate": sir["attack_rate"],
            "last_simulation": datetime.now(UTC).isoformat(),
        })
        self.twin.updated_at = datetime.now(UTC)
        self.db.commit()

        return {
            "simulation": "outbreak",
            "pathogen": profile["name"],
            "pathogen_key": pathogen,
            "r0": r0,
            "population": population,
            "mortality_rate": mortality_rate,
            "incubation_days": incubation_days,
            "no_intervention": {
                "peak_infected": sir["peak_infected"],
                "peak_day": sir["peak_day"],
                "total_infected": sir["total_infected"],
                "attack_rate_pct": sir["attack_rate"],
                "estimated_fatalities": estimated_fatalities,
            },
            "with_intervention": {
                "intervention_day": intervention_day,
                "intervention_effectiveness": intervention_effectiveness,
                "effective_r0": round(r0 * (1 - intervention_effectiveness), 2),
                "peak_infected": delayed_sir.get("peak_infected", sir["peak_infected"]),
                "peak_day": delayed_sir.get("peak_day", sir["peak_day"]) + intervention_day if delayed_sir.get("peak_day") else sir["peak_day"],
                "total_infected": delayed_sir.get("total_infected", sir["total_infected"]),
                "estimated_fatalities": delayed_fatalities,
                "fatalities_averted": fatalities_averted,
            },
            "healthcare_system_impact": {
                "hospitalization_rate": 0.03,
                "estimated_hospitalizations": int(sir["total_infected"] * 0.03),
                "icu_rate": 0.005,
                "estimated_icu_admissions": int(sir["total_infected"] * 0.005),
            },
        }

    async def _run_population_health(self, metrics: list[str]) -> dict:
        return await self.predict_population_health(metrics or ["life_expectancy", "infant_mortality", "chronic_disease_prevalence"])

    async def predict_population_health(self, metrics: list[str]) -> dict:
        results = {}
        for metric in metrics:
            if metric == "life_expectancy":
                base = 70.5
                trend = base + random.gauss(0.1, 0.05)
                results[metric] = {
                    "current": round(base, 1),
                    "trend": round(trend, 1),
                    "projected_1y": round(base + 0.2, 1),
                    "projected_5y": round(base + 1.0, 1),
                    "unit": "years",
                }
            elif metric == "infant_mortality":
                base = 22.0
                trend = base - random.gauss(0.5, 0.2)
                results[metric] = {
                    "current": round(base, 1),
                    "trend": round(max(trend, 15), 1),
                    "projected_1y": round(base - 0.8, 1),
                    "projected_5y": round(base - 3.5, 1),
                    "unit": "per_1000_live_births",
                }
            elif metric == "chronic_disease_prevalence":
                base_pct = random.uniform(15, 25)
                results[metric] = {
                    "current": round(base_pct, 1),
                    "trend": round(base_pct + random.uniform(0.5, 1.5), 1),
                    "breakdown": {
                        "diabetes": round(base_pct * 0.35, 1),
                        "hypertension": round(base_pct * 0.40, 1),
                        "respiratory": round(base_pct * 0.15, 1),
                        "cardiovascular": round(base_pct * 0.10, 1),
                    },
                    "unit": "pct",
                }
            elif metric == "vaccination_coverage":
                base_pct = random.uniform(75, 90)
                results[metric] = {
                    "current": round(base_pct, 1),
                    "trend": round(base_pct + random.gauss(0.0, 0.5), 1),
                    "breakdown": {
                        "polio": round(min(base_pct + 5, 98), 1),
                        "measles": round(base_pct - 3, 1),
                        "bcg": round(base_pct + 2, 1),
                        "hepatitis_b": round(base_pct, 1),
                    },
                    "unit": "pct",
                }
            elif metric == "healthcare_access":
                base_pct = random.uniform(60, 80)
                results[metric] = {
                    "current": round(base_pct, 1),
                    "urban": round(min(base_pct + 15, 98), 1),
                    "rural": round(max(base_pct - 20, 30), 1),
                    "unit": "pct",
                }
            elif metric == "bed_per_capita":
                beds_per_10k = random.uniform(1.0, 2.0)
                results[metric] = {
                    "current": round(beds_per_10k, 2),
                    "who_recommendation": 3.0,
                    "gap_pct": round((1 - beds_per_10k / 3.0) * 100, 1),
                    "unit": "beds_per_10000",
                }
            else:
                results[metric] = {
                    "current": None,
                    "error": f"Unknown metric: {metric}",
                }

        now = datetime.now(UTC)
        self.twin.state = self.twin.state or {}
        self.twin.state["last_population_health_calc"] = now.isoformat()
        self.twin.updated_at = now
        self.db.commit()

        return {
            "simulation": "population_health",
            "metrics": results,
            "overall_health_score": round(
                mean(
                    v.get("current", 0) / 100
                    for v in results.values()
                    if isinstance(v, dict) and v.get("unit") in ("pct",)
                )
                * 100
                if any(
                    isinstance(v, dict) and v.get("unit") in ("pct",)
                    for v in results.values()
                )
                else 0,
                1,
            ),
            "calculated_at": now.isoformat(),
        }
