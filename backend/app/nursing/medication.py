from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC
from app.ehr.models.medication import MedicationAdministration, MedicationRequest
from app.services.audit_service import log_action

logger = logging.getLogger("gula.nursing.medication")

_GS1_PATTERN = re.compile(r"^01\d{14}17\d{6}10\d{1,20}$|^\]C1\d{14}17\d{6}10\d{1,20}$")


class FiveRightsResult:
    def __init__(self, passed: bool, checks: dict[str, bool], message: str = ""):
        self.passed = passed
        self.checks = checks
        self.message = message


class MedicationAdminService:

    @staticmethod
    def verify_five_rights(
        right_patient: bool,
        right_drug: bool,
        right_dose: bool,
        right_route: bool,
        right_time: bool,
    ) -> FiveRightsResult:
        checks = {
            "right_patient": right_patient,
            "right_drug": right_drug,
            "right_dose": right_dose,
            "right_route": right_route,
            "right_time": right_time,
        }
        passed = all(checks.values())
        if not passed:
            failed = [k for k, v in checks.items() if not v]
            message = f"Failed checks: {', '.join(failed)}"
        else:
            message = "All five rights verified"
        return FiveRightsResult(passed=passed, checks=checks, message=message)

    @staticmethod
    def scan_barcode(barcode_data: str) -> dict[str, Any]:
        barcode_data = barcode_data.strip()
        if not _GS1_PATTERN.match(barcode_data):
            raise HTTPException(
                status_code=422,
                detail="Invalid barcode format — expected GS1 DataMatrix or Code 128",
                detail_ar="تنسيق الباركود غير صالح",
            )
        result: dict[str, Any] = {"format": "GS1"}
        if barcode_data.startswith("01"):
            result["gtin"] = barcode_data[2:16]
            remaining = barcode_data[16:]
            if remaining.startswith("17"):
                result["expiry"] = f"20{remaining[2:4]}-{remaining[4:6]}-{remaining[6:8]}"
                remaining = remaining[8:]
            if remaining.startswith("10"):
                result["lot_number"] = remaining[2:]
        elif barcode_data.startswith("]C1"):
            result["symbology"] = "GS1-128"
            result["gtin"] = barcode_data[4:18]
            remaining = barcode_data[18:]
            if remaining.startswith("17"):
                result["expiry"] = f"20{remaining[2:4]}-{remaining[4:6]}-{remaining[6:8]}"
                remaining = remaining[8:]
            if remaining.startswith("10"):
                result["lot_number"] = remaining[2:]
        return result

    @staticmethod
    def record_administration(
        db: Session, lab_id: int, user_id: int, admin_data: dict,
    ) -> MedicationAdministration:
        admin = MedicationAdministration(
            lab_id=lab_id,
            created_by=user_id,
            **admin_data,
        )
        admin.recorded_time = datetime.now(UTC)
        db.add(admin)
        db.flush()
        log_action(db, "nursing.medication.administer", "medication_administration", admin.id, user_id=user_id, lab_id=lab_id, details=admin_data)
        return admin

    @staticmethod
    def get_missed_doses(
        db: Session, lab_id: int, patient_id: int,
        start_date: date | None = None, end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        start_date = start_date or date.today()
        end_date = end_date or date.today()
        requests = db.query(MedicationRequest).filter(
            MedicationRequest.patient_id == patient_id,
            MedicationRequest.lab_id == lab_id,
            ~MedicationRequest.is_deleted,
            MedicationRequest.status == "active",
        ).all()
        missed = []
        for req in requests:
            given = db.query(MedicationAdministration).filter(
                MedicationAdministration.medication_request_id == req.id,
                MedicationAdministration.patient_id == patient_id,
                func.date(MedicationAdministration.administration_time).between(start_date, end_date),
                MedicationAdministration.status == "completed",
            ).count()
            if given == 0:
                missed.append({
                    "request_id": req.id,
                    "medication_name": req.medication_name,
                    "medication_name_ar": req.medication_name_ar,
                    "dosage_instruction": req.dosage_instruction,
                    "route": req.route,
                    "frequency": req.frequency,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "status": "missed",
                })
        return missed

    @staticmethod
    def get_late_doses(
        db: Session, lab_id: int, patient_id: int, window_minutes: int = 30,
    ) -> list[dict[str, Any]]:
        cutoff = datetime.now(UTC) - timedelta(minutes=window_minutes)
        late = db.query(MedicationAdministration).filter(
            MedicationAdministration.patient_id == patient_id,
            MedicationAdministration.lab_id == lab_id,
            ~MedicationAdministration.is_deleted,
            MedicationAdministration.status == "completed",
            MedicationAdministration.recorded_time > cutoff,
        ).order_by(MedicationAdministration.recorded_time.desc()).all()
        return [
            {
                "id": a.id,
                "medication_request_id": a.medication_request_id,
                "medication_name": a.medication_name,
                "dose_value": a.dose_value,
                "dose_unit": a.dose_unit,
                "route": a.route,
                "scheduled_time": a.administration_time.isoformat() if a.administration_time else None,
                "recorded_time": a.recorded_time.isoformat() if a.recorded_time else None,
                "delay_minutes": (
                    (a.recorded_time - a.administration_time).total_seconds() / 60
                    if a.recorded_time and a.administration_time else None
                ),
            }
            for a in late
        ]

    @staticmethod
    def get_medication_alerts(
        db: Session, lab_id: int, patient_id: int,
    ) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        requests = db.query(MedicationRequest).filter(
            MedicationRequest.patient_id == patient_id,
            MedicationRequest.lab_id == lab_id,
            ~MedicationRequest.is_deleted,
            MedicationRequest.status == "active",
        ).all()
        for req in requests:
            if req.quantity and req.duration_days:
                daily_dose = req.quantity / req.duration_days
                if daily_dose > 4:
                    alerts.append({
                        "type": "max_dose_warning",
                        "severity": "warning",
                        "medication_name": req.medication_name,
                        "message": f"Daily dose ({daily_dose:.0f} units) exceeds threshold",
                        "message_ar": f"الجرعة اليومية ({daily_dose:.0f} وحدة) تتجاوز الحد المسموح",
                    })
        return alerts

    @staticmethod
    def electronic_signature(
        db: Session, lab_id: int, nurse_id: str, medication_admin_id: str,
    ) -> dict[str, Any]:
        admin = db.query(MedicationAdministration).filter(
            MedicationAdministration.id == medication_admin_id,
            MedicationAdministration.lab_id == lab_id,
        ).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Medication administration record not found")
        signed_at = datetime.now(UTC)
        log_action(
            db, "nursing.medication.sign", "medication_administration",
            medication_admin_id, user_id=nurse_id, lab_id=lab_id,
            details={"signed_at": signed_at.isoformat()},
        )
        return {
            "medication_admin_id": medication_admin_id,
            "signed_by": nurse_id,
            "signed_at": signed_at.isoformat(),
            "signature_type": "electronic",
        }
