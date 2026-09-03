from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.clinical.appointments.service import AppointmentError
from app.identity.api.workspaces import NiamActor
from app.identity.lifecycle.models import CitizenLifecycle
from app.identity.models import (
    Account,
    Device,
    NiamConsent,
    NiamConsentStatus,
    NiamHealthIdentityOperation,
)
from app.identity.models.person import Person
from app.identity.services.canonical_audit import AuditEventInput, SyncCanonicalAuditService


class HealthIdentityError(AppointmentError):
    code = "HEALTH_IDENTITY_ERROR"
    status_code = 409


class VerificationUnavailableError(HealthIdentityError):
    code = "VERIFICATION_PROVIDER_UNAVAILABLE"
    status_code = 503


class HealthIdentityNotFoundError(HealthIdentityError):
    code = "HEALTH_IDENTITY_RESOURCE_NOT_FOUND"
    status_code = 404


class CanonicalHealthIdentityService:
    """Extends NIAM identity lifecycle without creating a second identity owner."""

    def __init__(self, db: Session):
        self.db = db
        self.audit = SyncCanonicalAuditService(db)

    def health_status(self, actor: NiamActor, *, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        self._active_actor(actor)
        person_id = self._person_id(actor)
        citizen = self.db.query(CitizenLifecycle).filter(CitizenLifecycle.person_id == person_id).order_by(CitizenLifecycle.created_at.desc()).first()
        response = {"person_id": person_id, "health_id_issued": bool(citizen and citizen.health_id), "status": citizen.status if citizen else "NOT_REGISTERED", "self_service_enabled": bool(citizen and citizen.self_service_enabled), "correlation_id": correlation_id}
        if citizen:
            self._audit(actor, "HEALTH_ID_STATUS_VIEWED", "citizen_lifecycle", citizen.id, correlation_id, request_id, {"health_id_issued": bool(citizen.health_id)})
        return response

    def request_verification(self, actor: NiamActor, *, method: str, purpose: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        self._active_actor(actor)
        payload = {"account_id": actor.account.id, "identity_id": actor.account.identity_id, "person_id": self._person_id(actor), "method": method, "purpose": purpose.strip()}
        cached = self._claim(actor, "identity.verification.request", idempotency_key, payload)
        if cached is not None:
            return cached
        operation = NiamHealthIdentityOperation(operation_id=_operation_id("VERIFY"), account_id=actor.account.id, identity_id=actor.account.identity_id, person_id=self._person_id(actor), operation_type="VERIFICATION", status="PENDING", method=method, provider="SYNTHETIC_ADAPTER" if method == "SYNTHETIC" else "NOT_CONNECTED_PROVIDER", assurance_level="L0", purpose=purpose.strip(), source="SYNTHETIC", version=1, is_active=True)
        self.db.add(operation)
        self.db.flush()
        response = self._operation_response(operation, correlation_id)
        self._complete(actor, "identity.verification.request", idempotency_key, response, operation.id)
        self._audit(actor, "IDENTITY_VERIFICATION_REQUESTED", "health_identity_operation", operation.id, correlation_id, request_id, {"method": method, "provider": operation.provider, "status_after": operation.status})
        return response

    def complete_verification(self, actor: NiamActor, *, operation_id: str, proof: str, verified_attributes: dict[str, Any] | None, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        self._active_actor(actor)
        operation = self._operation_for_actor(operation_id, actor, for_update=True)
        payload = {"resource_id": operation.id, "operation_id": operation.operation_id, "proof_digest": _digest(proof), "verified_attributes": self._safe_attributes(verified_attributes)}
        cached = self._claim(actor, "identity.verification.complete", idempotency_key, payload)
        if cached is not None:
            return cached
        if operation.status != "PENDING":
            raise HealthIdentityError("Verification operation is not pending", code="VERIFICATION_NOT_PENDING")
        if operation.method != "SYNTHETIC":
            raise VerificationUnavailableError("The requested verification provider is not connected; no verification was asserted")
        if proof != "SYNTHETIC-VERIFIED":
            operation.status = "FAILED"
            operation.version += 1
            operation.reason = "synthetic_proof_rejected"
            self.db.flush()
            self._audit(actor, "IDENTITY_VERIFICATION_FAILED", "health_identity_operation", operation.id, correlation_id, request_id, {"status_after": operation.status, "reason": operation.reason})
            raise HealthIdentityError("Verification proof was rejected", code="VERIFICATION_PROOF_REJECTED", status_code=422)
        operation.status = "VERIFIED"
        operation.assurance_level = "L1"
        operation.provider_reference = f"synthetic:{operation.operation_id}"
        operation.evidence_digest = _digest(proof)
        operation.verified_attributes = self._safe_attributes(verified_attributes)
        operation.completed_at = datetime.now(UTC)
        operation.version += 1
        self.db.flush()
        response = self._operation_response(operation, correlation_id)
        self._complete(actor, "identity.verification.complete", idempotency_key, response, operation.id)
        self._audit(actor, "IDENTITY_VERIFICATION_COMPLETED", "health_identity_operation", operation.id, correlation_id, request_id, {"status_after": operation.status, "assurance_level": operation.assurance_level, "version": operation.version})
        return response

    def issue_health_id(self, actor: NiamActor, *, verification_operation_id: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        self._active_actor(actor)
        operation = self._operation_for_actor(verification_operation_id, actor, for_update=False)
        if operation.operation_type != "VERIFICATION" or operation.status != "VERIFIED":
            raise HealthIdentityError("A verified identity operation is required before Health ID issuance", code="VERIFICATION_REQUIRED", status_code=422)
        payload = {"account_id": actor.account.id, "verification_operation_id": operation.id, "operation_version": operation.version}
        cached = self._claim(actor, "identity.health_id.issue", idempotency_key, payload)
        if cached is not None:
            return cached
        person = self.db.query(Person).filter(Person.id == operation.person_id, Person.is_active.is_(True)).with_for_update().first()
        if person is None:
            raise HealthIdentityError("Identity is not linked to an active person", code="IDENTITY_PERSON_UNRESOLVED", status_code=403)
        citizens = self.db.query(CitizenLifecycle).filter(CitizenLifecycle.person_id == operation.person_id).with_for_update().all()
        citizens_with_health_id = [row for row in citizens if row.health_id]
        if len(citizens_with_health_id) > 1:
            raise HealthIdentityError("Multiple Health IDs exist for one person; manual review is required", code="ONE_PERSON_HEALTH_ID_CONFLICT")
        citizen = citizens[0] if citizens else None
        if citizen is None:
            citizen = CitizenLifecycle(uuid=str(uuid.uuid4()), citizen_id=operation.person_id, person_id=operation.person_id, identity_id=operation.identity_id, status="identity_verified", identity_verified_at=datetime.now(UTC), is_active=True)
            self.db.add(citizen)
            self.db.flush()
        elif citizen.health_id:
            response = self._citizen_response(citizen, correlation_id)
            self._complete(actor, "identity.health_id.issue", idempotency_key, response, citizen.id)
            return response
        citizen.health_id = f"GULA-SYN-{uuid.uuid4().hex.upper()[:20]}"
        citizen.identity_id = operation.identity_id
        citizen.identity_verified_at = citizen.identity_verified_at or datetime.now(UTC)
        citizen.status = "health_id_issued"
        citizen.self_service_enabled = True
        citizen.is_active = True
        issuance = NiamHealthIdentityOperation(operation_id=_operation_id("NHID"), account_id=actor.account.id, identity_id=operation.identity_id, person_id=operation.person_id, operation_type="HEALTH_ID_ISSUANCE", status="COMPLETED", method="SYNTHETIC", provider="SYNTHETIC_ADAPTER", assurance_level=operation.assurance_level, provider_reference=operation.operation_id, purpose="issue synthetic Health ID", source="SYNTHETIC", version=1, is_active=True, completed_at=datetime.now(UTC))
        self.db.add(issuance)
        self.db.flush()
        response = self._citizen_response(citizen, correlation_id)
        self._complete(actor, "identity.health_id.issue", idempotency_key, response, citizen.id)
        self._audit(actor, "HEALTH_ID_ISSUED", "citizen_lifecycle", citizen.id, correlation_id, request_id, {"status_after": citizen.status, "health_id_issued": True, "synthetic_only": True})
        return response

    def register_device(self, actor: NiamActor, *, device_fingerprint: str, device_name: str | None, device_type: str | None, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        self._active_actor(actor)
        person_id = self._person_id(actor)
        payload = {"account_id": actor.account.id, "person_id": person_id, "device_fingerprint_digest": _digest(device_fingerprint), "device_name": device_name, "device_type": device_type}
        cached = self._claim(actor, "identity.device.register", idempotency_key, payload)
        if cached is not None:
            return cached
        device = self.db.query(Device).filter(Device.device_fingerprint == device_fingerprint).with_for_update().first()
        if device is not None and (device.person_id != person_id or (device.account_id is not None and device.account_id != actor.account.id)):
            raise HealthIdentityError("Device fingerprint belongs to another identity", code="DEVICE_OWNERSHIP_CONFLICT", status_code=403)
        if device is None:
            device = Device(uuid=str(uuid.uuid4()), person_id=person_id, account_id=actor.account.id, device_name=device_name, device_type=device_type, device_fingerprint=device_fingerprint, trusted=False, is_active=True, is_locked=False)
            self.db.add(device)
            self.db.flush()
        response = {"id": device.id, "device_id": device.device_id, "trusted": bool(device.trusted), "is_active": bool(device.is_active), "correlation_id": correlation_id}
        self._complete(actor, "identity.device.register", idempotency_key, response, device.id)
        self._audit(actor, "DEVICE_REGISTERED", "niam_device", device.id, correlation_id, request_id, {"trusted": bool(device.trusted), "fingerprint_redacted": True})
        return response

    def trust_device(self, actor: NiamActor, *, device_id: str, verification_operation_id: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        self._active_actor(actor)
        operation = self._operation_for_actor(verification_operation_id, actor, for_update=False)
        if operation.operation_type != "VERIFICATION" or operation.status != "VERIFIED":
            raise HealthIdentityError("Verified identity evidence is required for device trust", code="VERIFICATION_REQUIRED", status_code=422)
        device = self.db.query(Device).filter(Device.id == device_id, Device.account_id == actor.account.id, Device.person_id == self._person_id(actor), Device.is_active.is_(True)).with_for_update().first()
        if device is None:
            raise HealthIdentityNotFoundError("Device was not found")
        payload = {"resource_id": device.id, "workspace_id": "identity", "verification_operation_id": operation.id}
        cached = self._claim(actor, "identity.device.trust", idempotency_key, payload)
        if cached is not None:
            return cached
        device.trusted = True
        device.trusted_at = datetime.now(UTC)
        self.db.flush()
        response = {"id": device.id, "trusted": True, "trusted_at": device.trusted_at.isoformat(), "correlation_id": correlation_id}
        self._complete(actor, "identity.device.trust", idempotency_key, response, device.id)
        self._audit(actor, "DEVICE_TRUSTED", "niam_device", device.id, correlation_id, request_id, {"trusted": True, "verification_operation_id": operation.id})
        return response

    def grant_consent(self, actor: NiamActor, *, grantee_account_id: str, purpose: str, resource_domain: str, scope: dict[str, Any], expires_at: datetime, reason: str | None, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        self._active_actor(actor)
        self._validate_expiry(expires_at)
        self._validate_scope(scope)
        if grantee_account_id == actor.account.id:
            raise HealthIdentityError("Self-consent is implicit and cannot be granted as a sharing consent", code="CONSENT_SELF_GRANT", status_code=422)
        grantee = self.db.query(Account).filter(Account.id == grantee_account_id, Account.is_active.is_(True)).first()
        if grantee is None:
            raise HealthIdentityNotFoundError("Consent grantee was not found")
        payload = {"subject_account_id": actor.account.id, "grantee_account_id": grantee.id, "purpose": purpose.strip(), "resource_domain": resource_domain.strip(), "scope": scope, "expires_at": expires_at.isoformat(), "reason": reason}
        cached = self._claim(actor, "identity.consent.grant", idempotency_key, payload)
        if cached is not None:
            return cached
        prior = self.db.query(NiamConsent).filter(NiamConsent.subject_account_id == actor.account.id, NiamConsent.grantee_account_id == grantee.id, NiamConsent.purpose == purpose.strip(), NiamConsent.resource_domain == resource_domain.strip()).order_by(NiamConsent.version.desc()).with_for_update().first()
        version = 1
        if prior is not None:
            version = prior.version + 1
            if prior.is_valid_now():
                prior.status = NiamConsentStatus.revoked.value
                prior.is_active = False
                prior.withdrawn_at = datetime.now(UTC)
        consent = NiamConsent(uuid=str(uuid.uuid4()), subject_account_id=actor.account.id, grantee_account_id=grantee.id, purpose=purpose.strip(), scope=scope, resource_domain=resource_domain.strip(), status=NiamConsentStatus.active.value, expires_at=expires_at, version=version, source="USER_PORTAL", created_by=actor.account.id, supersedes_id=prior.id if prior else None, reason=reason.strip() if reason else None, is_active=True)
        self.db.add(consent)
        self.db.flush()
        response = self._consent_response(consent, correlation_id)
        self._complete(actor, "identity.consent.grant", idempotency_key, response, consent.id)
        self._audit(actor, "CONSENT_GRANTED", "niam_consent", consent.id, correlation_id, request_id, {"resource_domain": consent.resource_domain, "purpose": consent.purpose, "version": consent.version, "expires_at": expires_at.isoformat()})
        return response

    def revoke_consent(self, actor: NiamActor, *, consent_id: str, reason: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        self._active_actor(actor)
        consent = self.db.query(NiamConsent).filter(NiamConsent.id == consent_id, NiamConsent.subject_account_id == actor.account.id).with_for_update().first()
        if consent is None:
            raise HealthIdentityNotFoundError("Consent was not found")
        payload = {"resource_id": consent.id, "reason": reason.strip(), "version": consent.version}
        cached = self._claim(actor, "identity.consent.revoke", idempotency_key, payload)
        if cached is not None:
            return cached
        if consent.status != NiamConsentStatus.active.value or not consent.is_active:
            raise HealthIdentityError("Consent is not active", code="CONSENT_NOT_ACTIVE")
        consent.status = NiamConsentStatus.revoked.value
        consent.is_active = False
        consent.withdrawn_at = datetime.now(UTC)
        consent.reason = reason.strip()
        consent.version += 1
        self.db.flush()
        response = self._consent_response(consent, correlation_id)
        self._complete(actor, "identity.consent.revoke", idempotency_key, response, consent.id)
        self._audit(actor, "CONSENT_REVOKED", "niam_consent", consent.id, correlation_id, request_id, {"status_after": consent.status, "version": consent.version, "reason": reason.strip()})
        return response

    def request_recovery(self, actor: NiamActor, *, purpose: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        self._active_actor(actor)
        payload = {"account_id": actor.account.id, "purpose": purpose.strip()}
        cached = self._claim(actor, "identity.recovery.request", idempotency_key, payload)
        if cached is not None:
            return cached
        operation = NiamHealthIdentityOperation(operation_id=_operation_id("REC"), account_id=actor.account.id, identity_id=actor.account.identity_id, person_id=self._person_id(actor), operation_type="RECOVERY", status="PENDING", method="SYNTHETIC", provider="SYNTHETIC_ADAPTER", assurance_level="L0", purpose=purpose.strip(), source="SYNTHETIC", version=1, is_active=True, expires_at=datetime.now(UTC) + timedelta(minutes=15))
        self.db.add(operation)
        self.db.flush()
        response = {"operation_id": operation.operation_id, "status": operation.status, "expires_at": operation.expires_at.isoformat(), "correlation_id": correlation_id}
        self._complete(actor, "identity.recovery.request", idempotency_key, response, operation.id)
        self._audit(actor, "ACCOUNT_RECOVERY_REQUESTED", "health_identity_operation", operation.id, correlation_id, request_id, {"status_after": operation.status, "synthetic_only": True})
        return response

    def complete_recovery(self, actor: NiamActor, *, operation_id: str, proof: str, idempotency_key: str, correlation_id: str, request_id: str | None) -> dict[str, Any]:
        self._active_actor(actor)
        operation = self._operation_for_actor(operation_id, actor, for_update=True)
        if operation.operation_type != "RECOVERY":
            raise HealthIdentityError("Recovery operation is invalid", code="RECOVERY_OPERATION_INVALID")
        payload = {"resource_id": operation.id, "proof_digest": _digest(proof)}
        cached = self._claim(actor, "identity.recovery.complete", idempotency_key, payload)
        if cached is not None:
            return cached
        if operation.status != "PENDING":
            raise HealthIdentityError("Recovery operation is not pending", code="RECOVERY_NOT_PENDING")
        expiry = operation.expires_at
        if expiry is not None:
            expiry = expiry.replace(tzinfo=UTC) if expiry.tzinfo is None else expiry.astimezone(UTC)
        if expiry and expiry <= datetime.now(UTC):
            operation.status = "FAILED"
            operation.version += 1
            self.db.flush()
            self._audit(actor, "ACCOUNT_RECOVERY_FAILED", "health_identity_operation", operation.id, correlation_id, request_id, {"status_after": operation.status, "reason": "expired"})
            raise HealthIdentityError("Recovery operation expired", code="RECOVERY_EXPIRED")
        if proof != "SYNTHETIC-RECOVERY-VERIFIED":
            operation.status = "FAILED"
            operation.version += 1
            operation.reason = "synthetic_proof_rejected"
            self.db.flush()
            self._audit(actor, "ACCOUNT_RECOVERY_FAILED", "health_identity_operation", operation.id, correlation_id, request_id, {"status_after": operation.status, "reason": operation.reason})
            raise HealthIdentityError("Recovery proof was rejected", code="RECOVERY_PROOF_REJECTED", status_code=422)
        operation.status = "COMPLETED"
        operation.assurance_level = "L1"
        operation.evidence_digest = _digest(proof)
        operation.completed_at = datetime.now(UTC)
        operation.version += 1
        citizen = self.db.query(CitizenLifecycle).filter(CitizenLifecycle.person_id == operation.person_id).with_for_update().first()
        if citizen is not None:
            citizen.last_recovery_at = datetime.now(UTC)
        self.db.flush()
        response = {"operation_id": operation.operation_id, "status": operation.status, "completed_at": operation.completed_at.isoformat(), "correlation_id": correlation_id}
        self._complete(actor, "identity.recovery.complete", idempotency_key, response, operation.id)
        self._audit(actor, "ACCOUNT_RECOVERY_COMPLETED", "health_identity_operation", operation.id, correlation_id, request_id, {"status_after": operation.status, "assurance_level": operation.assurance_level})
        return response

    def _active_actor(self, actor: NiamActor) -> None:
        expires_at = getattr(actor.session, "expires_at", None)
        if not actor.account.is_active or actor.account.is_locked or str(actor.account.status) != "active" or not actor.session.is_active or (expires_at is not None and _expired(expires_at)):
            raise HealthIdentityError("Active account session is required", code="SESSION_INVALID", status_code=403)

    def _person_id(self, actor: NiamActor) -> str:
        from app.identity.models import IdentityRecord

        identity = self.db.query(IdentityRecord).filter(IdentityRecord.id == actor.account.identity_id, IdentityRecord.is_active.is_(True)).first()
        if identity is None or not identity.person_id:
            raise HealthIdentityError("Identity is not linked to an active person", code="IDENTITY_PERSON_UNRESOLVED", status_code=403)
        return identity.person_id

    def _operation_for_actor(self, operation_id: str, actor: NiamActor, *, for_update: bool):
        query = self.db.query(NiamHealthIdentityOperation).filter(NiamHealthIdentityOperation.operation_id == operation_id, NiamHealthIdentityOperation.account_id == actor.account.id, NiamHealthIdentityOperation.identity_id == actor.account.identity_id, NiamHealthIdentityOperation.is_active.is_(True))
        if for_update:
            query = query.with_for_update()
        row = query.first()
        if row is None:
            raise HealthIdentityNotFoundError("Health identity operation was not found")
        return row

    @staticmethod
    def _safe_attributes(attributes: dict[str, Any] | None) -> dict[str, Any] | None:
        if not attributes:
            return None
        allowed = {"name_match", "birth_year_match", "document_type", "assurance_note"}
        return {key: value for key, value in attributes.items() if key in allowed}

    @staticmethod
    def _validate_expiry(expires_at: datetime) -> None:
        now = datetime.now(UTC)
        value = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=UTC)
        if value <= now or value > now + timedelta(hours=72):
            raise HealthIdentityError("Consent expiry must be in the future and no more than 72 hours", code="CONSENT_EXPIRY_INVALID", status_code=422)

    @staticmethod
    def _validate_scope(scope: dict[str, Any]) -> None:
        if not scope or "*" in str(scope) or "public" in str(scope).lower():
            raise HealthIdentityError("Consent scope must be explicit and non-public", code="CONSENT_SCOPE_INVALID", status_code=422)

    def _claim(self, actor: NiamActor, operation: str, key: str, payload: dict[str, Any]):
        from app.clinical.command_guard import CanonicalClinicalCommandGuard

        guard = CanonicalClinicalCommandGuard(self.db, actor_account_id=actor.account.id)
        try:
            return guard.claim(operation=operation, idempotency_key=key, payload=payload)
        except ValueError as exc:
            raise AppointmentError(str(exc), status_code=400, code="IDEMPOTENCY_CONFLICT") from exc

    def _complete(self, actor: NiamActor, operation: str, key: str, response: dict[str, Any], resource_id: str) -> None:
        from app.clinical.command_guard import CanonicalClinicalCommandGuard

        CanonicalClinicalCommandGuard(self.db, actor_account_id=actor.account.id).complete(operation=operation, idempotency_key=key, resource_id=resource_id, response_body=response)

    def _audit(self, actor, event_type: str, target_type: str, target_id: str, correlation_id: str, request_id: str | None, changes: dict[str, Any]) -> None:
        self.audit.record(AuditEventInput(event_type=event_type, category="identity_health", action=event_type.lower(), actor_id=actor.account.id, actor_identity_id=actor.account.identity_id, actor_type="account", target_type=target_type, target_id=target_id, decision="allow", request_id=request_id, correlation_id=correlation_id, session_id=actor.session.uuid, source="api", data_classification="SENSITIVE", changes=changes))

    @staticmethod
    def _operation_response(row, correlation_id):
        return {"id": row.id, "operation_id": row.operation_id, "operation_type": row.operation_type, "status": row.status, "method": row.method, "provider": row.provider, "assurance_level": row.assurance_level, "purpose": row.purpose, "version": row.version, "completed_at": row.completed_at.isoformat() if row.completed_at else None, "correlation_id": correlation_id}

    @staticmethod
    def _citizen_response(row, correlation_id):
        return {"citizen_lifecycle_id": row.id, "person_id": row.person_id, "health_id": row.health_id, "status": row.status, "identity_verified": bool(row.identity_verified_at), "self_service_enabled": bool(row.self_service_enabled), "correlation_id": correlation_id}

    @staticmethod
    def _consent_response(row, correlation_id):
        return {"id": row.id, "subject_account_id": row.subject_account_id, "grantee_account_id": row.grantee_account_id, "purpose": row.purpose, "resource_domain": row.resource_domain, "scope": row.scope, "status": row.status, "version": row.version, "expires_at": row.expires_at.isoformat(), "correlation_id": correlation_id}


def _operation_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex.upper()}"


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _expired(value: datetime) -> bool:
    normalized = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return normalized <= datetime.now(UTC)
