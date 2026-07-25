from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.pilot_platform.domain.entities import (
    DeploymentRecord,
    GoNoGoGate,
    PilotFacility,
    PilotProgram,
    ReadinessChecklist,
)
from app.pilot_platform.exceptions import (
    PilotNotFoundError,
    ReadinessAssessmentNotFoundError,
)
from app.pilot_platform.infrastructure.models import (
    DeploymentRecordModel,
    GoNoGoGateModel,
    PilotFacilityModel,
    PilotProgramModel,
    ReadinessChecklistModel,
)

logger = logging.getLogger("gula.pilot_platform")


class PilotPlatformService:
    def __init__(self, db: Session, event_bus: Any = None):
        self.db = db
        self.event_bus = event_bus

    # ── Pilot Programs ──

    def create_pilot(self, data: dict[str, Any]) -> PilotProgram:
        model = PilotProgramModel(
            **{k: v for k, v in data.items() if hasattr(PilotProgramModel, k)}
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._program_from_model(model)

    def get_pilot(self, pilot_id: str) -> PilotProgram:
        model = self.db.query(PilotProgramModel).filter_by(id=pilot_id).first()
        if not model or model.is_deleted:
            raise PilotNotFoundError()
        return self._program_from_model(model)

    def list_pilots(
        self,
        status: str | None = None,
        module_name: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PilotProgram]:
        query = self.db.query(PilotProgramModel).filter(PilotProgramModel.is_deleted.isnot(True))
        if status:
            query = query.filter_by(status=status)
        if module_name:
            query = query.filter_by(module_name=module_name)
        query = query.order_by(PilotProgramModel.created_at.desc()).offset(skip).limit(limit)
        return [self._program_from_model(m) for m in query.all()]

    def advance_phase(self, pilot_id: str, phase: str) -> PilotProgram:
        model = self.db.query(PilotProgramModel).filter_by(id=pilot_id).first()
        if not model:
            raise PilotNotFoundError()
        model.current_phase = phase
        self.db.commit()
        self.db.refresh(model)
        return self._program_from_model(model)

    # ── Pilot Facilities ──

    def enroll_facility(self, data: dict[str, Any]) -> PilotFacility:
        model = PilotFacilityModel(
            **{k: v for k, v in data.items() if hasattr(PilotFacilityModel, k)}
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._facility_from_model(model)

    def list_pilot_facilities(
        self, pilot_id: str, skip: int = 0, limit: int = 100
    ) -> list[PilotFacility]:
        query = (
            self.db.query(PilotFacilityModel)
            .filter(
                PilotFacilityModel.pilot_id == pilot_id,
                PilotFacilityModel.is_deleted.isnot(True),
            )
            .offset(skip)
            .limit(limit)
        )
        return [self._facility_from_model(m) for m in query.all()]

    # ── Readiness Assessments ──

    def assess_readiness(self, data: dict[str, Any]) -> ReadinessChecklist:
        items = data.get("items", [])
        total = sum(item.get("score", 0) for item in items)
        max_score = len(items) * 100
        overall_score = round((total / max_score) * 100, 1) if max_score > 0 else 0

        if overall_score >= 90:
            level = "certified"
        elif overall_score >= 75:
            level = "ready"
        elif overall_score >= 50:
            level = "conditional"
        else:
            level = "not_ready"

        model = ReadinessChecklistModel(
            pilot_id=data.get("pilot_id", ""),
            facility_id=data.get("facility_id", ""),
            items=items,
            overall_score=overall_score,
            level=level,
            assessed_by=data.get("assessed_by", ""),
            assessed_at=datetime.now(UTC),
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        fac = (
            self.db.query(PilotFacilityModel)
            .filter_by(
                pilot_id=data.get("pilot_id", ""),
                facility_id=data.get("facility_id", ""),
            )
            .first()
        )
        if fac:
            fac.readiness_level = level
            fac.readiness_score = overall_score
            self.db.commit()

        return ReadinessChecklist(
            id=model.id,
            pilot_id=model.pilot_id or "",
            facility_id=model.facility_id or "",
            overall_score=overall_score,
            level=level,
            assessed_by=model.assessed_by or "",
        )

    def get_facility_readiness(self, facility_id: str, pilot_id: str) -> ReadinessChecklist:
        model = (
            self.db.query(ReadinessChecklistModel)
            .filter_by(
                facility_id=facility_id,
                pilot_id=pilot_id,
            )
            .order_by(ReadinessChecklistModel.assessed_at.desc())
            .first()
        )
        if not model:
            raise ReadinessAssessmentNotFoundError()
        return ReadinessChecklist(
            id=model.id,
            pilot_id=model.pilot_id or "",
            facility_id=model.facility_id or "",
            overall_score=model.overall_score or 0.0,
            level=model.level or "not_ready",
            assessed_by=model.assessed_by or "",
        )

    # ── Go/No-Go Gates ──

    def decide_gate(self, data: dict[str, Any]) -> GoNoGoGate:
        model = GoNoGoGateModel(**{k: v for k, v in data.items() if hasattr(GoNoGoGateModel, k)})
        model.decided_at = datetime.now(UTC)
        self.db.add(model)

        if data.get("result") == "passed" and data.get("facility_id"):
            fac = (
                self.db.query(PilotFacilityModel)
                .filter_by(
                    pilot_id=data.get("pilot_id", ""),
                    facility_id=data.get("facility_id", ""),
                )
                .first()
            )
            if fac:
                fac.go_no_go_approved = True
                self.db.commit()

        self.db.commit()
        self.db.refresh(model)
        return GoNoGoGate(
            id=model.id,
            pilot_id=model.pilot_id or "",
            facility_id=model.facility_id or "",
            gate_name=model.gate_name,
            result=model.result or "not_run",
            approver=model.approver or "",
            comments=model.comments or "",
        )

    def list_gates(self, pilot_id: str, facility_id: str | None = None) -> list[GoNoGoGate]:
        query = self.db.query(GoNoGoGateModel).filter(
            GoNoGoGateModel.pilot_id == pilot_id,
            GoNoGoGateModel.is_deleted.isnot(True),
        )
        if facility_id:
            query = query.filter_by(facility_id=facility_id)
        return [
            GoNoGoGate(
                id=m.id,
                pilot_id=m.pilot_id or "",
                facility_id=m.facility_id or "",
                gate_name=m.gate_name,
                result=m.result or "not_run",
                approver=m.approver or "",
                comments=m.comments or "",
            )
            for m in query.all()
        ]

    # ── Deployment Records ──

    def record_deployment(self, data: dict[str, Any]) -> DeploymentRecord:
        model = DeploymentRecordModel(
            **{k: v for k, v in data.items() if hasattr(DeploymentRecordModel, k)}
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._deployment_from_model(model)

    def list_deployments(
        self, pilot_id: str | None = None, facility_id: str | None = None
    ) -> list[DeploymentRecord]:
        query = self.db.query(DeploymentRecordModel).filter(
            DeploymentRecordModel.is_deleted.isnot(True)
        )
        if pilot_id:
            query = query.filter_by(pilot_id=pilot_id)
        if facility_id:
            query = query.filter_by(facility_id=facility_id)
        return [
            self._deployment_from_model(m)
            for m in query.order_by(DeploymentRecordModel.deployed_at.desc()).all()
        ]

    # ── Certification Integration ──

    def evaluate_with_certification(self, module_path: str, pilot_id: str) -> dict[str, Any]:
        try:
            from app.certification.engine import CertificationEngine

            engine = CertificationEngine(self.db)
            result = engine.evaluate(module_path)
            level = result.get("overall_level", "bronze")
            return {
                "module": module_path,
                "certification_level": level,
                "score": result.get("overall_score", 0),
                "dimensions": result.get("dimensions", []),
            }
        except Exception as e:
            logger.warning("Certification evaluation failed: %s", e)
            return {"module": module_path, "certification_level": "unknown", "error": str(e)}

    # ── Dashboard ──

    def get_dashboard(self) -> dict[str, Any]:
        total_pilots = (
            self.db.query(PilotProgramModel)
            .filter(PilotProgramModel.is_deleted.isnot(True))
            .count()
        )
        active_pilots = (
            self.db.query(PilotProgramModel)
            .filter_by(status="in_progress", is_deleted=False)
            .count()
        )
        completed = (
            self.db.query(PilotProgramModel).filter_by(status="completed", is_deleted=False).count()
        )
        facilities_enrolled = (
            self.db.query(PilotFacilityModel)
            .filter(PilotFacilityModel.is_deleted.isnot(True))
            .count()
        )
        facilities_certified = (
            self.db.query(PilotFacilityModel)
            .filter(
                PilotFacilityModel.readiness_level == "certified",
                PilotFacilityModel.is_deleted.isnot(True),
            )
            .count()
        )

        return {
            "total_pilots": total_pilots,
            "active_pilots": active_pilots,
            "completed_pilots": completed,
            "facilities_enrolled": facilities_enrolled,
            "facilities_certified": facilities_certified,
        }

    def _program_from_model(self, m: PilotProgramModel) -> PilotProgram:
        return PilotProgram(
            id=m.id,
            module_name=m.module_name,
            version=m.version,
            current_phase=m.current_phase or "planned",
            status=m.status or "planned",
            strategy=m.strategy or "canary",
            pilot_lead=m.pilot_lead or "",
            description=m.description or "",
        )

    def _facility_from_model(self, m: PilotFacilityModel) -> PilotFacility:
        return PilotFacility(
            id=m.id,
            pilot_id=m.pilot_id,
            facility_id=m.facility_id,
            facility_name=m.facility_name or "",
            readiness_level=m.readiness_level or "not_ready",
            readiness_score=m.readiness_score or 0.0,
        )

    def _deployment_from_model(self, m: DeploymentRecordModel) -> DeploymentRecord:
        return DeploymentRecord(
            id=m.id,
            pilot_id=m.pilot_id,
            module=m.module or "",
            version=m.version or "",
            facility_id=m.facility_id or "",
            strategy=m.strategy or "",
            status=m.status or "pending",
            deployed_by=m.deployed_by or "",
            health_check_passed=m.health_check_passed or False,
        )
