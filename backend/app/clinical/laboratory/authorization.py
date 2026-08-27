from __future__ import annotations

from app.clinical.appointments.authorization import (
    AppointmentAuthorizationError,
    AppointmentAuthorizationService,
    AppointmentScope,
)
from app.clinical.appointments.models import CoreAppointment
from app.clinical.encounters.models import CoreEncounter
from app.identity.api.workspaces import NiamActor


class LaboratoryAuthorizationService:
    """Server-authoritative contextual authorization for laboratory commands."""

    def __init__(self, db):
        self.db = db
        self.appointment_authz = AppointmentAuthorizationService(db)

    def resolve_scope(self, actor: NiamActor, workspace_id: str) -> AppointmentScope:
        return self.appointment_authz.resolve_scope(actor, workspace_id)

    def require_permission(self, actor: NiamActor, scope: AppointmentScope, permission: str) -> None:
        self.appointment_authz.require_permission(actor, scope, permission)

    def encounter_for_scope(self, encounter_id: str, scope: AppointmentScope) -> CoreEncounter:
        encounter = (
            self.db.query(CoreEncounter)
            .filter(
                CoreEncounter.id == encounter_id,
                CoreEncounter.organization_id == scope.organization_id,
                CoreEncounter.facility_id == scope.facility_id,
                CoreEncounter.workspace_id == scope.workspace_id,
            )
            .first()
        )
        if encounter is None:
            raise AppointmentAuthorizationError(
                "encounter_scope_unresolved",
                organization_id=scope.organization_id,
                facility_id=scope.facility_id,
                workspace_id=scope.workspace_id,
            )
        return encounter

    def appointment_for_encounter(self, encounter: CoreEncounter, scope: AppointmentScope) -> CoreAppointment:
        appointment = (
            self.db.query(CoreAppointment)
            .filter(
                CoreAppointment.id == encounter.appointment_id,
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

    def require_ordering_provider(self, actor: NiamActor, scope: AppointmentScope, appointment: CoreAppointment) -> None:
        if actor.account.id != appointment.provider_account_id:
            raise AppointmentAuthorizationError(
                "provider_object_mismatch",
                organization_id=scope.organization_id,
                facility_id=scope.facility_id,
                workspace_id=scope.workspace_id,
            )
        self.require_permission(actor, scope, "clinical.lab_order.create")

    def require_order_read(self, actor: NiamActor, scope: AppointmentScope, appointment: CoreAppointment) -> None:
        if actor.account.id in {appointment.requester_account_id, appointment.provider_account_id}:
            return
        self.require_permission(actor, scope, "clinical.lab_order.read")

    def require_specimen_operator(self, actor: NiamActor, scope: AppointmentScope) -> None:
        self.require_permission(actor, scope, "clinical.specimen.manage")

    def require_result_operator(self, actor: NiamActor, scope: AppointmentScope, permission: str) -> None:
        self.require_permission(actor, scope, permission)
