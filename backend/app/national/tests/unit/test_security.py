from __future__ import annotations

from app.national.security.abac import ABACEngine, AccessRequest
from app.national.security.break_glass import BreakGlassReason, BreakGlassService
from app.national.security.minimum_necessary import MinimumNecessaryEngine
from app.national.security.minor_protection import MinorProtectionService
from app.national.security.purpose_of_use import PurposeOfUse, PurposeOfUseEngine
from app.national.security.rbac import (
    ROLE_PERMISSIONS,
    NationalPermission,
    NationalRole,
    RBACEngine,
)
from app.national.security.sensitive_records import SensitiveRecordService, SensitivityLevel


class TestABACEngine:
    def test_sensitive_record_blocks_unauthorized(self):
        engine = ABACEngine()
        request = AccessRequest(subject_id="user1", subject_roles=["doctor"], resource_is_sensitive=True, action="read")
        decision = engine.evaluate(request)
        assert decision.granted is False

    def test_sensitive_record_allows_authorized(self):
        engine = ABACEngine()
        request = AccessRequest(subject_id="user1", subject_roles=["doctor", "sensitive_access"], resource_is_sensitive=True, action="read")
        decision = engine.evaluate(request)
        assert decision.granted is True

    def test_emergency_grants_access(self):
        engine = ABACEngine()
        request = AccessRequest(subject_id="user1", subject_roles=["doctor"], environment_is_emergency=True, action="read")
        decision = engine.evaluate(request)
        assert decision.granted is True
        assert "log_break_glass" in decision.obligations

    def test_vip_protection_blocks(self):
        engine = ABACEngine()
        request = AccessRequest(subject_id="user1", subject_roles=["nurse"], resource_is_vip=True, action="read")
        decision = engine.evaluate(request)
        assert decision.granted is False

    def test_minor_protection_blocks(self):
        engine = ABACEngine()
        request = AccessRequest(subject_id="user1", subject_roles=["nurse"], resource_is_minor=True, action="read")
        decision = engine.evaluate(request)
        assert decision.granted is False


class TestRBACEngine:
    def test_system_admin_has_all_permissions(self):
        engine = RBACEngine()
        assert engine.has_permission(NationalRole.SYSTEM_ADMIN, NationalPermission.CITIZEN_CREATE)
        assert engine.has_permission(NationalRole.SYSTEM_ADMIN, NationalPermission.BREAK_GLASS)

    def test_doctor_permissions(self):
        engine = RBACEngine()
        assert engine.has_permission(NationalRole.DOCTOR, NationalPermission.CITIZEN_READ)
        assert engine.has_permission(NationalRole.DOCTOR, NationalPermission.ENCOUNTER_CREATE)
        assert not engine.has_permission(NationalRole.DOCTOR, NationalPermission.CITIZEN_CREATE)
        assert not engine.has_permission(NationalRole.DOCTOR, NationalPermission.CITIZEN_MERGE)

    def test_citizen_limited_permissions(self):
        engine = RBACEngine()
        assert engine.has_permission(NationalRole.CITIZEN, NationalPermission.CITIZEN_READ)
        assert not engine.has_permission(NationalRole.CITIZEN, NationalPermission.CITIZEN_CREATE)

    def test_roles_have_permissions(self):
        for role in NationalRole:
            assert role in ROLE_PERMISSIONS, f"{role} has no permissions defined"


class TestBreakGlass:
    def test_request_access(self):
        svc = BreakGlassService()
        access = svc.request_access(
            user_id="user1", user_name="Dr. Ahmed", user_role="doctor",
            reason=BreakGlassReason.EMERGENCY, reason_detail="Patient critical",
            resource_type="Patient", resource_id="PAT001", patient_id="PAT001",
        )
        assert access.access_id is not None
        assert access.is_active is True

    def test_revoke_access(self):
        svc = BreakGlassService()
        access = svc.request_access(
            user_id="user1", user_name="Dr. Ahmed", user_role="doctor",
            reason=BreakGlassReason.EMERGENCY, reason_detail="Test",
            resource_type="Patient", resource_id="PAT001", patient_id="PAT001",
        )
        svc.revoke_access(access.access_id, "admin1", "Reviewed")
        assert svc.is_access_valid(access.access_id) is False


class TestPurposeOfUse:
    def test_treatment_allowed(self):
        engine = PurposeOfUseEngine()
        result = engine.validate(PurposeOfUse.TREATMENT)
        assert result.is_valid is True

    def test_research_requires_consent(self):
        engine = PurposeOfUseEngine()
        result = engine.validate(PurposeOfUse.RESEARCH)
        assert result.requires_consent is True

    def test_emergency_requires_break_glass(self):
        engine = PurposeOfUseEngine()
        result = engine.validate(PurposeOfUse.EMERGENCY)
        assert result.requires_break_glass is True


class TestMinimumNecessary:
    def test_treatment_fields(self):
        engine = MinimumNecessaryEngine()
        fields = engine.get_allowed_fields("treatment")
        assert "name" in fields
        assert "date_of_birth" in fields

    def test_filter_data(self):
        engine = MinimumNecessaryEngine()
        data = {"name": "Ali", "ssn": "123-45-6789", "diagnoses": "Flu", "credit_card": "4111-1111"}
        filtered = engine.filter_data(data, "treatment")
        assert "name" in filtered
        assert "diagnoses" in filtered
        assert "ssn" not in filtered
        assert "credit_card" not in filtered


class TestMinorProtection:
    def test_adult_not_minor(self):
        from datetime import date
        svc = MinorProtectionService()
        assert svc.is_minor(date(2000, 1, 1)) is False

    def test_child_is_minor(self):
        from datetime import date
        svc = MinorProtectionService()
        assert svc.is_minor(date(2020, 1, 1)) is True

    def test_minor_requires_guardian(self):
        from datetime import date
        svc = MinorProtectionService()
        assert svc.requires_guardian(date(2020, 1, 1)) is True


class TestSensitiveRecords:
    def test_hiv_is_highly_sensitive(self):
        svc = SensitiveRecordService()
        assert svc.get_sensitivity("HIV") == SensitivityLevel.HIGHLY_SENSITIVE

    def test_domestic_violence_is_restricted(self):
        svc = SensitiveRecordService()
        assert svc.get_sensitivity("DOMESTIC_VIOLENCE") == SensitivityLevel.RESTRICTED

    def test_normal_condition(self):
        svc = SensitiveRecordService()
        assert svc.get_sensitivity("COLD") == SensitivityLevel.NORMAL
