from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.pharmacy.enums import DispenseStatus, DrugCategory

logger = logging.getLogger("gula.pharmacy.dispensing")


@dataclass
class BarcodeScanResult:
    scanned_value: str
    barcode_type: str
    matched: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class VerificationResult:
    passed: bool
    checks: dict[str, bool] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass
class MedicationLabel:
    patient_name: str
    patient_mrn: str
    medication_name: str
    dosage: str
    route: str
    frequency: str
    quantity: int
    instructions: str
    warnings: list[str] = field(default_factory=list)
    barcode: str = ""
    timestamp: str = ""
    pharmacist: str = ""
    facility_name: str = ""


class PrescriptionQueueManager:
    def __init__(self, db: Session, lab_id: int | None = None):
        self.db = db
        self.lab_id = lab_id

    def prioritize(self, queue_entries: list[Any]) -> list[Any]:
        priority_order = {"stat": 0, "urgent": 1, "emergency": 2, "high": 3, "normal": 4, "low": 5}
        return sorted(
            queue_entries,
            key=lambda e: (priority_order.get(getattr(e, "priority", "normal"), 4), getattr(e, "queued_at", datetime.min)),
        )

    def sort_by_status(self, queue_entries: list[Any]) -> list[Any]:
        status_order = {
            DispenseStatus.PENDING: 0,
            DispenseStatus.VERIFIED: 1,
            DispenseStatus.PREPARED: 2,
            DispenseStatus.DISPENSED: 3,
        }
        return sorted(
            queue_entries,
            key=lambda e: status_order.get(getattr(e, "status", DispenseStatus.PENDING), 99),
        )

    def filter_by(self, queue_entries: list[Any], **filters: Any) -> list[Any]:
        result = queue_entries
        for attr, value in filters.items():
            if value is not None:
                result = [e for e in result if getattr(e, attr, None) == value]
        return result


class BarcodeVerification:
    def __init__(self, hmac_key: str | None = None):
        self._hmac_key = (hmac_key or os.getenv("DEVICE_HMAC_KEY", "")).encode("utf-8")

    def scan_patient_wristband(self, wristband_barcode: str, patient_mrn: str) -> BarcodeScanResult:
        try:
            expected = self._generate_patient_code(patient_mrn)
            matched = wristband_barcode == expected or patient_mrn in wristband_barcode
            return BarcodeScanResult(
                scanned_value=wristband_barcode,
                barcode_type="patient_wristband",
                matched=matched,
                data={"patient_mrn": patient_mrn} if matched else {},
                error=None if matched else "Wristband barcode does not match patient MRN",
            )
        except Exception as exc:
            return BarcodeScanResult(
                scanned_value=wristband_barcode,
                barcode_type="patient_wristband",
                matched=False,
                error=str(exc),
            )

    def scan_medication_barcode(self, scanned_barcode: str, expected_code: str) -> BarcodeScanResult:
        try:
            matched = scanned_barcode == expected_code or expected_code in scanned_barcode
            return BarcodeScanResult(
                scanned_value=scanned_barcode,
                barcode_type="medication",
                matched=matched,
                data={"medication_code": expected_code} if matched else {},
                error=None if matched else f"Scanned barcode does not match expected medication {expected_code}",
            )
        except Exception as exc:
            return BarcodeScanResult(
                scanned_value=scanned_barcode,
                barcode_type="medication",
                matched=False,
                error=str(exc),
            )

    def scan_prescriber_badge(self, badge_barcode: str, prescriber_id: str) -> BarcodeScanResult:
        try:
            expected = self._generate_prescriber_code(prescriber_id)
            matched = badge_barcode == expected or prescriber_id in badge_barcode
            return BarcodeScanResult(
                scanned_value=badge_barcode,
                barcode_type="prescriber_badge",
                matched=matched,
                data={"prescriber_id": prescriber_id} if matched else {},
                error=None if matched else "Badge does not match prescriber",
            )
        except Exception as exc:
            return BarcodeScanResult(
                scanned_value=badge_barcode,
                barcode_type="prescriber_badge",
                matched=False,
                error=str(exc),
            )

    def _generate_patient_code(self, patient_mrn: str) -> str:
        return hmac.new(self._hmac_key, patient_mrn.encode("utf-8"), hashlib.sha256).hexdigest()[:16]

    def _generate_prescriber_code(self, prescriber_id: str) -> str:
        return hmac.new(self._hmac_key, prescriber_id.encode("utf-8"), hashlib.sha256).hexdigest()[:12]


