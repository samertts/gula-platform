from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.care_continuum.enums import ReferralDirection
from app.care_continuum.models.referral import ReferralRequest
from app.insurance.domain.referral import InsuranceReferral
from app.models.lab_user import LabUser
from app.national.domain.patient import Patient as NationalPatient
from app.national.domain.practitioner import Practitioner
from app.national.domain.referral import Referral as NationalReferral
from app.national.enums import ReferralPriority, ReferralStatus


class CanonicalReferralMappingError(PermissionError):
    """Raised when a legacy referral cannot be proven safe to map."""


_STATUS_MAP = {
    "draft": ReferralStatus.DRAFT,
    "sent": ReferralStatus.SENT,
    "received": ReferralStatus.SENT,
    "accepted": ReferralStatus.ACCEPTED,
    "declined": ReferralStatus.REJECTED,
    "rejected": ReferralStatus.REJECTED,
    "completed": ReferralStatus.COMPLETED,
    "cancelled": ReferralStatus.CANCELLED,
    "expired": ReferralStatus.CANCELLED,
}
_PRIORITY_MAP = {
    "routine": ReferralPriority.ROUTINE,
    "urgent": ReferralPriority.URGENT,
    "emergency": ReferralPriority.EMERGENCY,
    "asap": ReferralPriority.ASAP,
}


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value)).lower()


def _status(value: Any) -> ReferralStatus:
    try:
        return _STATUS_MAP[_enum_value(value)]
    except KeyError as exc:
        raise CanonicalReferralMappingError("referral_status_mapping_missing") from exc


def _priority(value: Any) -> ReferralPriority:
    try:
        return _PRIORITY_MAP[_enum_value(value)]
    except KeyError as exc:
        raise CanonicalReferralMappingError("referral_priority_mapping_missing") from exc


