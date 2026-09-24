from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Final

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.identity.models.legacy_account_link import (
    LegacyAccountLink,
    LegacyAccountLinkSource,
    LegacyAccountLinkStatus,
)
from app.identity.services.audit_service import AuditService

FINGERPRINT_DIGEST: Final[str] = "sha256"


class LegacyMappingError(ValueError):
    """Base error for safe, operator-reviewed legacy mapping operations."""


class LegacyMappingNotFound(LegacyMappingError):
    pass


class LegacyMappingRollbackDenied(LegacyMappingError):
    pass


def make_source_fingerprint(
    source_kind: LegacyAccountLinkSource | str,
    legacy_account_id: int,
    hmac_key: str,
) -> str:
    """Create a stable HMAC fingerprint without storing raw PII or credentials."""
    if not hmac_key or len(hmac_key) < 32:
        raise ValueError("A dedicated mapping HMAC key of at least 32 characters is required")
    try:
        kind = LegacyAccountLinkSource(source_kind).value
    except ValueError as exc:
        raise ValueError(f"Unsupported legacy source kind: {source_kind}") from exc
    if legacy_account_id <= 0:
        raise ValueError("legacy_account_id must be a positive integer")
    message = f"gula-wave3:{kind}:{legacy_account_id}".encode()
    return hmac.new(hmac_key.encode("utf-8"), message, hashlib.sha256).hexdigest()


class LegacyMappingService:
    """Perform explicit, auditable mapping transitions only.

    This service never creates canonical accounts, copies legacy credentials, runs
    backfills, enables dual-write, or changes authorization decisions. Those
    actions require separate approved waves and an explicit feature-flagged cohort.
    """

    def __init__(self, session: Session, hmac_key: str) -> None:
        self.session = session
        self.hmac_key = hmac_key
        self.audit = AuditService(session)

    def get_link(
        self,
        source_kind: LegacyAccountLinkSource | str,
        legacy_account_id: int,
        *,
        for_update: bool = False,
    ) -> LegacyAccountLink | None:
        kind = LegacyAccountLinkSource(source_kind).value
        stmt = select(LegacyAccountLink).where(
            LegacyAccountLink.source_kind == kind,
            LegacyAccountLink.legacy_account_id == legacy_account_id,
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def ensure_pending_link(
        self,
        source_kind: LegacyAccountLinkSource | str,
        legacy_account_id: int,
    ) -> LegacyAccountLink:
        """Create one pending link; this is not a migration or a backfill."""
        kind = LegacyAccountLinkSource(source_kind)
        if legacy_account_id <= 0:
            raise ValueError("legacy_account_id must be a positive integer")
        existing = self.get_link(kind, legacy_account_id)
        if existing:
            return existing

        link = LegacyAccountLink(
            source_kind=kind.value,
            legacy_account_id=legacy_account_id,
            source_fingerprint=make_source_fingerprint(kind, legacy_account_id, self.hmac_key),
            status=LegacyAccountLinkStatus.pending.value,
            mapping_version=1,
            rollback_token=secrets.token_urlsafe(32),
        )
        self.session.add(link)
        self.session.flush()
        self.audit.record_event(
            action="legacy_mapping_created",
            target_type="legacy_account_link",
            target_id=link.id,
            metadata={
                "source_kind": kind.value,
                "mapping_version": link.mapping_version,
                "status": link.status,
            },
        )
        return link

    def transition(
        self,
        link_id: str,
        target: LegacyAccountLinkStatus | str,
        *,
        actor_id: str | None,
        reason: str | None = None,
    ) -> LegacyAccountLink:
        link = self._get_by_id(link_id, for_update=True)
        old_status = link.status
        target_status = LegacyAccountLinkStatus(target)
        link.transition(target_status, reason=reason)
        self.session.flush()
        self.audit.record_event(
            action="legacy_mapping_transition",
            actor_id=actor_id,
            target_type="legacy_account_link",
            target_id=link.id,
            metadata={
                "source_kind": link.source_kind,
                "from_status": old_status,
                "to_status": link.status,
                "mapping_version": link.mapping_version,
                "reason_present": bool(reason),
            },
        )
        return link

    def rollback(
        self,
        link_id: str,
        rollback_token: str,
        *,
        actor_id: str | None,
        reason: str,
    ) -> LegacyAccountLink:
        link = self._get_by_id(link_id, for_update=True)
        if not hmac.compare_digest(link.rollback_token, rollback_token):
            raise LegacyMappingRollbackDenied("Invalid rollback token")
        if not reason.strip():
            raise ValueError("A rollback reason is required")
        return self.transition(
            link.id,
            LegacyAccountLinkStatus.rolled_back,
            actor_id=actor_id,
            reason=reason,
        )

    def _get_by_id(self, link_id: str, *, for_update: bool) -> LegacyAccountLink:
        stmt = select(LegacyAccountLink).where(LegacyAccountLink.id == link_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = self.session.execute(stmt)
        link = result.scalar_one_or_none()
        if link is None:
            raise LegacyMappingNotFound(f"Legacy mapping link not found: {link_id}")
        return link
