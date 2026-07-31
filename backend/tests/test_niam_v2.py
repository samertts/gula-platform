from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from app._compat import UTC
from app.identity.base import IdentityBaseEntity
from app.identity.governance.models import (
    DigitalIdentityCouncil,
    IdentityAppeal,
    IdentityAuthority,
    IdentityCertificationRegistry,
    IdentityRestoration,
    IdentityReviewBoard,
    IdentitySuspension,
    NationalIdentityRegistry,
    PolicyApprovalWorkflow,
)
from app.identity.governance.services import (
    AppealService,
    GovernanceService,
    PolicyApprovalService,
    RegistryService,
    SuspensionService,
)
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


class TestGovernanceModels:
    """Verify all 9 governance models are importable and instantiable."""

    def test_identity_authority_model(self):
        a = IdentityAuthority(
            uuid=str(uuid.uuid4()),
            authority_id="IA-MOH-IRQ",
            name_en="Ministry of Health Identity Authority",
            name_ar="هوية وزارة الصحة",
            authority_type="identity_authority",
            jurisdiction="national",
            status="active",
            is_active=True,
        )
        assert a.authority_id == "IA-MOH-IRQ"
        assert a.authority_type == "identity_authority"

    def test_digital_identity_council_model(self):
        c = DigitalIdentityCouncil(
            uuid=str(uuid.uuid4()),
            council_id="C-GOV-001",
            name_en="National Digital Identity Governance Council",
            name_ar="مجلس حوكمة الهوية الرقمية الوطنية",
            council_type="governance",
            status="active",
            is_active=True,
        )
        assert c.council_id == "C-GOV-001"
        assert c.council_type == "governance"

    def test_policy_approval_workflow_model(self):
        w = PolicyApprovalWorkflow(
            uuid=str(uuid.uuid4()),
            workflow_id="WF-POL-001",
            policy_id="POL-001",
            submitted_by="admin",
            submitted_at=datetime.now(UTC),
            status="draft",
            is_active=True,
        )
        assert w.workflow_id == "WF-POL-001"
        assert w.status == "draft"

    def test_identity_appeal_model(self):
        a = IdentityAppeal(
            uuid=str(uuid.uuid4()),
            appeal_id="APL-001",
            appellant_person_id="p1",
            identity_id="id1",
            appeal_type="suspension",
            reason="Incorrect suspension",
            status="submitted",
            is_active=True,
        )
        assert a.appeal_id == "APL-001"
        assert a.status == "submitted"

    def test_identity_suspension_model(self):
        s = IdentitySuspension(
            uuid=str(uuid.uuid4()),
            suspension_id="SUS-001",
            person_id="p1",
            identity_id="id1",
            reason="Security breach",
            severity="high",
            suspended_by="admin",
            suspended_at=datetime.now(UTC),
            status="active",
            is_active=True,
        )
        assert s.suspension_id == "SUS-001"
        assert s.severity == "high"

    def test_identity_restoration_model(self):
        r = IdentityRestoration(
            uuid=str(uuid.uuid4()),
            restoration_id="RST-001",
            person_id="p1",
            identity_id="id1",
            request_reason="Issue resolved",
            requested_by="user",
            status="requested",
            restoration_type="manual",
            is_active=True,
        )
        assert r.restoration_id == "RST-001"
        assert r.status == "requested"

    def test_national_identity_registry_model(self):
        r = NationalIdentityRegistry(
            uuid=str(uuid.uuid4()),
            registry_id="REG-001",
            person_id="p1",
            identity_id="id1",
            registry_type="citizen",
            registration_number="IRQ-2026-000001",
            registered_at=datetime.now(UTC),
            registered_by="admin",
            status="active",
            is_active=True,
        )
        assert r.registration_number == "IRQ-2026-000001"
        assert r.registry_type == "citizen"

    def test_identity_certification_registry_model(self):
        c = IdentityCertificationRegistry(
            uuid=str(uuid.uuid4()),
            certification_id="CERT-001",
            person_id="p1",
            certifying_authority_id="auth1",
            certification_type="identity_proofing",
            certification_number="CERT-IRQ-001",
            issue_date=datetime.now(UTC).date(),
            verified_by="verifier",
            verification_method="in_person",
            status="active",
            is_active=True,
        )
        assert c.certification_number == "CERT-IRQ-001"
        assert c.status == "active"

    def test_identity_review_board_model(self):
        b = IdentityReviewBoard(
            uuid=str(uuid.uuid4()),
            board_id="BRD-001",
            name_en="National Identity Review Board",
            name_ar="مجلس مراجعة الهوية الوطنية",
            board_type="appeals",
            quorum_size=3,
            status="active",
            is_active=True,
        )
        assert b.board_id == "BRD-001"
        assert b.quorum_size == 3


