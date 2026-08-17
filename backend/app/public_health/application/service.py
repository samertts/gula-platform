from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.national.events.base import NationalDomainEvent
from app.public_health.domain.entities import (
    DiseaseCase,
    ImmunizationAdverseEvent,
    ImmunizationFollowUpTask,
    ImmunizationRecord,
    ImmunizationSchedule,
    ColdChainReading,
    VaccineCatalog,
    VaccineLot,
    OutbreakAlert,
    PublicHealthReport,
    SurveillanceSignal,
)
from app.public_health.domain.enums import AlertLevel, ImmunizationStatus, OutbreakStatus
from app.public_health.exceptions import (
    DiseaseCaseNotFoundError,
    ImmunizationScheduleConfigurationError,
    ImmunizationScheduleNotFoundError,
    ImmunizationStateError,
    OutbreakNotFoundError,
)
from app.services.cache_service import cache_key, delete as cache_delete, get_or_set as cache_get_or_set
from app.public_health.infrastructure.models import (
    DiseaseCaseModel,
    ImmunizationAdverseEventModel,
    ImmunizationFollowUpTaskModel,
    ImmunizationRecordModel,
    ImmunizationScheduleDefinitionModel,
    ImmunizationScheduleModel,
    ColdChainReadingModel,
    VaccineCatalogModel,
    VaccineLotModel,
    VaccineStockMovementModel,
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

    def list_cases(self, disease_code: str | None = None, region: str | None = None,
                   is_confirmed: bool | None = None, skip: int = 0, limit: int = 100) -> list[DiseaseCase]:
        query = self.db.query(DiseaseCaseModel).filter(DiseaseCaseModel.is_deleted.isnot(True))
        if disease_code:
            query = query.filter_by(disease_code=disease_code)
        if region:
            query = query.filter_by(region=region)
        if is_confirmed is not None:
            query = query.filter_by(is_confirmed=is_confirmed)
        query = query.order_by(DiseaseCaseModel.reported_at.desc()).offset(skip).limit(limit)
        return [self._case_from_model(m) for m in query.all()]

    def get_case_stats(self, region: str | None = None,
                       days: int = 30) -> dict[str, Any]:
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
            by_disease[c.disease_code or "unknown"] = by_disease.get(c.disease_code or "unknown", 0) + 1
        return {
            "total_cases": total,
            "confirmed_cases": confirmed,
            "period_days": days,
            "region": region or "all",
            "by_disease": by_disease,
        }

    # ── Outbreak Alerts ──

    def raise_alert(self, data: dict[str, Any]) -> OutbreakAlert:
        model = OutbreakAlertModel(**{k: v for k, v in data.items() if hasattr(OutbreakAlertModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._outbreak_from_model(model)

    def get_alert(self, alert_id: str) -> OutbreakAlert:
        model = self.db.query(OutbreakAlertModel).filter_by(id=alert_id).first()
        if not model or model.is_deleted:
            raise OutbreakNotFoundError()
        return self._outbreak_from_model(model)

    def list_alerts(self, status: str | None = None, alert_level: str | None = None,
                    region: str | None = None, skip: int = 0, limit: int = 100) -> list[OutbreakAlert]:
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
            model.investigation_notes = (model.investigation_notes or "") + f"\n[{datetime.now(UTC).isoformat()}] {notes}"
        if status == OutbreakStatus.DECLARED_OVER.value:
            model.declared_over_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(model)
        return self._outbreak_from_model(model)

    # ── Surveillance Signals ──

    def record_signal(self, data: dict[str, Any]) -> SurveillanceSignal:
        model = SurveillanceSignalModel(**{k: v for k, v in data.items() if hasattr(SurveillanceSignalModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return SurveillanceSignal(id=model.id, disease=model.disease, region=model.region,
                                   case_count=model.case_count or 0, z_score=model.z_score or 0.0,
                                   alert_level=model.alert_level or "information", recommendation=model.recommendation or "")

    def list_signals(self, alert_level: str | None = None, region: str | None = None,
                     skip: int = 0, limit: int = 100) -> list[SurveillanceSignal]:
        query = self.db.query(SurveillanceSignalModel).filter(SurveillanceSignalModel.is_deleted.isnot(True))
        if alert_level:
            query = query.filter_by(alert_level=alert_level)
        if region:
            query = query.filter_by(region=region)
        query = query.order_by(SurveillanceSignalModel.detected_at.desc()).offset(skip).limit(limit)
        return [SurveillanceSignal(id=m.id, disease=m.disease, region=m.region,
                                    case_count=m.case_count or 0, z_score=m.z_score or 0.0,
                                    alert_level=m.alert_level or "information", recommendation=m.recommendation or "")
                for m in query.all()]

    # ── Immunization Records ──

    def record_vaccination(self, data: dict[str, Any], lab_id: int) -> ImmunizationRecord:
        """Record a legacy/manual vaccination while preserving tenant isolation.

        New work should use ``mark_administered`` so an administration is linked to
        a patient-specific schedule row and cannot be duplicated.
        """
        self._require_lab_id(lab_id)
        payload = {k: v for k, v in data.items() if hasattr(ImmunizationRecordModel, k)}
        payload["lab_id"] = lab_id
        payload["administration_date"] = self._coerce_datetime(payload.get("administration_date"))
        payload["status"] = ImmunizationStatus.ADMINISTERED.value
        model = ImmunizationRecordModel(**payload)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._immunization_from_model(model)

    def list_vaccinations(self, patient_id: str | None = None, vaccine: str | None = None,
                          skip: int = 0, limit: int = 100, lab_id: int | None = None) -> list[ImmunizationRecord]:
        self._require_lab_id(lab_id)
        query = self.db.query(ImmunizationRecordModel).filter(
            ImmunizationRecordModel.is_deleted.isnot(True),
            ImmunizationRecordModel.lab_id == lab_id,
        )
        if patient_id:
            query = query.filter_by(patient_id=patient_id)
        if vaccine:
            query = query.filter_by(vaccine=vaccine)
        query = query.order_by(ImmunizationRecordModel.administration_date.desc()).offset(skip).limit(limit)
        return [self._immunization_from_model(m) for m in query.all()]

    def get_vaccination_coverage(self, vaccine: str | None = None,
                                 region: str | None = None, lab_id: int | None = None) -> dict[str, Any]:
        self._require_lab_id(lab_id)
        query = self.db.query(ImmunizationRecordModel).filter(
            ImmunizationRecordModel.is_deleted.isnot(True),
            ImmunizationRecordModel.lab_id == lab_id,
            ImmunizationRecordModel.status.in_(
                [ImmunizationStatus.ADMINISTERED.value, ImmunizationStatus.COMPLETE.value]
            ),
        )
        if vaccine:
            query = query.filter(ImmunizationRecordModel.vaccine == vaccine)
        total = query.count()
        return {
            "total_administered": total,
            "vaccine": vaccine or "all",
            "region": region or "all",
        }

    # ── Immunization Programme ──

    def configure_immunization_schedule(
        self, data: dict[str, Any], lab_id: int, approved_by: str | None = None
    ) -> dict[str, Any]:
        """Persist one Ministry-approved reference dose definition for a facility.

        The programme intentionally does not seed a country schedule in code.  An
        authorized health authority supplies the currently approved schedule version
        and source reference before patient schedules can be generated.
        """
        self._require_lab_id(lab_id)
        required = ("schedule_version", "vaccine", "vaccine_code", "dose_number", "total_doses", "recommended_age_days")
        if any(data.get(field) in (None, "") for field in required):
            raise ValueError("Incomplete immunization schedule definition")
        minimum_age_days = int(data.get("minimum_age_days", 0))
        recommended_age_days = int(data["recommended_age_days"])
        grace_period_days = int(data.get("grace_period_days", 0))
        dose_number = int(data["dose_number"])
        total_doses = int(data["total_doses"])
        if min(minimum_age_days, recommended_age_days, grace_period_days) < 0:
            raise ValueError("Schedule ages must not be negative")
        if recommended_age_days < minimum_age_days or not 1 <= dose_number <= total_doses:
            raise ValueError("Invalid dose sequence")

        duplicate = self.db.query(ImmunizationScheduleDefinitionModel).filter(
            ImmunizationScheduleDefinitionModel.lab_id == lab_id,
            ImmunizationScheduleDefinitionModel.schedule_version == str(data["schedule_version"]),
            ImmunizationScheduleDefinitionModel.vaccine_code == str(data["vaccine_code"]),
            ImmunizationScheduleDefinitionModel.dose_number == dose_number,
            ImmunizationScheduleDefinitionModel.is_deleted.isnot(True),
        ).first()
        if duplicate:
            raise ValueError("Schedule definition already exists")

        payload = {k: v for k, v in data.items() if hasattr(ImmunizationScheduleDefinitionModel, k)}
        payload.update({
            "lab_id": lab_id,
            "minimum_age_days": minimum_age_days,
            "recommended_age_days": recommended_age_days,
            "grace_period_days": grace_period_days,
            "dose_number": dose_number,
            "total_doses": total_doses,
            "approved_by": approved_by or data.get("approved_by"),
            "approved_at": datetime.now(UTC) if data.get("is_active", True) else None,
        })
        model = ImmunizationScheduleDefinitionModel(**payload)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._schedule_definition_to_dict(model)

    def generate_patient_immunization_schedule(
        self,
        patient_id: str,
        health_number: str,
        date_of_birth: date,
        lab_id: int,
        schedule_version: str,
        newborn_id: str | None = None,
        facility_id: str | None = None,
    ) -> list[ImmunizationSchedule]:
        self._require_lab_id(lab_id)
        if not patient_id or not health_number or not isinstance(date_of_birth, date):
            raise ValueError("Patient, health number, and date of birth are required")
        definitions = self.db.query(ImmunizationScheduleDefinitionModel).filter(
            ImmunizationScheduleDefinitionModel.lab_id == lab_id,
            ImmunizationScheduleDefinitionModel.schedule_version == schedule_version,
            ImmunizationScheduleDefinitionModel.is_active.is_(True),
            ImmunizationScheduleDefinitionModel.is_deleted.isnot(True),
        ).order_by(
            ImmunizationScheduleDefinitionModel.recommended_age_days,
            ImmunizationScheduleDefinitionModel.vaccine_code,
            ImmunizationScheduleDefinitionModel.dose_number,
        ).all()
        if not definitions:
            raise ImmunizationScheduleConfigurationError()

        generated: list[ImmunizationScheduleModel] = []
        for definition in definitions:
            existing = self.db.query(ImmunizationScheduleModel).filter(
                ImmunizationScheduleModel.lab_id == lab_id,
                ImmunizationScheduleModel.patient_id == patient_id,
                ImmunizationScheduleModel.schedule_definition_id == definition.id,
                ImmunizationScheduleModel.is_deleted.isnot(True),
            ).first()
            if existing:
                generated.append(existing)
                continue
            due_at = datetime.combine(
                date_of_birth + timedelta(days=definition.recommended_age_days),
                datetime.min.time(),
                tzinfo=UTC,
            )
            model = ImmunizationScheduleModel(
                lab_id=lab_id,
                patient_id=patient_id,
                health_number=health_number,
                newborn_id=newborn_id,
                schedule_definition_id=definition.id,
                schedule_version=definition.schedule_version,
                vaccine=definition.vaccine,
                vaccine_code=definition.vaccine_code,
                dose_number=definition.dose_number,
                total_doses=definition.total_doses,
                due_date=due_at,
                facility_id=facility_id,
                status=ImmunizationStatus.SCHEDULED.value,
            )
            self.db.add(model)
            generated.append(model)
        self.db.commit()
        for model in generated:
            self.db.refresh(model)
        return [self._schedule_from_model(model) for model in generated]

    def get_patient_immunization_schedule(
        self, patient_id: str, lab_id: int, include_closed: bool = True
    ) -> list[ImmunizationSchedule]:
        self._require_lab_id(lab_id)
        query = self.db.query(ImmunizationScheduleModel).filter(
            ImmunizationScheduleModel.lab_id == lab_id,
            ImmunizationScheduleModel.patient_id == patient_id,
            ImmunizationScheduleModel.is_deleted.isnot(True),
        )
        if not include_closed:
            query = query.filter(
                ImmunizationScheduleModel.status.in_(
                    [ImmunizationStatus.SCHEDULED.value, ImmunizationStatus.OVERDUE.value]
                )
            )
        return [self._schedule_from_model(model) for model in query.order_by(ImmunizationScheduleModel.due_date).all()]

    def schedule_immunization(
        self,
        schedule_id: str,
        lab_id: int,
        scheduled_date: datetime,
        appointment_id: str | None = None,
        facility_id: str | None = None,
    ) -> ImmunizationSchedule:
        self._require_lab_id(lab_id)
        model = self._get_schedule(schedule_id, lab_id, lock=True)
        if model.status in (ImmunizationStatus.ADMINISTERED.value, ImmunizationStatus.COMPLETE.value,
                            ImmunizationStatus.REFUSED.value, ImmunizationStatus.CONTRAINDICATED.value):
            raise ImmunizationStateError()
        model.scheduled_date = self._coerce_datetime(scheduled_date)
        model.appointment_id = appointment_id
        if facility_id:
            model.facility_id = facility_id
        if model.status == ImmunizationStatus.OVERDUE.value:
            model.status = ImmunizationStatus.SCHEDULED.value
        self.db.commit()
        self.db.refresh(model)
        return self._schedule_from_model(model)

    def get_overdue_vaccinations(self, lab_id: int, patient_id: str | None = None) -> list[ImmunizationSchedule]:
        self._require_lab_id(lab_id)
        now = datetime.now(UTC)
        query = self.db.query(ImmunizationScheduleModel).filter(
            ImmunizationScheduleModel.lab_id == lab_id,
            ImmunizationScheduleModel.is_deleted.isnot(True),
            ImmunizationScheduleModel.due_date < now,
            ImmunizationScheduleModel.status.in_(
                [ImmunizationStatus.SCHEDULED.value, ImmunizationStatus.OVERDUE.value]
            ),
        )
        if patient_id:
            query = query.filter(ImmunizationScheduleModel.patient_id == patient_id)
        schedules = query.order_by(ImmunizationScheduleModel.due_date).all()
        changed = False
        for model in schedules:
            if model.status != ImmunizationStatus.OVERDUE.value:
                model.status = ImmunizationStatus.OVERDUE.value
                changed = True
        if changed:
            self.db.commit()
            for model in schedules:
                self.db.refresh(model)
        return [self._schedule_from_model(model) for model in schedules]

    def mark_administered(
        self, schedule_id: str, data: dict[str, Any], lab_id: int, administered_by: str | None = None
    ) -> ImmunizationRecord:
        self._require_lab_id(lab_id)
        schedule = self._get_schedule(schedule_id, lab_id, lock=True)
        existing = self.db.query(ImmunizationRecordModel).filter(
            ImmunizationRecordModel.lab_id == lab_id,
            ImmunizationRecordModel.schedule_id == schedule_id,
            ImmunizationRecordModel.is_deleted.isnot(True),
        ).first()
        if existing:
            return self._immunization_from_model(existing)
        if schedule.status in (ImmunizationStatus.REFUSED.value, ImmunizationStatus.CONTRAINDICATED.value,
                               ImmunizationStatus.COMPLETE.value):
            raise ImmunizationStateError()

        administration_date = self._coerce_datetime(data.get("administration_date"))
        payload = {k: v for k, v in data.items() if hasattr(ImmunizationRecordModel, k)}
        payload.update({
            "lab_id": lab_id,
            "patient_id": schedule.patient_id,
            "health_number": schedule.health_number,
            "newborn_id": schedule.newborn_id,
            "schedule_id": schedule.id,
            "vaccine": schedule.vaccine,
            "vaccine_code": schedule.vaccine_code,
            "dose_number": schedule.dose_number,
            "total_doses": schedule.total_doses,
            "due_date": schedule.due_date,
            "scheduled_date": schedule.scheduled_date,
            "appointment_id": schedule.appointment_id,
            "administration_date": administration_date,
            "administered_by": administered_by or data.get("administered_by"),
            "status": (
                ImmunizationStatus.COMPLETE.value
                if schedule.dose_number >= schedule.total_doses
                else ImmunizationStatus.ADMINISTERED.value
            ),
        })
        record = ImmunizationRecordModel(**payload)
        schedule.status = record.status
        try:
            self.db.add(record)
            self.db.flush()
            from app.integration.healthcare.ehr_sync import queue_immunization_sync
            queue_immunization_sync(self.db, record, lab_id)
            self.db.commit()
            self.db.refresh(record)
        except Exception:
            self.db.rollback()
            raise
        cache_delete(cache_key("immunization_report", lab_id, version="monthly", year=administration_date.year, month=administration_date.month))
        return self._immunization_from_model(record)

    def record_non_administration(
        self,
        schedule_id: str,
        data: dict[str, Any],
        lab_id: int,
        recorded_by: str | None = None,
    ) -> ImmunizationSchedule:
        """Record why a planned dose was not given without deleting its history."""
        self._require_lab_id(lab_id)
        schedule = self._get_schedule(schedule_id, lab_id, lock=True)
        reason = str(data.get("reason", "")).strip().lower()
        allowed = {"refused", "contraindicated", "stockout", "absent", "transferred", "other"}
        if reason not in allowed:
            raise ValueError("Invalid non-administration reason")
        notes = str(data.get("notes", ""))[:2000]
        schedule.non_administration_reason = reason
        schedule.non_administration_notes = notes or None
        schedule.follow_up_priority = str(data.get("priority", "high" if reason in {"stockout", "absent"} else "normal"))
        schedule.follow_up_status = "not_required" if reason in {"refused", "contraindicated", "transferred"} else "pending"
        schedule.next_follow_up_date = self._coerce_datetime(data.get("next_follow_up_date")) if data.get("next_follow_up_date") else None
        if reason == "refused":
            schedule.status = ImmunizationStatus.REFUSED.value
            schedule.refusal_reason = notes or reason
        elif reason == "contraindicated":
            schedule.status = ImmunizationStatus.CONTRAINDICATED.value
            schedule.contraindication_reason = notes or reason
        else:
            due_date = self._coerce_datetime(schedule.due_date) if schedule.due_date else None
            schedule.status = ImmunizationStatus.OVERDUE.value if due_date and due_date < datetime.now(UTC) else ImmunizationStatus.SCHEDULED.value
            existing_task = self.db.query(ImmunizationFollowUpTaskModel).filter(
                ImmunizationFollowUpTaskModel.lab_id == lab_id,
                ImmunizationFollowUpTaskModel.schedule_id == schedule.id,
                ImmunizationFollowUpTaskModel.status.in_(["pending", "queued"]),
                ImmunizationFollowUpTaskModel.is_deleted.isnot(True),
            ).first()
            if not existing_task:
                self.db.add(ImmunizationFollowUpTaskModel(
                    lab_id=lab_id,
                    schedule_id=schedule.id,
                    patient_id=schedule.patient_id,
                    health_number=schedule.health_number,
                    vaccine=schedule.vaccine,
                    due_date=schedule.due_date,
                    status="pending",
                    priority=schedule.follow_up_priority,
                    reason=reason,
                    next_action_at=schedule.next_follow_up_date,
                    notes=f"recorded_by:{recorded_by or 'unknown'}",
                ))
        self.db.commit()
        self.db.refresh(schedule)
        return self._schedule_from_model(schedule)

    def list_follow_up_tasks(self, lab_id: int, status: str | None = None, limit: int = 100) -> list[ImmunizationFollowUpTask]:
        self._require_lab_id(lab_id)
        query = self.db.query(ImmunizationFollowUpTaskModel).filter(
            ImmunizationFollowUpTaskModel.lab_id == lab_id,
            ImmunizationFollowUpTaskModel.is_deleted.isnot(True),
        )
        if status:
            query = query.filter(ImmunizationFollowUpTaskModel.status == status)
        tasks = query.order_by(ImmunizationFollowUpTaskModel.priority.desc(), ImmunizationFollowUpTaskModel.due_date).limit(limit).all()
        return [self._follow_up_from_model(task) for task in tasks]

    def complete_follow_up_task(self, task_id: str, lab_id: int, completed_by: str, status: str = "completed") -> ImmunizationFollowUpTask:
        self._require_lab_id(lab_id)
        if status not in {"completed", "suppressed"}:
            raise ValueError("Invalid follow-up completion status")
        task = self.db.query(ImmunizationFollowUpTaskModel).filter(
            ImmunizationFollowUpTaskModel.id == task_id,
            ImmunizationFollowUpTaskModel.lab_id == lab_id,
            ImmunizationFollowUpTaskModel.is_deleted.isnot(True),
        ).first()
        if not task:
            raise ImmunizationScheduleNotFoundError()
        task.status = status
        task.completed_at = datetime.now(UTC)
        task.completed_by = completed_by
        self.db.commit()
        self.db.refresh(task)
        return self._follow_up_from_model(task)

    def report_adverse_event(self, record_id: str, data: dict[str, Any], lab_id: int, reported_by: str) -> ImmunizationAdverseEvent:
        self._require_lab_id(lab_id)
        record = self.db.query(ImmunizationRecordModel).filter(
            ImmunizationRecordModel.id == record_id,
            ImmunizationRecordModel.lab_id == lab_id,
            ImmunizationRecordModel.is_deleted.isnot(True),
        ).first()
        if not record:
            raise ImmunizationScheduleNotFoundError()
        symptoms = data.get("symptoms", [])
        if not isinstance(symptoms, list) or not all(isinstance(item, str) for item in symptoms):
            raise ValueError("Symptoms must be a list of strings")
        event = ImmunizationAdverseEventModel(
            lab_id=lab_id,
            record_id=record.id,
            schedule_id=record.schedule_id,
            patient_id=record.patient_id,
            health_number=record.health_number,
            vaccine=record.vaccine,
            onset_at=self._coerce_datetime(data.get("onset_at")) if data.get("onset_at") else None,
            severity=str(data.get("severity", "unknown")),
            symptoms=symptoms[:50],
            treatment=str(data.get("treatment", ""))[:4000] or None,
            outcome=str(data.get("outcome", ""))[:100] or None,
            investigation_status="reported",
            reported_by=reported_by,
            reported_at=datetime.now(UTC),
            notes=str(data.get("notes", ""))[:4000] or None,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return self._aefi_from_model(event)

    def send_reminder(self, schedule_id: str, lab_id: int) -> ImmunizationSchedule:
        """Mark a reminder as queued for the platform notification subsystem.

        This method deliberately emits no phone number, address, or external network
        request. A separate authorized notification worker resolves a consented
        contact destination and delivers the reminder idempotently.
        """
        self._require_lab_id(lab_id)
        schedule = self._get_schedule(schedule_id, lab_id, lock=True)
        if schedule.status not in (ImmunizationStatus.SCHEDULED.value, ImmunizationStatus.OVERDUE.value):
            raise ImmunizationStateError()
        now = datetime.now(UTC)
        schedule.reminder_sent = True
        schedule.reminder_sent_at = now
        schedule.reminder_count = (schedule.reminder_count or 0) + 1
        task = self.db.query(ImmunizationFollowUpTaskModel).filter(
            ImmunizationFollowUpTaskModel.lab_id == lab_id,
            ImmunizationFollowUpTaskModel.schedule_id == schedule.id,
            ImmunizationFollowUpTaskModel.status.in_(["pending", "queued"]),
            ImmunizationFollowUpTaskModel.is_deleted.isnot(True),
        ).first()
        if not task:
            task = ImmunizationFollowUpTaskModel(
                lab_id=lab_id,
                schedule_id=schedule.id,
                patient_id=schedule.patient_id,
                health_number=schedule.health_number,
                vaccine=schedule.vaccine,
                due_date=schedule.due_date,
                status="queued",
                priority="high" if schedule.status == ImmunizationStatus.OVERDUE.value else "normal",
                reason="overdue" if schedule.status == ImmunizationStatus.OVERDUE.value else "due",
                next_action_at=now,
                consent_verified=False,
                notes="Notification worker must verify consent and destination before delivery.",
            )
            self.db.add(task)
        else:
            task.status = "queued"
            task.last_attempt_at = now
        self.db.commit()
        self.db.refresh(schedule)
        self._emit(NationalDomainEvent(
            event_type="ImmunizationReminderQueued",
            aggregate_id=schedule.id,
            aggregate_type="ImmunizationSchedule",
            payload={"schedule_id": schedule.id, "patient_id": schedule.patient_id, "lab_id": lab_id},
            lab_id=lab_id,
        ))
        return self._schedule_from_model(schedule)

    def get_monthly_immunization_statistics(self, lab_id: int, year: int, month: int) -> dict[str, Any]:
        self._require_lab_id(lab_id)
        if not 1 <= month <= 12:
            raise ValueError("Month must be between 1 and 12")
        cache_key_value = cache_key("immunization_report", lab_id, version="monthly", year=year, month=month)
        return cache_get_or_set(
            cache_key_value,
            lambda: self._compute_monthly_immunization_statistics(lab_id, year, month),
            ttl_seconds=120,
        )

    def _compute_monthly_immunization_statistics(self, lab_id: int, year: int, month: int) -> dict[str, Any]:
        from sqlalchemy import func
        period_start = datetime(year, month, 1, tzinfo=UTC)

        period_end = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1, tzinfo=UTC)
        scheduled_query = self.db.query(ImmunizationScheduleModel).filter(
            ImmunizationScheduleModel.lab_id == lab_id,
            ImmunizationScheduleModel.is_deleted.isnot(True),
            ImmunizationScheduleModel.due_date >= period_start,
            ImmunizationScheduleModel.due_date < period_end,
        )
        planned_count = int(scheduled_query.with_entities(func.count(ImmunizationScheduleModel.id)).scalar() or 0)
        overdue_count = int(scheduled_query.filter(ImmunizationScheduleModel.status == ImmunizationStatus.OVERDUE.value).with_entities(func.count(ImmunizationScheduleModel.id)).scalar() or 0)
        administered_query = self.db.query(ImmunizationRecordModel).filter(
            ImmunizationRecordModel.lab_id == lab_id,
            ImmunizationRecordModel.is_deleted.isnot(True),
            ImmunizationRecordModel.administration_date >= period_start,
            ImmunizationRecordModel.administration_date < period_end,
            ImmunizationRecordModel.status.in_([ImmunizationStatus.ADMINISTERED.value, ImmunizationStatus.COMPLETE.value]),
        )
        administered_count = int(administered_query.with_entities(func.count(ImmunizationRecordModel.id)).scalar() or 0)
        grouped = administered_query.with_entities(ImmunizationRecordModel.vaccine, func.count(ImmunizationRecordModel.id)).group_by(ImmunizationRecordModel.vaccine).all()
        by_vaccine = {str(vaccine): int(count) for vaccine, count in grouped}
        return {
            "period": {"start": period_start.isoformat(), "end": period_end.isoformat()},
            "scheduled_doses": planned_count,
            "administered_doses": administered_count,
            "overdue_doses": overdue_count,
            "delivery_rate_pct": round((administered_count / planned_count * 100) if planned_count else 0.0, 2),
            "administered_by_vaccine": by_vaccine,
        }

    # ── Vaccine inventory and cold chain ──

    def register_vaccine_catalog(self, data: dict[str, Any], lab_id: int) -> VaccineCatalog:
        self._require_lab_id(lab_id)
        code = str(data.get("vaccine_code", "")).strip()
        name = str(data.get("name", "")).strip()
        if not code or not name:
            raise ValueError("Vaccine code and name are required")
        duplicate = self.db.query(VaccineCatalogModel).filter(
            VaccineCatalogModel.lab_id == lab_id,
            VaccineCatalogModel.vaccine_code == code,
            VaccineCatalogModel.is_deleted.isnot(True),
        ).first()
        if duplicate:
            raise ValueError("Vaccine catalog entry already exists")
        minimum = data.get("storage_min_c")
        maximum = data.get("storage_max_c")
        if minimum is not None and maximum is not None and float(minimum) > float(maximum):
            raise ValueError("Invalid storage temperature range")
        model = VaccineCatalogModel(
            lab_id=lab_id, vaccine_code=code, name=name,
            name_ar=str(data.get("name_ar", ""))[:200] or None,
            unit=str(data.get("unit", "dose"))[:24],
            manufacturer=str(data.get("manufacturer", ""))[:200] or None,
            storage_min_c=float(minimum) if minimum is not None else None,
            storage_max_c=float(maximum) if maximum is not None else None,
            source_reference=str(data.get("source_reference", ""))[:500] or None,
            is_active=bool(data.get("is_active", True)),
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._catalog_from_model(model)

    def receive_vaccine_lot(self, catalog_id: str, data: dict[str, Any], lab_id: int, performed_by: str) -> VaccineLot:
        self._require_lab_id(lab_id)
        catalog = self.db.query(VaccineCatalogModel).filter(
            VaccineCatalogModel.id == catalog_id,
            VaccineCatalogModel.lab_id == lab_id,
            VaccineCatalogModel.is_deleted.isnot(True),
            VaccineCatalogModel.is_active.is_(True),
        ).first()
        if not catalog:
            raise ValueError("Vaccine catalog entry not found")
        lot_number = str(data.get("lot_number", "")).strip()
        quantity = int(data.get("quantity", 0))
        expiry = self._coerce_datetime(data.get("expiry_date"))
        if not lot_number or quantity <= 0 or expiry <= datetime.now(UTC):
            raise ValueError("Valid lot number, positive quantity, and future expiry are required")
        duplicate = self.db.query(VaccineLotModel).filter(
            VaccineLotModel.lab_id == lab_id,
            VaccineLotModel.catalog_id == catalog_id,
            VaccineLotModel.lot_number == lot_number,
            VaccineLotModel.is_deleted.isnot(True),
        ).first()
        if duplicate:
            raise ValueError("Vaccine lot already exists")
        lot = VaccineLotModel(
            lab_id=lab_id, catalog_id=catalog_id, lot_number=lot_number,
            expiry_date=expiry, received_at=datetime.now(UTC),
            received_quantity=quantity, available_quantity=quantity,
            storage_equipment_id=str(data.get("storage_equipment_id", ""))[:100] or None,
        )
        self.db.add(lot)
        self.db.flush()
        self.db.add(VaccineStockMovementModel(
            lab_id=lab_id, lot_id=lot.id, movement_type="received", quantity=quantity,
            reference_type="receipt", reference_id=str(data.get("reference_id", ""))[:100] or None,
            idempotency_key=f"receipt:{lab_id}:{lot.id}", reason=str(data.get("reason", "initial receipt"))[:200],
            performed_by=performed_by, occurred_at=datetime.now(UTC),
        ))
        self.db.commit()
        self.db.refresh(lot)
        return self._lot_from_model(lot)

    def record_cold_chain_reading(self, data: dict[str, Any], lab_id: int, recorded_by: str) -> ColdChainReading:
        self._require_lab_id(lab_id)
        equipment_id = str(data.get("equipment_id", "")).strip()
        if not equipment_id or data.get("temperature_c") is None:
            raise ValueError("Equipment and temperature are required")
        minimum = float(data["minimum_allowed_c"]) if data.get("minimum_allowed_c") is not None else None
        maximum = float(data["maximum_allowed_c"]) if data.get("maximum_allowed_c") is not None else None
        temperature = float(data["temperature_c"])
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError("Invalid cold-chain range")
        out_of_range = (minimum is not None and temperature < minimum) or (maximum is not None and temperature > maximum)
        status = "out_of_range" if out_of_range else "within_range"
        reading = ColdChainReadingModel(
            lab_id=lab_id, equipment_id=equipment_id,
            reading_at=self._coerce_datetime(data.get("reading_at")), temperature_c=temperature,
            minimum_allowed_c=minimum, maximum_allowed_c=maximum, status=status,
            source=str(data.get("source", "manual"))[:24], recorded_by=recorded_by,
            notes=str(data.get("notes", ""))[:2000] or None,
        )
        self.db.add(reading)
        if out_of_range:
            lots = self.db.query(VaccineLotModel).filter(
                VaccineLotModel.lab_id == lab_id,
                VaccineLotModel.storage_equipment_id == equipment_id,
                VaccineLotModel.quarantined.is_(False),
                VaccineLotModel.is_deleted.isnot(True),
                VaccineLotModel.available_quantity > 0,
            ).all()
            for lot in lots:
                lot.quarantined = True
                lot.quarantine_reason = f"cold-chain excursion:{temperature}C"
        self.db.commit()
        self.db.refresh(reading)
        return self._cold_chain_from_model(reading)

    def list_vaccine_inventory(self, lab_id: int, vaccine_code: str | None = None) -> list[VaccineLot]:
        self._require_lab_id(lab_id)
        query = self.db.query(VaccineLotModel).join(VaccineCatalogModel, VaccineCatalogModel.id == VaccineLotModel.catalog_id).filter(
            VaccineLotModel.lab_id == lab_id,
            VaccineLotModel.is_deleted.isnot(True),
            VaccineCatalogModel.is_deleted.isnot(True),
        )
        if vaccine_code:
            query = query.filter(VaccineCatalogModel.vaccine_code == vaccine_code)
        return [self._lot_from_model(lot) for lot in query.order_by(VaccineLotModel.expiry_date).all()]

    def consume_vaccine_for_administration(
        self, record_id: str, lot_id: str, quantity: int, lab_id: int, performed_by: str, idempotency_key: str
    ) -> dict[str, Any]:
        self._require_lab_id(lab_id)
        if quantity != 1 or not idempotency_key.strip():
            raise ValueError("A single dose and idempotency key are required")
        existing = self.db.query(VaccineStockMovementModel).filter(
            VaccineStockMovementModel.lab_id == lab_id,
            VaccineStockMovementModel.idempotency_key == idempotency_key,
            VaccineStockMovementModel.is_deleted.isnot(True),
        ).first()
        if existing:
            return {"movement_id": existing.id, "lot_id": existing.lot_id, "quantity": existing.quantity, "idempotent_replay": True}
        record = self.db.query(ImmunizationRecordModel).filter(
            ImmunizationRecordModel.id == record_id,
            ImmunizationRecordModel.lab_id == lab_id,
            ImmunizationRecordModel.is_deleted.isnot(True),
        ).first()
        lot = self.db.query(VaccineLotModel).filter(
            VaccineLotModel.id == lot_id,
            VaccineLotModel.lab_id == lab_id,
            VaccineLotModel.is_deleted.isnot(True),
        ).with_for_update().first()
        if not record or not lot:
            raise ValueError("Vaccination record or vaccine lot not found")
        catalog = self.db.query(VaccineCatalogModel).filter(VaccineCatalogModel.id == lot.catalog_id).first()
        if not catalog or catalog.vaccine_code != record.vaccine_code:
            raise ValueError("Vaccine lot does not match administered vaccine")
        expiry_date = self._coerce_datetime(lot.expiry_date)
        if lot.quarantined or expiry_date <= datetime.now(UTC) or lot.available_quantity < quantity:
            raise ValueError("Vaccine lot is unavailable for dispensing")
        lot.available_quantity -= quantity
        movement = VaccineStockMovementModel(
            lab_id=lab_id, lot_id=lot.id, movement_type="dispensed", quantity=quantity,
            reference_type="immunization_record", reference_id=record.id,
            idempotency_key=idempotency_key[:160], reason="linked administration",
            performed_by=performed_by, occurred_at=datetime.now(UTC),
        )
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)
        return {"movement_id": movement.id, "lot_id": lot.id, "quantity": quantity, "idempotent_replay": False}

    def record_vaccine_wastage(self, lot_id: str, data: dict[str, Any], lab_id: int, performed_by: str) -> dict[str, Any]:
        self._require_lab_id(lab_id)
        quantity = int(data.get("quantity", 0))
        idempotency_key = str(data.get("idempotency_key", "")).strip()
        if quantity <= 0 or not idempotency_key:
            raise ValueError("Positive quantity and idempotency key are required")
        existing = self.db.query(VaccineStockMovementModel).filter(
            VaccineStockMovementModel.lab_id == lab_id,
            VaccineStockMovementModel.idempotency_key == idempotency_key,
            VaccineStockMovementModel.is_deleted.isnot(True),
        ).first()
        if existing:
            return {"movement_id": existing.id, "lot_id": existing.lot_id, "quantity": existing.quantity, "idempotent_replay": True}
        lot = self.db.query(VaccineLotModel).filter(
            VaccineLotModel.id == lot_id, VaccineLotModel.lab_id == lab_id,
            VaccineLotModel.is_deleted.isnot(True),
        ).with_for_update().first()
        if not lot or lot.available_quantity < quantity:
            raise ValueError("Vaccine lot is unavailable for wastage")
        lot.available_quantity -= quantity
        movement = VaccineStockMovementModel(
            lab_id=lab_id, lot_id=lot.id, movement_type="wasted", quantity=quantity,
            reference_type="wastage", reference_id=str(data.get("reference_id", ""))[:100] or None,
            idempotency_key=idempotency_key[:160], reason=str(data.get("reason", "wastage"))[:500],
            performed_by=performed_by, occurred_at=datetime.now(UTC),
        )
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)
        return {"movement_id": movement.id, "lot_id": lot.id, "quantity": quantity, "idempotent_replay": False}

    def adjust_vaccine_lot(self, lot_id: str, data: dict[str, Any], lab_id: int, performed_by: str) -> dict[str, Any]:
        self._require_lab_id(lab_id)
        delta = int(data.get("delta", 0))
        idempotency_key = str(data.get("idempotency_key", "")).strip()
        if delta == 0 or not idempotency_key:
            raise ValueError("Non-zero delta and idempotency key are required")
        existing = self.db.query(VaccineStockMovementModel).filter(
            VaccineStockMovementModel.lab_id == lab_id,
            VaccineStockMovementModel.idempotency_key == idempotency_key,
            VaccineStockMovementModel.is_deleted.isnot(True),
        ).first()
        if existing:
            return {"movement_id": existing.id, "lot_id": existing.lot_id, "quantity": existing.quantity, "idempotent_replay": True}
        lot = self.db.query(VaccineLotModel).filter(
            VaccineLotModel.id == lot_id, VaccineLotModel.lab_id == lab_id,
            VaccineLotModel.is_deleted.isnot(True),
        ).with_for_update().first()
        if not lot or lot.available_quantity + delta < 0:
            raise ValueError("Stock adjustment would make quantity negative")
        lot.available_quantity += delta
        movement = VaccineStockMovementModel(
            lab_id=lab_id, lot_id=lot.id, movement_type="adjusted", quantity=abs(delta),
            reference_type="stock_adjustment", reference_id=str(data.get("reference_id", ""))[:100] or None,
            idempotency_key=idempotency_key[:160], reason=str(data.get("reason", "physical count"))[:500],
            performed_by=performed_by, occurred_at=datetime.now(UTC),
        )
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)
        return {"movement_id": movement.id, "lot_id": lot.id, "quantity": delta, "idempotent_replay": False}

    def get_vaccine_inventory_report(self, lab_id: int) -> dict[str, Any]:
        self._require_lab_id(lab_id)
        lots = self.db.query(VaccineLotModel).filter(
            VaccineLotModel.lab_id == lab_id,
            VaccineLotModel.is_deleted.isnot(True),
        ).all()
        movements = self.db.query(VaccineStockMovementModel).filter(
            VaccineStockMovementModel.lab_id == lab_id,
            VaccineStockMovementModel.is_deleted.isnot(True),
        ).all()
        return {
            "total_lots": len(lots),
            "available_doses": sum(max(0, lot.available_quantity) for lot in lots if not lot.quarantined),
            "quarantined_lots": sum(1 for lot in lots if lot.quarantined),
            "expired_lots": sum(1 for lot in lots if lot.expiry_date <= datetime.now(UTC)),
            "wasted_doses": sum(item.quantity for item in movements if item.movement_type == "wasted"),
            "dispensed_doses": sum(item.quantity for item in movements if item.movement_type == "dispensed"),
            "out_of_range_readings": self.db.query(ColdChainReadingModel).filter(
                ColdChainReadingModel.lab_id == lab_id,
                ColdChainReadingModel.status == "out_of_range",
                ColdChainReadingModel.is_deleted.isnot(True),
            ).count(),
        }

    # ── Reports ──

    def publish_report(self, data: dict[str, Any]) -> PublicHealthReport:
        model = PublicHealthReportModel(**{k: v for k, v in data.items() if hasattr(PublicHealthReportModel, k)})
        model.status = "published"
        model.published_at = datetime.now(UTC)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._report_from_model(model)

    def list_reports(self, report_type: str | None = None, region: str | None = None,
                     skip: int = 0, limit: int = 100) -> list[PublicHealthReport]:
        query = self.db.query(PublicHealthReportModel).filter(PublicHealthReportModel.is_deleted.isnot(True))
        if report_type:
            query = query.filter_by(report_type=report_type)
        if region:
            query = query.filter_by(region=region)
        query = query.order_by(PublicHealthReportModel.period_start.desc()).offset(skip).limit(limit)
        return [self._report_from_model(m) for m in query.all()]

    # ── AI Fabric Integration ──

    def analyze_surveillance(self, disease: str, region: str, case_count: int,
                             expected_daily: float = 0) -> dict[str, Any]:
        from app.ai_fabric.public_health import DiseaseSurveillance
        ds = DiseaseSurveillance()
        if expected_daily > 0:
            ds.set_baseline(disease, region, expected_daily)
        signal = ds.analyze(disease, region, case_count)
        self.record_signal({
            "disease": signal.disease,
            "region": signal.location,
            "case_count": signal.case_count,
            "expected_count": signal.expected_count,
            "z_score": signal.z_score,
            "alert_level": signal.alert_level.value,
            "recommendation": signal.recommendation,
            "detected_at": datetime.fromtimestamp(signal.detected_at, tz=UTC),
        })
        return {"z_score": signal.z_score, "alert_level": signal.alert_level.value,
                "expected_count": signal.expected_count, "recommendation": signal.recommendation}

    def detect_outbreak_cluster(self, disease: str, region: str,
                                cases: list[dict[str, Any]]) -> dict[str, Any]:
        from app.ai_fabric.public_health import OutbreakDetector
        od = OutbreakDetector()
        alert = od.detect_cluster(disease, region, cases)
        if alert:
            self.raise_alert({
                "disease": alert.disease,
                "region": alert.region,
                "confirmed_cases": alert.confirmed_cases,
                "suspected_cases": alert.suspected_cases,
                "alert_level": AlertLevel.OUTBREAK.value,
                "status": OutbreakStatus.INVESTIGATING.value,
                "recommendations": alert.recommendation,
                "first_detected": datetime.fromtimestamp(alert.first_detected, tz=UTC),
            })
            return {"alert_raised": True, "region": alert.region,
                    "confirmed_cases": alert.confirmed_cases, "recommendation": alert.recommendation}
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

        vaccinations_30d = self.db.query(ImmunizationRecordModel).filter(
            ImmunizationRecordModel.administration_date >= thirty_days_ago,
            ImmunizationRecordModel.is_deleted.isnot(True),
        ).count()

        critical_signals = self.db.query(SurveillanceSignalModel).filter(
            SurveillanceSignalModel.alert_level.in_(["warning", "outbreak", "critical"]),
            SurveillanceSignalModel.is_deleted.isnot(True),
        ).count()

        return {
            "region": region or "all",
            "cases_last_30d": total_cases_30d,
            "active_outbreaks": active_alerts.count(),
            "vaccinations_last_30d": vaccinations_30d,
            "active_surveillance_signals": critical_signals,
            "period": {"start": thirty_days_ago.isoformat(), "end": now.isoformat()},
        }

    @staticmethod
    def _require_lab_id(lab_id: int | None) -> None:
        if not isinstance(lab_id, int) or lab_id <= 0:
            raise ValueError("A valid facility tenant is required")

    @staticmethod
    def _coerce_datetime(value: Any) -> datetime:
        if value is None:
            return datetime.now(UTC)
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value.astimezone(UTC)
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time(), tzinfo=UTC)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("Invalid ISO-8601 datetime") from exc
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        raise ValueError("Invalid datetime")

    def _get_schedule(self, schedule_id: str, lab_id: int, lock: bool = False) -> ImmunizationScheduleModel:
        query = self.db.query(ImmunizationScheduleModel).filter(
            ImmunizationScheduleModel.id == schedule_id,
            ImmunizationScheduleModel.lab_id == lab_id,
            ImmunizationScheduleModel.is_deleted.isnot(True),
        )
        if lock:
            query = query.with_for_update()
        model = query.first()
        if not model:
            raise ImmunizationScheduleNotFoundError()
        return model

    @staticmethod
    def _schedule_definition_to_dict(model: ImmunizationScheduleDefinitionModel) -> dict[str, Any]:
        return {
            "id": model.id,
            "schedule_version": model.schedule_version,
            "vaccine": model.vaccine,
            "vaccine_code": model.vaccine_code,
            "dose_number": model.dose_number,
            "total_doses": model.total_doses,
            "minimum_age_days": model.minimum_age_days,
            "recommended_age_days": model.recommended_age_days,
            "grace_period_days": model.grace_period_days,
            "is_active": model.is_active,
            "source_reference": model.source_reference,
        }

    def _schedule_from_model(self, m: ImmunizationScheduleModel) -> ImmunizationSchedule:
        return ImmunizationSchedule(
            id=m.id,
            patient_id=m.patient_id,
            health_number=m.health_number,
            newborn_id=m.newborn_id or "",
            schedule_definition_id=m.schedule_definition_id,
            schedule_version=m.schedule_version,
            vaccine=m.vaccine,
            vaccine_code=m.vaccine_code,
            dose_number=m.dose_number,
            total_doses=m.total_doses,
            due_date=m.due_date.isoformat() if m.due_date else "",
            scheduled_date=m.scheduled_date.isoformat() if m.scheduled_date else "",
            status=m.status,
            facility_id=m.facility_id or "",
            appointment_id=m.appointment_id or "",
            reminder_sent=bool(m.reminder_sent),
            reminder_sent_at=m.reminder_sent_at.isoformat() if m.reminder_sent_at else "",
            reminder_count=m.reminder_count or 0,
            contraindication_reason=m.contraindication_reason or "",
            refusal_reason=m.refusal_reason or "",
            notes=m.notes or "",
            follow_up_status=m.follow_up_status or "not_required",
            follow_up_priority=m.follow_up_priority or "normal",
            next_follow_up_date=m.next_follow_up_date.isoformat() if m.next_follow_up_date else "",
            non_administration_reason=m.non_administration_reason or "",
            non_administration_notes=m.non_administration_notes or "",
        )

    @staticmethod
    def _follow_up_from_model(m: ImmunizationFollowUpTaskModel) -> ImmunizationFollowUpTask:
        return ImmunizationFollowUpTask(
            id=m.id, schedule_id=m.schedule_id, patient_id=m.patient_id,
            health_number=m.health_number, vaccine=m.vaccine,
            due_date=m.due_date.isoformat() if m.due_date else "",
            status=m.status, priority=m.priority, reason=m.reason or "",
            next_action_at=m.next_action_at.isoformat() if m.next_action_at else "",
            consent_verified=bool(m.consent_verified), preferred_channel=m.preferred_channel or "",
            last_attempt_at=m.last_attempt_at.isoformat() if m.last_attempt_at else "",
            completed_at=m.completed_at.isoformat() if m.completed_at else "",
            completed_by=m.completed_by or "", notes=m.notes or "",
        )

    @staticmethod
    def _aefi_from_model(m: ImmunizationAdverseEventModel) -> ImmunizationAdverseEvent:
        return ImmunizationAdverseEvent(
            id=m.id, record_id=m.record_id, schedule_id=m.schedule_id or "",
            patient_id=m.patient_id, health_number=m.health_number or "", vaccine=m.vaccine,
            onset_at=m.onset_at.isoformat() if m.onset_at else "", severity=m.severity,
            symptoms=list(m.symptoms or []), treatment=m.treatment or "", outcome=m.outcome or "",
            investigation_status=m.investigation_status, reported_by=m.reported_by,
            reported_at=m.reported_at.isoformat() if m.reported_at else "", notes=m.notes or "",
        )

    @staticmethod
    def _catalog_from_model(m: VaccineCatalogModel) -> VaccineCatalog:
        return VaccineCatalog(
            id=m.id, vaccine_code=m.vaccine_code, name=m.name, name_ar=m.name_ar or "",
            unit=m.unit or "dose", manufacturer=m.manufacturer or "",
            storage_min_c=m.storage_min_c, storage_max_c=m.storage_max_c,
            source_reference=m.source_reference or "", is_active=bool(m.is_active),
        )

    @staticmethod
    def _lot_from_model(m: VaccineLotModel) -> VaccineLot:
        return VaccineLot(
            id=m.id, catalog_id=m.catalog_id, lot_number=m.lot_number,
            expiry_date=m.expiry_date.isoformat() if m.expiry_date else "",
            received_at=m.received_at.isoformat() if m.received_at else "",
            received_quantity=m.received_quantity or 0, available_quantity=m.available_quantity or 0,
            quarantined=bool(m.quarantined), quarantine_reason=m.quarantine_reason or "",
            storage_equipment_id=m.storage_equipment_id or "",
        )

    @staticmethod
    def _cold_chain_from_model(m: ColdChainReadingModel) -> ColdChainReading:
        return ColdChainReading(
            id=m.id, equipment_id=m.equipment_id,
            reading_at=m.reading_at.isoformat() if m.reading_at else "",
            temperature_c=float(m.temperature_c), minimum_allowed_c=m.minimum_allowed_c,
            maximum_allowed_c=m.maximum_allowed_c, status=m.status,
            source=m.source, recorded_by=m.recorded_by,
            alert_acknowledged=bool(m.alert_acknowledged), notes=m.notes or "",
        )

    def _case_from_model(self, m: DiseaseCaseModel) -> DiseaseCase:
        return DiseaseCase(id=m.id, disease_code=m.disease_code or "",
                           disease_name=m.disease_name or "", region=m.region or "",
                           is_confirmed=m.is_confirmed or False,
                           source=m.source or "laboratory", reported_by=m.reported_by or "",
                           reported_at=m.reported_at.isoformat() if m.reported_at else "")

    def _outbreak_from_model(self, m: OutbreakAlertModel) -> OutbreakAlert:
        return OutbreakAlert(id=m.id, disease=m.disease, region=m.region or "",
                              confirmed_cases=m.confirmed_cases or 0,
                              alert_level=m.alert_level or "information",
                              status=m.status or "monitoring",
                              recommendations=m.recommendations or "")

    def _immunization_from_model(self, m: ImmunizationRecordModel) -> ImmunizationRecord:
        return ImmunizationRecord(
            id=m.id,
            patient_id=m.patient_id or "",
            health_number=m.health_number or "",
            newborn_id=m.newborn_id or "",
            schedule_id=m.schedule_id or "",
            patient_name=m.patient_name or "",
            vaccine=m.vaccine,
            vaccine_code=m.vaccine_code or "",
            dose_number=m.dose_number or 1,
            total_doses=m.total_doses or 1,
            scheduled_date=m.scheduled_date.isoformat() if m.scheduled_date else "",
            due_date=m.due_date.isoformat() if m.due_date else "",
            status=m.status or ImmunizationStatus.ADMINISTERED.value,
            appointment_id=m.appointment_id or "",
            administration_date=m.administration_date.isoformat() if m.administration_date else "",
            administered_by=m.administered_by or "",
            facility_id=m.facility_id or "",
            lot_number=m.lot_number or "",
            expiry_date=m.expiry_date.isoformat() if m.expiry_date else "",
            route=m.route or "intramuscular",
            site=m.site or "deltoid",
            batch_number=m.batch_number or "",
            manufacturer=m.manufacturer or "",
            is_boosted=bool(m.is_boosted),
            adverse_event=m.adverse_event or "",
            reminder_sent=bool(m.reminder_sent),
            reminder_sent_at=m.reminder_sent_at.isoformat() if m.reminder_sent_at else "",
            notes=m.notes or "",
        )

    def _report_from_model(self, m: PublicHealthReportModel) -> PublicHealthReport:
        return PublicHealthReport(id=m.id, report_type=m.report_type or "weekly",
                                   region=m.region or "",
                                   total_cases=m.total_cases or 0,
                                   total_deaths=m.total_deaths or 0,
                                   key_findings=m.key_findings or "",
                                   published_by=m.published_by or "")
