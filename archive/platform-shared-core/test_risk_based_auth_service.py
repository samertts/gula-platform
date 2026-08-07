"""Unit tests for risk_based_auth_service — adaptive auth risk evaluation.

Covers: risk factor accumulation, threshold classification, impossible-travel
blocking, velocity tracking, location checking, decision log.
"""

from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")

import pytest
from app.services.risk_based_auth_service import (
    AdaptiveAuthWeights,
    AuthContext,
    AuthDecision,
    AuthRiskLevel,
    RequiredAction,
    RiskBasedAuthService,
)


def _ctx(**overrides) -> AuthContext:
    defaults = {
        "user_id": "u1",
        "user_role": "doctor",
        "ip_address": "1.2.3.4",
        "device_id": "dev1",
        "hour_of_day": 12,
    }
    defaults.update(overrides)
    return AuthContext(**defaults)


# ─── Threshold classification ─────────────────────────────────────────────────


def test_low_risk_proceeds():
    svc = RiskBasedAuthService()
    decision = svc.evaluate(_ctx(is_known_device=True))
    assert decision.risk_level == AuthRiskLevel.LOW
    assert decision.required_action == RequiredAction.PROCEED
    assert decision.message == "Access granted"


def test_unknown_device_adds_weight():
    svc = RiskBasedAuthService()
    decision = svc.evaluate(_ctx())
    assert decision.risk_score == AdaptiveAuthWeights.UNKNOWN_DEVICE
    assert decision.risk_level == AuthRiskLevel.LOW
    assert decision.required_action == RequiredAction.PROCEED
    assert decision.factors[0].startswith("+25 unknown device")


def test_high_risk_requires_mfa():
    svc = RiskBasedAuthService()
    decision = svc.evaluate(_ctx(is_tor=True))
    # 25 (unknown device) + 30 (tor) = 55
    assert decision.risk_score >= 50
    assert decision.risk_level == AuthRiskLevel.HIGH
    assert decision.required_action == RequiredAction.MFA_REQUIRED
    assert "totp" in decision.mfa_methods


def test_critical_risk_blocked():
    svc = RiskBasedAuthService()
    decision = svc.evaluate(_ctx(is_tor=True, is_datacenter=True, failed_attempts_24h=5))
    assert decision.risk_score >= 70
    assert decision.risk_level == AuthRiskLevel.CRITICAL
    assert decision.required_action == RequiredAction.BLOCKED


def test_failed_attempts_capped():
    svc = RiskBasedAuthService()
    capped = svc.evaluate(_ctx(failed_attempts_24h=99)).risk_score
    small = svc.evaluate(_ctx(failed_attempts_24h=5)).risk_score
    # both contribute min(15, attempts*5) — identical when > 3 attempts
    assert capped == small == AdaptiveAuthWeights.UNKNOWN_DEVICE + AdaptiveAuthWeights.FAILED_ATTEMPTS


def test_vpn_proxy_factor():
    svc = RiskBasedAuthService()
    decision = svc.evaluate(_ctx(is_vpn=True, is_known_device=True))
    assert any("VPN/proxy" in f for f in decision.factors)


def test_tor_factor_dominant():
    svc = RiskBasedAuthService()
    decision = svc.evaluate(_ctx(is_tor=True, is_known_device=True))
    assert decision.risk_score == AdaptiveAuthWeights.TOR - 10  # known device −10
    assert decision.risk_level == AuthRiskLevel.LOW


def test_anomaly_score_scaled():
    svc = RiskBasedAuthService()
    decision = svc.evaluate(_ctx(anomaly_score=1.0))
    assert decision.risk_score == AdaptiveAuthWeights.UNKNOWN_DEVICE + AdaptiveAuthWeights.ANOMALY


def test_anomaly_below_threshold_ignored():
    svc = RiskBasedAuthService()
    decision = svc.evaluate(_ctx(anomaly_score=0.4))
    assert decision.risk_score == AdaptiveAuthWeights.UNKNOWN_DEVICE


