"""Archived: citizen platform EmergencyQR + EmergencyQRService (finding #27).

Migrated by Commit 1.12 (ADR-028, archive-first). This module is DEAD —
the classes below had zero consumers repo-wide and were preserved byte-for-byte
from `backend/app/citizen_platform/identity.py`. Canonical provider:
`shared/qr` (real image generation).

Archive-first (ADR-028 Rule 5): the code survives here for rollback and audit.
Do not restore to the active tree without a migration order.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app._compat import UTC

from shared.security.hmac import hmac_sign, hmac_verify

logger = logging.getLogger("gula.citizen.identity")


@dataclass
class EmergencyQR:
    qr_id: str = ""
    citizen_id: str = ""
    token: str = ""
    created_at: str = ""
    expires_at: str = ""
    active: bool = True


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
