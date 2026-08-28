from __future__ import annotations

from datetime import UTC, datetime

from app.clinical.appointments.authorization import AppointmentAuthorizationService
from app.clinical.appointments.service import AppointmentError, VersionConflictError
from app.clinical.command_guard import CanonicalClinicalCommandGuard
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService

from .adapters import AnalyzerAdapter, SyntheticAnalyzerAdapter
from .advanced_models import (
    CoreLabAnalyzer,
    CoreLabAnalyzerMessage,
    CoreLabQualityControl,
    CoreLabTestCatalog,
)
from .models import CoreLabOrder, CoreLabOrderItem, CoreSpecimen


class LabAdvancedError(AppointmentError):
    status_code = 409


class LabAdvancedNotFound(LabAdvancedError):
    status_code = 404


class LabAdvancedValidation(LabAdvancedError):
    status_code = 422


class LabAdvancedAuthorization(LabAdvancedError):
    status_code = 403


class AnalyzerUntrustedError(LabAdvancedError):
    pass


class QualityGateError(LabAdvancedError):
    pass


class LISAdvancedService:
    def __init__(self, db, *, analyzer_adapter: AnalyzerAdapter | None = None):
        self.db = db
        self.authz = AppointmentAuthorizationService(db)
        self.audit = SyncCanonicalAuditService(db)
        self.guard = CanonicalClinicalCommandGuard(db, actor_account_id=None)
        self.analyzer_adapter = analyzer_adapter or SyntheticAnalyzerAdapter()

    def _scope(self, actor, workspace_id, permission):
        scope = self.authz.resolve_scope(actor, workspace_id)
        self.authz.require_permission(actor, scope, permission)
        return scope

    def _claim(self, actor, operation, key, payload):
        self.guard.actor_account_id = actor.account.id
        try:
            return self.guard.claim(operation=operation, idempotency_key=key, payload=payload)
        except ValueError as exc:
            raise LabAdvancedValidation(str(exc), code="LIS_IDEMPOTENCY_CONFLICT") from exc

    def _complete(self, actor, operation, key, response, resource_id):
        self.guard.actor_account_id = actor.account.id
        self.guard.complete(operation=operation, idempotency_key=key, resource_id=resource_id, response_body=response)

    def _audit(self, actor, event_type, target_type, target_id, scope, correlation_id, request_id, changes):
        self.audit.record(AuditEventInput(event_type=event_type, category="clinical_laboratory", action=event_type.lower(), actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type=target_type, target_id=target_id, decision="allow", request_id=request_id, correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="SENSITIVE", changes=changes))

    def create_test_catalog(self, actor, *, workspace_id, canonical_code, local_code, name, system, specimen_type, unit_ucum, method, reference_range, critical_range, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "clinical.laboratory.analyzer.manage")
        code = canonical_code.strip().upper()
        existing = self.db.query(CoreLabTestCatalog).filter_by(facility_id=scope.facility_id, canonical_code=code).order_by(CoreLabTestCatalog.version.desc()).first()
        version = (existing.version + 1) if existing else 1
        payload = {"workspace_id": scope.workspace_id, "canonical_code": code, "local_code": local_code, "name": name, "system": system, "specimen_type": specimen_type, "unit_ucum": unit_ucum, "method": method, "reference_range": reference_range, "critical_range": critical_range, "version": version}
        cached = self._claim(actor, "lab.test_catalog.create", key, payload)
        if cached is not None:
            return cached.response_body
        row = CoreLabTestCatalog(laboratory_id=scope.facility_id, organization_id=scope.organization_id, facility_id=scope.facility_id, canonical_code=code, local_code=local_code, name=name, system=system, specimen_type=specimen_type, unit_ucum=unit_ucum, method=method, reference_range=reference_range, critical_range=critical_range, active=True, version=version)
        self.db.add(row)
        self.db.flush()
        response = self._catalog_response(row, correlation_id)
        self._complete(actor, "lab.test_catalog.create", key, response, row.id)
        self._audit(actor, "LAB_TEST_CATALOG_VERSION_CREATED", "lab_test_catalog", row.id, scope, correlation_id, request_id, {"canonical_code": code, "version": version})
        return response

    def list_test_catalog(self, actor, *, workspace_id, canonical_code, limit, offset, correlation_id):
        scope = self._scope(actor, workspace_id, "clinical.lab_order.read")
        query = self.db.query(CoreLabTestCatalog).filter_by(facility_id=scope.facility_id, organization_id=scope.organization_id, active=True)
        if canonical_code:
            query = query.filter(CoreLabTestCatalog.canonical_code == canonical_code.strip().upper())
        rows = query.order_by(CoreLabTestCatalog.canonical_code.asc(), CoreLabTestCatalog.version.desc()).offset(offset).limit(limit).all()
        return {"items": [self._catalog_response(row, correlation_id) for row in rows], "limit": limit, "offset": offset, "correlation_id": correlation_id}

    def register_analyzer(self, actor, *, workspace_id, section, manufacturer, model, serial_fingerprint, protocol, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "clinical.laboratory.analyzer.manage")
        payload = {"workspace_id": scope.workspace_id, "section": section, "manufacturer": manufacturer, "model": model, "serial_fingerprint": serial_fingerprint, "protocol": protocol}
        cached = self._claim(actor, "lab.analyzer.create", key, payload)
        if cached is not None:
            return cached.response_body
        if self.db.query(CoreLabAnalyzer).filter_by(facility_id=scope.facility_id, serial_fingerprint=serial_fingerprint).first() is not None:
            raise LabAdvancedError("Analyzer serial fingerprint already exists", code="ANALYZER_DUPLICATE")
        row = CoreLabAnalyzer(laboratory_id=scope.facility_id, organization_id=scope.organization_id, facility_id=scope.facility_id, section=section, manufacturer=manufacturer, model=model, serial_fingerprint=serial_fingerprint, protocol=protocol, status="REGISTERED", configuration_version=1)
        self.db.add(row)
        self.db.flush()
        response = self._analyzer_response(row, correlation_id)
        self._complete(actor, "lab.analyzer.create", key, response, row.id)
        self._audit(actor, "ANALYZER_REGISTERED", "lab_analyzer", row.id, scope, correlation_id, request_id, {"protocol": protocol, "status": row.status})
        return response

    def transition_analyzer(self, actor, *, analyzer_id, workspace_id, target_status, expected_version, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "clinical.laboratory.analyzer.manage")
        row = self.db.query(CoreLabAnalyzer).filter_by(id=analyzer_id, organization_id=scope.organization_id, facility_id=scope.facility_id).with_for_update().first()
        if row is None:
            raise LabAdvancedNotFound("Analyzer was not found", code="ANALYZER_NOT_FOUND")
        if row.configuration_version != expected_version:
            raise VersionConflictError("The analyzer configuration changed")
        allowed = {"REGISTERED": {"VALIDATED", "QUARANTINED", "RETIRED"}, "VALIDATED": {"ACTIVE", "MAINTENANCE", "QUARANTINED", "RETIRED"}, "ACTIVE": {"MAINTENANCE", "QUARANTINED", "RETIRED"}, "MAINTENANCE": {"ACTIVE", "QUARANTINED", "RETIRED"}, "QUARANTINED": {"VALIDATED", "RETIRED"}}
        if target_status not in allowed.get(row.status, set()):
            raise LabAdvancedError("Analyzer transition is not allowed", code="ANALYZER_STATE_CONFLICT")
        payload = {"workspace_id": scope.workspace_id, "analyzer_id": analyzer_id, "target_status": target_status, "expected_version": expected_version}
        cached = self._claim(actor, "lab.analyzer.transition", key, payload)
        if cached is not None:
            return cached.response_body
        before = row.status
        row.status = target_status
        row.configuration_version += 1
        self.db.flush()
        response = self._analyzer_response(row, correlation_id)
        self._complete(actor, "lab.analyzer.transition", key, response, row.id)
        self._audit(actor, "ANALYZER_STATUS_CHANGED", "lab_analyzer", row.id, scope, correlation_id, request_id, {"state_before": before, "state_after": target_status, "version_after": row.configuration_version})
        return response

    def receive_analyzer_message(self, actor, *, workspace_id, message_id, analyzer_id, specimen_id, test_code, payload_hash, quality_flags, source, occurred_at, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "clinical.laboratory.analyzer.ingest")
        analyzer = self.db.query(CoreLabAnalyzer).filter_by(id=analyzer_id, organization_id=scope.organization_id, facility_id=scope.facility_id).with_for_update().first()
        if analyzer is None:
            raise LabAdvancedNotFound("Analyzer was not found", code="ANALYZER_NOT_FOUND")
        if analyzer.status != "ACTIVE":
            raise AnalyzerUntrustedError("Only an active trusted analyzer may submit messages", code="ANALYZER_UNTRUSTED")
        specimen = self.db.query(CoreSpecimen).filter_by(id=specimen_id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id).with_for_update().first()
        if specimen is None:
            raise LabAdvancedNotFound("Specimen was not found", code="SPECIMEN_NOT_FOUND")
        item = self.db.query(CoreLabOrderItem).filter_by(id=specimen.order_item_id, lab_order_id=specimen.lab_order_id).first()
        order = self.db.query(CoreLabOrder).filter_by(id=specimen.lab_order_id).first()
        if item is None or order is None or item.test_code != test_code:
            raise LabAdvancedValidation("Analyzer message does not match specimen/order test", code="SPECIMEN_TEST_MISMATCH")
        if analyzer.laboratory_id != specimen.laboratory_id or analyzer.laboratory_id != order.laboratory_id or analyzer.organization_id != order.organization_id or analyzer.facility_id != order.facility_id:
            raise LabAdvancedAuthorization("Analyzer and specimen laboratory do not match", code="ANALYZER_LAB_MISMATCH")
        try:
            validated = self.analyzer_adapter.validate_message(message_id=message_id, analyzer_id=analyzer_id, specimen_id=specimen_id, test_code=test_code, payload_hash=payload_hash, occurred_at=occurred_at or datetime.now(UTC), source=source)
        except ValueError as exc:
            code = "ANALYZER_SOURCE_UNAVAILABLE" if source != "SYNTHETIC" else "ANALYZER_MESSAGE_INVALID"
            raise LabAdvancedValidation(str(exc), code=code) from exc
        payload = {"workspace_id": scope.workspace_id, "message_id": validated.message_id, "analyzer_id": validated.analyzer_id, "specimen_id": validated.specimen_id, "test_code": validated.test_code, "payload_hash": validated.payload_hash, "quality_flags": quality_flags, "source": validated.source, "occurred_at": validated.occurred_at.isoformat()}
        existing = self.db.query(CoreLabAnalyzerMessage).filter_by(message_id=message_id).with_for_update().first()
        if existing is not None:
            if existing.payload_hash != payload_hash:
                raise LabAdvancedError("Analyzer message id was reused with a different payload", code="ANALYZER_MESSAGE_CONFLICT")
            return self._message_response(existing, correlation_id)
        cached = self._claim(actor, "lab.analyzer_message.receive", key, payload)
        if cached is not None:
            return cached.response_body
        row = CoreLabAnalyzerMessage(message_id=validated.message_id, analyzer_id=analyzer.id, lab_order_id=order.id, specimen_id=specimen.id, patient_person_id=specimen.patient_person_id, test_code=validated.test_code, payload_hash=validated.payload_hash, quality_flags=quality_flags, status="RECEIVED", source=validated.source, occurred_at=validated.occurred_at)
        self.db.add(row)
        self.db.flush()
        response = self._message_response(row, correlation_id)
        self._complete(actor, "lab.analyzer_message.receive", key, response, row.id)
        self._audit(actor, "ANALYZER_MESSAGE_RECEIVED", "lab_analyzer_message", row.id, scope, correlation_id, request_id, {"message_id": message_id, "source": source, "payload_hash": payload_hash})
        return response

    def create_qc(self, actor, *, workspace_id, result_id, analyzer_id, status, reason, override_reason, expected_version, key, correlation_id, request_id):
        scope = self._scope(actor, workspace_id, "clinical.laboratory.qc.write")
        from app.clinical.results.models import CoreLabResult

        result = self.db.query(CoreLabResult).filter_by(id=result_id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id).with_for_update().first()
        if result is None:
            raise LabAdvancedNotFound("Result was not found", code="RESULT_NOT_FOUND")
        if result.version != expected_version:
            raise VersionConflictError("The result changed before QC recording")
        if status in {"FAILED", "OVERRIDDEN"} and not (override_reason if status == "OVERRIDDEN" else reason):
            raise LabAdvancedValidation("A reason is required for failed or overridden QC", code="QC_REASON_REQUIRED")
        if status == "OVERRIDDEN":
            self.authz.require_permission(actor, scope, "clinical.laboratory.qc.override")
            if not override_reason:
                raise LabAdvancedValidation("QC override requires a reason", code="QC_OVERRIDE_REASON_REQUIRED")
        from .models import CoreSpecimen
        specimen = self.db.query(CoreSpecimen).filter_by(id=result.specimen_id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id).first()
        if specimen is None:
            raise LabAdvancedNotFound("Result specimen was not found", code="SPECIMEN_NOT_FOUND")
        analyzer = None
        if analyzer_id:
            analyzer = self.db.query(CoreLabAnalyzer).filter_by(id=analyzer_id, organization_id=scope.organization_id, facility_id=scope.facility_id).with_for_update().first()
            if analyzer is None:
                raise LabAdvancedNotFound("Analyzer was not found", code="ANALYZER_NOT_FOUND")
            if analyzer.laboratory_id != specimen.laboratory_id or analyzer.status != "ACTIVE":
                raise LabAdvancedAuthorization("The analyzer is not trusted for this result", code="ANALYZER_UNTRUSTED")
        elif result.provenance_type == "ANALYZER":
            raise LabAdvancedValidation("Analyzer identity is required for analyzer-derived QC", code="QC_ANALYZER_REQUIRED")
        existing = self.db.query(CoreLabQualityControl).filter_by(result_id=result.id).with_for_update().first()
        payload = {"workspace_id": scope.workspace_id, "result_id": result_id, "analyzer_id": analyzer_id, "status": status, "reason": reason, "override_reason": override_reason, "expected_version": expected_version}
        cached = self._claim(actor, "lab.qc.create", key, payload)
        if cached is not None:
            return cached.response_body
        if existing is not None:
            raise LabAdvancedError("A QC record already exists for this result", code="QC_DUPLICATE")
        row = CoreLabQualityControl(result_id=result.id, analyzer_id=analyzer.id if analyzer else None, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, status=status, reason=reason, override_reason=override_reason, performed_by_account_id=actor.account.id, version=1)
        self.db.add(row)
        self.db.flush()
        response = self._qc_response(row, correlation_id)
        self._complete(actor, "lab.qc.create", key, response, row.id)
        self._audit(actor, "QC_RECORDED", "lab_quality_control", row.id, scope, correlation_id, request_id, {"status": status, "result_id": result.id, "override": status == "OVERRIDDEN"})
        return response

    @staticmethod
    def _catalog_response(row, correlation_id):
        return {"id": row.id, "laboratory_id": row.laboratory_id, "facility_id": row.facility_id, "canonical_code": row.canonical_code, "local_code": row.local_code, "name": row.name, "system": row.system, "specimen_type": row.specimen_type, "unit_ucum": row.unit_ucum, "method": row.method, "reference_range": row.reference_range, "critical_range": row.critical_range, "active": row.active, "version": row.version, "correlation_id": correlation_id}

    @staticmethod
    def _analyzer_response(row, correlation_id):
        return {"id": row.id, "facility_id": row.facility_id, "section": row.section, "manufacturer": row.manufacturer, "model": row.model, "protocol": row.protocol, "status": row.status, "version": row.configuration_version, "correlation_id": correlation_id}

    @staticmethod
    def _message_response(row, correlation_id):
        return {"id": row.id, "message_id": row.message_id, "analyzer_id": row.analyzer_id, "specimen_id": row.specimen_id, "test_code": row.test_code, "status": row.status, "source": row.source, "payload_hash": row.payload_hash, "correlation_id": correlation_id}

    @staticmethod
    def _qc_response(row, correlation_id):
        return {"id": row.id, "result_id": row.result_id, "analyzer_id": row.analyzer_id, "status": row.status, "reason": row.reason, "override_reason": row.override_reason, "version": row.version, "correlation_id": correlation_id}