def test_unusual_hour():
    svc = RiskBasedAuthService()
    decision = svc.evaluate(_ctx(hour_of_day=3, is_known_device=True))
    assert decision.risk_score == AdaptiveAuthWeights.UNUSUAL_HOUR - 10


def test_risk_score_clamped_to_100():
    svc = RiskBasedAuthService()
    decision = svc.evaluate(
        _ctx(is_tor=True, is_datacenter=True, is_vpn=True, failed_attempts_24h=20,
             is_known_device=False, anomaly_score=1.0),
    )
    assert decision.risk_score == 100


def test_step_up_requires_approval_at_40():
    svc = RiskBasedAuthService()
    decision = svc.evaluate(_ctx(is_tor=True, is_vpn=True, is_known_device=True))
    # −10 (known) + 30 (tor) + 10 (vpn) = 30 → STEP_UP, below approval threshold
    assert decision.risk_score == 30
    assert decision.required_action == RequiredAction.STEP_UP_AUTH
    assert decision.requires_approval is False


def test_medium_requires_approval_above_40():
    svc = RiskBasedAuthService()
    decision = svc.evaluate(
        _ctx(is_tor=True, is_vpn=True, is_known_device=True, hour_of_day=3)
    )  # −10 + 30 + 10 + 15 = 45
    assert decision.risk_level == AuthRiskLevel.MEDIUM
    assert decision.requires_approval is True


# ─── New location detection ────────────────────────────────────────────────────


def test_same_country_city_known_location():
    svc = RiskBasedAuthService()
    ctx = _ctx(
        is_known_device=True,
        geolocation={"country": "IQ", "city": "Baghdad", "lat": 33.3, "lon": 44.3},
        previous_geos=[{"country": "IQ", "city": "Baghdad", "lat": 33.3, "lon": 44.3}],
    )
    assert svc._is_known_location(ctx.geolocation, ctx.previous_geos) is True


def test_close_distance_known_location():
    svc = RiskBasedAuthService()
    current = {"country": "IQ", "city": "Baghdad", "lat": 33.3, "lon": 44.3}
    previous = [{"country": "IQ", "city": "Baghdad", "lat": 33.31, "lon": 44.31}]
    assert svc._is_known_location(current, previous) is True


def test_far_location_unknown():
    svc = RiskBasedAuthService()
    current = {"country": "IQ", "city": "Baghdad", "lat": 33.3, "lon": 44.3}
    previous = [{"country": "US", "city": "New York", "lat": 40.7, "lon": -74.0}]
    assert svc._is_known_location(current, previous) is False


def test_new_location_adds_weight():
    svc = RiskBasedAuthService()
    ctx = _ctx(
        is_known_device=True,
        geolocation={"country": "IQ", "city": "Basra", "lat": 30.5, "lon": 47.8},
        previous_geos=[{"country": "IQ", "city": "Baghdad", "lat": 33.3, "lon": 44.3}],
        session_age_minutes=120,
    )
    decision = svc.evaluate(ctx)
    assert decision.risk_score == AdaptiveAuthWeights.NEW_LOCATION - 10
    assert decision.risk_level == AuthRiskLevel.LOW


# ─── Impossible travel ─────────────────────────────────────────────────────────


def test_impossible_travel_blocks():
    svc = RiskBasedAuthService()
    ctx = _ctx(
        is_known_device=True,
        geolocation={"country": "IQ", "lat": 33.3, "lon": 44.3},
        previous_geos=[{"country": "US", "lat": 40.7, "lon": -74.0}],
        session_age_minutes=5,
    )
    assert svc._impossible_travel_check(ctx) is True


def test_impossible_travel_ok_with_enough_time():
    svc = RiskBasedAuthService()
    ctx = _ctx(
        is_known_device=True,
        geolocation={"country": "IQ", "lat": 33.3, "lon": 44.3},
        previous_geos=[{"country": "US", "lat": 40.7, "lon": -74.0}],
        session_age_minutes=24 * 60,
    )
    assert svc._impossible_travel_check(ctx) is False


