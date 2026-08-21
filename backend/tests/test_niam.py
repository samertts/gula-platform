from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app._compat import UTC
from app.identity.events import IdentityEventBus, event_bus
from app.identity.models.account import Account, AccountStatus, AccountType
from app.identity.models.assignment import Assignment, AssignmentStatus
from app.identity.models.audit import AuditAction, IdentityAuditEntry
from app.identity.models.credential import Credential, CredentialType
from app.identity.models.device import Device
from app.identity.models.employment import Employment, EmploymentStatus
from app.identity.models.enterprise_account import EnterpriseAccount
from app.identity.models.identity import IdentityRecord, IdentityType
from app.identity.models.license import LicenseStatus, ProfessionalLicense
from app.identity.models.machine_identity import MachineIdentity
from app.identity.models.niam_organization import ORG_TYPES, NIAMOrganization
from app.identity.models.person import Person
from app.identity.models.policy import IdentityPolicy
from app.identity.models.session import UserSession
from app.identity.policy_engine import PolicyContext, PolicyEngine
from app.identity.repositories.account_repository import AccountRepository
from app.identity.repositories.person_repository import PersonRepository
from app.identity.repositories.session_repository import SessionRepository
from app.identity.services.account_service import AccountService
from app.identity.services.audit_service import AuditService
from app.identity.services.authentication_service import AuthenticationService
from app.identity.services.device_service import DeviceOwnershipError, DeviceService
from app.identity.services.person_service import PersonService
from app.identity.services.session_service import SessionService
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


