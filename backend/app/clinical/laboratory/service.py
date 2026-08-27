from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import Any

from app.clinical.appointments.service import (
    AppointmentError,
    VersionConflictError,
)
from app.clinical.command_guard import CanonicalClinicalCommandGuard
from app.contracts.clinical_core import require_transition
from app.identity.api.workspaces import NiamActor
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService

from .authorization import LaboratoryAuthorizationService
from .models import (
    CoreLabOrder,
    CoreLabOrderItem,
    CoreSpecimen,
    CoreSpecimenEvent,
)


class LabOrderNotFoundError(AppointmentError):
    code = "LAB_ORDER_NOT_FOUND"
    status_code = 404


class LabOrderStateConflictError(AppointmentError):
    code = "LAB_ORDER_STATE_CONFLICT"
    status_code = 409


class SpecimenNotFoundError(AppointmentError):
    code = "SPECIMEN_NOT_FOUND"
    status_code = 404


class SpecimenStateConflictError(AppointmentError):
    code = "SPECIMEN_STATE_CONFLICT"
    status_code = 409


class DuplicateSpecimenError(AppointmentError):
    code = "SPECIMEN_ALREADY_EXISTS"
    status_code = 409


class LaboratoryService:
    """Canonical Laboratory Core; no analyzer or external notification side effects."""

    def __init__(self, db):
        self.db = db
        self.authz = LaboratoryAuthorizationService(db)
        self.audit = SyncCanonicalAuditService(db)
        self.command_guard = CanonicalClinicalCommandGuard(db, actor_account_id=None)

    def create_order(
        self,
        actor: NiamActor,
        *,
        encounter_id: str,
        workspace_id: str,
        priority: str,
        clinical_indication: str | None,
        items: list[dict[str, str]],
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        encounter = self.authz.encounter_for_scope(encounter_id, scope)
        appointment = self.authz.appointment_for_encounter(encounter, scope)
        self.authz.require_ordering_provider(actor, scope, appointment)
        if encounter.status not in {"IN_PROGRESS", "COMPLETED"}:
            raise LabOrderStateConflictError("Lab orders require an active or completed encounter")
        if len({item["test_code"] for item in items}) != len(items):
            raise AppointmentError("Duplicate test codes are not allowed", status_code=422, code="VALIDATION_ERROR")
        payload = {
            "encounter_id": encounter.id,
            "workspace_id": scope.workspace_id,
            "priority": priority,
            "clinical_indication": clinical_indication,
            "items": items,
        }
        cached = self._claim(actor, "lab.order.create", idempotency_key, payload)
        if cached is not None:
            return cached
        order = CoreLabOrder(
            encounter_id=encounter.id,
            patient_person_id=encounter.patient_person_id,
            ordering_provider_account_id=actor.account.id,
            laboratory_id=scope.facility_id,
            organization_id=scope.organization_id,
            facility_id=scope.facility_id,
            workspace_id=scope.workspace_id,
            status="DRAFT",
            priority=priority,
            clinical_indication=clinical_indication.strip() if clinical_indication else None,
            version=1,
        )
        self.db.add(order)
        self.db.flush()
        for item in items:
            self.db.add(CoreLabOrderItem(
                lab_order_id=order.id,
                test_code=item["test_code"],
                test_name=item["test_name"],
                specimen_type=item["specimen_type"],
                status="ORDERED",
                version=1,
            ))
        self.db.flush()
        self._transition_order(order, "PLACED")
        response = self._order_response(order, correlation_id)
        self._complete(actor, "lab.order.create", idempotency_key, response, order.id)
        self._audit(actor, "LAB_ORDER_CREATED", "lab_order", order.id, scope, correlation_id, request_id, {"state_before": "DRAFT", "state_after": "PLACED", "version_after": order.version, "item_count": len(items)})
        return response

    def get_order(self, actor: NiamActor, *, order_id: str, workspace_id: str, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        order = self._order_for_scope(order_id, scope)
        encounter = self.authz.encounter_for_scope(order.encounter_id, scope)
        appointment = self.authz.appointment_for_encounter(encounter, scope)
        self.authz.require_order_read(actor, scope, appointment)
        return self._order_response(order, correlation_id, include_items=True)

    def verify_order(self, actor: NiamActor, *, order_id: str, workspace_id: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        order = self._order_for_update(order_id, scope)
        self.authz.require_permission(actor, scope, "clinical.lab_order.verify")
        self._assert_version(order.version, expected_version)
        payload = {"resource_id": order.id, "workspace_id": scope.workspace_id, "expected_version": expected_version}
        cached = self._claim(actor, "lab.order.verify", idempotency_key, payload)
        if cached is not None:
            return cached
        if order.status != "PLACED":
            raise LabOrderStateConflictError("Only a placed order may be accepted")
        before = order.status
        self._transition_order(order, "ACCEPTED")
        order.verified_by_account_id = actor.account.id
        order.verified_at = datetime.now(UTC)
        self.db.flush()
        response = self._order_response(order, correlation_id)
        self._complete(actor, "lab.order.verify", idempotency_key, response, order.id)
        self._audit(actor, "LAB_ORDER_VERIFIED", "lab_order", order.id, scope, correlation_id, request_id, {"state_before": before, "state_after": order.status, "version_before": expected_version, "version_after": order.version})
        return response

    def create_specimen(self, actor: NiamActor, *, order_item_id: str, workspace_id: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        item = self.db.query(CoreLabOrderItem).filter(CoreLabOrderItem.id == order_item_id).first()
        if item is None:
            raise LabOrderNotFoundError("Lab order item not found")
        order = self._order_for_scope(item.lab_order_id, scope)
        self.authz.require_specimen_operator(actor, scope)
        if order.status not in {"PLACED", "VERIFIED", "ACCEPTED"}:
            raise LabOrderStateConflictError("The order is not eligible for specimen creation")
        payload = {"order_item_id": item.id, "workspace_id": scope.workspace_id}
        cached = self._claim(actor, "specimen.create", idempotency_key, payload)
        if cached is not None:
            return cached
        existing = self.db.query(CoreSpecimen).filter(CoreSpecimen.order_item_id == item.id).with_for_update().first()
        if existing is not None:
            raise DuplicateSpecimenError("A specimen already exists for this order item")
        specimen = CoreSpecimen(
            lab_order_id=order.id,
            order_item_id=item.id,
            encounter_id=order.encounter_id,
            patient_person_id=order.patient_person_id,
            laboratory_id=order.laboratory_id,
            organization_id=scope.organization_id,
            facility_id=scope.facility_id,
            workspace_id=scope.workspace_id,
            specimen_type=item.specimen_type,
            accession_number=self._accession(),
            barcode=self._barcode(),
            status="ORDERED",
            version=1,
        )
        self.db.add(specimen)
        self.db.flush()
        self._event(actor, specimen, "SPECIMEN_CREATED", "ORDERED", "ORDERED", scope, correlation_id, request_id)
        response = self._specimen_response(specimen, correlation_id)
        self._complete(actor, "specimen.create", idempotency_key, response, specimen.id)
        self._audit(actor, "SPECIMEN_CREATED", "specimen", specimen.id, scope, correlation_id, request_id, {"state_before": None, "state_after": "ORDERED", "version_after": specimen.version})
        return response

    def transition_specimen(self, actor: NiamActor, *, specimen_id: str, workspace_id: str, target: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None, reason: str | None = None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        specimen = self._specimen_for_update(specimen_id, scope)
        self.authz.require_specimen_operator(actor, scope)
        self._assert_version(specimen.version, expected_version)
        operation = f"specimen.{target.lower()}"
        payload = {"resource_id": specimen.id, "workspace_id": scope.workspace_id, "expected_version": expected_version, "reason": reason}
        cached = self._claim(actor, operation, idempotency_key, payload)
        if cached is not None:
            return cached
        before = specimen.status
        if target == "REJECTED":
            if not reason or not reason.strip():
                raise AppointmentError("A specimen rejection reason is required", status_code=422, code="VALIDATION_ERROR")
            if before in {"VALIDATED", "REJECTED"}:
                raise SpecimenStateConflictError("The specimen cannot be rejected in its current state")
        else:
            try:
                require_transition("specimen", before, target)
            except ValueError as exc:
                raise SpecimenStateConflictError("The specimen transition is not allowed") from exc
        specimen.status = target
        specimen.version += 1
        now = datetime.now(UTC)
        if target == "COLLECTED":
            specimen.collector_account_id = actor.account.id
            specimen.collected_at = now
        elif target == "RECEIVED":
            specimen.receiver_account_id = actor.account.id
            specimen.received_at = now
        elif target == "PROCESSING":
            specimen.processing_started_at = now
        elif target == "VALIDATED":
            specimen.validated_at = now
        elif target == "REJECTED":
            specimen.rejection_reason = reason.strip() if reason else None
        self.db.flush()
        self._event(actor, specimen, f"SPECIMEN_{target}", before, target, scope, correlation_id, request_id, {"reason": reason} if reason else None)
        response = self._specimen_response(specimen, correlation_id)
        self._complete(actor, operation, idempotency_key, response, specimen.id)
        self._audit(actor, f"SPECIMEN_{target}", "specimen", specimen.id, scope, correlation_id, request_id, {"state_before": before, "state_after": target, "version_before": expected_version, "version_after": specimen.version})
        return response

    def list_worklist(self, actor: NiamActor, *, workspace_id: str, status: str | None, priority: str | None, limit: int, offset: int, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_specimen_operator(actor, scope)
        query = self.db.query(CoreSpecimen).filter(
            CoreSpecimen.organization_id == scope.organization_id,
            CoreSpecimen.facility_id == scope.facility_id,
            CoreSpecimen.workspace_id == scope.workspace_id,
        )
        if status:
            query = query.filter(CoreSpecimen.status == status)
        if priority:
            query = query.join(CoreLabOrder, CoreLabOrder.id == CoreSpecimen.lab_order_id).filter(CoreLabOrder.priority == priority)
        total = query.count()
        rows = query.order_by(CoreSpecimen.created_at.desc(), CoreSpecimen.id.desc()).offset(offset).limit(limit).all()
        return {"items": [self._specimen_response(item, correlation_id) for item in rows], "limit": limit, "offset": offset, "total": total, "correlation_id": correlation_id}

    def _order_for_scope(self, order_id: str, scope):
        order = self.db.query(CoreLabOrder).filter(CoreLabOrder.id == order_id, CoreLabOrder.organization_id == scope.organization_id, CoreLabOrder.facility_id == scope.facility_id, CoreLabOrder.workspace_id == scope.workspace_id).first()
        if order is None:
            raise LabOrderNotFoundError("Lab order not found")
        return order

    def _order_for_update(self, order_id: str, scope):
        order = self.db.query(CoreLabOrder).filter(CoreLabOrder.id == order_id, CoreLabOrder.organization_id == scope.organization_id, CoreLabOrder.facility_id == scope.facility_id, CoreLabOrder.workspace_id == scope.workspace_id).with_for_update().first()
        if order is None:
            raise LabOrderNotFoundError("Lab order not found")
        return order

    def _specimen_for_update(self, specimen_id: str, scope):
        specimen = self.db.query(CoreSpecimen).filter(CoreSpecimen.id == specimen_id, CoreSpecimen.organization_id == scope.organization_id, CoreSpecimen.facility_id == scope.facility_id, CoreSpecimen.workspace_id == scope.workspace_id).with_for_update().first()
        if specimen is None:
            raise SpecimenNotFoundError("Specimen not found")
        return specimen

    @staticmethod
    def _assert_version(actual: int, expected: int) -> None:
        if expected < 1 or actual != expected:
            raise VersionConflictError("The resource changed before this operation")

    @staticmethod
    def _transition_order(order: CoreLabOrder, target: str) -> None:
        try:
            require_transition("lab-order", order.status, target)
        except ValueError as exc:
            raise LabOrderStateConflictError("The lab order transition is not allowed") from exc
        order.status = target
        order.version += 1

    def _event(self, actor, specimen, event_type, before, after, scope, correlation_id, request_id, metadata=None):
        self.db.add(CoreSpecimenEvent(
            specimen_id=specimen.id,
            event_type=event_type,
            previous_state=before,
            new_state=after,
            actor_account_id=actor.account.id,
            laboratory_id=specimen.laboratory_id,
            organization_id=scope.organization_id,
            facility_id=scope.facility_id,
            workspace_id=scope.workspace_id,
            correlation_id=correlation_id,
            event_metadata=metadata,
            occurred_at=datetime.now(UTC),
        ))
        self.db.flush()

    def _claim(self, actor, operation: str, key: str, payload: dict[str, Any]):
        self.command_guard.actor_account_id = actor.account.id
        try:
            return self.command_guard.claim(operation=operation, idempotency_key=key, payload=payload)
        except ValueError as exc:
            raise AppointmentError(str(exc), status_code=400, code="VALIDATION_ERROR") from exc

    def _complete(self, actor, operation, key, response, resource_id):
        self.command_guard.actor_account_id = actor.account.id
        self.command_guard.complete(operation=operation, idempotency_key=key, resource_id=resource_id, response_body=response)

    def _audit(self, actor, event_type, target_type, target_id, scope, correlation_id, request_id, changes):
        self.audit.record(AuditEventInput(event_type=event_type, category="clinical_laboratory", action=event_type.lower(), actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type=target_type, target_id=target_id, decision="allow", request_id=request_id, correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="SENSITIVE", changes=changes))

    def _order_response(self, order, correlation_id, include_items=False):
        body = {"id": order.id, "encounter_id": order.encounter_id, "patient_person_id": order.patient_person_id, "ordering_provider_account_id": order.ordering_provider_account_id, "laboratory_id": order.laboratory_id, "organization_id": order.organization_id, "facility_id": order.facility_id, "workspace_id": order.workspace_id, "status": order.status, "priority": order.priority, "version": order.version, "item_count": self.db.query(CoreLabOrderItem).filter(CoreLabOrderItem.lab_order_id == order.id).count(), "created_at": order.created_at.isoformat() if order.created_at else None, "correlation_id": correlation_id}
        if include_items:
            body["items"] = [{"id": item.id, "test_code": item.test_code, "test_name": item.test_name, "specimen_type": item.specimen_type, "status": item.status, "version": item.version} for item in self.db.query(CoreLabOrderItem).filter(CoreLabOrderItem.lab_order_id == order.id).order_by(CoreLabOrderItem.created_at.asc(), CoreLabOrderItem.id.asc()).all()]
        return body

    @staticmethod
    def _specimen_response(specimen, correlation_id):
        return {"id": specimen.id, "lab_order_id": specimen.lab_order_id, "order_item_id": specimen.order_item_id, "patient_person_id": specimen.patient_person_id, "specimen_type": specimen.specimen_type, "accession_number": specimen.accession_number, "barcode": specimen.barcode, "status": specimen.status, "version": specimen.version, "correlation_id": correlation_id}

    @staticmethod
    def _accession() -> str:
        return f"ACC-{datetime.now(UTC):%Y%m%d}-{secrets.token_hex(5).upper()}"

    @staticmethod
    def _barcode() -> str:
        return f"GULA-{secrets.token_hex(8).upper()}"
