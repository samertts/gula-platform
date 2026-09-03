from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.clinical.appointments.authorization import (
    AppointmentAuthorizationError,
    AppointmentAuthorizationService,
    AppointmentScope,
)
from app.clinical.appointments.models import (
    CoreAppointment,
    CoreAppointmentIdempotencyReceipt,
    CoreAppointmentSlot,
)
from app.contracts.clinical_core import require_transition
from app.domain.exceptions import DomainError
from app.identity.api.workspaces import NiamActor
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService

logger = logging.getLogger("gula.clinical.appointments")


class AppointmentError(DomainError):
    code = "INTERNAL_ERROR"
    status_code = 500

    def __init__(
        self,
        message: str = "Appointment operation failed",
        *,
        status_code: int | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.details = details or {}


class AppointmentNotFoundError(AppointmentError):
    code = "NOT_FOUND"
    status_code = 404


class AppointmentConflictError(AppointmentError):
    code = "CONFLICT"
    status_code = 409


class SlotUnavailableError(AppointmentConflictError):
    code = "SLOT_UNAVAILABLE"


class VersionConflictError(AppointmentConflictError):
    code = "VERSION_CONFLICT"


class IdempotencyConflictError(AppointmentConflictError):
    code = "IDEMPOTENCY_CONFLICT"


class ValidationError(AppointmentError):
    code = "VALIDATION_ERROR"
    status_code = 400


class PreconditionRequiredError(AppointmentError):
    code = "PRECONDITION_REQUIRED"
    status_code = 428


@dataclass(frozen=True)
class IdempotencyClaim:
    receipt: CoreAppointmentIdempotencyReceipt
    replay: dict[str, Any] | None = None


class CoreAppointmentService:
    """Production persistence boundary for the first canonical appointment slice."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.authz = AppointmentAuthorizationService(db)
        self.audit = SyncCanonicalAuditService(db)

    def create_slot(
        self,
        actor: NiamActor,
        *,
        workspace_id: str,
        provider_account_id: str,
        service_code: str,
        starts_at: datetime,
        ends_at: datetime,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_permission(actor, scope, "appointment.slot.manage")
        self.authz.require_provider_in_scope(provider_account_id, scope)

        claim = self._claim(
            actor,
            operation="appointment.slot.create",
            idempotency_key=idempotency_key,
            payload={
                "workspace_id": scope.workspace_id,
                "provider_account_id": provider_account_id,
                "service_code": service_code,
                "starts_at": starts_at.isoformat(),
                "ends_at": ends_at.isoformat(),
            },
        )
        if claim.replay is not None:
            return claim.replay

        slot = CoreAppointmentSlot(
            organization_id=scope.organization_id,
            facility_id=scope.facility_id,
            workspace_id=scope.workspace_id,
            provider_account_id=provider_account_id,
            service_code=service_code,
            starts_at=starts_at,
            ends_at=ends_at,
            status="AVAILABLE",
            version=1,
        )
        self.db.add(slot)
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise AppointmentConflictError("The provider already has a slot in this time window") from exc

        response = self._slot_response(slot)
        claim.receipt.status = "COMPLETED"
        claim.receipt.resource_id = slot.id
        claim.receipt.response_body = response
        claim.receipt.completed_at = datetime.now(UTC)
        self.db.flush()
        self._audit(
            actor,
            event_type="APPOINTMENT_SLOT_CREATED",
            action="appointment.slot.create",
            target_id=slot.id,
            scope=scope,
            correlation_id=correlation_id,
            request_id=request_id,
            changes={"state_before": None, "state_after": "AVAILABLE", "version_after": slot.version},
            target_type="appointment_slot",
        )
        return response

    def list_slots(
        self,
        actor: NiamActor,
        *,
        workspace_id: str,
        starts_at: datetime | None,
        ends_at: datetime | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        query = self.db.query(CoreAppointmentSlot).filter(
            CoreAppointmentSlot.organization_id == scope.organization_id,
            CoreAppointmentSlot.facility_id == scope.facility_id,
            CoreAppointmentSlot.workspace_id == scope.workspace_id,
            CoreAppointmentSlot.status == "AVAILABLE",
            CoreAppointmentSlot.is_active.is_(True),
        )
        if starts_at is not None:
            query = query.filter(CoreAppointmentSlot.starts_at >= starts_at)
        if ends_at is not None:
            query = query.filter(CoreAppointmentSlot.ends_at <= ends_at)
        total = query.count()
        slots = query.order_by(CoreAppointmentSlot.starts_at.asc()).offset(offset).limit(limit).all()
        return {
            "items": [self._slot_response(slot) for slot in slots],
            "limit": limit,
            "offset": offset,
            "total": total,
        }

    def request_appointment(
        self,
        actor: NiamActor,
        *,
        workspace_id: str,
        patient_person_id: str,
        slot_id: str,
        purpose: str,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_permission(actor, scope, "appointment.request")
        self.authz.require_self_patient(scope, patient_person_id)

        slot = (
            self.db.query(CoreAppointmentSlot)
            .filter(
                CoreAppointmentSlot.id == slot_id,
                CoreAppointmentSlot.organization_id == scope.organization_id,
                CoreAppointmentSlot.facility_id == scope.facility_id,
                CoreAppointmentSlot.workspace_id == scope.workspace_id,
                CoreAppointmentSlot.is_active.is_(True),
            )
            .with_for_update()
            .first()
        )
        if slot is None:
            raise AppointmentNotFoundError("Appointment slot not found")
        self.authz.require_provider_in_scope(slot.provider_account_id, scope)

        claim = self._claim(
            actor,
            operation="appointment.request",
            idempotency_key=idempotency_key,
            payload={
                "workspace_id": scope.workspace_id,
                "patient_person_id": patient_person_id,
                "slot_id": slot.id,
                "purpose": purpose,
            },
        )
        if claim.replay is not None:
            return claim.replay
        if slot.status != "AVAILABLE":
            raise SlotUnavailableError("The requested appointment slot is not available")

        appointment = CoreAppointment(
            patient_person_id=patient_person_id,
            requester_account_id=actor.account.id,
            provider_account_id=slot.provider_account_id,
            organization_id=scope.organization_id,
            facility_id=scope.facility_id,
            workspace_id=scope.workspace_id,
            slot_id=slot.id,
            service_code=slot.service_code,
            purpose=purpose,
            starts_at=slot.starts_at,
            ends_at=slot.ends_at,
            state="REQUESTED",
            version=1,
        )
        slot.status = "BOOKED"
        slot.version += 1
        self.db.add(appointment)
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise SlotUnavailableError("The requested appointment slot was taken concurrently") from exc

        response = self._appointment_response(appointment, correlation_id)
        claim.receipt.status = "COMPLETED"
        claim.receipt.resource_id = appointment.id
        claim.receipt.response_body = response
        claim.receipt.completed_at = datetime.now(UTC)
        self.db.flush()
        self._audit(
            actor,
            event_type="APPOINTMENT_REQUESTED",
            action="appointment.request",
            target_id=appointment.id,
            scope=scope,
            correlation_id=correlation_id,
            request_id=request_id,
            changes={"state_before": None, "state_after": appointment.state, "version_after": appointment.version},
        )
        return response

    def confirm_appointment(
        self,
        actor: NiamActor,
        *,
        appointment_id: str,
        workspace_id: str,
        expected_version: int,
        reason: str | None,
        idempotency_key: str,
        correlation_id: str,
        request_id: str | None,
    ) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_permission(actor, scope, "appointment.confirm")
        appointment = (
            self.db.query(CoreAppointment)
            .filter(
                CoreAppointment.id == appointment_id,
                CoreAppointment.organization_id == scope.organization_id,
                CoreAppointment.facility_id == scope.facility_id,
                CoreAppointment.workspace_id == scope.workspace_id,
            )
            .with_for_update()
            .first()
        )
        if appointment is None:
            raise AppointmentNotFoundError("Appointment not found")

        claim = self._claim(
            actor,
            operation="appointment.confirm",
            idempotency_key=idempotency_key,
            payload={
                "resource_id": appointment.id,
                "workspace_id": scope.workspace_id,
                "expected_version": expected_version,
                "reason": reason or "",
            },
        )
        if claim.replay is not None:
            return claim.replay
        if appointment.version != expected_version:
            raise VersionConflictError("The appointment changed before confirmation")

        before = appointment.state
        try:
            require_transition("appointment", before, "CONFIRMED")
        except ValueError as exc:
            raise AppointmentConflictError("The appointment cannot be confirmed from its current state") from exc
        appointment.state = "CONFIRMED"
        appointment.version += 1
        appointment.confirmed_at = datetime.now(UTC)
        self.db.flush()

        response = self._appointment_response(appointment, correlation_id)
        claim.receipt.status = "COMPLETED"
        claim.receipt.resource_id = appointment.id
        claim.receipt.response_body = response
        claim.receipt.completed_at = datetime.now(UTC)
        self.db.flush()
        self._audit(
            actor,
            event_type="APPOINTMENT_CONFIRMED",
            action="appointment.confirm",
            target_id=appointment.id,
            scope=scope,
            correlation_id=correlation_id,
            request_id=request_id,
            changes={"state_before": before, "state_after": appointment.state, "version_before": expected_version, "version_after": appointment.version},
            metadata={"reason": reason or None},
        )
        return response

    def get_appointment(
        self,
        actor: NiamActor,
        *,
        appointment_id: str,
        workspace_id: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        appointment = (
            self.db.query(CoreAppointment)
            .filter(
                CoreAppointment.id == appointment_id,
                CoreAppointment.organization_id == scope.organization_id,
                CoreAppointment.facility_id == scope.facility_id,
                CoreAppointment.workspace_id == scope.workspace_id,
            )
            .first()
        )
        if appointment is None:
            raise AppointmentNotFoundError("Appointment not found")
        if actor.account.id not in {appointment.requester_account_id, appointment.provider_account_id}:
            self.authz.require_permission(actor, scope, "appointment.read")
        return self._appointment_response(appointment, correlation_id)

    def list_appointments(
        self,
        actor: NiamActor,
        *,
        workspace_id: str,
        state: str | None,
        limit: int,
        offset: int,
        correlation_id: str,
    ) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        can_read_scope = True
        try:
            self.authz.require_permission(actor, scope, "appointment.read")
        except AppointmentAuthorizationError:
            can_read_scope = False

        query = self.db.query(CoreAppointment).filter(
            CoreAppointment.organization_id == scope.organization_id,
            CoreAppointment.facility_id == scope.facility_id,
            CoreAppointment.workspace_id == scope.workspace_id,
        )
        if not can_read_scope:
            query = query.filter(
                (CoreAppointment.requester_account_id == actor.account.id)
                | (CoreAppointment.provider_account_id == actor.account.id)
            )
        if state:
            query = query.filter(CoreAppointment.state == state)
        total = query.count()
        appointments = query.order_by(CoreAppointment.starts_at.asc()).offset(offset).limit(limit).all()
        return {
            "items": [self._appointment_response(item, correlation_id) for item in appointments],
            "limit": limit,
            "offset": offset,
            "total": total,
        }

    def _claim(
        self,
        actor: NiamActor,
        *,
        operation: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> IdempotencyClaim:
        if not idempotency_key or len(idempotency_key) > 128:
            raise ValidationError("A valid Idempotency-Key is required")
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
        ).hexdigest()
        existing = (
            self.db.query(CoreAppointmentIdempotencyReceipt)
            .filter(
                CoreAppointmentIdempotencyReceipt.actor_account_id == actor.account.id,
                CoreAppointmentIdempotencyReceipt.operation == operation,
                CoreAppointmentIdempotencyReceipt.idempotency_key == idempotency_key,
            )
            .first()
        )
        if existing is not None:
            if existing.request_fingerprint != fingerprint:
                raise IdempotencyConflictError("The Idempotency-Key was reused for a different request")
            if existing.status == "COMPLETED" and existing.response_body:
                return IdempotencyClaim(existing, existing.response_body)
            raise IdempotencyConflictError("The request is already being processed")

        receipt = CoreAppointmentIdempotencyReceipt(
            actor_account_id=actor.account.id,
            operation=operation,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            status="CLAIMED",
        )
        self.db.add(receipt)
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise IdempotencyConflictError("The request is already being processed") from exc
        return IdempotencyClaim(receipt)

    def _audit(
        self,
        actor: NiamActor,
        *,
        event_type: str,
        action: str,
        target_id: str,
        scope: AppointmentScope,
        correlation_id: str,
        request_id: str | None,
        changes: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        target_type: str = "appointment",
    ) -> None:
        self.audit.record(
            AuditEventInput(
                event_type=event_type,
                category="clinical_appointment",
                action=action,
                actor_id=actor.account.id,
                actor_identity_id=actor.account.identity_id,
                actor_type="account",
                organization_id=scope.organization_id,
                facility_id=scope.facility_id,
                workspace_id=scope.workspace_id,
                target_type=target_type,
                target_id=target_id,
                decision="allow",
                request_id=request_id,
                correlation_id=correlation_id,
                session_id=actor.session.uuid,
                source="api",
                data_classification="INTERNAL",
                changes=changes,
                metadata=metadata,
            ),
        )

    @staticmethod
    def _slot_response(slot: CoreAppointmentSlot) -> dict[str, Any]:
        return {
            "id": slot.id,
            "workspace_id": slot.workspace_id,
            "provider_account_id": slot.provider_account_id,
            "service_code": slot.service_code,
            "starts_at": slot.starts_at.isoformat(),
            "ends_at": slot.ends_at.isoformat(),
            "status": slot.status,
            "version": slot.version,
        }

    @staticmethod
    def _appointment_response(appointment: CoreAppointment, correlation_id: str) -> dict[str, Any]:
        return {
            "id": appointment.id,
            "state": appointment.state,
            "version": appointment.version,
            "slot_id": appointment.slot_id,
            "service_code": appointment.service_code,
            "purpose": appointment.purpose,
            "provider_account_id": appointment.provider_account_id,
            "organization_id": appointment.organization_id,
            "facility_id": appointment.facility_id,
            "workspace_id": appointment.workspace_id,
            "starts_at": appointment.starts_at.isoformat(),
            "ends_at": appointment.ends_at.isoformat(),
            "requested_at": appointment.requested_at.isoformat(),
            "confirmed_at": appointment.confirmed_at.isoformat() if appointment.confirmed_at else None,
            "correlation_id": correlation_id,
        }