def _make_mock_execute(return_val=None):
    """Configure session.execute to return a mock result that returns return_val
    when scalar_one_or_none() is called."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = return_val
    return mock_result


@pytest.fixture
def person_repo(mock_session):
    return PersonRepository(mock_session)


@pytest.fixture
def account_repo(mock_session):
    return AccountRepository(mock_session)


@pytest.fixture
def session_repo(mock_session):
    return SessionRepository(mock_session)


class TestModels:
    """Verify that all model classes are importable and instantiable."""

    def test_person_model(self):
        p = Person(
            uuid=str(uuid.uuid4()),
            given_name="علي",
            family_name="الجنابي",
            is_active=True,
        )
        assert p.given_name == "علي"
        assert p.family_name == "الجنابي"
        assert p.is_active is True
        assert p.uuid is not None

    def test_identity_model(self):
        ident = IdentityRecord(
            uuid=str(uuid.uuid4()),
            person_id="test_person_id",
            identity_type=IdentityType.citizen.value,
            status="active",
            issued_at=datetime.now(UTC),
            is_active=True,
        )
        assert ident.identity_type == "citizen"
        assert ident.status == "active"

    def test_account_model(self):
        acct = Account(
            uuid=str(uuid.uuid4()),
            identity_id="test_identity_id",
            account_type=AccountType.human.value,
            status=AccountStatus.active.value,
            is_active=True,
        )
        assert acct.account_type == "human"
        assert acct.status == "active"

    def test_organization_model(self):
        org = NIAMOrganization(
            uuid=str(uuid.uuid4()),
            org_id="MOH-IRQ",
            name_en="Ministry of Health Iraq",
            name_ar="وزارة الصحة العراقية",
            org_type="ministry",
            status="active",
            is_active=True,
        )
        assert org.org_id == "MOH-IRQ"
        assert org.org_type in ORG_TYPES

    def test_employment_model(self):
        emp = Employment(
            uuid=str(uuid.uuid4()),
            person_id="p1",
            organization_id="o1",
            employment_type="full_time",
            status=EmploymentStatus.active.value,
            position="Lab Technician",
            start_date=datetime.now(UTC).date(),
            is_active=True,
        )
        assert emp.status == "active"
        assert emp.employment_type == "full_time"

    def test_assignment_model(self):
        a = Assignment(
            uuid=str(uuid.uuid4()),
            employment_id="e1",
            person_id="p1",
            role_id="lab_technician",
            assignment_type="primary",
            status=AssignmentStatus.active.value,
            start_date=datetime.now(UTC).date(),
            is_active=True,
        )
        assert a.role_id == "lab_technician"
        assert a.status == "active"

    def test_license_model(self):
        lic = ProfessionalLicense(
            uuid=str(uuid.uuid4()),
            person_id="p1",
            license_type="medical",
            license_number="LIC-001",
            license_name="Medical License",
            issuing_authority="MOH",
            issue_date=datetime.now(UTC).date(),
            status=LicenseStatus.active.value,
            is_active=True,
        )
        assert lic.license_number == "LIC-001"
        assert lic.status == "active"

    def test_credential_model(self):
        cred = Credential(
            uuid=str(uuid.uuid4()),
            account_id="a1",
            credential_type=CredentialType.password.value,
            credential_value="$2b$12$hashvalue",
            is_primary=False,
            is_active=True,
        )
        assert cred.credential_type == "password"
        assert cred.is_primary is False

    def test_session_model(self):
        sess = UserSession(
            uuid=str(uuid.uuid4()),
            account_id="a1",
            token_jti=str(uuid.uuid4()),
            session_type="web",
            started_at=datetime.now(UTC),
            last_activity_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            is_active=True,
        )
        assert sess.session_type == "web"
        assert sess.is_active is True
        assert sess.expires_at > sess.started_at

    def test_device_model(self):
        d = Device(
            uuid=str(uuid.uuid4()),
            person_id="p1",
            device_fingerprint="fp-abc-123",
            trusted=False,
            is_active=True,
        )
        assert d.device_fingerprint == "fp-abc-123"
        assert d.trusted is False

    def test_machine_identity_model(self):
        m = MachineIdentity(
            uuid=str(uuid.uuid4()),
            organization_id="o1",
            machine_name="Sysmex-XN1000",
            machine_type="lab_instrument",
            is_active=True,
        )
        assert m.machine_name == "Sysmex-XN1000"
        assert m.machine_type == "lab_instrument"

    def test_policy_model(self):
        pol = IdentityPolicy(
            uuid=str(uuid.uuid4()),
            policy_id="POL-LAB-RESULTS-READ",
            name="Lab Results Read",
            policy_type="abac",
            effect="allow",
            actions=["read"],
            resources=["lab_results"],
            subjects=["lab_technician"],
            created_by="system",
            is_active=True,
        )
        assert pol.policy_id == "POL-LAB-RESULTS-READ"
        assert pol.effect == "allow"

    def test_audit_entry_model(self):
        entry = IdentityAuditEntry(
            uuid=str(uuid.uuid4()),
            action=AuditAction.account_created.value,
            outcome="success",
            occurred_at=datetime.now(UTC),
        )
        assert entry.action == "account_created"
        assert entry.outcome == "success"

    def test_enterprise_account_model(self):
        ea = EnterpriseAccount(
            uuid=str(uuid.uuid4()),
            organization_id="o1",
            display_name="LabLink Integration",
            is_active=True,
        )
        assert ea.display_name == "LabLink Integration"

    def test_organization_types_list(self):
        assert "ministry" in ORG_TYPES
        assert "directorate" in ORG_TYPES
        assert "private_laboratory" in ORG_TYPES
        assert len(ORG_TYPES) >= 18

    def test_identity_type_enum(self):
        assert IdentityType.citizen.value == "citizen"
        assert IdentityType.machine.value == "machine"
        assert IdentityType.guest.value == "guest"
        assert IdentityType.external_federation.value == "external_federation"

    def test_account_type_enum(self):
        assert AccountType.human.value == "human"
        assert AccountType.machine.value == "machine"
        assert AccountType.service.value == "service"
        assert AccountType.system.value == "system"

    def test_account_status_enum(self):
        assert AccountStatus.active.value == "active"
        assert AccountStatus.locked.value == "locked"
        assert AccountStatus.suspended.value == "suspended"
        assert AccountStatus.pending_verification.value == "pending_verification"

    def test_employment_status_enum(self):
        assert EmploymentStatus.active.value == "active"
        assert EmploymentStatus.on_leave.value == "on_leave"
        assert EmploymentStatus.terminated.value == "terminated"
        assert EmploymentStatus.transferred.value == "transferred"

    def test_assignment_status_enum(self):
        assert AssignmentStatus.active.value == "active"
        assert AssignmentStatus.completed.value == "completed"
        assert AssignmentStatus.expired.value == "expired"

    def test_license_status_enum(self):
        assert LicenseStatus.active.value == "active"
        assert LicenseStatus.revoked.value == "revoked"
        assert LicenseStatus.pending.value == "pending"

    def test_credential_type_enum(self):
        assert CredentialType.password.value == "password"
        assert CredentialType.passkey.value == "passkey"
        assert CredentialType.fido2.value == "fido2"
        assert CredentialType.biometric.value == "biometric"

    def test_audit_action_enum(self):
        assert AuditAction.person_created.value == "person_created"
        assert AuditAction.account_locked.value == "account_locked"
        assert AuditAction.bootstrap_completed.value == "bootstrap_completed"
        assert len(AuditAction) >= 35


class TestServices:
    """Verify service layer methods exist and accept correct types."""

    @pytest.mark.asyncio
    async def test_person_service_create(self, mock_session):
        svc = PersonService(mock_session)
        result = await svc.create_person(
            given_name="Test",
            family_name="User",
            phone="+964771234567",
        )
        assert isinstance(result, Person)
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_person_service_get(self, mock_session):
        svc = PersonService(mock_session)
        mock_session.execute.return_value = _make_mock_execute(None)
        result = await svc.get_person("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_person_service_deactivate(self, mock_session):
        svc = PersonService(mock_session)
        mock_session.execute.return_value = _make_mock_execute(None)
        with patch.object(PersonRepository, "get_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = Person(
                uuid=str(uuid.uuid4()),
                id="test-id",
                given_name="X",
                family_name="Y",
            )
            await svc.deactivate_person("test-id")
            assert True

    @pytest.mark.asyncio
    async def test_account_service_create(self, mock_session):
        svc = AccountService(mock_session)
        result = await svc.create_account(
            identity_id="id-1",
            email="test@gula.iq",
            password="SecurePass123!@#",
        )
        assert isinstance(result, Account)
        assert result.email == "test@gula.iq"

    @pytest.mark.asyncio
    async def test_account_service_lookup(self, mock_session):
        svc = AccountService(mock_session)
        mock_session.execute.return_value = _make_mock_execute(None)
        result = await svc.find_by_email("nonexistent@test.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_authentication_service_login_failure(self, mock_session):
        svc = AuthenticationService(mock_session)
        mock_session.execute.return_value = _make_mock_execute(None)
        result = await svc.login(login="bad@user.com", password="wrongpass")
        assert result is None

    @pytest.mark.asyncio
    async def test_session_service_terminate(self, mock_session):
        svc = SessionService(mock_session)
        mock_session.execute.return_value = _make_mock_execute(None)
        with patch.object(SessionRepository, "get_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = UserSession(
                uuid=str(uuid.uuid4()),
                id="sess-1",
                account_id="a1",
                token_jti="jti-1",
                session_type="web",
                started_at=datetime.now(UTC),
                last_activity_at=datetime.now(UTC),
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
            await svc.terminate("sess-1", "test")
            assert True

    @pytest.mark.asyncio
    async def test_device_service_register(self, mock_session):
        svc = DeviceService(mock_session)
        mock_session.execute.return_value = _make_mock_execute(None)
        result = await svc.register_device(
            person_id="p1",
            device_fingerprint="fp-new-device",
            device_name="iPhone 15",
            device_type="mobile",
        )
        assert isinstance(result, Device)
        assert result.device_fingerprint == "fp-new-device"

    @pytest.mark.asyncio
    async def test_device_service_rejects_cross_account_fingerprint(
        self, mock_session: MagicMock
    ) -> None:
        svc = DeviceService(mock_session)
        existing = Device(
            id="device-1",
            person_id="person-1",
            account_id="account-1",
            device_fingerprint="fp-existing",
            is_active=True,
        )
        svc.repo.find_by_fingerprint = AsyncMock(return_value=existing)

        with pytest.raises(DeviceOwnershipError):
            await svc.register_device(
                person_id="person-2",
                account_id="account-2",
                device_fingerprint="fp-existing",
            )
        mock_session.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_audit_service_record(self, mock_session):
        svc = AuditService(mock_session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        result = await svc.record(
            action=AuditAction.person_created,
            actor_id="admin-1",
            target_type="person",
            target_id="p-1",
        )
        assert isinstance(result, IdentityAuditEntry)
        assert result.action == "person_created"
        assert result.entry_hash is not None


class TestPolicyEngine:
    """Verify fail-closed compatibility behavior."""

    @pytest.mark.asyncio
    async def test_policy_evaluate_without_trusted_actor_denies_by_default(self):
        engine = PolicyEngine()
        ctx = PolicyContext(
            subject_id="u1",
            subject_type="user",
            action="read",
            resource_type="lab_result",
        )
        result = await engine.evaluate(ctx)
        assert result is False

    def test_policy_context_defaults(self):
        ctx = PolicyContext(
            subject_id="u1",
            subject_type="user",
            action="read",
            resource_type="lab_result",
        )
        assert ctx.resource_id is None
        assert ctx.organization_id is None
        assert ctx.environment == {}


class TestEventBus:
    """Verify event bus stub."""

    def test_event_bus_publish_subscribe(self):
        results = []

        def handler(payload):
            results.append(payload)

        event_bus.subscribe("test.event", handler)
        event_bus.publish("test.event", {"key": "value"})
        assert len(results) == 1
        assert results[0]["key"] == "value"

    def test_event_bus_multiple_handlers(self):
        results = []

        def h1(payload):
            results.append("h1")

        def h2(payload):
            results.append("h2")

        bus = IdentityEventBus()
        bus.subscribe("multi", h1)
        bus.subscribe("multi", h2)
        bus.publish("multi", {})
        assert results == ["h1", "h2"]


class TestRepositoryBase:
    """Verify repository base class."""

    @pytest.mark.asyncio
    async def test_base_create(self, mock_session):
        from app.identity.repositories.base import IdentityRepositoryBase

        repo = IdentityRepositoryBase(mock_session)
        entity = MagicMock()
        result = await repo.create(entity)
        assert result == entity
        mock_session.add.assert_called_once_with(entity)
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_base_soft_delete(self, mock_session):
        from app.identity.repositories.person_repository import PersonRepository

        repo = PersonRepository(mock_session)
        mock_session.execute.return_value = _make_mock_execute(None)
        await repo.soft_delete("entity-id")
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()


class TestBootstrap:
    """Verify bootstrap seed functions."""

    @pytest.mark.asyncio
    async def test_seed_master_admin(self, mock_session):
        from app.identity.bootstrap.seed import seed_master_admin

        result = await seed_master_admin(mock_session)
        assert isinstance(result, str)
        assert len(result) > 0
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_seed_platform_organization(self, mock_session):
        from app.identity.bootstrap.seed import seed_platform_organization

        result = await seed_platform_organization(mock_session)
        assert isinstance(result, str)
        assert len(result) > 0


class TestModelsImports:
    """Verify all __init__ exports work."""

    def test_models_init_exports(self):
        from app.identity.models import (
            Account,
            AccountStatus,
            AccountType,
            Assignment,
            AssignmentStatus,
            Credential,
            CredentialType,
            Device,
            Employment,
            EmploymentStatus,
            EnterpriseAccount,
            IdentityAuditEntry,
            IdentityPolicy,
            IdentityRecord,
            IdentityType,
            LicenseStatus,
            MachineIdentity,
            NIAMOrganization,
            Person,
            ProfessionalLicense,
            UserSession,
        )
        assert Person is not None
        assert IdentityType is not None
        assert Account is not None
        assert NIAMOrganization is not None
        assert IdentityPolicy is not None
        assert IdentityAuditEntry is not None

    def test_services_init_exports(self):
        from app.identity.services import (
            AccountService,
            AuditService,
            AuthenticationService,
            AuthorizationService,
            DeviceService,
            IdentityService,
            PersonService,
            SessionService,
        )
        assert PersonService is not None
        assert AuthenticationService is not None
        assert AuditService is not None

    def test_repositories_init_exports(self):
        from app.identity.repositories import (
            AccountRepository,
            AssignmentRepository,
            DeviceRepository,
            EmploymentRepository,
            IdentityRepository,
            OrganizationRepository,
            PersonRepository,
            SessionRepository,
        )
        assert PersonRepository is not None
        assert OrganizationRepository is not None
        assert SessionRepository is not None


class TestAuditActions:
    """Verify all audit actions cover the lifecycle."""

    def test_all_audit_actions_defined(self):
        actions = {a.value for a in AuditAction}
        required = {
            "person_created",
            "person_updated",
            "identity_created",
            "identity_verified",
            "account_created",
            "account_locked",
            "account_unlocked",
            "account_password_changed",
            "account_mfa_enabled",
            "session_started",
            "session_terminated",
            "role_assigned",
            "role_revoked",
            "permission_granted",
            "policy_created",
            "policy_denied",
            "breach_detected",
            "organization_created",
            "bootstrap_completed",
        }
        missing = required - actions
        assert not missing, f"Missing audit actions: {missing}"
