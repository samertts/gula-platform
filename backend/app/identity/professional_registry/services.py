from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.professional_registry.models import (
    PROFESSION_CATEGORIES,
    ProfessionalRegistryEntry,
)

DEFAULT_VERIFICATION_WINDOW_DAYS = 90


class RegistryError(Exception):
    pass


class VerificationRequiredError(RegistryError):
    """Raised when operational privileges are requested before verification."""


class ProfessionalRegistryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register(
        self,
        person_id: str,
        identity_id: str,
        profession: str,
        registration_number: str,
        issuing_authority: str,
        issued_at: date,
        specialty: str | None = None,
        issuing_authority_id: str | None = None,
        issuing_country: str = "IRQ",
        expires_at: date | None = None,
        license_number: str | None = None,
    ) -> ProfessionalRegistryEntry:
        if profession not in PROFESSION_CATEGORIES:
            raise RegistryError(
                f"invalid profession '{profession}'; allowed: {PROFESSION_CATEGORIES}"
            )
        entry = ProfessionalRegistryEntry(
            id=...,
            uuid=str(uuid.uuid4()),
            registry_id=f"REG-{uuid.uuid4().hex[:16].upper()}",
            person_id=person_id,
            identity_id=identity_id,
            profession=profession,
            specialty=specialty,
            registration_number=registration_number,
            issuing_authority=issuing_authority,
            issuing_authority_id=issuing_authority_id,
            issuing_country=issuing_country,
            status="pending",
            verified=False,
            license_number=license_number,
            license_verified=False,
            issued_at=issued_at,
            expires_at=expires_at,
            is_active=True,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get_entry(self, registry_id: str) -> ProfessionalRegistryEntry | None:
        stmt = select(ProfessionalRegistryEntry).where(
            ProfessionalRegistryEntry.registry_id == registry_id,
            ProfessionalRegistryEntry.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_entry_by_registration_number(
        self, registration_number: str
    ) -> ProfessionalRegistryEntry | None:
        stmt = select(ProfessionalRegistryEntry).where(
            ProfessionalRegistryEntry.registration_number == registration_number,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_person(self, person_id: str) -> list[ProfessionalRegistryEntry]:
        stmt = select(ProfessionalRegistryEntry).where(
            ProfessionalRegistryEntry.person_id == person_id,
            ProfessionalRegistryEntry.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def verify(
        self,
        registry_id: str,
        verified_by: str,
        verification_method: str = "authority_confirmation",
    ) -> ProfessionalRegistryEntry:
        """Verify a professional registration.

        This is the ONLY path that activates privileges. It must be invoked by
        the responsible issuing authority (or an explicitly authorized verifier
        within it). Clinical privileges are never activated automatically.
        """
        entry = await self.get_entry(registry_id)
        if not entry:
            raise RegistryError("entry_not_found")
        if entry.status == "revoked":
            raise RegistryError("entry_revoked")
        if entry.expires_at and entry.expires_at < date.today():
            raise RegistryError("entry_expired")

        entry.verified = True
        entry.verified_at = datetime.now(UTC)
        entry.verified_by = verified_by
        entry.verification_method = verification_method
        entry.status = "verified"
        entry.license_verified = bool(entry.license_number)
        entry.privileges_activated_at = datetime.now(UTC)
        entry.privileges_activated_by = verified_by
        await self.session.flush()
        return entry

    async def suspend(self, registry_id: str, reason: str, actor: str) -> ProfessionalRegistryEntry:
        entry = await self.get_entry(registry_id)
        if not entry:
            raise RegistryError("entry_not_found")
        entry.status = "suspended"
        entry.status_reason = reason
        # Privileges are revoked immediately on suspension.
        entry.privileges_activated_at = None
        entry.privileges_activated_by = None
        await self.session.flush()
        return entry

    async def revoke(self, registry_id: str, reason: str, actor: str) -> ProfessionalRegistryEntry:
        entry = await self.get_entry(registry_id)
        if not entry:
            raise RegistryError("entry_not_found")
        entry.status = "revoked"
        entry.status_reason = reason
        entry.verified = False
        entry.privileges_activated_at = None
        entry.privileges_activated_by = None
        await self.session.flush()
        return entry

    async def is_privileged(
        self,
        person_id: str,
        profession: str | None = None,
    ) -> bool:
        """Authoritative gate for professional privileges.

        Returns True ONLY for entries that have been verified by the issuing
        authority, are not expired, and are not suspended/revoked. This is the
        single enforcement point the authorization layer must consult.
        """
        entries = await self.list_for_person(person_id)
        today = date.today()
        for entry in entries:
            if profession and entry.profession != profession:
                continue
            if not entry.verified:
                continue
            if entry.status != "verified":
                continue
            if entry.expires_at and entry.expires_at < today:
                continue
            return True
        return False

    async def check_verification_renewal_due(self, registry_id: str) -> bool:
        entry = await self.get_entry(registry_id)
        if not entry or not entry.verified_at:
            return True
        threshold = entry.verified_at + timedelta(days=DEFAULT_VERIFICATION_WINDOW_DAYS)
        return datetime.now(UTC) > threshold
