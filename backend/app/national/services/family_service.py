from __future__ import annotations

from typing import Any

from app.national.domain.family import Family, FamilyMember
from app.national.exceptions import FamilyNotFoundError
from shared.events import events


class FamilyService:
    async def create_family(self, data: dict[str, Any]) -> Family:
        family = Family(**{k: v for k, v in data.items() if hasattr(Family, k)})
        events.emit("national.family.created", {"family_id": family.id, **data})
        return family

    async def add_member(self, family_id: str, member_data: dict[str, Any]) -> FamilyMember:
        member = FamilyMember(family_id=family_id, **{k: v for k, v in member_data.items() if hasattr(FamilyMember, k)})
        events.emit("national.family.member_added", {"family_id": family_id, **member_data})
        return member

    async def remove_member(self, family_id: str, member_id: str) -> None:
        events.emit("national.family.member_removed", {"family_id": family_id, "member_id": member_id})

    async def get_family(self, family_id: str) -> Family:
        family = Family.query.get(family_id)
        if not family:
            raise FamilyNotFoundError(family_id)
        return family

    async def get_family_by_hash(self, family_hash: str) -> Family | None:
        return Family.query.filter(Family.family_id_hash == family_hash).first()
