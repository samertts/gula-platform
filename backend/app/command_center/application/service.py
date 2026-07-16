from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.command_center.domain.entities import (
    AfterActionReport,
    EmergencyDeclaration,
    ResourceRequest,
    SituationReport,
)
from app.command_center.exceptions import (
    EmergencyNotFoundError,
    ResourceRequestNotFoundError,
)
from app.command_center.infrastructure.models import (
    AfterActionReportModel,
    EmergencyDeclarationModel,
    ResourceRequestModel,
    SituationReportModel,
)
from app.national.events.base import NationalDomainEvent

logger = logging.getLogger("gula.command_center")


class CommandCenterService:
    def __init__(self, db: Session, event_bus: Any = None):
        self.db = db
        self.event_bus = event_bus

    def _emit(self, event: NationalDomainEvent) -> None:
        if self.event_bus:
            self.event_bus.emit(event.event_type, event.__dict__)

    # ── Emergency Declaration ──

    def declare_emergency(self, data: dict[str, Any]) -> EmergencyDeclaration:
        model = EmergencyDeclarationModel(**{k: v for k, v in data.items() if hasattr(EmergencyDeclarationModel, k)})
        model.status = "active"
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._emergency_from_model(model)

    def get_emergency(self, emergency_id: str) -> EmergencyDeclaration:
        model = self.db.query(EmergencyDeclarationModel).filter_by(id=emergency_id).first()
        if not model or model.is_deleted:
            raise EmergencyNotFoundError()
        return self._emergency_from_model(model)

    def list_emergencies(self, status: str | None = None, emergency_type: str | None = None,
                         region: str | None = None, skip: int = 0, limit: int = 100) -> list[EmergencyDeclaration]:
        query = self.db.query(EmergencyDeclarationModel).filter(EmergencyDeclarationModel.is_deleted.isnot(True))
        if status:
            query = query.filter_by(status=status)
        if emergency_type:
            query = query.filter_by(emergency_type=emergency_type)
        if region:
            query = query.filter_by(region=region)
        query = query.order_by(EmergencyDeclarationModel.declared_at.desc()).offset(skip).limit(limit)
        return [self._emergency_from_model(m) for m in query.all()]

    def resolve_emergency(self, emergency_id: str, resolved_by: str = "",
                          notes: str = "") -> EmergencyDeclaration:
        model = self.db.query(EmergencyDeclarationModel).filter_by(id=emergency_id).first()
        if not model:
            raise EmergencyNotFoundError()
        model.status = "resolved"
        model.resolved_at = datetime.now(UTC)
        model.resolved_by = resolved_by
        if notes:
            model.situation_summary = (model.situation_summary or "") + f"\n[RESOLVED] {notes}"
        self.db.commit()
        self.db.refresh(model)
        return self._emergency_from_model(model)

    # ── Resource Requests ──

    def request_resource(self, data: dict[str, Any]) -> ResourceRequest:
        model = ResourceRequestModel(**{k: v for k, v in data.items() if hasattr(ResourceRequestModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._resource_from_model(model)

    def list_resource_requests(self, emergency_id: str | None = None,
                               status: str | None = None, skip: int = 0, limit: int = 100) -> list[ResourceRequest]:
        query = self.db.query(ResourceRequestModel).filter(ResourceRequestModel.is_deleted.isnot(True))
        if emergency_id:
            query = query.filter_by(emergency_id=emergency_id)
        if status:
            query = query.filter_by(status=status)
        query = query.order_by(ResourceRequestModel.requested_at.desc()).offset(skip).limit(limit)
        return [self._resource_from_model(m) for m in query.all()]

    def fulfill_resource(self, request_id: str, data: dict[str, Any]) -> ResourceRequest:
        model = self.db.query(ResourceRequestModel).filter_by(id=request_id).first()
        if not model:
            raise ResourceRequestNotFoundError()
        model.status = "fulfilled"
        model.fulfilled_quantity = data.get("fulfilled_quantity", model.quantity)
        model.fulfilled_by = data.get("fulfilled_by", "")
        model.fulfilled_at = datetime.now(UTC)
        model.source = data.get("source", "")
        model.notes = data.get("notes", "")
        self.db.commit()
        self.db.refresh(model)
        return self._resource_from_model(model)

    # ── Situation Reports ──

    def publish_situation_report(self, data: dict[str, Any]) -> SituationReport:
        model = SituationReportModel(**{k: v for k, v in data.items() if hasattr(SituationReportModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._situation_from_model(model)

    def list_situation_reports(self, emergency_id: str | None = None,
                               skip: int = 0, limit: int = 100) -> list[SituationReport]:
        query = self.db.query(SituationReportModel).filter(SituationReportModel.is_deleted.isnot(True))
        if emergency_id:
            query = query.filter_by(emergency_id=emergency_id)
        query = query.order_by(SituationReportModel.published_at.desc()).offset(skip).limit(limit)
        return [self._situation_from_model(m) for m in query.all()]

    # ── After-Action Reports ──

    def complete_after_action(self, data: dict[str, Any]) -> AfterActionReport:
        model = AfterActionReportModel(**{k: v for k, v in data.items() if hasattr(AfterActionReportModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._after_action_from_model(model)

    def list_after_action_reports(self, skip: int = 0, limit: int = 100) -> list[AfterActionReport]:
        query = self.db.query(AfterActionReportModel).filter(
            AfterActionReportModel.is_deleted.isnot(True)
        ).order_by(AfterActionReportModel.completed_at.desc()).offset(skip).limit(limit)
        return [self._after_action_from_model(m) for m in query.all()]

    # ── Unified Dashboard (integrates existing modules) ──

    def get_unified_command_dashboard(self) -> dict[str, Any]:
        now = datetime.now(UTC)

        active_emergencies = self.db.query(EmergencyDeclarationModel).filter(
            EmergencyDeclarationModel.status == "active",
            EmergencyDeclarationModel.is_deleted.isnot(True),
        ).count()

        try:
            from app.command_intelligence.engine import CommandIntelligenceEngine
            ci = CommandIntelligenceEngine(self.db)
            situation = ci.get_live_situation_room()
            ci.get_national_kpis()
            readiness = situation.get("national_readiness", 0) if isinstance(situation, dict) else 0
        except Exception as e:
            logger.warning("Command intelligence integration: %s", e)
            situation = {}
            readiness = 0

        try:
            from app.ems.application.service import EMSService
            ems = EMSService(self.db)
            ems_dashboard = ems.get_dashboard_stats()
            ems_active = ems_dashboard.get("active_incidents", 0)
            ambulances = ems_dashboard.get("available_ambulances", 0)
        except Exception:
            ems_active = 0
            ambulances = 0

        try:
            from app.critical_care.application.service import CriticalCareService
            cc = CriticalCareService(self.db)
            cc_stats = cc.get_dashboard_stats()
            icu_occupancy = cc_stats.get("occupancy_pct", 0)
            ventilators = cc_stats.get("available_ventilators", 0)
            beds = cc_stats.get("available_beds", 0)
        except Exception:
            icu_occupancy = 0
            ventilators = 0
            beds = 0

        try:
            from app.blood_bank.application.service import BloodBankService
            bb = BloodBankService(self.db)
            bb_stats = bb.get_dashboard_stats()
            blood_units = bb_stats.get("available_units", 0)
        except Exception:
            blood_units = 0

        try:
            from app.public_health.application.service import PublicHealthService
            ph = PublicHealthService(self.db)
            ph_dash = ph.get_dashboard()
            active_outbreaks = ph_dash.get("active_outbreaks", 0)
        except Exception:
            active_outbreaks = 0

        twenty_four_hours_ago = now - timedelta(hours=24)
        critical_alerts = 0
        try:
            from app.models.outbox import OutboxEvent
            alert_models = self.db.query(OutboxEvent).filter(
                OutboxEvent.created_at >= twenty_four_hours_ago,
                OutboxEvent.event_type == "critical_alert",
            ).count()
            critical_alerts = alert_models
        except Exception:
            pass

        return {
            "overall_status": "red" if active_emergencies > 0 else "green",
            "active_emergencies": active_emergencies,
            "active_outbreaks": active_outbreaks,
            "icus_occupancy_pct": icu_occupancy,
            "ventilators_available": ventilators,
            "blood_units_available": blood_units,
            "ambulances_available": ambulances,
            "ems_incidents_active": ems_active,
            "critical_alerts_last_24h": critical_alerts,
            "beds_available": beds,
            "national_readiness_score": readiness,
            "situation_room": situation if isinstance(situation, dict) else {},
            "timestamp": now.isoformat(),
        }

    def _emergency_from_model(self, m: EmergencyDeclarationModel) -> EmergencyDeclaration:
        return EmergencyDeclaration(
            id=m.id, emergency_type=m.emergency_type, level=m.level or "level_1_minor",
            status=m.status or "standby", region=m.region,
            declared_by=m.declared_by or "",
            declared_at=m.declared_at.isoformat() if m.declared_at else "",
            description=m.description or "",
        )

    def _resource_from_model(self, m: ResourceRequestModel) -> ResourceRequest:
        return ResourceRequest(
            id=m.id, emergency_id=m.emergency_id or "",
            resource_type=m.resource_type, quantity=m.quantity or 1,
            priority=m.priority or "medium", status=m.status or "pending",
            requested_by=m.requested_by or "",
            requested_at=m.requested_at.isoformat() if m.requested_at else "",
        )

    def _situation_from_model(self, m: SituationReportModel) -> SituationReport:
        return SituationReport(
            id=m.id, emergency_id=m.emergency_id or "",
            report_number=m.report_number or 1, summary=m.summary or "",
            published_by=m.published_by or "",
            published_at=m.published_at.isoformat() if m.published_at else "",
        )

    def _after_action_from_model(self, m: AfterActionReportModel) -> AfterActionReport:
        return AfterActionReport(
            id=m.id, emergency_id=m.emergency_id or "",
            emergency_type=m.emergency_type or "", region=m.region or "",
            overall_rating=m.overall_rating or "satisfactory",
            completed_by=m.completed_by or "",
        )
