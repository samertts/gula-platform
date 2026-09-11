from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app._compat import UTC
from app.identity.models.identity import IdentityRecord, IdentityType
from app.identity.repositories.identity_repository import IdentityRepository


class IdentityService:

    def __init__(self, session: Session) -> None:
        self.repo = IdentityRepository(session)

    def create_identity(
        self,
        person_id: str,
        identity_type: IdentityType,
        issued_by_organization: str | None = None,
        expires_at: datetime | None = None,
        notes: str | None = None,
    ) -> IdentityRecord:
        identity = IdentityRecord(
            id=...,
            uuid=str(uuid.uuid4()),
            person_id=person_id,
            identity_type=identity_type.value,
            status="active",
            issued_at=datetime.now(UTC),
            expires_at=expires_at,
            issued_by_organization=issued_by_organization,
            notes=notes,
            is_active=True,
        )
        return self.repo.create(identity)

    def get_identity(self, identity_id: str) -> IdentityRecord | None:
        return self.repo.get_by_id(identity_id)

    def verify_identity(
        self,
        identity_id: str,
        verified_by: str,
        verification_method: str,
    ) -> IdentityRecord | None:
        identity = self.repo.get_by_id(identity_id)
        if not identity:
            return None
        identity.verified_at = datetime.now(UTC)
        identity.verified_by = verified_by
        identity.verification_method = verification_method
        self.repo.session.flush()
        return identity

    def revoke_identity(self, identity_id: str) -> None:
        self.repo.soft_delete(identity_id)
