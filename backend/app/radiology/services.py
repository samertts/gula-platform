from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.radiology.enums import (
    CriticalFindingStatus,
    ExamStatus,
    ReportStatus,
)
from app.radiology.models import (
    CriticalFinding,
    ImageAnnotation,
    ImageMeasurement,
    Protocol,
    RadiologyAppointment,
    RadiologyExam,
    RadiologyImage,
    RadiologyOrder,
    RadiologyReport,
    RadiologySeries,
    ReportTemplate,
    WorklistEntry,
)
from app.services.audit_service import log_action

logger = logging.getLogger("gula.radiology.services")


class RadiologyWorkflowError(ValueError):
    """Raised when a radiology workflow safety invariant is violated."""


_EXAM_TRANSITIONS: dict[ExamStatus, set[ExamStatus]] = {
    ExamStatus.SCHEDULED: {ExamStatus.CHECKED_IN, ExamStatus.CANCELLED},
    ExamStatus.CHECKED_IN: {ExamStatus.IN_PROGRESS, ExamStatus.CANCELLED},
    ExamStatus.IN_PROGRESS: {ExamStatus.COMPLETED, ExamStatus.CANCELLED},
    ExamStatus.COMPLETED: {ExamStatus.VERIFIED},
    ExamStatus.VERIFIED: {ExamStatus.REPORTED},
    ExamStatus.REPORTED: {ExamStatus.APPROVED},
    ExamStatus.APPROVED: set(),
    ExamStatus.CANCELLED: set(),
}




def _generate_accession() -> str:
    date_part = datetime.now(UTC).strftime("%Y%m%d")
    uid = str(uuid.uuid4()).replace("-", "").upper()[:8]
    return f"ACC-{date_part}-{uid}"


def _generate_order_number() -> str:
    date_part = datetime.now(UTC).strftime("%Y%m%d")
    uid = str(uuid.uuid4()).replace("-", "").upper()[:6]
    return f"ORD-{date_part}-{uid}"


# ==============================================================================
# RadiologyService
# ==============================================================================


