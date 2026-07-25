"""Tests for the Risk-Based Authentication Service."""

from app.services.risk_based_auth_service import (
    AuthContext,
    AuthRiskLevel,
    RequiredAction,
    RiskBasedAuthService,
)


class TestRiskBasedAuth:
    def test_low_risk_proceed(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-001",
            user_role="doctor",
            ip_address="192.168.1.1",
            device_id="device-001",
            device_trust_level="high",
            is_known_device=True,
            hour_of_day=14,
            day_of_week=2,
            login_velocity=1,
            failed_attempts_24h=0,
        )
        decision = svc.evaluate(ctx)
        assert decision.risk_level == AuthRiskLevel.LOW
        assert decision.required_action == RequiredAction.PROCEED

    def test_unknown_device_elevates_risk(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-002",
            user_role="doctor",
            ip_address="10.0.0.1",
            device_id="unknown-device",
            device_trust_level="unknown",
            is_known_device=False,
            hour_of_day=14,
        )
        decision = svc.evaluate(ctx)
        assert decision.risk_score > 0
        assert "unknown" in " ".join(decision.factors).lower()

    def test_unusual_hour_elevates_risk(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-003",
            user_role="nurse",
            ip_address="10.0.0.1",
            device_id="device-003",
            is_known_device=True,
            device_trust_level="medium",
            hour_of_day=3,
        )
        decision = svc.evaluate(ctx)
        assert decision.risk_score > 0
        assert any("unusual" in f.lower() for f in decision.factors)

    def test_many_failed_attempts_requires_mfa(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-004",
            user_role="staff",
            ip_address="10.0.0.1",
            device_id="device-004",
            is_known_device=False,
            device_trust_level="unknown",
            failed_attempts_24h=10,
            hour_of_day=14,
        )
        decision = svc.evaluate(ctx)
        assert decision.risk_score >= 25
        assert decision.required_action in (
            RequiredAction.STEP_UP_AUTH, RequiredAction.MFA_REQUIRED, RequiredAction.BLOCKED
        )

    def test_tor_detected(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-005",
            user_role="admin",
            ip_address="185.220.101.1",
            device_id="device-005",
            is_known_device=False,
            device_trust_level="unknown",
            is_tor=True,
            hour_of_day=14,
        )
        decision = svc.evaluate(ctx)
        assert decision.risk_score >= 50
        assert decision.required_action != RequiredAction.PROCEED

    def test_vpn_proxy_detected(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-006",
            user_role="doctor",
            ip_address="1.2.3.4",
            device_id="device-006",
            is_known_device=False,
            device_trust_level="unknown",
            is_vpn=True,
            hour_of_day=14,
        )
        decision = svc.evaluate(ctx)
        assert decision.risk_score > 0
        assert decision.required_action != RequiredAction.PROCEED

    def test_step_up_auth_for_medium_risk(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-007",
            user_role="staff",
            ip_address="10.0.0.1",
            device_id="new-device",
            is_known_device=False,
            device_trust_level="unknown",
            hour_of_day=14,
        )
        decision = svc.evaluate(ctx)
        assert decision.risk_score >= 20
        if 30 <= decision.risk_score < 50:
            assert decision.required_action == RequiredAction.STEP_UP_AUTH

    def test_known_device_low_risk(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-008",
            user_role="doctor",
            ip_address="192.168.1.1",
            device_id="trusted-device",
            is_known_device=True,
            device_trust_level="trusted",
            hour_of_day=14,
            login_velocity=1,
            failed_attempts_24h=0,
        )
        decision = svc.evaluate(ctx)
        assert decision.risk_level == AuthRiskLevel.LOW
        assert decision.required_action == RequiredAction.PROCEED

    def test_high_velocity_login(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-009",
            user_role="staff",
            ip_address="10.0.0.1",
            device_id="device-009",
            is_known_device=True,
            device_trust_level="medium",
            hour_of_day=14,
        )
        svc._velocity_tracker["user-009"] = list(range(10))
        ctx.login_velocity = 10
        decision = svc.evaluate(ctx)
        velocity_factors = [f for f in decision.factors if "velocity" in f.lower()]
        assert len(velocity_factors) > 0

    def test_decision_logging(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-010",
            user_role="doctor",
            ip_address="10.0.0.1",
            device_id="device-010",
            is_known_device=True,
            device_trust_level="high",
            hour_of_day=14,
        )
        svc.evaluate(ctx)
        decisions = svc.get_decisions(user_id="user-010")
        assert len(decisions) == 1
        assert decisions[0]["user_id"] == "user-010"

    def test_multiple_decisions_logged(self):
        svc = RiskBasedAuthService()
        for i in range(5):
            ctx = AuthContext(
                user_id=f"user-{i:03d}",
                user_role="doctor",
                ip_address=f"10.0.0.{i}",
                device_id=f"device-{i:03d}",
                is_known_device=True,
                device_trust_level="medium",
                hour_of_day=14,
            )
            svc.evaluate(ctx)
        decisions = svc.get_decisions()
        assert len(decisions) == 5

    def test_anomaly_score_increases_risk(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-011",
            user_role="admin",
            ip_address="10.0.0.1",
            device_id="device-011",
            is_known_device=True,
            device_trust_level="medium",
            anomaly_score=0.8,
            hour_of_day=14,
        )
        decision = svc.evaluate(ctx)
        anomaly_factors = [f for f in decision.factors if "anomaly" in f.lower()]
        assert len(anomaly_factors) > 0

    def test_datacenter_ip_elevates_risk(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-012",
            user_role="staff",
            ip_address="8.8.8.8",
            device_id="device-012",
            is_known_device=False,
            device_trust_level="unknown",
            is_datacenter=True,
            hour_of_day=14,
        )
        decision = svc.evaluate(ctx)
        dc_factors = [f for f in decision.factors if "datacenter" in f.lower()]
        assert len(dc_factors) > 0

    def test_close_proximity_not_impossible_travel(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-013",
            user_role="doctor",
            ip_address="10.0.0.1",
            device_id="device-013",
            is_known_device=True,
            device_trust_level="high",
            geolocation={"lat": 33.3, "lon": 44.4, "country": "IQ", "city": "Baghdad"},
            previous_geos=[{"lat": 33.4, "lon": 44.3, "country": "IQ", "city": "Baghdad"}],
            session_age_minutes=60,
            hour_of_day=14,
        )
        decision = svc.evaluate(ctx)
        assert decision.required_action == RequiredAction.PROCEED

    def test_far_distance_impossible_travel(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-014",
            user_role="doctor",
            ip_address="10.0.0.1",
            device_id="device-014",
            is_known_device=True,
            device_trust_level="high",
            geolocation={"lat": 35.0, "lon": 44.0, "country": "IQ", "city": "Erbil"},
            previous_geos=[{"lat": 30.5, "lon": 47.8, "country": "IQ", "city": "Basra"}],
            session_age_minutes=5,
            hour_of_day=14,
        )
        decision = svc.evaluate(ctx)
        impossible_factors = [f for f in decision.factors if "impossible" in f.lower()]
        assert len(impossible_factors) > 0

    def test_risk_score_clamped(self):
        svc = RiskBasedAuthService()
        ctx = AuthContext(
            user_id="user-015",
            user_role="staff",
            ip_address="unknown",
            device_id="unknown",
            is_known_device=False,
            device_trust_level="unknown",
            is_tor=True,
            is_vpn=True,
            is_datacenter=True,
            failed_attempts_24h=20,
            hour_of_day=3,
            anomaly_score=1.0,
        )
        decision = svc.evaluate(ctx)
        assert 0 <= decision.risk_score <= 100

    def test_context_serialization(self):
        ctx = AuthContext(
            user_id="user-100",
            user_role="doctor",
            ip_address="10.0.0.1",
        )
        d = ctx.to_dict()
        assert d["user_id"] == "user-100"
        assert d["user_role"] == "doctor"
