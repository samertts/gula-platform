from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import require_permission
from .engine import DigitalTwinEngine
from .models import (
    DigitalTwin,
    Prediction,
    Simulation,
    SimulationSnapshot,
    TwinType,
)

router = APIRouter(prefix="/simulation", tags=["simulation"])

ENGINE_INSTANCES: dict[str, DigitalTwinEngine] = {}


def _get_engine(db: Session) -> DigitalTwinEngine:
    key = str(id(db))
    if key not in ENGINE_INSTANCES:
        ENGINE_INSTANCES[key] = DigitalTwinEngine(db)
    return ENGINE_INSTANCES[key]


# ── Request / Response models ──────────────────────────────────────────────────


class TwinCreateRequest(BaseModel):
    twin_type: TwinType
    entity_id: int
    entity_type: str = Field(default="lab")


class TwinResponse(BaseModel):
    id: int
    twin_type: str
    entity_id: int
    entity_type: str
    name: str
    config: dict | None
    state: dict | None
    metrics: dict | None
    version: int
    is_active: bool
    created_at: str | None
    updated_at: str | None

    model_config = ConfigDict(from_attributes=True)


class SimulationRequest(BaseModel):
    simulation_type: str
    parameters: dict = Field(default_factory=dict)


class SimulationResponse(BaseModel):
    id: int
    twin_id: int
    name: str
    simulation_type: str
    parameters: dict | None
    status: str
    result: dict | None
    started_at: str | None
    completed_at: str | None
    error: str | None
    triggered_by: int | None
    created_at: str | None

    model_config = ConfigDict(from_attributes=True)


class PredictionRequest(BaseModel):
    prediction_type: str
    horizon_days: int = Field(default=30, ge=1, le=365)


class PredictionResponse(BaseModel):
    id: int
    twin_id: int
    prediction_type: str
    target_date: str
    predicted_value: dict | None
    confidence: float | None
    model_name: str | None
    features_used: dict | None
    actual_value: dict | None
    created_at: str | None

    model_config = ConfigDict(from_attributes=True)


class DashboardTwinSummary(BaseModel):
    id: int
    name: str
    twin_type: str
    entity_id: int
    entity_type: str
    status: str
    health_score: float
    simulation_count: int
    prediction_count: int
    last_updated: str | None
    is_active: bool


class DashboardResponse(BaseModel):
    twins: list[DashboardTwinSummary]
    total_twins: int
    total_simulations: int
    total_predictions: int
    healthy_count: int
    degraded_count: int
    unhealthy_count: int
    by_type: dict


# ── Routes ─────────────────────────────────────────────────────────────────────


