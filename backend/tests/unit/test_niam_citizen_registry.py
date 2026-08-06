from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.identity.citizen_registry.models import IDENTIFIER_TYPES, IdentityProvider
from app.identity.citizen_registry.services import (
    CitizenRegistryError,
    CitizenRegistryService,
    ProviderDisabledError,
    UnsupportedIdentifierTypeError,
)


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


class TestCitizenRegistryModels:
    def test_identifier_types_are_country_agnostic(self):
        for t in [
            "national_id",
            "civil_id",
            "national_health_id",
            "social_security_number",
            "resident_id",
            "passport",
            "tax_number",
            "custom",
        ]:
            assert t in IDENTIFIER_TYPES

    def test_provider_model_instantiation(self):
        p = IdentityProvider(
            id=...,
            uuid=str(uuid.uuid4()),
            provider_id="IRQ-NID",
            name_en="Iraq National ID Service",
            name_ar="خدمة الهوية الوطنية العراقية",
            provider_type="government",
            country="IRQ",
            identifier_types=["national_id", "passport"],
            status="active",
            is_default=True,
            is_active=True,
        )
        assert p.country == "IRQ"
        assert "national_id" in p.identifier_types


class TestCitizenRegistryService:
    async def test_register_provider(self, mock_session):
        service = CitizenRegistryService(mock_session)
        provider = await service.register_provider(
            provider_id="IRQ-NID",
            name_en="Iraq National ID",
            provider_type="government",
            country="IRQ",
            identifier_types=["national_id", "civil_id"],
            is_default=True,
        )
        assert provider.status == "active"
        assert provider.identifier_types == ["national_id", "civil_id"]

    async def test_register_provider_rejects_unknown_identifier(self, mock_session):
        service = CitizenRegistryService(mock_session)
        with pytest.raises(CitizenRegistryError):
            await service.register_provider(
                provider_id="X",
                name_en="X",
                provider_type="government",
                country="XX",
                identifier_types=["flying_saucer_id"],
            )

    async def test_verify_citizen_identifier_ok(self, mock_session):
        provider = IdentityProvider(
            id="p1",
            uuid=str(uuid.uuid4()),
            provider_id="IRQ-NID",
            name_en="IRQ NID",
            provider_type="government",
            country="IRQ",
            identifier_types=["national_id", "passport"],
            status="active",
            is_active=True,
        )
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: provider))
        service = CitizenRegistryService(mock_session)
        assert await service.verify_citizen_identifier(
            person_id="p1", provider_id="IRQ-NID", identifier_type="national_id", identifier="1234567890"
        ) is True

    async def test_verify_rejects_disabled_provider(self, mock_session):
        provider = IdentityProvider(
            id="p1",
            uuid=str(uuid.uuid4()),
            provider_id="IRQ-NID",
            name_en="IRQ NID",
            provider_type="government",
            country="IRQ",
            identifier_types=["national_id"],
            status="maintenance",
            is_active=True,
        )
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: provider))
        service = CitizenRegistryService(mock_session)
        with pytest.raises(ProviderDisabledError):
            await service.verify_citizen_identifier(
                person_id="p1", provider_id="IRQ-NID", identifier_type="national_id", identifier="1234"
            )

    async def test_verify_rejects_unsupported_identifier(self, mock_session):
        provider = IdentityProvider(
            id="p1",
            uuid=str(uuid.uuid4()),
            provider_id="IRQ-NID",
            name_en="IRQ NID",
            provider_type="government",
            country="IRQ",
            identifier_types=["national_id"],
            status="active",
            is_active=True,
        )
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: provider))
        service = CitizenRegistryService(mock_session)
        with pytest.raises(UnsupportedIdentifierTypeError):
            await service.verify_citizen_identifier(
                person_id="p1", provider_id="IRQ-NID", identifier_type="passport", identifier="AB123"
            )

    async def test_verify_rejects_unknown_type(self, mock_session):
        service = CitizenRegistryService(mock_session)
        with pytest.raises(UnsupportedIdentifierTypeError):
            await service.verify_citizen_identifier(
                person_id="p1", provider_id="IRQ-NID", identifier_type="universe_id", identifier="1234"
            )

    async def test_verify_rejects_missing_provider(self, mock_session):
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: None))
        service = CitizenRegistryService(mock_session)
        with pytest.raises(CitizenRegistryError):
            await service.verify_citizen_identifier(
                person_id="p1", provider_id="GHOST", identifier_type="national_id", identifier="1234"
            )

    async def test_get_default_provider(self, mock_session):
        provider = IdentityProvider(
            id="p1",
            uuid=str(uuid.uuid4()),
            provider_id="IRQ-NID",
            name_en="IRQ NID",
            provider_type="government",
            country="IRQ",
            identifier_types=["national_id"],
            status="active",
            is_default=True,
            is_active=True,
        )
        result = MagicMock()
        result.scalars.return_value.first.return_value = provider
        mock_session.execute = AsyncMock(return_value=result)
        service = CitizenRegistryService(mock_session)
        assert (await service.get_default_provider()) is provider

    def test_hash_identifier_deterministic(self):
        service = CitizenRegistryService(MagicMock())
        assert (
            service._hash_identifier("irq-national-id-123")
            == service._hash_identifier("irq-national-id-123")
        )
        assert service._hash_identifier("a") != service._hash_identifier("b")