class PatientVerification:
    def verify_identity(
        self,
        provided_mrn: str,
        provided_name: str,
        provided_dob: str | None,
        stored_mrn: str,
        stored_name: str,
        stored_dob: str | None = None,
    ) -> VerificationResult:
        checks: dict[str, bool] = {}
        errors: list[str] = []

        mrn_match = provided_mrn == stored_mrn
        checks["mrn"] = mrn_match
        if not mrn_match:
            errors.append("MRN does not match")

        name_match = provided_name.strip().lower() == stored_name.strip().lower()
        checks["name"] = name_match
        if not name_match:
            errors.append("Name does not match")

        if provided_dob and stored_dob:
            dob_match = provided_dob == stored_dob
            checks["dob"] = dob_match
            if not dob_match:
                errors.append("Date of birth does not match")
        else:
            checks["dob"] = True

        passed = len(errors) == 0
        return VerificationResult(passed=passed, checks=checks, errors=errors)


class MedicationLabelGenerator:
    def __init__(self, facility_name: str = ""):
        self.facility_name = facility_name

    def generate_label(self, label_data: MedicationLabel) -> str:
        lines: list[str] = [
            "=" * 48,
            f"  {self.facility_name or 'PHARMACY'}",
            "=" * 48,
            f"  Patient:    {label_data.patient_name}",
            f"  MRN:        {label_data.patient_mrn}",
            "-" * 48,
            f"  Medication: {label_data.medication_name}",
            f"  Dosage:     {label_data.dosage}",
            f"  Route:      {label_data.route}",
            f"  Frequency:  {label_data.frequency}",
            f"  Quantity:   {label_data.quantity}",
            f"  Instructions: {label_data.instructions}",
        ]

        if label_data.warnings:
            lines.append("-" * 48)
            for warning in label_data.warnings:
                lines.append(f"  ! {warning}")

        lines.append("-" * 48)
        lines.append(f"  Pharmacist: {label_data.pharmacist}")
        lines.append(f"  Dispensed:  {label_data.timestamp}")
        if label_data.barcode:
            lines.append(f"  Barcode:    {label_data.barcode}")

        lines.append("=" * 48)
        return "\n".join(lines)

    def generate_label_text(self, label_data: MedicationLabel) -> str:
        return self.generate_label(label_data)

    def generate_label_html(self, label_data: MedicationLabel) -> str:
        warnings_html = ""
        if label_data.warnings:
            warnings_html = (
                '<div style="border-top: 2px dashed #000; margin: 8px 0; padding: 8px 0;">'
                + "".join(f'<p style="color: #cc0000; font-weight: bold;">⚠ {w}</p>' for w in label_data.warnings)
                + "</div>"
            )

        return f"""<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="utf-8"><title>Medication Label</title></head>
<body style="font-family: monospace; padding: 20px; max-width: 400px;">
<div style="border: 2px solid #000; padding: 16px;">
<h2 style="text-align: center;">{self.facility_name or 'Pharmacy'}</h2>
<hr>
<p><strong>Patient:</strong> {label_data.patient_name}</p>
<p><strong>MRN:</strong> {label_data.patient_mrn}</p>
<hr>
<p><strong>Medication:</strong> {label_data.medication_name}</p>
<p><strong>Dosage:</strong> {label_data.dosage}</p>
<p><strong>Route:</strong> {label_data.route}</p>
<p><strong>Frequency:</strong> {label_data.frequency}</p>
<p><strong>Quantity:</strong> {label_data.quantity}</p>
<p><strong>Instructions:</strong> {label_data.instructions}</p>
{warnings_html}
<hr>
<p><strong>Pharmacist:</strong> {label_data.pharmacist}</p>
<p><strong>Dispensed:</strong> {label_data.timestamp}</p>
</div>
</body>
</html>"""


