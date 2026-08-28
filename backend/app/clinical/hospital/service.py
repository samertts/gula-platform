from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.clinical.appointments.authorization import (
    AppointmentAuthorizationError,
    AppointmentAuthorizationService,
)
from app.clinical.appointments.service import AppointmentError, VersionConflictError
from app.clinical.command_guard import CanonicalClinicalCommandGuard
from app.contracts.clinical_core import require_transition
from app.identity.api.workspaces import NiamActor
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService

from .models import (
    CoreAdmission,
    CoreBedAllocation,
    CoreCareTeamMember,
    CoreDischarge,
    CoreDischargeSummary,
    CoreHandover,
    CoreHospitalBed,
    CoreHospitalRoom,
    CoreHospitalWard,
    CoreMedicationAdministration,
    CoreMedicationSafetyEvent,
    CoreNursingTask,
    CorePatientTransfer,
    CoreVitalObservation,
)


class HospitalNotFoundError(AppointmentError):
    code = "HOSPITAL_RESOURCE_NOT_FOUND"
    status_code = 404


class HospitalConflictError(AppointmentError):
    code = "HOSPITAL_STATE_CONFLICT"
    status_code = 409


class BedUnavailableError(HospitalConflictError):
    code = "BED_UNAVAILABLE"


class BedAlreadyAllocatedError(HospitalConflictError):
    code = "BED_ALREADY_ALLOCATED"


class InvalidAdmissionStateError(HospitalConflictError):
    code = "INVALID_ADMISSION_STATE"


class TransferConflictError(HospitalConflictError):
    code = "TRANSFER_CONFLICT"


class TaskAlreadyClaimedError(HospitalConflictError):
    code = "TASK_ALREADY_CLAIMED"


class DuplicateAdministrationError(HospitalConflictError):
    code = "DUPLICATE_ADMINISTRATION"


class DischargeNotReadyError(HospitalConflictError):
    code = "DISCHARGE_NOT_READY"


