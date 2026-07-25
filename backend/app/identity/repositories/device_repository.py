from sqlalchemy import select

from app.identity.models.device import Device
from app.identity.repositories.base import IdentityRepositoryBase


class DeviceRepository(IdentityRepositoryBase[Device]):
    model_class = Device

    async def find_by_fingerprint(self, fingerprint: str) -> Device | None:
        stmt = select(self.model_class).where(
            self.model_class.device_fingerprint == fingerprint,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_person_id(self, person_id: str) -> list[Device]:
        stmt = select(self.model_class).where(
            self.model_class.person_id == person_id,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_account_id(self, account_id: str) -> list[Device]:
        stmt = select(self.model_class).where(
            self.model_class.account_id == account_id,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_trusted(self, person_id: str) -> list[Device]:
        stmt = select(self.model_class).where(
            self.model_class.person_id == person_id,
            self.model_class.trusted.is_(True),
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
