import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..security.dependencies import get_current_user
from .engine import RoadmapEngine
from .models import (
    MissionStatus,
    Priority,
    ProgramStatus,
    RiskLevel,
    TaskStatus,
    TechnicalDebt,
)

logger = logging.getLogger("gula.roadmap")

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


# ── Pydantic schemas ────────────────────────────────────────────────────────


class ProgramCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    version: str | None = None
    start_date: datetime | None = None
    target_date: datetime | None = None
    owner: str | None = None
    budget: str | None = None
    metadata_json: dict | None = None


class ProgramStatusUpdate(BaseModel):
    status: ProgramStatus


class MissionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    priority: Priority = Priority.MEDIUM
    start_date: datetime | None = None
    target_date: datetime | None = None
    owner: str | None = None
    risk_level: RiskLevel = RiskLevel.LOW
    metadata_json: dict | None = None


class MissionStatusUpdate(BaseModel):
    status: MissionStatus


class EpicCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    priority: Priority = Priority.MEDIUM
    story_points: int | None = None
    metadata_json: dict | None = None


class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    priority: Priority = Priority.MEDIUM
    assignee: str | None = None
    estimated_hours: float | None = None
    dependencies: list[int] | None = None
    metadata_json: dict | None = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class MilestoneCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    target_date: datetime
    description: str | None = None
    metadata_json: dict | None = None


class RiskCreate(BaseModel):
    description: str = Field(..., min_length=1)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    probability: float | None = Field(None, ge=0, le=1)
    impact: float | None = Field(None, ge=0, le=1)
    mitigation: str | None = None
    owner: str | None = None


class TechnicalDebtCreate(BaseModel):
    component: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    severity: Priority = Priority.MEDIUM
    estimated_effort_hours: float | None = None
    identified_by: str | None = None
    metadata_json: dict | None = None


class ADRCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    context: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    consequences: str | None = None
    domain: str | None = None
    created_by: str | None = None
    approved_by: str | None = None
    superseded_by: int | None = None


# ── Helper ──────────────────────────────────────────────────────────────────


def _engine(db: Session, current_user=None) -> RoadmapEngine:
    return RoadmapEngine(db=db, current_user=current_user)


# ── Program endpoints ───────────────────────────────────────────────────────


@router.post("/programs", status_code=201)
def create_program(
    body: ProgramCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.create_program(**body.model_dump())


@router.get("/programs")
def list_programs(
    status: ProgramStatus | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.list_programs(status=status)


@router.get("/programs/{program_id}")
def get_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    program = eng.get_program(program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    progress = eng.get_program_progress(program_id)
    return {**program.__dict__, "progress": progress}


@router.patch("/programs/{program_id}/status")
def update_program_status(
    program_id: int,
    body: ProgramStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    try:
        return eng.update_program_status(program_id, body.status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Resource not found") from e


# ── Mission endpoints ───────────────────────────────────────────────────────


@router.post("/programs/{program_id}/missions", status_code=201)
def create_mission(
    program_id: int,
    body: MissionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.create_mission(program_id=program_id, **body.model_dump())


@router.get("/programs/{program_id}/missions")
def list_missions(
    program_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    missions = eng.get_missions_for_program(program_id)
    result = []
    for m in missions:
        progress = eng.get_mission_progress(m.id)
        result.append({**m.__dict__, "progress": progress})
    return result


@router.get("/missions/{mission_id}")
def get_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    mission = eng.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    progress = eng.get_mission_progress(mission_id)
    critical = eng.get_critical_path(mission_id)
    return {
        **mission.__dict__,
        "progress": progress,
        "critical_path": [
            {"id": t.id, "name": t.name, "status": t.status, "estimated_hours": t.estimated_hours}
            for t in critical
        ],
    }


@router.patch("/missions/{mission_id}/status")
def update_mission_status(
    mission_id: int,
    body: MissionStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    try:
        return eng.update_mission_status(mission_id, body.status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Resource not found") from e


# ── Epic & Task endpoints ───────────────────────────────────────────────────


@router.post("/missions/{mission_id}/epics", status_code=201)
def create_epic(
    mission_id: int,
    body: EpicCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.create_epic(mission_id=mission_id, **body.model_dump())


@router.post("/epics/{epic_id}/tasks", status_code=201)
def create_task(
    epic_id: int,
    body: TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.create_task(epic_id=epic_id, **body.model_dump())


@router.patch("/tasks/{task_id}/status")
def update_task_status(
    task_id: int,
    body: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    try:
        return eng.update_task_status(task_id, body.status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Resource not found") from e


# ── Critical path & dependency graph ────────────────────────────────────────


@router.get("/missions/{mission_id}/critical-path")
def get_critical_path(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.get_critical_path(mission_id)


@router.get("/missions/{mission_id}/dependency-graph")
def get_dependency_graph(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.get_dependency_graph(mission_id)


# ── Milestone endpoints ─────────────────────────────────────────────────────


@router.post("/missions/{mission_id}/milestones", status_code=201)
def create_milestone(
    mission_id: int,
    body: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.create_milestone(mission_id=mission_id, **body.model_dump())


@router.get("/milestones/upcoming")
def get_upcoming_milestones(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.get_upcoming_milestones(days=days)


# ── Risk endpoints ──────────────────────────────────────────────────────────


@router.post("/missions/{mission_id}/risks", status_code=201)
def create_risk(
    mission_id: int,
    body: RiskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.create_risk(mission_id=mission_id, **body.model_dump())


@router.get("/risks/matrix")
def get_risk_matrix(
    program_id: int = Query(..., description="Filter risks by program ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.get_risk_matrix(program_id)


# ── Technical debt endpoints ────────────────────────────────────────────────


@router.post("/technical-debt", status_code=201)
def create_technical_debt(
    body: TechnicalDebtCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    debt = TechnicalDebt(
        component=body.component,
        description=body.description,
        severity=body.severity.value,
        estimated_effort_hours=body.estimated_effort_hours,
        identified_by=body.identified_by,
        metadata_json=body.metadata_json or {},
    )
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return debt


@router.get("/technical-debt")
def get_technical_debt_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.get_technical_debt_summary()


# ── ADR endpoints ───────────────────────────────────────────────────────────


@router.post("/adrs", status_code=201)
def create_adr(
    body: ADRCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.create_adr(**body.model_dump())


@router.get("/adrs")
def list_adrs(
    domain: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.list_adrs(domain=domain)


# ── Executive dashboard ─────────────────────────────────────────────────────


@router.get("/executive-dashboard")
def get_executive_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    eng = _engine(db, current_user)
    return eng.get_executive_dashboard()
