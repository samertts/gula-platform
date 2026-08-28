from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.clinical.appointments.service import (
    AppointmentError,
    IdempotencyConflictError,
    VersionConflictError,
)
from app.clinical.command_guard import CanonicalClinicalCommandGuard
from app.clinical.laboratory.advanced_models import CoreLabQualityControl
from app.clinical.laboratory.authorization import LaboratoryAuthorizationService
from app.clinical.laboratory.models import (
    CoreLabOrder,
    CoreLabOrderItem,
    CoreSpecimen,
)
from app.contracts.clinical_core import require_transition
from app.identity.api.workspaces import NiamActor
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService

from .models import CoreClinicalNotification, CoreCriticalResultEvent, CoreLabResult


class ResultNotFoundError(AppointmentError):
    code = "RESULT_NOT_FOUND"
    status_code = 404


class ResultStateConflictError(AppointmentError):
    code = "RESULT_STATE_CONFLICT"
    status_code = 409


class CriticalAckRequiredError(AppointmentError):
    code = "CRITICAL_ACK_REQUIRED"
    status_code = 409


class SeparationOfDutiesError(AppointmentError):
    code = "SEPARATION_OF_DUTIES_REQUIRED"
    status_code = 403


class CriticalResultNotFoundError(AppointmentError):
    code = "CRITICAL_RESULT_NOT_FOUND"
    status_code = 404


class QualityGateFailedError(AppointmentError):
    code = "QC_FAILED"
    status_code = 409


