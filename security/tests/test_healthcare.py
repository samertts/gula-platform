from __future__ import annotations

import os

import pytest


class TestSMARTOnFHIR:
    def test_smart_on_fhir_launch(self, jwt_manager):
        token = jwt_manager.create_access_token(
            "practitioner-001",
            {
                "roles": ["physician"],
                "fhir_user": "practitioner-001",
                "patient": "pat-001",
                "purpose_of_use": "TREATMENT",
                "organization": "hospital-001",
            },
        )
        claims = jwt_manager.verify_access_token(token)
        assert claims is not None
        assert claims.get("roles") == ["physician"]
        assert claims.get("patient") == "pat-001"
        assert claims.get("purpose_of_use") == "TREATMENT"

    def test_smart_fhir_scope_validation(self, jwt_manager):
        token = jwt_manager.create_access_token(
            "app-001",
            {"scopes": ["patient/*.read", "user/*.write"]},
        )
        claims = jwt_manager.verify_access_token(token)
        assert claims is not None
        scopes = claims.get("scopes", [])
        assert "patient/*.read" in scopes


class TestBreakGlass:
    def test_break_glass_access_workflow(self, phi_encryptor):
        encrypted = phi_encryptor.encrypt_phi(
            "emergency-patient-data", "pat-999", "patients", "phi_data",
        )
        emergency_key = os.urandom(32)
        phi_encryptor.enable_break_glass(emergency_key)
        decrypted = phi_encryptor.decrypt_phi(
            encrypted, "pat-999", "patients", "phi_data",
            break_glass=True, break_glass_reason="patient_unconscious",
        )
        assert decrypted == "emergency-patient-data"

    def test_break_glass_disabled(self, phi_encryptor):
        encrypted = phi_encryptor.encrypt_phi("data", "pat-001", "patients", "phi")
        phi_encryptor.disable_break_glass()
        with pytest.raises(Exception):
            phi_encryptor.decrypt_phi(
                encrypted, "pat-001", "patients", "phi",
                break_glass=True, break_glass_reason="test",
            )

    def test_break_glass_without_key(self, phi_encryptor):
        encrypted = phi_encryptor.encrypt_phi("data", "pat-001", "t", "c")
        with pytest.raises(Exception):
            phi_encryptor.decrypt_phi(
                encrypted, "pat-001", "t", "c",
                break_glass=True, break_glass_reason="no_key",
            )


class TestConsent:
    def test_consent_enforcement(self, phi_encryptor):
        token = phi_encryptor.generate_consent_token("pat-001")
        encrypted = phi_encryptor.encrypt_phi(
            "data", "pat-001", "records", "phi", consent_token=token,
        )
        decrypted = phi_encryptor.decrypt_phi(encrypted, "pat-001", "records", "phi")
        assert decrypted == "data"

    def test_consent_without_token(self, phi_encryptor):
        with pytest.raises((PermissionError, Exception)):
            phi_encryptor.encrypt_phi("data", "pat-001", "records", "phi", consent_token="invalid")

    def test_consent_different_patients(self, phi_encryptor):
        token1 = phi_encryptor.generate_consent_token("pat-001")
        token2 = phi_encryptor.generate_consent_token("pat-002")
        assert token1 != token2


class TestPurposeOfUse:
    def test_purpose_of_use_enforcement(self, abac_engine):
        from security.modules.identity.abac import Effect, Policy

        policy = Policy(
            id="pou-001",
            name="PHI access requires treatment",
            effect=Effect.ALLOW,
            resource="phi",
            action="read",
            purpose_of_use=["TREATMENT"],
        )
        abac_engine.add_policy(policy)

        decision = abac_engine.evaluate(
            "phi", "read",
            environment={"purpose_of_use": "TREATMENT"},
        )
        assert decision.permitted is True

        decision = abac_engine.evaluate(
            "phi", "read",
            environment={"purpose_of_use": "PAYMENT"},
        )
        assert decision.permitted is False

    def test_purpose_of_use_emergency(self, abac_engine):
        from security.modules.identity.abac import Effect, Policy

        policy = Policy(
            id="pou-002",
            name="Emergency override",
            effect=Effect.ALLOW,
            resource="phi",
            action="read",
            purpose_of_use=["EMERGENCY"],
        )
        abac_engine.add_policy(policy)
        decision = abac_engine.evaluate(
            "phi", "read",
            environment={"purpose_of_use": "EMERGENCY"},
        )
        assert decision.permitted is True


class TestPrivacyMasking:
    def test_privacy_masking(self, field_encryptor):
        phi_data = "123-45-6789"
        encrypted = field_encryptor.encrypt_field(phi_data, "ssn", "patients")
        assert encrypted != phi_data
        decrypted = field_encryptor.decrypt_field(encrypted, "ssn", "patients")
        assert decrypted == phi_data

    def test_role_based_masking(self, rbac_engine):
        rbac_engine.assign_role("nurse-001", "nurse")
        perms = rbac_engine.get_effective_permissions("nurse-001")
        assert len(perms) > 0