class TestTrustModels:
    """Verify trust framework models."""

    def test_trust_framework_model(self):
        from app.identity.trust.models import TrustFramework

        tf = TrustFramework(
            uuid=str(uuid.uuid4()),
            framework_id="TF-NIST-800-63",
            name_en="NIST 800-63 Identity Assurance",
            name_ar="ضمان الهوية",
            version="4.0",
            status="active",
            is_active=True,
        )
        assert tf.framework_id == "TF-NIST-800-63"
        assert tf.status == "active"

    def test_assurance_profile_model(self):
        from app.identity.trust.models import IdentityAssuranceProfile

        ap = IdentityAssuranceProfile(
            uuid=str(uuid.uuid4()),
            person_id="p1",
            identity_id="id1",
            ial="IAL2",
            aal="AAL2",
            fal="FAL1",
            overall_assurance="IAL2/AAL2",
            profile_version="1.0",
            assessed_by="assessor",
            assessed_at=datetime.now(UTC),
            status="active",
            is_active=True,
        )
        assert ap.ial == "IAL2"
        assert ap.aal == "AAL2"
        assert ap.overall_assurance == "IAL2/AAL2"

    def test_trust_anchor_model(self):
        from app.identity.trust.models import TrustAnchor

        ta = TrustAnchor(
            uuid=str(uuid.uuid4()),
            anchor_id="TA-ROOT-GULA",
            name="GULA Root CA",
            anchor_type="root_ca",
            public_key_hash="sha256-hash",
            status="active",
            valid_from=datetime.now(UTC),
            valid_to=datetime.now(UTC) + timedelta(days=3650),
            is_active=True,
        )
        assert ta.anchor_id == "TA-ROOT-GULA"
        assert ta.anchor_type == "root_ca"


class TestFederationModels:
    """Verify federation models."""

    def test_federated_provider_model(self):
        from app.identity.federation.models import FederatedProvider

        fp = FederatedProvider(
            uuid=str(uuid.uuid4()),
            provider_id="FP-MOH-IDP",
            name_en="MOH Identity Provider",
            name_ar="مزود هوية وزارة الصحة",
            provider_type="government_idp",
            issuer_url="https://idp.moh.gov.iq",
            client_id="client-123",
            status="active",
            is_active=True,
        )
        assert fp.provider_id == "FP-MOH-IDP"
        assert fp.provider_type == "government_idp"

    def test_federated_identity_model(self):
        from app.identity.federation.models import FederatedIdentity

        fi = FederatedIdentity(
            uuid=str(uuid.uuid4()),
            fed_id="FI-001",
            person_id="p1",
            identity_id="id1",
            provider_id="prov1",
            external_subject_id="ext-123",
            linked_at=datetime.now(UTC),
            status="active",
            is_active=True,
        )
        assert fi.fed_id == "FI-001"
        assert fi.external_subject_id == "ext-123"


