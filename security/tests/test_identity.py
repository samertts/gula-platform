from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pytest import approx

from security.modules.identity.abac import (
    ABACEngine,
    CombinationAlgorithm,
    ConditionOperator,
    Effect,
    Policy,
    PolicyCondition,
)
from security.modules.identity.models import (
    AccessDecision,
    AccessRequest,
    AuthenticationMethod,
    AuthFactor,
    IdentityProvider,
    RiskLevel,
    SessionInfo,
    TokenClaims,
    UserIdentity,
)


class TestRBAC:
    def test_rbac_permission_verification(self, rbac_engine):
        rbac_engine.assign_role("user-1", "technician")
        result = rbac_engine.check_access("technician", "results", "read")
        assert result.permitted is True

        result = rbac_engine.check_access("technician", "admin", "delete")
        assert result.permitted is False

    def test_rbac_role_hierarchy_inheritance(self, rbac_engine):
        rbac_engine.assign_role("manager-1", "manager")
        perms = rbac_engine.get_effective_permissions("manager-1")
        assert "patients:*" in perms
        assert "results:*" in perms
        assert "users:read" in perms

    def test_rbac_role_ancestors(self, rbac_engine):
        ancestors = rbac_engine.get_role_ancestors("technician")
        assert "supervisor" in ancestors
        assert "manager" in ancestors

    def test_rbac_role_descendants(self, rbac_engine):
        descendants = rbac_engine.get_role_descendants("supervisor")
        assert "technician" in descendants

    def test_rbac_master_admin_has_all_permissions(self, rbac_engine):
        result = rbac_engine.check_access("master_admin", "any", "action")
        assert result.permitted is True

    def test_rbac_bulk_check(self, rbac_engine):
        rbac_engine.assign_role("user-1", "viewer")
        results = rbac_engine.bulk_check("viewer", ["patients:read", "patients:write", "admin:delete"])
        assert results["patients:read"] is True
        assert results["patients:write"] is False

    def test_rbac_add_custom_role(self, rbac_engine):
        rbac_engine.add_role("custom_role", parent="viewer")
        rbac_engine.register_permission("custom_role", "custom:action")
        assert rbac_engine.has_permission("custom_role", "patients:read")
        assert rbac_engine.has_permission("custom_role", "custom:action")

    def test_rbac_get_role_level(self, rbac_engine):
        assert rbac_engine.get_role_level("master_admin") == 1
        assert rbac_engine.get_role_level("viewer") > 1

    def test_rbac_can_manage_role(self, rbac_engine):
        assert rbac_engine.can_manage_role("master_admin", "viewer") is True
        assert rbac_engine.can_manage_role("technician", "master_admin") is False


class TestABAC:
    def test_abac_policy_evaluation(self, abac_engine):
        policy = Policy(
            id="pol-001",
            name="Allow PHI access during business hours",
            effect=Effect.ALLOW,
            resource="phi",
            action="read",
            subject_conditions=[
                PolicyCondition(operator=ConditionOperator.EQUALS, attribute="subject.role", value="physician"),
            ],
            environment_conditions=[
                PolicyCondition(operator=ConditionOperator.LESS_THAN, attribute="env.hour", value=18),
            ],
        )
        abac_engine.add_policy(policy)
        decision = abac_engine.evaluate("phi", "read", subject={"role": "physician"}, environment={"hour": 14})
        assert decision.permitted is True

    def test_abac_deny_by_default(self, abac_engine):
        decision = abac_engine.evaluate("phi", "read", subject={"role": "nurse"})
        assert decision.permitted is False

    def test_abac_deny_overrides(self, abac_engine):
        allow = Policy(id="pol-002", name="Allow all", effect=Effect.ALLOW, resource="*", action="*")
        deny = Policy(id="pol-003", name="Deny phi", effect=Effect.DENY, resource="phi", action="read")
        abac_engine.add_policy(allow)
        abac_engine.add_policy(deny)
        decision = abac_engine.evaluate("phi", "read")
        assert decision.permitted is False

    def test_abac_permit_overrides(self, abac_engine):
        engine = ABACEngine(combination_algorithm=CombinationAlgorithm.PERMIT_OVERRIDES)
        deny = Policy(id="pol-004", name="Deny", effect=Effect.DENY, resource="*", action="*")
        allow = Policy(id="pol-005", name="Allow specific", effect=Effect.ALLOW, resource="phi", action="read")
        engine.add_policy(deny)
        engine.add_policy(allow)
        decision = engine.evaluate("phi", "read")
        assert decision.permitted is True

    def test_abac_purpose_of_use_enforcement(self, abac_engine):
        policy = Policy(
            id="pol-006",
            name="PHI access requires treatment purpose",
            effect=Effect.ALLOW,
            resource="phi",
            action="read",
            purpose_of_use=["treatment"],
        )
        abac_engine.add_policy(policy)
        decision = abac_engine.evaluate("phi", "read", environment={"purpose_of_use": "payment"})
        assert decision.permitted is False

    def test_abac_inactive_policy(self, abac_engine):
        policy = Policy(
            id="pol-007", name="Inactive policy", effect=Effect.ALLOW,
            resource="*", action="*", is_active=False,
        )
        abac_engine.add_policy(policy)
        decision = abac_engine.evaluate("anything", "read")
        assert decision.permitted is False

    def test_abac_condition_operators(self, abac_engine):
        policy = Policy(
            id="pol-008", name="Department match", effect=Effect.ALLOW,
            resource="records", action="read",
            subject_conditions=[
                PolicyCondition(operator=ConditionOperator.IN, attribute="subject.department", value=["cardiology", "neurology"]),
            ],
        )
        abac_engine.add_policy(policy)
        assert abac_engine.evaluate("records", "read", subject={"department": "cardiology"}).permitted is True
        assert abac_engine.evaluate("records", "read", subject={"department": "hr"}).permitted is False


