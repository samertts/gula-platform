from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.governance.models.identity import GovernanceBreakGlassAccess
from app.governance.repositories.base import GovernanceRepository


class BreakGlassAccessRepository(GovernanceRepository[GovernanceBreakGlassAccess]):
    def __init__(self, db: Session):
        super().__init__(db, GovernanceBreakGlassAccess, audit_resource="gov_break_glass")

    def get_active(self, access_id: str) -> GovernanceBreakGlassAccess | None:
        return (
            self._db.query(GovernanceBreakGlassAccess)
            .filter(
                GovernanceBreakGlassAccess.id == access_id,
                GovernanceBreakGlassAccess.is_active.is_(True),
            )
            .first()
        )

    def list_active(self, user_id: str | None = None) -> list[GovernanceBreakGlassAccess]:
        q = self._db.query(GovernanceBreakGlassAccess).filter(
            GovernanceBreakGlassAccess.is_active.is_(True),
        )
        if user_id:
            q = q.filter(GovernanceBreakGlassAccess.user_id == user_id)
        return q.order_by(GovernanceBreakGlassAccess.accessed_at.desc()).all()

    def expire_stale(self) -> int:
        now = datetime.now(UTC)
        stale = (
            self._db.query(GovernanceBreakGlassAccess)
            .filter(
                GovernanceBreakGlassAccess.is_active.is_(True),
                GovernanceBreakGlassAccess.expires_at.isnot(None),
                GovernanceBreakGlassAccess.expires_at < now,
            )
            .all()
        )
        for access in stale:
            access.is_active = False
        return len(stale)