def test_impossible_travel_overrides_risk():
    svc = RiskBasedAuthService()
    ctx = _ctx(
        is_known_device=True,
        geolocation={"country": "IQ", "lat": 33.3, "lon": 44.3},
        previous_geos=[{"country": "US", "lat": 40.7, "lon": -74.0}],
        session_age_minutes=1,
    )
    decision = svc.evaluate(ctx)
    assert decision.risk_level == AuthRiskLevel.CRITICAL
    assert decision.risk_score == 100
    assert decision.required_action == RequiredAction.BLOCKED
    assert "impossible_travel" in decision.factors


def test_no_geo_no_travel_check():
    svc = RiskBasedAuthService()
    assert svc._impossible_travel_check(_ctx()) is False


# ─── Haversine ─────────────────────────────────────────────────────────────────


def test_haversine_zero_distance():
    svc = RiskBasedAuthService()
    assert svc._haversine(33.3, 44.3, 33.3, 44.3) == pytest.approx(0, abs=1e-6)


def test_haversine_known_distance():
    svc = RiskBasedAuthService()
    # Baghdad ~ Los Angeles is far; use approximate comparison only for magnitude
    d = svc._haversine(33.3, 44.3, 33.4, 44.4)
    assert 5 < d < 20


# ─── Velocity tracking ─────────────────────────────────────────────────────────


def test_velocity_sliding_window():
    svc = RiskBasedAuthService()
    assert svc._check_velocity("u1") == 1
    assert svc._check_velocity("u1") == 2
    assert svc._check_velocity("u1") == 3


def test_velocity_tracks_per_user():
    svc = RiskBasedAuthService()
    svc._check_velocity("u1")
    svc._check_velocity("u1")
    svc._check_velocity("u2")
    assert svc._check_velocity("u1") == 3
    assert svc._check_velocity("u2") == 2


def test_high_velocity_adds_weight():
    svc = RiskBasedAuthService()
    for _ in range(6):
        svc._check_velocity("u-fast")
    decision = svc.evaluate(_ctx(user_id="u-fast", is_known_device=True, login_velocity=0))
    assert decision.risk_score == AdaptiveAuthWeights.HIGH_VELOCITY - 10


# ─── Decision log ──────────────────────────────────────────────────────────────


def test_decision_logged():
    svc = RiskBasedAuthService()
    svc.evaluate(_ctx(is_known_device=True))
    log = svc.get_decisions()
    assert len(log) == 1
    assert log[0]["user_id"] == "u1"
    assert log[0]["risk_level"] == "low"
    assert log[0]["action"] == "proceed"


def test_get_decisions_filters_by_user():
    svc = RiskBasedAuthService()
    svc.evaluate(_ctx(user_id="a", is_known_device=True))
    svc.evaluate(_ctx(user_id="b", is_known_device=True))
    assert len(svc.get_decisions(user_id="a")) == 1
    assert len(svc.get_decisions(user_id="b")) == 1


def test_get_decisions_respects_limit():
    svc = RiskBasedAuthService()
    for i in range(10):
        svc.evaluate(_ctx(user_id=f"u{i}", is_known_device=True))
    assert len(svc.get_decisions(limit=3)) == 3


def test_get_decisions_empty():
    svc = RiskBasedAuthService()
    assert svc.get_decisions() == []


# ─── AuthContext / AuthDecision serialization ─────────────────────────────────


def test_auth_context_to_dict():
    ctx = _ctx(anomaly_score=0.9)
    d = ctx.to_dict()
    assert d["user_id"] == "u1"
    assert d["anomaly_score"] == 0.9
    assert "geolocation" in d
    assert "session_age_minutes" in d


def test_auth_decision_defaults():
    decision = AuthDecision()
    assert decision.risk_level == AuthRiskLevel.LOW
    assert decision.required_action == RequiredAction.PROCEED
    assert decision.factors == []
    assert decision.mfa_methods == []
