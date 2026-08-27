from __future__ import annotations

from app.clinical.appointments.authorization import (
    AppointmentAuthorizationError,
    AppointmentAuthorizationService,
    AppointmentScope,
)
from app.clinical.appointments.models import CoreAppointment
from app.identity.api.workspaces import NiamActor


class EncounterAuthorizationService:
    """Contextual authorization for the canonical encounter slice."""

    def __init__(self, db):
        self.db = db
        self.appointment_authz = AppointmentAuthorizationService(db)

    def resolve_scope(self, actor: NiamActor, workspace_id: str) -> AppointmentScope:
        return self.appointment_authz.resolve_scope(actor, workspace_id)

    def require_permission(self, actor: NiamActor, scope: AppointmentScope, permission: str) -> None:
        self.appointment_authz.require_permission(actor, scope, permission)

    def appointment_for_scope(self, appointment_id: str, scope: AppointmentScope) -> CoreAppointment:
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
            raise AppointmentAuthorizationError(
                "appointment_scope_unresolved",
                organization_id=scope.organization_id,
                facility_id=scope.facility_id,
                workspace_id=scope.workspace_id,
            )
        return appointment

    def require_patient_self(self, scope: AppointmentScope, appointment: CoreAppointment) -> None:
        if scope.actor_person_id != appointment.patient_person_id:
            raise AppointmentAuthorizationError(
                "patient_identity_mismatch",
                organization_id=scope.organization_id,
                facility_id=scope.facility_id,
                workspace_id=scope.workspace_id,
            )

    def require_provider(self, actor: NiamActor, scope: AppointmentScope, appointment: CoreAppointment, permission: str) -> None:
        if actor.account.id != appointment.provider_account_id:
            raise AppointmentAuthorizationError(
                "provider_object_mismatch",
                organization_id=scope.organization_id,
                facility_id=scope.facility_id,
                workspace_id=scope.workspace_id,
            )
        self.require_permission(actor, scope, permission)

    def require_actor_for_read(self, actor: NiamActor, scope: AppointmentScope, appointment, permission: str) -> None:
        if actor.account.id in {appointment.requester_account_id, appointment.provider_account_id}:
            return
        self.require_permission(actor, scope, permission)
