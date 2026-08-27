from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import Any

from app.clinical.appointments.authorization import (
    AppointmentAuthorizationError,
    AppointmentAuthorizationService,
)
from app.clinical.appointments.service import AppointmentError, VersionConflictError
from app.clinical.command_guard import CanonicalClinicalCommandGuard
from app.contracts.clinical_core import require_transition
from app.identity.api.workspaces import NiamActor
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService

from .adapters import SyntheticImagingAdapter
from .models import (
    CoreImagingCriticalEvent,
    CoreImagingInstance,
    CoreImagingOrder,
    CoreImagingReport,
    CoreImagingStudy,
)


class ImagingNotFoundError(AppointmentError):
    code = "IMAGING_RESOURCE_NOT_FOUND"
    status_code = 404


class ImagingStateConflictError(AppointmentError):
    code = "IMAGING_STATE_CONFLICT"
    status_code = 409


class ImagingStudyNotFoundError(ImagingNotFoundError):
    code = "STUDY_NOT_FOUND"


class ImagingReportNotFoundError(ImagingNotFoundError):
    code = "REPORT_NOT_FOUND"


class DicomDuplicateError(ImagingStateConflictError):
    code = "DICOM_DUPLICATE"


class DicomInvalidError(AppointmentError):
    code = "DICOM_INVALID"
    status_code = 422


class ReportImmutableError(ImagingStateConflictError):
    code = "REPORT_ALREADY_FINAL"


