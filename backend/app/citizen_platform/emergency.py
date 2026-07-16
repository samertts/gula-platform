from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC

logger = logging.getLogger("gula.citizen.emergency")


@dataclass
class EmergencyAccessGrant:
    id: str = ""
    citizen_id: str = ""
    granted_to: str = ""
    granted_by: str = ""
    reason: str = ""
    scope: str = "emergency"
    granted_at: str = ""
    expires_at: str = ""
    is_active: bool = True
    audit_trail: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class EmergencyContact:
    id: str = ""
    citizen_id: str = ""
    name: str = ""
    relationship: str = ""
    phone: str = ""
    alternative_phone: str = ""
    email: str = ""
    is_notified: bool = False
    priority: int = 1


@dataclass
class CriticalHealthInfo:
    citizen_id: str = ""
    blood_group: str = ""
    allergies: list[str] = field(default_factory=list)
    chronic_conditions: list[str] = field(default_factory=list)
    current_medications: list[str] = field(default_factory=list)
    implantable_devices: list[str] = field(default_factory=list)
    organ_donor: bool = False
    emergency_notes: str = ""
    last_updated: str = ""


class EmergencyAccessService:
    def __init__(self) -> None:
        self._grants: dict[str, list[EmergencyAccessGrant]] = {}

    def grant_emergency_access(
        self,
        citizen_id: str,
        granted_to: str,
        granted_by: str,
        reason: str,
        expires_minutes: int = 60,
    ) -> EmergencyAccessGrant:
        grant = EmergencyAccessGrant(
            id=str(uuid.uuid4()),
            citizen_id=citizen_id,
            granted_to=granted_to,
            granted_by=granted_by,
            reason=reason,
            scope="emergency_full",
            granted_at=datetime.now(UTC).isoformat(),
            expires_at=datetime.now(UTC).isoformat(),
        )
        from datetime import timedelta
        grant.expires_at = (datetime.now(UTC) + timedelta(minutes=expires_minutes)).isoformat()
        grant.audit_trail.append({
            "action": "granted",
            "by": granted_by,
            "at": grant.granted_at,
        })
        if citizen_id not in self._grants:
            self._grants[citizen_id] = []
        self._grants[citizen_id].append(grant)
        return grant

    def revoke_emergency_access(self, grant_id: str, revoked_by: str) -> bool:
        for grants in self._grants.values():
            for g in grants:
                if g.id == grant_id and g.is_active:
                    g.is_active = False
                    g.audit_trail.append({
                        "action": "revoked",
                        "by": revoked_by,
                        "at": datetime.now(UTC).isoformat(),
                    })
                    return True
        return False

    def is_access_valid(self, citizen_id: str, accessor_id: str) -> bool:
        grants = self._grants.get(citizen_id, [])
        now = datetime.now(UTC).isoformat()
        return any(
            g.granted_to == accessor_id
            and g.is_active
            and g.expires_at >= now
            for g in grants
        )

    def get_access_log(self, citizen_id: str) -> list[EmergencyAccessGrant]:
        return self._grants.get(citizen_id, [])


class EmergencyContactService:
    def __init__(self) -> None:
        self._contacts: dict[str, list[EmergencyContact]] = {}

    def add_contact(
        self,
        citizen_id: str,
        name: str,
        relationship: str,
        phone: str,
        alternative_phone: str = "",
        email: str = "",
        priority: int = 1,
    ) -> EmergencyContact:
        contact = EmergencyContact(
            id=str(uuid.uuid4()),
            citizen_id=citizen_id,
            name=name,
            relationship=relationship,
            phone=phone,
            alternative_phone=alternative_phone,
            email=email,
            priority=priority,
        )
        if citizen_id not in self._contacts:
            self._contacts[citizen_id] = []
        self._contacts[citizen_id].append(contact)
        self._contacts[citizen_id].sort(key=lambda c: c.priority)
        return contact

    def update_contact(self, contact_id: str, citizen_id: str, **updates: Any) -> bool:
        contacts = self._contacts.get(citizen_id, [])
        for c in contacts:
            if c.id == contact_id:
                for key, value in updates.items():
                    if hasattr(c, key):
                        setattr(c, key, value)
                return True
        return False

    def remove_contact(self, contact_id: str, citizen_id: str) -> bool:
        contacts = self._contacts.get(citizen_id, [])
        before = len(contacts)
        self._contacts[citizen_id] = [c for c in contacts if c.id != contact_id]
        return len(self._contacts[citizen_id]) < before

    def get_contacts(self, citizen_id: str) -> list[EmergencyContact]:
        return self._contacts.get(citizen_id, [])

    def get_primary_contact(self, citizen_id: str) -> EmergencyContact | None:
        contacts = self._contacts.get(citizen_id, [])
        return contacts[0] if contacts else None

    def notify_contacts(self, citizen_id: str, message: str) -> list[str]:
        notified: list[str] = []
        contacts = self._contacts.get(citizen_id, [])
        for contact in contacts:
            contact.is_notified = True
            notified.append(contact.phone)
        return notified


class CriticalInfoService:
    def __init__(self) -> None:
        self._info: dict[str, CriticalHealthInfo] = {}

    def update_critical_info(
        self,
        citizen_id: str,
        blood_group: str = "",
        allergies: list[str] | None = None,
        chronic_conditions: list[str] | None = None,
        current_medications: list[str] | None = None,
        implantable_devices: list[str] | None = None,
        organ_donor: bool = False,
        emergency_notes: str = "",
    ) -> CriticalHealthInfo:
        info = self._info.get(citizen_id) or CriticalHealthInfo(citizen_id=citizen_id)
        if blood_group:
            info.blood_group = blood_group
        if allergies is not None:
            info.allergies = allergies
        if chronic_conditions is not None:
            info.chronic_conditions = chronic_conditions
        if current_medications is not None:
            info.current_medications = current_medications
        if implantable_devices is not None:
            info.implantable_devices = implantable_devices
        info.organ_donor = organ_donor
        if emergency_notes:
            info.emergency_notes = emergency_notes
        info.last_updated = datetime.now(UTC).isoformat()
        self._info[citizen_id] = info
        return info

    def get_critical_info(self, citizen_id: str) -> CriticalHealthInfo | None:
        return self._info.get(citizen_id)

    def get_emergency_summary(self, citizen_id: str) -> dict[str, Any] | None:
        info = self._info.get(citizen_id)
        if not info:
            return None
        return {
            "blood_group": info.blood_group,
            "allergies": info.allergies,
            "chronic_conditions": info.chronic_conditions,
            "current_medications": info.current_medications,
            "implantable_devices": info.implantable_devices,
            "organ_donor": info.organ_donor,
            "emergency_notes": info.emergency_notes,
        }