class TestJWT:
    def test_jwt_token_creation_and_verification(self, jwt_manager):
        token = jwt_manager.create_access_token("user-001", {"roles": ["physician"]})
        assert token is not None
        claims = jwt_manager.verify_access_token(token)
        assert claims is not None
        assert claims["sub"] == "user-001"
        assert claims["roles"] == ["physician"]

    def test_jwt_token_revocation(self, jwt_manager):
        token = jwt_manager.create_access_token("user-001")
        claims = jwt_manager.verify_access_token(token)
        assert claims is not None
        jti = claims["jti"]
        jwt_manager.revoke_token(jti)
        assert jwt_manager.verify_access_token(token) is None

    def test_jwt_refresh_token(self, jwt_manager):
        token = jwt_manager.create_refresh_token("user-001")
        claims = jwt_manager.verify_refresh_token(token)
        assert claims is not None
        assert claims["type"] == "refresh"

    def test_jwt_id_token(self, jwt_manager):
        token = jwt_manager.create_id_token("user-001", "gula-platform")
        claims = jwt_manager.verify_token(token)
        assert claims is not None
        assert claims["type"] == "id_token"

    def test_jwt_invalid_token(self, jwt_manager):
        result = jwt_manager.verify_token("invalid.jwt.token")
        assert result is None

    def test_jwt_parse_claims(self, jwt_manager):
        token = jwt_manager.create_access_token("user-001")
        claims = jwt_manager.parse_claims(token)
        assert claims is not None
        assert claims.sub == "user-001"

    def test_jwt_introspect(self, jwt_manager):
        token = jwt_manager.create_access_token("user-001")
        intro = jwt_manager.introspect_token(token)
        assert intro["active"] is True
        assert intro["sub"] == "user-001"

    def test_jwt_validate_claims(self, jwt_manager):
        token = jwt_manager.create_access_token("user-001")
        assert jwt_manager.validate_claims(token) is True
        assert jwt_manager.validate_claims(token, expected_iss="wrong-issuer") is False

    def test_jwt_jwks_endpoint(self, jwt_manager):
        jwks = jwt_manager.get_jwks()
        assert len(jwks) > 0
        for key in jwks:
            assert "kid" in key
            assert "alg" in key


class TestPKCE:
    def test_pkce_challenge_generation(self, pkce_manager):
        verifier = pkce_manager.generate_code_verifier()
        assert len(verifier) >= 43
        challenge = pkce_manager.derive_code_challenge(verifier)
        assert pkce_manager.verify_code_challenge(verifier, challenge, "S256")

    def test_pkce_plain_method(self, pkce_manager):
        verifier = pkce_manager.generate_code_verifier(64)
        challenge = pkce_manager.derive_code_challenge(verifier, "plain")
        assert verifier == challenge

    def test_pkce_state_validation(self, pkce_manager):
        state = pkce_manager.generate_state()
        pkce_manager.store_state(state, {"client_id": "test-client"})
        assert pkce_manager.validate_state(state, {"client_id": "test-client"}) is True
        assert pkce_manager.validate_state(state) is False

    def test_pkce_nonce_validation(self, pkce_manager):
        nonce = pkce_manager.generate_nonce()
        pkce_manager.store_nonce(nonce)
        assert pkce_manager.validate_nonce(nonce) is True
        assert pkce_manager.validate_nonce(nonce) is False

    def test_pkce_cleanup_expired(self, pkce_manager):
        pkce_manager.generate_code_verifier()
        count = pkce_manager.cleanup_expired()
        assert count >= 0


