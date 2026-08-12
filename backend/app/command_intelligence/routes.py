from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app._compat import UTC

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import require_permission
from .engine import analyzer, engine, kpi_engine

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class IncidentReport(BaseModel):
    incident_type: str = Field(..., min_length=1, max_length=100)
    severity: str = Field(..., pattern=r"^(low|medium|high|critical)$")
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    affected_entities: list[dict[str, Any]] | None = None
    root_cause: str | None = None
    impact_analysis: dict[str, Any] | None = None
    recommendation: dict[str, Any] | None = None


class RecommendationRequest(BaseModel):
    recommendation_type: str = Field(..., min_length=1, max_length=100)
    priority: int = Field(default=0, ge=0, le=100)
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    expected_impact: dict[str, Any] | None = None
    risk_assessment: dict[str, Any] | None = None


@router.get("/situation-room")
async def get_situation_room(
    region: str | None = Query(None),
    current_user: LabUser = Depends(require_permission("dashboard:read")),
    db: Session = Depends(get_db),
):
    return await engine.get_live_situation_room(db, region)


@router.get("/kpis")
async def get_kpis(
    category: str | None = Query(None),
    current_user: LabUser = Depends(require_permission("dashboard:read")),
    db: Session = Depends(get_db),
):
    kpis = await engine.get_national_kpis(db, category)

    categories = list({k["kpi_category"] for k in kpis})

    return {
        "kpis": kpis,
        "categories": categories,
        "total": len(kpis),
    }


@router.get("/kpis/{kpi_name}/trend")
async def get_kpi_trend(
    kpi_name: str,
    days: int = Query(default=30, ge=1, le=365),
    current_user: LabUser = Depends(require_permission("dashboard:read")),
    db: Session = Depends(get_db),
):
    trend = await kpi_engine.get_kpi_trend(db, kpi_name, days)
    if not trend:
        raise HTTPException(status_code=404, detail=f"No data found for KPI: {kpi_name}")
    return {
        "kpi_name": kpi_name,
        "data_points": len(trend),
        "days": days,
        "trend": trend,
    }


@router.get("/incidents")
async def get_incidents(
    severity: str | None = Query(None),
    current_user: LabUser = Depends(require_permission("dashboard:read")),
    db: Session = Depends(get_db),
):
    incidents = await engine.get_active_incidents(db, severity)
    return {
        "incidents": incidents,
        "total": len(incidents),
    }


@router.post("/incidents", status_code=201)
async def report_incident(
    body: IncidentReport,
    current_user: LabUser = Depends(require_permission("system:admin")),
    db: Session = Depends(get_db),
):
    from .models import IncidentIntelligence

    incident = IncidentIntelligence(
        incident_type=body.incident_type,
        severity=body.severity,
        title=body.title,
        description=body.description,
        affected_entities=body.affected_entities or [],
        root_cause=body.root_cause,
        impact_analysis=body.impact_analysis or {},
        recommendation=body.recommendation or {},
        status="active",
        detected_at=datetime.now(UTC),
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    return {
        "id": incident.id,
        "incident_type": incident.incident_type,
        "severity": incident.severity,
        "title": incident.title,
        "status": incident.status,
        "detected_at": incident.detected_at.isoformat() if incident.detected_at else None,
    }


@router.get("/capacity")
async def get_capacity(
    entity_type: str | None = Query(None),
    current_user: LabUser = Depends(require_permission("dashboard:read")),
    db: Session = Depends(get_db),
):
    capacities = await engine.get_capacity_intelligence(db, entity_type)
    return {
        "capacities": capacities,
        "total": len(capacities),
    }


@router.post("/recommendations", status_code=201)
async def create_recommendation(
    body: RecommendationRequest,
    current_user: LabUser = Depends(require_permission("system:admin")),
    db: Session = Depends(get_db),
):
    context = body.model_dump()
    context["created_by"] = current_user.id
    return await engine.generate_recommendation(db, context)


@router.get("/executive-dashboard")
async def executive_dashboard(
    current_user: LabUser = Depends(require_permission("dashboard:read")),
    db: Session = Depends(get_db),
):
    situation = await engine.get_live_situation_room(db)
    health = await analyzer.analyze_national_health(db)
    readiness = await analyzer.compute_national_readiness(db)
    anomalies = await analyzer.detect_anomalies(db)

    return {
        "situation_room": situation["situation_status"],
        "national_health": health,
        "national_readiness": readiness,
        "anomalies": anomalies,
        "kpis": situation["kpis"],
        "active_incidents": situation["active_incidents"],
        "capacity": situation["capacity"],
        "pending_recommendations": situation["pending_recommendations"],
        "generated_at": datetime.now(UTC).isoformat(),
    }


@router.get("/regional/{region}/dashboard")
async def regional_dashboard(
    region: str,
    current_user: LabUser = Depends(require_permission("dashboard:read")),
    db: Session = Depends(get_db),
):
    situation = await engine.get_live_situation_room(db, region)
    health = await analyzer.analyze_regional_health(db, region)
    anomalies = await analyzer.detect_anomalies(db)
    region_anomalies = [a for a in anomalies if a.get("region") == region or "region" not in a]

    return {
        "region": region,
        "situation_room": situation["situation_status"],
        "regional_health": health,
        "regional_kpis": situation["kpis"],
        "active_incidents": situation["active_incidents"],
        "capacity": situation["capacity"],
        "anomalies": region_anomalies,
        "generated_at": datetime.now(UTC).isoformat(),
    }