class TestCertificateModels:
    """Verify certificate models."""

    def test_digital_certificate_model(self):
        from app.identity.certificates.models import DigitalCertificate

        dc = DigitalCertificate(
            uuid=str(uuid.uuid4()),
            certificate_id="CERT-DC-001",
            serial_number="SN-001",
            subject="CN=GULA Platform",
            issuer="CN=GULA Root CA",
            certificate_type="tls",
            thumbprint="thumb-001",
            issued_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=365),
            status="active",
            is_active=True,
        )
        assert dc.serial_number == "SN-001"
        assert dc.certificate_type == "tls"

    def test_certificate_authority_model(self):
        from app.identity.certificates.models import CertificateAuthority

        ca = CertificateAuthority(
            uuid=str(uuid.uuid4()),
            ca_id="CA-ROOT-001",
            name="GULA Root Certificate Authority",
            ca_type="root",
            status="active",
            valid_from=datetime.now(UTC),
            valid_to=datetime.now(UTC) + timedelta(days=3650),
            is_active=True,
        )
        assert ca.ca_id == "CA-ROOT-001"
        assert ca.ca_type == "root"

    def test_api_key_model(self):
        from app.identity.certificates.models import APIKey

        ak = APIKey(
            uuid=str(uuid.uuid4()),
            api_key_id="KEY-001",
            key_prefix="gula_",
            key_hash="hash123",
            name="Test API Key",
            organization_id="org1",
            created_by="admin",
            status="active",
            is_active=True,
        )
        assert ak.key_prefix == "gula_"
        assert ak.status == "active"


class TestLifecycleModels:
    """Verify lifecycle models."""

    def test_enterprise_registration_model(self):
        from app.identity.lifecycle.models import EnterpriseRegistration

        er = EnterpriseRegistration(
            uuid=str(uuid.uuid4()),
            reg_id="ER-001",
            organization_id="org1",
            status="draft",
            submitted_by="admin",
            submitted_at=datetime.now(UTC),
            is_active=True,
        )
        assert er.reg_id == "ER-001"
        assert er.status == "draft"

    def test_government_appointment_model(self):
        from app.identity.lifecycle.models import GovernmentAppointment

        ga = GovernmentAppointment(
            uuid=str(uuid.uuid4()),
            appointment_id="GA-001",
            person_id="p1",
            organization_id="org1",
            hr_reference="HR-2026-001",
            appointment_type="permanent",
            position="Lab Director",
            grade="Grade 1",
            department="Laboratory",
            start_date=datetime.now(UTC).date(),
            status="draft",
            is_active=True,
        )
        assert ga.hr_reference == "HR-2026-001"
        assert ga.appointment_type == "permanent"

    def test_citizen_lifecycle_model(self):
        from app.identity.lifecycle.models import CitizenLifecycle

        cl = CitizenLifecycle(
            uuid=str(uuid.uuid4()),
            citizen_id="CIT-001",
            person_id="p1",
            identity_id="id1",
            status="registered",
            registration_date=datetime.now(UTC),
            is_active=True,
        )
        assert cl.citizen_id == "CIT-001"
        assert cl.status == "registered"

    def test_guardian_account_model(self):
        from app.identity.lifecycle.models import GuardianAccount

        ga = GuardianAccount(
            uuid=str(uuid.uuid4()),
            guardian_id="GU-001",
            guardian_person_id="p1",
            dependent_person_id="p2",
            relationship="parent",
            guardian_type="parent",
            start_date=datetime.now(UTC).date(),
            status="active",
            is_active=True,
        )
        assert ga.guardian_id == "GU-001"
        assert ga.relationship == "parent"