class CanonicalImagingService:
    """Canonical imaging metadata/report workflow with synthetic adapters only."""

    def __init__(self, db):
        self.db = db
        self.authz = AppointmentAuthorizationService(db)
        self.audit = SyncCanonicalAuditService(db)
        self.command_guard = CanonicalClinicalCommandGuard(db, actor_account_id=None)
        self.synthetic_adapter = SyntheticImagingAdapter()

    def create_order(self, actor: NiamActor, *, encounter_id: str, workspace_id: str, modality: str, body_part: str | None, clinical_indication: str | None, priority: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        encounter = self._encounter_for_scope(encounter_id, scope)
        if encounter.status not in {"IN_PROGRESS", "COMPLETED"}:
            raise ImagingStateConflictError("Imaging orders require an active or completed encounter", code="ENCOUNTER_NOT_ELIGIBLE")
        if actor.account.id != encounter.provider_account_id:
            raise AppointmentAuthorizationError("ordering_provider_object_mismatch", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        self.authz.require_permission(actor, scope, "clinical.imaging.order")
        payload = {"encounter_id": encounter.id, "workspace_id": scope.workspace_id, "modality": modality, "body_part": body_part, "priority": priority}
        cached = self._claim(actor, "imaging.order.create", idempotency_key, payload)
        if cached is not None:
            return cached
        order_id = _core_id()
        order = CoreImagingOrder(id=order_id, order_id=order_id, encounter_id=encounter.id, patient_person_id=encounter.patient_person_id, ordering_provider_account_id=actor.account.id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, accession_number=f"IMG-{datetime.now(UTC):%Y%m%d}-{secrets.token_hex(4).upper()}", modality=modality.strip(), body_part=body_part.strip() if body_part else None, clinical_indication=clinical_indication.strip() if clinical_indication else None, priority=priority, status="DRAFT", version=1)
        self.db.add(order)
        self.db.flush()
        response = self._order_response(order, correlation_id)
        self._complete(actor, "imaging.order.create", idempotency_key, response, order.id)
        self._audit(actor, "IMAGING_ORDER_CREATED", "imaging_order", order.id, scope, correlation_id, request_id, {"status_after": order.status, "accession_number": order.accession_number})
        return response

    def transition_order(self, actor: NiamActor, *, order_id: str, workspace_id: str, target: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        order = self._order_for_update(order_id, scope)
        self.authz.require_permission(actor, scope, "clinical.imaging.order")
        self._assert_version(order.version, expected_version)
        payload = {"resource_id": order.id, "workspace_id": scope.workspace_id, "target": target, "expected_version": expected_version}
        operation = f"imaging.order.{target.lower()}"
        cached = self._claim(actor, operation, idempotency_key, payload)
        if cached is not None:
            return cached
        before = order.status
        try:
            require_transition("imaging-order", before, target)
        except ValueError as exc:
            raise ImagingStateConflictError("The imaging order transition is not allowed", code="ORDER_STATE_CONFLICT") from exc
        order.status = target
        order.version += 1
        self.db.flush()
        response = self._order_response(order, correlation_id)
        self._complete(actor, operation, idempotency_key, response, order.id)
        self._audit(actor, f"IMAGING_ORDER_{target}", "imaging_order", order.id, scope, correlation_id, request_id, {"status_before": before, "status_after": target, "version_after": order.version})
        return response

    def ingest_study(self, actor: NiamActor, *, order_id: str, workspace_id: str, study_instance_uid: str, accession_number: str, modality: str, source_message_id: str, provenance_type: str, study_description: str | None, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_permission(actor, scope, "clinical.imaging.ingest")
        order = self._order_for_scope(order_id, scope)
        if order.status not in {"PLACED", "SCHEDULED", "IN_PROGRESS"}:
            raise ImagingStateConflictError("Study ingestion requires a placed or active order", code="ORDER_NOT_INGESTIBLE")
        if accession_number != order.accession_number or modality.strip() != order.modality:
            raise DicomInvalidError("DICOM metadata does not exactly match the server order")
        adapter_payload = self.synthetic_adapter.retrieve_metadata(source_message_id=source_message_id, study_instance_uid=study_instance_uid)
        payload = {"order_id": order.id, "workspace_id": scope.workspace_id, "study_instance_uid": study_instance_uid, "accession_number": accession_number, "source_message_id": source_message_id, "provenance_type": provenance_type}
        cached = self._claim(actor, "imaging.study.ingest", idempotency_key, payload)
        if cached is not None:
            return cached
        duplicate = self.db.query(CoreImagingStudy).filter((CoreImagingStudy.study_instance_uid == study_instance_uid) | (CoreImagingStudy.source_message_id == source_message_id)).first()
        if duplicate is not None:
            raise DicomDuplicateError("DICOM study or source message has already been ingested")
        study_id = _core_id()
        study = CoreImagingStudy(id=study_id, study_id=study_id, order_id=order.id, patient_person_id=order.patient_person_id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, study_instance_uid=study_instance_uid.strip(), accession_number=accession_number.strip(), modality=modality.strip(), study_description=study_description.strip() if study_description else None, status="RECEIVED", provenance_type=provenance_type, source_message_id=source_message_id.strip(), version=1, metadata_=adapter_payload)
        self.db.add(study)
        self.db.flush()
        response = self._study_response(study, correlation_id)
        self._complete(actor, "imaging.study.ingest", idempotency_key, response, study.id)
        self._audit(actor, "IMAGING_STUDY_RECEIVED", "imaging_study", study.id, scope, correlation_id, request_id, {"status_after": study.status, "provenance_type": study.provenance_type, "source_message_id": source_message_id})
        return response

    def transition_study(self, actor: NiamActor, *, study_id: str, workspace_id: str, target: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None, quarantine_reason: str | None = None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        study = self._study_for_update(study_id, scope)
        self.authz.require_permission(actor, scope, "clinical.imaging.ingest")
        self._assert_version(study.version, expected_version)
        if target == "QUARANTINED" and not quarantine_reason:
            raise DicomInvalidError("A quarantine reason is required")
        payload = {"resource_id": study.id, "workspace_id": scope.workspace_id, "target": target, "expected_version": expected_version, "quarantine_reason": quarantine_reason}
        operation = f"imaging.study.{target.lower()}"
        cached = self._claim(actor, operation, idempotency_key, payload)
        if cached is not None:
            return cached
        before = study.status
        try:
            require_transition("imaging-study", before, target)
        except ValueError as exc:
            raise ImagingStateConflictError("The imaging study transition is not allowed", code="STUDY_STATE_CONFLICT") from exc
        study.status = target
        study.version += 1
        if target == "QUARANTINED":
            study.quarantine_reason = quarantine_reason.strip() if quarantine_reason else None
        if target == "COMPLETED":
            study.completed_at = datetime.now(UTC)
        self.db.flush()
        response = self._study_response(study, correlation_id)
        self._complete(actor, operation, idempotency_key, response, study.id)
        self._audit(actor, f"IMAGING_STUDY_{target}", "imaging_study", study.id, scope, correlation_id, request_id, {"status_before": before, "status_after": target, "version_after": study.version, "quarantine_reason": quarantine_reason})
        return response

    def ingest_instance(self, actor: NiamActor, *, study_id: str, workspace_id: str, series_instance_uid: str, sop_instance_uid: str, source_message_id: str, object_reference: str, checksum: str, file_size_bytes: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_permission(actor, scope, "clinical.imaging.ingest")
        study = self._study_for_scope(study_id, scope)
        if study.status == "QUARANTINED":
            raise ImagingStateConflictError("Quarantined studies cannot receive instances", code="STUDY_QUARANTINED")
        if object_reference.startswith(("http://", "https://")):
            raise DicomInvalidError("Public image URLs are not accepted")
        if file_size_bytes <= 0 or not checksum.strip():
            raise DicomInvalidError("DICOM object metadata is invalid")
        payload = {"study_id": study.id, "workspace_id": scope.workspace_id, "series_instance_uid": series_instance_uid, "sop_instance_uid": sop_instance_uid, "source_message_id": source_message_id, "checksum": checksum, "file_size_bytes": file_size_bytes}
        cached = self._claim(actor, "imaging.instance.ingest", idempotency_key, payload)
        if cached is not None:
            return cached
        if self.db.query(CoreImagingInstance).filter((CoreImagingInstance.sop_instance_uid == sop_instance_uid) | (CoreImagingInstance.source_message_id == source_message_id)).first() is not None:
            raise DicomDuplicateError("DICOM instance or source message has already been ingested")
        new_series = self.db.query(CoreImagingInstance.id).filter(CoreImagingInstance.study_id == study.id, CoreImagingInstance.series_instance_uid == series_instance_uid.strip()).first() is None
        instance = CoreImagingInstance(study_id=study.id, series_instance_uid=series_instance_uid.strip(), sop_instance_uid=sop_instance_uid.strip(), patient_person_id=study.patient_person_id, provenance_type=study.provenance_type, source_message_id=source_message_id.strip(), object_reference=object_reference.strip(), checksum=checksum.strip(), file_size_bytes=file_size_bytes)
        self.db.add(instance)
        study.instance_count += 1
        if new_series:
            study.series_count += 1
        study.version += 1
        self.db.flush()
        response = {"id": instance.id, "study_id": instance.study_id, "series_instance_uid": instance.series_instance_uid, "sop_instance_uid": instance.sop_instance_uid, "provenance_type": instance.provenance_type, "file_size_bytes": instance.file_size_bytes, "correlation_id": correlation_id}
        self._complete(actor, "imaging.instance.ingest", idempotency_key, response, instance.id)
        self._audit(actor, "DICOM_INSTANCE_INGESTED", "imaging_instance", instance.id, scope, correlation_id, request_id, {"study_id": study.id, "sop_instance_uid": instance.sop_instance_uid, "size": file_size_bytes})
        return response

    def create_report(self, actor: NiamActor, *, study_id: str, workspace_id: str, findings: str | None, impression: str | None, critical: bool, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_permission(actor, scope, "clinical.imaging.report.write")
        study = self._study_for_scope(study_id, scope)
        if study.status != "COMPLETED":
            raise ImagingStateConflictError("A report requires a completed study", code="STUDY_NOT_COMPLETE")
        order = self._order_for_scope(study.order_id, scope)
        payload = {"study_id": study.id, "workspace_id": scope.workspace_id, "findings": findings, "impression": impression, "critical": critical}
        cached = self._claim(actor, "imaging.report.create", idempotency_key, payload)
        if cached is not None:
            return cached
        report_id = _core_id()
        report = CoreImagingReport(id=report_id, report_id=report_id, study_id=study.id, patient_person_id=study.patient_person_id, ordering_provider_account_id=order.ordering_provider_account_id, radiologist_account_id=actor.account.id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, version=1, status="DRAFT", findings=findings.strip() if findings else None, impression=impression.strip() if impression else None, critical=1 if critical else 0)
        self.db.add(report)
        self.db.flush()
        response = self._report_response(report, correlation_id)
        self._complete(actor, "imaging.report.create", idempotency_key, response, report.id)
        self._audit(actor, "IMAGING_REPORT_CREATED", "imaging_report", report.id, scope, correlation_id, request_id, {"status_after": report.status, "study_id": study.id})
        return response

    def sign_report(self, actor: NiamActor, *, report_id: str, workspace_id: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        report = self._report_for_update(report_id, scope)
        self._require_radiologist(actor, scope, report)
        self.authz.require_permission(actor, scope, "clinical.imaging.report.sign")
        self._assert_version(report.version, expected_version)
        payload = {"resource_id": report.id, "workspace_id": scope.workspace_id, "expected_version": expected_version}
        cached = self._claim(actor, "imaging.report.sign", idempotency_key, payload)
        if cached is not None:
            return cached
        if report.status != "DRAFT":
            raise ReportImmutableError("Only a draft report can be signed")
        require_transition("imaging-report", report.status, "SIGNED")
        report.status = "SIGNED"
        report.signed_at = datetime.now(UTC)
        report.version += 1
        self.db.flush()
        response = self._report_response(report, correlation_id)
        self._complete(actor, "imaging.report.sign", idempotency_key, response, report.id)
        self._audit(actor, "IMAGING_REPORT_SIGNED", "imaging_report", report.id, scope, correlation_id, request_id, {"status_after": report.status, "content_immutable": True})
        return response

    def release_report(self, actor: NiamActor, *, report_id: str, workspace_id: str, expected_version: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        report = self._report_for_update(report_id, scope)
        self._require_radiologist(actor, scope, report)
        self.authz.require_permission(actor, scope, "clinical.imaging.report.release")
        self._assert_version(report.version, expected_version)
        payload = {"resource_id": report.id, "workspace_id": scope.workspace_id, "expected_version": expected_version}
        cached = self._claim(actor, "imaging.report.release", idempotency_key, payload)
        if cached is not None:
            return cached
        if report.status != "SIGNED":
            raise ReportImmutableError("Only a signed report can be released")
        require_transition("imaging-report", report.status, "RELEASED")
        report.status = "RELEASED"
        report.released_at = datetime.now(UTC)
        report.version += 1
        self.db.flush()
        if report.critical:
            critical = CoreImagingCriticalEvent(report_id=report.id, patient_person_id=report.patient_person_id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, status="DETECTED", severity="CRITICAL", required_action="Review released critical imaging finding", version=1)
            self.db.add(critical)
            from app.clinical.results.models import CoreClinicalNotification
            self.db.add(CoreClinicalNotification(event_key=f"imaging-critical:{report.id}", recipient_account_id=report.ordering_provider_account_id, event_type="IMAGING_CRITICAL_FINDING", channel="SYNTHETIC", status="PENDING", payload={"report_id": report.id, "study_id": report.study_id, "severity": "CRITICAL"}, attempt_count=0))
            self.db.flush()
        response = self._report_response(report, correlation_id)
        self._complete(actor, "imaging.report.release", idempotency_key, response, report.id)
        self._audit(actor, "IMAGING_REPORT_RELEASED", "imaging_report", report.id, scope, correlation_id, request_id, {"status_after": report.status, "critical": bool(report.critical), "notification": "SYNTHETIC" if report.critical else None})
        return response

    def amend_report(self, actor: NiamActor, *, report_id: str, workspace_id: str, expected_version: int, reason: str, findings: str | None, impression: str | None, critical: bool, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        original = self._report_for_update(report_id, scope)
        self._require_radiologist(actor, scope, original)
        self.authz.require_permission(actor, scope, "clinical.imaging.report.amend")
        self._assert_version(original.version, expected_version)
        if original.status not in {"SIGNED", "RELEASED"}:
            raise ReportImmutableError("Only a signed or released report can be amended")
        payload = {"resource_id": original.id, "workspace_id": scope.workspace_id, "expected_version": expected_version, "reason": reason.strip(), "critical": critical}
        cached = self._claim(actor, "imaging.report.amend", idempotency_key, payload)
        if cached is not None:
            return cached
        before = original.status
        original.status = "AMENDED"
        amended = CoreImagingReport(id=_core_id(), report_id=original.report_id, study_id=original.study_id, patient_person_id=original.patient_person_id, ordering_provider_account_id=original.ordering_provider_account_id, radiologist_account_id=actor.account.id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, version=original.version + 1, status="DRAFT", findings=findings.strip() if findings else None, impression=impression.strip() if impression else None, critical=1 if critical else 0, supersedes_id=original.id, amendment_reason=reason.strip())
        self.db.add(amended)
        self.db.flush()
        response = self._report_response(amended, correlation_id)
        self._complete(actor, "imaging.report.amend", idempotency_key, response, amended.id)
        self._audit(actor, "IMAGING_REPORT_AMENDED", "imaging_report", amended.id, scope, correlation_id, request_id, {"supersedes_id": original.id, "state_before": before, "state_after": original.status, "version_after": amended.version, "reason": reason.strip()})
        return response

    def acknowledge_critical(self, actor: NiamActor, *, report_id: str, workspace_id: str, expected_version: int, reason: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        event = self.db.query(CoreImagingCriticalEvent).filter(CoreImagingCriticalEvent.report_id == report_id, CoreImagingCriticalEvent.organization_id == scope.organization_id, CoreImagingCriticalEvent.facility_id == scope.facility_id, CoreImagingCriticalEvent.workspace_id == scope.workspace_id).with_for_update().first()
        if event is None:
            raise ImagingNotFoundError("Critical imaging event was not found", code="CRITICAL_FINDING_NOT_FOUND")
        self.authz.require_permission(actor, scope, "clinical.imaging.critical_ack")
        self._assert_version(event.version, expected_version)
        payload = {"resource_id": event.id, "workspace_id": scope.workspace_id, "expected_version": expected_version, "reason": reason.strip()}
        cached = self._claim(actor, "imaging.critical.acknowledge", idempotency_key, payload)
        if cached is not None:
            return cached
        if event.status != "DETECTED":
            raise ImagingStateConflictError("The critical imaging event is not awaiting acknowledgement", code="CRITICAL_ACK_STATE_CONFLICT")
        event.status = "ACKNOWLEDGED"
        event.acknowledged_by_account_id = actor.account.id
        event.acknowledged_at = datetime.now(UTC)
        event.version += 1
        self.db.flush()
        response = {"id": event.id, "report_id": event.report_id, "status": event.status, "version": event.version, "correlation_id": correlation_id}
        self._complete(actor, "imaging.critical.acknowledge", idempotency_key, response, event.id)
        self._audit(actor, "IMAGING_CRITICAL_ACKNOWLEDGED", "imaging_critical_event", event.id, scope, correlation_id, request_id, {"status_after": event.status, "reason": reason.strip(), "version_after": event.version})
        return response

    def get_study(self, actor: NiamActor, *, study_id: str, workspace_id: str, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        study = self._study_for_scope(study_id, scope)
        order = self._order_for_scope(study.order_id, scope)
        self._require_read(actor, scope, study.patient_person_id, order.ordering_provider_account_id)
        return self._study_response(study, correlation_id)

    def get_report(self, actor: NiamActor, *, report_id: str, workspace_id: str, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        report = self._report_for_scope(report_id, scope)
        study = self._study_for_scope(report.study_id, scope)
        order = self._order_for_scope(study.order_id, scope)
        staff_object_access = report.radiologist_account_id == actor.account.id or order.ordering_provider_account_id == actor.account.id
        if scope.actor_person_id != report.patient_person_id and not staff_object_access:
            raise AppointmentAuthorizationError("report_object_denied", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        if report.status != "RELEASED" and not staff_object_access:
            raise AppointmentAuthorizationError("report_not_released", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        return self._report_response(report, correlation_id)

    def fhir_order(self, actor: NiamActor, *, order_id: str, workspace_id: str, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        order = self._order_for_scope(order_id, scope)
        self._encounter_for_scope(order.encounter_id, scope)
        self._require_read(actor, scope, order.patient_person_id, order.ordering_provider_account_id)
        self._audit_read(actor, "IMAGING_ORDER_FHIR_VIEWED", "imaging_order", order.id, scope, correlation_id)
        return self.fhir_service_request(order)

    def fhir_study(self, actor: NiamActor, *, study_id: str, workspace_id: str, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        study = self._study_for_scope(study_id, scope)
        order = self._order_for_scope(study.order_id, scope)
        self._require_read(actor, scope, study.patient_person_id, order.ordering_provider_account_id)
        self._audit_read(actor, "IMAGING_STUDY_FHIR_VIEWED", "imaging_study", study.id, scope, correlation_id)
        return self.fhir_imaging_study(study)

    def fhir_report(self, actor: NiamActor, *, report_id: str, workspace_id: str, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        report = self._report_for_scope(report_id, scope)
        study = self._study_for_scope(report.study_id, scope)
        order = self._order_for_scope(study.order_id, scope)
        staff_object_access = report.radiologist_account_id == actor.account.id or order.ordering_provider_account_id == actor.account.id
        if scope.actor_person_id != report.patient_person_id and not staff_object_access:
            raise AppointmentAuthorizationError("report_object_denied", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        if report.status != "RELEASED" and not staff_object_access:
            raise AppointmentAuthorizationError("report_not_released", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)
        self._audit_read(actor, "IMAGING_REPORT_FHIR_VIEWED", "imaging_report", report.id, scope, correlation_id)
        return self.fhir_diagnostic_report(report)

    @staticmethod
    def fhir_service_request(order: CoreImagingOrder) -> dict[str, Any]:
        return {"resourceType": "ServiceRequest", "id": order.order_id, "status": "active" if order.status not in {"COMPLETED", "CANCELLED"} else ("completed" if order.status == "COMPLETED" else "revoked"), "intent": "order", "code": {"text": order.modality}, "subject": {"reference": f"Patient/{order.patient_person_id}"}, "encounter": {"reference": f"Encounter/{order.encounter_id}"}, "identifier": [{"system": "urn:gula:accession", "value": order.accession_number}]}

    @staticmethod
    def fhir_imaging_study(study: CoreImagingStudy) -> dict[str, Any]:
        return {"resourceType": "ImagingStudy", "id": study.study_id, "status": "available" if study.status == "COMPLETED" else "registered", "subject": {"reference": f"Patient/{study.patient_person_id}"}, "identifier": [{"system": "urn:dicom:study-instance", "value": study.study_instance_uid}, {"system": "urn:gula:accession", "value": study.accession_number}], "numberOfSeries": study.series_count, "numberOfInstances": study.instance_count}

    @staticmethod
    def fhir_diagnostic_report(report: CoreImagingReport) -> dict[str, Any]:
        return {"resourceType": "DiagnosticReport", "id": report.report_id, "status": "final" if report.status == "RELEASED" else "preliminary", "subject": {"reference": f"Patient/{report.patient_person_id}"}, "conclusion": report.impression, "presentedForm": []}

    def _encounter_for_scope(self, encounter_id: str, scope):
        from app.clinical.encounters.models import CoreEncounter
        row = self.db.query(CoreEncounter).filter(CoreEncounter.id == encounter_id, CoreEncounter.organization_id == scope.organization_id, CoreEncounter.facility_id == scope.facility_id, CoreEncounter.workspace_id == scope.workspace_id).first()
        if row is None:
            raise ImagingNotFoundError("Encounter was not found", code="ENCOUNTER_NOT_FOUND")
        return row

    def _order_for_scope(self, order_id: str, scope):
        row = self.db.query(CoreImagingOrder).filter(CoreImagingOrder.id == order_id, CoreImagingOrder.organization_id == scope.organization_id, CoreImagingOrder.facility_id == scope.facility_id, CoreImagingOrder.workspace_id == scope.workspace_id).first()
        if row is None:
            raise ImagingNotFoundError("Imaging order was not found", code="ORDER_NOT_FOUND")
        return row

    def _order_for_update(self, order_id: str, scope):
        row = self.db.query(CoreImagingOrder).filter(CoreImagingOrder.id == order_id, CoreImagingOrder.organization_id == scope.organization_id, CoreImagingOrder.facility_id == scope.facility_id, CoreImagingOrder.workspace_id == scope.workspace_id).with_for_update().first()
        if row is None:
            raise ImagingNotFoundError("Imaging order was not found", code="ORDER_NOT_FOUND")
        return row

    def _study_for_scope(self, study_id: str, scope):
        row = self.db.query(CoreImagingStudy).filter(CoreImagingStudy.id == study_id, CoreImagingStudy.organization_id == scope.organization_id, CoreImagingStudy.facility_id == scope.facility_id, CoreImagingStudy.workspace_id == scope.workspace_id).first()
        if row is None:
            raise ImagingStudyNotFoundError("Imaging study was not found")
        return row

    def _study_for_update(self, study_id: str, scope):
        row = self.db.query(CoreImagingStudy).filter(CoreImagingStudy.id == study_id, CoreImagingStudy.organization_id == scope.organization_id, CoreImagingStudy.facility_id == scope.facility_id, CoreImagingStudy.workspace_id == scope.workspace_id).with_for_update().first()
        if row is None:
            raise ImagingStudyNotFoundError("Imaging study was not found")
        return row

    def _report_for_scope(self, report_id: str, scope):
        row = self.db.query(CoreImagingReport).filter(CoreImagingReport.id == report_id, CoreImagingReport.organization_id == scope.organization_id, CoreImagingReport.facility_id == scope.facility_id, CoreImagingReport.workspace_id == scope.workspace_id).first()
        if row is None:
            raise ImagingReportNotFoundError("Imaging report was not found")
        return row

    def _report_for_update(self, report_id: str, scope):
        row = self.db.query(CoreImagingReport).filter(CoreImagingReport.id == report_id, CoreImagingReport.organization_id == scope.organization_id, CoreImagingReport.facility_id == scope.facility_id, CoreImagingReport.workspace_id == scope.workspace_id).with_for_update().first()
        if row is None:
            raise ImagingReportNotFoundError("Imaging report was not found")
        return row

    def _require_radiologist(self, actor, scope, report):
        if report.radiologist_account_id != actor.account.id:
            raise AppointmentAuthorizationError("radiologist_object_mismatch", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)

    def _require_read(self, actor, scope, patient_person_id, ordering_provider_account_id):
        if scope.actor_person_id == patient_person_id or ordering_provider_account_id == actor.account.id:
            return
        raise AppointmentAuthorizationError("study_object_denied", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id)

    @staticmethod
    def _assert_version(actual: int, expected: int):
        if expected < 1 or actual != expected:
            raise VersionConflictError("The imaging resource changed before this operation")

    def _claim(self, actor, operation, key, payload):
        self.command_guard.actor_account_id = actor.account.id
        try:
            return self.command_guard.claim(operation=operation, idempotency_key=key, payload=payload)
        except ValueError as exc:
            raise AppointmentError(str(exc), status_code=400, code="IDEMPOTENCY_CONFLICT") from exc

    def _complete(self, actor, operation, key, response, resource_id):
        self.command_guard.actor_account_id = actor.account.id
        self.command_guard.complete(operation=operation, idempotency_key=key, resource_id=resource_id, response_body=response)

    def _audit_read(self, actor, event_type, target_type, target_id, scope, correlation_id):
        self.audit.record(AuditEventInput(event_type=event_type, category="clinical_imaging", action=event_type.lower(), actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type=target_type, target_id=target_id, decision="allow", correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="SENSITIVE", outcome="allowed"))

    def _audit(self, actor, event_type, target_type, target_id, scope, correlation_id, request_id, changes):
        self.audit.record(AuditEventInput(event_type=event_type, category="clinical_imaging", action=event_type.lower(), actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type=target_type, target_id=target_id, decision="allow", request_id=request_id, correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="SENSITIVE", changes=changes))

    @staticmethod
    def _order_response(row, correlation_id):
        return {"id": row.id, "order_id": row.order_id, "encounter_id": row.encounter_id, "patient_person_id": row.patient_person_id, "ordering_provider_account_id": row.ordering_provider_account_id, "organization_id": row.organization_id, "facility_id": row.facility_id, "workspace_id": row.workspace_id, "accession_number": row.accession_number, "modality": row.modality, "body_part": row.body_part, "priority": row.priority, "status": row.status, "version": row.version, "correlation_id": correlation_id}

    @staticmethod
    def _study_response(row, correlation_id):
        return {"id": row.id, "study_id": row.study_id, "order_id": row.order_id, "patient_person_id": row.patient_person_id, "study_instance_uid": row.study_instance_uid, "accession_number": row.accession_number, "modality": row.modality, "status": row.status, "provenance_type": row.provenance_type, "series_count": row.series_count, "instance_count": row.instance_count, "version": row.version, "correlation_id": correlation_id}

    @staticmethod
    def _report_response(row, correlation_id):
        return {"id": row.id, "report_id": row.report_id, "study_id": row.study_id, "patient_person_id": row.patient_person_id, "ordering_provider_account_id": row.ordering_provider_account_id, "radiologist_account_id": row.radiologist_account_id, "version": row.version, "status": row.status, "findings": row.findings if row.status in {"DRAFT", "SIGNED", "RELEASED"} else None, "impression": row.impression if row.status in {"DRAFT", "SIGNED", "RELEASED"} else None, "critical": bool(row.critical), "supersedes_id": row.supersedes_id, "signed_at": row.signed_at.isoformat() if row.signed_at else None, "released_at": row.released_at.isoformat() if row.released_at else None, "correlation_id": correlation_id}


def _core_id() -> str:
    return secrets.token_hex(13).upper()
