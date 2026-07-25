from __future__ import annotations

import ipaddress
import logging
import math
import re
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from security.modules.identity.models import RiskLevel

logger = logging.getLogger("gula.security.modules.identity.risk_engine")

_RISK_WEIGHTS: dict[str, float] = {
    "ip_reputation": 0.15,
    "geolocation_anomaly": 0.15,
    "device_fingerprint": 0.10,
    "behavior_pattern": 0.15,
    "time_anomaly": 0.10,
    "failed_attempts_velocity": 0.15,
    "credential_stuffing": 0.10,
    "impossible_travel": 0.10,
}

_RISK_THRESHOLDS: dict[RiskLevel, float] = {
    RiskLevel.LOW: 0.3,
    RiskLevel.MEDIUM: 0.5,
    RiskLevel.HIGH: 0.75,
    RiskLevel.CRITICAL: 0.9,
}

_KNOWN_BAD_IPS: set[str] = {
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "127.0.0.0/8",
    "169.254.0.0/16",
}


class RiskEngine:
    def __init__(self, redis_client: Any = None) -> None:
        self._redis = redis_client
        self._lock = threading.Lock()
        self._weights: dict[str, float] = dict(_RISK_WEIGHTS)
        self._thresholds: dict[RiskLevel, float] = dict(_RISK_THRESHOLDS)
        self._historical_profiles: dict[str, dict[str, Any]] = {}
        self._failed_attempts: dict[str, list[float]] = defaultdict(list)
        self._known_locations: dict[str, tuple[float, float]] = {}
        self._custom_factors: list[Callable[[dict[str, Any]], float]] = []

    def set_weight(self, factor: str, weight: float) -> None:
        with self._lock:
            self._weights[factor] = weight

    def set_threshold(self, level: RiskLevel, threshold: float) -> None:
        with self._lock:
            self._thresholds[level] = threshold

    def add_custom_factor(self, fn: Callable[[dict[str, Any]], float]) -> None:
        self._custom_factors.append(fn)

    def _score_ip_reputation(self, context: dict[str, Any]) -> float:
        ip_str = context.get("ip_address", "")
        if not ip_str:
            return 0.0

        try:
            addr = ipaddress.ip_address(ip_str)
            if addr.is_private or addr.is_loopback or addr.is_reserved:
                return 0.1
            if addr.is_global:
                if self._redis is not None:
                    try:
                        rep = self._redis.get(f"ip:reputation:{ip_str}")
                        if rep is not None:
                            return min(float(rep), 1.0)
                    except Exception:
                        pass
        except ValueError:
            return 0.5

        tor_exit_pattern = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        if tor_exit_pattern.fullmatch(ip_str):
            try:
                import socket
                hostname = socket.gethostbyaddr(ip_str)[0]
                if "tor" in hostname.lower():
                    return 0.8
            except Exception:
                pass

        return 0.1

    def _score_geolocation_anomaly(self, context: dict[str, Any]) -> float:
        geo = context.get("geolocation", {})
        latitude = geo.get("latitude") if isinstance(geo, dict) else None
        longitude = geo.get("longitude") if isinstance(geo, dict) else None
        user_id = context.get("user_id", "")

        if latitude is None or longitude is None or not user_id:
            return 0.3

        known = self._known_locations.get(user_id)
        if known is None:
            return 0.1

        lat_diff = abs(latitude - known[0])
        lon_diff = abs(longitude - known[1])
        distance = math.sqrt(lat_diff ** 2 + lon_diff ** 2) * 111

        if distance > 1000:
            return 0.9
        if distance > 500:
            return 0.7
        if distance > 100:
            return 0.4
        return 0.1

    def _score_device_fingerprint(self, context: dict[str, Any]) -> float:
        device_id = context.get("device_id", "")
        user_agent = context.get("user_agent", "")
        user_id = context.get("user_id", "")

        if not device_id and not user_agent:
            return 0.5

        if user_id and device_id:
            profile = self._historical_profiles.get(user_id, {})
            known_devices = profile.get("known_devices", [])
            if device_id not in known_devices:
                return 0.6
            return 0.1

        if user_id and user_agent:
            profile = self._historical_profiles.get(user_id, {})
            known_agents = profile.get("known_user_agents", [])
            if user_agent not in known_agents:
                return 0.4
            return 0.1

        return 0.3

    def _score_behavior_pattern(self, context: dict[str, Any]) -> float:
        user_id = context.get("user_id", "")
        requested_resource = context.get("resource", "")
        action = context.get("action", "")

        if not user_id:
            return 0.3

        profile = self._historical_profiles.get(user_id, {})
        patterns = profile.get("behavior_patterns", {})

        if not patterns:
            return 0.1

        resource_key = f"{requested_resource}:{action}"
        if resource_key in patterns:
            frequency = patterns[resource_key]
            if frequency > 100:
                return 0.1
            if frequency > 10:
                return 0.2
            return 0.3

        return 0.5

    def _score_time_anomaly(self, context: dict[str, Any]) -> float:
        user_id = context.get("user_id", "")
        current_hour = datetime.now(UTC).hour

        if not user_id:
            return 0.3

        profile = self._historical_profiles.get(user_id, {})
        active_hours = profile.get("active_hours", set())

        if not active_hours:
            return 0.1

        if current_hour in active_hours:
            return 0.1

        distance = min(abs(current_hour - h) for h in active_hours) if active_hours else 12
        return min(distance * 0.1, 0.9)

    def _score_failed_attempts_velocity(self, context: dict[str, Any]) -> float:
        user_id = context.get("user_id", "")
        if not user_id:
            return 0.3

        now = time.time()
        window = 300

        with self._lock:
            attempts = [t for t in self._failed_attempts.get(user_id, []) if now - t < window]
            self._failed_attempts[user_id] = attempts

        count = len(attempts)

        if count >= 20:
            return 1.0
        if count >= 10:
            return 0.8
        if count >= 5:
            return 0.5
        if count >= 3:
            return 0.3
        return 0.0

    def _score_credential_stuffing(self, context: dict[str, Any]) -> float:
        ip_str = context.get("ip_address", "")
        if not ip_str:
            return 0.0

        now = time.time()
        window = 60

        key = f"stuffing:{ip_str}"
        if self._redis is not None:
            try:
                count_str = self._redis.get(key)
                count = int(count_str) if count_str else 0
                if count >= 30:
                    return 0.9
                if count >= 15:
                    return 0.6
                if count >= 5:
                    return 0.3
            except Exception:
                pass

        return 0.0

    def _score_impossible_travel(self, context: dict[str, Any]) -> float:
        user_id = context.get("user_id", "")
        geo = context.get("geolocation", {})

        if not user_id or not geo:
            return 0.0

        latitude = geo.get("latitude") if isinstance(geo, dict) else None
        longitude = geo.get("longitude") if isinstance(geo, dict) else None
        if latitude is None or longitude is None:
            return 0.0

        now = time.time()
        profile = self._historical_profiles.get(user_id, {})
        last_auth = profile.get("last_authentication")

        if last_auth is None:
            return 0.0

        last_time = last_auth.get("timestamp", 0)
        last_lat = last_auth.get("latitude")
        last_lon = last_auth.get("longitude")

        if last_lat is None or last_lon is None:
            return 0.0

        time_diff = now - last_time
        if time_diff < 60:
            return 0.0

        lat_diff = abs(latitude - last_lat)
        lon_diff = abs(longitude - last_lon)
        distance_km = math.sqrt(lat_diff ** 2 + lon_diff ** 2) * 111

        speed_kmh = (distance_km / (time_diff / 3600)) if time_diff > 0 else 0

        if speed_kmh > 900:
            return 0.95
        if speed_kmh > 500:
            return 0.7
        if speed_kmh > 100:
            return 0.3
        return 0.0

    def calculate_risk(self, context: dict[str, Any]) -> dict[str, Any]:
        factors = {
            "ip_reputation": self._score_ip_reputation(context),
            "geolocation_anomaly": self._score_geolocation_anomaly(context),
            "device_fingerprint": self._score_device_fingerprint(context),
            "behavior_pattern": self._score_behavior_pattern(context),
            "time_anomaly": self._score_time_anomaly(context),
            "failed_attempts_velocity": self._score_failed_attempts_velocity(context),
            "credential_stuffing": self._score_credential_stuffing(context),
            "impossible_travel": self._score_impossible_travel(context),
        }

        custom_score = 0.0
        for fn in self._custom_factors:
            try:
                custom_score = max(custom_score, fn(context))
            except Exception as exc:
                logger.warning("Custom risk factor error: %s", exc)

        if custom_score > 0:
            factors["custom_factors"] = custom_score

        total_weight = sum(self._weights.get(k, 0.1) for k in factors)
        if total_weight == 0:
            total_weight = 1.0

        weighted_score = sum(
            factors[k] * self._weights.get(k, 0.1) for k in factors
        ) / total_weight

        weighted_score = max(0.0, min(1.0, weighted_score))

        risk_level = RiskLevel.LOW
        for level, threshold in sorted(self._thresholds.items(), key=lambda x: x[1]):
            if weighted_score >= threshold:
                risk_level = level

        return {
            "score": round(weighted_score, 4),
            "level": risk_level.value,
            "factors": factors,
            "timestamp": time.time(),
        }

    def get_risk_based_action(self, risk: dict[str, Any]) -> str:
        level = risk.get("level", "low")
        score = risk.get("score", 0.0)

        if level == RiskLevel.CRITICAL.value or score >= 0.9:
            return "deny"
        if level == RiskLevel.HIGH.value:
            return "require_admin_approval"
        if level == RiskLevel.MEDIUM.value:
            return "challenge_mfa"
        if score > 0.3:
            return "step_up"
        return "allow"

    def record_failed_attempt(self, user_id: str) -> None:
        now = time.time()
        with self._lock:
            self._failed_attempts[user_id].append(now)

    def record_successful_auth(self, user_id: str, context: dict[str, Any]) -> None:
        now = time.time()
        with self._lock:
            self._failed_attempts[user_id] = []

        profile = self._historical_profiles.get(user_id, {})
        if not profile:
            profile = {
                "known_devices": [],
                "known_user_agents": [],
                "behavior_patterns": {},
                "active_hours": set(),
                "last_authentication": None,
            }

        device_id = context.get("device_id", "")
        if device_id and device_id not in profile["known_devices"]:
            profile["known_devices"].append(device_id)

        user_agent = context.get("user_agent", "")
        if user_agent and user_agent not in profile["known_user_agents"]:
            profile["known_user_agents"].append(user_agent)

        resource = context.get("resource", "")
        action = context.get("action", "")
        if resource and action:
            key = f"{resource}:{action}"
            profile["behavior_patterns"][key] = profile["behavior_patterns"].get(key, 0) + 1

        current_hour = datetime.now(UTC).hour
        profile["active_hours"].add(current_hour)

        geo = context.get("geolocation", {})
        if isinstance(geo, dict):
            lat = geo.get("latitude")
            lon = geo.get("longitude")
            if lat is not None and lon is not None:
                self._known_locations[user_id] = (lat, lon)
                profile["last_authentication"] = {
                    "timestamp": now,
                    "latitude": lat,
                    "longitude": lon,
                }

        with self._lock:
            self._historical_profiles[user_id] = profile

    def get_session_risk(self, user_id: str, session_id: str) -> float:
        profile = self._historical_profiles.get(user_id, {})
        session_risks = profile.get("session_risks", {})
        return session_risks.get(session_id, 0.0)

    def update_session_risk(self, user_id: str, session_id: str, score: float) -> None:
        profile = self._historical_profiles.get(user_id, {})
        if "session_risks" not in profile:
            profile["session_risks"] = {}
        profile["session_risks"][session_id] = score
        with self._lock:
            self._historical_profiles[user_id] = profile

    def get_historical_profile(self, user_id: str) -> dict[str, Any]:
        return self._historical_profiles.get(user_id, {})

    def report_ip_reputation(self, ip_address: str, score: float) -> None:
        if self._redis is not None:
            try:
                self._redis.set(f"ip:reputation:{ip_address}", str(score), ex=86400)
            except Exception:
                pass

    def get_risk_level(self, score: float) -> RiskLevel:
        for level, threshold in sorted(self._thresholds.items(), key=lambda x: x[1]):
            if score >= threshold:
                return level
        return RiskLevel.LOW