class TestMFA:
    def test_mfa_totp_verification(self, mfa_manager):
        secret = mfa_manager.generate_totp_secret()
        import pyotp
        totp = pyotp.TOTP(secret)
        token = totp.now()
        assert mfa_manager.verify_totp(secret, token) is True

    def test_mfa_totp_wrong_token(self, mfa_manager):
        secret = mfa_manager.generate_totp_secret()
        assert mfa_manager.verify_totp(secret, "000000") is False

    def test_mfa_recovery_codes(self, mfa_manager):
        codes = mfa_manager.generate_recovery_codes()
        assert len(codes) == 10
        hashed = [mfa_manager.hash_recovery_code(c) for c in codes]
        result = mfa_manager.verify_recovery_code(codes[0], hashed)
        assert result == hashed[0]

    def test_mfa_enrollment(self, mfa_manager):
        result = mfa_manager.enroll_totp("user-001", "user@gula.iq")
        assert "secret" in result
        assert "uri" in result
        assert "backup_codes" in result
        assert mfa_manager.is_mfa_enabled("user-001") is True

    def test_mfa_remove_device(self, mfa_manager):
        mfa_manager.enroll_totp("user-001", "user@gula.iq")
        result = mfa_manager.remove_device("user-001", "totp")
        assert result is True
        assert mfa_manager.is_mfa_enabled("user-001") is False

    def test_mfa_step_up_authentication(self, mfa_manager):
        result = mfa_manager.step_up_authentication("user-001", RiskLevel.HIGH, RiskLevel.LOW)
        assert result["step_up_required"] is True
        token = result["session_token"]
        assert mfa_manager.verify_step_up(token) is True

    def test_mfa_get_enrolled_methods(self, mfa_manager):
        mfa_manager.enroll_totp("user-001", "user@gula.iq")
        methods = mfa_manager.get_enrolled_methods("user-001")
        assert AuthFactor.TOTP in methods


class TestRiskEngine:
    def test_risk_engine_scoring(self, risk_engine):
        context = {
            "user_id": "user-001",
            "ip_address": "198.51.100.42",
            "resource": "phi",
            "action": "read",
        }
        result = risk_engine.calculate_risk(context)
        assert "score" in result
        assert "level" in result
        assert 0.0 <= result["score"] <= 1.0

    def test_risk_engine_low_risk(self, risk_engine):
        risk_engine.record_successful_auth("user-001", {
            "device_id": "known-device",
            "user_agent": "known-agent",
            "resource": "home",
            "action": "view",
        })
        context = {
            "user_id": "user-001",
            "device_id": "known-device",
            "user_agent": "known-agent",
            "resource": "home", "action": "view",
            "ip_address": "203.0.113.1",
        }
        result = risk_engine.calculate_risk(context)
        assert result["score"] < 0.3

    def test_risk_engine_high_failed_attempts(self, risk_engine):
        for _ in range(10):
            risk_engine.record_failed_attempt("user-001")
        context = {"user_id": "user-001", "ip_address": "198.51.100.1"}
        result = risk_engine.calculate_risk(context)
        assert result["score"] > 0.3

    def test_risk_engine_get_risk_based_action(self, risk_engine):
        assert risk_engine.get_risk_based_action({"level": "low", "score": 0.1}) == "allow"
        assert risk_engine.get_risk_based_action({"level": "medium", "score": 0.5}) == "challenge_mfa"
        assert risk_engine.get_risk_based_action({"level": "high", "score": 0.8}) == "require_admin_approval"
        assert risk_engine.get_risk_based_action({"level": "critical", "score": 0.95}) == "deny"

    def test_risk_engine_custom_factor(self, risk_engine):
        risk_engine.add_custom_factor(lambda ctx: 0.5 if ctx.get("is_vip") else 0.0)
        result = risk_engine.calculate_risk({"user_id": "vip-user", "is_vip": True})
        assert result["score"] > 0


class TestSessionManagement:
    def test_session_creation(self, session_manager):
        session = session_manager.create_session(
            user_id="user-001",
            ip_address="203.0.113.1",
            user_agent="test-agent",
            auth_methods=[AuthenticationMethod.PASSWORD],
        )
        assert session.session_id is not None
        assert session.user_id == "user-001"

    def test_session_retrieval(self, session_manager):
        session = session_manager.create_session("user-001", "203.0.113.1")
        retrieved = session_manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.user_id == "user-001"

    def test_session_touch(self, session_manager):
        session = session_manager.create_session("user-001", "203.0.113.1")
        assert session_manager.touch_session(session.session_id) is True

    def test_session_destroy(self, session_manager):
        session = session_manager.create_session("user-001", "203.0.113.1")
        assert session_manager.destroy_session(session.session_id) is True
        assert session_manager.get_session(session.session_id) is None

    def test_session_hijacking_detection(self, session_manager):
        session = session_manager.create_session(
            "user-001", "203.0.113.1", user_agent="original-agent",
        )
        alerts = session_manager.detect_hijacking(
            session.session_id, "198.51.100.42", "malicious-agent",
        )
        assert "ip_address_change" in alerts
        assert "user_agent_change" in alerts

    def test_session_concurrent_limit(self, session_manager):
        for i in range(5):
            session_manager.create_session(
                "user-001", f"203.0.113.{i}", device_id=f"device-{i}",
            )
        assert session_manager.get_active_session_count("user-001") <= 5
