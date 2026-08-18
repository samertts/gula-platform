from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app._compat import UTC
from app.clinical_gateway.access_context import ClinicalAccessContext
from app.clinical_gateway.context import ClinicalGatewayBlocked
from app.nursing.enums import AssignmentType, NursingTaskType, ShiftType, TaskPriority
from app.nursing.models import NursingShift, NursingTask, PatientAssignment


class ClinicalWorkflowService:
    def __init__(self, db: Session):
        self.db = db

    def start_shift(self, *, access: ClinicalAccessContext, shift_type: str, department_id: int | None = None) -> NursingShift:
        access.require_operation("shift_start")
        try:
            shift_enum = ShiftType(shift_type)
        except ValueError as exc:
            raise ClinicalGatewayBlocked("invalid_shift_type") from exc
        now = datetime.now(UTC)
        active = (
            self.db.query(NursingShift)
            .filter(
                NursingShift.lab_id == access.legacy_lab_id,
                or_(NursingShift.nurse_id == str(access.legacy_user_id), NursingShift.clinician_user_id == str(access.legacy_user_id)),
                NursingShift.is_deleted.is_(False),
                NursingShift.start_time <= now,
                (NursingShift.end_time.is_(None) | (NursingShift.end_time > now)),
            )
            .count()
        )
        if active:
            raise ClinicalGatewayBlocked("active_shift_already_exists")
        shift = NursingShift(
            nurse_id=str(access.legacy_user_id),
            clinician_user_id=str(access.legacy_user_id),
            department_id=department_id,
            shift_type=shift_enum,
            shift_date=date.today(),
            start_time=now,
            metadata_={"workspace_id": access.workspace_id, "purpose": access.purpose},
        )
        self.db.add(shift)
        self.db.flush()
        return shift

    def end_shift(self, *, access: ClinicalAccessContext, shift_id: str) -> NursingShift:
        access.require_operation("shift_end")
        shift = (
            self.db.query(NursingShift)
            .filter(
                NursingShift.id == shift_id,
                NursingShift.lab_id == access.legacy_lab_id,
                or_(NursingShift.nurse_id == str(access.legacy_user_id), NursingShift.clinician_user_id == str(access.legacy_user_id)),
                NursingShift.is_deleted.is_(False),
                NursingShift.end_time.is_(None),
            )
            .one_or_none()
        )
        if shift is None:
            raise ClinicalGatewayBlocked("shift_scope_denied_or_already_ended")
        shift.end_time = datetime.now(UTC)
        self.db.flush()
        return shift

    def assign_patient(
        self,
        *,
        access: ClinicalAccessContext,
        shift_id: str,
        patient_id: int,
        encounter_id: str | None = None,
        assignment_type: str = "primary",
    ) -> PatientAssignment:
        shift = self._active_shift(access=access, shift_id=shift_id)
        scoped = access.__class__(**{**access.__dict__, "shift_id": str(shift.id), "patient_scope": f"patient:{patient_id}"})
        scoped.require_operation("patient_assign")
        try:
            assignment_enum = AssignmentType(assignment_type)
        except ValueError as exc:
            raise ClinicalGatewayBlocked("invalid_assignment_type") from exc
        existing = (
            self.db.query(PatientAssignment)
            .filter(
                PatientAssignment.lab_id == access.legacy_lab_id,
                PatientAssignment.patient_id == patient_id,
                PatientAssignment.is_active.is_(True),
                PatientAssignment.is_deleted.is_(False),
                or_(PatientAssignment.nurse_id == str(access.legacy_user_id), PatientAssignment.clinician_user_id == str(access.legacy_user_id)),
            )
            .count()
        )
        if existing:
            raise ClinicalGatewayBlocked("patient_assignment_already_exists")
        assignment = PatientAssignment(
            nurse_id=str(access.legacy_user_id),
            clinician_user_id=str(access.legacy_user_id),
            patient_id=patient_id,
            encounter_id=encounter_id,
            department_id=shift.department_id,
            assignment_type=assignment_enum,
            start_date=datetime.now(UTC),
            is_active=True,
        )
        self.db.add(assignment)
        self.db.flush()
        return assignment

    def create_task(
        self,
        *,
        access: ClinicalAccessContext,
        patient_id: int,
        task_type: str,
        description: str,
        priority: str = "medium",
        encounter_id: str | None = None,
        due_time: datetime | None = None,
    ) -> NursingTask:
        scoped = ClinicalAccessContext.from_gateway_for_patient(
            self.db,
            self._gateway_context(access),
            patient_id=patient_id,
            purpose=access.purpose,
            permissions=frozenset({"task:create"}),
            correlation_id=access.correlation_id,
        )
        scoped.require_operation("task_create")
        try:
            task_enum = NursingTaskType(task_type)
            priority_enum = TaskPriority(priority)
        except ValueError as exc:
            raise ClinicalGatewayBlocked("invalid_task_type_or_priority") from exc
        task = NursingTask(
            patient_id=patient_id,
            encounter_id=encounter_id,
            assigned_by=str(access.legacy_user_id),
            assigned_to=str(access.legacy_user_id),
            task_type=task_enum,
            description=description.strip(),
            priority=priority_enum,
            status="pending",
            due_time=due_time,
        )
        self.db.add(task)
        self.db.flush()
        return task

    def complete_task(self, *, access: ClinicalAccessContext, task_id: str, notes: str | None = None) -> NursingTask:
        task = (
            self.db.query(NursingTask)
            .filter(
                NursingTask.id == task_id,
                NursingTask.lab_id == access.legacy_lab_id,
                NursingTask.assigned_to == str(access.legacy_user_id),
                NursingTask.is_deleted.is_(False),
            )
            .one_or_none()
        )
        if task is None:
            raise ClinicalGatewayBlocked("task_scope_denied")
        scoped = ClinicalAccessContext.from_gateway_for_patient(
            self.db,
            self._gateway_context(access),
            patient_id=task.patient_id,
            purpose=access.purpose,
            permissions=frozenset({"update"}),
            correlation_id=access.correlation_id,
        )
        scoped.require_operation("update")
        if task.status in {"completed", "cancelled", "voided"}:
            raise ClinicalGatewayBlocked("task_already_terminal")
        task.status = "completed"
        task.completed_at = datetime.now(UTC)
        task.completed_by = str(access.legacy_user_id)
        task.notes = notes
        self.db.flush()
        return task

    def _active_shift(self, *, access: ClinicalAccessContext, shift_id: str) -> NursingShift:
        now = datetime.now(UTC)
        shift = (
            self.db.query(NursingShift)
            .filter(
                NursingShift.id == shift_id,
                NursingShift.lab_id == access.legacy_lab_id,
                or_(NursingShift.nurse_id == str(access.legacy_user_id), NursingShift.clinician_user_id == str(access.legacy_user_id)),
                NursingShift.is_deleted.is_(False),
                NursingShift.start_time <= now,
                (NursingShift.end_time.is_(None) | (NursingShift.end_time > now)),
            )
            .one_or_none()
        )
        if shift is None:
            raise ClinicalGatewayBlocked("active_shift_scope_denied")
        return shift

    @staticmethod
    def _gateway_context(access: ClinicalAccessContext):
        # Command routes pass a gateway context in ``access`` metadata only in
        # future adapters. This explicit stop prevents reconstructing authority
        # from client values in the meantime.
        gateway = getattr(access, "gateway_context", None)
        if gateway is None:
            raise ClinicalGatewayBlocked("gateway_context_required")
        return gateway

    @staticmethod
    def to_safe_dict(resource: Any) -> dict[str, Any]:
        return {
            "id": resource.id,
            "patient_id": getattr(resource, "patient_id", None),
            "shift_id": getattr(resource, "shift_id", None),
            "status": getattr(resource, "status", None),
            "start_time": getattr(resource, "start_time", None),
            "end_time": getattr(resource, "end_time", None),
            "completed_at": getattr(resource, "completed_at", None),
            "task_type": getattr(getattr(resource, "task_type", None), "value", getattr(resource, "task_type", None)),
            "priority": getattr(getattr(resource, "priority", None), "value", getattr(resource, "priority", None)),
            "description": getattr(resource, "description", None),
        }
