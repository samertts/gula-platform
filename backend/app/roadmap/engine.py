import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC

from .models import (
    ArchitectureDecision,
    Epic,
    EpicStatus,
    Milestone,
    Mission,
    MissionStatus,
    Priority,
    Program,
    ProgramStatus,
    Risk,
    RiskLevel,
    RoadmapTask,
    TaskStatus,
    TechnicalDebt,
)

logger = logging.getLogger("gula.roadmap.engine")


def _now():
    return datetime.now(UTC)


class RoadmapEngine:
    """Master Roadmap Engine - plans, tracks, and governs the entire GULA ecosystem evolution."""

    def __init__(self, db: Session, current_user=None):
        self.db = db
        self.current_user = current_user

    # ── Program management ─────────────────────────────────────────────────────

    def create_program(
        self,
        name: str,
        code: str,
        description: str | None = None,
        version: str | None = None,
        start_date: datetime | None = None,
        target_date: datetime | None = None,
        owner: str | None = None,
        budget: str | None = None,
        metadata_json: dict | None = None,
    ) -> Program:
        program = Program(
            name=name,
            code=code,
            description=description,
            status=ProgramStatus.PLANNING,
            version=version,
            start_date=start_date,
            target_date=target_date,
            owner=owner,
            budget=budget,
            metadata_json=metadata_json or {},
        )
        self.db.add(program)
        self.db.commit()
        self.db.refresh(program)
        logger.info("Roadmap program created: %s (%s)", program.name, program.code)
        return program

    def get_program(self, program_id: int) -> Program | None:
        return self.db.query(Program).filter(Program.id == program_id).first()

    def list_programs(self, status: ProgramStatus | None = None) -> list[Program]:
        q = self.db.query(Program)
        if status:
            q = q.filter(Program.status == status.value)
        return q.order_by(Program.created_at.desc()).all()

    def update_program_status(self, program_id: int, status: ProgramStatus) -> Program:
        program = self.get_program(program_id)
        if not program:
            raise ValueError(f"Program {program_id} not found")
        program.status = status.value
        if status == ProgramStatus.COMPLETED:
            program.completed_date = _now()
        program.updated_at = _now()
        self.db.commit()
        self.db.refresh(program)
        logger.info("Program %d status updated to %s", program_id, status.value)
        return program

    # ── Mission management ─────────────────────────────────────────────────────

    def create_mission(
        self,
        program_id: int,
        name: str,
        code: str,
        description: str | None = None,
        priority: Priority = Priority.MEDIUM,
        start_date: datetime | None = None,
        target_date: datetime | None = None,
        owner: str | None = None,
        risk_level: RiskLevel = RiskLevel.LOW,
        metadata_json: dict | None = None,
    ) -> Mission:
        mission = Mission(
            program_id=program_id,
            name=name,
            code=code,
            description=description,
            status=MissionStatus.PLANNING,
            priority=priority.value,
            start_date=start_date,
            target_date=target_date,
            owner=owner,
            risk_level=risk_level.value,
            metadata_json=metadata_json or {},
        )
        self.db.add(mission)
        self.db.commit()
        self.db.refresh(mission)
        logger.info(
            "Mission created: %s (%s) under program %d", mission.name, mission.code, program_id
        )
        return mission

    def get_mission(self, mission_id: int) -> Mission | None:
        return self.db.query(Mission).filter(Mission.id == mission_id).first()

    def get_missions_for_program(self, program_id: int) -> list[Mission]:
        return (
            self.db.query(Mission)
            .filter(Mission.program_id == program_id)
            .order_by(Mission.created_at.asc())
            .all()
        )

    def update_mission_status(self, mission_id: int, status: MissionStatus) -> Mission:
        mission = self.get_mission(mission_id)
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")
        mission.status = status.value
        if status == MissionStatus.COMPLETED:
            mission.completed_date = _now()
        mission.updated_at = _now()
        self.db.commit()
        self.db.refresh(mission)
        logger.info("Mission %d status updated to %s", mission_id, status.value)
        return mission

    # ── Epic & Task management ─────────────────────────────────────────────────

    def create_epic(
        self,
        mission_id: int,
        name: str,
        code: str,
        description: str | None = None,
        priority: Priority = Priority.MEDIUM,
        story_points: int | None = None,
        metadata_json: dict | None = None,
    ) -> Epic:
        epic = Epic(
            mission_id=mission_id,
            name=name,
            code=code,
            description=description,
            status=EpicStatus.BACKLOG,
            priority=priority.value,
            story_points=story_points,
            metadata_json=metadata_json or {},
        )
        self.db.add(epic)
        self.db.commit()
        self.db.refresh(epic)
        logger.info("Epic created: %s (%s) under mission %d", epic.name, epic.code, mission_id)
        return epic

    def create_task(
        self,
        epic_id: int,
        name: str,
        description: str | None = None,
        priority: Priority = Priority.MEDIUM,
        assignee: str | None = None,
        estimated_hours: float | None = None,
        dependencies: list[int] | None = None,
        metadata_json: dict | None = None,
    ) -> RoadmapTask:
        task = RoadmapTask(
            epic_id=epic_id,
            name=name,
            description=description,
            status=TaskStatus.TODO,
            priority=priority.value,
            assignee=assignee,
            estimated_hours=estimated_hours,
            dependencies=dependencies or [],
            metadata_json=metadata_json or {},
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        logger.info("Task created: %s under epic %d", task.name, epic_id)
        return task

    def update_task_status(self, task_id: int, status: TaskStatus) -> RoadmapTask:
        task = self.db.query(RoadmapTask).filter(RoadmapTask.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        old_status = task.status
        task.status = status.value
        task.updated_at = _now()
        if status == TaskStatus.IN_PROGRESS and old_status != TaskStatus.IN_PROGRESS.value:
            task.started_at = task.started_at or _now()
        if status == TaskStatus.DONE:
            task.completed_at = _now()
        self.db.commit()
        self.db.refresh(task)
        logger.info("Task %d status updated to %s", task_id, status.value)
        return task

    # ── Dependency graph ───────────────────────────────────────────────────────

    def get_dependency_graph(self, mission_id: int) -> dict[str, Any]:
        tasks = self.db.query(RoadmapTask).join(Epic).filter(Epic.mission_id == mission_id).all()
        nodes = []
        edges = []
        task_map = {t.id: t for t in tasks}
        for t in tasks:
            nodes.append(
                {
                    "id": t.id,
                    "name": t.name,
                    "status": t.status,
                    "epic_id": t.epic_id,
                }
            )
            deps = t.dependencies or []
            for dep_id in deps:
                if dep_id in task_map:
                    edges.append({"from": dep_id, "to": t.id})
        return {"nodes": nodes, "edges": edges}

    def check_dependency_cycle(self) -> list[list[int]]:
        tasks = self.db.query(RoadmapTask).all()
        adj = defaultdict(list)
        for t in tasks:
            deps = t.dependencies or []
            for d in deps:
                adj[t.id].append(d)

        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(list(path[cycle_start:]))
                    return True
            path.pop()
            rec_stack.discard(node)
            return False

        for t in tasks:
            if t.id not in visited:
                dfs(t.id)

        return cycles

    def get_critical_path(self, mission_id: int) -> list[RoadmapTask]:
        tasks = self.db.query(RoadmapTask).join(Epic).filter(Epic.mission_id == mission_id).all()
        if not tasks:
            return []

        task_map = {t.id: t for t in tasks}

        in_degree = {t.id: 0 for t in tasks}
        adj = defaultdict(list)
        for t in tasks:
            deps = t.dependencies or []
            for d in deps:
                if d in task_map:
                    adj[d].append(t.id)
                    in_degree[t.id] = in_degree.get(t.id, 0) + 1

        topo_queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
        topo_order = []
        while topo_queue:
            node = topo_queue.popleft()
            topo_order.append(node)
            for neighbor in adj.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    topo_queue.append(neighbor)

        est = {t.id: 0 for t in tasks}
        for tid in topo_order:
            for neighbor in adj.get(tid, []):
                hours = task_map[tid].estimated_hours or 0
                est[neighbor] = max(est[neighbor], est[tid] + hours)

        max_est = max(est.values()) if est else 0
        critical_ids = [tid for tid, e in est.items() if e == max_est]
        return [task_map[tid] for tid in critical_ids]

    # ── Analytics ──────────────────────────────────────────────────────────────

    def get_program_progress(self, program_id: int) -> dict[str, Any]:
        program = self.get_program(program_id)
        if not program:
            return {"error": "Program not found"}

        missions = self.get_missions_for_program(program_id)
        total_epics = 0
        total_tasks = 0
        completed_tasks = 0
        total_story_points = 0
        completed_story_points = 0

        for mission in missions:
            for epic in mission.epics:
                total_epics += 1
                if epic.story_points:
                    total_story_points += epic.story_points
                    if epic.status == EpicStatus.DONE.value:
                        completed_story_points += epic.story_points
                for task in epic.tasks:
                    total_tasks += 1
                    if task.status == TaskStatus.DONE.value:
                        completed_tasks += 1

        return {
            "program_id": program_id,
            "program_name": program.name,
            "program_status": program.status,
            "total_missions": len(missions),
            "total_epics": total_epics,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "task_completion_pct": round(completed_tasks / total_tasks * 100, 1)
            if total_tasks
            else 0,
            "total_story_points": total_story_points,
            "completed_story_points": completed_story_points,
            "story_points_pct": round(completed_story_points / total_story_points * 100, 1)
            if total_story_points
            else 0,
        }

    def get_mission_progress(self, mission_id: int) -> dict[str, Any]:
        mission = self.get_mission(mission_id)
        if not mission:
            return {"error": "Mission not found"}

        epics = self.db.query(Epic).filter(Epic.mission_id == mission_id).all()
        total_epics = len(epics)
        done_epics = sum(1 for e in epics if e.status == EpicStatus.DONE.value)
        total_tasks = 0
        done_tasks = 0
        blocked_tasks = 0
        total_hours = 0.0
        completed_hours = 0.0

        for epic in epics:
            for task in epic.tasks:
                total_tasks += 1
                if task.status == TaskStatus.DONE.value:
                    done_tasks += 1
                if task.status == TaskStatus.BLOCKED.value:
                    blocked_tasks += 1
                if task.estimated_hours:
                    total_hours += task.estimated_hours
                    if task.status == TaskStatus.DONE.value and task.actual_hours:
                        completed_hours += task.actual_hours
                    elif task.status == TaskStatus.DONE.value:
                        completed_hours += task.estimated_hours

        return {
            "mission_id": mission_id,
            "mission_name": mission.name,
            "mission_status": mission.status,
            "total_epics": total_epics,
            "done_epics": done_epics,
            "epic_completion_pct": round(done_epics / total_epics * 100, 1) if total_epics else 0,
            "total_tasks": total_tasks,
            "done_tasks": done_tasks,
            "blocked_tasks": blocked_tasks,
            "task_completion_pct": round(done_tasks / total_tasks * 100, 1) if total_tasks else 0,
            "estimated_hours": round(total_hours, 1),
            "completed_hours": round(completed_hours, 1),
        }

    def get_risk_matrix(self, program_id: int) -> list[dict[str, Any]]:
        missions = self.get_missions_for_program(program_id)
        risks = []
        for mission in missions:
            for risk in mission.risks:
                risks.append(
                    {
                        "risk_id": risk.id,
                        "mission_id": mission.id,
                        "mission_name": mission.name,
                        "description": risk.description,
                        "risk_level": risk.risk_level,
                        "probability": risk.probability,
                        "impact": risk.impact,
                        "score": round((risk.probability or 0) * (risk.impact or 0), 2),
                        "mitigation": risk.mitigation,
                        "status": risk.status,
                        "owner": risk.owner,
                    }
                )
        return sorted(risks, key=lambda r: r["score"], reverse=True)

    def get_technical_debt_summary(self) -> dict[str, Any]:
        debts = self.db.query(TechnicalDebt).all()
        by_severity = defaultdict(int)
        by_component = defaultdict(int)
        total_effort = 0.0
        resolved = 0

        for d in debts:
            by_severity[d.severity] += 1
            by_component[d.component] += 1
            if d.estimated_effort_hours:
                total_effort += d.estimated_effort_hours
            if d.status == "RESOLVED":
                resolved += 1

        return {
            "total_items": len(debts),
            "resolved": resolved,
            "open": len(debts) - resolved,
            "by_severity": dict(by_severity),
            "by_component": dict(by_component),
            "total_estimated_effort_hours": round(total_effort, 1),
        }

    def get_velocity(self, program_id: int, sprint_days: int = 14) -> float:
        cutoff = _now() - timedelta(days=sprint_days)
        completed = (
            self.db.query(func.count(RoadmapTask.id))
            .join(Epic)
            .join(Mission)
            .filter(
                Mission.program_id == program_id,
                RoadmapTask.completed_at >= cutoff,
            )
            .scalar()
            or 0
        )
        return round(completed / max(sprint_days / 7, 1), 1)

    # ── Milestones ─────────────────────────────────────────────────────────────

    def create_milestone(
        self,
        mission_id: int,
        name: str,
        target_date: datetime,
        description: str | None = None,
        metadata_json: dict | None = None,
    ) -> Milestone:
        milestone = Milestone(
            mission_id=mission_id,
            name=name,
            target_date=target_date,
            description=description,
            status="PENDING",
            metadata_json=metadata_json or {},
        )
        self.db.add(milestone)
        self.db.commit()
        self.db.refresh(milestone)
        logger.info("Milestone created: %s for mission %d", milestone.name, mission_id)
        return milestone

    def get_upcoming_milestones(self, days: int = 30) -> list[Milestone]:
        cutoff = _now() + timedelta(days=days)
        return (
            self.db.query(Milestone)
            .filter(
                Milestone.target_date <= cutoff,
                Milestone.status == "PENDING",
            )
            .order_by(Milestone.target_date.asc())
            .all()
        )

    # ── Risks ──────────────────────────────────────────────────────────────────

    def create_risk(
        self,
        mission_id: int,
        description: str,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        probability: float | None = None,
        impact: float | None = None,
        mitigation: str | None = None,
        owner: str | None = None,
    ) -> Risk:
        risk = Risk(
            mission_id=mission_id,
            description=description,
            risk_level=risk_level.value,
            probability=probability,
            impact=impact,
            mitigation=mitigation,
            status="OPEN",
            owner=owner,
        )
        self.db.add(risk)
        self.db.commit()
        self.db.refresh(risk)
        logger.info("Risk created for mission %d: level=%s", mission_id, risk_level.value)
        return risk

    # ── Architecture decisions ─────────────────────────────────────────────────

    def create_adr(
        self,
        title: str,
        context: str,
        decision: str,
        consequences: str | None = None,
        domain: str | None = None,
        created_by: str | None = None,
        approved_by: str | None = None,
        superseded_by: int | None = None,
    ) -> ArchitectureDecision:
        adr = ArchitectureDecision(
            title=title,
            context=context,
            decision=decision,
            consequences=consequences,
            status="PROPOSED",
            domain=domain,
            created_by=created_by,
            approved_by=approved_by,
            superseded_by=superseded_by,
        )
        self.db.add(adr)
        self.db.commit()
        self.db.refresh(adr)
        logger.info("ADR created: %s (domain=%s, status=PROPOSED)", adr.title, adr.domain)
        return adr

    def get_adr(self, adr_id: int) -> ArchitectureDecision | None:
        return self.db.query(ArchitectureDecision).filter(ArchitectureDecision.id == adr_id).first()

    def list_adrs(self, domain: str | None = None) -> list[ArchitectureDecision]:
        q = self.db.query(ArchitectureDecision)
        if domain:
            q = q.filter(ArchitectureDecision.domain == domain)
        return q.order_by(ArchitectureDecision.created_at.desc()).all()

    # ── Dashboard ──────────────────────────────────────────────────────────────

    def get_executive_dashboard(self) -> dict[str, Any]:
        programs = self.db.query(Program).all()
        total_programs = len(programs)
        active_programs = sum(1 for p in programs if p.status == ProgramStatus.ACTIVE.value)
        completed_programs = sum(1 for p in programs if p.status == ProgramStatus.COMPLETED.value)

        missions = self.db.query(Mission).all()
        total_missions = len(missions)
        completed_missions = sum(1 for m in missions if m.status == MissionStatus.COMPLETED.value)
        blocked_missions = sum(1 for m in missions if m.status == MissionStatus.BLOCKED.value)

        epics = self.db.query(Epic).all()
        total_epics = len(epics)
        done_epics = sum(1 for e in epics if e.status == EpicStatus.DONE.value)

        tasks = self.db.query(RoadmapTask).all()
        total_tasks = len(tasks)
        done_tasks = sum(1 for t in tasks if t.status == TaskStatus.DONE.value)
        blocked_tasks = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED.value)

        risks = self.db.query(Risk).all()
        open_risks = sum(1 for r in risks if r.status == "OPEN")
        high_risks = sum(
            1 for r in risks if r.risk_level in (RiskLevel.HIGH.value, RiskLevel.CRITICAL.value)
        )

        debts = self.db.query(TechnicalDebt).all()
        open_debt = sum(1 for d in debts if d.status != "RESOLVED")

        upcoming = self.get_upcoming_milestones(days=30)

        return {
            "programs": {
                "total": total_programs,
                "active": active_programs,
                "completed": completed_programs,
            },
            "missions": {
                "total": total_missions,
                "completed": completed_missions,
                "blocked": blocked_missions,
                "completion_pct": round(completed_missions / total_missions * 100, 1)
                if total_missions
                else 0,
            },
            "epics": {
                "total": total_epics,
                "done": done_epics,
                "completion_pct": round(done_epics / total_epics * 100, 1) if total_epics else 0,
            },
            "tasks": {
                "total": total_tasks,
                "done": done_tasks,
                "blocked": blocked_tasks,
                "completion_pct": round(done_tasks / total_tasks * 100, 1) if total_tasks else 0,
            },
            "risks": {
                "total": len(risks),
                "open": open_risks,
                "high_or_critical": high_risks,
            },
            "technical_debt": {
                "total": len(debts),
                "open": open_debt,
            },
            "upcoming_milestones_30d": len(upcoming),
            "generated_at": _now().isoformat(),
        }