class RadiologyService:
    def __init__(
        self,
        db: Session,
        actor_user_id: int | None = None,
        actor_lab_id: int | None = None,
        actor_role: str | None = None,
    ):
        self.db = db
        self.actor_user_id = actor_user_id
        self.actor_lab_id = actor_lab_id
        self.actor_role = actor_role or "system"

    def _audit(self, action: str, resource_type: str, resource_id: str, details: dict[str, Any]) -> None:
        if self.actor_user_id is None or self.actor_lab_id is None:
            return
        log_action(
            self.db,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=self.actor_user_id,
            user_role=self.actor_role,
            lab_id=self.actor_lab_id,
            details=details,
        )

    def _patient_scoped_query(self, model: Any, patient_ids: set[str] | None):
        query = self.db.query(model)
        if patient_ids is not None:
            query = query.filter(model.patient_id.in_(patient_ids))
        return query

    # ── Order Management ──────────────────────────────────────────────────────

    def create_order(
        self,
        patient_id: str,
        modality: str,
        body_part: str | None = None,
        clinical_indication: str | None = None,
        ordering_provider_id: str | None = None,
        encounter_id: str | None = None,
        priority: str = "routine",
        diagnosis_code: str | None = None,
        diagnosis_system: str | None = None,
        ordering_department_id: str | None = None,
        notes: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RadiologyOrder:
        order = RadiologyOrder(
            patient_id=patient_id,
            encounter_id=encounter_id,
            ordering_provider_id=ordering_provider_id,
            order_number=_generate_order_number(),
            modality=modality.upper(),
            body_part=body_part,
            clinical_indication=clinical_indication,
            diagnosis_code=diagnosis_code,
            diagnosis_system=diagnosis_system,
            priority=priority,
            status="pending",
            requested_date=datetime.now(UTC),
            ordering_department_id=ordering_department_id,
            notes=notes,
            extra_metadata=metadata or {},
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        logger.info("Radiology order created: %s", order.order_number)
        return order

    def get_order(self, order_id: str) -> RadiologyOrder | None:
        return self.db.query(RadiologyOrder).filter(RadiologyOrder.id == order_id, ~RadiologyOrder.is_deleted).first()

    def get_order_by_number(self, order_number: str) -> RadiologyOrder | None:
        return self.db.query(RadiologyOrder).filter(RadiologyOrder.order_number == order_number, ~RadiologyOrder.is_deleted).first()

    def search_orders(
        self,
        patient_id: str | None = None,
        modality: str | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        priority: str | None = None,
        skip: int = 0,
        limit: int = 50,
        patient_ids: set[str] | None = None,
    ) -> list[RadiologyOrder]:
        q = self.db.query(RadiologyOrder).filter(~RadiologyOrder.is_deleted)
        if patient_id:
            q = q.filter(RadiologyOrder.patient_id == patient_id)
        elif patient_ids is not None:
            q = q.filter(RadiologyOrder.patient_id.in_(patient_ids))
        if modality:
            q = q.filter(RadiologyOrder.modality == modality.upper())
        if status:
            q = q.filter(RadiologyOrder.status == status)
        if date_from:
            q = q.filter(RadiologyOrder.requested_date >= date_from)
        if date_to:
            q = q.filter(RadiologyOrder.requested_date <= date_to)
        if priority:
            q = q.filter(RadiologyOrder.priority == priority)
        q = q.order_by(RadiologyOrder.requested_date.desc())
        return q.offset(skip).limit(limit).all()

    def update_order_status(self, order_id: str, status: str) -> RadiologyOrder | None:
        order = self.get_order(order_id)
        if not order:
            return None
        order.status = status
        self.db.commit()
        self.db.refresh(order)
        return order

    # ── Appointment Management ────────────────────────────────────────────────

    def schedule_appointment(
        self,
        order_id: str,
        patient_id: str,
        scheduled_date: datetime,
        modality: str,
        scheduled_time: str | None = None,
        duration_minutes: int = 30,
        room: str | None = None,
        technologist_id: str | None = None,
        preparation_instructions: str | None = None,
        contrast_required: bool = False,
        contrast_details: str | None = None,
        notes: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RadiologyAppointment:
        appointment = RadiologyAppointment(
            order_id=order_id,
            patient_id=patient_id,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            duration_minutes=duration_minutes,
            modality=modality.upper(),
            room=room,
            technologist_id=technologist_id,
            status="scheduled",
            preparation_instructions=preparation_instructions,
            contrast_required=contrast_required,
            contrast_details=contrast_details,
            notes=notes,
            extra_metadata=metadata or {},
        )
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        logger.info("Radiology appointment scheduled: %s", appointment.id)
        return appointment

    def get_appointment(self, appointment_id: str) -> RadiologyAppointment | None:
        return self.db.query(RadiologyAppointment).filter(RadiologyAppointment.id == appointment_id, ~RadiologyAppointment.is_deleted).first()

    def list_appointments(
        self,
        patient_id: str | None = None,
        modality: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
        patient_ids: set[str] | None = None,
    ) -> list[RadiologyAppointment]:
        q = self.db.query(RadiologyAppointment).filter(~RadiologyAppointment.is_deleted)
        if patient_id:
            q = q.filter(RadiologyAppointment.patient_id == patient_id)
        elif patient_ids is not None:
            q = q.filter(RadiologyAppointment.patient_id.in_(patient_ids))
        if modality:
            q = q.filter(RadiologyAppointment.modality == modality.upper())
        if date_from:
            q = q.filter(RadiologyAppointment.scheduled_date >= date_from)
        if date_to:
            q = q.filter(RadiologyAppointment.scheduled_date <= date_to)
        if status:
            q = q.filter(RadiologyAppointment.status == status)
        q = q.order_by(RadiologyAppointment.scheduled_date.asc())
        return q.offset(skip).limit(limit).all()

    def check_in_appointment(self, appointment_id: str) -> RadiologyAppointment | None:
        appointment = self.get_appointment(appointment_id)
        if not appointment:
            return None
        appointment.check_in_time = datetime.now(UTC)
        appointment.status = "checked_in"
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def arrive_appointment(self, appointment_id: str) -> RadiologyAppointment | None:
        appointment = self.get_appointment(appointment_id)
        if not appointment:
            return None
        appointment.arrival_time = datetime.now(UTC)
        appointment.status = "arrived"
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    # ── Exam Management ───────────────────────────────────────────────────────

    def create_exam(
        self,
        order_id: str | None = None,
        appointment_id: str | None = None,
        patient_id: str = "",
        accession_number: str | None = None,
        modality: str = "",
        body_part: str | None = None,
        laterality: str | None = None,
        protocol_id: str | None = None,
        exam_code: str | None = None,
        exam_name: str | None = None,
        technologist_id: str | None = None,
        radiologist_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RadiologyExam:
        exam = RadiologyExam(
            order_id=order_id,
            appointment_id=appointment_id,
            patient_id=patient_id,
            accession_number=accession_number or _generate_accession(),
            modality=modality.upper(),
            body_part=body_part,
            laterality=laterality,
            protocol_id=protocol_id,
            status=ExamStatus.SCHEDULED,
            exam_code=exam_code,
            exam_name=exam_name,
            technologist_id=technologist_id,
            radiologist_id=radiologist_id,
            extra_metadata=metadata or {},
        )
        self.db.add(exam)
        self.db.commit()
        self.db.refresh(exam)
        logger.info("Radiology exam created: %s", exam.accession_number)
        return exam

    def get_exam(self, exam_id: str) -> RadiologyExam | None:
        return self.db.query(RadiologyExam).filter(RadiologyExam.id == exam_id, ~RadiologyExam.is_deleted).first()

    def get_exam_by_accession(self, accession_number: str) -> RadiologyExam | None:
        return self.db.query(RadiologyExam).filter(RadiologyExam.accession_number == accession_number, ~RadiologyExam.is_deleted).first()

    def list_exams(
        self,
        patient_id: str | None = None,
        modality: str | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        technologist_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
        patient_ids: set[str] | None = None,
    ) -> list[RadiologyExam]:
        q = self.db.query(RadiologyExam).filter(~RadiologyExam.is_deleted)
        if patient_id:
            q = q.filter(RadiologyExam.patient_id == patient_id)
        elif patient_ids is not None:
            q = q.filter(RadiologyExam.patient_id.in_(patient_ids))
        if modality:
            q = q.filter(RadiologyExam.modality == modality.upper())
        if status:
            q = q.filter(RadiologyExam.status == status)
        if date_from:
            q = q.filter(RadiologyExam.started_at >= date_from)
        if date_to:
            q = q.filter(RadiologyExam.started_at <= date_to)
        if technologist_id:
            q = q.filter(RadiologyExam.technologist_id == technologist_id)
        q = q.order_by(RadiologyExam.created_at.desc())
        return q.offset(skip).limit(limit).all()

    def update_exam_status(
        self,
        exam_id: str,
        status: ExamStatus,
        *,
        expected_version: int,
    ) -> RadiologyExam | None:
        exam = self.db.query(RadiologyExam).filter(
            RadiologyExam.id == exam_id,
            ~RadiologyExam.is_deleted,
        ).with_for_update().first()
        if not exam:
            return None
        if exam.version != expected_version:
            raise RadiologyWorkflowError("radiology examination version conflict")
        current = ExamStatus(exam.status)
        if status not in _EXAM_TRANSITIONS[current]:
            raise RadiologyWorkflowError(f"illegal examination transition: {current.value} -> {status.value}")
        state_before = current.value
        exam.status = status
        if status == ExamStatus.IN_PROGRESS and not exam.started_at:
            exam.started_at = datetime.now(UTC)
        elif status == ExamStatus.COMPLETED and not exam.completed_at:
            exam.completed_at = datetime.now(UTC)
        exam.version += 1
        self.db.flush()
        self._audit(
            "radiology.exam.status_changed",
            "radiology_exam",
            exam.id,
            {"state_before": state_before, "state_after": status.value, "version": exam.version},
        )
        return exam

    def update_exam_images(self, exam_id: str, images_count: int, series_count: int) -> RadiologyExam | None:
        exam = self.get_exam(exam_id)
        if not exam:
            return None
        exam.images_count = images_count
        exam.series_count = series_count
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def perform_exam(
        self,
        exam_id: str,
        technologist_id: str,
        contrast_used: bool = False,
        contrast_type: str | None = None,
        contrast_amount_ml: float | None = None,
        contrast_batch: str | None = None,
        total_dose: float | None = None,
        dose_unit: str | None = None,
        image_quality: str | None = None,
        notes: str | None = None,
    ) -> RadiologyExam | None:
        exam = self.get_exam(exam_id)
        if not exam:
            return None
        exam.technologist_id = technologist_id
        exam.contrast_used = contrast_used
        if contrast_type:
            exam.contrast_type = contrast_type
        exam.contrast_amount_ml = contrast_amount_ml
        exam.contrast_batch = contrast_batch
        exam.total_dose = total_dose
        exam.dose_unit = dose_unit
        if image_quality:
            exam.image_quality = image_quality
        exam.notes = notes
        exam.status = ExamStatus.COMPLETED
        exam.completed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(exam)
        return exam

    # ── Series & Image Management ─────────────────────────────────────────────

    def create_series(
        self,
        exam_id: str,
        series_instance_uid: str,
        series_number: int | None = None,
        series_description: str | None = None,
        modality: str = "",
        body_part: str | None = None,
        laterality: str | None = None,
        protocol_name: str | None = None,
        image_count: int = 0,
        manufacturer: str | None = None,
        device_model: str | None = None,
        acquisition_date: datetime | None = None,
        kvp: float | None = None,
        mas: float | None = None,
        slice_thickness: float | None = None,
        fov: str | None = None,
        matrix_size: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RadiologySeries:
        series = RadiologySeries(
            exam_id=exam_id,
            series_instance_uid=series_instance_uid,
            series_number=series_number,
            series_description=series_description,
            modality=modality.upper(),
            body_part=body_part,
            laterality=laterality,
            protocol_name=protocol_name,
            image_count=image_count,
            manufacturer=manufacturer,
            device_model=device_model,
            acquisition_date=acquisition_date,
            kvp=kvp,
            mas=mas,
            slice_thickness=slice_thickness,
            fov=fov,
            matrix_size=matrix_size,
            extra_metadata=metadata or {},
        )
        self.db.add(series)
        self.db.commit()
        self.db.refresh(series)
        return series

    def create_image(
        self,
        series_id: str,
        sop_instance_uid: str,
        instance_number: int | None = None,
        image_type: str | None = None,
        laterality: str | None = None,
        view_position: str | None = None,
        acquisition_date: datetime | None = None,
        file_size_bytes: int | None = None,
        file_format: str = "dcm",
        storage_path: str = "",
        storage_tier: str = "hot",
        checksum: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RadiologyImage:
        image = RadiologyImage(
            series_id=series_id,
            sop_instance_uid=sop_instance_uid,
            instance_number=instance_number,
            image_type=image_type,
            laterality=laterality,
            view_position=view_position,
            acquisition_date=acquisition_date,
            file_size_bytes=file_size_bytes,
            file_format=file_format,
            storage_path=storage_path,
            storage_tier=storage_tier,
            checksum=checksum,
            extra_metadata=metadata or {},
        )
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        return image

    def get_series_for_exam(self, exam_id: str) -> list[RadiologySeries]:
        return self.db.query(RadiologySeries).filter(RadiologySeries.exam_id == exam_id, ~RadiologySeries.is_deleted).all()

    def get_images_for_series(self, series_id: str) -> list[RadiologyImage]:
        return self.db.query(RadiologyImage).filter(RadiologyImage.series_id == series_id, ~RadiologyImage.is_deleted).all()

    # ── Reporting ─────────────────────────────────────────────────────────────

    def create_report(
        self,
        exam_id: str,
        accession_number: str,
        patient_id: str,
        radiologist_id: str | None = None,
        ordering_provider_id: str | None = None,
        clinical_indication: str | None = None,
        technique: str | None = None,
        comparison: str | None = None,
        findings: str | None = None,
        impression: str | None = None,
        conclusion: str | None = None,
        recommendation: str | None = None,
        body_text: str | None = None,
        transcribed_by: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RadiologyReport:
        report = RadiologyReport(
            exam_id=exam_id,
            accession_number=accession_number,
            patient_id=patient_id,
            radiologist_id=radiologist_id,
            ordering_provider_id=ordering_provider_id,
            status=ReportStatus.DRAFT,
            clinical_indication=clinical_indication,
            technique=technique,
            comparison=comparison,
            findings=findings,
            impression=impression,
            conclusion=conclusion,
            recommendation=recommendation,
            body_text=body_text,
            transcribed_by=transcribed_by,
            draft_at=datetime.now(UTC),
            extra_metadata=metadata or {},
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        logger.info("Radiology report created (draft): %s", report.id)
        return report

    def get_report(self, report_id: str) -> RadiologyReport | None:
        return self.db.query(RadiologyReport).filter(RadiologyReport.id == report_id, ~RadiologyReport.is_deleted).first()

    def get_report_by_exam(self, exam_id: str) -> RadiologyReport | None:
        return self.db.query(RadiologyReport).filter(RadiologyReport.exam_id == exam_id, ~RadiologyReport.is_deleted).order_by(RadiologyReport.version.desc()).first()

    def search_reports(
        self,
        patient_id: str | None = None,
        radiologist_id: str | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        critical_finding: bool | None = None,
        skip: int = 0,
        limit: int = 50,
        patient_ids: set[str] | None = None,
    ) -> list[RadiologyReport]:
        q = self.db.query(RadiologyReport).filter(~RadiologyReport.is_deleted)
        if patient_id:
            q = q.filter(RadiologyReport.patient_id == patient_id)
        elif patient_ids is not None:
            q = q.filter(RadiologyReport.patient_id.in_(patient_ids))
        if radiologist_id:
            q = q.filter(RadiologyReport.radiologist_id == radiologist_id)
        if status:
            q = q.filter(RadiologyReport.status == status)
        if date_from:
            q = q.filter(RadiologyReport.created_at >= date_from)
        if date_to:
            q = q.filter(RadiologyReport.created_at <= date_to)
        if critical_finding is not None:
            q = q.filter(RadiologyReport.critical_finding == critical_finding)
        q = q.order_by(RadiologyReport.created_at.desc())
        return q.offset(skip).limit(limit).all()

    def _locked_report(self, report_id: str) -> RadiologyReport | None:
        return self.db.query(RadiologyReport).filter(
            RadiologyReport.id == report_id,
            ~RadiologyReport.is_deleted,
        ).with_for_update().first()

    def save_report_draft(
        self,
        report_id: str,
        *,
        expected_version: int,
        findings: str | None = None,
        impression: str | None = None,
        conclusion: str | None = None,
        recommendation: str | None = None,
        body_text: str | None = None,
    ) -> RadiologyReport | None:
        report = self._locked_report(report_id)
        if not report:
            return None
        if report.version != expected_version:
            raise RadiologyWorkflowError("radiology report version conflict")
        if report.status not in {ReportStatus.DRAFT, ReportStatus.PRELIMINARY}:
            raise RadiologyWorkflowError("only draft or preliminary reports can be edited")
        state_before = report.status.value
        for field, value in {
            "findings": findings,
            "impression": impression,
            "conclusion": conclusion,
            "recommendation": recommendation,
            "body_text": body_text,
        }.items():
            if value is not None:
                setattr(report, field, value)
        report.status = ReportStatus.DRAFT
        report.version += 1
        self.db.flush()
        self._audit(
            "radiology.report.draft_saved",
            "radiology_report",
            report.id,
            {"state_before": state_before, "state_after": report.status.value, "version": report.version},
        )
        return report

    def finalize_report(
        self,
        report_id: str,
        *,
        expected_version: int,
        radiologist_id: str,
    ) -> RadiologyReport | None:
        report = self._locked_report(report_id)
        if not report:
            return None
        if report.version != expected_version:
            raise RadiologyWorkflowError("radiology report version conflict")
        if report.status not in {ReportStatus.DRAFT, ReportStatus.PRELIMINARY}:
            raise RadiologyWorkflowError("only draft or preliminary reports can be finalized")
        if not radiologist_id:
            raise RadiologyWorkflowError("a reporting radiologist is required")
        if not any((report.findings, report.impression, report.conclusion, report.body_text)):
            raise RadiologyWorkflowError("a report cannot be finalized without clinical content")
        if report.critical_finding:
            notified = self.db.query(CriticalFinding).filter(
                CriticalFinding.report_id == report.id,
                CriticalFinding.status.in_([CriticalFindingStatus.NOTIFIED, CriticalFindingStatus.ACKNOWLEDGED]),
                ~CriticalFinding.is_deleted,
            ).first()
            if notified is None:
                raise RadiologyWorkflowError("critical reports require a documented notification before finalization")
        state_before = report.status.value
        report.radiologist_id = radiologist_id
        report.status = ReportStatus.FINAL
        report.completed_at = datetime.now(UTC)
        report.version += 1
        self.db.flush()
        self._audit(
            "radiology.report.finalized",
            "radiology_report",
            report.id,
            {"state_before": state_before, "state_after": report.status.value, "version": report.version},
        )
        logger.info("Radiology report finalized: %s", report.id)
        return report

    def preliminary_report(self, report_id: str) -> RadiologyReport | None:
        report = self.get_report(report_id)
        if not report:
            return None
        report.status = ReportStatus.PRELIMINARY
        report.preliminary_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(report)
        return report

    def amend_report(
        self,
        report_id: str,
        *,
        expected_version: int,
        findings: str,
        impression: str,
        reason: str,
        conclusion: str | None = None,
        recommendation: str | None = None,
        amended_by: str,
    ) -> RadiologyReport | None:
        report = self._locked_report(report_id)
        if not report:
            return None
        if report.version != expected_version:
            raise RadiologyWorkflowError("radiology report version conflict")
        if report.status not in {ReportStatus.FINAL, ReportStatus.AMENDED}:
            raise RadiologyWorkflowError("only a finalized report can be amended")
        if not reason.strip():
            raise RadiologyWorkflowError("an amendment reason is required")
        if not findings.strip() or not impression.strip():
            raise RadiologyWorkflowError("amended reports require findings and impression")
        state_before = report.status.value
        report.version += 1
        report.findings = findings
        report.impression = impression
        if conclusion is not None:
            report.conclusion = conclusion
        if recommendation is not None:
            report.recommendation = recommendation
        report.status = ReportStatus.AMENDED
        report.amended_at = datetime.now(UTC)
        metadata = dict(report.extra_metadata or {})
        amendments = list(metadata.get("amendments", []))
        amendments.append({"version": report.version, "reason": reason, "amended_by": amended_by, "at": report.amended_at.isoformat()})
        metadata["amendments"] = amendments
        report.extra_metadata = metadata
        self.db.flush()
        self._audit(
            "radiology.report.amended",
            "radiology_report",
            report.id,
            {"state_before": state_before, "state_after": report.status.value, "version": report.version, "reason": reason},
        )
        logger.info("Radiology report amended (v%s): %s", report.version, report.id)
        return report

    def verify_report(
        self,
        report_id: str,
        *,
        expected_version: int,
        verified_by: str,
    ) -> RadiologyReport | None:
        report = self._locked_report(report_id)
        if not report:
            return None
        if report.version != expected_version:
            raise RadiologyWorkflowError("radiology report version conflict")
        if report.status not in {ReportStatus.FINAL, ReportStatus.AMENDED}:
            raise RadiologyWorkflowError("only finalized or amended reports can be verified")
        if not verified_by or verified_by == report.radiologist_id:
            raise RadiologyWorkflowError("a second qualified reviewer must verify the report")
        report.verified_at = datetime.now(UTC)
        report.version += 1
        metadata = dict(report.extra_metadata or {})
        metadata["verified_by"] = verified_by
        report.extra_metadata = metadata
        self.db.flush()
        self._audit(
            "radiology.report.verified",
            "radiology_report",
            report.id,
            {"state_before": report.status.value, "state_after": report.status.value, "version": report.version, "verified_by": verified_by},
        )
        return report

    # ── Report Templates ──────────────────────────────────────────────────────

    def create_report_template(
        self,
        template_code: str,
        template_name: str,
        template_name_ar: str | None = None,
        modality: str | None = None,
        body_part: str | None = None,
        structured_template: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ReportTemplate:
        template = ReportTemplate(
            template_code=template_code,
            template_name=template_name,
            template_name_ar=template_name_ar,
            modality=modality.upper() if modality else None,
            body_part=body_part,
            structured_template=structured_template or {},
            is_active=True,
            extra_metadata=metadata or {},
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def list_report_templates(self, modality: str | None = None, body_part: str | None = None) -> list[ReportTemplate]:
        q = self.db.query(ReportTemplate).filter(ReportTemplate.is_active, ~ReportTemplate.is_deleted)
        if modality:
            q = q.filter(ReportTemplate.modality == modality.upper())
        if body_part:
            q = q.filter(ReportTemplate.body_part == body_part)
        return q.all()

    # ── Critical Findings ─────────────────────────────────────────────────────

    def create_critical_finding(
        self,
        exam_id: str,
        finding_type: str,
        finding_description: str,
        *,
        report_id: str | None = None,
        notes: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CriticalFinding:
        if not finding_description.strip():
            raise RadiologyWorkflowError("critical finding description is required")
        exam = self.db.query(RadiologyExam).filter(
            RadiologyExam.id == exam_id,
            ~RadiologyExam.is_deleted,
        ).with_for_update().first()
        if exam is None:
            raise RadiologyWorkflowError("critical finding exam not found")
        if exam.status not in {ExamStatus.COMPLETED, ExamStatus.VERIFIED, ExamStatus.REPORTED, ExamStatus.APPROVED}:
            raise RadiologyWorkflowError("critical findings require a completed examination")
        if report_id:
            report = self._locked_report(report_id)
            if report is None or report.exam_id != exam_id:
                raise RadiologyWorkflowError("critical finding report does not belong to the examination")
            report.critical_finding = True
            report.critical_finding_type = finding_type
            report.version += 1
        exam.version += 1
        finding = CriticalFinding(
            exam_id=exam_id,
            report_id=report_id,
            finding_type=finding_type,
            finding_description=finding_description,
            status=CriticalFindingStatus.PENDING,
            notes=notes,
            extra_metadata=metadata or {},
        )
        self.db.add(finding)
        self.db.flush()
        self._audit(
            "radiology.critical_finding.created",
            "radiology_critical_finding",
            finding.id,
            {"exam_id": exam_id, "report_id": report_id, "state_after": finding.status.value},
        )
        logger.warning("Critical finding created: %s on exam %s", finding_type, exam_id)
        return finding

    def get_critical_finding(self, finding_id: str) -> CriticalFinding | None:
        return self.db.query(CriticalFinding).filter(CriticalFinding.id == finding_id, ~CriticalFinding.is_deleted).first()

    def list_critical_findings(
        self,
        status: str | None = None,
        exam_id: str | None = None,
        notified_to: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
        patient_ids: set[str] | None = None,
    ) -> list[CriticalFinding]:
        q = self.db.query(CriticalFinding).filter(~CriticalFinding.is_deleted)
        if patient_ids is not None:
            q = q.join(RadiologyExam, CriticalFinding.exam_id == RadiologyExam.id).filter(
                RadiologyExam.patient_id.in_(patient_ids),
                ~RadiologyExam.is_deleted,
            )
        if status:
            q = q.filter(CriticalFinding.status == status)
        if exam_id:
            q = q.filter(CriticalFinding.exam_id == exam_id)
        if notified_to:
            q = q.filter(CriticalFinding.notified_to == notified_to)
        if date_from:
            q = q.filter(CriticalFinding.notification_time >= date_from)
        if date_to:
            q = q.filter(CriticalFinding.notification_time <= date_to)
        q = q.order_by(CriticalFinding.created_at.desc())
        return q.offset(skip).limit(limit).all()

    def acknowledge_critical_finding(
        self,
        finding_id: str,
        *,
        expected_version: int,
        acknowledged_by: str,
        notes: str | None = None,
    ) -> CriticalFinding | None:
        finding = self.db.query(CriticalFinding).filter(
            CriticalFinding.id == finding_id,
            ~CriticalFinding.is_deleted,
        ).with_for_update().first()
        if not finding:
            return None
        if finding.version != expected_version:
            raise RadiologyWorkflowError("critical finding version conflict")
        if finding.status != CriticalFindingStatus.NOTIFIED:
            raise RadiologyWorkflowError("only a notified critical finding can be acknowledged")
        if not acknowledged_by or acknowledged_by != finding.notified_to:
            raise RadiologyWorkflowError("only the documented recipient can acknowledge a critical finding")
        state_before = finding.status.value
        finding.status = CriticalFindingStatus.ACKNOWLEDGED
        finding.acknowledged_by = acknowledged_by
        finding.acknowledgement_time = datetime.now(UTC)
        if notes:
            finding.notes = notes
        finding.version += 1
        self.db.flush()
        self._audit(
            "radiology.critical_finding.acknowledged",
            "radiology_critical_finding",
            finding.id,
            {"state_before": state_before, "state_after": finding.status.value, "version": finding.version},
        )
        return finding

    def notify_critical_finding(
        self,
        finding_id: str,
        *,
        expected_version: int,
        notified_by: str,
        notified_to: str,
    ) -> CriticalFinding | None:
        finding = self.db.query(CriticalFinding).filter(
            CriticalFinding.id == finding_id,
            ~CriticalFinding.is_deleted,
        ).with_for_update().first()
        if not finding:
            return None
        if finding.version != expected_version:
            raise RadiologyWorkflowError("critical finding version conflict")
        if finding.status not in {CriticalFindingStatus.PENDING, CriticalFindingStatus.ESCALATED}:
            raise RadiologyWorkflowError("only pending or escalated critical findings can be notified")
        if not notified_by or not notified_to:
            raise RadiologyWorkflowError("notification sender and recipient are required")
        state_before = finding.status.value
        finding.notified_by = notified_by
        finding.notified_to = notified_to
        finding.notification_time = datetime.now(UTC)
        finding.status = CriticalFindingStatus.NOTIFIED
        finding.version += 1
        self.db.flush()
        self._audit(
            "radiology.critical_finding.notified",
            "radiology_critical_finding",
            finding.id,
            {"state_before": state_before, "state_after": finding.status.value, "version": finding.version, "notified_to": notified_to},
        )
        return finding

    # ── Worklist Management ───────────────────────────────────────────────────

    def get_technologist_worklist(self, modality: str | None = None, date: datetime | None = None, patient_ids: set[str] | None = None) -> list[RadiologyExam]:
        q = self.db.query(RadiologyExam).filter(~RadiologyExam.is_deleted)
        if patient_ids is not None:
            q = q.filter(RadiologyExam.patient_id.in_(patient_ids))
        if modality:
            q = q.filter(RadiologyExam.modality == modality.upper())
        if date:
            q = q.filter(RadiologyExam.created_at >= date, RadiologyExam.created_at < date + timedelta(days=1))
        q = q.filter(RadiologyExam.status.in_([ExamStatus.SCHEDULED, ExamStatus.CHECKED_IN, ExamStatus.IN_PROGRESS]))
        q = q.order_by(RadiologyExam.created_at.asc())
        return q.all()

    def get_radiologist_worklist(self, status: str | None = None, priority: str | None = None, patient_ids: set[str] | None = None) -> list[RadiologyExam]:
        q = self.db.query(RadiologyExam).filter(~RadiologyExam.is_deleted)
        if patient_ids is not None:
            q = q.filter(RadiologyExam.patient_id.in_(patient_ids))
        status_filter = [ExamStatus.COMPLETED, ExamStatus.VERIFIED]
        if status:
            status_filter = [status]
        q = q.filter(RadiologyExam.status.in_(status_filter))
        q = q.order_by(RadiologyExam.completed_at.asc().nullslast())
        return q.all()

    def get_modality_worklist(
        self,
        modality_device_id: str | None = None,
        patient_ids: set[str] | None = None,
    ) -> list[WorklistEntry]:
        q = self.db.query(WorklistEntry).filter(~WorklistEntry.is_deleted)
        if patient_ids is not None:
            q = q.filter(WorklistEntry.patient_id.in_(patient_ids))
        if modality_device_id:
            q = q.filter(WorklistEntry.modality_device_id == modality_device_id)
        q = q.filter(WorklistEntry.status == "scheduled")
        q = q.order_by(WorklistEntry.scheduled_datetime.asc())
        return q.all()

    # ── Protocol Management ───────────────────────────────────────────────────

    def create_protocol(
        self,
        code: str,
        name: str,
        modality: str,
        name_ar: str | None = None,
        body_part: str | None = None,
        protocol_type: str = "standard",
        contrast_protocol: str | None = None,
        typical_duration: int | None = None,
        typical_dose: str | None = None,
        preparation_instructions: str | None = None,
        positioning_instructions: str | None = None,
        series_parameters: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Protocol:
        protocol = Protocol(
            code=code,
            name=name,
            name_ar=name_ar,
            modality=modality.upper(),
            body_part=body_part,
            protocol_type=protocol_type,
            contrast_protocol=contrast_protocol,
            typical_duration=typical_duration,
            typical_dose=typical_dose,
            preparation_instructions=preparation_instructions,
            positioning_instructions=positioning_instructions,
            series_parameters=series_parameters or {},
            is_active=True,
            extra_metadata=metadata or {},
        )
        self.db.add(protocol)
        self.db.commit()
        self.db.refresh(protocol)
        return protocol

    def get_protocol(self, protocol_id: str) -> Protocol | None:
        return self.db.query(Protocol).filter(Protocol.id == protocol_id, ~Protocol.is_deleted).first()

    def list_protocols(self, modality: str | None = None, body_part: str | None = None) -> list[Protocol]:
        q = self.db.query(Protocol).filter(Protocol.is_active, ~Protocol.is_deleted)
        if modality:
            q = q.filter(Protocol.modality == modality.upper())
        if body_part:
            q = q.filter(Protocol.body_part == body_part)
        return q.all()

    # ── Dashboard / Analytics ─────────────────────────────────────────────────

    def get_exam_volume(
        self,
        date_from: datetime,
        date_to: datetime,
        patient_ids: set[str] | None = None,
    ) -> dict[str, Any]:
        total = self._patient_scoped_query(RadiologyExam, patient_ids).filter(
            ~RadiologyExam.is_deleted,
            RadiologyExam.created_at >= date_from,
            RadiologyExam.created_at <= date_to,
        ).count()
        by_modality = {}
        for modality in self._patient_scoped_query(RadiologyExam, patient_ids).with_entities(RadiologyExam.modality).filter(
            ~RadiologyExam.is_deleted,
            RadiologyExam.created_at >= date_from,
            RadiologyExam.created_at <= date_to,
        ).distinct().all():
            mod = modality[0]
            cnt = self._patient_scoped_query(RadiologyExam, patient_ids).filter(
                RadiologyExam.modality == mod,
                ~RadiologyExam.is_deleted,
                RadiologyExam.created_at >= date_from,
                RadiologyExam.created_at <= date_to,
            ).count()
            by_modality[mod.value if hasattr(mod, "value") else str(mod)] = cnt
        return {
            "total": total,
            "by_modality": by_modality,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
        }

    def get_report_tat(
        self,
        date_from: datetime,
        date_to: datetime,
        patient_ids: set[str] | None = None,
    ) -> dict[str, Any]:
        reports = self._patient_scoped_query(RadiologyReport, patient_ids).filter(
            ~RadiologyReport.is_deleted,
            RadiologyReport.status.in_([ReportStatus.FINAL, ReportStatus.AMENDED]),
            RadiologyReport.completed_at >= date_from,
            RadiologyReport.completed_at <= date_to,
        ).all()
        tat_minutes = []
        for r in reports:
            if r.draft_at and r.completed_at:
                delta = (r.completed_at - r.draft_at).total_seconds() / 60.0
                tat_minutes.append(delta)
        avg = sum(tat_minutes) / len(tat_minutes) if tat_minutes else 0
        return {
            "average_minutes": round(avg, 2),
            "count": len(tat_minutes),
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
        }

    def get_modality_utilization(
        self,
        date_from: datetime,
        date_to: datetime,
        patient_ids: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        results = []
        for mod_enum in self._patient_scoped_query(RadiologyExam, patient_ids).with_entities(RadiologyExam.modality).filter(
            ~RadiologyExam.is_deleted,
            RadiologyExam.created_at >= date_from,
            RadiologyExam.created_at <= date_to,
        ).distinct().all():
            mod = mod_enum[0]
            total = self._patient_scoped_query(RadiologyExam, patient_ids).filter(
                RadiologyExam.modality == mod,
                ~RadiologyExam.is_deleted,
                RadiologyExam.created_at >= date_from,
                RadiologyExam.created_at <= date_to,
            ).count()
            completed = self._patient_scoped_query(RadiologyExam, patient_ids).filter(
                RadiologyExam.modality == mod,
                RadiologyExam.status == ExamStatus.COMPLETED,
                ~RadiologyExam.is_deleted,
                RadiologyExam.created_at >= date_from,
                RadiologyExam.created_at <= date_to,
            ).count()
            results.append({
                "modality": mod.value if hasattr(mod, "value") else str(mod),
                "total": total,
                "completed": completed,
                "utilization_pct": round((completed / total * 100) if total else 0, 2),
            })
        return results

    def get_workload_by_radiologist(
        self,
        date_from: datetime,
        date_to: datetime,
        patient_ids: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        results = []
        radiologists = self._patient_scoped_query(RadiologyReport, patient_ids).with_entities(RadiologyReport.radiologist_id).filter(
            ~RadiologyReport.is_deleted,
            RadiologyReport.completed_at >= date_from,
            RadiologyReport.completed_at <= date_to,
            RadiologyReport.radiologist_id.isnot(None),
        ).distinct().all()
        for (rid,) in radiologists:
            count = self._patient_scoped_query(RadiologyReport, patient_ids).filter(
                RadiologyReport.radiologist_id == rid,
                ~RadiologyReport.is_deleted,
                RadiologyReport.completed_at >= date_from,
                RadiologyReport.completed_at <= date_to,
            ).count()
            results.append({"radiologist_id": rid, "report_count": count})
        return results

    def get_workload_by_technologist(
        self,
        date_from: datetime,
        date_to: datetime,
        patient_ids: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        results = []
        techs = self._patient_scoped_query(RadiologyExam, patient_ids).with_entities(RadiologyExam.technologist_id).filter(
            ~RadiologyExam.is_deleted,
            RadiologyExam.completed_at >= date_from,
            RadiologyExam.completed_at <= date_to,
            RadiologyExam.technologist_id.isnot(None),
        ).distinct().all()
        for (tid,) in techs:
            count = self._patient_scoped_query(RadiologyExam, patient_ids).filter(
                RadiologyExam.technologist_id == tid,
                ~RadiologyExam.is_deleted,
                RadiologyExam.completed_at >= date_from,
                RadiologyExam.completed_at <= date_to,
            ).count()
            results.append({"technologist_id": tid, "exam_count": count})
        return results

    # ── Annotations & Measurements ────────────────────────────────────────────

    def create_annotation(
        self,
        image_id: str,
        exam_id: str,
        annotated_by: str,
        annotation_type: str,
        annotation_data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> ImageAnnotation:
        ann = ImageAnnotation(
            image_id=image_id,
            exam_id=exam_id,
            annotated_by=annotated_by,
            annotation_type=annotation_type,
            annotation_data=annotation_data,
            extra_metadata=metadata or {},
        )
        self.db.add(ann)
        self.db.commit()
        self.db.refresh(ann)
        return ann

    def create_measurement(
        self,
        image_id: str,
        exam_id: str,
        measured_by: str,
        measurement_type: str,
        value: float,
        unit: str,
        location: str | None = None,
        finding_code: str | None = None,
        finding_description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ImageMeasurement:
        meas = ImageMeasurement(
            image_id=image_id,
            exam_id=exam_id,
            measured_by=measured_by,
            measurement_type=measurement_type,
            value=value,
            unit=unit,
            location=location,
            finding_code=finding_code,
            finding_description=finding_description,
            extra_metadata=metadata or {},
        )
        self.db.add(meas)
        self.db.commit()
        self.db.refresh(meas)
        return meas