class TestWorkflowModels:
    """Verify workflow engine models."""

    def test_workflow_definition_model(self):
        from app.identity.workflows.models import WorkflowDefinition

        wd = WorkflowDefinition(
            uuid=str(uuid.uuid4()),
            def_id="WF-APPROVAL-001",
            name="Identity Approval Workflow",
            description="Approval workflow for identity verification",
            workflow_type="approval",
            status="active",
            is_active=True,
        )
        assert wd.def_id == "WF-APPROVAL-001"
        assert wd.workflow_type == "approval"

    def test_workflow_instance_model(self):
        from app.identity.workflows.models import WorkflowInstance

        wi = WorkflowInstance(
            uuid=str(uuid.uuid4()),
            instance_id="WI-001",
            def_id="def1",
            trigger_type="manual",
            trigger_id="trig1",
            initiator_id="admin",
            status="pending",
            started_at=datetime.now(UTC),
            is_active=True,
        )
        assert wi.instance_id == "WI-001"
        assert wi.status == "pending"

    def test_workflow_approval_model(self):
        from app.identity.workflows.models import WorkflowApproval

        wa = WorkflowApproval(
            uuid=str(uuid.uuid4()),
            approval_id="WA-001",
            instance_id="wi1",
            step_name="review",
            approver_id="reviewer1",
            status="pending",
            assigned_at=datetime.now(UTC),
            is_active=True,
        )
        assert wa.approval_id == "WA-001"
        assert wa.status == "pending"


class TestNotificationModels:
    """Verify notification engine models."""

    def test_notification_template_model(self):
        from app.identity.notifications.models import NotificationTemplate

        nt = NotificationTemplate(
            uuid=str(uuid.uuid4()),
            template_id="TMP-LOGIN-ALERT",
            name="Login Alert",
            notification_type="email",
            subject="New login detected",
            body="A new login was detected on your account",
            locale="en",
            is_active=True,
        )
        assert nt.template_id == "TMP-LOGIN-ALERT"
        assert nt.notification_type == "email"

    def test_notification_queue_model(self):
        from app.identity.notifications.models import NotificationQueue

        nq = NotificationQueue(
            uuid=str(uuid.uuid4()),
            queue_id="Q-001",
            recipient_id="user1",
            recipient_type="person",
            notification_type="email",
            channel="email",
            subject="Test notification",
            body="This is a test",
            priority="high",
            status="queued",
            is_active=True,
        )
        assert nq.queue_id == "Q-001"
        assert nq.status == "queued"


class TestAdaptiveAuthModels:
    """Verify adaptive auth models."""

    def test_risk_event_model(self):
        from app.identity.adaptive_auth.models import RiskEvent

        re = RiskEvent(
            uuid=str(uuid.uuid4()),
            event_id="RE-001",
            event_type="failed_login",
            severity="medium",
            risk_score=50,
            timestamp=datetime.now(UTC),
            is_active=True,
        )
        assert re.event_id == "RE-001"
        assert re.event_type == "failed_login"

    def test_session_policy_model(self):
        from app.identity.adaptive_auth.models import SessionPolicy

        sp = SessionPolicy(
            uuid=str(uuid.uuid4()),
            policy_id="SP-CITIZEN",
            name="Citizen Session Policy",
            applies_to="citizen",
            max_sessions=1,
            session_timeout_minutes=60,
            inactivity_timeout_minutes=15,
            is_active=True,
        )
        assert sp.policy_id == "SP-CITIZEN"
        assert sp.max_sessions == 1


class TestAdminModels:
    """Verify admin console models."""

    def test_enterprise_portal_model(self):
        from app.identity.admin.models import EnterprisePortal

        ep = EnterprisePortal(
            uuid=str(uuid.uuid4()),
            portal_id="PORT-001",
            organization_id="org1",
            name="MOH Portal",
            portal_type="enterprise",
            features=["employees", "licenses"],
            created_by="admin",
            status="active",
            is_active=True,
        )
        assert ep.portal_id == "PORT-001"
        assert ep.name == "MOH Portal"

    def test_fhir_connection_model(self):
        from app.identity.admin.models import FHIRConnection

        fc = FHIRConnection(
            uuid=str(uuid.uuid4()),
            conn_id="FHIR-001",
            organization_id="org1",
            name="Main FHIR Server",
            fhir_version="R4",
            base_url="https://fhir.moh.gov.iq",
            auth_type="bearer",
            status="active",
            is_active=True,
        )
        assert fc.fhir_version == "R4"
        assert fc.auth_type == "bearer"

    def test_portal_subscription_model(self):
        from app.identity.admin.models import PortalSubscription

        ps = PortalSubscription(
            uuid=str(uuid.uuid4()),
            sub_id="SUB-001",
            organization_id="org1",
            plan_type="enterprise",
            status="active",
            start_date=datetime.now(UTC).date(),
            renewal_date=datetime.now(UTC).date() + timedelta(days=365),
            billing_cycle="annual",
            billing_amount=10000.0,
            currency="IQD",
            is_active=True,
        )
        assert ps.sub_id == "SUB-001"
        assert ps.plan_type == "enterprise"


