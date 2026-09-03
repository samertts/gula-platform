from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.clinical.appointments.service import (
    AppointmentError,
    VersionConflictError,
)
from app.clinical.command_guard import CanonicalClinicalCommandGuard
from app.clinical.laboratory.authorization import LaboratoryAuthorizationService
from app.clinical.results.models import CoreClinicalNotification, CoreLabResult
from app.identity.api.workspaces import NiamActor
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService

from .models import CoreAccessGrant, CoreAccessHistory


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class AccessGrantNotFoundError(AppointmentError):
    code = "ACCESS_GRANT_NOT_FOUND"
    status_code = 404


class AccessNotGrantedError(AppointmentError):
    code = "ACCESS_NOT_GRANTED"
    status_code = 403


class AccessExpiredError(AppointmentError):
    code = "ACCESS_EXPIRED"
    status_code = 403


class AccessRevokedError(AppointmentError):
    code = "ACCESS_REVOKED"
    status_code = 403


class DuplicateAccessGrantError(AppointmentError):
    code = "DUPLICATE_ACCESS_GRANT"
    status_code = 409


class AccessStateConflictError(AppointmentError):
    code = "ACCESS_STATE_CONFLICT"
    status_code = 409


class AccessService:
    """Explicit patient access grants; no public tokens and no provider-side self-enrolment."""

    MAX_HOURS = 72

    def __init__(self, db):
        self.db = db
        self.authz = LaboratoryAuthorizationService(db)
        self.audit = SyncCanonicalAuditService(db)
        self.command_guard = CanonicalClinicalCommandGuard(db, actor_account_id=None)

    def grant(self, actor: NiamActor, *, workspace_id: str, resource_type: str, resource_id: str, grantee_account_id: str, purpose: str, scope_payload: dict[str, Any], duration_hours: int, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        result = self._released_result(resource_id, scope, resource_type)
        if scope.actor_person_id != result.patient_person_id:
            raise AccessNotGrantedError("Only the patient may grant this access")
        if grantee_account_id == actor.account.id:
            raise AppointmentError("The grantee must be another account", status_code=422, code="VALIDATION_ERROR")
        self.authz.appointment_authz.require_provider_in_scope(grantee_account_id, scope)
        expires_at = datetime.now(UTC) + timedelta(hours=min(duration_hours, self.MAX_HOURS))
        payload = {"workspace_id": scope.workspace_id, "resource_type": resource_type, "resource_id": result.id, "grantee_account_id": grantee_account_id, "purpose": purpose, "scope": scope_payload, "duration_hours": duration_hours}
        cached = self._claim(actor, "access.grant", idempotency_key, payload)
        if cached is not None:
            return cached
        existing = self.db.query(CoreAccessGrant).filter(CoreAccessGrant.patient_person_id == result.patient_person_id, CoreAccessGrant.grantee_account_id == grantee_account_id, CoreAccessGrant.resource_type == resource_type, CoreAccessGrant.resource_id == result.id, CoreAccessGrant.status == "ACTIVE").with_for_update().first()
        if existing is not None:
            raise DuplicateAccessGrantError("An active grant already exists for this resource and provider")
        grant = CoreAccessGrant(patient_person_id=result.patient_person_id, grantee_account_id=grantee_account_id, resource_type=resource_type, resource_id=result.id, organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, purpose=purpose, scope=scope_payload, status="ACTIVE", version=1, expires_at=expires_at, created_by_account_id=actor.account.id)
        self.db.add(grant)
        self.db.flush()
        self._history(grant, actor.account.id, "GRANT_CREATED", "ALLOW", "PATIENT_GRANTED", correlation_id)
        self._notification(f"access-grant:{grant.id}:created", grantee_account_id, "ACCESS_GRANTED", {"grant_id": grant.id, "resource_type": resource_type, "scope": scope_payload})
        response = self._grant_response(grant, correlation_id)
        self._complete(actor, "access.grant", idempotency_key, response, grant.id)
        self._audit(actor, "GRANT_CREATED", "access_grant", grant.id, scope, correlation_id, request_id, {"resource_id": result.id, "resource_type": resource_type, "purpose": purpose, "scope": scope_payload, "expires_at": expires_at.isoformat(), "version": grant.version})
        return response

    def revoke(self, actor: NiamActor, *, grant_id: str, workspace_id: str, expected_version: int, reason: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        grant = self._grant_for_update(grant_id, scope)
        if scope.actor_person_id != grant.patient_person_id:
            raise AccessNotGrantedError("Only the patient may revoke this access")
        if grant.status != "ACTIVE":
            raise AccessStateConflictError("The access grant is not active")
        if grant.version != expected_version:
            raise VersionConflictError("The access grant changed before revocation")
        cached = self._claim(actor, "access.revoke", idempotency_key, {"resource_id": grant.id, "workspace_id": scope.workspace_id, "expected_version": expected_version, "reason": reason.strip()})
        if cached is not None:
            return cached
        before = grant.status
        grant.status = "REVOKED"
        grant.version += 1
        grant.revoked_by_account_id = actor.account.id
        grant.revoked_at = datetime.now(UTC)
        grant.reason = reason.strip()
        self.db.flush()
        self._history(grant, actor.account.id, "GRANT_REVOKED", "ALLOW", "PATIENT_REVOKED", correlation_id)
        self._notification(f"access-grant:{grant.id}:revoked:{grant.version}", grant.grantee_account_id, "ACCESS_REVOKED", {"grant_id": grant.id, "version": grant.version})
        response = self._grant_response(grant, correlation_id)
        self._complete(actor, "access.revoke", idempotency_key, response, grant.id)
        self._audit(actor, "GRANT_REVOKED", "access_grant", grant.id, scope, correlation_id, request_id, {"state_before": before, "state_after": grant.status, "version_before": expected_version, "version_after": grant.version, "reason": grant.reason})
        return response

    def read_result(self, actor: NiamActor, *, result_id: str, workspace_id: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        result = self._released_result(result_id, scope, "lab_result")
        if scope.actor_person_id == result.patient_person_id:
            return self._safe_result(result, correlation_id, "OWNER")
        grant = self.db.query(CoreAccessGrant).filter(CoreAccessGrant.patient_person_id == result.patient_person_id, CoreAccessGrant.grantee_account_id == actor.account.id, CoreAccessGrant.resource_type == "lab_result", CoreAccessGrant.resource_id == result.id, CoreAccessGrant.organization_id == scope.organization_id, CoreAccessGrant.facility_id == scope.facility_id, CoreAccessGrant.workspace_id == scope.workspace_id).with_for_update().first()
        if grant is None:
            self._audit_denial(actor, "ACCESS_NOT_GRANTED", "lab_result", result.id, scope, correlation_id, request_id)
            raise AccessNotGrantedError("Access to this result is not granted")
        if grant.status == "REVOKED":
            self._audit_denial(actor, "ACCESS_REVOKED", "lab_result", result.id, scope, correlation_id, request_id)
            raise AccessRevokedError("Access to this result was revoked")
        if grant.status == "EXPIRED":
            self._audit_denial(actor, "ACCESS_EXPIRED", "lab_result", result.id, scope, correlation_id, request_id)
            raise AccessExpiredError("Access to this result has expired")
        now = datetime.now(UTC)
        expires_at = _utc(grant.expires_at)
        if expires_at is None or expires_at <= now:
            grant.status = "EXPIRED"
            grant.version += 1
            self.db.flush()
            self._history(grant, actor.account.id, "GRANT_EXPIRED", "DENY", "SERVER_TIME_EXPIRY", correlation_id)
            self._audit_denial(actor, "ACCESS_EXPIRED", "lab_result", result.id, scope, correlation_id, request_id)
            raise AccessExpiredError("Access to this result has expired")
        if grant.scope.get("read_result") is not True:
            self._audit_denial(actor, "SCOPE_DENIED", "lab_result", result.id, scope, correlation_id, request_id)
            raise AccessNotGrantedError("The granted scope does not include this result")
        self._history(grant, actor.account.id, "ACCESS_USED", "ALLOW", "ACTIVE_GRANT", correlation_id)
        self._audit(actor, "ACCESS_USED", "lab_result", result.id, scope, correlation_id, request_id, {"grant_id": grant.id, "purpose": grant.purpose, "scope": grant.scope})
        return self._safe_result(result, correlation_id, "GRANTED")

    def read_imaging_report(self, actor: NiamActor, *, report_id: str, workspace_id: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        report = self._released_result(report_id, scope, "imaging_report")
        if scope.actor_person_id == report.patient_person_id:
            return self._safe_imaging_report(report, correlation_id, "OWNER")
        grant = self.db.query(CoreAccessGrant).filter(CoreAccessGrant.patient_person_id == report.patient_person_id, CoreAccessGrant.grantee_account_id == actor.account.id, CoreAccessGrant.resource_type == "imaging_report", CoreAccessGrant.resource_id == report.id, CoreAccessGrant.organization_id == scope.organization_id, CoreAccessGrant.facility_id == scope.facility_id, CoreAccessGrant.workspace_id == scope.workspace_id).with_for_update().first()
        if grant is None:
            self._audit_denial(actor, "ACCESS_NOT_GRANTED", "imaging_report", report.id, scope, correlation_id, request_id)
            raise AccessNotGrantedError("Access to this imaging report is not granted")
        if grant.status == "REVOKED":
            self._audit_denial(actor, "ACCESS_REVOKED", "imaging_report", report.id, scope, correlation_id, request_id)
            raise AccessRevokedError("Access to this imaging report was revoked")
        if grant.status == "EXPIRED":
            self._audit_denial(actor, "ACCESS_EXPIRED", "imaging_report", report.id, scope, correlation_id, request_id)
            raise AccessExpiredError("Access to this imaging report has expired")
        expires_at = _utc(grant.expires_at)
        if expires_at is None or expires_at <= datetime.now(UTC):
            grant.status = "EXPIRED"
            grant.version += 1
            self.db.flush()
            self._history(grant, actor.account.id, "GRANT_EXPIRED", "DENY", "SERVER_TIME_EXPIRY", correlation_id)
            self._audit_denial(actor, "ACCESS_EXPIRED", "imaging_report", report.id, scope, correlation_id, request_id)
            raise AccessExpiredError("Access to this imaging report has expired")
        if grant.scope.get("read_report") is not True and grant.scope.get("read_imaging") is not True:
            self._audit_denial(actor, "SCOPE_DENIED", "imaging_report", report.id, scope, correlation_id, request_id)
            raise AccessNotGrantedError("The granted scope does not include this imaging report")
        self._history(grant, actor.account.id, "ACCESS_USED", "ALLOW", "ACTIVE_GRANT", correlation_id)
        self._audit(actor, "ACCESS_USED", "imaging_report", report.id, scope, correlation_id, request_id, {"grant_id": grant.id, "purpose": grant.purpose, "scope": grant.scope})
        return self._safe_imaging_report(report, correlation_id, "GRANTED")

    def list_grants(self, actor: NiamActor, *, workspace_id: str, limit: int, offset: int, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        query = self.db.query(CoreAccessGrant).filter(CoreAccessGrant.patient_person_id == scope.actor_person_id, CoreAccessGrant.organization_id == scope.organization_id, CoreAccessGrant.facility_id == scope.facility_id, CoreAccessGrant.workspace_id == scope.workspace_id)
        total = query.count()
        rows = query.order_by(CoreAccessGrant.created_at.desc(), CoreAccessGrant.id.desc()).offset(offset).limit(limit).all()
        return {"items": [self._grant_response(item, correlation_id) for item in rows], "total": total, "limit": limit, "offset": offset, "correlation_id": correlation_id}

    def history(self, actor: NiamActor, *, workspace_id: str, provider_account_id: str | None, resource_type: str | None, purpose: str | None, action: str | None, limit: int, offset: int, correlation_id: str) -> dict[str, Any]:
        scope = self.authz.resolve_scope(actor, workspace_id)
        query = self.db.query(CoreAccessHistory).filter(CoreAccessHistory.patient_person_id == scope.actor_person_id, CoreAccessHistory.organization_id == scope.organization_id, CoreAccessHistory.facility_id == scope.facility_id, CoreAccessHistory.workspace_id == scope.workspace_id)
        if provider_account_id:
            query = query.filter(CoreAccessHistory.actor_account_id == provider_account_id)
        if resource_type:
            query = query.filter(CoreAccessHistory.resource_type == resource_type)
        if purpose:
            query = query.filter(CoreAccessHistory.purpose == purpose)
        if action:
            query = query.filter(CoreAccessHistory.action == action)
        total = query.count()
        rows = query.order_by(CoreAccessHistory.occurred_at.desc(), CoreAccessHistory.id.desc()).offset(offset).limit(limit).all()
        return {"items": [{"action": item.action, "decision": item.decision, "purpose": item.purpose, "resource_type": item.resource_type, "occurred_at": item.occurred_at.isoformat(), "actor_display": "Care team member", "organization_display": "Authorized care organization", "reason_code": item.reason_code} for item in rows], "total": total, "limit": limit, "offset": offset, "correlation_id": correlation_id}

    def _released_result(self, resource_id, scope, resource_type):
        if resource_type == "lab_result":
            result = self.db.query(CoreLabResult).filter(CoreLabResult.id == resource_id, CoreLabResult.organization_id == scope.organization_id, CoreLabResult.facility_id == scope.facility_id, CoreLabResult.workspace_id == scope.workspace_id, CoreLabResult.status == "RELEASED").first()
        elif resource_type == "imaging_report":
            from app.clinical.imaging.models import CoreImagingReport
            result = self.db.query(CoreImagingReport).filter(CoreImagingReport.id == resource_id, CoreImagingReport.organization_id == scope.organization_id, CoreImagingReport.facility_id == scope.facility_id, CoreImagingReport.workspace_id == scope.workspace_id, CoreImagingReport.status == "RELEASED").first()
        else:
            raise AccessNotGrantedError("The requested resource type is not available")
        if result is None:
            raise AccessNotGrantedError("The requested clinical resource is not available")
        return result

    def _grant_for_update(self, grant_id, scope):
        grant = self.db.query(CoreAccessGrant).filter(CoreAccessGrant.id == grant_id, CoreAccessGrant.organization_id == scope.organization_id, CoreAccessGrant.facility_id == scope.facility_id, CoreAccessGrant.workspace_id == scope.workspace_id).with_for_update().first()
        if grant is None:
            raise AccessGrantNotFoundError("Access grant not found")
        return grant

    def _history(self, grant, actor_id, action, decision, reason_code, correlation_id):
        self.db.add(CoreAccessHistory(grant_id=grant.id, patient_person_id=grant.patient_person_id, actor_account_id=actor_id, resource_type=grant.resource_type, resource_id=grant.resource_id, organization_id=grant.organization_id, facility_id=grant.facility_id, workspace_id=grant.workspace_id, purpose=grant.purpose, scope=grant.scope, action=action, decision=decision, reason_code=reason_code, correlation_id=correlation_id, occurred_at=datetime.now(UTC)))
        self.db.flush()

    def _audit(self, actor, event_type, target_type, target_id, scope, correlation_id, request_id, changes):
        self.audit.record(AuditEventInput(event_type=event_type, category="clinical_access", action=event_type.lower(), actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type=target_type, target_id=target_id, decision="allow", request_id=request_id, correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="SENSITIVE", changes=changes))

    def _audit_denial(self, actor, reason, target_type, target_id, scope, correlation_id, request_id):
        self.audit.record(AuditEventInput(event_type="ACCESS_DENIED", category="clinical_access", action="access.read", actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", organization_id=scope.organization_id, facility_id=scope.facility_id, workspace_id=scope.workspace_id, target_type=target_type, target_id=target_id, decision="deny", reason_code=reason, request_id=request_id, correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="INTERNAL", outcome="denied"))

    def _notification(self, event_key, recipient, event_type, payload):
        self.db.add(CoreClinicalNotification(event_key=event_key, recipient_account_id=recipient, event_type=event_type, channel="SYNTHETIC", status="PENDING", payload=payload, attempt_count=0))
        self.db.flush()

    def _claim(self, actor, operation, key, payload):
        self.command_guard.actor_account_id = actor.account.id
        try:
            return self.command_guard.claim(operation=operation, idempotency_key=key, payload=payload)
        except ValueError as exc:
            raise AppointmentError(str(exc), status_code=400, code="VALIDATION_ERROR") from exc

    def _complete(self, actor, operation, key, response, resource_id):
        self.command_guard.actor_account_id = actor.account.id
        self.command_guard.complete(operation=operation, idempotency_key=key, resource_id=resource_id, response_body=response)

    @staticmethod
    def _grant_response(grant, correlation_id):
        return {"id": grant.id, "resource_type": grant.resource_type, "resource_id": grant.resource_id, "grantee_account_id": grant.grantee_account_id, "purpose": grant.purpose, "scope": grant.scope, "status": grant.status, "version": grant.version, "expires_at": grant.expires_at.isoformat(), "correlation_id": correlation_id}

    @staticmethod
    def _safe_result(result, correlation_id, access_mode):
        return {"id": result.id, "result_id": result.result_id, "test_code": result.test_code, "test_name": result.test_name, "value_numeric": float(result.value_numeric) if result.value_numeric is not None else None, "value_text": result.value_text, "unit": result.unit, "reference_low": float(result.reference_low) if result.reference_low is not None else None, "reference_high": float(result.reference_high) if result.reference_high is not None else None, "abnormal_flag": result.abnormal_flag, "status": result.status, "version": result.version, "released_at": result.released_at.isoformat() if result.released_at else None, "access_mode": access_mode, "correlation_id": correlation_id}

    @staticmethod
    def _safe_imaging_report(report, correlation_id, access_mode):
        return {"id": report.id, "report_id": report.report_id, "study_id": report.study_id, "status": report.status, "version": report.version, "findings": report.findings, "impression": report.impression, "critical": bool(report.critical), "signed_at": report.signed_at.isoformat() if report.signed_at else None, "released_at": report.released_at.isoformat() if report.released_at else None, "access_mode": access_mode, "correlation_id": correlation_id}
