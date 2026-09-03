from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.clinical.appointments.authorization import (
    AppointmentAuthorizationService,
)
from app.clinical.appointments.service import AppointmentError, VersionConflictError
from app.clinical.command_guard import CanonicalClinicalCommandGuard
from app.contracts.clinical_core import require_transition
from app.identity.api.workspaces import NiamActor
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService

from .models import (
    CoreEmergencyBreakGlass,
    CoreEmergencyBreakGlassEvent,
    CoreEmergencyDispatch,
    CoreEmergencyEPCR,
    CoreEmergencyHandover,
    CoreEmergencyIncident,
    CoreEmergencyOutbox,
    CoreEmergencyPrealert,
    CoreEmergencyTemporarySubject,
    CoreEmergencyTreatment,
    CoreEmergencyTriage,
)


class EmergencyNotFoundError(AppointmentError):
    code = "EMERGENCY_RESOURCE_NOT_FOUND"
    status_code = 404


class EmergencyConflictError(AppointmentError):
    code = "EMERGENCY_STATE_CONFLICT"
    status_code = 409


class EmergencyStateError(EmergencyConflictError):
    code = "INVALID_EMERGENCY_STATE"


class CanonicalEmergencyService:
    """Canonical prehospital/emergency workflow with synthetic integrations only."""

    def __init__(self, db):
        self.db = db
        self.authz = AppointmentAuthorizationService(db)
        self.audit = SyncCanonicalAuditService(db)
        self.command_guard = CanonicalClinicalCommandGuard(db, actor_account_id=None)

    def create_temporary_subject(self, actor: NiamActor, *, workspace_id: str, synthetic_label: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.subject.write")
        payload = {"workspace_id": scope.workspace_id, "synthetic_label": synthetic_label.strip()}
        cached = self._claim(actor, "emergency.subject.create", idempotency_key, payload)
        if cached is not None:
            return cached
        subject_id = _synthetic_reference()
        subject = CoreEmergencyTemporarySubject(temporary_subject_id=subject_id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, created_by_account_id=actor.account.id, status="ACTIVE", synthetic_label=synthetic_label.strip(), reconciliation_status="UNMATCHED", version=1)
        self.db.add(subject)
        self.db.flush()
        response = self._subject_response(subject, correlation_id)
        self._complete(actor, "emergency.subject.create", idempotency_key, response, subject.id)
        self._audit(actor, "TEMPORARY_SUBJECT_CREATED", "emergency_temporary_subject", subject.id, scope, correlation_id, request_id, {"state_after": subject.status, "reconciliation_status": subject.reconciliation_status})
        return response

    def create_incident(self, actor: NiamActor, *, incident_id: str, workspace_id: str, chief_complaint: str, priority: str, patient_person_id: str | None, temporary_subject_id: str | None, location_summary: str | None, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.incident.write")
        if bool(patient_person_id) == bool(temporary_subject_id):
            raise EmergencyConflictError("Exactly one subject reference is required", code="SUBJECT_REFERENCE_INVALID", status_code=422)
        if temporary_subject_id:
            subject = self._subject_for_scope(temporary_subject_id, scope)
            if subject.status not in {"ACTIVE", "UNVERIFIED"}:
                raise EmergencyConflictError("Temporary subject is not active", code="TEMPORARY_SUBJECT_NOT_ACTIVE")
        payload = {"incident_id": incident_id, "workspace_id": scope.workspace_id, "chief_complaint": chief_complaint.strip(), "priority": priority, "patient_person_id": patient_person_id, "temporary_subject_id": temporary_subject_id, "location_summary": location_summary}
        cached = self._claim(actor, "emergency.incident.create", idempotency_key, payload)
        if cached is not None:
            return cached
        if self.db.query(CoreEmergencyIncident).filter(CoreEmergencyIncident.incident_id == incident_id).first() is not None:
            raise EmergencyConflictError("Incident already exists", code="INCIDENT_EXISTS")
        incident = CoreEmergencyIncident(incident_id=incident_id.strip(), subject_kind="KNOWN_PATIENT" if patient_person_id else "TEMPORARY", patient_person_id=patient_person_id, temporary_subject_id=temporary_subject_id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, reported_by_account_id=actor.account.id, status="REPORTED", priority=priority, chief_complaint=chief_complaint.strip(), location_summary=location_summary.strip() if location_summary else None, version=1)
        self.db.add(incident)
        self.db.flush()
        response = self._incident_response(incident, correlation_id)
        self._complete(actor, "emergency.incident.create", idempotency_key, response, incident.id)
        self._audit(actor, "EMERGENCY_INCIDENT_CREATED", "emergency_incident", incident.id, scope, correlation_id, request_id, {"state_after": incident.status, "subject_kind": incident.subject_kind, "priority": incident.priority})
        return response

    def transition_incident(self, actor: NiamActor, *, incident_id: str, workspace_id: str, target_status: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.incident.write")
        incident = self._incident_for_update(incident_id, scope)
        self._assert_version(incident.version, expected_version)
        payload = {"resource_id": incident.id, "workspace_id": scope.workspace_id, "target_status": target_status, "expected_version": expected_version}
        cached = self._claim(actor, "emergency.incident.transition", idempotency_key, payload)
        if cached is not None:
            return cached
        if target_status in {"DISPATCHED", "EN_ROUTE", "ON_SCENE", "TRANSPORTING", "AT_DESTINATION", "HANDOVER_COMPLETE"}:
            raise EmergencyConflictError("Use the dispatch or handover workflow for this transition", code="DEDICATED_WORKFLOW_REQUIRED")
        require_transition("emergency-incident", incident.status, target_status)
        before = incident.status
        incident.status = target_status
        incident.version += 1
        if target_status == "CLOSED":
            incident.closed_at = datetime.now(UTC)
        self.db.flush()
        response = self._incident_response(incident, correlation_id)
        self._complete(actor, "emergency.incident.transition", idempotency_key, response, incident.id)
        self._audit(actor, "EMERGENCY_INCIDENT_STATUS_CHANGED", "emergency_incident", incident.id, scope, correlation_id, request_id, {"state_before": before, "state_after": target_status, "version": incident.version})
        return response

    def create_triage(self, actor: NiamActor, *, incident_id: str, workspace_id: str, triage_id: str, category: str, clinician_summary: str, vital_snapshot: dict[str, Any], idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.triage.write")
        incident = self._incident_for_update(incident_id, scope)
        payload = {"incident_id": incident.id, "workspace_id": scope.workspace_id, "triage_id": triage_id, "category": category, "clinician_summary": clinician_summary.strip(), "vital_snapshot": vital_snapshot}
        cached = self._claim(actor, "emergency.triage.create", idempotency_key, payload)
        if cached is not None:
            return cached
        if incident.status in {"CLOSED", "CANCELLED"}:
            raise EmergencyStateError("Closed incident cannot be triaged")
        if self.db.query(CoreEmergencyTriage).filter(CoreEmergencyTriage.triage_id == triage_id).first() is not None:
            raise EmergencyConflictError("Triage record already exists", code="TRIAGE_EXISTS")
        triage = CoreEmergencyTriage(triage_id=triage_id.strip(), incident_id=incident.id, patient_person_id=incident.patient_person_id, temporary_subject_id=incident.temporary_subject_id, category=category, clinician_summary=clinician_summary.strip(), vital_snapshot=self._minimal_vitals(vital_snapshot), assessed_by_account_id=actor.account.id, version=1)
        incident.status = "TRIAGED"
        incident.version += 1
        self.db.add(triage)
        self.db.flush()
        response = self._triage_response(triage, correlation_id)
        self._complete(actor, "emergency.triage.create", idempotency_key, response, triage.id)
        self._audit(actor, "EMERGENCY_TRIAGE_RECORDED", "emergency_triage", triage.id, scope, correlation_id, request_id, {"incident_id": incident.id, "category": category, "incident_version": incident.version})
        return response

    def create_dispatch(self, actor: NiamActor, *, dispatch_request_id: str, incident_id: str, workspace_id: str, ambulance_reference: str, crew_references: list[str], dispatch_notes: str | None, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.dispatch.write")
        incident = self._incident_for_update(incident_id, scope)
        payload = {"dispatch_request_id": dispatch_request_id, "incident_id": incident.id, "workspace_id": scope.workspace_id, "ambulance_reference": ambulance_reference, "crew_references": crew_references, "dispatch_notes": dispatch_notes}
        cached = self._claim(actor, "emergency.dispatch.create", idempotency_key, payload)
        if cached is not None:
            return cached
        if incident.status != "TRIAGED":
            raise EmergencyStateError("Dispatch requires a triaged incident")
        if self.db.query(CoreEmergencyDispatch).filter(CoreEmergencyDispatch.dispatch_request_id == dispatch_request_id).first() is not None:
            raise EmergencyConflictError("Dispatch request already exists", code="DISPATCH_EXISTS")
        dispatch = CoreEmergencyDispatch(dispatch_request_id=dispatch_request_id.strip(), incident_id=incident.id, ambulance_reference=ambulance_reference.strip(), crew_references=sorted(set(crew_references)), status="ASSIGNED", assigned_by_account_id=actor.account.id, dispatch_notes=dispatch_notes.strip() if dispatch_notes else None, version=1)
        self.db.add(dispatch)
        require_transition("emergency-incident", incident.status, "DISPATCHED")
        incident.status = "DISPATCHED"
        incident.version += 1
        self.db.flush()
        response = self._dispatch_response(dispatch, correlation_id)
        self._complete(actor, "emergency.dispatch.create", idempotency_key, response, dispatch.id)
        self._audit(actor, "EMERGENCY_DISPATCH_ASSIGNED", "emergency_dispatch", dispatch.id, scope, correlation_id, request_id, {"incident_id": incident.id, "state_after": dispatch.status, "incident_state_after": incident.status})
        return response

    def transition_dispatch(self, actor: NiamActor, *, dispatch_id: str, workspace_id: str, target_status: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.dispatch.write")
        dispatch = self.db.query(CoreEmergencyDispatch).join(CoreEmergencyIncident, CoreEmergencyIncident.id == CoreEmergencyDispatch.incident_id).filter(CoreEmergencyDispatch.id == dispatch_id, CoreEmergencyIncident.organization_id == scope.organization_id, CoreEmergencyIncident.facility_id == scope.facility_id, CoreEmergencyIncident.workspace_id == scope.workspace_id).with_for_update().first()
        if dispatch is None:
            raise EmergencyNotFoundError("Dispatch was not found", code="DISPATCH_NOT_FOUND")
        self._assert_version(dispatch.version, expected_version)
        payload = {"resource_id": dispatch.id, "workspace_id": scope.workspace_id, "target_status": target_status, "expected_version": expected_version}
        cached = self._claim(actor, "emergency.dispatch.transition", idempotency_key, payload)
        if cached is not None:
            return cached
        require_transition("emergency-dispatch", dispatch.status, target_status)
        incident = self._incident_for_update(dispatch.incident_id, scope)
        incident_target = {"EN_ROUTE": "EN_ROUTE", "ON_SCENE": "ON_SCENE", "TRANSPORTING": "TRANSPORTING", "AT_DESTINATION": "AT_DESTINATION", "COMPLETED": "HANDOVER_COMPLETE"}.get(target_status)
        if incident_target:
            require_transition("emergency-incident", incident.status, incident_target)
            incident.status = incident_target
            incident.version += 1
        before = dispatch.status
        dispatch.status = target_status
        dispatch.version += 1
        if target_status == "COMPLETED":
            dispatch.completed_at = datetime.now(UTC)
        self.db.flush()
        response = self._dispatch_response(dispatch, correlation_id)
        self._complete(actor, "emergency.dispatch.transition", idempotency_key, response, dispatch.id)
        self._audit(actor, "EMERGENCY_DISPATCH_STATUS_CHANGED", "emergency_dispatch", dispatch.id, scope, correlation_id, request_id, {"state_before": before, "state_after": target_status, "version": dispatch.version, "incident_status": incident.status})
        return response

    def create_treatment(self, actor: NiamActor, *, treatment_request_id: str, incident_id: str, workspace_id: str, treatment_type: str, treatment_details: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.treatment.write")
        incident = self._incident_for_scope(incident_id, scope)
        if incident.status in {"CLOSED", "CANCELLED"}:
            raise EmergencyStateError("Treatment cannot be added to a closed incident")
        payload = {"treatment_request_id": treatment_request_id, "incident_id": incident.id, "workspace_id": scope.workspace_id, "treatment_type": treatment_type, "treatment_details": treatment_details}
        cached = self._claim(actor, "emergency.treatment.create", idempotency_key, payload)
        if cached is not None:
            return cached
        if self.db.query(CoreEmergencyTreatment).filter(CoreEmergencyTreatment.treatment_request_id == treatment_request_id).first() is not None:
            raise EmergencyConflictError("Treatment request already exists", code="TREATMENT_EXISTS")
        treatment = CoreEmergencyTreatment(treatment_request_id=treatment_request_id.strip(), incident_id=incident.id, patient_person_id=incident.patient_person_id, temporary_subject_id=incident.temporary_subject_id, treatment_type=treatment_type.strip(), treatment_details=treatment_details.strip(), performed_by_account_id=actor.account.id)
        self.db.add(treatment)
        self.db.flush()
        response = {"id": treatment.id, "treatment_request_id": treatment.treatment_request_id, "incident_id": treatment.incident_id, "patient_person_id": treatment.patient_person_id, "temporary_subject_id": treatment.temporary_subject_id, "treatment_type": treatment.treatment_type, "performed_at": treatment.performed_at.isoformat(), "correlation_id": correlation_id}
        self._complete(actor, "emergency.treatment.create", idempotency_key, response, treatment.id)
        self._audit(actor, "EMERGENCY_TREATMENT_RECORDED", "emergency_treatment", treatment.id, scope, correlation_id, request_id, {"incident_id": incident.id, "treatment_type": treatment.treatment_type})
        return response

    def create_prealert(self, actor: NiamActor, *, prealert_request_id: str, incident_id: str, workspace_id: str, destination_facility_reference: str, acuity: str, estimated_arrival_minutes: int, minimal_payload: dict[str, Any], idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.prealert.write")
        incident = self._incident_for_scope(incident_id, scope)
        if incident.status not in {"ON_SCENE", "TRANSPORTING", "AT_DESTINATION"}:
            raise EmergencyStateError("Pre-alert requires an active dispatch")
        allowed = {"chief_complaint", "acuity", "vital_summary", "interventions", "allergies_known", "eta_minutes", "special_requirements"}
        payload_data = {key: value for key, value in minimal_payload.items() if key in allowed}
        payload = {"prealert_request_id": prealert_request_id, "incident_id": incident.id, "workspace_id": scope.workspace_id, "destination_facility_reference": destination_facility_reference, "acuity": acuity, "estimated_arrival_minutes": estimated_arrival_minutes, "minimal_payload": payload_data}
        cached = self._claim(actor, "emergency.prealert.create", idempotency_key, payload)
        if cached is not None:
            return cached
        if self.db.query(CoreEmergencyPrealert).filter(CoreEmergencyPrealert.prealert_request_id == prealert_request_id).first() is not None:
            raise EmergencyConflictError("Pre-alert request already exists", code="PREALERT_EXISTS")
        prealert = CoreEmergencyPrealert(prealert_request_id=prealert_request_id.strip(), incident_id=incident.id, destination_facility_reference=destination_facility_reference.strip(), acuity=acuity, estimated_arrival_minutes=estimated_arrival_minutes, minimal_payload=payload_data, delivery_mode="SYNTHETIC_INTENT", status="PENDING", created_by_account_id=actor.account.id, version=1)
        self.db.add(prealert)
        self.db.flush()
        self._add_outbox(actor, event_type="emergency.prealert.created", aggregate_type="emergency_prealert", aggregate_id=prealert.id, payload={"prealert_id": prealert.id, "incident_id": incident.id, "destination": destination_facility_reference, "delivery_mode": "SYNTHETIC_INTENT"})
        response = self._prealert_response(prealert, correlation_id)
        self._complete(actor, "emergency.prealert.create", idempotency_key, response, prealert.id)
        self._audit(actor, "EMERGENCY_PREALERT_CREATED", "emergency_prealert", prealert.id, scope, correlation_id, request_id, {"state_after": prealert.status, "delivery_mode": prealert.delivery_mode})
        return response

    def acknowledge_prealert(self, actor: NiamActor, *, prealert_id: str, workspace_id: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.prealert.write")
        prealert = self.db.query(CoreEmergencyPrealert).join(CoreEmergencyIncident, CoreEmergencyIncident.id == CoreEmergencyPrealert.incident_id).filter(CoreEmergencyPrealert.id == prealert_id, CoreEmergencyIncident.organization_id == scope.organization_id, CoreEmergencyIncident.facility_id == scope.facility_id, CoreEmergencyIncident.workspace_id == scope.workspace_id).with_for_update().first()
        if prealert is None:
            raise EmergencyNotFoundError("Pre-alert was not found", code="PREALERT_NOT_FOUND")
        self._assert_version(prealert.version, expected_version)
        payload = {"resource_id": prealert.id, "workspace_id": scope.workspace_id, "expected_version": expected_version}
        cached = self._claim(actor, "emergency.prealert.ack", idempotency_key, payload)
        if cached is not None:
            return cached
        if prealert.status != "PENDING":
            raise EmergencyConflictError("Only a pending pre-alert can be acknowledged", code="PREALERT_NOT_PENDING")
        prealert.status = "ACKNOWLEDGED"
        prealert.acknowledged_by_account_id = actor.account.id
        prealert.acknowledged_at = datetime.now(UTC)
        prealert.version += 1
        self.db.flush()
        response = self._prealert_response(prealert, correlation_id)
        self._complete(actor, "emergency.prealert.ack", idempotency_key, response, prealert.id)
        self._audit(actor, "EMERGENCY_PREALERT_ACKNOWLEDGED", "emergency_prealert", prealert.id, scope, correlation_id, request_id, {"state_after": prealert.status, "version": prealert.version})
        return response

    def create_handover(self, actor: NiamActor, *, handover_request_id: str, incident_id: str, workspace_id: str, receiving_facility_reference: str, minimal_summary: dict[str, Any], idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.handover.write")
        incident = self._incident_for_scope(incident_id, scope)
        if incident.status not in {"AT_DESTINATION", "TRANSPORTING"}:
            raise EmergencyStateError("Handover requires an active transport")
        allowed = {"diagnosis_context", "vital_summary", "interventions", "medications", "allergies_known", "pending_results", "risks", "care_needs"}
        summary = {key: value for key, value in minimal_summary.items() if key in allowed}
        payload = {"handover_request_id": handover_request_id, "incident_id": incident.id, "workspace_id": scope.workspace_id, "receiving_facility_reference": receiving_facility_reference, "minimal_summary": summary}
        cached = self._claim(actor, "emergency.handover.create", idempotency_key, payload)
        if cached is not None:
            return cached
        if self.db.query(CoreEmergencyHandover).filter(CoreEmergencyHandover.handover_request_id == handover_request_id).first() is not None:
            raise EmergencyConflictError("Handover request already exists", code="HANDOVER_EXISTS")
        handover = CoreEmergencyHandover(handover_request_id=handover_request_id.strip(), incident_id=incident.id, receiving_facility_reference=receiving_facility_reference.strip(), patient_person_id=incident.patient_person_id, temporary_subject_id=incident.temporary_subject_id, minimal_summary=summary, submitted_by_account_id=actor.account.id, status="SUBMITTED", version=1)
        self.db.add(handover)
        self.db.flush()
        self._add_outbox(actor, event_type="emergency.handover.submitted", aggregate_type="emergency_handover", aggregate_id=handover.id, payload={"handover_id": handover.id, "incident_id": incident.id, "delivery_mode": "SYNTHETIC_INTENT"})
        response = self._handover_response(handover, correlation_id)
        self._complete(actor, "emergency.handover.create", idempotency_key, response, handover.id)
        self._audit(actor, "EMERGENCY_HANDOVER_SUBMITTED", "emergency_handover", handover.id, scope, correlation_id, request_id, {"state_after": handover.status, "field_count": len(summary)})
        return response

    def acknowledge_handover(self, actor: NiamActor, *, handover_id: str, workspace_id: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.handover.write")
        handover = self.db.query(CoreEmergencyHandover).join(CoreEmergencyIncident, CoreEmergencyIncident.id == CoreEmergencyHandover.incident_id).filter(CoreEmergencyHandover.id == handover_id, CoreEmergencyIncident.organization_id == scope.organization_id, CoreEmergencyIncident.facility_id == scope.facility_id, CoreEmergencyIncident.workspace_id == scope.workspace_id).with_for_update().first()
        if handover is None:
            raise EmergencyNotFoundError("Handover was not found", code="HANDOVER_NOT_FOUND")
        self._assert_version(handover.version, expected_version)
        payload = {"resource_id": handover.id, "workspace_id": scope.workspace_id, "expected_version": expected_version}
        cached = self._claim(actor, "emergency.handover.ack", idempotency_key, payload)
        if cached is not None:
            return cached
        if handover.status != "SUBMITTED":
            raise EmergencyConflictError("Only a submitted handover can be acknowledged", code="HANDOVER_NOT_PENDING")
        handover.status = "ACKNOWLEDGED"
        handover.received_by_account_id = actor.account.id
        handover.acknowledged_at = datetime.now(UTC)
        handover.version += 1
        incident = self._incident_for_update(handover.incident_id, scope)
        require_transition("emergency-incident", incident.status, "HANDOVER_COMPLETE")
        incident.status = "HANDOVER_COMPLETE"
        incident.version += 1
        self.db.flush()
        response = self._handover_response(handover, correlation_id)
        self._complete(actor, "emergency.handover.ack", idempotency_key, response, handover.id)
        self._audit(actor, "EMERGENCY_HANDOVER_ACKNOWLEDGED", "emergency_handover", handover.id, scope, correlation_id, request_id, {"state_after": handover.status, "incident_status": incident.status, "version": handover.version})
        return response

    def create_epcr(self, actor: NiamActor, *, epcr_id: str, incident_id: str, workspace_id: str, chief_complaint: str, narrative: str, interventions: list[dict[str, Any]], destination_facility_reference: str | None, signature_evidence: dict[str, Any] | None, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.epcr.write")
        incident = self._incident_for_scope(incident_id, scope)
        payload = {"epcr_id": epcr_id, "incident_id": incident.id, "workspace_id": scope.workspace_id, "chief_complaint": chief_complaint, "narrative": narrative, "interventions": interventions, "destination_facility_reference": destination_facility_reference, "signature_evidence": signature_evidence}
        cached = self._claim(actor, "emergency.epcr.create", idempotency_key, payload)
        if cached is not None:
            return cached
        if self.db.query(CoreEmergencyEPCR).filter(CoreEmergencyEPCR.epcr_id == epcr_id, CoreEmergencyEPCR.version == 1).first() is not None:
            raise EmergencyConflictError("ePCR already exists", code="EPCR_EXISTS")
        epcr = CoreEmergencyEPCR(epcr_id=epcr_id.strip(), incident_id=incident.id, patient_person_id=incident.patient_person_id, temporary_subject_id=incident.temporary_subject_id, version=1, status="DRAFT", chief_complaint=chief_complaint.strip(), narrative=narrative.strip(), interventions=interventions, destination_facility_reference=destination_facility_reference.strip() if destination_facility_reference else None, signature_evidence=signature_evidence, authored_by_account_id=actor.account.id)
        self.db.add(epcr)
        self.db.flush()
        response = self._epcr_response(epcr, correlation_id)
        self._complete(actor, "emergency.epcr.create", idempotency_key, response, epcr.id)
        self._audit(actor, "EPCR_CREATED", "emergency_epcr", epcr.id, scope, correlation_id, request_id, {"state_after": epcr.status, "version": epcr.version})
        return response

    def sign_epcr(self, actor: NiamActor, *, epcr_id: str, workspace_id: str, expected_version: int, signature_evidence: dict[str, Any] | None, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.epcr.sign")
        epcr = self.db.query(CoreEmergencyEPCR).join(CoreEmergencyIncident, CoreEmergencyIncident.id == CoreEmergencyEPCR.incident_id).filter(CoreEmergencyEPCR.id == epcr_id, CoreEmergencyIncident.organization_id == scope.organization_id, CoreEmergencyIncident.facility_id == scope.facility_id, CoreEmergencyIncident.workspace_id == scope.workspace_id).with_for_update().first()
        if epcr is None:
            raise EmergencyNotFoundError("ePCR was not found", code="EPCR_NOT_FOUND")
        self._assert_version(epcr.version, expected_version)
        payload = {"resource_id": epcr.id, "workspace_id": scope.workspace_id, "expected_version": expected_version}
        cached = self._claim(actor, "emergency.epcr.sign", idempotency_key, payload)
        if cached is not None:
            return cached
        if epcr.status != "DRAFT":
            raise EmergencyConflictError("Signed ePCR is immutable", code="EPCR_IMMUTABLE")
        if signature_evidence is not None:
            epcr.signature_evidence = {key: value for key, value in signature_evidence.items() if key in {"method", "key_id", "signed_at", "synthetic"}}
        if not epcr.signature_evidence:
            raise EmergencyConflictError("Signature evidence is required", code="EPCR_SIGNATURE_REQUIRED", status_code=422)
        epcr.status = "SIGNED"
        epcr.signed_by_account_id = actor.account.id
        epcr.signed_at = datetime.now(UTC)
        epcr.version += 1
        self.db.flush()
        response = self._epcr_response(epcr, correlation_id)
        self._complete(actor, "emergency.epcr.sign", idempotency_key, response, epcr.id)
        self._audit(actor, "EPCR_SIGNED", "emergency_epcr", epcr.id, scope, correlation_id, request_id, {"state_after": epcr.status, "version": epcr.version})
        return response

    def reconcile_temporary_subject(self, actor: NiamActor, *, temporary_subject_id: str, workspace_id: str, resolution: str, person_id: str | None, reason: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.subject.write")
        subject = self.db.query(CoreEmergencyTemporarySubject).filter(CoreEmergencyTemporarySubject.id == temporary_subject_id, CoreEmergencyTemporarySubject.organization_id == scope.organization_id, CoreEmergencyTemporarySubject.facility_id == scope.facility_id, CoreEmergencyTemporarySubject.workspace_id == scope.workspace_id).with_for_update().first()
        if subject is None:
            raise EmergencyNotFoundError("Temporary subject was not found", code="TEMPORARY_SUBJECT_NOT_FOUND")
        self._assert_version(subject.version, expected_version)
        if subject.reconciliation_status == "MATCHED":
            raise EmergencyConflictError("A matched temporary subject requires an explicit correction workflow", code="RECONCILIATION_ALREADY_FINAL")
        if resolution == "MATCHED":
            if not person_id:
                raise EmergencyConflictError("A person reference is required for a matched resolution", code="RECONCILIATION_PERSON_REQUIRED", status_code=422)
            from app.identity.models.person import Person

            if self.db.query(Person).filter(Person.id == person_id, Person.is_active.is_(True)).first() is None:
                raise EmergencyNotFoundError("The reconciliation person was not found", code="RECONCILIATION_PERSON_NOT_FOUND")
        elif person_id:
            raise EmergencyConflictError("A person reference is not allowed unless resolution is MATCHED", code="RECONCILIATION_PERSON_INVALID", status_code=422)
        payload = {"resource_id": subject.id, "workspace_id": scope.workspace_id, "resolution": resolution, "person_id": person_id, "reason": reason.strip(), "expected_version": expected_version}
        cached = self._claim(actor, "emergency.subject.reconcile", idempotency_key, payload)
        if cached is not None:
            return cached
        before = subject.reconciliation_status
        subject.reconciliation_status = {"MATCHED": "MATCHED", "MULTIPLE_MATCHES": "PENDING_REVIEW", "NO_MATCH": "REJECTED", "REQUIRES_REVIEW": "PENDING_REVIEW"}[resolution]
        subject.reconciled_person_id = person_id if resolution == "MATCHED" else None
        subject.reconciliation_reason = reason.strip()
        subject.status = "RECONCILED" if resolution == "MATCHED" else "ACTIVE"
        subject.version += 1
        self.db.flush()
        response = self._subject_response(subject, correlation_id)
        response["resolution"] = resolution
        self._complete(actor, "emergency.subject.reconcile", idempotency_key, response, subject.id)
        self._audit(actor, "TEMPORARY_SUBJECT_RECONCILED", "emergency_temporary_subject", subject.id, scope, correlation_id, request_id, {"state_before": before, "state_after": subject.reconciliation_status, "resolution": resolution, "manual_review": resolution != "MATCHED", "version": subject.version})
        return response

    def amend_handover(self, actor: NiamActor, *, handover_id: str, workspace_id: str, handover_request_id: str, receiving_facility_reference: str, minimal_summary: dict[str, Any], amendment_reason: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.handover.write")
        original = self.db.query(CoreEmergencyHandover).join(CoreEmergencyIncident, CoreEmergencyIncident.id == CoreEmergencyHandover.incident_id).filter(CoreEmergencyHandover.id == handover_id, CoreEmergencyIncident.organization_id == scope.organization_id, CoreEmergencyIncident.facility_id == scope.facility_id, CoreEmergencyIncident.workspace_id == scope.workspace_id).with_for_update().first()
        if original is None:
            raise EmergencyNotFoundError("Handover was not found", code="HANDOVER_NOT_FOUND")
        self._assert_version(original.version, expected_version)
        if original.status == "CANCELLED":
            raise EmergencyStateError("A cancelled handover cannot be amended", code="HANDOVER_AMENDMENT_INVALID")
        summary = self._minimal_summary(minimal_summary)
        payload = {"resource_id": original.id, "handover_request_id": handover_request_id, "workspace_id": scope.workspace_id, "receiving_facility_reference": receiving_facility_reference, "minimal_summary": summary, "amendment_reason": amendment_reason.strip(), "expected_version": expected_version}
        cached = self._claim(actor, "emergency.handover.amend", idempotency_key, payload)
        if cached is not None:
            return cached
        amended = CoreEmergencyHandover(handover_request_id=handover_request_id.strip(), incident_id=original.incident_id, receiving_facility_reference=receiving_facility_reference.strip(), patient_person_id=original.patient_person_id, temporary_subject_id=original.temporary_subject_id, minimal_summary=summary, submitted_by_account_id=actor.account.id, status="SUBMITTED", version=1, supersedes_id=original.id, amendment_reason=amendment_reason.strip())
        self.db.add(amended)
        self.db.flush()
        self._add_outbox(actor, event_type="emergency.handover.amended", aggregate_type="emergency_handover", aggregate_id=amended.id, payload={"handover_id": amended.id, "supersedes_id": original.id, "delivery_mode": "SYNTHETIC_INTENT"})
        response = self._handover_response(amended, correlation_id)
        response["supersedes_id"] = original.id
        response["amendment_reason"] = amended.amendment_reason
        self._complete(actor, "emergency.handover.amend", idempotency_key, response, amended.id)
        self._audit(actor, "EMERGENCY_HANDOVER_AMENDED", "emergency_handover", amended.id, scope, correlation_id, request_id, {"supersedes_id": original.id, "state_after": amended.status, "amendment_reason": amended.amendment_reason})
        return response

    def amend_epcr(self, actor: NiamActor, *, epcr_id: str, workspace_id: str, chief_complaint: str, narrative: str, interventions: list[dict[str, Any]], destination_facility_reference: str | None, amendment_reason: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.epcr.write")
        original = self.db.query(CoreEmergencyEPCR).join(CoreEmergencyIncident, CoreEmergencyIncident.id == CoreEmergencyEPCR.incident_id).filter(CoreEmergencyEPCR.id == epcr_id, CoreEmergencyIncident.organization_id == scope.organization_id, CoreEmergencyIncident.facility_id == scope.facility_id, CoreEmergencyIncident.workspace_id == scope.workspace_id).with_for_update().first()
        if original is None:
            raise EmergencyNotFoundError("ePCR was not found", code="EPCR_NOT_FOUND")
        self._assert_version(original.version, expected_version)
        if original.status == "DRAFT":
            raise EmergencyConflictError("Only a signed ePCR can be amended", code="EPCR_AMENDMENT_REQUIRES_SIGNED")
        latest = self.db.query(CoreEmergencyEPCR).filter(CoreEmergencyEPCR.epcr_id == original.epcr_id).order_by(CoreEmergencyEPCR.version.desc()).with_for_update().first()
        if latest is None or latest.status == "DRAFT":
            raise EmergencyConflictError("An ePCR amendment is already pending signature", code="EPCR_AMENDMENT_PENDING")
        payload = {"resource_id": original.id, "epcr_id": original.epcr_id, "workspace_id": scope.workspace_id, "chief_complaint": chief_complaint, "narrative": narrative, "interventions": interventions, "destination_facility_reference": destination_facility_reference, "amendment_reason": amendment_reason.strip(), "expected_version": expected_version}
        cached = self._claim(actor, "emergency.epcr.amend", idempotency_key, payload)
        if cached is not None:
            return cached
        amended = CoreEmergencyEPCR(epcr_id=original.epcr_id, incident_id=original.incident_id, patient_person_id=original.patient_person_id, temporary_subject_id=original.temporary_subject_id, version=latest.version + 1, status="DRAFT", chief_complaint=chief_complaint.strip(), narrative=narrative.strip(), interventions=interventions, destination_facility_reference=destination_facility_reference.strip() if destination_facility_reference else None, signature_evidence=None, authored_by_account_id=actor.account.id, supersedes_id=latest.id, amendment_reason=amendment_reason.strip())
        self.db.add(amended)
        self.db.flush()
        response = self._epcr_response(amended, correlation_id)
        response["supersedes_id"] = latest.id
        response["amendment_reason"] = amended.amendment_reason
        self._complete(actor, "emergency.epcr.amend", idempotency_key, response, amended.id)
        self._audit(actor, "EPCR_AMENDED", "emergency_epcr", amended.id, scope, correlation_id, request_id, {"supersedes_id": latest.id, "state_after": amended.status, "version": amended.version, "amendment_reason": amended.amendment_reason})
        return response

    @staticmethod
    def _minimal_summary(data: dict[str, Any]) -> dict[str, Any]:
        allowed = {"diagnosis_context", "vital_summary", "interventions", "medications", "allergies_known", "pending_results", "risks", "care_needs", "devices", "timeline", "pending_actions"}
        return {key: value for key, value in data.items() if key in allowed}

    def _add_outbox(self, actor: NiamActor, *, event_type: str, aggregate_type: str, aggregate_id: str, payload: dict[str, Any]) -> None:
        event_key = f"{event_type}:{aggregate_id}"
        if self.db.query(CoreEmergencyOutbox).filter(CoreEmergencyOutbox.event_key == event_key).first() is None:
            self.db.add(CoreEmergencyOutbox(event_key=event_key, event_type=event_type, aggregate_type=aggregate_type, aggregate_id=aggregate_id, payload=payload, delivery_mode="SYNTHETIC_INTENT", status="PENDING", attempt_count=0))

    def request_break_glass(self, actor: NiamActor, *, request_id: str, workspace_id: str, patient_person_id: str, reason: str, purpose: str, resource_scope: dict[str, Any], duration_minutes: int, idempotency_key: str, correlation_id: str, request_id_header: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.break_glass.write")
        if not reason.strip():
            raise EmergencyStateError("Break-glass reason is required", code="BREAK_GLASS_REASON_REQUIRED")
        if duration_minutes < 1 or duration_minutes > 60:
            raise EmergencyStateError("Break-glass duration must be between 1 and 60 minutes", code="BREAK_GLASS_SCOPE_INVALID")
        if not resource_scope or not isinstance(resource_scope, dict):
            raise EmergencyStateError("Break-glass resource scope is required", code="BREAK_GLASS_SCOPE_INVALID")
        payload = {"request_id": request_id, "workspace_id": scope.workspace_id, "patient_person_id": patient_person_id, "purpose": purpose, "resource_scope": resource_scope, "duration_minutes": duration_minutes}
        cached = self._claim(actor, "emergency.break_glass.request", idempotency_key, payload)
        if cached is not None:
            return cached
        now = datetime.now(UTC)
        row = CoreEmergencyBreakGlass(request_id=request_id, patient_person_id=patient_person_id.strip(), organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, requested_by_account_id=actor.account.id, reason=reason.strip(), purpose=purpose.strip(), resource_scope=resource_scope, status="REQUESTED", version=1, requested_at=now, expires_at=now + timedelta(minutes=duration_minutes))
        self.db.add(row)
        self.db.flush()
        self.db.add(CoreEmergencyBreakGlassEvent(break_glass_id=row.id, event_key=f"{request_id}:ATTEMPTED", event_type="ATTEMPTED", actor_account_id=actor.account.id, payload={"reason": row.reason, "purpose": row.purpose, "resource_scope": resource_scope}))
        response = self._break_glass_response(row, correlation_id)
        self._complete(actor, "emergency.break_glass.request", idempotency_key, response, row.id)
        self._audit(actor, "BREAK_GLASS_ATTEMPTED", "emergency_break_glass", row.id, scope, correlation_id, request_id_header, {"status_after": row.status, "reason": row.reason, "resource_scope": resource_scope})
        return response

    def activate_break_glass(self, actor: NiamActor, *, break_glass_id: str, workspace_id: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.break_glass.activate")
        row = self.db.query(CoreEmergencyBreakGlass).filter(CoreEmergencyBreakGlass.id == break_glass_id, CoreEmergencyBreakGlass.organization_id == scope.organization_id, CoreEmergencyBreakGlass.facility_id == scope.facility_id, CoreEmergencyBreakGlass.workspace_id == scope.workspace_id).with_for_update().first()
        if row is None:
            raise EmergencyNotFoundError("Break-glass request was not found", code="BREAK_GLASS_NOT_FOUND")
        self._assert_version(row.version, expected_version)
        if row.status != "REQUESTED":
            raise EmergencyStateError("Break-glass request is not activatable", code="INVALID_STATE_TRANSITION")
        expiry_at = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=UTC)
        if expiry_at <= datetime.now(UTC):
            row.status = "EXPIRED"
            row.version += 1
            self.db.add(CoreEmergencyBreakGlassEvent(break_glass_id=row.id, event_key=f"{row.request_id}:EXPIRED", event_type="EXPIRED", actor_account_id=actor.account.id, payload={"reason": "expiry"}))
            raise EmergencyStateError("Break-glass request has expired", code="BREAK_GLASS_EXPIRED")
        payload = {"break_glass_id": row.id, "workspace_id": scope.workspace_id, "expected_version": expected_version}
        cached = self._claim(actor, "emergency.break_glass.activate", idempotency_key, payload)
        if cached is not None:
            return cached
        row.status = "ACTIVE"
        row.activated_at = datetime.now(UTC)
        row.version += 1
        self.db.add(CoreEmergencyBreakGlassEvent(break_glass_id=row.id, event_key=f"{row.request_id}:ACTIVATED", event_type="ACTIVATED", actor_account_id=actor.account.id, payload={"expires_at": row.expires_at.isoformat(), "resource_scope": row.resource_scope}))
        response = self._break_glass_response(row, correlation_id)
        self._complete(actor, "emergency.break_glass.activate", idempotency_key, response, row.id)
        self._audit(actor, "BREAK_GLASS_ACTIVATED", "emergency_break_glass", row.id, scope, correlation_id, request_id, {"status_before": "REQUESTED", "status_after": row.status, "expires_at": row.expires_at.isoformat()})
        return response

    def revoke_break_glass(self, actor: NiamActor, *, break_glass_id: str, workspace_id: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self._scope(actor, workspace_id, "clinical.emergency.break_glass.revoke")
        row = self.db.query(CoreEmergencyBreakGlass).filter(CoreEmergencyBreakGlass.id == break_glass_id, CoreEmergencyBreakGlass.organization_id == scope.organization_id, CoreEmergencyBreakGlass.facility_id == scope.facility_id, CoreEmergencyBreakGlass.workspace_id == scope.workspace_id).with_for_update().first()
        if row is None:
            raise EmergencyNotFoundError("Break-glass session was not found", code="BREAK_GLASS_NOT_FOUND")
        self._assert_version(row.version, expected_version)
        if row.status != "ACTIVE":
            raise EmergencyStateError("Only active break-glass sessions can be revoked", code="INVALID_STATE_TRANSITION")
        payload = {"break_glass_id": row.id, "workspace_id": scope.workspace_id, "expected_version": expected_version}
        cached = self._claim(actor, "emergency.break_glass.revoke", idempotency_key, payload)
        if cached is not None:
            return cached
        row.status = "REVOKED"
        row.revoked_at = datetime.now(UTC)
        row.version += 1
        self.db.add(CoreEmergencyBreakGlassEvent(break_glass_id=row.id, event_key=f"{row.request_id}:REVOKED", event_type="REVOKED", actor_account_id=actor.account.id, payload={"revoked_at": row.revoked_at.isoformat()}))
        response = self._break_glass_response(row, correlation_id)
        self._complete(actor, "emergency.break_glass.revoke", idempotency_key, response, row.id)
        self._audit(actor, "BREAK_GLASS_REVOKED", "emergency_break_glass", row.id, scope, correlation_id, request_id, {"status_before": "ACTIVE", "status_after": row.status})
        return response

    @staticmethod
    def _break_glass_response(row, correlation_id):
        return {"id": row.id, "request_id": row.request_id, "patient_person_id": row.patient_person_id, "status": row.status, "purpose": row.purpose, "resource_scope": row.resource_scope, "version": row.version, "expires_at": row.expires_at.isoformat(), "activated_at": row.activated_at.isoformat() if row.activated_at else None, "revoked_at": row.revoked_at.isoformat() if row.revoked_at else None, "correlation_id": correlation_id}

    def _scope(self, actor: NiamActor, workspace_id: str, permission: str):
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_permission(actor, scope, permission)
        return scope

    def _subject_for_scope(self, subject_id: str, scope):
        row = self.db.query(CoreEmergencyTemporarySubject).filter(CoreEmergencyTemporarySubject.id == subject_id, CoreEmergencyTemporarySubject.organization_id == scope.organization_id, CoreEmergencyTemporarySubject.facility_id == scope.facility_id, CoreEmergencyTemporarySubject.workspace_id == scope.workspace_id).first()
        if row is None:
            raise EmergencyNotFoundError("Temporary subject was not found", code="TEMPORARY_SUBJECT_NOT_FOUND")
        return row

    def _incident_for_scope(self, incident_id: str, scope):
        row = self.db.query(CoreEmergencyIncident).filter(CoreEmergencyIncident.id == incident_id, CoreEmergencyIncident.organization_id == scope.organization_id, CoreEmergencyIncident.facility_id == scope.facility_id, CoreEmergencyIncident.workspace_id == scope.workspace_id).first()
        if row is None:
            raise EmergencyNotFoundError("Emergency incident was not found", code="INCIDENT_NOT_FOUND")
        return row

    def _incident_for_update(self, incident_id: str, scope):
        row = self.db.query(CoreEmergencyIncident).filter(CoreEmergencyIncident.id == incident_id, CoreEmergencyIncident.organization_id == scope.organization_id, CoreEmergencyIncident.facility_id == scope.facility_id, CoreEmergencyIncident.workspace_id == scope.workspace_id).with_for_update().first()
        if row is None:
            raise EmergencyNotFoundError("Emergency incident was not found", code="INCIDENT_NOT_FOUND")
        return row

    @staticmethod
    def _assert_version(actual: int, expected: int) -> None:
        if expected < 1 or actual != expected:
            raise VersionConflictError("The emergency resource changed before this operation")

    @staticmethod
    def _minimal_vitals(data: dict[str, Any]) -> dict[str, Any]:
        allowed = {"heart_rate", "respiratory_rate", "oxygen_saturation", "blood_pressure_systolic", "blood_pressure_diastolic", "temperature", "gcs"}
        return {key: value for key, value in data.items() if key in allowed}

    def _claim(self, actor: NiamActor, operation: str, key: str, payload: dict[str, Any]):
        self.command_guard.actor_account_id = actor.account.id
        try:
            return self.command_guard.claim(operation=operation, idempotency_key=key, payload=payload)
        except ValueError as exc:
            raise AppointmentError(str(exc), status_code=400, code="IDEMPOTENCY_CONFLICT") from exc

    def _complete(self, actor: NiamActor, operation: str, key: str, response: dict[str, Any], resource_id: str) -> None:
        self.command_guard.actor_account_id = actor.account.id
        self.command_guard.complete(operation=operation, idempotency_key=key, resource_id=resource_id, response_body=response)

    def _audit(self, actor, event_type: str, target_type: str, target_id: str, scope, correlation_id: str, request_id: str | None, changes: dict[str, Any]) -> None:
        self.audit.record(AuditEventInput(event_type=event_type, category="clinical_emergency", action=event_type.lower(), actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type=target_type, target_id=target_id, decision="allow", request_id=request_id, correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="SENSITIVE", changes=changes))

    @staticmethod
    def _subject_response(row, correlation_id):
        return {"id": row.id, "temporary_subject_id": row.temporary_subject_id, "status": row.status, "reconciliation_status": row.reconciliation_status, "synthetic_label": row.synthetic_label, "version": row.version, "created_at": row.created_at.isoformat(), "correlation_id": correlation_id}

    @staticmethod
    def _incident_response(row, correlation_id):
        return {"id": row.id, "incident_id": row.incident_id, "subject_kind": row.subject_kind, "patient_person_id": row.patient_person_id, "temporary_subject_id": row.temporary_subject_id, "encounter_id": row.encounter_id, "status": row.status, "priority": row.priority, "chief_complaint": row.chief_complaint, "location_summary": row.location_summary, "version": row.version, "reported_at": row.reported_at.isoformat(), "closed_at": row.closed_at.isoformat() if row.closed_at else None, "correlation_id": correlation_id}

    @staticmethod
    def _triage_response(row, correlation_id):
        return {"id": row.id, "triage_id": row.triage_id, "incident_id": row.incident_id, "patient_person_id": row.patient_person_id, "temporary_subject_id": row.temporary_subject_id, "category": row.category, "clinician_summary": row.clinician_summary, "vital_snapshot": row.vital_snapshot, "assessed_at": row.assessed_at.isoformat(), "version": row.version, "correlation_id": correlation_id}

    @staticmethod
    def _dispatch_response(row, correlation_id):
        return {"id": row.id, "dispatch_request_id": row.dispatch_request_id, "incident_id": row.incident_id, "ambulance_reference": row.ambulance_reference, "crew_references": row.crew_references, "status": row.status, "version": row.version, "assigned_at": row.assigned_at.isoformat(), "completed_at": row.completed_at.isoformat() if row.completed_at else None, "correlation_id": correlation_id}

    @staticmethod
    def _prealert_response(row, correlation_id):
        return {"id": row.id, "prealert_request_id": row.prealert_request_id, "incident_id": row.incident_id, "destination_facility_reference": row.destination_facility_reference, "acuity": row.acuity, "estimated_arrival_minutes": row.estimated_arrival_minutes, "minimal_payload": row.minimal_payload, "delivery_mode": row.delivery_mode, "status": row.status, "version": row.version, "acknowledged_at": row.acknowledged_at.isoformat() if row.acknowledged_at else None, "correlation_id": correlation_id}

    @staticmethod
    def _handover_response(row, correlation_id):
        return {"id": row.id, "handover_request_id": row.handover_request_id, "incident_id": row.incident_id, "receiving_facility_reference": row.receiving_facility_reference, "patient_person_id": row.patient_person_id, "temporary_subject_id": row.temporary_subject_id, "minimal_summary": row.minimal_summary, "status": row.status, "version": row.version, "acknowledged_at": row.acknowledged_at.isoformat() if row.acknowledged_at else None, "correlation_id": correlation_id}

    @staticmethod
    def _epcr_response(row, correlation_id):
        return {"id": row.id, "epcr_id": row.epcr_id, "incident_id": row.incident_id, "patient_person_id": row.patient_person_id, "temporary_subject_id": row.temporary_subject_id, "status": row.status, "version": row.version, "chief_complaint": row.chief_complaint, "narrative": row.narrative, "interventions": row.interventions, "destination_facility_reference": row.destination_facility_reference, "signed_at": row.signed_at.isoformat() if row.signed_at else None, "correlation_id": correlation_id}


def _synthetic_reference() -> str:
    return f"TMP-{datetime.now(UTC):%Y%m%d%H%M%S}-{uuid.uuid4().hex[:10].upper()}"
