from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.governance.models.citizen_platform import (
    GuardianRecord,
    QRCodeRecord,
    RecoveryRequestRecord,
)
from app.governance.repositories.citizen_platform_repositories import (
    GuardianRepository,
    QRCodeRepository,
    RecoveryRequestRepository,
)
from shared.security.hmac import hmac_sign, hmac_verify


class PersistedEmergencyQRService:
    def __init__(self, db: Session, hmac_key: str, qr_expiry_hours: int = 24):
        self._repo = QRCodeRepository(db)
        self._db = db
        self._hmac_key = hmac_key
        self._qr_expiry_hours = qr_expiry_hours

    def generate_qr(self, citizen_id: str) -> dict[str, Any]:
        qr_id = str(uuid.uuid4())
        raw = f"{citizen_id}:{qr_id}:{datetime.now(UTC).isoformat()}"
        token = hmac_sign(raw, self._hmac_key)
        now = datetime.now(UTC)
        expires = now + timedelta(hours=self._qr_expiry_hours)
        record = QRCodeRecord(
            id=qr_id,
            citizen_id=citizen_id,
            token=token,
            expires_at=expires,
            is_active=True,
            version=1,
        )
        self._repo.add(record)
        self._db.commit()
        return {
            "qr_id": qr_id,
            "citizen_id": citizen_id,
            "token": token,
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "active": True,
        }

    def verify_qr_token(self, qr_id: str, token: str) -> dict[str, Any]:
        record = self._repo.get_active(qr_id)
        if not record:
            return {"valid": False, "reason": "qr_not_found"}
        now = datetime.now(UTC)
        if record.expires_at and now > record.expires_at:
            record.is_active = False
            record.deactivated_at = now
            record.version += 1
            self._db.commit()
            return {"valid": False, "reason": "qr_expired"}
        data = token.rsplit(".", 1)[0] if "." in token else token
        sig = token.rsplit(".", 1)[1] if "." in token else ""
        if not hmac_verify(data, sig, self._hmac_key):
            return {"valid": False, "reason": "signature_mismatch"}
        return {"valid": True, "citizen_id": record.citizen_id}

    def deactivate_qr(self, qr_id: str) -> bool:
        record = self._repo.get(qr_id)
        if not record:
            return False
        record.is_active = False
        record.deactivated_at = datetime.now(UTC)
        record.version += 1
        self._db.commit()
        return True


class PersistedIdentityRecoveryService:
    def __init__(self, db: Session):
        self._repo = RecoveryRequestRepository(db)
        self._db = db

    def create_recovery_request(self, citizen_id: str, method: str) -> dict[str, Any]:
        req_id = str(uuid.uuid4())
        token = str(uuid.uuid4()).replace("-", "")
        record = RecoveryRequestRecord(
            id=req_id,
            citizen_id=citizen_id,
            method=method,
            verification_token=token,
            status="pending",
            version=1,
        )
        self._repo.add(record)
        self._db.commit()
        return {
            "id": req_id,
            "citizen_id": citizen_id,
            "method": method,
            "status": "pending",
            "verification_token": token,
            "created_at": datetime.now(UTC).isoformat(),
        }

    def verify_recovery_token(self, request_id: str, token: str) -> bool:
        record = self._repo.get_pending(request_id)
        if not record:
            return False
        if record.verification_token == token:
            record.status = "verified"
            record.resolved_at = datetime.now(UTC)
            record.version += 1
            self._db.commit()
            return True
        return False

    def get_recovery_status(self, request_id: str) -> dict[str, Any] | None:
        record = self._repo.get(request_id)
        if not record:
            return None
        return {
            "id": record.id,
            "citizen_id": record.citizen_id,
            "method": record.method,
            "status": record.status,
            "created_at": record.created_at.isoformat() if record.created_at else "",
            "resolved_at": record.resolved_at.isoformat() if record.resolved_at else None,
        }


class PersistedGuardianService:
    def __init__(self, db: Session):
        self._repo = GuardianRepository(db)
        self._db = db

    def assign_guardian(self, citizen_id: str, guardian_citizen_id: str,
                        guardian_type: str = "legal_guardian", relationship: str = "") -> dict[str, Any]:
        existing = self._repo.get_active(citizen_id)
        for g in existing:
            if g.guardian_id == guardian_citizen_id and g.is_active:
                return {
                    "id": g.id, "citizen_id": g.citizen_id,
                    "guardian_id": g.guardian_id, "guardian_type": g.guardian_type,
                    "relationship": g.relationship, "is_active": True,
                    "assigned_at": g.assigned_at.isoformat() if g.assigned_at else "",
                }
        record = GuardianRecord(
            id=str(uuid.uuid4()), citizen_id=citizen_id, guardian_id=guardian_citizen_id,
            guardian_type=guardian_type, relationship=relationship, is_active=True, version=1,
        )
        self._repo.add(record)
        self._db.commit()
        return {
            "id": record.id, "citizen_id": record.citizen_id,
            "guardian_id": record.guardian_id, "guardian_type": record.guardian_type,
            "relationship": record.relationship, "is_active": True,
            "assigned_at": record.assigned_at.isoformat() if record.assigned_at else "",
        }

    def remove_guardian(self, citizen_id: str, guardian_id: str) -> bool:
        records = self._repo.get_active(citizen_id)
        for r in records:
            if r.guardian_id == guardian_id:
                r.is_active = False
                r.revoked_at = datetime.now(UTC)
                r.version += 1
                self._db.commit()
                return True
        return False

    def get_guardians(self, citizen_id: str) -> list[dict[str, Any]]:
        records = self._repo.get_active(citizen_id)
        return [
            {"id": r.id, "citizen_id": r.citizen_id, "guardian_id": r.guardian_id,
             "guardian_type": r.guardian_type, "relationship": r.relationship, "is_active": True,
             "assigned_at": r.assigned_at.isoformat() if r.assigned_at else ""}
            for r in records
        ]

    def is_guardian(self, guardian_citizen_id: str, ward_citizen_id: str) -> bool:
        return self._repo.is_guardian(guardian_citizen_id, ward_citizen_id)


class PersistedFamilyAccountService:
    def __init__(self, db: Session):
        self._db = db
        self._guardian_svc = PersistedGuardianService(db)

    def get_family_members(self, citizen_id: str) -> list[dict[str, Any]]:
        return self._guardian_svc.get_guardians(citizen_id)

    def add_family_member(self, citizen_id: str, member_citizen_id: str,
                          relationship: str, **kwargs) -> dict[str, Any]:
        return self._guardian_svc.assign_guardian(citizen_id, member_citizen_id, relationship=relationship)

    def remove_family_member(self, citizen_id: str, member_id: str) -> bool:
        return self._guardian_svc.remove_guardian(citizen_id, member_id)

    def get_dependents(self, citizen_id: str) -> list[dict[str, Any]]:
        return self._guardian_svc.get_guardians(citizen_id)
