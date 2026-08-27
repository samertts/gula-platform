from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.clinical.appointments.models import CoreAppointment, CoreAppointmentIdempotencyReceipt
from app.clinical.appointments.service import (
    AppointmentError,
    IdempotencyConflictError,
    VersionConflictError,
)
from app.contracts.clinical_core import require_transition
from app.identity.api.workspaces import NiamActor
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService

from .authorization import EncounterAuthorizationService
from .models import CoreClinicalNote, CoreEncounter, CoreEncounterQueueEntry


class EncounterNotFoundError(AppointmentError):
    code = "ENCOUNTER_NOT_FOUND"
    status_code = 404


class AppointmentNotEligibleError(AppointmentError):
    code = "APPOINTMENT_NOT_ELIGIBLE"
    status_code = 409


class AlreadyCheckedInError(AppointmentError):
    code = "ALREADY_CHECKED_IN"
    status_code = 409


class EncounterStateConflictError(AppointmentError):
    code = "ENCOUNTER_STATE_CONFLICT"
    status_code = 409


class ClinicalNoteNotFoundError(AppointmentError):
    code = "CLINICAL_NOTE_NOT_FOUND"
    status_code = 404


class NoteImmutableError(AppointmentError):
    code = "CLINICAL_NOTE_IMMUTABLE"
    status_code = 409


