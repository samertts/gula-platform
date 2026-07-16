from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.national.services.citizen_service import CitizenService as NationalCitizenService
from shared.security.encryption import decrypt_national_id, encrypt_national_id
from shared.security.hmac import hmac_sign, hmac_verify

logger = logging.getLogger("gula.citizen.identity")


@dataclass
class IdentityDocument:
    id: str = ""
    citizen_id: str = ""
    document_type: str = ""
    document_number: str = ""
    issuer: str = ""
    issued_at: str = ""
    expires_at: str = ""
    verified: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmergencyQR:
    qr_id: str = ""
    citizen_id: str = ""
    token: str = ""
    created_at: str = ""
    expires_at: str = ""
    active: bool = True


@dataclass
class IdentityRecoveryRequest:
    id: str = ""
    citizen_id: str = ""
    method: str = ""
    status: str = "pending"
    verification_token: str = ""
    created_at: str = ""
    resolved_at: str | None = None


class HealthIdentityService:
    def __init__(
        self,
        citizen_service: NationalCitizenService,
        encryption_key: str,
        hmac_key: str,
    ) -> None:
        self._citizen_service = citizen_service
        self._encryption_key = encryption_key
        self._hmac_key = hmac_key

    async def verify_identity(
        self, citizen_id: str, national_id: str
    ) -> dict[str, Any]:
        citizen = await self._citizen_service.get_citizen(citizen_id)
        stored_encrypted = citizen.national_id_hash
        if not stored_encrypted:
            return {"verified": False, "reason": "no_national_id_on_file"}
        decrypted = decrypt_national_id(
            stored_encrypted, self._encryption_key, self._hmac_key
        )
        if decrypted is None:
            return {"verified": False, "reason": "decryption_failed"}
        return {"verified": decrypted == national_id, "citizen_id": citizen.id}

    async def encrypt_and_store_national_id(
        self, citizen_id: str, national_id: str
    ) -> str:
        await self._citizen_service.get_citizen(citizen_id)
        secure_token = encrypt_national_id(
            national_id, self._encryption_key, self._hmac_key
        )
        await self._citizen_service.update_citizen(
            citizen_id, {"national_id_hash": secure_token}
        )
        return secure_token


class EmergencyQRService:
    def __init__(self, hmac_key: str, qr_expiry_hours: int = 24) -> None:
        self._hmac_key = hmac_key
        self._qr_expiry_hours = qr_expiry_hours
        self._qrs: dict[str, EmergencyQR] = {}

    def generate_qr(self, citizen_id: str) -> EmergencyQR:
        qr_id = str(uuid.uuid4())
        raw = f"{citizen_id}:{qr_id}:{datetime.now(UTC).isoformat()}"
        token = hmac_sign(raw, self._hmac_key)
        created = datetime.now(UTC)
        expires = created.replace(hour=created.hour + self._qr_expiry_hours)
        qr = EmergencyQR(
            qr_id=qr_id,
            citizen_id=citizen_id,
            token=token,
            created_at=created.isoformat(),
            expires_at=expires.isoformat(),
        )
        self._qrs[qr_id] = qr
        return qr

    def verify_qr_token(self, qr_id: str, token: str) -> dict[str, Any]:
        qr = self._qrs.get(qr_id)
        if not qr:
            return {"valid": False, "reason": "qr_not_found"}
        if not qr.active:
            return {"valid": False, "reason": "qr_deactivated"}
        now = datetime.now(UTC)
        if qr.expires_at and now.isoformat() > qr.expires_at:
            return {"valid": False, "reason": "qr_expired"}
        data = token.rsplit(".", 1)[0] if "." in token else token
        sig = token.rsplit(".", 1)[1] if "." in token else ""
        if not hmac_verify(data, sig, self._hmac_key):
            return {"valid": False, "reason": "signature_mismatch"}
        return {"valid": True, "citizen_id": qr.citizen_id}

    def deactivate_qr(self, qr_id: str) -> bool:
        qr = self._qrs.get(qr_id)
        if not qr:
            return False
        qr.active = False
        return True


class IdentityRecoveryService:
    def __init__(self) -> None:
        self._requests: dict[str, IdentityRecoveryRequest] = {}

    def create_recovery_request(
        self, citizen_id: str, method: str
    ) -> IdentityRecoveryRequest:
        req_id = str(uuid.uuid4())
        token = str(uuid.uuid4()).replace("-", "")
        req = IdentityRecoveryRequest(
            id=req_id,
            citizen_id=citizen_id,
            method=method,
            verification_token=token,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._requests[req_id] = req
        return req

    def verify_recovery_token(self, request_id: str, token: str) -> bool:
        req = self._requests.get(request_id)
        if not req:
            return False
        if req.status != "pending":
            return False
        if req.verification_token == token:
            req.status = "verified"
            req.resolved_at = datetime.now(UTC).isoformat()
            return True
        return False

    def get_recovery_status(self, request_id: str) -> dict[str, Any] | None:
        req = self._requests.get(request_id)
        if not req:
            return None
        return {
            "id": req.id,
            "citizen_id": req.citizen_id,
            "method": req.method,
            "status": req.status,
            "created_at": req.created_at,
            "resolved_at": req.resolved_at,
        }
