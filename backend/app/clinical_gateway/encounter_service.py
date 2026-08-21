from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.clinical_gateway.access_context import ClinicalAccessContext
from app.clinical_gateway.context import ClinicalGatewayBlocked
from app.models.clinical_scope import ClinicalEhrFacilityBinding, ClinicalEhrFacilityBindingStatus
from app.models.lab_user import LabUser
from app.national.domain.encounter import Encounter
from app.national.domain.patient import Patient as NationalPatient
from app.national.domain.practitioner import Practitioner
from app.national.enums import EncounterStatus, EncounterType, PractitionerRole


class EncounterService:
    def __init__(self, db: Session):
        self.db = db

    def _resolve_patient(self, access: ClinicalAccessContext, legacy_patient_id: int) -> NationalPatient:
        patients = (
            self.db.query(NationalPatient)
            .filter(
                NationalPatient.lab_patient_id == legacy_patient_id,
                NationalPatient.lab_id == access.legacy_lab_id,
                NationalPatient.is_active.is_(True),
                NationalPatient.is_deleted.is_(False),
            )
            .all()
        )
        if len(patients) != 1:
            raise ClinicalGatewayBlocked("national_patient_mapping_missing_or_ambiguous")
        return patients[0]

    def _resolve_practitioner(self, access: ClinicalAccessContext) -> Practitioner:
        user = self.db.get(LabUser, access.legacy_user_id)
        if user is None or not user.national_id_hash:
            raise ClinicalGatewayBlocked("server_practitioner_mapping_required")
        practitioners = (
            self.db.query(Practitioner)
            .filter(
                Practitioner.national_id_hash == user.national_id_hash,
                Practitioner.is_active.is_(True),
                Practitioner.is_verified.is_(True),
                Practitioner.role.in_((PractitionerRole.DOCTOR, PractitionerRole.SPECIALIST, PractitionerRole.CONSULTANT, PractitionerRole.RESIDENT)),
            )
            .all()
        )
        if len(practitioners) != 1:
            raise ClinicalGatewayBlocked("server_practitioner_mapping_missing_or_ambiguous")
        return practitioners[0]

    def _resolve_facility_id(self, access: ClinicalAccessContext) -> str:
        bindings = (
            self.db.query(ClinicalEhrFacilityBinding)
            .filter(
                ClinicalEhrFacilityBinding.facility_resource_id == access.operational_facility_id,
                ClinicalEhrFacilityBinding.status == ClinicalEhrFacilityBindingStatus.active.value,
            )
            .all()
        )
        if len(bindings) != 1:
            raise ClinicalGatewayBlocked("national_facility_mapping_missing_or_ambiguous")
        return str(bindings[0].national_facility_id)

    def create(
        self,
        *,
        access: ClinicalAccessContext,
        patient_id: int,
        encounter_type: str,
        reason_code: str | None = None,
        reason_description: str | None = None,
        priority: str = "routine",
        is_emergency: bool = False,
    ) -> Encounter:
        access.require_operation("create")
        try:
            encounter_type_enum = EncounterType(encounter_type)
        except ValueError as exc:
            raise ClinicalGatewayBlocked("invalid_encounter_type") from exc
        patient = self._resolve_patient(access, patient_id)
        practitioner = self._resolve_practitioner(access)
        facility_id = self._resolve_facility_id(access)
        encounter = Encounter(
            encounter_type=encounter_type_enum,
            status=EncounterStatus.PLANNED,
            patient_id=str(patient.id),
            citizen_id=patient.citizen_id,
            facility_id=facility_id,
            practitioner_id=str(practitioner.id),
            period_start=datetime.now(UTC),
            reason_code=reason_code,
            reason_description=reason_description,
            priority=priority,
            is_emergency=is_emergency,
            metadata_={"clinical_scope_mapping_version": access.scope_mapping_version},
        )
        self.db.add(encounter)
        self.db.flush()
        return encounter

    def _get_owned(self, access: ClinicalAccessContext, encounter_id: str) -> Encounter:
        practitioner = self._resolve_practitioner(access)
        facility_id = self._resolve_facility_id(access)
        encounter = (
            self.db.query(Encounter)
            .filter(
                Encounter.id == encounter_id,
                Encounter.practitioner_id == str(practitioner.id),
                Encounter.facility_id == facility_id,
                Encounter.is_deleted.is_(False),
            )
            .one_or_none()
        )
        if encounter is None:
            raise ClinicalGatewayBlocked("encounter_scope_denied")
        return encounter

    def start(self, *, access: ClinicalAccessContext, encounter_id: str) -> Encounter:
        access.require_operation("update")
        encounter = self._get_owned(access, encounter_id)
        if encounter.status != EncounterStatus.PLANNED:
            raise ClinicalGatewayBlocked("invalid_encounter_start_transition")
        encounter.status = EncounterStatus.IN_PROGRESS
        self.db.flush()
        return encounter

    def complete(self, *, access: ClinicalAccessContext, encounter_id: str, disposition: str | None = None, notes: str | None = None) -> Encounter:
        access.require_operation("update")
        encounter = self._get_owned(access, encounter_id)
        if encounter.status != EncounterStatus.IN_PROGRESS:
            raise ClinicalGatewayBlocked("invalid_encounter_complete_transition")
        encounter.status = EncounterStatus.COMPLETED
        encounter.period_end = datetime.now(UTC)
        if encounter.period_start:
            encounter.duration_minutes = max(0, int((encounter.period_end - encounter.period_start).total_seconds() // 60))
        encounter.disposition = disposition
        encounter.notes = notes
        self.db.flush()
        return encounter

    @staticmethod
    def to_safe_dict(encounter: Encounter) -> dict[str, Any]:
        return {
            "id": encounter.id,
            "encounter_type": encounter.encounter_type.value if hasattr(encounter.encounter_type, "value") else encounter.encounter_type,
            "status": encounter.status.value if hasattr(encounter.status, "value") else encounter.status,
            "patient_id": encounter.patient_id,
            "citizen_id": encounter.citizen_id,
            "facility_id": encounter.facility_id,
            "practitioner_id": encounter.practitioner_id,
            "period_start": encounter.period_start,
            "period_end": encounter.period_end,
            "duration_minutes": encounter.duration_minutes,
            "reason_code": encounter.reason_code,
            "reason_description": encounter.reason_description,
            "priority": encounter.priority,
            "is_emergency": encounter.is_emergency,
            "disposition": encounter.disposition,
            "notes": encounter.notes,
        }
