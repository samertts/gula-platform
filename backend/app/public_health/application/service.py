from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.national.events.base import NationalDomainEvent
from app.public_health.domain.entities import (
    DiseaseCase,
    ImmunizationRecord,
    OutbreakAlert,
    PublicHealthReport,
    SurveillanceSignal,
)
from app.public_health.domain.enums import AlertLevel, OutbreakStatus
from app.public_health.exceptions import (
    DiseaseCaseNotFoundError,
    OutbreakNotFoundError,
)
from app.public_health.infrastructure.models import (
    DiseaseCaseModel,
    ImmunizationRecordModel,
    OutbreakAlertModel,
    PublicHealthReportModel,
    SurveillanceSignalModel,
)


class PublicHealthService:
    def __init__(self, db: Session, event_bus: Any = None):
        self.db = db
        self.event_bus = event_bus

    def _emit(self, event: NationalDomainEvent) -> None:
        if self.event_bus:
            self.event_bus.emit(event.event_type, event.__dict__)

    # ── Disease Cases ──

    def report_case(self, data: dict[str, Any]) -> DiseaseCase:
        model = DiseaseCaseModel(**{k: v for k, v in data.items() if hasattr(DiseaseCaseModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._case_from_model(model)

    def get_case(self, case_id: str) -> DiseaseCase:
        model = self.db.query(DiseaseCaseModel).filter_by(id=case_id).first()
        if not model or model.is_deleted:
            raise DiseaseCaseNotFoundError()
        return self._case_from_model(model)

    def list_cases(
        self,
        disease_code: str | None = None,
        region: str | None = None,
        is_confirmed: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DiseaseCase]:
        query = self.db.query(DiseaseCaseModel).filter(DiseaseCaseModel.is_deleted.isnot(True))
        if disease_code:
            query = query.filter_by(disease_code=disease_code)
        if region:
            query = query.filter_by(region=region)
        if is_confirmed is not None:
            query = query.filter_by(is_confirmed=is_confirmed)
        query = query.order_by(DiseaseCaseModel.reported_at.desc()).offset(skip).limit(limit)
        return [self._case_from_model(m) for m in query.all()]

    def get_case_stats(self, region: str | None = None, days: int = 30) -> dict[str, Any]:
        since = datetime.now(UTC) - timedelta(days=days)
        query = self.db.query(DiseaseCaseModel).filter(
            DiseaseCaseModel.reported_at >= since,
            DiseaseCaseModel.is_deleted.isnot(True),
        )
        if region:
            query = query.filter_by(region=region)
        cases = query.all()
        total = len(cases)
        confirmed = sum(1 for c in cases if c.is_confirmed)
        by_disease: dict[str, int] = {}
        for c in cases:
            by_disease[c.disease_code or "unknown"] = (
                by_disease.get(c.disease_code or "unknown", 0) + 1
            )
        return {
            "total_cases": total,
            "confirmed_cases": confirmed,
            "period_days": days,
            "region": region or "all",
            "by_disease": by_disease,
        }

    # ── Outbreak Alerts ──

    def raise_alert(self, data: dict[str, Any]) -> OutbreakAlert:
        model = OutbreakAlertModel(
            **{k: v for k, v in data.items() if hasattr(OutbreakAlertModel, k)}
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._outbreak_from_model(model)

    def get_alert(self, alert_id: str) -> OutbreakAlert:
        model = self.db.query(OutbreakAlertModel).filter_by(id=alert_id).first()
        if not model or model.is_deleted:
            raise OutbreakNotFoundError()
        return self._outbreak_from_model(model)

    def list_alerts(
        self,
        status: str | None = None,
        alert_level: str | None = None,
        region: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OutbreakAlert]:
        query = self.db.query(OutbreakAlertModel).filter(OutbreakAlertModel.is_deleted.isnot(True))
        if status:
            query = query.filter_by(status=status)
        if alert_level:
            query = query.filter_by(alert_level=alert_level)
        if region:
            query = query.filter_by(region=region)
        query = query.order_by(OutbreakAlertModel.first_detected.desc()).offset(skip).limit(limit)
        return [self._outbreak_from_model(m) for m in query.all()]

    def update_alert_status(self, alert_id: str, status: str, notes: str = "") -> OutbreakAlert:
        model = self.db.query(OutbreakAlertModel).filter_by(id=alert_id).first()
        if not model:
            raise OutbreakNotFoundError()
        model.status = status
        model.last_updated = datetime.now(UTC)
        if notes:
            model.investigation_notes = (
                model.investigation_notes or ""
            ) + f"\n[{datetime.now(UTC).isoformat()}] {notes}"
        if status == OutbreakStatus.DECLARED_OVER.value:
            model.declared_over_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(model)
        return self._outbreak_from_model(model)

    # ── Surveillance Signals ──

    def record_signal(self, data: dict[str, Any]) -> SurveillanceSignal:
        model = SurveillanceSignalModel(
            **{k: v for k, v in data.items() if hasattr(SurveillanceSignalModel, k)}
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return SurveillanceSignal(
            id=model.id,
            disease=model.disease,
            region=model.region,
            case_count=model.case_count or 0,
            z_score=model.z_score or 0.0,
            alert_level=model.alert_level or "information",
            recommendation=model.recommendation or "",
        )

    def list_signals(
        self,
        alert_level: str | None = None,
        region: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SurveillanceSignal]:
        query = self.db.query(SurveillanceSignalModel).filter(
            SurveillanceSignalModel.is_deleted.isnot(True)
        )
        if alert_level:
            query = query.filter_by(alert_level=alert_level)
        if region:
            query = query.filter_by(region=region)
        query = query.order_by(SurveillanceSignalModel.detected_at.desc()).offset(skip).limit(limit)
        return [
            SurveillanceSignal(
                id=m.id,
                disease=m.disease,
                region=m.region,
                case_count=m.case_count or 0,
                z_score=m.z_score or 0.0,
                alert_level=m.alert_level or "information",
                recommendation=m.recommendation or "",
            )
            for m in query.all()
        ]

    # ── Immunization Records ──

    def record_vaccination(self, data: dict[str, Any]) -> ImmunizationRecord:
        model = ImmunizationRecordModel(
            **{k: v for k, v in data.items() if hasattr(ImmunizationRecordModel, k)}
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._immunization_from_model(model)

    def list_vaccinations(
        self,
        patient_id: str | None = None,
        vaccine: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ImmunizationRecord]:
        query = self.db.query(ImmunizationRecordModel).filter(
            ImmunizationRecordModel.is_deleted.isnot(True)
        )
        if patient_id:
            query = query.filter_by(patient_id=patient_id)
        if vaccine:
            query = query.filter_by(vaccine=vaccine)
        query = (
            query.order_by(ImmunizationRecordModel.administration_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return [self._immunization_from_model(m) for m in query.all()]

    def get_vaccination_coverage(
        self, vaccine: str | None = None, region: str | None = None
    ) -> dict[str, Any]:
        query = self.db.query(ImmunizationRecordModel).filter(
            ImmunizationRecordModel.is_deleted.isnot(True)
        )
        total = query.count()
        return {"total_vaccinations": total, "vaccine": vaccine or "all", "region": region or "all"}

    # ── Reports ──

    def publish_report(self, data: dict[str, Any]) -> PublicHealthReport:
        model = PublicHealthReportModel(
            **{k: v for k, v in data.items() if hasattr(PublicHealthReportModel, k)}
        )
        model.status = "published"
        model.published_at = datetime.now(UTC)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._report_from_model(model)

    def list_reports(
        self,
        report_type: str | None = None,
        region: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PublicHealthReport]:
        query = self.db.query(PublicHealthReportModel).filter(
            PublicHealthReportModel.is_deleted.isnot(True)
        )
        if report_type:
            query = query.filter_by(report_type=report_type)
        if region:
            query = query.filter_by(region=region)
        query = (
            query.order_by(PublicHealthReportModel.period_start.desc()).offset(skip).limit(limit)
        )
        return [self._report_from_model(m) for m in query.all()]

    # ── AI Fabric Integration ──

    def analyze_surveillance(
        self, disease: str, region: str, case_count: int, expected_daily: float = 0
    ) -> dict[str, Any]:
        from app.ai_fabric.public_health import DiseaseSurveillance

        ds = DiseaseSurveillance()
        if expected_daily > 0:
            ds.set_baseline(disease, region, expected_daily)
        signal = ds.analyze(disease, region, case_count)
        self.record_signal(
            {
                "disease": signal.disease,
                "region": signal.location,
                "case_count": signal.case_count,
                "expected_count": signal.expected_count,
                "z_score": signal.z_score,
                "alert_level": signal.alert_level.value,
                "recommendation": signal.recommendation,
                "detected_at": datetime.fromtimestamp(signal.detected_at, tz=UTC),
            }
        )
        return {
            "z_score": signal.z_score,
            "alert_level": signal.alert_level.value,
            "expected_count": signal.expected_count,
            "recommendation": signal.recommendation,
        }

    def detect_outbreak_cluster(
        self, disease: str, region: str, cases: list[dict[str, Any]]
    ) -> dict[str, Any]:
        from app.ai_fabric.public_health import OutbreakDetector

        od = OutbreakDetector()
        alert = od.detect_cluster(disease, region, cases)
        if alert:
            self.raise_alert(
                {
                    "disease": alert.disease,
                    "region": alert.region,
                    "confirmed_cases": alert.confirmed_cases,
                    "suspected_cases": alert.suspected_cases,
                    "alert_level": AlertLevel.OUTBREAK.value,
                    "status": OutbreakStatus.INVESTIGATING.value,
                    "recommendations": alert.recommendation,
                    "first_detected": datetime.fromtimestamp(alert.first_detected, tz=UTC),
                }
            )
            return {
                "alert_raised": True,
                "region": alert.region,
                "confirmed_cases": alert.confirmed_cases,
                "recommendation": alert.recommendation,
            }
        return {"alert_raised": False}

    # ── Dashboard ──

    def get_dashboard(self, region: str | None = None) -> dict[str, Any]:
        now = datetime.now(UTC)
        thirty_days_ago = now - timedelta(days=30)
        recent_cases = self.db.query(DiseaseCaseModel).filter(
            DiseaseCaseModel.reported_at >= thirty_days_ago,
            DiseaseCaseModel.is_deleted.isnot(True),
        )
        if region:
            recent_cases = recent_cases.filter_by(region=region)
        total_cases_30d = recent_cases.count()

        active_alerts = self.db.query(OutbreakAlertModel).filter(
            OutbreakAlertModel.status.in_(["monitoring", "investigating", "confirmed"]),
            OutbreakAlertModel.is_deleted.isnot(True),
        )
        if region:
            active_alerts = active_alerts.filter_by(region=region)

        vaccinations_30d = (
            self.db.query(ImmunizationRecordModel)
            .filter(
                ImmunizationRecordModel.administration_date >= thirty_days_ago,
                ImmunizationRecordModel.is_deleted.isnot(True),
            )
            .count()
        )

        critical_signals = (
            self.db.query(SurveillanceSignalModel)
            .filter(
                SurveillanceSignalModel.alert_level.in_(["warning", "outbreak", "critical"]),
                SurveillanceSignalModel.is_deleted.isnot(True),
            )
            .count()
        )

        return {
            "region": region or "all",
            "cases_last_30d": total_cases_30d,
            "active_outbreaks": active_alerts.count(),
            "vaccinations_last_30d": vaccinations_30d,
            "active_surveillance_signals": critical_signals,
            "period": {"start": thirty_days_ago.isoformat(), "end": now.isoformat()},
        }

    def _case_from_model(self, m: DiseaseCaseModel) -> DiseaseCase:
        return DiseaseCase(
            id=m.id,
            disease_code=m.disease_code or "",
            disease_name=m.disease_name or "",
            region=m.region or "",
            is_confirmed=m.is_confirmed or False,
            source=m.source or "laboratory",
            reported_by=m.reported_by or "",
            reported_at=m.reported_at.isoformat() if m.reported_at else "",
        )

    def _outbreak_from_model(self, m: OutbreakAlertModel) -> OutbreakAlert:
        return OutbreakAlert(
            id=m.id,
            disease=m.disease,
            region=m.region or "",
            confirmed_cases=m.confirmed_cases or 0,
            alert_level=m.alert_level or "information",
            status=m.status or "monitoring",
            recommendations=m.recommendations or "",
        )

    def _immunization_from_model(self, m: ImmunizationRecordModel) -> ImmunizationRecord:
        return ImmunizationRecord(
            id=m.id,
            patient_id=m.patient_id or "",
            patient_name=m.patient_name or "",
            vaccine=m.vaccine,
            dose_number=m.dose_number or 1,
            administered_by=m.administered_by or "",
            lot_number=m.lot_number or "",
        )

    def _report_from_model(self, m: PublicHealthReportModel) -> PublicHealthReport:
        return PublicHealthReport(
            id=m.id,
            report_type=m.report_type or "weekly",
            region=m.region or "",
            total_cases=m.total_cases or 0,
            total_deaths=m.total_deaths or 0,
            key_findings=m.key_findings or "",
            published_by=m.published_by or "",
        )
