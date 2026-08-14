from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC

from .models import (
    AdaptiveMFASession,
    ImpossibleTravelEvent,
    RiskEvent,
    RiskPolicy,
    SessionPolicy,
)


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    c = 2 * asin(sqrt(a))
    return radius_km * c


_EVENT_TYPES = {
    "impossible_travel",
    "new_location",
    "new_device",
    "failed_login",
    "credential_stuffing",
    "password_spray",
    "brute_force",
    "suspicious_ip",
    "tor_usage",
    "vpn_usage",
    "anomalous_time",
    "anomalous_behavior",
    "high_value_action",
}

_SEVERITIES = {"low", "medium", "high", "critical"}


class AdaptiveAuthService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def evaluate_risk(
        self,
        account_id: str,
        ip_address: str,
        user_agent: str,
        location: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        score = 0
        factors: list[dict[str, Any]] = []

        travel = await self.check_impossible_travel(account_id, ip_address, location)
        if travel and travel.get("impossible"):
            score += travel.get("risk_score", 30)
            factors.append({"factor": "impossible_travel", "score": travel.get("risk_score", 30)})

        stuffing = await self.check_credential_stuffing(account_id, ip_address)
        if stuffing:
            score += stuffing
            factors.append({"factor": "credential_stuffing", "score": stuffing})

        spray = await self.check_password_spray(ip_address)
        if spray:
            score += spray
            factors.append({"factor": "password_spray", "score": spray})

        brute = await self.check_brute_force(account_id)
        if brute:
            score += brute
            factors.append({"factor": "brute_force", "score": brute})

        new_loc = await self.detect_new_location(account_id, ip_address, location)
        if new_loc:
            score += 15
            factors.append({"factor": "new_location", "score": 15})

        score = min(score, 100)

        return {"risk_score": score, "factors": factors}

    async def check_impossible_travel(
        self,
        account_id: str,
        ip_address: str,
        location: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        stmt = (
            select(RiskEvent)
            .where(
                RiskEvent.account_id == account_id,
                RiskEvent.event_type.in_(["login", "authentication"]),
                RiskEvent.is_active.is_(True),
            )
            .order_by(RiskEvent.timestamp.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        last_event = result.scalar_one_or_none()
        if not last_event or not last_event.location_lat or not last_event.location_lng:
            return None

        if not location or not location.get("lat") or not location.get("lng"):
            return None

        try:
            prev_lat = float(last_event.location_lat)
            prev_lng = float(last_event.location_lng)
            curr_lat = float(location["lat"])
            curr_lng = float(location["lng"])
        except (ValueError, TypeError):
            return None

        distance = _haversine_km(prev_lat, prev_lng, curr_lat, curr_lng)
        time_delta = datetime.now(UTC) - last_event.timestamp
        minutes = time_delta.total_seconds() / 60.0

        if minutes <= 0:
            return None

        speed = distance / (minutes / 60.0) if minutes > 0 else 0
        impossible = speed > 900

        travel_id = str(uuid.uuid4())
        travel_event = ImpossibleTravelEvent(
            uuid=str(uuid.uuid4()),
            travel_id=travel_id,
            account_id=account_id,
            session_id=None,
            previous_ip=last_event.ip_address,
            previous_location_city=last_event.location_city,
            previous_location_country=last_event.location_country,
            previous_lat=last_event.location_lat,
            previous_lng=last_event.location_lng,
            previous_timestamp=last_event.timestamp,
            current_ip=ip_address,
            current_location_city=location.get("city"),
            current_location_country=location.get("country"),
            current_lat=str(curr_lat),
            current_lng=str(curr_lng),
            current_timestamp=datetime.now(UTC),
            distance_km=distance,
            time_delta_minutes=minutes,
            speed_kmh=speed,
            impossible=impossible,
            risk_score=min(int(speed / 10), 90) if impossible else 0,
            is_active=True,
        )
        self.session.add(travel_event)

        if impossible:
            await self.record_risk_event(
                event_type="impossible_travel",
                severity="high",
                risk_score=min(int(speed / 10), 90),
                details={
                    "distance_km": distance,
                    "time_delta_minutes": minutes,
                    "speed_kmh": speed,
                    "travel_id": travel_id,
                },
                account_id=account_id,
                ip_address=ip_address,
            )

        await self.session.flush()
        return {
            "impossible": impossible,
            "distance_km": distance,
            "speed_kmh": speed,
            "risk_score": min(int(speed / 10), 90) if impossible else 0,
        }

    async def check_credential_stuffing(
        self, account_id: str, ip_address: str,
    ) -> int | None:
        since = datetime.now(UTC) - timedelta(minutes=5)
        stmt = (
            select(func.count(RiskEvent.id))
            .where(
                RiskEvent.account_id == account_id,
                RiskEvent.event_type == "failed_login",
                RiskEvent.ip_address == ip_address,
                RiskEvent.timestamp >= since,
                RiskEvent.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        count = result.scalar() or 0
        if count >= 10:
            await self.record_risk_event(
                event_type="credential_stuffing",
                severity="high",
                risk_score=40,
                details={"failed_attempts": count, "window_minutes": 5},
                account_id=account_id,
                ip_address=ip_address,
            )
            return 40
        return None

    async def check_password_spray(self, ip_address: str) -> int | None:
        since = datetime.now(UTC) - timedelta(minutes=10)
        stmt = (
            select(func.count(func.distinct(RiskEvent.account_id)))
            .where(
                RiskEvent.event_type == "failed_login",
                RiskEvent.ip_address == ip_address,
                RiskEvent.timestamp >= since,
                RiskEvent.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        distinct_accounts = result.scalar() or 0
        if distinct_accounts >= 5:
            await self.record_risk_event(
                event_type="password_spray",
                severity="high",
                risk_score=50,
                details={"distinct_accounts": distinct_accounts, "window_minutes": 10},
                account_id="",
                ip_address=ip_address,
            )
            return 50
        return None

    async def check_brute_force(self, account_id: str) -> int | None:
        since = datetime.now(UTC) - timedelta(minutes=2)
        stmt = (
            select(func.count(RiskEvent.id))
            .where(
                RiskEvent.account_id == account_id,
                RiskEvent.event_type == "failed_login",
                RiskEvent.timestamp >= since,
                RiskEvent.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        count = result.scalar() or 0
        if count >= 5:
            await self.record_risk_event(
                event_type="brute_force",
                severity="critical",
                risk_score=60,
                details={"failed_attempts": count, "window_minutes": 2},
                account_id=account_id,
            )
            return 60
        return None

    async def detect_new_location(
        self,
        account_id: str,
        ip_address: str,
        location: dict[str, Any] | None = None,
    ) -> bool:
        if not location or not location.get("city"):
            return False

        stmt = (
            select(RiskEvent)
            .where(
                RiskEvent.account_id == account_id,
                RiskEvent.location_city == location["city"],
                RiskEvent.is_active.is_(True),
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return False

        await self.record_risk_event(
            event_type="new_location",
            severity="medium",
            risk_score=15,
            details={"city": location.get("city"), "country": location.get("country")},
            account_id=account_id,
            ip_address=ip_address,
            location_city=location.get("city"),
            location_country=location.get("country"),
            location_lat=str(location.get("lat", "")),
            location_lng=str(location.get("lng", "")),
        )
        return True

    async def detect_new_device(
        self, account_id: str, device_fingerprint: str,
    ) -> bool:
        stmt = (
            select(RiskEvent)
            .where(
                RiskEvent.account_id == account_id,
                RiskEvent.details["device_fingerprint"].as_string() == device_fingerprint,
                RiskEvent.is_active.is_(True),
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return False

        await self.record_risk_event(
            event_type="new_device",
            severity="medium",
            risk_score=20,
            details={"device_fingerprint": device_fingerprint},
            account_id=account_id,
        )
        return True

    async def record_risk_event(
        self,
        event_type: str,
        severity: str,
        risk_score: int,
        details: dict[str, Any] | None = None,
        account_id: str | None = None,
        person_id: str | None = None,
        session_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        location_city: str | None = None,
        location_country: str | None = None,
        location_lat: str | None = None,
        location_lng: str | None = None,
        mitigation_action: str | None = None,
    ) -> RiskEvent:
        if event_type not in _EVENT_TYPES:
            event_type = "anomalous_behavior"
        if severity not in _SEVERITIES:
            severity = "medium"

        entity = RiskEvent(
            uuid=str(uuid.uuid4()),
            event_id=str(uuid.uuid4()).replace("-", ""),
            person_id=person_id,
            account_id=account_id,
            session_id=session_id,
            event_type=event_type,
            severity=severity,
            risk_score=min(risk_score, 100),
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            location_city=location_city,
            location_country=location_country,
            location_lat=location_lat,
            location_lng=location_lng,
            timestamp=datetime.now(UTC),
            mitigated=mitigation_action is not None,
            mitigation_action=mitigation_action,
            is_active=True,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def apply_mitigation(
        self, risk_score: int, account_id: str,
    ) -> dict[str, Any]:
        stmt = (
            select(RiskPolicy)
            .where(
                RiskPolicy.enabled.is_(True),
                RiskPolicy.is_active.is_(True),
            )
            .order_by(RiskPolicy.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        policy = result.scalar_one_or_none()

        if not policy:
            if risk_score >= 80:
                return {"action": "block", "reason": "critical_risk"}
            if risk_score >= 60:
                return {"action": "mfa_challenge", "reason": "high_risk"}
            if risk_score >= 30:
                return {"action": "mfa_challenge", "reason": "medium_risk"}
            return {"action": "allow", "reason": "low_risk"}

        if risk_score >= policy.risk_threshold_critical:
            action = policy.actions.get("critical", "lock_account")
            if action == "lock_account":
                await self.record_risk_event(
                    event_type="high_value_action",
                    severity="critical",
                    risk_score=risk_score,
                    details={"mitigation": action, "policy_id": policy.policy_id},
                    account_id=account_id,
                    mitigation_action=action,
                )
            return {"action": action, "reason": "critical_risk", "policy_id": policy.policy_id}

        if risk_score >= policy.risk_threshold_high:
            action = policy.actions.get("high", "block")
            return {"action": action, "reason": "high_risk", "policy_id": policy.policy_id}

        if risk_score >= policy.risk_threshold_medium:
            action = policy.actions.get("medium", "mfa_challenge")
            return {"action": action, "reason": "medium_risk", "policy_id": policy.policy_id}

        action = policy.actions.get("low", "allow")
        return {"action": action, "reason": "low_risk", "policy_id": policy.policy_id}

    async def create_mfa_challenge(
        self, account_id: str, mfa_type: str = "totp",
    ) -> AdaptiveMFASession:
        challenge_code = str(uuid.uuid4()).replace("-", "")[:12]
        expires_at = datetime.now(UTC) + timedelta(minutes=5)

        entity = AdaptiveMFASession(
            uuid=str(uuid.uuid4()),
            mfa_id=str(uuid.uuid4()).replace("-", ""),
            account_id=account_id,
            session_id=None,
            mfa_type=mfa_type,
            challenge=challenge_code,
            challenge_expires_at=expires_at,
            verified=False,
            attempts=0,
            max_attempts=3,
            status="pending",
            is_active=True,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def verify_mfa(
        self, mfa_id: str, challenge_response: str,
    ) -> dict[str, Any]:
        stmt = (
            select(AdaptiveMFASession)
            .where(
                AdaptiveMFASession.mfa_id == mfa_id,
                AdaptiveMFASession.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        mfa_session = result.scalar_one_or_none()

        if not mfa_session:
            return {"verified": False, "reason": "mfa_session_not_found"}

        if mfa_session.status == "verified":
            return {"verified": True, "reason": "already_verified"}

        if mfa_session.status == "expired":
            return {"verified": False, "reason": "mfa_expired"}

        if mfa_session.challenge_expires_at < datetime.now(UTC):
            mfa_session.status = "expired"
            await self.session.flush()
            return {"verified": False, "reason": "mfa_expired"}

        if mfa_session.attempts >= mfa_session.max_attempts:
            mfa_session.status = "failed"
            await self.session.flush()
            return {"verified": False, "reason": "max_attempts_exceeded"}

        mfa_session.attempts += 1

        if mfa_session.challenge == challenge_response:
            mfa_session.verified = True
            mfa_session.verified_at = datetime.now(UTC)
            mfa_session.status = "verified"
            await self.session.flush()
            return {"verified": True, "reason": "success"}

        await self.session.flush()
        remaining = mfa_session.max_attempts - mfa_session.attempts
        return {"verified": False, "reason": "invalid_challenge", "remaining_attempts": remaining}

    async def get_risk_history(
        self, account_id: str, limit: int = 50,
    ) -> list[RiskEvent]:
        stmt = (
            select(RiskEvent)
            .where(
                RiskEvent.account_id == account_id,
                RiskEvent.is_active.is_(True),
            )
            .order_by(RiskEvent.timestamp.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class SessionGovernanceService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_session_policy(self, account_type: str) -> SessionPolicy | None:
        stmt = (
            select(SessionPolicy)
            .where(
                SessionPolicy.applies_to == account_type,
                SessionPolicy.is_active.is_(True),
            )
            .order_by(SessionPolicy.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def enforce_session_policy(
        self, account_id: str, account_type: str,
    ) -> dict[str, Any]:
        policy = await self.get_session_policy(account_type)
        if not policy:
            return {"enforced": False, "reason": "no_policy_found"}

        active_count = await self.get_active_session_count(account_id)

        if not policy.allow_concurrent and active_count >= policy.max_sessions:
            if policy.terminate_previous_on_new_login:
                await self.terminate_previous_sessions(
                    account_id, current_session_id=None, notify=policy.notify_previous_device,
                )
                return {
                    "enforced": True,
                    "action": "terminated_previous",
                    "max_sessions": policy.max_sessions,
                }
            return {
                "enforced": True,
                "action": "block_new_session",
                "reason": "max_sessions_reached",
                "max_sessions": policy.max_sessions,
            }

        return {
            "enforced": True,
            "action": "allowed",
            "max_sessions": policy.max_sessions,
            "require_mfa": policy.require_mfa,
            "session_timeout_minutes": policy.session_timeout_minutes,
            "inactivity_timeout_minutes": policy.inactivity_timeout_minutes,
        }

    async def terminate_previous_sessions(
        self,
        account_id: str,
        current_session_id: str | None = None,
        notify: bool = True,
    ) -> int:
        from app.identity.models import UserSession

        stmt = (
            select(UserSession)
            .where(
                UserSession.account_id == account_id,
                UserSession.is_active.is_(True),
            )
        )
        if current_session_id:
            stmt = stmt.where(UserSession.id != current_session_id)

        result = await self.session.execute(stmt)
        sessions = list(result.scalars().all())

        count = 0
        for session in sessions:
            session.is_active = False
            session.terminated_at = datetime.now(UTC)
            session.termination_reason = "superseded_by_new_login"
            count += 1

        if count > 0:
            await self.session.flush()

        if notify and count > 0:
            await self.notify_previous_device(account_id, current_session_id)

        return count

    async def notify_previous_device(
        self, account_id: str, session_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "notification_sent": True,
            "account_id": account_id,
            "session_id": session_id,
            "channel": "push",
            "message": "New login detected from another device",
        }

    async def create_session_policy(
        self,
        policy_id: str,
        name: str,
        applies_to: str,
        max_sessions: int = 1,
        allow_concurrent: bool = False,
        require_mfa: bool = False,
        session_timeout_minutes: int | None = None,
        inactivity_timeout_minutes: int | None = None,
        notify_previous_device: bool = True,
        terminate_previous_on_new_login: bool = True,
        enforce_geo_restriction: bool = False,
        allowed_geo: dict | None = None,
        enforce_ip_restriction: bool = False,
        allowed_ips: dict | None = None,
    ) -> SessionPolicy:
        entity = SessionPolicy(
            uuid=str(uuid.uuid4()),
            policy_id=policy_id,
            name=name,
            applies_to=applies_to,
            max_sessions=max_sessions,
            allow_concurrent=allow_concurrent,
            require_mfa=require_mfa,
            session_timeout_minutes=session_timeout_minutes,
            inactivity_timeout_minutes=inactivity_timeout_minutes,
            notify_previous_device=notify_previous_device,
            terminate_previous_on_new_login=terminate_previous_on_new_login,
            enforce_geo_restriction=enforce_geo_restriction,
            allowed_geo=allowed_geo,
            enforce_ip_restriction=enforce_ip_restriction,
            allowed_ips=allowed_ips,
            is_active=True,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update_session_policy(
        self, policy_id: str, **kwargs: Any,
    ) -> SessionPolicy | None:
        stmt = select(SessionPolicy).where(
            SessionPolicy.policy_id == policy_id,
            SessionPolicy.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        if not entity:
            return None
        for key, value in kwargs.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        await self.session.flush()
        return entity

    async def check_session_expiry(self) -> int:
        from app.identity.models import UserSession

        now = datetime.now(UTC)
        expired_count = 0

        policies_result = await self.session.execute(
            select(SessionPolicy).where(SessionPolicy.is_active.is_(True)),
        )
        policies = list(policies_result.scalars().all())

        for policy in policies:
            if not policy.session_timeout_minutes:
                continue

            timeout_limit = now - timedelta(minutes=policy.session_timeout_minutes)

            stmt = (
                select(UserSession)
                .where(
                    UserSession.is_active.is_(True),
                    UserSession.created_at < timeout_limit,
                )
            )
            result = await self.session.execute(stmt)
            sessions = list(result.scalars().all())

            for session in sessions:
                session.is_active = False
                session.terminated_at = now
                session.termination_reason = "session_timeout"
                expired_count += 1

        inactivity_stmt = (
            select(UserSession)
            .where(
                UserSession.is_active.is_(True),
                UserSession.last_activity_at.isnot(None),
            )
        )
        inactivity_result = await self.session.execute(inactivity_stmt)
        all_sessions = list(inactivity_result.scalars().all())

        for session in all_sessions:
            if not session.last_activity_at:
                continue
            stmt = select(SessionPolicy).where(
                SessionPolicy.applies_to == session.account_type,
                SessionPolicy.is_active.is_(True),
            )
            policy_result = await self.session.execute(stmt)
            policy = policy_result.scalar_one_or_none()
            if policy and policy.inactivity_timeout_minutes:
                inactive_limit = datetime.now(UTC) - timedelta(minutes=policy.inactivity_timeout_minutes)
                if session.last_activity_at < inactive_limit:
                    session.is_active = False
                    session.terminated_at = datetime.now(UTC)
                    session.termination_reason = "inactivity_timeout"
                    expired_count += 1

        if expired_count > 0:
            await self.session.flush()

        return expired_count

    async def get_active_session_count(self, account_id: str) -> int:
        from app.identity.models import UserSession

        stmt = (
            select(func.count(UserSession.id))
            .where(
                UserSession.account_id == account_id,
                UserSession.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def is_session_valid(self, session_id: str) -> bool:
        from app.identity.models import UserSession

        stmt = select(UserSession).where(
            UserSession.id == session_id,
            UserSession.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            return False

        if not session.last_activity_at:
            return True

        stmt = select(SessionPolicy).where(
            SessionPolicy.applies_to == session.account_type,
            SessionPolicy.is_active.is_(True),
        )
        policy_result = await self.session.execute(stmt)
        policy = policy_result.scalar_one_or_none()

        if policy and policy.inactivity_timeout_minutes:
            inactive_limit = datetime.now(UTC) - timedelta(minutes=policy.inactivity_timeout_minutes)
            if session.last_activity_at < inactive_limit:
                session.is_active = False
                session.terminated_at = datetime.now(UTC)
                session.termination_reason = "inactivity_timeout"
                await self.session.flush()
                return False

        return True
