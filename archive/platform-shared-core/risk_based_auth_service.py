from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("gula.security.rba")


class AuthRiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequiredAction(Enum):
    PROCEED = "proceed"
    MFA_REQUIRED = "mfa_required"
    STEP_UP_AUTH = "step_up_auth"
    DEVICE_VERIFICATION = "device_verification"
    BLOCKED = "blocked"


@dataclass
class AuthContext:
    user_id: str = ""
    user_role: str = ""
    ip_address: str = ""
    device_id: str = ""
    device_trust_level: str = "unknown"
    geolocation: dict[str, Any] = field(default_factory=dict)
    previous_ips: list[str] = field(default_factory=list)
    previous_geos: list[dict[str, Any]] = field(default_factory=list)
    hour_of_day: int = 0
    day_of_week: int = 0
    is_known_device: bool = False
    login_velocity: int = 0
    failed_attempts_24h: int = 0
    is_vpn: bool = False
    is_tor: bool = False
    is_datacenter: bool = False
    browser_fingerprint: str = ""
    session_age_minutes: float = 0.0
    requested_resource: str = ""
    anomaly_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "user_role": self.user_role,
            "ip_address": self.ip_address,
            "device_id": self.device_id,
            "device_trust_level": self.device_trust_level,
            "geolocation": self.geolocation,
            "hour_of_day": self.hour_of_day,
            "is_known_device": self.is_known_device,
            "login_velocity": self.login_velocity,
            "failed_attempts_24h": self.failed_attempts_24h,
            "is_vpn": self.is_vpn,
            "is_tor": self.is_tor,
            "is_datacenter": self.is_datacenter,
            "session_age_minutes": self.session_age_minutes,
            "requested_resource": self.requested_resource,
            "anomaly_score": self.anomaly_score,
        }


@dataclass
class AuthDecision:
    risk_level: AuthRiskLevel = AuthRiskLevel.LOW
    risk_score: float = 0.0
    required_action: RequiredAction = RequiredAction.PROCEED
    factors: list[str] = field(default_factory=list)
    confidence: float = 1.0
    mfa_methods: list[str] = field(default_factory=list)
    message: str = ""
    requires_approval: bool = False


class AdaptiveAuthWeights:
    UNKNOWN_DEVICE = 25
    NEW_LOCATION = 20
    UNUSUAL_HOUR = 15
    HIGH_VELOCITY = 20
    FAILED_ATTEMPTS = 15
    VPN_PROXY = 10
    TOR = 30
    DATACENTER_IP = 15
    ANOMALY = 10
    UNUSUAL_RESOURCE = 10


