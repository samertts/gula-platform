from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.services.governance.identity_governance import (
    IdentityGovernanceService,
    RelationshipType,
)

logger = logging.getLogger("gula.identity.family")


@dataclass
class FamilyMember:
    health_number: str = ""
    full_name: str = ""
    relationship: str = ""
    date_of_birth: str = ""
    is_dependent: bool = False


@dataclass
class FamilyRecord:
    id: str = ""
    family_id_hash: str = ""
    family_name: str = ""
    primary_member_hn: str = ""
    members: list[FamilyMember] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


class FamilyRegistryService:
    def __init__(self, identity_service: IdentityGovernanceService):
        self._identity = identity_service
        self._families: dict[str, FamilyRecord] = {}
        self._member_index: dict[str, str] = {}

    def create_family(
        self,
        family_name: str,
        primary_member_hn: str,
        family_id: str = "",
    ) -> FamilyRecord:
        family_id_hash = self._hash_family_id(family_id or primary_member_hn)
        record = FamilyRecord(
            family_id_hash=family_id_hash,
            family_name=family_name,
            primary_member_hn=primary_member_hn,
            members=[
                FamilyMember(
                    health_number=primary_member_hn,
                    full_name="",
                    relationship="self",
                    is_dependent=False,
                ),
            ],
        )
        self._families[record.id] = record
        self._member_index[primary_member_hn] = record.id
        logger.info("Family created: %s (primary: %s)", family_name, primary_member_hn)
        return record

    def add_member(
        self,
        family_id: str,
        health_number: str,
        relationship: str,
        full_name: str = "",
        is_dependent: bool = False,
    ) -> FamilyRecord:
        family = self._get_family(family_id)
        member = FamilyMember(
            health_number=health_number,
            full_name=full_name,
            relationship=relationship,
            is_dependent=is_dependent,
        )
        family.members.append(member)
        self._member_index[health_number] = family.id
        family.updated_at = datetime.now(UTC)

        dependent = self._identity._get_by_health_number(health_number)
        dependent.relationships.append({
            "related_to": family.primary_member_hn,
            "relationship_type": relationship,
            "family_id": family.id,
            "added_at": datetime.now(UTC).isoformat(),
        })
        dependent.add_history_entry({
            "action": "family_member_added",
            "family_id": family.id,
            "relationship": relationship,
        })

        logger.info(
            "Member %s added to family %s as %s",
            health_number,
            family.family_name,
            relationship,
        )
        return family

    def link_guardian(
        self, guardian_hn: str, dependent_hn: str,
    ) -> None:
        guardian = self._identity._get_by_health_number(guardian_hn)
        dependent = self._identity._get_by_health_number(dependent_hn)

        guardian.relationships.append({
            "related_to": dependent_hn,
            "relationship_type": RelationshipType.GUARDIAN.value,
            "added_at": datetime.now(UTC).isoformat(),
        })
        dependent.relationships.append({
            "related_to": guardian_hn,
            "relationship_type": RelationshipType.CHILD.value,
            "added_at": datetime.now(UTC).isoformat(),
        })
        guardian.add_history_entry({
            "action": "guardian_linked",
            "dependent": dependent_hn,
        })
        dependent.add_history_entry({
            "action": "guardian_assigned",
            "guardian": guardian_hn,
        })
        logger.info("Guardian linked: %s -> %s", guardian_hn, dependent_hn)

    def get_family_by_member(
        self, health_number: str,
    ) -> FamilyRecord | None:
        family_id = self._member_index.get(health_number)
        if family_id:
            return self._families.get(family_id)
        return None

    def get_family(self, family_id: str) -> FamilyRecord:
        family = self._families.get(family_id)
        if not family:
            raise ValueError(f"Family not found: {family_id}")
        return family

    def list_dependents(
        self, health_number: str,
    ) -> list[FamilyMember]:
        family = self.get_family_by_member(health_number)
        if not family:
            return []
        return [
            m for m in family.members
            if m.is_dependent
        ]

    def list_guardians(
        self, health_number: str,
    ) -> list[FamilyMember]:
        family = self.get_family_by_member(health_number)
        if not family:
            return []
        return [
            m for m in family.members
            if not m.is_dependent and m.health_number != health_number
        ]

    def _get_family(self, family_id: str) -> FamilyRecord:
        family = self._families.get(family_id)
        if not family:
            raise ValueError(f"Family not found: {family_id}")
        return family

    def _hash_family_id(self, family_id: str) -> str:
        return hashlib.sha256(family_id.encode()).hexdigest()