class TestComplianceModels:
    """Verify compliance models."""

    def test_compliance_framework_model(self):
        from app.identity.compliance.models import ComplianceFramework

        cf = ComplianceFramework(
            uuid=str(uuid.uuid4()),
            framework_id="CF-NIST-800-63",
            name="NIST Special Publication 800-63",
            framework_type="nist_800_63",
            version="4.0",
            status="active",
            is_active=True,
        )
        assert cf.framework_id == "CF-NIST-800-63"
        assert cf.framework_type == "nist_800_63"

    def test_compliance_check_model(self):
        from app.identity.compliance.models import ComplianceCheck

        cc = ComplianceCheck(
            uuid=str(uuid.uuid4()),
            check_id="CHK-001",
            framework_id="fw1",
            requirement_id="REQ-001",
            target_type="identity",
            target_id="id1",
            check_type="automated",
            status="passed",
            checked_by="system",
            checked_at=datetime.now(UTC),
            is_active=True,
        )
        assert cc.check_id == "CHK-001"
        assert cc.status == "passed"

    def test_compliance_report_model(self):
        from app.identity.compliance.models import ComplianceReport

        cr = ComplianceReport(
            uuid=str(uuid.uuid4()),
            report_id="RPT-001",
            organization_id="org1",
            framework_id="fw1",
            report_type="self_assessment",
            overall_score=85,
            passed_count=10,
            failed_count=2,
            warning_count=1,
            not_applicable_count=0,
            generated_by="system",
            generated_at=datetime.now(UTC),
            status="draft",
            is_active=True,
        )
        assert cr.report_id == "RPT-001"
        assert cr.overall_score == 85