class RiskBasedAuthService:
    def __init__(self):
        self._decision_log: list[dict[str, Any]] = []
        self._velocity_tracker: dict[str, list[float]] = {}

    def evaluate(self, context: AuthContext) -> AuthDecision:
        risk_score = 0.0
        factors: list[str] = []

        if context.is_known_device:
            device_factor = -10
            factors.append(f"-10 known device ({context.device_trust_level})")
        else:
            device_factor = AdaptiveAuthWeights.UNKNOWN_DEVICE
            factors.append(f"+{AdaptiveAuthWeights.UNKNOWN_DEVICE} unknown device")

        risk_score += device_factor

        if context.previous_geos and context.geolocation and not self._is_known_location(context.geolocation, context.previous_geos):
            risk_score += AdaptiveAuthWeights.NEW_LOCATION
            factors.append(f"+{AdaptiveAuthWeights.NEW_LOCATION} new location")

        if context.hour_of_day < 6 or context.hour_of_day > 23:
            risk_score += AdaptiveAuthWeights.UNUSUAL_HOUR
            factors.append(
                f"+{AdaptiveAuthWeights.UNUSUAL_HOUR} unusual hour ({context.hour_of_day}:00)"
            )

        velocity = max(self._check_velocity(context.user_id), context.login_velocity)
        if velocity > 5:
            risk_score += AdaptiveAuthWeights.HIGH_VELOCITY
            factors.append(
                f"+{AdaptiveAuthWeights.HIGH_VELOCITY} high login velocity ({velocity}/min)"
            )

        if context.failed_attempts_24h > 3:
            f_score = min(AdaptiveAuthWeights.FAILED_ATTEMPTS, context.failed_attempts_24h * 5)
            risk_score += f_score
            factors.append(f"+{f_score} failed attempts ({context.failed_attempts_24h}/24h)")

        if context.is_vpn:
            risk_score += AdaptiveAuthWeights.VPN_PROXY
            factors.append(f"+{AdaptiveAuthWeights.VPN_PROXY} VPN/proxy detected")

        if context.is_tor:
            risk_score += AdaptiveAuthWeights.TOR
            factors.append(f"+{AdaptiveAuthWeights.TOR} Tor exit node")

        if context.is_datacenter:
            risk_score += AdaptiveAuthWeights.DATACENTER_IP
            factors.append(f"+{AdaptiveAuthWeights.DATACENTER_IP} datacenter IP")

        if context.anomaly_score > 0.5:
            risk_score += AdaptiveAuthWeights.ANOMALY * context.anomaly_score
            factors.append(
                f"+{AdaptiveAuthWeights.ANOMALY * context.anomaly_score:.1f} anomaly score ({context.anomaly_score:.2f})"
            )

        risk_score = max(0, min(100, risk_score))

        decision = self._classify_risk(risk_score, factors, context)
        self._log_decision(context, decision)
        return decision

    def _check_velocity(self, user_id: str) -> int:
        now = time.time()
        window = 60
        attempts = self._velocity_tracker.setdefault(user_id, [])
        attempts[:] = [t for t in attempts if now - t < window]
        attempts.append(now)
        return len(attempts)

    def _is_known_location(
        self,
        current: dict[str, Any],
        previous: list[dict[str, Any]],
    ) -> bool:
        for prev in previous:
            if prev.get("country") == current.get("country"):
                if prev.get("city") == current.get("city"):
                    return True
                dist = self._haversine(
                    prev.get("lat", 0),
                    prev.get("lon", 0),
                    current.get("lat", 0),
                    current.get("lon", 0),
                )
                if dist < 100:
                    return True
        return False

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _impossible_travel_check(self, context: AuthContext) -> bool:
        if not context.previous_geos or not context.geolocation:
            return False
        last_geo = context.previous_geos[-1]
        current_geo = context.geolocation
        dist = self._haversine(
            last_geo.get("lat", 0),
            last_geo.get("lon", 0),
            current_geo.get("lat", 0),
            current_geo.get("lon", 0),
        )
        if dist < 50:
            return False
        min_hours = dist / 900
        if context.session_age_minutes < min_hours * 60:
            logger.warning(
                "Impossible travel detected for user %s: %.0fkm in %.0fmin",
                context.user_id,
                dist,
                context.session_age_minutes,
            )
            return True
        return False

    def _classify_risk(
        self,
        risk_score: float,
        factors: list[str],
        context: AuthContext,
    ) -> AuthDecision:
        if self._impossible_travel_check(context):
            return AuthDecision(
                risk_level=AuthRiskLevel.CRITICAL,
                risk_score=100,
                required_action=RequiredAction.BLOCKED,
                factors=[*factors, "impossible_travel"],
                message="Blocked due to impossible travel detection",
            )

        if risk_score >= 70:
            return AuthDecision(
                risk_level=AuthRiskLevel.CRITICAL,
                risk_score=risk_score,
                required_action=RequiredAction.BLOCKED,
                factors=factors,
                message="Access blocked due to high risk",
            )

        if risk_score >= 50:
            return AuthDecision(
                risk_level=AuthRiskLevel.HIGH,
                risk_score=risk_score,
                required_action=RequiredAction.MFA_REQUIRED,
                factors=factors,
                mfa_methods=["totp", "webauthn"],
                message="Additional verification required",
            )

        if risk_score >= 30:
            return AuthDecision(
                risk_level=AuthRiskLevel.MEDIUM,
                risk_score=risk_score,
                required_action=RequiredAction.STEP_UP_AUTH,
                factors=factors,
                mfa_methods=["totp"],
                message="Step-up authentication recommended",
                requires_approval=risk_score >= 40,
            )

        return AuthDecision(
            risk_level=AuthRiskLevel.LOW,
            risk_score=risk_score,
            required_action=RequiredAction.PROCEED,
            factors=factors,
            message="Access granted",
        )

    def _log_decision(self, context: AuthContext, decision: AuthDecision) -> None:
        entry = {
            "timestamp": time.time(),
            "user_id": context.user_id,
            "risk_score": decision.risk_score,
            "risk_level": decision.risk_level.value,
            "action": decision.required_action.value,
            "factors": decision.factors,
            "ip_address": context.ip_address,
            "device_id": context.device_id,
        }
        self._decision_log.append(entry)
        if decision.risk_level in (AuthRiskLevel.HIGH, AuthRiskLevel.CRITICAL):
            logger.warning(
                "Risk Based Auth: user=%s score=%.1f level=%s action=%s factors=%s",
                context.user_id,
                decision.risk_score,
                decision.risk_level.value,
                decision.required_action.value,
                decision.factors,
            )

    def get_decisions(self, user_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if user_id:
            return [d for d in self._decision_log if d["user_id"] == user_id][-limit:]
        return list(self._decision_log[-limit:])
