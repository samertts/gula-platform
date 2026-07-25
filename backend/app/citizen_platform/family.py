from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app._compat import UTC

logger = logging.getLogger("gula.citizen.family")


@dataclass
class FamilyMemberInfo:
    member_id: str = ""
    citizen_id: str = ""
    full_name: str = ""
    relationship: str = ""
    date_of_birth: str = ""
    blood_group: str = ""
    is_dependent: bool = False
    is_emergency_contact: bool = False
    phone: str = ""


class FamilyAccountService:
    def __init__(self) -> None:
        self._families: dict[str, list[FamilyMemberInfo]] = {}

    def get_family_members(self, citizen_id: str) -> list[FamilyMemberInfo]:
        return self._families.get(citizen_id, [])

    def add_family_member(
        self,
        citizen_id: str,
        member_citizen_id: str,
        relationship: str,
        full_name: str = "",
        date_of_birth: str = "",
        blood_group: str = "",
        phone: str = "",
        is_dependent: bool = False,
    ) -> FamilyMemberInfo:
        member = FamilyMemberInfo(
            member_id=str(uuid.uuid4()),
            citizen_id=member_citizen_id,
            full_name=full_name,
            relationship=relationship,
            date_of_birth=date_of_birth,
            blood_group=blood_group,
            is_dependent=is_dependent,
            phone=phone,
        )
        if citizen_id not in self._families:
            self._families[citizen_id] = []
        self._families[citizen_id].append(member)
        return member

    def remove_family_member(self, citizen_id: str, member_id: str) -> bool:
        members = self._families.get(citizen_id, [])
        before = len(members)
        self._families[citizen_id] = [m for m in members if m.member_id != member_id]
        return len(self._families[citizen_id]) < before

    def get_dependents(self, citizen_id: str) -> list[FamilyMemberInfo]:
        return [m for m in self._families.get(citizen_id, []) if m.is_dependent]


class GuardianService:
    def __init__(self) -> None:
        self._guardians: dict[str, list[dict[str, Any]]] = {}

    def assign_guardian(
        self,
        citizen_id: str,
        guardian_citizen_id: str,
        guardian_type: str = "legal_guardian",
        relationship: str = "",
    ) -> dict[str, Any]:
        assignment = {
            "id": str(uuid.uuid4()),
            "citizen_id": citizen_id,
            "guardian_id": guardian_citizen_id,
            "guardian_type": guardian_type,
            "relationship": relationship,
            "assigned_at": datetime.now(UTC).isoformat(),
            "is_active": True,
        }
        if citizen_id not in self._guardians:
            self._guardians[citizen_id] = []
        self._guardians[citizen_id].append(assignment)
        return assignment

    def remove_guardian(self, citizen_id: str, guardian_id: str) -> bool:
        guardians = self._guardians.get(citizen_id, [])
        for g in guardians:
            if g["guardian_id"] == guardian_id:
                g["is_active"] = False
                return True
        return False

    def get_guardians(self, citizen_id: str) -> list[dict[str, Any]]:
        return [g for g in self._guardians.get(citizen_id, []) if g["is_active"]]

    def is_guardian(self, guardian_citizen_id: str, ward_citizen_id: str) -> bool:
        guardians = self._guardians.get(ward_citizen_id, [])
        return any(g["guardian_id"] == guardian_citizen_id and g["is_active"] for g in guardians)


class ConsentManager:
    def __init__(self) -> None:
        self._consents: dict[str, list[dict[str, Any]]] = {}

    def grant_consent(
        self,
        citizen_id: str,
        granted_to: str,
        scope: str,
        expires_at: str | None = None,
    ) -> dict[str, Any]:
        consent = {
            "id": str(uuid.uuid4()),
            "citizen_id": citizen_id,
            "granted_to": granted_to,
            "scope": scope,
            "status": "active",
            "granted_at": datetime.now(UTC).isoformat(),
            "expires_at": expires_at,
        }
        if citizen_id not in self._consents:
            self._consents[citizen_id] = []
        self._consents[citizen_id].append(consent)
        return consent

    def revoke_consent(self, citizen_id: str, consent_id: str) -> bool:
        consents = self._consents.get(citizen_id, [])
        for c in consents:
            if c["id"] == consent_id:
                c["status"] = "revoked"
                return True
        return False

    def check_consent(
        self,
        citizen_id: str,
        granted_to: str,
        scope: str,
    ) -> bool:
        consents = self._consents.get(citizen_id, [])
        return any(
            c["granted_to"] == granted_to and c["scope"] == scope and c["status"] == "active"
            for c in consents
        )

    def get_active_consents(self, citizen_id: str) -> list[dict[str, Any]]:
        return [c for c in self._consents.get(citizen_id, []) if c["status"] == "active"]

    def get_consent_history(self, citizen_id: str) -> list[dict[str, Any]]:
        return self._consents.get(citizen_id, [])
