from __future__ import annotations

from sqlalchemy import select

from app.identity.models.policy import IdentityPolicy
from app.identity.repositories.base import IdentityRepositoryBase


class PolicyRepository(IdentityRepositoryBase[IdentityPolicy]):
    """Read-only lookup for enabled policies that name an exact action."""

    model_class = IdentityPolicy

    async def find_enabled_for_action(self, action: str) -> list[IdentityPolicy]:
        statement = select(self.model_class).where(
            self.model_class.is_active.is_(True),
            self.model_class.is_enabled.is_(True),
        )
        result = await self.session.execute(statement)
        return [policy for policy in result.scalars().all() if action in (policy.actions or [])]