class TestGovernanceServices:
    """Verify governance services instantiation."""

    @pytest.mark.asyncio
    async def test_governance_service_create_authority(self, mock_session):
        svc = GovernanceService(mock_session)
        result = svc.create_authority(
            authority_id="IA-TEST",
            name_en="Test Authority",
            name_ar="هيئة اختبار",
            authority_type="identity_authority",
            jurisdiction="national",
        )
        mock_session.add.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_policy_approval_service_submit(self, mock_session):
        svc = PolicyApprovalService(mock_session)
        result = svc.submit_policy(
            policy_id="POL-001",
            submitted_by="admin",
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_appeal_service_submit(self, mock_session):
        svc = AppealService(mock_session)
        result = svc.submit_appeal(
            appeal_id="APL-TEST-001",
            appellant_person_id="p1",
            identity_id="id1",
            appeal_type="suspension",
            reason="Incorrect suspension",
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_suspension_service_suspend(self, mock_session):
        svc = SuspensionService(mock_session)
        result = svc.suspend_identity(
            person_id="p1",
            identity_id="id1",
            reason="Security breach",
            severity="high",
            suspended_by="admin",
            duration_hours=72,
        )
        assert result is not None
        assert result.severity == "high"

    @pytest.mark.asyncio
    async def test_registry_service_register(self, mock_session):
        svc = RegistryService(mock_session)
        result = svc.register_identity(
            person_id="p1",
            identity_id="id1",
            registry_type="citizen",
            registered_by="admin",
        )
        assert result is not None
        assert result.registry_type == "citizen"


class TestAuditHashChain:
    """Verify cryptographic hash chain integrity."""

    @pytest.mark.asyncio
    async def test_audit_service_with_hash_chain(self, mock_session):
        from app.identity.models.audit import AuditAction
        from app.identity.services.audit_service import AuditService

        svc = AuditService(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        entry = await svc.record(
            action=AuditAction.person_created,
            actor_id="admin",
            target_type="person",
            target_id="p1",
        )

        assert entry.entry_hash is not None
        assert len(entry.entry_hash) == 64
        assert entry.previous_hash is None

    @pytest.mark.asyncio
    async def test_audit_hash_chain_linked(self, mock_session):
        from app.identity.models.audit import AuditAction
        from app.identity.services.audit_service import AuditService

        svc = AuditService(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        entry1 = await svc.record(
            action=AuditAction.person_created,
            actor_id="admin",
            target_type="person",
            target_id="p1",
        )

        mock_result.scalar_one_or_none.return_value = entry1.entry_hash

        entry2 = await svc.record(
            action=AuditAction.account_created,
            actor_id="admin",
            target_type="account",
            target_id="a1",
        )

        assert entry2.previous_hash == entry1.entry_hash


class TestUpdatedModels:
    """Verify model updates from PROGRAM-NIAM-002."""

    def test_machine_identity_has_new_fields(self):
        from app.identity.models.machine_identity import MachineIdentity

        m = MachineIdentity(
            uuid=str(uuid.uuid4()),
            organization_id="org1",
            machine_name="Sysmex-XN1000",
            machine_type="lab_instrument",
            iot_device_type="analyzer",
            robot_type="lab_robot",
            ai_agent_id="ai-001",
            device_attestation="attestation-data",
            attested_at=datetime.now(UTC),
            health_status="healthy",
            firmware_version="1.2.3",
            analyzer_type="hematology",
            risk_score=25,
            is_active=True,
        )
        assert m.health_status == "healthy"
        assert m.analyzer_type == "hematology"
        assert m.risk_score == 25

    def test_session_has_governance_fields(self):
        from app.identity.models.session import UserSession

        s = UserSession(
            uuid=str(uuid.uuid4()),
            account_id="a1",
            token_jti=str(uuid.uuid4()),
            session_type="web",
            policy_id="SP-CITIZEN",
            governance_action="single_session_enforced",
            risk_score_at_login=30,
            risk_level_at_login="medium",
            started_at=datetime.now(UTC),
            last_activity_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            is_active=True,
        )
        assert s.policy_id == "SP-CITIZEN"
        assert s.risk_score_at_login == 30
        assert s.risk_level_at_login == "medium"


class TestAuditActionsExpanded:
    """Verify expanded audit actions from PROGRAM-NIAM-002."""

    def test_new_audit_actions_exist(self):
        from app.identity.models.audit import AuditAction

        new_actions = [
            "authority_created",
            "appeal_submitted",
            "appeal_decided",
            "suspension_created",
            "suspension_lifted",
            "trust_framework_created",
            "federation_trust_established",
            "federation_trust_terminated",
            "enterprise_registration_approved",
            "government_appointment_activated",
            "government_promotion",
            "citizen_registered",
            "citizen_verified",
            "guardianship_created",
            "certificate_issued",
            "certificate_revoked",
            "risk_event_detected",
            "mfa_verified",
            "impossible_travel_detected",
            "credential_stuffing_detected",
            "workflow_approved",
            "compliance_check_failed",
            "audit_tamper_detected",
            "portal_created",
        ]
        for action in new_actions:
            assert action in [a.value for a in AuditAction], f"Missing: {action}"

    def test_audit_action_count(self):
        from app.identity.models.audit import AuditAction

        assert len(AuditAction) >= 90, f"Only {len(AuditAction)} audit actions defined"