class ResultService:
    """Canonical result lifecycle. Analyzer/FHIR/notifications remain adapters, not domain writers."""

    def __init__(self, db):
        self.db = db
        self.authz = LaboratoryAuthorizationService(db)
        self.audit = SyncCanonicalAuditService(db)
        self.command_guard = CanonicalClinicalCommandGuard(db, actor_account_id=None)

    def create_result(self, actor: NiamActor, *, specimen_id: str, workspace_id: str, value_numeric: float | None, value_text: str | None, unit: str | None, reference_low: float | None, reference_high: float | None, source_message_id: str | None, provenance_type: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        specimen = self.db.query(CoreSpecimen).filter(CoreSpecimen.id == specimen_id, CoreSpecimen.organization_id == scope.organization_id, CoreSpecimen.facility_id == scope.facility_id, CoreSpecimen.workspace_id == scope.workspace_id).with_for_update().first()
        if specimen is None:
            raise ResultNotFoundError("Specimen not found")
        self.authz.require_result_operator(actor, scope, "clinical.result.write")
        if specimen.status != "VALIDATED":
            raise ResultStateConflictError("A result requires a verified specimen")
        item = self.db.query(CoreLabOrderItem).filter(CoreLabOrderItem.id == specimen.order_item_id, CoreLabOrderItem.lab_order_id == specimen.lab_order_id).first()
        order = self.db.query(CoreLabOrder).filter(CoreLabOrder.id == specimen.lab_order_id).first()
        if item is None or order is None:
            raise ResultNotFoundError("The specimen provenance chain is incomplete")
        payload = {"specimen_id": specimen.id, "workspace_id": scope.workspace_id, "value_numeric": value_numeric, "value_text": value_text, "unit": unit, "reference_low": reference_low, "reference_high": reference_high, "source_message_id": source_message_id, "provenance_type": provenance_type}
        cached = self._claim(actor, "result.create", idempotency_key, payload)
        if cached is not None:
            return cached
        if source_message_id:
            existing_source = self.db.query(CoreLabResult).filter(CoreLabResult.source_message_id == source_message_id).with_for_update().first()
            if existing_source is not None:
                if not self._same_result_payload(existing_source, payload):
                    raise IdempotencyConflictError("The source message was reused with a different result")
                response = self._result_response(existing_source, correlation_id)
                self._complete(actor, "result.create", idempotency_key, response, existing_source.id)
                return response
        result_id = self._new_id()
        abnormal_flag = self._flag(value_numeric, reference_low, reference_high)
        result = CoreLabResult(
            result_id=result_id,
            specimen_id=specimen.id,
            lab_order_id=order.id,
            order_item_id=item.id,
            encounter_id=order.encounter_id,
            patient_person_id=order.patient_person_id,
            laboratory_id=order.laboratory_id,
            organization_id=scope.organization_id,
            facility_id=scope.facility_id,
            workspace_id=scope.workspace_id,
            status="DRAFT",
            version=1,
            value_numeric=Decimal(str(value_numeric)) if value_numeric is not None else None,
            value_text=value_text.strip() if value_text else None,
            unit=unit.strip() if unit else None,
            reference_low=Decimal(str(reference_low)) if reference_low is not None else None,
            reference_high=Decimal(str(reference_high)) if reference_high is not None else None,
            abnormal_flag=abnormal_flag,
            test_code=item.test_code,
            test_name=item.test_name,
            provenance_type=provenance_type,
            source_message_id=source_message_id,
        )
        self.db.add(result)
        self.db.flush()
        if abnormal_flag in {"HIGH", "CRITICAL"}:
            critical = CoreCriticalResultEvent(
                result_id=result.id,
                patient_person_id=result.patient_person_id,
                organization_id=scope.organization_id,
                facility_id=scope.facility_id,
                workspace_id=scope.workspace_id,
                severity="CRITICAL" if abnormal_flag == "CRITICAL" else "HIGH",
                status="DETECTED",
                required_action="Authorized clinician review and patient-safety follow-up",
                version=1,
            )
            self.db.add(critical)
            self.db.flush()
            notification = CoreClinicalNotification(
                event_key=f"critical-result:{result.id}",
                recipient_account_id=order.ordering_provider_account_id,
                event_type="CRITICAL_RESULT_DETECTED",
                channel="SYNTHETIC",
                status="PENDING",
                payload={"result_id": result.id, "severity": critical.severity, "required_action": critical.required_action},
                attempt_count=0,
            )
            self.db.add(notification)
            self.db.flush()
        response = self._result_response(result, correlation_id)
        self._complete(actor, "result.create", idempotency_key, response, result.id)
        self._audit(actor, "RESULT_CREATED", "lab_result", result.id, scope, correlation_id, request_id, {"state_before": None, "state_after": "DRAFT", "version_after": result.version, "provenance_type": provenance_type, "critical": abnormal_flag in {"HIGH", "CRITICAL"}})
        return response

    def technical_validate(self, actor: NiamActor, *, result_id: str, workspace_id: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        return self._transition_result(actor, result_id=result_id, workspace_id=workspace_id, target="TECHNICALLY_VALIDATED", expected_version=expected_version, idempotency_key=idempotency_key, correlation_id=correlation_id, request_id=request_id, permission="clinical.result.validate_technical", event_type="TECHNICAL_VALIDATION")

    def clinical_validate(self, actor: NiamActor, *, result_id: str, workspace_id: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        result = self._result_for_update(result_id, scope)
        self.authz.require_result_operator(actor, scope, "clinical.result.validate_clinical")
        self._assert_version(result.version, expected_version)
        if result.technical_validated_by == actor.account.id:
            raise SeparationOfDutiesError("Technical and clinical validation require separate authorized actors")
        return self._transition_result_after_loaded(actor, result, scope, "CLINICALLY_VALIDATED", expected_version, idempotency_key, correlation_id, request_id, "clinical.result.validate_clinical", "CLINICAL_VALIDATION")

    def release(self, actor: NiamActor, *, result_id: str, workspace_id: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        result = self._result_for_update(result_id, scope)
        self.authz.require_result_operator(actor, scope, "clinical.result.release")
        self._assert_version(result.version, expected_version)
        critical = self.db.query(CoreCriticalResultEvent).filter(CoreCriticalResultEvent.result_id == result.id).with_for_update().first()
        if critical is not None and critical.status not in {"ACKNOWLEDGED", "ACTIONED", "CLOSED"}:
            raise CriticalAckRequiredError("Critical result acknowledgement is required before release")
        if result.provenance_type in {"ANALYZER", "IMPORTED_SYNTHETIC"}:
            qc = self.db.query(CoreLabQualityControl).filter_by(result_id=result.id).with_for_update().first()
            if qc is None or qc.status not in {"PASS", "OVERRIDDEN"}:
                raise QualityGateFailedError("QC pass or authorized override is required before release")
        return self._transition_result_after_loaded(actor, result, scope, "RELEASED", expected_version, idempotency_key, correlation_id, request_id, "clinical.result.release", "RESULT_RELEASED", released=True)

    def acknowledge_critical(self, actor: NiamActor, *, result_id: str, workspace_id: str, expected_version: int, reason: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        result = self._result_for_scope(result_id, scope)
        self.authz.require_result_operator(actor, scope, "clinical.critical.acknowledge")
        critical = self.db.query(CoreCriticalResultEvent).filter(CoreCriticalResultEvent.result_id == result.id).with_for_update().first()
        if critical is None:
            raise CriticalResultNotFoundError("No critical event exists for this result")
        self._assert_version(critical.version, expected_version)
        if critical.status not in {"DETECTED", "NOTIFIED", "ESCALATED"}:
            raise ResultStateConflictError("The critical event is not awaiting acknowledgement")
        cached = self._claim(actor, "critical.acknowledge", idempotency_key, {"resource_id": critical.id, "workspace_id": scope.workspace_id, "expected_version": expected_version, "reason": reason.strip()})
        if cached is not None:
            return cached
        before = critical.status
        critical.status = "ACKNOWLEDGED"
        critical.acknowledged_by = actor.account.id
        critical.acknowledged_at = datetime.now(UTC)
        critical.version += 1
        self.db.flush()
        response = {"id": result.id, "result_id": result.id, "critical_event_id": critical.id, "status": critical.status, "version": critical.version, "correlation_id": correlation_id}
        self._complete(actor, "critical.acknowledge", idempotency_key, response, critical.id)
        self._audit(actor, "CRITICAL_ACKNOWLEDGED", "critical_result", critical.id, scope, correlation_id, request_id, {"state_before": before, "state_after": critical.status, "version_before": expected_version, "version_after": critical.version, "reason": reason.strip()})
        return response

    def amend(self, actor: NiamActor, *, result_id: str, workspace_id: str, expected_version: int, reason: str, value_numeric: float | None, value_text: str | None, unit: str | None, reference_low: float | None, reference_high: float | None, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        previous = self._result_for_update(result_id, scope)
        self.authz.require_result_operator(actor, scope, "clinical.result.amend")
        self._assert_version(previous.version, expected_version)
        if previous.status != "RELEASED":
            raise ResultStateConflictError("Only a released result may be amended")
        payload = {"resource_id": previous.id, "workspace_id": scope.workspace_id, "expected_version": expected_version, "reason": reason.strip(), "value_numeric": value_numeric, "value_text": value_text, "unit": unit, "reference_low": reference_low, "reference_high": reference_high}
        cached = self._claim(actor, "result.amend", idempotency_key, payload)
        if cached is not None:
            return cached
        try:
            require_transition("result", previous.status, "CORRECTED")
        except ValueError as exc:
            raise ResultStateConflictError("The released result cannot be amended") from exc
        previous.status = "CORRECTED"
        previous.version += 1
        new_result = CoreLabResult(
            result_id=previous.result_id,
            specimen_id=previous.specimen_id,
            lab_order_id=previous.lab_order_id,
            order_item_id=previous.order_item_id,
            encounter_id=previous.encounter_id,
            patient_person_id=previous.patient_person_id,
            laboratory_id=previous.laboratory_id,
            organization_id=scope.organization_id,
            facility_id=scope.facility_id,
            workspace_id=scope.workspace_id,
            status="DRAFT",
            version=previous.version,
            value_numeric=Decimal(str(value_numeric)) if value_numeric is not None else None,
            value_text=value_text.strip() if value_text else None,
            unit=unit.strip() if unit else None,
            reference_low=Decimal(str(reference_low)) if reference_low is not None else None,
            reference_high=Decimal(str(reference_high)) if reference_high is not None else None,
            abnormal_flag=self._flag(value_numeric, reference_low, reference_high),
            test_code=previous.test_code,
            test_name=previous.test_name,
            provenance_type="MANUAL",
            supersedes_id=previous.id,
            amendment_reason=reason.strip(),
        )
        self.db.add(new_result)
        self.db.flush()
        response = self._result_response(new_result, correlation_id)
        self._complete(actor, "result.amend", idempotency_key, response, new_result.id)
        self._audit(actor, "RESULT_CORRECTED", "lab_result", previous.id, scope, correlation_id, request_id, {"state_before": "RELEASED", "state_after": "CORRECTED", "version_before": expected_version, "version_after": previous.version})
        self._audit(actor, "RESULT_AMENDED", "lab_result", new_result.id, scope, correlation_id, request_id, {"state_before": None, "state_after": "DRAFT", "supersedes_id": previous.id, "version": new_result.version, "reason": reason.strip()})
        return response

    def get_result(self, actor: NiamActor, *, result_id: str, workspace_id: str, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        result = self._result_for_scope(result_id, scope)
        order = self.db.query(CoreLabOrder).filter(CoreLabOrder.id == result.lab_order_id).first()
        if order is None:
            raise ResultNotFoundError("Result provenance is incomplete")
        if scope.actor_person_id == result.patient_person_id:
            if result.status != "RELEASED":
                raise ResultStateConflictError("This result is not released for citizen access")
        else:
            self.authz.require_result_operator(actor, scope, "clinical.result.read")
        return self._result_response(result, correlation_id)

    def _transition_result(self, actor, *, result_id, workspace_id, target, expected_version, idempotency_key, correlation_id, request_id, permission, event_type):
        scope = self.authz.resolve_scope(actor, workspace_id)
        result = self._result_for_update(result_id, scope)
        self.authz.require_result_operator(actor, scope, permission)
        self._assert_version(result.version, expected_version)
        return self._transition_result_after_loaded(actor, result, scope, target, expected_version, idempotency_key, correlation_id, request_id, permission, event_type)

    def _transition_result_after_loaded(self, actor, result, scope, target, expected_version, idempotency_key, correlation_id, request_id, operation, event_type, released=False):
        operation_key = operation
        cached = self._claim(actor, operation_key, idempotency_key, {"resource_id": result.id, "workspace_id": scope.workspace_id, "expected_version": expected_version})
        if cached is not None:
            return cached
        before = result.status
        try:
            require_transition("result", before, target)
        except ValueError as exc:
            raise ResultStateConflictError("The result transition is not allowed") from exc
        result.status = target
        result.version += 1
        now = datetime.now(UTC)
        if target == "TECHNICALLY_VALIDATED":
            result.technical_validated_by = actor.account.id
            result.technical_validated_at = now
        elif target == "CLINICALLY_VALIDATED":
            result.clinically_validated_by = actor.account.id
            result.clinically_validated_at = now
        elif released:
            result.released_at = now
        self.db.flush()
        response = self._result_response(result, correlation_id)
        self._complete(actor, operation_key, idempotency_key, response, result.id)
        self._audit(actor, event_type, "lab_result", result.id, scope, correlation_id, request_id, {"state_before": before, "state_after": target, "version_before": expected_version, "version_after": result.version})
        return response

    def _result_for_scope(self, result_id, scope):
        result = self.db.query(CoreLabResult).filter(CoreLabResult.id == result_id, CoreLabResult.organization_id == scope.organization_id, CoreLabResult.facility_id == scope.facility_id, CoreLabResult.workspace_id == scope.workspace_id).first()
        if result is None:
            raise ResultNotFoundError("Result not found")
        return result

    def _result_for_update(self, result_id, scope):
        result = self.db.query(CoreLabResult).filter(CoreLabResult.id == result_id, CoreLabResult.organization_id == scope.organization_id, CoreLabResult.facility_id == scope.facility_id, CoreLabResult.workspace_id == scope.workspace_id).with_for_update().first()
        if result is None:
            raise ResultNotFoundError("Result not found")
        return result

    @staticmethod
    def _assert_version(actual, expected):
        if expected < 1 or actual != expected:
            raise VersionConflictError("The resource changed before this operation")

    @staticmethod
    def _flag(value, low, high):
        if value is None or low is None or high is None:
            return None
        if value < low:
            return "LOW"
        if value > high:
            return "HIGH"
        return "NORMAL"

    @staticmethod
    def _new_id():
        return str(uuid.uuid4()).replace("-", "").upper()[:26]

    @staticmethod
    def _same_result_payload(result, payload):
        return result.specimen_id == payload["specimen_id"] and (float(result.value_numeric) if result.value_numeric is not None else None) == payload["value_numeric"] and result.value_text == payload["value_text"]

    def _claim(self, actor, operation, key, payload):
        self.command_guard.actor_account_id = actor.account.id
        try:
            return self.command_guard.claim(operation=operation, idempotency_key=key, payload=payload)
        except ValueError as exc:
            raise AppointmentError(str(exc), status_code=400, code="VALIDATION_ERROR") from exc

    def _complete(self, actor, operation, key, response, resource_id):
        self.command_guard.actor_account_id = actor.account.id
        self.command_guard.complete(operation=operation, idempotency_key=key, resource_id=resource_id, response_body=response)

    def _audit(self, actor, event_type, target_type, target_id, scope, correlation_id, request_id, changes):
        self.audit.record(AuditEventInput(event_type=event_type, category="clinical_results", action=event_type.lower(), actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type=target_type, target_id=target_id, decision="allow", request_id=request_id, correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="SENSITIVE", changes=changes))

    @staticmethod
    def _result_response(result, correlation_id):
        return {"id": result.id, "result_id": result.result_id, "specimen_id": result.specimen_id, "lab_order_id": result.lab_order_id, "order_item_id": result.order_item_id, "encounter_id": result.encounter_id, "patient_person_id": result.patient_person_id, "laboratory_id": result.laboratory_id, "organization_id": result.organization_id, "facility_id": result.facility_id, "workspace_id": result.workspace_id, "status": result.status, "version": result.version, "value_numeric": float(result.value_numeric) if result.value_numeric is not None else None, "value_text": result.value_text, "unit": result.unit, "reference_low": float(result.reference_low) if result.reference_low is not None else None, "reference_high": float(result.reference_high) if result.reference_high is not None else None, "abnormal_flag": result.abnormal_flag, "test_code": result.test_code, "test_name": result.test_name, "provenance_type": result.provenance_type, "source_message_id": result.source_message_id, "technical_validated_by": result.technical_validated_by, "clinically_validated_by": result.clinically_validated_by, "released_at": result.released_at.isoformat() if result.released_at else None, "supersedes_id": result.supersedes_id, "amendment_reason": result.amendment_reason, "correlation_id": correlation_id}