def _format_dt(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


@router.post("/twins", response_model=TwinResponse)
def create_twin(
    data: TwinCreateRequest,
    current_user: LabUser = Depends(require_permission("simulation:write")),
    db: Session = Depends(get_db),
):
    engine = _get_engine(db)
    import asyncio

    twin = asyncio.run(
        engine.get_or_create_twin(
            twin_type=data.twin_type,
            entity_id=data.entity_id,
            entity_type=data.entity_type,
        ),
    )
    return TwinResponse(
        id=twin.id,
        twin_type=twin.twin_type.value if hasattr(twin.twin_type, "value") else str(twin.twin_type),
        entity_id=twin.entity_id,
        entity_type=twin.entity_type,
        name=twin.name,
        config=twin.config,
        state=twin.state,
        metrics=twin.metrics,
        version=twin.version,
        is_active=twin.is_active,
        created_at=_format_dt(twin.created_at),
        updated_at=_format_dt(twin.updated_at),
    )


@router.get("/twins/{twin_id}", response_model=TwinResponse)
def get_twin(
    twin_id: int,
    current_user: LabUser = Depends(require_permission("simulation:read")),
    db: Session = Depends(get_db),
):
    twin = db.query(DigitalTwin).filter(DigitalTwin.id == twin_id).first()
    if not twin:
        raise HTTPException(status_code=404, detail="Digital twin not found")
    return TwinResponse(
        id=twin.id,
        twin_type=twin.twin_type.value if hasattr(twin.twin_type, "value") else str(twin.twin_type),
        entity_id=twin.entity_id,
        entity_type=twin.entity_type,
        name=twin.name,
        config=twin.config,
        state=twin.state,
        metrics=twin.metrics,
        version=twin.version,
        is_active=twin.is_active,
        created_at=_format_dt(twin.created_at),
        updated_at=_format_dt(twin.updated_at),
    )


@router.post("/twins/{twin_id}/simulate", response_model=SimulationResponse)
def run_simulation(
    twin_id: int,
    data: SimulationRequest,
    current_user: LabUser = Depends(require_permission("simulation:write")),
    db: Session = Depends(get_db),
):
    twin = db.query(DigitalTwin).filter(DigitalTwin.id == twin_id).first()
    if not twin:
        raise HTTPException(status_code=404, detail="Digital twin not found")

    engine = _get_engine(db)
    import asyncio

    sim = asyncio.run(
        engine.run_simulation(
            twin_id=twin_id,
            simulation_type=data.simulation_type,
            parameters=data.parameters,
            triggered_by=current_user.id,
        ),
    )
    return SimulationResponse(
        id=sim.id,
        twin_id=sim.twin_id,
        name=sim.name,
        simulation_type=sim.simulation_type,
        parameters=sim.parameters,
        status=sim.status.value if hasattr(sim.status, "value") else str(sim.status),
        result=sim.result,
        started_at=_format_dt(sim.started_at),
        completed_at=_format_dt(sim.completed_at),
        error=sim.error,
        triggered_by=sim.triggered_by,
        created_at=_format_dt(sim.created_at),
    )


@router.get("/simulations/{sim_id}", response_model=SimulationResponse)
def get_simulation(
    sim_id: int,
    current_user: LabUser = Depends(require_permission("simulation:read")),
    db: Session = Depends(get_db),
):
    sim = db.query(Simulation).filter(Simulation.id == sim_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")

    snapshots = (
        db.query(SimulationSnapshot)
        .filter(SimulationSnapshot.simulation_id == sim_id)
        .order_by(SimulationSnapshot.timestamp)
        .all()
    )

    return SimulationResponse(
        id=sim.id,
        twin_id=sim.twin_id,
        name=sim.name,
        simulation_type=sim.simulation_type,
        parameters=sim.parameters,
        status=sim.status.value if hasattr(sim.status, "value") else str(sim.status),
        result={
            **(sim.result or {}),
            "snapshots": [
                {
                    "timestamp": _format_dt(s.timestamp),
                    "state": s.state_snapshot,
                    "metrics": s.metrics_snapshot,
                }
                for s in snapshots
            ],
        }
        if sim.result
        else {
            "snapshots": [
                {
                    "timestamp": _format_dt(s.timestamp),
                    "state": s.state_snapshot,
                    "metrics": s.metrics_snapshot,
                }
                for s in snapshots
            ]
        },
        started_at=_format_dt(sim.started_at),
        completed_at=_format_dt(sim.completed_at),
        error=sim.error,
        triggered_by=sim.triggered_by,
        created_at=_format_dt(sim.created_at),
    )


@router.post("/twins/{twin_id}/predict", response_model=PredictionResponse)
def create_prediction(
    twin_id: int,
    data: PredictionRequest,
    current_user: LabUser = Depends(require_permission("simulation:write")),
    db: Session = Depends(get_db),
):
    twin = db.query(DigitalTwin).filter(DigitalTwin.id == twin_id).first()
    if not twin:
        raise HTTPException(status_code=404, detail="Digital twin not found")

    engine = _get_engine(db)
    import asyncio

    prediction = asyncio.run(
        engine.predict_capacity(
            twin_id=twin_id,
            metric=data.prediction_type,
            horizon_days=data.horizon_days,
        ),
    )
    return PredictionResponse(
        id=prediction.id,
        twin_id=prediction.twin_id,
        prediction_type=prediction.prediction_type,
        target_date=_format_dt(prediction.target_date),
        predicted_value=prediction.predicted_value,
        confidence=prediction.confidence,
        model_name=prediction.model_name,
        features_used=prediction.features_used,
        actual_value=prediction.actual_value,
        created_at=_format_dt(prediction.created_at),
    )


@router.get("/predictions/{prediction_id}", response_model=PredictionResponse)
def get_prediction(
    prediction_id: int,
    current_user: LabUser = Depends(require_permission("simulation:read")),
    db: Session = Depends(get_db),
):
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return PredictionResponse(
        id=prediction.id,
        twin_id=prediction.twin_id,
        prediction_type=prediction.prediction_type,
        target_date=_format_dt(prediction.target_date),
        predicted_value=prediction.predicted_value,
        confidence=prediction.confidence,
        model_name=prediction.model_name,
        features_used=prediction.features_used,
        actual_value=prediction.actual_value,
        created_at=_format_dt(prediction.created_at),
    )


@router.get("/twins/{twin_id}/health")
def get_twin_health(
    twin_id: int,
    current_user: LabUser = Depends(require_permission("simulation:read")),
    db: Session = Depends(get_db),
):
    engine = _get_engine(db)
    import asyncio

    return asyncio.run(engine.get_twin_health(twin_id))


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    current_user: LabUser = Depends(require_permission("simulation:read")),
    db: Session = Depends(get_db),
):
    twins = db.query(DigitalTwin).filter(DigitalTwin.is_active.is_(True)).all()
    engine = _get_engine(db)

    twin_summaries = []
    healthy = degraded = unhealthy = 0
    total_simulations = 0
    total_predictions = 0
    by_type: dict[str, int] = {}

    import asyncio

    for twin in twins:
        try:
            health = asyncio.run(engine.get_twin_health(twin.id))
        except Exception:
            health = {"score": 0, "status": "unhealthy"}

        score = health.get("score", 0)
        status = health.get("status", "unknown")
        if status == "healthy":
            healthy += 1
        elif status == "degraded":
            degraded += 1
        else:
            unhealthy += 1

        sim_count = health.get("simulations", 0)
        pred_count = health.get("predictions", 0)
        total_simulations += sim_count
        total_predictions += pred_count

        twin_type_key = (
            twin.twin_type.value if hasattr(twin.twin_type, "value") else str(twin.twin_type)
        )
        by_type[twin_type_key] = by_type.get(twin_type_key, 0) + 1

        twin_summaries.append(
            DashboardTwinSummary(
                id=twin.id,
                name=twin.name,
                twin_type=twin_type_key,
                entity_id=twin.entity_id,
                entity_type=twin.entity_type,
                status=status,
                health_score=score,
                simulation_count=sim_count,
                prediction_count=pred_count,
                last_updated=_format_dt(twin.updated_at),
                is_active=twin.is_active,
            ),
        )

    return DashboardResponse(
        twins=twin_summaries,
        total_twins=len(twins),
        total_simulations=total_simulations,
        total_predictions=total_predictions,
        healthy_count=healthy,
        degraded_count=degraded,
        unhealthy_count=unhealthy,
        by_type=by_type,
    )
