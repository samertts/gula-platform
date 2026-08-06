from __future__ import annotations

import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.identity.professional_registry.models import (
    PROFESSION_CATEGORIES,
    ProfessionalRegistryEntry,
)
from app.identity.professional_registry.services import (
    ProfessionalRegistryService,
    RegistryError,
)


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


class TestProfessionalRegistryModels:
    def test_profession_categories_complete(self):
        for p in [
            "doctor",
            "dentist",
            "pharmacist",
            "laboratory_scientist",
            "nurse",
            "radiographer",
            "physiotherapist",
            "veterinarian",
            "researcher",
            "student",
            "retired_professional",
            "foreign_professional",
        ]:
            assert p in PROFESSION_CATEGORIES

    def test_entry_model_instantiation(self):
        e = ProfessionalRegistryEntry(
            id=...,
            uuid=str(uuid.uuid4()),
            registry_id="REG-1",
            person_id="p1",
            identity_id="id1",
            profession="doctor",
            registration_number="DOC-12345",
            issuing_authority="MOH Iraq",
            issuing_country="IRQ",
            status="pending",
            verified=False,
            issued_at=date(2024, 1, 1),
            is_active=True,
        )
        assert e.registration_number == "DOC-12345"
        assert e.verified is False


class TestProfessionalRegistryService:
    async def test_register_creates_pending_entry(self, mock_session):
        service = ProfessionalRegistryService(mock_session)
        entry = await service.register(
            person_id="p1",
            identity_id="id1",
            profession="doctor",
            registration_number="DOC-1",
            issuing_authority="MOH",
            issued_at=date(2024, 1, 1),
        )
        assert entry.status == "pending"
        assert entry.verified is False
        assert entry.privileges_activated_at is None

    async def test_register_rejects_unknown_profession(self, mock_session):
        service = ProfessionalRegistryService(mock_session)
        with pytest.raises(RegistryError):
            await service.register(
                person_id="p1",
                identity_id="id1",
                profession="alchemist",
                registration_number="A-1",
                issuing_authority="MOH",
                issued_at=date(2024, 1, 1),
            )

    async def test_verify_activates_privileges(self, mock_session):
        entry = ProfessionalRegistryEntry(
            id="e1",
            uuid=str(uuid.uuid4()),
            registry_id="REG-1",
            person_id="p1",
            identity_id="id1",
            profession="doctor",
            registration_number="DOC-1",
            issuing_authority="MOH",
            issuing_country="IRQ",
            status="pending",
            verified=False,
            license_number="L-1",
            issued_at=date(2024, 1, 1),
            is_active=True,
        )
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: entry))
        service = ProfessionalRegistryService(mock_session)
        verified = await service.verify("REG-1", verified_by="authority-user")
        assert verified.verified is True
        assert verified.status == "verified"
        assert verified.privileges_activated_at is not None
        assert verified.license_verified is True

    async def test_suspend_revokes_privileges(self, mock_session):
        entry = ProfessionalRegistryEntry(
            id="e1",
            uuid=str(uuid.uuid4()),
            registry_id="REG-1",
            person_id="p1",
            identity_id="id1",
            profession="doctor",
            registration_number="DOC-1",
            issuing_authority="MOH",
            issuing_country="IRQ",
            status="verified",
            verified=True,
            issued_at=date(2024, 1, 1),
            is_active=True,
        )
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: entry))
        service = ProfessionalRegistryService(mock_session)
        suspended = await service.suspend("REG-1", reason="misconduct", actor="a1")
        assert suspended.status == "suspended"
        assert suspended.privileges_activated_at is None

    async def test_revoke_clears_verification(self, mock_session):
        entry = ProfessionalRegistryEntry(
            id="e1",
            uuid=str(uuid.uuid4()),
            registry_id="REG-1",
            person_id="p1",
            identity_id="id1",
            profession="doctor",
            registration_number="DOC-1",
            issuing_authority="MOH",
            issuing_country="IRQ",
            status="verified",
            verified=True,
            issued_at=date(2024, 1, 1),
            is_active=True,
        )
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: entry))
        service = ProfessionalRegistryService(mock_session)
        revoked = await service.revoke("REG-1", reason="fraud", actor="a1")
        assert revoked.status == "revoked"
        assert revoked.verified is False
        assert revoked.privileges_activated_at is None

    async def test_is_privileged_requires_verified_and_current(self, mock_session):
        entry = ProfessionalRegistryEntry(
            id="e1",
            uuid=str(uuid.uuid4()),
            registry_id="REG-1",
            person_id="p1",
            identity_id="id1",
            profession="doctor",
            registration_number="DOC-1",
            issuing_authority="MOH",
            issuing_country="IRQ",
            status="verified",
            verified=True,
            issued_at=date(2024, 1, 1),
            expires_at=date.today() + timedelta(days=365),
            is_active=True,
        )
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: [entry])))
        )
        service = ProfessionalRegistryService(mock_session)
        assert await service.is_privileged("p1", "doctor") is True

    async def test_is_privileged_false_when_pending(self, mock_session):
        entry = ProfessionalRegistryEntry(
            id="e1",
            uuid=str(uuid.uuid4()),
            registry_id="REG-1",
            person_id="p1",
            identity_id="id1",
            profession="doctor",
            registration_number="DOC-1",
            issuing_authority="MOH",
            issuing_country="IRQ",
            status="pending",
            verified=False,
            issued_at=date(2024, 1, 1),
            is_active=True,
        )
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: [entry])))
        )
        service = ProfessionalRegistryService(mock_session)
        assert await service.is_privileged("p1", "doctor") is False

    async def test_is_privileged_false_when_expired(self, mock_session):
        entry = ProfessionalRegistryEntry(
            id="e1",
            uuid=str(uuid.uuid4()),
            registry_id="REG-1",
            person_id="p1",
            identity_id="id1",
            profession="doctor",
            registration_number="DOC-1",
            issuing_authority="MOH",
            issuing_country="IRQ",
            status="verified",
            verified=True,
            issued_at=date(2020, 1, 1),
            expires_at=date(2021, 1, 1),
            is_active=True,
        )
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: [entry])))
        )
        service = ProfessionalRegistryService(mock_session)
        assert await service.is_privileged("p1", "doctor") is False

    async def test_verify_rejects_revoked(self, mock_session):
        entry = ProfessionalRegistryEntry(
            id="e1",
            uuid=str(uuid.uuid4()),
            registry_id="REG-1",
            person_id="p1",
            identity_id="id1",
            profession="doctor",
            registration_number="DOC-1",
            issuing_authority="MOH",
            issuing_country="IRQ",
            status="revoked",
            verified=False,
            issued_at=date(2024, 1, 1),
            is_active=True,
        )
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: entry))
        service = ProfessionalRegistryService(mock_session)
        with pytest.raises(RegistryError):
            await service.verify("REG-1", verified_by="a1")

    async def test_list_for_person(self, mock_session):
        entry = ProfessionalRegistryEntry(
            id="e1",
            uuid=str(uuid.uuid4()),
            registry_id="REG-1",
            person_id="p1",
            identity_id="id1",
            profession="doctor",
            registration_number="DOC-1",
            issuing_authority="MOH",
            issuing_country="IRQ",
            status="verified",
            verified=True,
            issued_at=date(2024, 1, 1),
            is_active=True,
        )
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: [entry])))
        )
        service = ProfessionalRegistryService(mock_session)
        entries = await service.list_for_person("p1")
        assert len(entries) == 1
        assert entries[0].profession == "doctor"
