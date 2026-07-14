from datetime import date, datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC
from ..enums import CompetencyLevel, LicenseStatus, ProductivityPeriod
from ..models.workforce import (
    AttendanceRecord,
    BoardCertification,
    CompetencyAssessment,
    HealthcareWorker,
    ProductivityRecord,
    ProfessionalLicense,
    RotationRecord,
    TrainingRecord,
    WorkerPrivilege,
)


class WorkforceGovernanceService:
    def __init__(self, db: Session):
        self.db = db

    def register_worker(
        self,
        employee_code: str,
        full_name_ar: str,
        profession: str,
        full_name_en: str | None = None,
        national_id_hash: str | None = None,
        specialization: str | None = None,
        organization_node_id: int | None = None,
        department: str | None = None,
        unit: str | None = None,
        employment_date: date | None = None,
        contact_phone: str | None = None,
        contact_email: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> HealthcareWorker:
        worker = HealthcareWorker(
            employee_code=employee_code,
            full_name_ar=full_name_ar,
            full_name_en=full_name_en,
            national_id_hash=national_id_hash,
            profession=profession,
            specialization=specialization,
            organization_node_id=organization_node_id,
            department=department,
            unit=unit,
            employment_date=employment_date,
            contact_phone=contact_phone,
            contact_email=contact_email,
            metadata_json=metadata_json,
        )
        self.db.add(worker)
        self.db.flush()
        return worker

    def get_worker(self, worker_id: int) -> HealthcareWorker | None:
        return self.db.query(HealthcareWorker).filter(HealthcareWorker.id == worker_id).first()

    def get_worker_by_code(self, employee_code: str) -> HealthcareWorker | None:
        return (
            self.db.query(HealthcareWorker)
            .filter(HealthcareWorker.employee_code == employee_code)
            .first()
        )

    def get_workers_by_node(self, node_id: int) -> list[HealthcareWorker]:
        return (
            self.db.query(HealthcareWorker)
            .filter(HealthcareWorker.organization_node_id == node_id)
            .all()
        )

    def add_license(
        self,
        worker_id: int,
        license_number: str,
        license_type: str,
        issuing_authority: str,
        issued_date: date,
        expiry_date: date | None = None,
    ) -> ProfessionalLicense:
        license = ProfessionalLicense(
            worker_id=worker_id,
            license_number=license_number,
            license_type=license_type,
            issuing_authority=issuing_authority,
            status=LicenseStatus.ACTIVE,
            issued_date=issued_date,
            expiry_date=expiry_date,
        )
        self.db.add(license)
        return license

    def verify_license(self, license_id: int, verified_by: str) -> ProfessionalLicense | None:
        lic = self.db.query(ProfessionalLicense).filter(ProfessionalLicense.id == license_id).first()
        if lic:
            lic.verified_at = datetime.now(UTC)
            lic.verified_by = verified_by
            lic.status = LicenseStatus.ACTIVE
        return lic

    def add_board_certification(
        self,
        worker_id: int,
        board_name: str,
        specialty: str,
        issuing_body: str,
        issued_date: date,
        certificate_number: str | None = None,
        expiry_date: date | None = None,
    ) -> BoardCertification:
        board = BoardCertification(
            worker_id=worker_id,
            board_name=board_name,
            specialty=specialty,
            certificate_number=certificate_number,
            issuing_body=issuing_body,
            issued_date=issued_date,
            expiry_date=expiry_date,
        )
        self.db.add(board)
        return board

    def add_training(
        self,
        worker_id: int,
        training_name: str,
        training_type: str,
        provider: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        hours: float | None = None,
        completed: bool = False,
    ) -> TrainingRecord:
        training = TrainingRecord(
            worker_id=worker_id,
            training_name=training_name,
            training_type=training_type,
            provider=provider,
            start_date=start_date,
            end_date=end_date,
            hours=hours,
            completed=completed,
        )
        self.db.add(training)
        return training

    def assess_competency(
        self,
        worker_id: int,
        competency_name: str,
        level: CompetencyLevel,
        assessed_by: str | None = None,
        assessment_date: date | None = None,
        next_assessment_date: date | None = None,
        score: float | None = None,
        notes: str | None = None,
    ) -> CompetencyAssessment:
        assessment = CompetencyAssessment(
            worker_id=worker_id,
            competency_name=competency_name,
            level=level,
            assessed_by=assessed_by,
            assessment_date=assessment_date or date.today(),
            next_assessment_date=next_assessment_date,
            score=score,
            notes=notes,
        )
        self.db.add(assessment)
        return assessment

    def grant_privilege(
        self,
        worker_id: int,
        privilege_name: str,
        scope: str | None = None,
        granted_by: str | None = None,
        granted_date: date | None = None,
        expiry_date: date | None = None,
    ) -> WorkerPrivilege:
        priv = WorkerPrivilege(
            worker_id=worker_id,
            privilege_name=privilege_name,
            scope=scope,
            granted_by=granted_by,
            granted_date=granted_date or date.today(),
            expiry_date=expiry_date,
        )
        self.db.add(priv)
        return priv

    def record_rotation(
        self,
        worker_id: int,
        from_department: str,
        to_department: str,
        start_date: date,
        end_date: date | None = None,
        reason: str | None = None,
        approved_by: str | None = None,
    ) -> RotationRecord:
        rotation = RotationRecord(
            worker_id=worker_id,
            from_department=from_department,
            to_department=to_department,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            approved_by=approved_by,
        )
        self.db.add(rotation)
        return rotation

    def record_attendance(
        self,
        worker_id: int,
        date_val: date,
        check_in: datetime | None = None,
        check_out: datetime | None = None,
        status: str = "present",
        notes: str | None = None,
        recorded_by: str | None = None,
    ) -> AttendanceRecord:
        record = AttendanceRecord(
            worker_id=worker_id,
            date=date_val,
            check_in=check_in,
            check_out=check_out,
            status=status,
            notes=notes,
            recorded_by=recorded_by,
        )
        self.db.add(record)
        return record

    def record_productivity(
        self,
        worker_id: int,
        period: ProductivityPeriod,
        period_start: date,
        period_end: date,
        tests_performed: int = 0,
        samples_processed: int = 0,
        reports_generated: int = 0,
        errors_count: int = 0,
        tat_average_minutes: float | None = None,
        quality_score: float | None = None,
        metrics_json: dict[str, Any] | None = None,
    ) -> ProductivityRecord:
        record = ProductivityRecord(
            worker_id=worker_id,
            period=period,
            period_start=period_start,
            period_end=period_end,
            tests_performed=tests_performed,
            samples_processed=samples_processed,
            reports_generated=reports_generated,
            errors_count=errors_count,
            tat_average_minutes=tat_average_minutes,
            quality_score=quality_score,
            metrics_json=metrics_json,
        )
        self.db.add(record)
        self.db.flush()
        self._update_rankings(record, period, period_start, period_end)
        return record

    def _update_rankings(
        self,
        record: ProductivityRecord,
        period: ProductivityPeriod,
        period_start: date,
        period_end: date,
    ) -> None:
        q = self.db.query(ProductivityRecord).filter(
            ProductivityRecord.period == period,
            ProductivityRecord.period_start == period_start,
            ProductivityRecord.period_end == period_end,
        ).order_by(ProductivityRecord.quality_score.desc().nullslast(), ProductivityRecord.tests_performed.desc())

        ranked = q.all()
        for i, r in enumerate(ranked, 1):
            r.national_rank = i

        lab_records = [r for r in ranked if r.worker_id == record.worker_id]
        if lab_records:
            other_lab = (
                self.db.query(ProductivityRecord)
                .filter(
                    ProductivityRecord.period == period,
                    ProductivityRecord.period_start == period_start,
                    ProductivityRecord.period_end == period_end,
                    ProductivityRecord.id != record.id,
                )
                .count()
            )
            record.lab_rank = other_lab + 1

    def get_productivity(
        self, worker_id: int, period: ProductivityPeriod | None = None, limit: int = 12
    ) -> list[ProductivityRecord]:
        q = (
            self.db.query(ProductivityRecord)
            .filter(ProductivityRecord.worker_id == worker_id)
        )
        if period:
            q = q.filter(ProductivityRecord.period == period)
        return q.order_by(ProductivityRecord.period_start.desc()).limit(limit).all()

    def get_national_ranking(
        self, period: ProductivityPeriod, period_start: date, period_end: date, limit: int = 100
    ) -> list[ProductivityRecord]:
        return (
            self.db.query(ProductivityRecord)
            .filter(
                ProductivityRecord.period == period,
                ProductivityRecord.period_start == period_start,
                ProductivityRecord.period_end == period_end,
            )
            .order_by(ProductivityRecord.national_rank.asc().nullslast())
            .limit(limit)
            .all()
        )

    def get_worker_stats(self, worker_id: int) -> dict[str, Any]:
        worker = self.get_worker(worker_id)
        if not worker:
            return {}
        licenses = self.db.query(ProfessionalLicense).filter(
            ProfessionalLicense.worker_id == worker_id,
            ProfessionalLicense.status == LicenseStatus.ACTIVE,
        ).count()
        trainings = self.db.query(TrainingRecord).filter(
            TrainingRecord.worker_id == worker_id, TrainingRecord.completed.is_(True)
        ).count()
        latest_productivity = (
            self.db.query(ProductivityRecord)
            .filter(ProductivityRecord.worker_id == worker_id)
            .order_by(ProductivityRecord.period_start.desc())
            .first()
        )
        return {
            "worker_id": worker_id,
            "employee_code": worker.employee_code,
            "full_name_ar": worker.full_name_ar,
            "profession": worker.profession,
            "active_licenses": licenses,
            "completed_trainings": trainings,
            "latest_quality_score": latest_productivity.quality_score if latest_productivity else None,
            "latest_national_rank": latest_productivity.national_rank if latest_productivity else None,
        }
