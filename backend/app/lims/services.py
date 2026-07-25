"""National LIMS Business Services — orchestration layer for domain operations.

All services accept a SQLAlchemy Session and current user context,
emit outbox events for async consumers, and enforce state machine rules.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.services.audit_service import log_action

from .exceptions import (
    AccessionNumberConflict,
    DuplicateSpecimenBarcode,
)
from .models import (
    IQC,
    Calibration,
    ElectronicSignature,
    Instrument,
    LabReport,
    Maintenance,
    Order,
    Result,
    ResultRelease,
    ResultValidation,
    Specimen,
    Transportation,
)
from .quality import evaluate_westgard
from .state_machine import (
    enforce_can_reject,
    enforce_order_transition,
    enforce_specimen_transition,
)
from .workflows import auto_validate_result

# ===========================================================================
# Specimen Service
# ===========================================================================


class SpecimenService:
    """Complete specimen lifecycle management."""

    @staticmethod
    def register(
        db: Session,
        order_id: int,
        lab_id: int,
        specimen_type: str,
        barcode: str,
        user_id: int,
        container_type: str | None = None,
        **kwargs,
    ) -> Specimen:
        existing = db.query(Specimen).filter(Specimen.barcode == barcode).first()
        if existing:
            raise DuplicateSpecimenBarcode(f"Barcode {barcode} already in use")

        specimen = Specimen(
            lab_id=lab_id,
            order_id=order_id,
            barcode=barcode,
            specimen_type=specimen_type,
            container_type=container_type,
            status="ordered",
            created_by=user_id,
            **kwargs,
        )
        db.add(specimen)
        db.flush()
        log_action(
            db,
            "create",
            "lims_specimen",
            specimen.id,
            user_id,
            "lab_tech",
            f"Specimen {barcode} registered",
        )
        return specimen

    @staticmethod
    def transition(
        db: Session,
        specimen: Specimen,
        target_status: str,
        user_id: int,
        notes: str | None = None,
    ) -> Specimen:
        enforce_specimen_transition(specimen.status, target_status)
        now = datetime.now(UTC)

        if target_status == "rejected":
            enforce_can_reject(specimen.status)
            specimen.rejected_at = now
            specimen.rejected_by = user_id

        specimen.status = target_status
        specimen.updated_by = user_id
        specimen.updated_at = now

        if target_status == "collected":
            specimen.collection_time = now
            specimen.collected_by = user_id
        elif target_status == "received":
            specimen.received_at = now
            specimen.received_by = user_id
        elif target_status == "accepted":
            specimen.accepted_at = now
            specimen.accepted_by = user_id
        elif target_status == "analyzed":
            specimen.analyzed_at = now
        elif target_status == "verified":
            specimen.verified_at = now
            specimen.verified_by = user_id
        elif target_status == "validated":
            specimen.validated_at = now
            specimen.validated_by = user_id
        elif target_status == "released":
            specimen.released_at = now
            specimen.released_by = user_id

        db.flush()
        log_action(
            db,
            "transition",
            "lims_specimen",
            specimen.id,
            user_id,
            "lab_tech",
            f"Specimen {specimen.barcode}: {specimen.status} → {target_status}",
        )
        return specimen

    @staticmethod
    def reject(
        db: Session,
        specimen: Specimen,
        reason: str,
        user_id: int,
    ) -> Specimen:
        specimen.rejection_reason = reason
        return SpecimenService.transition(db, specimen, "rejected", user_id)

    @staticmethod
    def record_transportation(
        db: Session,
        specimen_id: int,
        from_location: str,
        to_location: str,
        lab_id: int,
        user_id: int,
        **kwargs,
    ) -> Transportation:
        transport = Transportation(
            specimen_id=specimen_id,
            lab_id=lab_id,
            from_location=from_location,
            to_location=to_location,
            created_by=user_id,
            **kwargs,
        )
        db.add(transport)
        db.flush()
        return transport


# ===========================================================================
# Order Service
# ===========================================================================


class OrderService:
    """Laboratory order lifecycle management."""

    @staticmethod
    def create_lims_order(
        db: Session,
        order_id: int,
        lab_id: int,
        user_id: int,
        accession_number: str,
        priority: str = "routine",
        **kwargs,
    ) -> Order:
        existing = db.query(Order).filter(Order.accession_number == accession_number).first()
        if existing:
            raise AccessionNumberConflict(f"Accession number {accession_number} already in use")

        lims_order = Order(
            order_id=order_id,
            lab_id=lab_id,
            accession_number=accession_number,
            priority=priority,
            order_status="pending",
            ordered_by=user_id,
            created_by=user_id,
            **kwargs,
        )
        db.add(lims_order)
        db.flush()
        log_action(
            db,
            "create",
            "lims_order",
            lims_order.id,
            user_id,
            "lab_tech",
            f"LIMS order {accession_number} created",
        )
        return lims_order

    @staticmethod
    def transition(
        db: Session,
        lims_order: Order,
        target_status: str,
        user_id: int,
    ) -> Order:
        enforce_order_transition(lims_order.order_status, target_status)
        lims_order.order_status = target_status
        lims_order.updated_by = user_id
        lims_order.updated_at = datetime.now(UTC)
        db.flush()
        return lims_order


# ===========================================================================
# Result Service
# ===========================================================================


class ResultService:
    """Result management with auto-validation, delta check, and QC integration."""

    @staticmethod
    def create_result(
        db: Session,
        specimen_id: int,
        order_id: int,
        lab_id: int,
        test_code: str,
        test_name: str,
        user_id: int,
        value_numeric: float | None = None,
        value_text: str | None = None,
        unit: str | None = None,
        instrument_id: int | None = None,
        **kwargs,
    ) -> Result:
        result = Result(
            specimen_id=specimen_id,
            order_id=order_id,
            lab_id=lab_id,
            test_code=test_code,
            test_name=test_name,
            value_numeric=value_numeric,
            value_text=value_text,
            unit=unit,
            instrument_id=instrument_id,
            created_by=user_id,
            **kwargs,
        )
        db.add(result)
        db.flush()

        # Run auto-validation
        validation = auto_validate_result(
            db,
            value_numeric,
            test_code,
            lab_id=lab_id,
            instrument_id=instrument_id,
        )

        if validation["auto_validated"]:
            result.validation_status = "auto_validated"
            result.auto_validated = True
            result.auto_validated_at = datetime.now(UTC)

        if validation["flags"]:
            for flag in validation["flags"]:
                if flag.startswith("critical"):
                    result.is_critical = True
                elif flag in ("high", "low"):
                    result.is_abnormal = True
            result.flag = validation["flags"][0] if validation["flags"] else None

        db.flush()
        log_action(
            db,
            "create",
            "lims_result",
            result.id,
            user_id,
            "lab_tech",
            f"Result {test_code}: {value_numeric} {unit or ''}".strip(),
        )
        return result

    @staticmethod
    def validate_manually(
        db: Session,
        result: Result,
        user_id: int,
        notes: str | None = None,
        signature_data: str | None = None,
    ) -> Result:
        now = datetime.now(UTC)
        result.validation_status = "validated"
        result.validated_by = user_id
        result.validated_at = now
        result.updated_by = user_id
        result.updated_at = now

        validation = ResultValidation(
            result_id=result.id,
            action="manual_validated",
            validated_by=user_id,
            validated_at=now,
            notes=notes,
        )
        db.add(validation)

        if signature_data:
            sig = ElectronicSignature(
                lab_id=result.lab_id,
                user_id=user_id,
                signature_type="validation",
                resource_type="result",
                resource_id=result.id,
                signature_hash=signature_data,
                signed_at=now,
            )
            db.add(sig)

        db.flush()
        return result

    @staticmethod
    def release(
        db: Session,
        result: Result,
        user_id: int,
        channel: str = "portal",
    ) -> ResultRelease:
        release = ResultRelease(
            lab_id=result.lab_id,
            order_id=result.order_id,
            released_by=user_id,
            released_at=datetime.now(UTC),
            release_channel=channel,
        )
        db.add(release)
        db.flush()
        return release


# ===========================================================================
# QC Service
# ===========================================================================


class QCService:
    """Quality Control management with Westgard evaluation."""

    @staticmethod
    def run_iqc(
        db: Session,
        lab_id: int,
        program_id: int,
        test_code: str,
        measured_value: float,
        expected_value: float,
        sd: float,
        user_id: int,
        level: str = "normal",
        lot_number: str | None = None,
        instrument_id: int | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        # Get recent IQC history for Westgard evaluation
        recent_iqc = (
            db.query(IQC)
            .filter(
                IQC.test_code == test_code,
                IQC.lab_id == lab_id,
                IQC.program_id == program_id,
            )
            .order_by(IQC.performed_at.desc())
            .limit(12)
            .all()
        )

        history = [r.measured_value for r in reversed(recent_iqc)]

        violation, triggered_rules = evaluate_westgard(measured_value, expected_value, sd, history)

        status = "in_control"
        if violation == "out_of_control":
            status = "out_of_control"
        elif violation == "warning":
            status = "warning"

        iqc = IQC(
            lab_id=lab_id,
            program_id=program_id,
            instrument_id=instrument_id,
            test_code=test_code,
            lot_number=lot_number,
            level=level,
            measured_value=measured_value,
            expected_value=expected_value,
            mean=expected_value,
            sd=sd,
            status=status,
            violation=violation,
            performed_by=user_id,
            performed_at=datetime.now(UTC),
            notes=notes,
            created_by=user_id,
        )
        db.add(iqc)
        db.flush()

        return {
            "iqc_id": iqc.id,
            "status": status,
            "violation": violation,
            "triggered_rules": triggered_rules,
            "z_score": (measured_value - expected_value) / sd if sd > 0 else 0,
        }


# ===========================================================================
# Instrument Service
# ===========================================================================


class InstrumentService:
    """Instrument/analyzer management."""

    @staticmethod
    def record_maintenance(
        db: Session,
        instrument_id: int,
        maintenance_type: str,
        title: str,
        performed_by: int,
        **kwargs,
    ) -> Maintenance:
        maint = Maintenance(
            instrument_id=instrument_id,
            maintenance_type=maintenance_type,
            title=title,
            performed_by=performed_by,
            performed_at=datetime.now(UTC),
            **kwargs,
        )
        db.add(maint)
        db.flush()
        return maint

    @staticmethod
    def record_calibration(
        db: Session,
        instrument_id: int,
        calibration_type: str,
        performed_by: int,
        passed: bool | None = None,
        **kwargs,
    ) -> Calibration:
        cal = Calibration(
            instrument_id=instrument_id,
            calibration_type=calibration_type,
            performed_by=performed_by,
            performed_at=datetime.now(UTC),
            passed=passed,
            **kwargs,
        )
        db.add(cal)
        db.flush()
        return cal

    @staticmethod
    def mark_online(db: Session, instrument_id: int) -> Instrument:
        inst = db.query(Instrument).filter(Instrument.id == instrument_id).first()
        if inst:
            inst.status = "online"
            inst.last_connected_at = datetime.now(UTC)
            db.flush()
        return inst

    @staticmethod
    def mark_offline(db: Session, instrument_id: int) -> Instrument:
        inst = db.query(Instrument).filter(Instrument.id == instrument_id).first()
        if inst:
            inst.status = "offline"
            db.flush()
        return inst


# ===========================================================================
# Report Service
# ===========================================================================


class ReportService:
    """Laboratory report generation and management."""

    @staticmethod
    def generate_report(
        db: Session,
        order_id: int,
        lab_id: int,
        report_number: str,
        user_id: int,
        locale: str = "ar",
        **kwargs,
    ) -> LabReport:
        report = LabReport(
            order_id=order_id,
            lab_id=lab_id,
            report_number=report_number,
            status="draft",
            locale=locale,
            generated_by=user_id,
            generated_at=datetime.now(UTC),
            created_by=user_id,
            **kwargs,
        )
        db.add(report)
        db.flush()
        return report

    @staticmethod
    def finalize(
        db: Session,
        report: LabReport,
        user_id: int,
    ) -> LabReport:
        report.status = "final"
        report.finalized_by = user_id
        report.finalized_at = datetime.now(UTC)
        report.updated_by = user_id
        db.flush()
        return report

    @staticmethod
    def correct(
        db: Session,
        report: LabReport,
        reason: str,
        user_id: int,
    ) -> LabReport:
        report.status = "corrected"
        report.corrected_by = user_id
        report.corrected_at = datetime.now(UTC)
        report.correction_reason = reason
        report.updated_by = user_id
        db.flush()
        return report
