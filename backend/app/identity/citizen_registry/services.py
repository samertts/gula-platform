from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.citizen_registry.models import (
    IDENTIFIER_TYPES,
    IdentityProvider,
)


class CitizenRegistryError(Exception):
    pass


class UnsupportedIdentifierTypeError(CitizenRegistryError):
    pass


class ProviderDisabledError(CitizenRegistryError):
    pass


class CitizenRegistryService:
    """Country-agnostic citizen identity registry backed by configurable
    national identity providers."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _hash_identifier(identifier: str) -> str:
        return hashlib.sha256(identifier.encode("utf-8")).hexdigest()

    async def register_provider(
        self,
        provider_id: str,
        name_en: str,
        provider_type: str,
        country: str,
        identifier_types: list[str],
        name_ar: str | None = None,
        verification_methods: list[str] | None = None,
        configuration: dict | None = None,
        is_default: bool = False,
    ) -> IdentityProvider:
        unknown = [t for t in identifier_types if t not in IDENTIFIER_TYPES]
        if unknown:
            raise CitizenRegistryError(f"unknown_identifier_types: {unknown}")
        provider = IdentityProvider(
            id=...,
            uuid=str(uuid.uuid4()),
            provider_id=provider_id,
            name_en=name_en,
            name_ar=name_ar,
            provider_type=provider_type,
            country=country,
            identifier_types=identifier_types,
            verification_methods=verification_methods or [],
            configuration=configuration or {},
            status="active",
            is_default=is_default,
            is_active=True,
        )
        self.session.add(provider)
        await self.session.flush()
        return provider

    async def get_provider(self, provider_id: str) -> IdentityProvider | None:
        stmt = select(IdentityProvider).where(
            IdentityProvider.provider_id == provider_id,
            IdentityProvider.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_default_provider(self) -> IdentityProvider | None:
        stmt = (
            select(IdentityProvider)
            .where(
                IdentityProvider.is_default.is_(True),
                IdentityProvider.is_active.is_(True),
                IdentityProvider.status == "active",
            )
            .order_by(IdentityProvider.created_at)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_providers(self, country: str | None = None) -> list[IdentityProvider]:
        stmt = select(IdentityProvider).where(IdentityProvider.is_active.is_(True))
        if country:
            stmt = stmt.where(IdentityProvider.country == country)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def verify_citizen_identifier(
        self,
        person_id: str,
        provider_id: str,
        identifier_type: str,
        identifier: str,
    ) -> bool:
        """Verify that a citizen identifier is acceptable.

        Returns True when the provider is active and accepts the identifier
        type. Country rules remain entirely configurable — nothing is
        hard-coded to a specific nation.
        """
        if identifier_type not in IDENTIFIER_TYPES:
            raise UnsupportedIdentifierTypeError(identifier_type)
        provider = await self.get_provider(provider_id)
        if not provider:
            raise CitizenRegistryError("provider_not_found")
        if provider.status != "active":
            raise ProviderDisabledError(provider.status)
        if identifier_type not in provider.identifier_types:
            raise UnsupportedIdentifierTypeError(identifier_type)
        return bool(identifier) and len(identifier) >= 4
