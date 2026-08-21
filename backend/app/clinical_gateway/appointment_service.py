from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.clinical_gateway.access_context import ClinicalAccessContext
from app.clinical_gateway.context import (
    ClinicalGatewayBlocked,
    ClinicalGatewayContext,
    ClinicalGatewayContextResolver,
)
from app.identity.api.workspaces import NiamActor
from app.national.domain.patient import Patient as NationalPatient
from app.national.scheduling_platform.application.service import SchedulingPlatformService
from app.national.scheduling_platform.domain.entities import Appointment
from app.national.scheduling_platform.infrastructure.models import NationalAppointment


class AppointmentCanonicalConflict(RuntimeError):
    """A canonical appointment command cannot be applied safely."""


class AppointmentCanonicalService:
    """Server-authoritative facade over the durable national scheduling service."""

    def __init__(self, db: Session, scheduler: SchedulingPlatformService) -> None:
        self.db = db
        self.scheduler = scheduler

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _gateway(self, actor: NiamActor) -> ClinicalGatewayContext:
        return ClinicalGatewayContextResolver(self.db).resolve(actor)

    def _access_for_patient(
        self,
        actor: NiamActor,
        patient_id: str,
        *,
        purpose: str,
        permissions: frozenset[str],
    ) -> ClinicalAccessContext:
        gateway = self._gateway(actor)
        patient = (
            self.db.query(NationalPatient)
            .filter(
                NationalPatient.id == patient_id,
                NationalPatient.lab_id == gateway.legacy_user.lab_id,
                NationalPatient.is_deleted.is_(False),
                NationalPatient.is_active.is_(True),
                NationalPatient.lab_patient_id.isnot(None),
            )
            .one_or_none()
        )
        if patient is None or patient.lab_patient_id is None:
            raise ClinicalGatewayBlocked("national_patient_mapping_missing")
        return ClinicalAccessContext.from_gateway_for_patient(
            self.db,
            gateway,
            patient_id=int(patient.lab_patient_id),
            purpose=purpose,
            permissions=permissions,
        )

    def _access_for_appointment(
        self,
        actor: NiamActor,
        appointment: NationalAppointment,
        *,
        purpose: str,
        permissions: frozenset[str],
    ) -> ClinicalAccessContext:
        access = self._access_for_patient(
            actor,
            appointment.patient_id,
            purpose=purpose,
            permissions=permissions,
        )
        if (
            appointment.organization_id != access.organization_id
            or appointment.facility_id != access.facility_id
            or appointment.workspace_id != access.workspace_id
            or appointment.tenant_id != access.tenant_id
        ):
            raise ClinicalGatewayBlocked("appointment_scope_mismatch")
        return access

    @staticmethod
    def _appointment_model(db: Session, appointment_id: str) -> NationalAppointment:
        appointment = (
            db.query(NationalAppointment)
            .filter(
                NationalAppointment.id == appointment_id,
                NationalAppointment.is_deleted.is_(False),
            )
            .one_or_none()
        )
        if appointment is None:
            raise AppointmentCanonicalConflict("appointment_not_found")
        if not appointment.organization_id or not appointment.workspace_id or appointment.tenant_id is None:
            raise ClinicalGatewayBlocked("appointment_scope_unresolved")
        return appointment

    @staticmethod
    def to_safe_dict(appointment: NationalAppointment | Appointment) -> dict[str, Any]:
        return {
            "id": appointment.id,
            "patient_id": appointment.patient_id,
            "practitioner_id": appointment.practitioner_id or None,
            "facility_id": appointment.facility_id or None,
            "appointment_type": appointment.appointment_type,
            "title": appointment.title,
            "description": appointment.description,
            "start_at": appointment.start_at.isoformat() if appointment.start_at else None,
            "end_at": appointment.end_at.isoformat() if appointment.end_at else None,
            "status": appointment.status.value if hasattr(appointment.status, "value") else str(appointment.status),
            "notes": appointment.notes,
            "version": appointment.version,
            "organization_id": getattr(appointment, "organization_id", None),
            "workspace_id": getattr(appointment, "workspace_id", None),
            "department_id": getattr(appointment, "department_id", None),
        }

    def get(
        self,
        *,
        actor: NiamActor,
        appointment_id: str,
    ) -> tuple[ClinicalAccessContext, NationalAppointment]:
        model = self._appointment_model(self.db, appointment_id)
        access = self._access_for_appointment(
            actor,
            model,
            purpose="appointment.read",
            permissions=frozenset({"read"}),
        )
        return access, model

    def list_for_workspace(
        self,
        *,
        actor: NiamActor,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[ClinicalAccessContext, list[NationalAppointment]]:
        gateway = self._gateway(actor)
        access = ClinicalAccessContext.from_gateway(
            gateway,
            purpose="appointment.read",
            permissions=frozenset({"read"}),
        )
        query = self.db.query(NationalAppointment).filter(
            NationalAppointment.organization_id == access.organization_id,
            NationalAppointment.facility_id == access.facility_id,
            NationalAppointment.workspace_id == access.workspace_id,
            NationalAppointment.tenant_id == access.tenant_id,
            NationalAppointment.is_deleted.is_(False),
        )
        if status:
            query = query.filter(NationalAppointment.status == status)
        rows = query.order_by(NationalAppointment.start_at.asc().nullsfirst()).offset(offset).limit(limit).all()
        return access, rows

    async def create(
        self,
        *,
        actor: NiamActor,
        patient_id: str,
        appointment_type: str,
        start_at: datetime,
        end_at: datetime,
        title: str = "",
        description: str = "",
        notes: str = "",
        idempotency_key: str | None = None,
    ) -> NationalAppointment:
        access = self._access_for_patient(
            actor,
            patient_id,
            purpose="appointment.create",
            permissions=frozenset({"create"}),
        )
        access.require_operation("create")
        if not appointment_type.strip() or start_at >= end_at:
            raise AppointmentCanonicalConflict("invalid_appointment_input")
        start_at = self._utc(start_at)
        end_at = self._utc(end_at)
        if idempotency_key:
            existing = (
                self.db.query(NationalAppointment)
                .filter(
                    NationalAppointment.organization_id == access.organization_id,
                    NationalAppointment.workspace_id == access.workspace_id,
                    NationalAppointment.idempotency_key == idempotency_key,
                    NationalAppointment.is_deleted.is_(False),
                )
                .one_or_none()
            )
            if existing is not None:
                return existing

        practitioner_id = access.membership.identity_id or None
        appointment = await self.scheduler.create_appointment(
            patient_id=patient_id,
            practitioner_id=str(practitioner_id) if practitioner_id else "",
            facility_id=access.facility_id,
            resource_id="",
            title=title,
            description=description,
            start_at=start_at,
            end_at=end_at,
            appointment_type=appointment_type,
            notes=notes,
            metadata={"clinical_access": access.audit_fields(action="appointment.create")},
            created_by=str(access.account_id),
        )
        model = self.db.query(NationalAppointment).filter(NationalAppointment.id == appointment.id).one()
        model.organization_id = access.organization_id
        model.workspace_id = access.workspace_id
        model.department_id = access.department_id
        model.tenant_id = access.tenant_id
        model.legacy_lab_id = access.legacy_lab_id
        model.idempotency_key = idempotency_key
        self.db.commit()
        self.db.refresh(model)
        return model

    async def reschedule(
        self,
        *,
        actor: NiamActor,
        appointment_id: str,
        start_at: datetime,
        end_at: datetime,
        expected_version: int | None,
        reason: str = "",
    ) -> NationalAppointment:
        model = self._appointment_model(self.db, appointment_id)
        access = self._access_for_appointment(actor, model, purpose="appointment.reschedule", permissions=frozenset({"update"}))
        access.require_operation("update")
        if expected_version is not None and model.version != expected_version:
            raise AppointmentCanonicalConflict("appointment_version_conflict")
        if start_at >= end_at:
            raise AppointmentCanonicalConflict("invalid_appointment_time")
        await self.scheduler.reschedule_appointment(appointment_id, self._utc(start_at), self._utc(end_at), reason)
        self.db.refresh(model)
        return model

    async def cancel(
        self,
        *,
        actor: NiamActor,
        appointment_id: str,
        expected_version: int | None,
        reason: str = "",
    ) -> NationalAppointment:
        model = self._appointment_model(self.db, appointment_id)
        access = self._access_for_appointment(actor, model, purpose="appointment.cancel", permissions=frozenset({"update"}))
        access.require_operation("update")
        if expected_version is not None and model.version != expected_version:
            raise AppointmentCanonicalConflict("appointment_version_conflict")
        await self.scheduler.cancel_appointment(appointment_id, reason)
        self.db.refresh(model)
        return model

    async def transition(
        self,
        *,
        actor: NiamActor,
        appointment_id: str,
        status: str,
        expected_version: int | None,
    ) -> NationalAppointment:
        model = self._appointment_model(self.db, appointment_id)
        access = self._access_for_appointment(actor, model, purpose="appointment.transition", permissions=frozenset({"update"}))
        access.require_operation("update")
        if expected_version is not None and model.version != expected_version:
            raise AppointmentCanonicalConflict("appointment_version_conflict")
        from app.national.scheduling_platform.domain.enums import AppointmentStatus

        try:
            target = AppointmentStatus(status)
        except ValueError as exc:
            raise AppointmentCanonicalConflict("invalid_appointment_status") from exc
        await self.scheduler.update_appointment_status(appointment_id, target)
        self.db.refresh(model)
        return model