class CounselingChecklist:
    _STANDARD_POINTS_BY_CATEGORY: dict[DrugCategory, list[str]] = {
        DrugCategory.GENERIC: [
            "Confirm patient identity",
            "Explain purpose of medication",
            "Dosage and administration timing",
            "Common side effects",
            "Storage instructions",
            "Missed dose instructions",
        ],
        DrugCategory.BRAND: [
            "Confirm patient identity",
            "Explain purpose of medication",
            "Brand-specific counseling points",
            "Dosage and administration",
            "Side effects profile",
            "Storage requirements",
        ],
        DrugCategory.BIOLOGIC: [
            "Confirm patient identity",
            "Explain biologic therapy purpose",
            "Injection/administration technique",
            "Storage (refrigeration) requirements",
            "Signs of allergic reaction",
            "Immunosuppression precautions",
            "Infection monitoring",
            "Vaccination recommendations",
        ],
        DrugCategory.BIOSIMILAR: [
            "Confirm patient identity",
            "Explain biosimilar vs. biologic",
            "Administration technique",
            "Storage requirements",
            "Side effect monitoring",
            "Report any differences in response",
        ],
        DrugCategory.VACCINE: [
            "Confirm patient identity and age",
            "Explain vaccine purpose and schedule",
            "Common side effects (fever, soreness)",
            "Contraindications and precautions",
            "Emergency allergy preparedness",
            "Observation period after administration",
            "Second dose reminder if applicable",
        ],
        DrugCategory.CONTRAST: [
            "Confirm patient identity",
            "Explain contrast agent purpose",
            "Ask about allergies (iodine/shellfish)",
            "Assess renal function",
            "Hydration instructions",
            "Metformin hold order if applicable",
            "Monitor for adverse reactions",
        ],
        DrugCategory.RADIOPHARMACEUTICAL: [
            "Confirm patient identity",
            "Explain procedure purpose",
            "Radiation safety precautions",
            "Hydration to promote elimination",
            "Avoid close contact with pregnant women/children",
            "Follow-up instructions",
        ],
        DrugCategory.OTHER: [
            "Confirm patient identity",
            "Explain purpose of medication",
            "Dosage instructions",
            "Side effects",
            "Follow-up plan",
        ],
    }

    def get_checklist(self, category: DrugCategory, additional_points: list[str] | None = None) -> list[str]:
        points = list(self._STANDARD_POINTS_BY_CATEGORY.get(category, self._STANDARD_POINTS_BY_CATEGORY[DrugCategory.OTHER]))
        if additional_points:
            points.extend(additional_points)
        return points

    def verify_checklist_completed(self, completed_points: list[str], category: DrugCategory) -> VerificationResult:
        required = self.get_checklist(category)
        checks: dict[str, bool] = {}
        errors: list[str] = []
        for point in required:
            matched = any(point.lower() in cp.lower() for cp in completed_points)
            checks[point] = matched
            if not matched:
                errors.append(f"Counseling point not completed: {point}")
        return VerificationResult(passed=len(errors) == 0, checks=checks, errors=errors)


class DispensingConfirmation:
    def __init__(self):
        self._signatures: dict[str, dict[str, Any]] = {}

    def capture_electronic_signature(self, dispenser_id: str, signature_data: str) -> str:
        sig_hash = hashlib.sha256(f"{dispenser_id}:{signature_data}:{datetime.now(UTC).isoformat()}".encode()).hexdigest()
        self._signatures[sig_hash] = {
            "dispenser_id": dispenser_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "signature_type": "electronic",
            "verified": True,
        }
        return sig_hash

    def verify_controlled_substance_witness(self, dispenser_id: str, witness_id: str, substance_code: str) -> VerificationResult:
        checks: dict[str, bool] = {
            "dispenser_identified": bool(dispenser_id),
            "witness_identified": bool(witness_id),
            "different_persons": dispenser_id != witness_id,
            "substance_controlled": True,
        }
        errors: list[str] = []
        if not dispenser_id:
            errors.append("Dispenser not identified")
        if not witness_id:
            errors.append("Witness not identified")
        if dispenser_id == witness_id:
            errors.append("Witness must be a different person from dispenser for controlled substances")
        return VerificationResult(passed=len(errors) == 0, checks=checks, errors=errors)

    def get_signature(self, sig_hash: str) -> dict[str, Any] | None:
        return self._signatures.get(sig_hash)


class PharmacyAuditTrail:
    def __init__(self):
        self._entries: list[dict[str, Any]] = []

    def log_step(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        performed_by: str,
        details: str | None = None,
        controlled_substance: bool = False,
        witness: str | None = None,
    ) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "performed_by": performed_by,
            "details": details,
            "controlled_substance": controlled_substance,
        }
        if witness:
            entry["witness"] = witness

        if controlled_substance:
            entry["hash"] = hashlib.sha256(
                json.dumps(entry, sort_keys=True, default=str).encode()
            ).hexdigest()

        self._entries.append(entry)
        logger.info(
            "[AUDIT] %s %s %s by %s%s",
            action, resource_type, resource_id, performed_by,
            " [CONTROLLED]" if controlled_substance else "",
        )
        return entry

    def get_audit_log(self, resource_id: str | None = None) -> list[dict[str, Any]]:
        if resource_id:
            return [e for e in self._entries if e.get("resource_id") == resource_id]
        return list(self._entries)

    def verify_chain_integrity(self) -> bool:
        previous_hash = ""
        for entry in self._entries:
            if entry.get("controlled_substance") and entry.get("hash"):
                stored_hash = entry["hash"]
                entry_copy = dict(entry)
                entry_copy.pop("hash")
                computed_hash = hashlib.sha256(
                    json.dumps(entry_copy, sort_keys=True, default=str).encode()
                ).hexdigest()
                if stored_hash != computed_hash or (previous_hash and stored_hash == previous_hash):
                    return False
                previous_hash = stored_hash
        return True