class EncounterService:
    """Server-authoritative check-in, encounter and note boundary."""

    def __init__(self, db):
        self.db = db
        self.authz = EncounterAuthorizationService(db)
        self.audit = SyncCanonicalAuditService(db)

    def check_in(self, actor: NiamActor, *, appointment_id: str, workspace_id: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        appointment = self._appointment_for_update(appointment_id, scope)
        if actor.account.id == appointment.requester_account_id:
            self.authz.require_patient_self(scope, appointment)
        else:
            self.authz.require_provider(actor, scope, appointment, "encounter.checkin")
        claim = self._claim(actor, "encounter.checkin", idempotency_key, {"appointment_id": appointment.id, "workspace_id": scope.workspace_id})
        if claim is not None:
            return claim
        if appointment.state != "CONFIRMED":
            if appointment.state == "CHECKED_IN":
                raise AlreadyCheckedInError("The appointment is already checked in")
            raise AppointmentNotEligibleError("The appointment is not eligible for check-in")
        existing = self.db.query(CoreEncounter).filter(CoreEncounter.appointment_id == appointment.id).with_for_update().first()
        if existing is not None:
            raise AlreadyCheckedInError("The appointment is already checked in")
        encounter = CoreEncounter(
            appointment_id=appointment.id,
            patient_person_id=appointment.patient_person_id,
            provider_account_id=appointment.provider_account_id,
            organization_id=scope.organization_id,
            facility_id=scope.facility_id,
            workspace_id=scope.workspace_id,
            status="CHECKED_IN",
            version=1,
            checked_in_at=datetime.now(UTC),
        )
        appointment.state = "CHECKED_IN"
        appointment.version += 1
        self.db.add(encounter)
        self.db.flush()
        self.db.add(CoreEncounterQueueEntry(encounter_id=encounter.id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, status="WAITING", version=1))
        self.db.flush()
        response = self._encounter_response(encounter, correlation_id)
        self._complete_receipt(actor, "encounter.checkin", idempotency_key, response, encounter.id)
        self._audit(actor, "ENCOUNTER_CHECKED_IN", "encounter.checkin", encounter.id, scope, correlation_id, request_id, {"state_before": "CONFIRMED", "state_after": "CHECKED_IN", "version_after": encounter.version})
        return response

    def get_encounter(self, actor: NiamActor, *, encounter_id: str, workspace_id: str, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        encounter = self._encounter_for_scope(encounter_id, scope)
        appointment = self.db.query(CoreAppointment).filter(CoreAppointment.id == encounter.appointment_id).first()
        if appointment is None:
            raise EncounterNotFoundError("Encounter appointment not found")
        self.authz.require_actor_for_read(actor, scope, appointment, "encounter.read")
        return self._encounter_response(encounter, correlation_id)

    def transition_encounter(self, actor: NiamActor, *, encounter_id: str, workspace_id: str, target: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        encounter = self._encounter_for_update(encounter_id, scope)
        appointment = self.db.query(CoreAppointment).filter(CoreAppointment.id == encounter.appointment_id).first()
        if appointment is None:
            raise EncounterNotFoundError("Encounter appointment not found")
        self.authz.require_provider(actor, scope, appointment, "encounter.manage")
        claim = self._claim(actor, f"encounter.{target.lower()}", idempotency_key, {"resource_id": encounter.id, "workspace_id": scope.workspace_id, "expected_version": expected_version})
        if claim is not None:
            return claim
        if encounter.version != expected_version:
            raise VersionConflictError("The encounter changed before this operation")
        try:
            require_transition("encounter", encounter.status, target)
        except ValueError as exc:
            raise EncounterStateConflictError("The encounter transition is not allowed") from exc
        before = encounter.status
        queue = self.db.query(CoreEncounterQueueEntry).filter(CoreEncounterQueueEntry.encounter_id == encounter.id).with_for_update().first()
        encounter.status = target
        encounter.version += 1
        if queue is not None and target == "IN_PROGRESS":
            queue.status = "IN_SERVICE"
            queue.version += 1
        elif queue is not None and target == "COMPLETED":
            queue.status = "COMPLETED"
            queue.version += 1
        now = datetime.now(UTC)
        if target == "IN_PROGRESS":
            encounter.started_at = now
        elif target == "COMPLETED":
            encounter.completed_at = now
        self.db.flush()
        response = self._encounter_response(encounter, correlation_id)
        self._complete_receipt(actor, f"encounter.{target.lower()}", idempotency_key, response, encounter.id)
        self._audit(actor, f"ENCOUNTER_{target}", f"encounter.{target.lower()}", encounter.id, scope, correlation_id, request_id, {"state_before": before, "state_after": target, "version_before": expected_version, "version_after": encounter.version})
        return response

    def create_note(self, actor: NiamActor, *, encounter_id: str, workspace_id: str, fields: dict[str, Any], idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        encounter = self._encounter_for_scope(encounter_id, scope)
        appointment = self.db.query(CoreAppointment).filter(CoreAppointment.id == encounter.appointment_id).first()
        if appointment is None:
            raise EncounterNotFoundError("Encounter appointment not found")
        self.authz.require_provider(actor, scope, appointment, "clinical.note.write")
        if encounter.status != "IN_PROGRESS":
            raise EncounterStateConflictError("Clinical notes require an in-progress encounter")
        payload = {"encounter_id": encounter.id, "workspace_id": scope.workspace_id, **fields}
        claim = self._claim(actor, "clinical.note.create", idempotency_key, payload)
        if claim is not None:
            return claim
        note_id = self._id()
        note = CoreClinicalNote(note_id=note_id, encounter_id=encounter.id, patient_person_id=encounter.patient_person_id, author_account_id=actor.account.id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, status="DRAFT", version=1, **self._note_fields(fields))
        self.db.add(note)
        self.db.flush()
        response = self._note_response(note, correlation_id)
        self._complete_receipt(actor, "clinical.note.create", idempotency_key, response, note.id)
        self._audit(actor, "NOTE_CREATED", "clinical.note.create", note.id, scope, correlation_id, request_id, {"state_before": None, "state_after": "DRAFT", "version_after": note.version})
        return response

    def update_note(self, actor: NiamActor, *, note_id: str, workspace_id: str, expected_version: int, fields: dict[str, Any], idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        note = self._note_for_update(note_id, scope)
        encounter = self._encounter_for_scope(note.encounter_id, scope)
        appointment = self.db.query(CoreAppointment).filter(CoreAppointment.id == encounter.appointment_id).first()
        if appointment is None:
            raise EncounterNotFoundError("Encounter appointment not found")
        self.authz.require_provider(actor, scope, appointment, "clinical.note.write")
        if note.author_account_id != actor.account.id:
            raise NoteImmutableError("Only the note author may update a draft")
        if note.status not in {"DRAFT", "COMPLETED"}:
            raise NoteImmutableError("Signed notes require an amendment")
        if note.version != expected_version:
            raise VersionConflictError("The clinical note changed before this operation")
        claim = self._claim(actor, "clinical.note.update", idempotency_key, {"resource_id": note.id, "workspace_id": scope.workspace_id, "expected_version": expected_version, **fields})
        if claim is not None:
            return claim
        before = note.version
        for key, value in self._note_fields(fields).items():
            setattr(note, key, value)
        note.version += 1
        self.db.flush()
        response = self._note_response(note, correlation_id)
        self._complete_receipt(actor, "clinical.note.update", idempotency_key, response, note.id)
        self._audit(actor, "NOTE_UPDATED", "clinical.note.update", note.id, scope, correlation_id, request_id, {"state_before": note.status, "state_after": note.status, "version_before": before, "version_after": note.version})
        return response

    def transition_note(self, actor: NiamActor, *, note_id: str, workspace_id: str, target: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        note = self._note_for_update(note_id, scope)
        encounter = self._encounter_for_scope(note.encounter_id, scope)
        appointment = self.db.query(CoreAppointment).filter(CoreAppointment.id == encounter.appointment_id).first()
        if appointment is None:
            raise EncounterNotFoundError("Encounter appointment not found")
        permission = "clinical.note.sign" if target == "SIGNED" else "clinical.note.write"
        self.authz.require_provider(actor, scope, appointment, permission)
        if note.version != expected_version:
            raise VersionConflictError("The clinical note changed before this operation")
        claim = self._claim(actor, f"clinical.note.{target.lower()}", idempotency_key, {"resource_id": note.id, "workspace_id": scope.workspace_id, "expected_version": expected_version})
        if claim is not None:
            return claim
        try:
            require_transition("clinical-note", note.status, target)
        except ValueError as exc:
            raise NoteImmutableError("The clinical note transition is not allowed") from exc
        before = note.status
        note.status = target
        note.version += 1
        if target == "SIGNED":
            note.signed_by_account_id = actor.account.id
            note.signed_at = datetime.now(UTC)
        self.db.flush()
        response = self._note_response(note, correlation_id)
        self._complete_receipt(actor, f"clinical.note.{target.lower()}", idempotency_key, response, note.id)
        self._audit(actor, f"NOTE_{target}", f"clinical.note.{target.lower()}", note.id, scope, correlation_id, request_id, {"state_before": before, "state_after": target, "version_before": expected_version, "version_after": note.version})
        return response

    def amend_note(self, actor: NiamActor, *, note_id: str, workspace_id: str, reason: str, idempotency_key: str, correlation_id: str, request_id: str | None, fields: dict[str, Any]) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        note = self._note_for_update(note_id, scope)
        encounter = self._encounter_for_scope(note.encounter_id, scope)
        appointment = self.db.query(CoreAppointment).filter(CoreAppointment.id == encounter.appointment_id).first()
        if appointment is None:
            raise EncounterNotFoundError("Encounter appointment not found")
        self.authz.require_provider(actor, scope, appointment, "clinical.note.amend")
        if note.status != "SIGNED" or not reason.strip():
            raise NoteImmutableError("A signed note requires a non-empty amendment reason")
        claim = self._claim(actor, "clinical.note.amend", idempotency_key, {"resource_id": note.id, "workspace_id": scope.workspace_id, "reason": reason.strip(), **fields})
        if claim is not None:
            return claim
        new_note = CoreClinicalNote(note_id=note.note_id, encounter_id=note.encounter_id, patient_person_id=note.patient_person_id, author_account_id=actor.account.id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, status="AMENDED", version=note.version + 1, supersedes_id=note.id, amendment_reason=reason.strip(), **self._note_fields(fields, note))
        self.db.add(new_note)
        self.db.flush()
        response = self._note_response(new_note, correlation_id)
        self._complete_receipt(actor, "clinical.note.amend", idempotency_key, response, new_note.id)
        self._audit(actor, "NOTE_AMENDED", "clinical.note.amend", new_note.id, scope, correlation_id, request_id, {"state_before": "SIGNED", "state_after": "AMENDED", "version_before": note.version, "version_after": new_note.version})
        return response

    def _appointment_for_update(self, appointment_id, scope):
        appointment = self.db.query(CoreAppointment).filter(CoreAppointment.id == appointment_id, CoreAppointment.organization_id == scope.organization_id, CoreAppointment.facility_id == scope.facility_id, CoreAppointment.workspace_id == scope.workspace_id).with_for_update().first()
        if appointment is None:
            raise AppointmentNotEligibleError("Appointment not found in the authorized scope")
        return appointment

    def _encounter_for_scope(self, encounter_id, scope):
        encounter = self.db.query(CoreEncounter).filter(CoreEncounter.id == encounter_id, CoreEncounter.organization_id == scope.organization_id, CoreEncounter.facility_id == scope.facility_id, CoreEncounter.workspace_id == scope.workspace_id).first()
        if encounter is None:
            raise EncounterNotFoundError("Encounter not found")
        return encounter

    def _encounter_for_update(self, encounter_id, scope):
        encounter = self.db.query(CoreEncounter).filter(CoreEncounter.id == encounter_id, CoreEncounter.organization_id == scope.organization_id, CoreEncounter.facility_id == scope.facility_id, CoreEncounter.workspace_id == scope.workspace_id).with_for_update().first()
        if encounter is None:
            raise EncounterNotFoundError("Encounter not found")
        return encounter

    def _note_for_update(self, note_id, scope):
        note = self.db.query(CoreClinicalNote).filter(CoreClinicalNote.id == note_id, CoreClinicalNote.organization_id == scope.organization_id, CoreClinicalNote.facility_id == scope.facility_id, CoreClinicalNote.workspace_id == scope.workspace_id).with_for_update().first()
        if note is None:
            raise ClinicalNoteNotFoundError("Clinical note not found")
        return note

    def _claim(self, actor, operation, key, payload):
        if not key or len(key) > 128:
            raise AppointmentError("Idempotency-Key is required", status_code=400, code="VALIDATION_ERROR")
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        existing = self.db.query(CoreAppointmentIdempotencyReceipt).filter(CoreAppointmentIdempotencyReceipt.actor_account_id == actor.account.id, CoreAppointmentIdempotencyReceipt.operation == operation, CoreAppointmentIdempotencyReceipt.idempotency_key == key).first()
        if existing is not None:
            if existing.request_fingerprint != fingerprint:
                raise IdempotencyConflictError("The Idempotency-Key was reused for a different request")
            if existing.status == "COMPLETED" and existing.response_body:
                return existing.response_body
            raise IdempotencyConflictError("The request is already being processed")
        receipt = CoreAppointmentIdempotencyReceipt(actor_account_id=actor.account.id, operation=operation, idempotency_key=key, request_fingerprint=fingerprint, status="CLAIMED")
        self.db.add(receipt)
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise IdempotencyConflictError("The request is already being processed") from exc
        return None

    def _complete_receipt(self, actor, operation, key, response, resource_id):
        receipt = self.db.query(CoreAppointmentIdempotencyReceipt).filter(CoreAppointmentIdempotencyReceipt.actor_account_id == actor.account.id, CoreAppointmentIdempotencyReceipt.operation == operation, CoreAppointmentIdempotencyReceipt.idempotency_key == key).with_for_update().one()
        receipt.status = "COMPLETED"
        receipt.resource_id = resource_id
        receipt.response_body = response
        receipt.completed_at = datetime.now(UTC)
        self.db.flush()

    def _audit(self, actor, event_type, action, target_id, scope, correlation_id, request_id, changes):
        self.audit.record(AuditEventInput(event_type=event_type, category="clinical_encounter", action=action, actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type="encounter" if "NOTE" not in event_type else "clinical_note", target_id=target_id, decision="allow", request_id=request_id, correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="INTERNAL", changes=changes))

    @staticmethod
    def _id():
        import uuid
        return str(uuid.uuid4()).replace("-", "").upper()[:26]

    @staticmethod
    def _note_fields(fields, source=None):
        allowed = ("chief_complaint", "history", "examination", "assessment", "plan")
        return {key: fields[key] if key in fields else getattr(source, key, None) if source is not None else None for key in allowed}

    @staticmethod
    def _encounter_response(item, correlation_id):
        return {"id": item.id, "appointment_id": item.appointment_id, "patient_person_id": item.patient_person_id, "provider_account_id": item.provider_account_id, "organization_id": item.organization_id, "facility_id": item.facility_id, "workspace_id": item.workspace_id, "status": item.status, "version": item.version, "checked_in_at": item.checked_in_at.isoformat() if item.checked_in_at else None, "started_at": item.started_at.isoformat() if item.started_at else None, "completed_at": item.completed_at.isoformat() if item.completed_at else None, "correlation_id": correlation_id}

    @staticmethod
    def _note_response(item, correlation_id):
        return {"id": item.id, "note_id": item.note_id, "encounter_id": item.encounter_id, "patient_person_id": item.patient_person_id, "author_account_id": item.author_account_id, "status": item.status, "version": item.version, "chief_complaint": item.chief_complaint, "history": item.history, "examination": item.examination, "assessment": item.assessment, "plan": item.plan, "amendment_reason": item.amendment_reason, "supersedes_id": item.supersedes_id, "signed_by_account_id": item.signed_by_account_id, "signed_at": item.signed_at.isoformat() if item.signed_at else None, "correlation_id": correlation_id}
