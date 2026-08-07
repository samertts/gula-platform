"""Archived: persisted citizen-platform EmergencyQR service (finding #28).

Migrated by Commit 1.12 (ADR-028, archive-first). This module is DEAD — the
class below had zero consumers repo-wide and was preserved byte-for-byte from
`backend/app/governance/services/citizen_platform_persistence.py`. Canonical
provider: `shared/qr` (real image generation). Dead twin of the already-dead
in-memory `EmergencyQRService` (finding #27, archived in the same commit).

Archive-first (ADR-028 Rule 5): the code survives here for rollback and audit.
Do not restore to the active tree without a migration order.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from app._compat import UTC
from app.governance.models.citizen_platform import QRCodeRecord
from app.governance.repositories.citizen_platform_repositories import (
    QRCodeRepository,
)
from sqlalchemy.orm import Session

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
