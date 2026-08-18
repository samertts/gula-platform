from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.clinical_gateway.access_context import ClinicalAccessContext
from app.clinical_gateway.context import ClinicalGatewayBlocked
from app.models.lab_order import CLINICAL_ORDER_STATUSES, LabOrder


_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "DRAFT": frozenset({"PLACED", "CANCELLED"}),
    "PLACED": frozenset({"ACCEPTED", "CANCELLED", "REJECTED", "EXPIRED"}),
    "ACCEPTED": frozenset({"IN_PROGRESS", "CANCELLED", "REJECTED"}),
    "IN_PROGRESS": frozenset({"COMPLETED", "FAILED", "CANCELLED"}),
    "COMPLETED": frozenset(),
    "CANCELLED": frozenset(),
    "REJECTED": frozenset(),
    "FAILED": frozenset(),
    "EXPIRED": frozenset(),
}


class ClinicalOrderService:
    """Durable clinical order commands using the existing lab_orders table."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        access: ClinicalAccessContext,
        patient_id: int,
        encounter_id: str | None,
        service: str,
        priority: str = "routine",
        clinical_indication: str | None = None,
        client_prescriber_id: str | None = None,
    ) -> LabOrder:
        access.require_operation("create")
        if not patient_id or not service.strip():
            raise ClinicalGatewayBlocked("invalid_order_input")
        if client_prescriber_id is not None and client_prescriber_id != str(access.legacy_user_id):
            raise ClinicalGatewayBlocked("prescriber_mismatch")
        order = LabOrder(
            patient_id=patient_id,
            lab_id=access.legacy_lab_id,
            doctor_user_id=access.legacy_user_id,
            doctor_name=None,
            clinical_status="DRAFT",
            encounter_id=encounter_id,
            ordering_practitioner_id=str(access.legacy_user_id),
            ordering_account_id=access.account_id,
            organization_id=access.organization_id,
            facility_id=access.facility_id,
            department_id=access.department_id,
            workspace_id=access.workspace_id,
            tenant_id=access.tenant_id,
            service=service.strip(),
            priority=priority,
            clinical_indication=clinical_indication,
            correlation_id=str(access.correlation_id),
            status="pending",
        )
        self.db.add(order)
        self.db.flush()
        return order

    def get_scoped(self, *, access: ClinicalAccessContext, order_id: int) -> LabOrder:
        query = self.db.query(LabOrder).filter(
            LabOrder.id == order_id,
            LabOrder.lab_id == access.legacy_lab_id,
            LabOrder.tenant_id == access.tenant_id,
            LabOrder.organization_id == access.organization_id,
            LabOrder.facility_id == access.facility_id,
            LabOrder.workspace_id == access.workspace_id,
        )
        order = query.one_or_none()
        if order is None:
            raise ClinicalGatewayBlocked("order_scope_denied")
        return order

    def transition(
        self,
        *,
        access: ClinicalAccessContext,
        order_id: int,
        expected_version: int,
        new_status: str,
        reason: str | None = None,
    ) -> LabOrder:
        access.require_operation("update")
        if new_status not in CLINICAL_ORDER_STATUSES:
            raise ClinicalGatewayBlocked("invalid_order_status")
        order = self.get_scoped(access=access, order_id=order_id)
        current = order.clinical_status or "DRAFT"
        if order.version != expected_version:
            raise ClinicalGatewayBlocked("order_version_conflict")
        if new_status not in _ALLOWED_TRANSITIONS.get(current, frozenset()):
            raise ClinicalGatewayBlocked("invalid_order_transition")
        if current == "COMPLETED" and new_status != "COMPLETED":
            raise ClinicalGatewayBlocked("completed_order_immutable")
        order.clinical_status = new_status
        order.version = expected_version + 1
        if new_status == "COMPLETED":
            order.status = "completed"
        elif new_status == "CANCELLED":
            order.status = "cancelled"
        self.db.flush()
        return order

    @staticmethod
    def to_safe_dict(order: LabOrder) -> dict[str, Any]:
        return {
            "id": order.id,
            "patient_id": order.patient_id,
            "encounter_id": order.encounter_id,
            "service": order.service,
            "priority": order.priority,
            "clinical_status": order.clinical_status,
            "status": order.status,
            "version": order.version,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "correlation_id": order.correlation_id,
        }
