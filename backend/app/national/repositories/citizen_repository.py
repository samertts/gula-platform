from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.national.domain.citizen import Citizen
from app.national.repositories.base import Repository


class CitizenRepository(Repository[Citizen]):
    def __init__(self, db: Session) -> None:
        self.db = db

    async def get(self, id: str) -> Citizen | None:
        return self.db.query(Citizen).filter(Citizen.id == id, ~Citizen.is_deleted).first()

    async def get_by_health_number(self, health_number: str) -> Citizen | None:
        return self.db.query(Citizen).filter(Citizen.health_number == health_number, ~Citizen.is_deleted).first()

    async def get_by_national_id_hash(self, nid_hash: str) -> Citizen | None:
        return self.db.query(Citizen).filter(Citizen.national_id_hash == nid_hash, ~Citizen.is_deleted).first()

    async def list(self, skip: int = 0, limit: int = 100, **filters: Any) -> list[Citizen]:
        query = self.db.query(Citizen).filter(~Citizen.is_deleted)
        for key, value in filters.items():
            if hasattr(Citizen, key) and value is not None:
                query = query.filter(getattr(Citizen, key) == value)
        return query.offset(skip).limit(limit).all()

    async def create(self, entity: Citizen) -> Citizen:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    async def update(self, entity: Citizen) -> Citizen:
        self.db.commit()
        self.db.refresh(entity)
        return entity

    async def delete(self, id: str, soft: bool = True) -> None:
        entity = await self.get(id)
        if entity:
            if soft:
                entity.soft_delete()
            else:
                self.db.delete(entity)
            self.db.commit()

    async def count(self, **filters: Any) -> int:
        query = self.db.query(Citizen).filter(~Citizen.is_deleted)
        for key, value in filters.items():
            if hasattr(Citizen, key) and value is not None:
                query = query.filter(getattr(Citizen, key) == value)
        return query.count()