class CanonicalReferralMappingService:
    """Bridge legacy referrals without accepting legacy IDs as canonical authority."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _existing(self, canonical_id: str | None, lab_id: int) -> ReferralRequest | None:
        if not canonical_id:
            return None
        return (
            self.db.query(ReferralRequest)
            .filter(
                ReferralRequest.id == canonical_id,
                ReferralRequest.lab_id == lab_id,
                ReferralRequest.is_deleted.is_(False),
            )
            .one_or_none()
        )

    def _national_patient(self, *, lab_id: int, legacy_patient_id: int) -> NationalPatient:
        rows = (
            self.db.query(NationalPatient)
            .filter(
                NationalPatient.lab_id == lab_id,
                NationalPatient.lab_patient_id == legacy_patient_id,
                NationalPatient.is_active.is_(True),
                NationalPatient.is_deleted.is_(False),
            )
            .all()
        )
        if len(rows) != 1:
            raise CanonicalReferralMappingError("national_patient_mapping_missing_or_ambiguous")
        return rows[0]

    def _national_practitioner(self, *, lab_id: int, legacy_user_id: int | None) -> Practitioner | None:
        if legacy_user_id is None:
            return None
        user = (
            self.db.query(LabUser)
            .filter(
                LabUser.id == legacy_user_id,
                LabUser.lab_id == lab_id,
                LabUser.is_active.is_(True),
                LabUser.national_id_hash.isnot(None),
            )
            .one_or_none()
        )
        if user is None:
            raise CanonicalReferralMappingError("server_practitioner_mapping_required")
        practitioners = (
            self.db.query(Practitioner)
            .filter(
                Practitioner.national_id_hash == user.national_id_hash,
                Practitioner.is_active.is_(True),
            )
            .all()
        )
        if len(practitioners) != 1:
            raise CanonicalReferralMappingError("server_practitioner_mapping_missing_or_ambiguous")
        return practitioners[0]

    @staticmethod
    def _require_facility_mapping(legacy_facility_id: int | None) -> None:
        if legacy_facility_id is not None:
            # Insurance's integer facility space has no implicit equality with
            # national facility IDs. A reviewed bridge must be added before use.
            raise CanonicalReferralMappingError("server_facility_mapping_required")

    def from_national(self, *, legacy_id: str, lab_id: int) -> ReferralRequest:
        source = (
            self.db.query(NationalReferral)
            .filter(
                NationalReferral.id == legacy_id,
                NationalReferral.lab_id == lab_id,
                NationalReferral.is_deleted.is_(False),
            )
            .one_or_none()
        )
        if source is None:
            raise CanonicalReferralMappingError("national_referral_not_found_or_scope_denied")
        existing = self._existing(source.canonical_referral_id, lab_id)
        if existing is not None:
            return existing
        existing = (
            self.db.query(ReferralRequest)
            .filter(
                ReferralRequest.national_referral_id == source.id,
                ReferralRequest.lab_id == lab_id,
                ReferralRequest.is_deleted.is_(False),
            )
            .one_or_none()
        )
        if existing is not None:
            source.canonical_referral_id = existing.id
            self.db.flush()
            return existing
        if not source.referring_practitioner_id:
            raise CanonicalReferralMappingError("server_practitioner_mapping_required")
        canonical = ReferralRequest(
            patient_id=source.patient_id,
            citizen_id=source.citizen_id,
            national_referral_id=source.id,
            encounter_id=source.encounter_id,
            direction=ReferralDirection.OUTGOING,
            status=_status(source.status),
            priority=_priority(source.priority),
            referring_practitioner_id=source.referring_practitioner_id,
            referring_facility_id=source.referring_facility_id,
            receiving_practitioner_id=source.receiving_practitioner_id,
            receiving_facility_id=source.receiving_facility_id,
            receiving_department_id=source.receiving_department_id,
            referral_reason=source.referral_reason,
            clinical_summary=source.clinical_findings,
            diagnosis_code=source.diagnosis_code,
            icd10_code=source.icd10_code,
            additional_notes=source.additional_notes,
            sent_at=source.sent_at,
            accepted_at=source.accepted_at,
            completed_at=source.completed_at,
            cancelled_at=source.cancelled_at,
            cancellation_reason=source.cancellation_reason,
            metadata_={"legacy_source": "national_referrals", "legacy_id": source.id},
            lab_id=lab_id,
        )
        self.db.add(canonical)
        self.db.flush()
        source.canonical_referral_id = canonical.id
        self.db.flush()
        return canonical

    def from_insurance(self, *, legacy_id: int, lab_id: int) -> ReferralRequest:
        source = (
            self.db.query(InsuranceReferral)
            .filter(InsuranceReferral.id == legacy_id, InsuranceReferral.lab_id == lab_id)
            .one_or_none()
        )
        if source is None:
            raise CanonicalReferralMappingError("insurance_referral_not_found_or_scope_denied")
        existing = self._existing(source.canonical_referral_id, lab_id)
        if existing is not None:
            return existing
        patient = self._national_patient(lab_id=lab_id, legacy_patient_id=source.patient_id)
        referring = self._national_practitioner(lab_id=lab_id, legacy_user_id=source.from_practitioner_id)
        receiving = self._national_practitioner(lab_id=lab_id, legacy_user_id=source.to_practitioner_id)
        if referring is None:
            raise CanonicalReferralMappingError("server_practitioner_mapping_required")
        self._require_facility_mapping(source.from_facility_id)
        self._require_facility_mapping(source.to_facility_id)
        canonical = ReferralRequest(
            patient_id=patient.id,
            citizen_id=patient.citizen_id,
            direction=ReferralDirection.OUTGOING,
            status=_status(source.status),
            priority=_priority(source.priority),
            referring_practitioner_id=referring.id,
            receiving_practitioner_id=receiving.id if receiving else None,
            referral_reason=source.clinical_reason or source.service_description or "Insurance referral",
            clinical_summary=source.clinical_notes,
            diagnosis_code=source.diagnosis_code,
            icd10_code=source.icd10_code,
            additional_notes=source.notes,
            metadata_={"legacy_source": "ins_referrals", "legacy_id": str(source.id), "referral_number": source.referral_number},
            lab_id=lab_id,
        )
        self.db.add(canonical)
        self.db.flush()
        source.canonical_referral_id = canonical.id
        self.db.flush()
        return canonical
