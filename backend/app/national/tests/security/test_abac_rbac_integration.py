from __future__ import annotations

from app.national.security.abac import ABACEngine, AccessRequest
from app.national.security.rbac import NationalPermission, NationalRole, RBACEngine


class TestABACRBACIntegration:
    def test_doctor_can_read_patient(self):
        rbac = RBACEngine()
        assert rbac.has_permission(NationalRole.DOCTOR, NationalPermission.PATIENT_READ)

    def test_minister_can_access_sensitive(self):
        rbac = RBACEngine()
        assert rbac.has_permission(
            NationalRole.MINISTRY_OFFICIAL, NationalPermission.SENSITIVE_ACCESS,
        )

    def test_nurse_cannot_merge_identities(self):
        rbac = RBACEngine()
        assert not rbac.has_permission(NationalRole.NURSE, NationalPermission.CITIZEN_MERGE)

    def test_abac_blocks_vip_from_nurse(self):
        abac = ABACEngine()
        request = AccessRequest(
            subject_id="nurse1",
            subject_roles=["nurse"],
            resource_is_vip=True,
            action="read",
        )
        decision = abac.evaluate(request)
        assert decision.granted is False

    def test_abac_allows_admin_vip(self):
        abac = ABACEngine()
        request = AccessRequest(
            subject_id="admin1",
            subject_roles=["vip_access"],
            resource_is_vip=True,
            action="read",
        )
        decision = abac.evaluate(request)
        assert decision.granted is True
