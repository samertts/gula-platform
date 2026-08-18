"""Central server-derived clinical access context.

This is intentionally derived from the reviewed ClinicalGatewayContext. Client
fields are never accepted as authority. Read compatibility can use a scoped
context; clinical writes/signatures/approvals require an active shift,
assignment, and task until those durable models are available.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app._compat import UTC
from app.clinical_gateway.context import ClinicalGatewayContext, ClinicalGatewayBlocked


WRITE_OPERATIONS = frozenset({"create", "update", "delete", "sign", "approve", "publish", "validate"})
WORKFLOW_BOOTSTRAP_OPERATIONS = frozenset({"shift_start", "shift_end", "patient_assign", "task_create"})


@dataclass(frozen=True)
class ClinicalAccessContext:
    account_id: int
    session_id: int
    legacy_user_id: int
    legacy_lab_id: int
    organization_id: str
    facility_id: str
    workspace_id: str
    department_id: str | None
    operational_organization_id: int
    operational_facility_id: int
    tenant_id: int
    shift_id: str | None
    assignment_id: str | None
    task_id: str | None
    patient_scope: str
    purpose: str
    permissions: frozenset[str]
    issued_at: datetime
    expires_at: datetime | None
    correlation_id: UUID
    gateway_context: ClinicalGatewayContext | None = None

    @classmethod
    def from_gateway(
        cls,
        context: ClinicalGatewayContext,
        *,
        purpose: str,
        permissions: frozenset[str] = frozenset(),
        correlation_id: UUID | None = None,
    ) -> "ClinicalAccessContext":
        purpose_value = purpose.strip()
        if not purpose_value:
            raise ClinicalGatewayBlocked("missing_purpose")
        now = datetime.now(UTC)
        return cls(
            account_id=int(context.actor.account.id),
            session_id=int(context.actor.session.id),
            legacy_user_id=int(context.legacy_user.id),
            legacy_lab_id=int(context.legacy_user.lab_id),
            organization_id=str(context.workspace.organization_id),
            facility_id=str(context.workspace.facility_id),
            workspace_id=str(context.workspace.id),
            department_id=(str(context.workspace.department_id) if context.workspace.department_id else None),
            operational_organization_id=int(context.scope.operational_organization_id),
            operational_facility_id=int(context.scope.operational_facility_id),
            tenant_id=int(context.scope.tenant_id),
            shift_id=None,
            assignment_id=None,
            task_id=None,
            patient_scope="workspace_read",
            purpose=purpose_value,
            permissions=frozenset(permissions),
            issued_at=now,
            expires_at=None,
            correlation_id=correlation_id or uuid4(),
            gateway_context=context,
        )

    @classmethod
    def from_gateway_for_patient(
        cls,
        db: Session,
        context: ClinicalGatewayContext,
        *,
        patient_id: int,
        purpose: str,
        permissions: frozenset[str] = frozenset(),
        correlation_id: UUID | None = None,
        require_task: bool = True,
    ) -> "ClinicalAccessContext":
        """Derive patient/shift/task proof from server-side nursing workflow rows."""
        if patient_id <= 0:
            raise ClinicalGatewayBlocked("invalid_patient_scope")
        base = cls.from_gateway(
            context,
            purpose=purpose,
            permissions=permissions,
            correlation_id=correlation_id,
        )
        try:
            from app.nursing.models import NursingShift, NursingTask, PatientAssignment

            now = datetime.now(UTC)
            active_shifts = (
                db.query(NursingShift)
                .filter(
                    NursingShift.lab_id == context.legacy_user.lab_id,
                    or_(NursingShift.nurse_id == str(context.legacy_user.id), NursingShift.clinician_user_id == str(context.legacy_user.id)),
                    NursingShift.is_deleted.is_(False),
                    NursingShift.start_time <= now,
                    (NursingShift.end_time.is_(None) | (NursingShift.end_time > now)),
                )
                .all()
            )
            assignments = (
                db.query(PatientAssignment)
                .filter(
                    PatientAssignment.lab_id == context.legacy_user.lab_id,
                    or_(PatientAssignment.nurse_id == str(context.legacy_user.id), PatientAssignment.clinician_user_id == str(context.legacy_user.id)),
                    PatientAssignment.patient_id == patient_id,
                    PatientAssignment.is_active.is_(True),
                    PatientAssignment.is_deleted.is_(False),
                    PatientAssignment.start_date <= now,
                    (PatientAssignment.end_date.is_(None) | (PatientAssignment.end_date > now)),
                )
                .all()
            )
            tasks = (
                db.query(NursingTask)
                .filter(
                    NursingTask.lab_id == context.legacy_user.lab_id,
                    NursingTask.assigned_to == str(context.legacy_user.id),
                    NursingTask.patient_id == patient_id,
                    NursingTask.is_deleted.is_(False),
                    NursingTask.status.notin_(("completed", "cancelled", "voided")),
                )
                .all()
            ) if require_task else []
        except Exception as exc:
            raise ClinicalGatewayBlocked("workflow_context_unavailable") from exc
        if len(active_shifts) != 1:
            raise ClinicalGatewayBlocked("active_shift_missing_or_ambiguous")
        if len(assignments) != 1:
            raise ClinicalGatewayBlocked("patient_assignment_missing_or_ambiguous")
        if require_task and len(tasks) != 1:
            raise ClinicalGatewayBlocked("clinical_task_missing_or_ambiguous")
        return replace(
            base,
            shift_id=str(active_shifts[0].id),
            assignment_id=str(assignments[0].id),
            task_id=str(tasks[0].id),
            patient_scope=f"patient:{patient_id}",
        )

    def require_operation(self, operation: str) -> None:
        """Fail closed for writes until shift/assignment/task are durable."""
        if operation not in WRITE_OPERATIONS and operation not in WORKFLOW_BOOTSTRAP_OPERATIONS:
            raise ClinicalGatewayBlocked("unknown_clinical_operation")
        if operation == "shift_start":
            if "shift:start" not in self.permissions:
                raise ClinicalGatewayBlocked("clinical_permission_required")
            return
        if operation == "shift_end":
            if "shift:end" not in self.permissions:
                raise ClinicalGatewayBlocked("clinical_permission_required")
            return
        if operation == "patient_assign":
            if "patient:assign" not in self.permissions:
                raise ClinicalGatewayBlocked("clinical_permission_required")
            if not self.shift_id or self.patient_scope == "workspace_read":
                raise ClinicalGatewayBlocked("shift_and_patient_scope_required")
            return
        if operation == "task_create":
            if "task:create" not in self.permissions:
                raise ClinicalGatewayBlocked("clinical_permission_required")
            if not (self.shift_id and self.assignment_id) or self.patient_scope == "workspace_read":
                raise ClinicalGatewayBlocked("shift_assignment_and_patient_scope_required")
            return
        if operation in WRITE_OPERATIONS and not (self.shift_id and self.assignment_id and self.task_id):
            raise ClinicalGatewayBlocked("clinical_shift_assignment_task_required")
        if operation in WRITE_OPERATIONS and self.patient_scope == "workspace_read":
            raise ClinicalGatewayBlocked("patient_scope_required")
        if operation in WRITE_OPERATIONS and operation not in self.permissions:
            raise ClinicalGatewayBlocked("clinical_permission_required")

    def audit_fields(self, *, resource_id: str | None = None, action: str | None = None) -> dict[str, object]:
        """Return safe audit context; never includes national ID or credentials."""
        return {
            "account_id": self.account_id,
            "session_id": self.session_id,
            "legacy_user_id": self.legacy_user_id,
            "legacy_lab_id": self.legacy_lab_id,
            "organization_id": self.organization_id,
            "facility_id": self.facility_id,
            "workspace_id": self.workspace_id,
            "department_id": self.department_id,
            "tenant_id": self.tenant_id,
            "shift_id": self.shift_id,
            "assignment_id": self.assignment_id,
            "task_id": self.task_id,
            "patient_scope": self.patient_scope,
            "purpose": self.purpose,
            "resource_id": resource_id,
            "action": action,
            "correlation_id": str(self.correlation_id),
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