class CanonicalHospitalService:
    """Server-authoritative hospital workflow over canonical opaque IDs.

    Legacy hospital tables and services remain outside this owner boundary. The
    service never accepts patient/facility/organization identity from a client;
    patient is derived from the canonical encounter and scope is derived from
    the active NIAM workspace context.
    """

    def __init__(self, db):
        self.db = db
        self.authz = AppointmentAuthorizationService(db)
        self.audit = SyncCanonicalAuditService(db)
        self.command_guard = CanonicalClinicalCommandGuard(db, actor_account_id=None)

    def create_ward(self, actor: NiamActor, *, workspace_id: str, code: str, name: str, capacity: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.bed.manage")
        code = code.strip()
        payload = {"workspace_id": scope.workspace_id, "code": code, "name": name.strip(), "capacity": capacity}
        cached = self._claim(actor, "hospital.ward.create", idempotency_key, payload)
        if cached is not None:
            return cached
        if self.db.query(CoreHospitalWard).filter(CoreHospitalWard.facility_id == scope.facility_id, CoreHospitalWard.code == code).first() is not None:
            raise HospitalConflictError("Ward code already exists in this facility", code="WARD_EXISTS")
        ward = CoreHospitalWard(facility_id=scope.facility_id, organization_id=scope.organization_id, code=code, name=name.strip(), capacity=capacity, status="ACTIVE", version=1)
        self.db.add(ward)
        self.db.flush()
        response = {"id": ward.id, "facility_id": ward.facility_id, "organization_id": ward.organization_id, "code": ward.code, "name": ward.name, "capacity": ward.capacity, "status": ward.status, "version": ward.version, "correlation_id": correlation_id}
        self._complete(actor, "hospital.ward.create", idempotency_key, response, ward.id)
        self._audit(actor, "WARD_CREATED", "hospital_ward", ward.id, scope, correlation_id, request_id, {"code": ward.code, "capacity": ward.capacity})
        return response

    def create_room(self, actor: NiamActor, *, workspace_id: str, ward_id: str, code: str, name: str, capacity: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.bed.manage")
        ward = self._ward_for_scope(ward_id, scope)
        code = code.strip()
        payload = {"workspace_id": scope.workspace_id, "ward_id": ward.id, "code": code, "name": name.strip(), "capacity": capacity}
        cached = self._claim(actor, "hospital.room.create", idempotency_key, payload)
        if cached is not None:
            return cached

        if self.db.query(CoreHospitalRoom).filter(CoreHospitalRoom.ward_id == ward.id, CoreHospitalRoom.code == code).first() is not None:
            raise HospitalConflictError("Room code already exists in this ward", code="ROOM_EXISTS")
        room = CoreHospitalRoom(ward_id=ward.id, facility_id=scope.facility_id, organization_id=scope.organization_id, code=code, name=name.strip(), capacity=capacity, status="ACTIVE", version=1)
        self.db.add(room)
        self.db.flush()
        response = {"id": room.id, "ward_id": room.ward_id, "facility_id": room.facility_id, "code": room.code, "name": room.name, "capacity": room.capacity, "status": room.status, "version": room.version, "correlation_id": correlation_id}
        self._complete(actor, "hospital.room.create", idempotency_key, response, room.id)
        self._audit(actor, "ROOM_CREATED", "hospital_room", room.id, scope, correlation_id, request_id, {"ward_id": ward.id, "code": room.code, "capacity": room.capacity})
        return response

    def create_bed(self, actor: NiamActor, *, workspace_id: str, room_id: str, code: str, bed_type: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.bed.manage")

        room = self.db.query(CoreHospitalRoom).filter(CoreHospitalRoom.id == room_id, CoreHospitalRoom.organization_id == scope.organization_id, CoreHospitalRoom.facility_id == scope.facility_id, CoreHospitalRoom.status == "ACTIVE").with_for_update().first()
        if room is None:
            raise HospitalNotFoundError("Room was not found", code="ROOM_NOT_FOUND")
        code = code.strip()
        payload = {"workspace_id": scope.workspace_id, "room_id": room.id, "code": code, "bed_type": bed_type.strip()}
        cached = self._claim(actor, "hospital.bed.create", idempotency_key, payload)
        if cached is not None:
            return cached
        from sqlalchemy import func

        existing_count = self.db.query(func.count(CoreHospitalBed.id)).filter(CoreHospitalBed.room_id == room.id).scalar() or 0
        if existing_count >= room.capacity:
            raise HospitalConflictError("Room capacity has been reached", code="ROOM_CAPACITY_REACHED")
        if self.db.query(CoreHospitalBed).filter(CoreHospitalBed.room_id == room.id, CoreHospitalBed.code == code).first() is not None:
            raise HospitalConflictError("Bed code already exists in this room", code="BED_EXISTS")
        bed = CoreHospitalBed(room_id=room.id, ward_id=room.ward_id, facility_id=scope.facility_id, organization_id=scope.organization_id, code=code, bed_type=bed_type.strip(), status="AVAILABLE", version=1)
        self.db.add(bed)
        self.db.flush()
        response = self._bed_response(bed, correlation_id)
        self._complete(actor, "hospital.bed.create", idempotency_key, response, bed.id)
        self._audit(actor, "BED_CREATED", "hospital_bed", bed.id, scope, correlation_id, request_id, {"room_id": room.id, "code": bed.code, "status_after": bed.status})
        return response

    def add_care_team_member(self, actor: NiamActor, *, admission_id: str, workspace_id: str, account_id: str, role: str, member_scope: str, purpose: str, starts_at: datetime | None, ends_at: datetime | None, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.care_team.write")
        admission = self._admission_for_scope(admission_id, scope)
        starts_at = starts_at or datetime.now(UTC)
        if ends_at is not None and ends_at <= starts_at:
            raise HospitalConflictError("Care-team end must be after start", code="CARE_TEAM_TIME_INVALID", status_code=422)
        role = role.strip().lower()
        if role not in {"physician", "nurse", "pharmacist", "specialist", "other"}:
            raise HospitalConflictError("Care-team role is not allowed", code="CARE_TEAM_ROLE_INVALID", status_code=422)
        from app.identity.models import Account, Membership

        member = self.db.query(Account).filter(Account.id == account_id, Account.is_active.is_(True), Account.is_locked.is_(False), Account.status == "active").first()
        if member is None:
            raise HospitalNotFoundError("Care-team account was not found", code="CARE_TEAM_ACCOUNT_NOT_FOUND")
        membership = self.db.query(Membership).filter(Membership.account_id == member.id, Membership.organization_id == scope.organization_id, Membership.facility_id == scope.facility_id, Membership.workspace_id == scope.workspace_id, Membership.status == "active", Membership.is_active.is_(True)).first()
        if membership is None:
            raise AppointmentAuthorizationError("care_team_membership_denied", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        payload = {"admission_id": admission.id, "workspace_id": scope.workspace_id, "account_id": member.id, "role": role, "scope": member_scope.strip(), "purpose": purpose.strip(), "starts_at": starts_at.isoformat(), "ends_at": ends_at.isoformat() if ends_at else None}
        cached = self._claim(actor, "hospital.care_team.create", idempotency_key, payload)
        if cached is not None:
            return cached
        existing = self.db.query(CoreCareTeamMember).filter(CoreCareTeamMember.admission_id == admission.id, CoreCareTeamMember.account_id == member.id, CoreCareTeamMember.status == "ACTIVE").first()
        if existing is not None:
            raise HospitalConflictError("This account is already on the active care team", code="CARE_TEAM_MEMBER_EXISTS")
        row = CoreCareTeamMember(admission_id=admission.id, patient_person_id=admission.patient_person_id, account_id=member.id, role=role, scope=member_scope.strip(), purpose=purpose.strip(), starts_at=starts_at, ends_at=ends_at, status="ACTIVE", version=1)
        self.db.add(row)
        self.db.flush()
        response = {"id": row.id, "admission_id": row.admission_id, "patient_person_id": row.patient_person_id, "account_id": row.account_id, "role": row.role, "scope": row.scope, "purpose": row.purpose, "status": row.status, "starts_at": row.starts_at.isoformat(), "ends_at": row.ends_at.isoformat() if row.ends_at else None, "version": row.version, "correlation_id": correlation_id}
        self._complete(actor, "hospital.care_team.create", idempotency_key, response, row.id)
        self._audit(actor, "CARE_TEAM_MEMBER_ADDED", "hospital_care_team_member", row.id, scope, correlation_id, request_id, {"admission_id": row.admission_id, "account_id": row.account_id, "role": row.role, "scope": row.scope, "purpose": row.purpose})
        return response

    def create_admission(
        self,
        actor: NiamActor,
        *,
        admission_request_id: str,
        encounter_id: str,
        workspace_id: str,
        ward_id: str,
        admission_reason: str,
        admission_type: str,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.admission.create")
        encounter = self._encounter_for_scope(encounter_id, scope)
        if encounter.status not in {"IN_PROGRESS", "COMPLETED"}:
            raise InvalidAdmissionStateError("Admission requires an active or completed encounter", code="ENCOUNTER_NOT_ELIGIBLE")
        if encounter.provider_account_id != actor.account.id:
            raise AppointmentAuthorizationError("admission_provider_object_denied", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        ward = self._ward_for_scope(ward_id, scope)
        payload = {
            "admission_request_id": admission_request_id,
            "encounter_id": encounter.id,
            "workspace_id": scope.workspace_id,
            "ward_id": ward.id,
            "admission_type": admission_type,
            "admission_reason": admission_reason.strip(),
        }
        cached = self._claim(actor, "hospital.admission.create", idempotency_key, payload)
        if cached is not None:
            return cached
        existing = self.db.query(CoreAdmission).filter(CoreAdmission.admission_request_id == admission_request_id).first()
        if existing is not None:
            raise HospitalConflictError("Admission request already exists", code="ADMISSION_REQUEST_EXISTS")
        admission = CoreAdmission(
            admission_request_id=admission_request_id.strip(),
            patient_person_id=encounter.patient_person_id,
            encounter_id=encounter.id,
            facility_id=scope.facility_id,
            organization_id=scope.organization_id,
            ward_id=ward.id,
            admitting_provider_account_id=actor.account.id,
            admission_reason=admission_reason.strip(),
            admission_type=admission_type,
            status="REQUESTED",
            version=1,
        )
        self.db.add(admission)
        self.db.flush()
        response = self._admission_response(admission, correlation_id)
        self._complete(actor, "hospital.admission.create", idempotency_key, response, admission.id)
        self._audit(actor, "ADMISSION_CREATED", "hospital_admission", admission.id, scope, correlation_id, request_id, {"state_after": admission.status, "version": admission.version, "admission_type": admission.admission_type})
        return response

    def transition_admission(
        self,
        actor: NiamActor,
        *,
        admission_id: str,
        workspace_id: str,
        target_status: str,
        expected_version: int,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.admission.transition")
        admission = self._admission_for_update(admission_id, scope)
        self._assert_version(admission.version, expected_version)
        payload = {"resource_id": admission.id, "workspace_id": scope.workspace_id, "target_status": target_status, "expected_version": expected_version}
        cached = self._claim(actor, "hospital.admission.transition", idempotency_key, payload)
        if cached is not None:
            return cached
        if target_status in {"DISCHARGED", "TRANSFERRED"}:
            raise HospitalConflictError("Use the dedicated discharge or transfer workflow", code="DEDICATED_WORKFLOW_REQUIRED")
        require_transition("hospital-admission", admission.status, target_status)
        before = admission.status
        admission.status = target_status
        admission.version += 1
        now = datetime.now(UTC)
        if target_status == "ADMITTED":
            admission.admitted_at = now
        if target_status == "DISCHARGED":
            admission.discharged_at = now
        self.db.flush()
        response = self._admission_response(admission, correlation_id)
        self._complete(actor, "hospital.admission.transition", idempotency_key, response, admission.id)
        self._audit(actor, "ADMISSION_STATUS_CHANGED", "hospital_admission", admission.id, scope, correlation_id, request_id, {"state_before": before, "state_after": target_status, "version": admission.version})
        return response

    def allocate_bed(
        self,
        actor: NiamActor,
        *,
        admission_id: str,
        bed_id: str,
        workspace_id: str,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.bed.allocate")
        admission = self._admission_for_update(admission_id, scope)
        bed = self._bed_for_update(bed_id, scope)
        payload = {"admission_id": admission.id, "bed_id": bed.id, "workspace_id": scope.workspace_id}
        cached = self._claim(actor, "hospital.bed.allocate", idempotency_key, payload)
        if cached is not None:
            return cached
        if admission.status not in {"ACCEPTED", "ADMITTED", "IN_CARE"}:
            raise InvalidAdmissionStateError("Only an accepted or admitted admission can receive a bed")
        if admission.status == "ACCEPTED":
            require_transition("hospital-admission", admission.status, "ADMITTED")
        if bed.status not in {"AVAILABLE", "RESERVED"}:
            raise BedUnavailableError("Bed is not available")
        active_bed = self.db.query(CoreBedAllocation).filter(CoreBedAllocation.bed_id == bed.id, CoreBedAllocation.released_at.is_(None)).with_for_update().first()
        if active_bed is not None:
            raise BedAlreadyAllocatedError("Bed already has an active allocation")
        active_patient = self.db.query(CoreBedAllocation).filter(CoreBedAllocation.patient_person_id == admission.patient_person_id, CoreBedAllocation.released_at.is_(None)).with_for_update().first()
        if active_patient is not None:
            raise BedAlreadyAllocatedError("Patient already has an active bed allocation")
        if admission.ward_id != bed.ward_id:
            raise HospitalConflictError("Bed is outside the admission ward", code="WARD_SCOPE_MISMATCH")
        allocation = CoreBedAllocation(admission_id=admission.id, patient_person_id=admission.patient_person_id, bed_id=bed.id, ward_id=bed.ward_id, facility_id=scope.facility_id, organization_id=scope.organization_id, allocated_by_account_id=actor.account.id, version=1)
        self.db.add(allocation)
        before = bed.status
        bed.status = "OCCUPIED"
        bed.version += 1
        if admission.status == "ACCEPTED":
            admission.status = "ADMITTED"
            admission.admitted_at = datetime.now(UTC)
            admission.version += 1
        self.db.flush()
        response = {"allocation": self._allocation_response(allocation, correlation_id), "bed": self._bed_response(bed, correlation_id), "admission": self._admission_response(admission, correlation_id)}
        self._complete(actor, "hospital.bed.allocate", idempotency_key, response, allocation.id)
        self._audit(actor, "BED_ALLOCATED", "hospital_bed_allocation", allocation.id, scope, correlation_id, request_id, {"bed_id": bed.id, "state_before": before, "state_after": bed.status, "admission_id": admission.id, "version": bed.version})
        return response

    def create_task(
        self,
        actor: NiamActor,
        *,
        admission_id: str,
        workspace_id: str,
        task_type: str,
        instructions: str | None,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.task.write")
        admission = self._admission_for_scope(admission_id, scope)
        payload = {"admission_id": admission.id, "workspace_id": scope.workspace_id, "task_type": task_type, "instructions": instructions}
        cached = self._claim(actor, "hospital.task.create", idempotency_key, payload)
        if cached is not None:
            return cached
        task = CoreNursingTask(admission_id=admission.id, patient_person_id=admission.patient_person_id, ward_id=admission.ward_id, facility_id=scope.facility_id, organization_id=scope.organization_id, task_type=task_type.strip(), instructions=instructions.strip() if instructions else None, status="OPEN", version=1)
        self.db.add(task)
        self.db.flush()
        response = self._task_response(task, correlation_id)
        self._complete(actor, "hospital.task.create", idempotency_key, response, task.id)
        self._audit(actor, "TASK_CREATED", "hospital_nursing_task", task.id, scope, correlation_id, request_id, {"state_after": task.status, "task_type": task.task_type})
        return response

    def transition_task(
        self,
        actor: NiamActor,
        *,
        task_id: str,
        workspace_id: str,
        target_status: str,
        expected_version: int,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.task.write")
        task = self.db.query(CoreNursingTask).filter(CoreNursingTask.id == task_id, CoreNursingTask.organization_id == scope.organization_id, CoreNursingTask.facility_id == scope.facility_id).with_for_update().first()
        if task is None:
            raise HospitalNotFoundError("Nursing task was not found", code="TASK_NOT_FOUND")
        self._assert_version(task.version, expected_version)
        payload = {"resource_id": task.id, "workspace_id": scope.workspace_id, "target_status": target_status, "expected_version": expected_version}
        cached = self._claim(actor, "hospital.task.transition", idempotency_key, payload)
        if cached is not None:
            return cached
        require_transition("hospital-task", task.status, target_status)
        if target_status == "CLAIMED":
            if task.assigned_to_account_id is not None:
                raise TaskAlreadyClaimedError("Task is already claimed")
            task.assigned_to_account_id = actor.account.id
            task.claimed_at = datetime.now(UTC)
        elif task.assigned_to_account_id not in {None, actor.account.id}:
            raise AppointmentAuthorizationError("task_object_denied", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        before = task.status
        task.status = target_status
        task.version += 1
        if target_status == "COMPLETED":
            task.completed_at = datetime.now(UTC)
        self.db.flush()
        response = self._task_response(task, correlation_id)
        self._complete(actor, "hospital.task.transition", idempotency_key, response, task.id)
        self._audit(actor, "TASK_STATUS_CHANGED", "hospital_nursing_task", task.id, scope, correlation_id, request_id, {"state_before": before, "state_after": target_status, "version": task.version})
        return response

    def record_vital(
        self,
        actor: NiamActor,
        *,
        admission_id: str | None,
        encounter_id: str,
        workspace_id: str,
        vital_type: str,
        value_numeric: str,
        unit: str,
        method: str,
        source: str,
        observed_at: datetime,
        device_reference: str | None,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.vitals.write")
        encounter = self._encounter_for_scope(encounter_id, scope)
        admission = self._admission_for_scope(admission_id, scope) if admission_id else None
        if admission is not None and admission.patient_person_id != encounter.patient_person_id:
            raise AppointmentAuthorizationError("vital_patient_mismatch", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        normalized_type = vital_type.strip().lower()
        numeric = self._parse_numeric(value_numeric)
        normalized_unit = unit.strip()
        self._validate_vital(normalized_type, numeric, normalized_unit)
        warning_code = self._vital_warning(normalized_type, numeric, normalized_unit)
        payload = {"encounter_id": encounter.id, "admission_id": admission.id if admission else None, "workspace_id": scope.workspace_id, "vital_type": normalized_type, "value_numeric": str(numeric), "unit": normalized_unit, "observed_at": observed_at.isoformat()}
        cached = self._claim(actor, "hospital.vital.create", idempotency_key, payload)
        if cached is not None:
            return cached
        observation = CoreVitalObservation(patient_person_id=encounter.patient_person_id, encounter_id=encounter.id, admission_id=admission.id if admission else None, observer_account_id=actor.account.id, device_reference=device_reference, vital_type=normalized_type, value_numeric=str(numeric), unit=normalized_unit, method=method.strip(), source=source.strip(), observed_at=observed_at, validation_status="WARNING" if warning_code else "VALID", warning_code=warning_code, version=1)
        self.db.add(observation)
        self.db.flush()
        response = self._vital_response(observation, correlation_id)
        self._complete(actor, "hospital.vital.create", idempotency_key, response, observation.id)
        self._audit(actor, "VITAL_RECORDED", "hospital_vital_observation", observation.id, scope, correlation_id, request_id, {"vital_type": normalized_type, "validation_status": observation.validation_status, "warning_code": warning_code})
        return response

    def create_emar(
        self,
        actor: NiamActor,
        *,
        admission_id: str,
        prescription_id: str,
        prescription_item_id: str,
        workspace_id: str,
        administration_key: str,
        dose_value: str,
        dose_unit: str,
        route: str,
        scheduled_at: datetime | None,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.emar.write")
        admission = self._admission_for_scope(admission_id, scope)
        from app.clinical.pharmacy.models import CorePrescription, CorePrescriptionItem

        prescription = self.db.query(CorePrescription).filter(CorePrescription.id == prescription_id, CorePrescription.organization_id == scope.organization_id, CorePrescription.facility_id == scope.facility_id, CorePrescription.workspace_id == scope.workspace_id).first()
        if prescription is None or prescription.status not in {"SIGNED", "AMENDED", "COMPLETED"}:
            raise HospitalConflictError("Only a signed prescription may be administered", code="PRESCRIPTION_NOT_ADMINISTRABLE")
        item = self.db.query(CorePrescriptionItem).filter(CorePrescriptionItem.id == prescription_item_id, CorePrescriptionItem.prescription_row_id == prescription.id).first()
        if item is None or prescription.patient_person_id != admission.patient_person_id:
            raise HospitalConflictError("Prescription does not belong to the admitted patient", code="PRESCRIPTION_PATIENT_MISMATCH")
        payload = {"administration_key": administration_key, "admission_id": admission.id, "prescription_id": prescription.id, "prescription_item_id": item.id, "workspace_id": scope.workspace_id, "dose_value": dose_value.strip(), "dose_unit": dose_unit.strip(), "route": route.strip()}
        cached = self._claim(actor, "hospital.emar.create", idempotency_key, payload)
        if cached is not None:
            return cached
        if self.db.query(CoreMedicationAdministration).filter(CoreMedicationAdministration.administration_key == administration_key).first() is not None:
            raise DuplicateAdministrationError("Administration key already exists")
        emar = CoreMedicationAdministration(administration_key=administration_key.strip(), admission_id=admission.id, patient_person_id=admission.patient_person_id, encounter_id=prescription.encounter_id, prescription_id=prescription.id, prescription_item_id=item.id, medication_catalog_id=item.medication_catalog_id, administrator_account_id=actor.account.id, dose_value=dose_value.strip(), dose_unit=dose_unit.strip(), route=route.strip(), scheduled_at=scheduled_at, status="ORDERED", version=1)
        self.db.add(emar)
        self.db.flush()
        response = self._emar_response(emar, correlation_id)
        self._complete(actor, "hospital.emar.create", idempotency_key, response, emar.id)
        self._audit(actor, "MEDICATION_ORDERED_FOR_ADMINISTRATION", "hospital_emar", emar.id, scope, correlation_id, request_id, {"state_after": emar.status, "prescription_id": prescription.id})
        return response

    def transition_emar(
        self,
        actor: NiamActor,
        *,
        administration_id: str,
        workspace_id: str,
        target_status: str,
        reason: str | None,
        expected_version: int,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.emar.write")
        emar = self.db.query(CoreMedicationAdministration).filter(CoreMedicationAdministration.id == administration_id, CoreMedicationAdministration.organization_id == scope.organization_id, CoreMedicationAdministration.facility_id == scope.facility_id).with_for_update().first()
        if emar is None:
            raise HospitalNotFoundError("Medication administration was not found", code="EMAR_NOT_FOUND")
        self._assert_version(emar.version, expected_version)
        payload = {"resource_id": emar.id, "workspace_id": scope.workspace_id, "target_status": target_status, "expected_version": expected_version, "reason": reason}
        cached = self._claim(actor, "hospital.emar.transition", idempotency_key, payload)
        if cached is not None:
            return cached
        require_transition("hospital-emar", emar.status, target_status)
        if target_status in {"HELD", "REFUSED", "MISSED", "CANCELLED"} and not reason:
            raise HospitalConflictError("A reason is required for this outcome", code="EMAR_REASON_REQUIRED", status_code=422)
        from app.clinical.pharmacy.models import CorePrescriptionItem

        item = self.db.query(CorePrescriptionItem).filter(CorePrescriptionItem.id == emar.prescription_item_id).first()
        if item is None or item.medication_catalog_id != emar.medication_catalog_id:
            raise HospitalConflictError("Medication identity cannot be verified", code="MEDICATION_MISMATCH")
        before = emar.status
        emar.status = target_status
        emar.reason = reason.strip() if reason else None
        emar.version += 1
        if target_status == "ADMINISTERED":
            emar.administered_at = datetime.now(UTC)
        self.db.flush()
        response = self._emar_response(emar, correlation_id)
        self._complete(actor, "hospital.emar.transition", idempotency_key, response, emar.id)
        self._audit(actor, "MEDICATION_ADMINISTRATION_STATUS_CHANGED", "hospital_emar", emar.id, scope, correlation_id, request_id, {"state_before": before, "state_after": target_status, "version": emar.version, "reason": reason})
        return response

    def create_safety_event(
        self,
        actor: NiamActor,
        *,
        administration_id: str,
        workspace_id: str,
        event_type: str,
        severity: str,
        description: str,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.emar.write")
        emar = self.db.query(CoreMedicationAdministration).filter(CoreMedicationAdministration.id == administration_id, CoreMedicationAdministration.organization_id == scope.organization_id, CoreMedicationAdministration.facility_id == scope.facility_id).first()
        if emar is None:
            raise HospitalNotFoundError("Medication administration was not found", code="EMAR_NOT_FOUND")
        payload = {"administration_id": emar.id, "workspace_id": scope.workspace_id, "event_type": event_type, "severity": severity, "description": description}
        cached = self._claim(actor, "hospital.emar.safety_event", idempotency_key, payload)
        if cached is not None:
            return cached
        event = CoreMedicationSafetyEvent(administration_id=emar.id, patient_person_id=emar.patient_person_id, event_type=event_type.strip(), severity=severity, description=description.strip(), reported_by_account_id=actor.account.id)
        self.db.add(event)
        self.db.flush()
        response = {"id": event.id, "administration_id": event.administration_id, "event_type": event.event_type, "severity": event.severity, "created_at": event.created_at.isoformat(), "correlation_id": correlation_id}
        self._complete(actor, "hospital.emar.safety_event", idempotency_key, response, event.id)
        self._audit(actor, "SAFETY_EVENT_CREATED", "hospital_medication_safety_event", event.id, scope, correlation_id, request_id, {"administration_id": emar.id, "severity": severity})
        return response

    def create_transfer(
        self,
        actor: NiamActor,
        *,
        transfer_request_id: str,
        admission_id: str,
        from_bed_id: str,
        to_bed_id: str,
        workspace_id: str,
        reason: str,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.transfer.write")
        admission = self._admission_for_scope(admission_id, scope)
        source = self._bed_for_scope(from_bed_id, scope)
        target = self._bed_for_scope(to_bed_id, scope)
        if source.id == target.id:
            raise TransferConflictError("Source and target beds must differ")
        if source.ward_id == target.ward_id:
            raise TransferConflictError("Transfer requires a different ward", code="TRANSFER_SAME_WARD")
        payload = {"transfer_request_id": transfer_request_id, "admission_id": admission.id, "from_bed_id": source.id, "to_bed_id": target.id, "workspace_id": scope.workspace_id, "reason": reason.strip()}
        cached = self._claim(actor, "hospital.transfer.create", idempotency_key, payload)
        if cached is not None:
            return cached
        if self.db.query(CorePatientTransfer).filter(CorePatientTransfer.transfer_request_id == transfer_request_id).first() is not None:
            raise TransferConflictError("Transfer request already exists", code="TRANSFER_REQUEST_EXISTS")
        active = self.db.query(CoreBedAllocation).filter(CoreBedAllocation.admission_id == admission.id, CoreBedAllocation.released_at.is_(None)).first()
        if active is None or active.bed_id != source.id:
            raise TransferConflictError("Source bed is not the active bed for this admission")
        transfer = CorePatientTransfer(transfer_request_id=transfer_request_id.strip(), admission_id=admission.id, patient_person_id=admission.patient_person_id, from_ward_id=source.ward_id, to_ward_id=target.ward_id, from_bed_id=source.id, to_bed_id=target.id, facility_id=scope.facility_id, organization_id=scope.organization_id, requested_by_account_id=actor.account.id, status="REQUESTED", reason=reason.strip(), version=1)
        self.db.add(transfer)
        self.db.flush()
        response = self._transfer_response(transfer, correlation_id)
        self._complete(actor, "hospital.transfer.create", idempotency_key, response, transfer.id)
        self._audit(actor, "PATIENT_TRANSFER_REQUESTED", "hospital_transfer", transfer.id, scope, correlation_id, request_id, {"state_after": transfer.status, "from_bed_id": source.id, "to_bed_id": target.id})
        return response

    def transition_transfer(
        self,
        actor: NiamActor,
        *,
        transfer_id: str,
        workspace_id: str,
        target_status: str,
        expected_version: int,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.transfer.write")
        transfer = self.db.query(CorePatientTransfer).filter(CorePatientTransfer.id == transfer_id, CorePatientTransfer.organization_id == scope.organization_id, CorePatientTransfer.facility_id == scope.facility_id).with_for_update().first()
        if transfer is None:
            raise HospitalNotFoundError("Transfer was not found", code="TRANSFER_NOT_FOUND")
        self._assert_version(transfer.version, expected_version)
        payload = {"resource_id": transfer.id, "workspace_id": scope.workspace_id, "target_status": target_status, "expected_version": expected_version}
        cached = self._claim(actor, "hospital.transfer.transition", idempotency_key, payload)
        if cached is not None:
            return cached
        require_transition("hospital-transfer", transfer.status, target_status)
        if transfer.status == "IN_TRANSIT" and target_status == "RECEIVED":
            self._move_allocation(transfer, scope, actor)
        before = transfer.status
        transfer.status = target_status
        transfer.version += 1
        if target_status == "COMPLETED":
            transfer.completed_at = datetime.now(UTC)
        self.db.flush()
        response = self._transfer_response(transfer, correlation_id)
        self._complete(actor, "hospital.transfer.transition", idempotency_key, response, transfer.id)
        self._audit(actor, "PATIENT_TRANSFERRED" if target_status == "COMPLETED" else "PATIENT_TRANSFER_STATUS_CHANGED", "hospital_transfer", transfer.id, scope, correlation_id, request_id, {"state_before": before, "state_after": target_status, "version": transfer.version})
        return response

    def create_handover(
        self,
        actor: NiamActor,
        *,
        handover_request_id: str,
        admission_id: str,
        workspace_id: str,
        minimal_summary: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.handover.write")
        admission = self._admission_for_scope(admission_id, scope)
        allowed = {"diagnosis_context", "current_status", "medications", "allergies", "devices", "lines", "pending_tasks", "pending_results", "risks"}
        summary = {key: value for key, value in minimal_summary.items() if key in allowed}
        payload = {"handover_request_id": handover_request_id, "admission_id": admission.id, "workspace_id": scope.workspace_id, "minimal_summary": summary}
        cached = self._claim(actor, "hospital.handover.create", idempotency_key, payload)
        if cached is not None:
            return cached
        if self.db.query(CoreHandover).filter(CoreHandover.handover_request_id == handover_request_id).first() is not None:
            raise HospitalConflictError("Handover request already exists", code="HANDOVER_EXISTS")
        handover = CoreHandover(handover_request_id=handover_request_id.strip(), admission_id=admission.id, patient_person_id=admission.patient_person_id, sender_account_id=actor.account.id, status="SUBMITTED", minimal_summary=summary, version=1)
        self.db.add(handover)
        self.db.flush()
        response = self._handover_response(handover, correlation_id)
        self._complete(actor, "hospital.handover.create", idempotency_key, response, handover.id)
        self._audit(actor, "HANDOVER_SUBMITTED", "hospital_handover", handover.id, scope, correlation_id, request_id, {"state_after": handover.status, "field_count": len(summary)})
        return response

    def acknowledge_handover(
        self,
        actor: NiamActor,
        *,
        handover_id: str,
        workspace_id: str,
        expected_version: int,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.handover.write")
        handover = self.db.query(CoreHandover).join(CoreAdmission, CoreAdmission.id == CoreHandover.admission_id).filter(CoreHandover.id == handover_id, CoreAdmission.organization_id == scope.organization_id, CoreAdmission.facility_id == scope.facility_id).with_for_update().first()
        if handover is None:
            raise HospitalNotFoundError("Handover was not found", code="HANDOVER_NOT_FOUND")
        self._assert_version(handover.version, expected_version)
        payload = {"resource_id": handover.id, "workspace_id": scope.workspace_id, "expected_version": expected_version}
        cached = self._claim(actor, "hospital.handover.ack", idempotency_key, payload)
        if cached is not None:
            return cached
        if handover.status != "SUBMITTED":
            raise HospitalConflictError("Only a submitted handover can be acknowledged", code="HANDOVER_NOT_PENDING")
        handover.status = "ACKNOWLEDGED"
        handover.receiver_account_id = actor.account.id
        handover.acknowledged_at = datetime.now(UTC)
        handover.version += 1
        self.db.flush()
        response = self._handover_response(handover, correlation_id)
        self._complete(actor, "hospital.handover.ack", idempotency_key, response, handover.id)
        self._audit(actor, "HANDOVER_ACKNOWLEDGED", "hospital_handover", handover.id, scope, correlation_id, request_id, {"state_after": handover.status, "version": handover.version})
        return response

    def create_discharge(
        self,
        actor: NiamActor,
        *,
        discharge_request_id: str,
        admission_id: str,
        workspace_id: str,
        disposition: str,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.discharge.write")
        admission = self._admission_for_update(admission_id, scope)
        if admission.status not in {"ADMITTED", "IN_CARE", "DISCHARGE_PLANNED"}:
            raise InvalidAdmissionStateError("Admission is not eligible for discharge")
        payload = {"discharge_request_id": discharge_request_id, "admission_id": admission.id, "workspace_id": scope.workspace_id, "disposition": disposition}
        cached = self._claim(actor, "hospital.discharge.create", idempotency_key, payload)
        if cached is not None:
            return cached
        if self.db.query(CoreDischarge).filter(CoreDischarge.discharge_request_id == discharge_request_id).first() is not None:
            raise HospitalConflictError("Discharge request already exists", code="DISCHARGE_EXISTS")
        discharge = CoreDischarge(discharge_request_id=discharge_request_id.strip(), admission_id=admission.id, patient_person_id=admission.patient_person_id, facility_id=scope.facility_id, organization_id=scope.organization_id, responsible_provider_account_id=actor.account.id, disposition=disposition, status="PLANNED", version=1)
        self.db.add(discharge)
        if admission.status != "DISCHARGE_PLANNED":
            require_transition("hospital-admission", admission.status, "DISCHARGE_PLANNED")
            admission.status = "DISCHARGE_PLANNED"
            admission.version += 1
        self.db.flush()
        response = self._discharge_response(discharge, correlation_id)
        self._complete(actor, "hospital.discharge.create", idempotency_key, response, discharge.id)
        self._audit(actor, "DISCHARGE_CREATED", "hospital_discharge", discharge.id, scope, correlation_id, request_id, {"state_after": discharge.status, "disposition": disposition})
        return response

    def update_discharge_readiness(
        self,
        actor: NiamActor,
        *,
        discharge_id: str,
        workspace_id: str,
        medication_reconciliation_complete: bool,
        pending_results_reviewed: bool,
        follow_up_plan: str | None,
        instructions: str | None,
        expected_version: int,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.discharge.write")
        discharge = self._discharge_for_update(discharge_id, scope)
        self._assert_version(discharge.version, expected_version)
        payload = {"resource_id": discharge.id, "workspace_id": scope.workspace_id, "medication_reconciliation_complete": medication_reconciliation_complete, "pending_results_reviewed": pending_results_reviewed, "follow_up_plan": follow_up_plan, "instructions": instructions, "expected_version": expected_version}
        cached = self._claim(actor, "hospital.discharge.readiness", idempotency_key, payload)
        if cached is not None:
            return cached
        discharge.medication_reconciliation_complete = int(medication_reconciliation_complete)
        discharge.pending_results_reviewed = int(pending_results_reviewed)
        discharge.follow_up_plan = follow_up_plan.strip() if follow_up_plan else None
        discharge.instructions = instructions.strip() if instructions else None
        discharge.version += 1
        self.db.flush()
        response = self._discharge_response(discharge, correlation_id)
        self._complete(actor, "hospital.discharge.readiness", idempotency_key, response, discharge.id)
        self._audit(actor, "DISCHARGE_READINESS_UPDATED", "hospital_discharge", discharge.id, scope, correlation_id, request_id, {"version": discharge.version, "medication_reconciliation_complete": bool(discharge.medication_reconciliation_complete), "pending_results_reviewed": bool(discharge.pending_results_reviewed)})
        return response

    def create_discharge_summary(
        self,
        actor: NiamActor,
        *,
        discharge_id: str,
        workspace_id: str,
        data: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.discharge.write")
        discharge = self._discharge_for_scope(discharge_id, scope)
        payload = {"discharge_id": discharge.id, "workspace_id": scope.workspace_id, **data}
        cached = self._claim(actor, "hospital.discharge.summary.create", idempotency_key, payload)
        if cached is not None:
            return cached
        latest = self.db.query(CoreDischargeSummary).filter(CoreDischargeSummary.discharge_id == discharge.id).order_by(CoreDischargeSummary.summary_version.desc()).first()
        if latest is not None and latest.status == "DRAFT":
            raise HospitalConflictError("A draft discharge summary already exists", code="DISCHARGE_SUMMARY_EXISTS")
        version = latest.summary_version + 1 if latest else 1
        summary = CoreDischargeSummary(discharge_id=discharge.id, summary_version=version, status="DRAFT", authored_by_account_id=actor.account.id, **data)
        self.db.add(summary)
        self.db.flush()
        response = self._summary_response(summary, correlation_id)
        self._complete(actor, "hospital.discharge.summary.create", idempotency_key, response, summary.id)
        self._audit(actor, "DISCHARGE_SUMMARY_CREATED", "hospital_discharge_summary", summary.id, scope, correlation_id, request_id, {"status_after": summary.status, "summary_version": summary.summary_version})
        return response

    def sign_discharge_summary(
        self,
        actor: NiamActor,
        *,
        summary_id: str,
        workspace_id: str,
        expected_version: int,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.discharge.sign")
        summary = self.db.query(CoreDischargeSummary).join(CoreDischarge, CoreDischarge.id == CoreDischargeSummary.discharge_id).filter(CoreDischargeSummary.id == summary_id, CoreDischarge.organization_id == scope.organization_id, CoreDischarge.facility_id == scope.facility_id).with_for_update().first()
        if summary is None:
            raise HospitalNotFoundError("Discharge summary was not found", code="DISCHARGE_SUMMARY_NOT_FOUND")
        discharge = self._discharge_for_update(summary.discharge_id, scope)
        self._assert_version(summary.summary_version, expected_version)
        payload = {"resource_id": summary.id, "workspace_id": scope.workspace_id, "expected_version": expected_version}
        cached = self._claim(actor, "hospital.discharge.summary.sign", idempotency_key, payload)
        if cached is not None:
            return cached
        if summary.status != "DRAFT":
            raise HospitalConflictError("Signed discharge summaries are immutable", code="DISCHARGE_SUMMARY_IMMUTABLE")
        if not discharge.medication_reconciliation_complete or not discharge.pending_results_reviewed:
            raise DischargeNotReadyError("Discharge prerequisites are incomplete")
        summary.status = "SIGNED"
        summary.signed_at = datetime.now(UTC)
        summary.signed_by_account_id = actor.account.id
        self.db.flush()
        response = self._summary_response(summary, correlation_id)
        self._complete(actor, "hospital.discharge.summary.sign", idempotency_key, response, summary.id)
        self._audit(actor, "DISCHARGE_SUMMARY_SIGNED", "hospital_discharge_summary", summary.id, scope, correlation_id, request_id, {"status_after": summary.status, "summary_version": summary.summary_version, "discharge_version": discharge.version})
        return response

    def complete_discharge(
        self,
        actor: NiamActor,
        *,
        discharge_id: str,
        workspace_id: str,
        expected_version: int,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.hospital.discharge.write")
        discharge = self._discharge_for_update(discharge_id, scope)
        self._assert_version(discharge.version, expected_version)
        payload = {"resource_id": discharge.id, "workspace_id": scope.workspace_id, "expected_version": expected_version}
        cached = self._claim(actor, "hospital.discharge.complete", idempotency_key, payload)
        if cached is not None:
            return cached
        if discharge.status not in {"PLANNED", "APPROVED"}:
            raise HospitalConflictError("Discharge is not completable", code="DISCHARGE_NOT_COMPLETABLE")
        if not discharge.medication_reconciliation_complete or not discharge.pending_results_reviewed:
            raise DischargeNotReadyError("Discharge prerequisites are incomplete")
        summary = self.db.query(CoreDischargeSummary).filter(CoreDischargeSummary.discharge_id == discharge.id, CoreDischargeSummary.status == "SIGNED").order_by(CoreDischargeSummary.summary_version.desc()).first()
        if summary is None:
            raise DischargeNotReadyError("A signed discharge summary is required")
        admission = self._admission_for_update(discharge.admission_id, scope)
        active = self.db.query(CoreBedAllocation).filter(CoreBedAllocation.admission_id == admission.id, CoreBedAllocation.released_at.is_(None)).with_for_update().first()
        if active is not None:
            bed = self._bed_for_update(active.bed_id, scope)
            active.released_at = datetime.now(UTC)
            active.version += 1
            bed.status = "CLEANING"
            bed.version += 1
        require_transition("hospital-admission", admission.status, "DISCHARGED")
        admission.status = "DISCHARGED"
        admission.discharged_at = datetime.now(UTC)
        admission.version += 1
        discharge.status = "COMPLETED"
        discharge.completed_at = datetime.now(UTC)
        discharge.version += 1
        self.db.flush()
        response = self._discharge_response(discharge, correlation_id)
        self._complete(actor, "hospital.discharge.complete", idempotency_key, response, discharge.id)
        self._audit(actor, "DISCHARGE_COMPLETED", "hospital_discharge", discharge.id, scope, correlation_id, request_id, {"state_after": discharge.status, "admission_status": admission.status, "bed_released": active is not None, "version": discharge.version})
        return response

    def _scope(self, actor: NiamActor, workspace_id: str, permission: str):
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_permission(actor, scope, permission)
        return scope

    def _encounter_for_scope(self, encounter_id: str, scope):
        from app.clinical.encounters.models import CoreEncounter

        row = self.db.query(CoreEncounter).filter(CoreEncounter.id == encounter_id, CoreEncounter.organization_id == scope.organization_id, CoreEncounter.facility_id == scope.facility_id, CoreEncounter.workspace_id == scope.workspace_id).first()
        if row is None:
            raise HospitalNotFoundError("Encounter was not found", code="ENCOUNTER_NOT_FOUND")
        return row

    def _ward_for_scope(self, ward_id: str, scope):
        row = self.db.query(CoreHospitalWard).filter(CoreHospitalWard.id == ward_id, CoreHospitalWard.organization_id == scope.organization_id, CoreHospitalWard.facility_id == scope.facility_id, CoreHospitalWard.status == "ACTIVE").first()
        if row is None:
            raise HospitalNotFoundError("Ward was not found", code="WARD_NOT_FOUND")
        return row

    def _bed_for_scope(self, bed_id: str, scope):
        row = self.db.query(CoreHospitalBed).filter(CoreHospitalBed.id == bed_id, CoreHospitalBed.organization_id == scope.organization_id, CoreHospitalBed.facility_id == scope.facility_id).first()
        if row is None:
            raise HospitalNotFoundError("Bed was not found", code="BED_NOT_FOUND")
        return row

    def _bed_for_update(self, bed_id: str, scope):
        row = self.db.query(CoreHospitalBed).filter(CoreHospitalBed.id == bed_id, CoreHospitalBed.organization_id == scope.organization_id, CoreHospitalBed.facility_id == scope.facility_id).with_for_update().first()
        if row is None:
            raise HospitalNotFoundError("Bed was not found", code="BED_NOT_FOUND")
        return row

    def _admission_for_scope(self, admission_id: str, scope):
        row = self.db.query(CoreAdmission).filter(CoreAdmission.id == admission_id, CoreAdmission.organization_id == scope.organization_id, CoreAdmission.facility_id == scope.facility_id).first()
        if row is None:
            raise HospitalNotFoundError("Admission was not found", code="ADMISSION_NOT_FOUND")
        return row

    def _admission_for_update(self, admission_id: str, scope):
        row = self.db.query(CoreAdmission).filter(CoreAdmission.id == admission_id, CoreAdmission.organization_id == scope.organization_id, CoreAdmission.facility_id == scope.facility_id).with_for_update().first()
        if row is None:
            raise HospitalNotFoundError("Admission was not found", code="ADMISSION_NOT_FOUND")
        return row

    def _discharge_for_scope(self, discharge_id: str, scope):
        row = self.db.query(CoreDischarge).filter(CoreDischarge.id == discharge_id, CoreDischarge.organization_id == scope.organization_id, CoreDischarge.facility_id == scope.facility_id).first()
        if row is None:
            raise HospitalNotFoundError("Discharge was not found", code="DISCHARGE_NOT_FOUND")
        return row

    def _discharge_for_update(self, discharge_id: str, scope):
        row = self.db.query(CoreDischarge).filter(CoreDischarge.id == discharge_id, CoreDischarge.organization_id == scope.organization_id, CoreDischarge.facility_id == scope.facility_id).with_for_update().first()
        if row is None:
            raise HospitalNotFoundError("Discharge was not found", code="DISCHARGE_NOT_FOUND")
        return row

    def _move_allocation(self, transfer: CorePatientTransfer, scope, actor: NiamActor) -> None:
        admission = self._admission_for_update(transfer.admission_id, scope)
        source = self._bed_for_update(transfer.from_bed_id, scope)
        target = self._bed_for_update(transfer.to_bed_id, scope)
        if target.status not in {"AVAILABLE", "RESERVED"}:
            raise BedUnavailableError("Target bed is not available")
        active = self.db.query(CoreBedAllocation).filter(CoreBedAllocation.admission_id == admission.id, CoreBedAllocation.released_at.is_(None)).with_for_update().first()
        if active is None or active.bed_id != source.id:
            raise TransferConflictError("Source allocation is no longer active")
        target_active = self.db.query(CoreBedAllocation).filter(CoreBedAllocation.bed_id == target.id, CoreBedAllocation.released_at.is_(None)).with_for_update().first()
        if target_active is not None:
            raise BedAlreadyAllocatedError("Target bed already has an active allocation")
        active.released_at = datetime.now(UTC)
        active.version += 1
        source.status = "CLEANING"
        source.version += 1
        new_allocation = CoreBedAllocation(admission_id=admission.id, patient_person_id=admission.patient_person_id, bed_id=target.id, ward_id=target.ward_id, facility_id=scope.facility_id, organization_id=scope.organization_id, allocated_by_account_id=actor.account.id, version=1)
        self.db.add(new_allocation)
        target.status = "OCCUPIED"
        target.version += 1
        admission.ward_id = target.ward_id
        admission.version += 1
        self.db.flush()

    @staticmethod
    def _parse_numeric(value: str) -> Decimal:
        try:
            return Decimal(value)
        except (InvalidOperation, ValueError) as exc:
            raise AppointmentError("Vital value must be numeric", status_code=422, code="VITAL_VALUE_INVALID") from exc

    @staticmethod
    def _validate_vital(vital_type: str, value: Decimal, unit: str) -> None:
        ranges = {
            "temperature": (Decimal("-50"), Decimal("80"), {"C", "°C", "F", "°F"}),
            "heart_rate": (Decimal("0"), Decimal("400"), {"bpm", "beats/min"}),
            "respiratory_rate": (Decimal("0"), Decimal("200"), {"breaths/min"}),
            "blood_pressure_systolic": (Decimal("0"), Decimal("400"), {"mmHg"}),
            "blood_pressure_diastolic": (Decimal("0"), Decimal("300"), {"mmHg"}),
            "oxygen_saturation": (Decimal("0"), Decimal("100"), {"%"}),
            "weight": (Decimal("0"), Decimal("1000"), {"kg", "lb"}),
            "height": (Decimal("0"), Decimal("300"), {"cm", "in"}),
            "gcs": (Decimal("3"), Decimal("15"), {"score"}),
        }
        if vital_type not in ranges:
            return
        low, high, units = ranges[vital_type]
        if unit not in units:
            raise AppointmentError("Vital unit is not valid for this observation", status_code=422, code="VITAL_UNIT_INVALID")
        if value < low or value > high:
            raise AppointmentError("Vital value is outside the accepted physical range", status_code=422, code="VITAL_VALUE_INVALID")

    @staticmethod
    def _vital_warning(vital_type: str, value: Decimal, unit: str) -> str | None:
        if vital_type == "heart_rate" and (value < 40 or value > 180):
            return "HEART_RATE_UNUSUAL"
        if vital_type == "oxygen_saturation" and value < 90:
            return "OXYGEN_SATURATION_LOW"
        if vital_type == "temperature" and unit in {"C", "°C"} and (value < 35 or value > 40):
            return "TEMPERATURE_UNUSUAL"
        if vital_type == "gcs" and value < 8:
            return "GCS_LOW"
        return None

    def _claim(self, actor: NiamActor, operation: str, key: str, payload: dict[str, Any]):
        self.command_guard.actor_account_id = actor.account.id
        try:
            return self.command_guard.claim(operation=operation, idempotency_key=key, payload=payload)
        except ValueError as exc:
            raise AppointmentError(str(exc), status_code=400, code="IDEMPOTENCY_CONFLICT") from exc

    def _complete(self, actor: NiamActor, operation: str, key: str, response: dict[str, Any], resource_id: str) -> None:
        self.command_guard.actor_account_id = actor.account.id
        self.command_guard.complete(operation=operation, idempotency_key=key, resource_id=resource_id, response_body=response)

    @staticmethod
    def _assert_version(actual: int, expected: int) -> None:
        if expected < 1 or actual != expected:
            raise VersionConflictError("The hospital resource changed before this operation")

    def _audit(self, actor, event_type: str, target_type: str, target_id: str, scope, correlation_id: str, request_id: str | None, changes: dict[str, Any]) -> None:
        self.audit.record(AuditEventInput(event_type=event_type, category="clinical_hospital", action=event_type.lower(), actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type=target_type, target_id=target_id, decision="allow", request_id=request_id, correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="SENSITIVE", changes=changes))

    @staticmethod
    def _admission_response(row, correlation_id):
        return {"id": row.id, "admission_request_id": row.admission_request_id, "patient_person_id": row.patient_person_id, "encounter_id": row.encounter_id, "facility_id": row.facility_id, "organization_id": row.organization_id, "ward_id": row.ward_id, "admitting_provider_account_id": row.admitting_provider_account_id, "admission_type": row.admission_type, "status": row.status, "version": row.version, "requested_at": row.requested_at.isoformat(), "admitted_at": row.admitted_at.isoformat() if row.admitted_at else None, "discharged_at": row.discharged_at.isoformat() if row.discharged_at else None, "correlation_id": correlation_id}

    @staticmethod
    def _bed_response(row, correlation_id):
        return {"id": row.id, "room_id": row.room_id, "ward_id": row.ward_id, "facility_id": row.facility_id, "status": row.status, "version": row.version, "correlation_id": correlation_id}

    @staticmethod
    def _allocation_response(row, correlation_id):
        return {"id": row.id, "admission_id": row.admission_id, "patient_person_id": row.patient_person_id, "bed_id": row.bed_id, "ward_id": row.ward_id, "allocated_at": row.allocated_at.isoformat(), "released_at": row.released_at.isoformat() if row.released_at else None, "version": row.version, "correlation_id": correlation_id}

    @staticmethod
    def _task_response(row, correlation_id):
        return {"id": row.id, "admission_id": row.admission_id, "patient_person_id": row.patient_person_id, "ward_id": row.ward_id, "task_type": row.task_type, "status": row.status, "assigned_to_account_id": row.assigned_to_account_id, "version": row.version, "claimed_at": row.claimed_at.isoformat() if row.claimed_at else None, "completed_at": row.completed_at.isoformat() if row.completed_at else None, "correlation_id": correlation_id}

    @staticmethod
    def _vital_response(row, correlation_id):
        return {"id": row.id, "patient_person_id": row.patient_person_id, "encounter_id": row.encounter_id, "admission_id": row.admission_id, "vital_type": row.vital_type, "value_numeric": row.value_numeric, "unit": row.unit, "method": row.method, "source": row.source, "observed_at": row.observed_at.isoformat(), "validation_status": row.validation_status, "warning_code": row.warning_code, "version": row.version, "correlation_id": correlation_id}

    @staticmethod
    def _emar_response(row, correlation_id):
        return {"id": row.id, "administration_key": row.administration_key, "admission_id": row.admission_id, "patient_person_id": row.patient_person_id, "encounter_id": row.encounter_id, "prescription_id": row.prescription_id, "prescription_item_id": row.prescription_item_id, "medication_catalog_id": row.medication_catalog_id, "administrator_account_id": row.administrator_account_id, "dose_value": row.dose_value, "dose_unit": row.dose_unit, "route": row.route, "status": row.status, "reason": row.reason, "administered_at": row.administered_at.isoformat() if row.administered_at else None, "version": row.version, "correlation_id": correlation_id}

    @staticmethod
    def _transfer_response(row, correlation_id):
        return {"id": row.id, "transfer_request_id": row.transfer_request_id, "admission_id": row.admission_id, "patient_person_id": row.patient_person_id, "from_bed_id": row.from_bed_id, "to_bed_id": row.to_bed_id, "status": row.status, "reason": row.reason, "version": row.version, "completed_at": row.completed_at.isoformat() if row.completed_at else None, "correlation_id": correlation_id}

    @staticmethod
    def _handover_response(row, correlation_id):
        return {"id": row.id, "handover_request_id": row.handover_request_id, "admission_id": row.admission_id, "patient_person_id": row.patient_person_id, "sender_account_id": row.sender_account_id, "receiver_account_id": row.receiver_account_id, "status": row.status, "minimal_summary": row.minimal_summary, "version": row.version, "acknowledged_at": row.acknowledged_at.isoformat() if row.acknowledged_at else None, "correlation_id": correlation_id}

    @staticmethod
    def _discharge_response(row, correlation_id):
        return {"id": row.id, "discharge_request_id": row.discharge_request_id, "admission_id": row.admission_id, "patient_person_id": row.patient_person_id, "responsible_provider_account_id": row.responsible_provider_account_id, "disposition": row.disposition, "status": row.status, "medication_reconciliation_complete": bool(row.medication_reconciliation_complete), "pending_results_reviewed": bool(row.pending_results_reviewed), "follow_up_plan": row.follow_up_plan, "instructions": row.instructions, "version": row.version, "completed_at": row.completed_at.isoformat() if row.completed_at else None, "correlation_id": correlation_id}

    @staticmethod
    def _summary_response(row, correlation_id):
        return {"id": row.id, "discharge_id": row.discharge_id, "summary_version": row.summary_version, "status": row.status, "admission_reason": row.admission_reason, "diagnoses": row.diagnoses, "procedures": row.procedures, "treatment": row.treatment, "medications": row.medications, "results": row.results, "condition": row.condition, "follow_up": row.follow_up, "authored_by_account_id": row.authored_by_account_id, "signed_at": row.signed_at.isoformat() if row.signed_at else None, "signed_by_account_id": row.signed_by_account_id, "correlation_id": correlation_id}
