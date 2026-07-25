from __future__ import annotations

import hashlib
import logging
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from security.modules.identity.models import AuthenticationMethod, RiskLevel, SessionInfo

logger = logging.getLogger("gula.security.modules.identity.session")

_DEFAULT_IDLE_TIMEOUT = 1800
_DEFAULT_ABSOLUTE_TIMEOUT = 43200
_DEFAULT_MAX_CONCURRENT = 5


class SessionManager:
    def __init__(
        self,
        redis_client: Any = None,
        idle_timeout: int = _DEFAULT_IDLE_TIMEOUT,
        absolute_timeout: int = _DEFAULT_ABSOLUTE_TIMEOUT,
        max_concurrent_sessions: int = _DEFAULT_MAX_CONCURRENT,
    ) -> None:
        self._redis = redis_client
        self._idle_timeout = idle_timeout
        self._absolute_timeout = absolute_timeout
        self._max_concurrent = max_concurrent_sessions
        self._lock = threading.Lock()
        self._sessions: dict[str, dict[str, Any]] = {}
        self._user_sessions: dict[str, list[str]] = {}
        self._device_map: dict[str, str] = {}

        try:
            from backend.app.security.session import bump_perm_version as _bump
            from backend.app.security.session import warm_perm_version as _warm
            self._backend_bump = _bump
            self._backend_warm = _warm
        except ImportError:
            self._backend_bump = None
            self._backend_warm = None

    def create_session(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str = "",
        auth_methods: list[AuthenticationMethod] | None = None,
        risk_level: RiskLevel = RiskLevel.LOW,
        device_id: str = "",
    ) -> SessionInfo:
        self._enforce_concurrent_limit(user_id)

        session_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self._absolute_timeout)

        session_data: dict[str, Any] = {
            "session_id": session_id,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "auth_methods": [m.value for m in (auth_methods or [])],
            "risk_level": risk_level.value,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_activity": now.isoformat(),
            "is_active": True,
            "device_id": device_id,
            "original_ip": ip_address,
            "original_ua": user_agent,
        }

        with self._lock:
            self._sessions[session_id] = session_data
            self._user_sessions.setdefault(user_id, []).append(session_id)
            if device_id:
                self._device_map[device_id] = session_id

        if self._redis is not None:
            try:
                key = f"session:{session_id}"
                self._redis.set(key, str(session_data), ex=self._absolute_timeout)
            except Exception as exc:
                logger.warning("Redis session store failed: %s", exc)

        logger.info("Session created: %s for user %s", session_id[:16], user_id)
        return SessionInfo(
            session_id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            auth_methods=auth_methods or [],
            risk_level=risk_level,
            created_at=now,
            expires_at=expires_at,
            last_activity=now,
        )

    def get_session(self, session_id: str) -> SessionInfo | None:
        session = self._get_session_data(session_id)
        if session is None:
            return None
        if not session.get("is_active", True):
            return None

        now = datetime.now(timezone.utc)
        expires_at = datetime.fromisoformat(session["expires_at"])
        if now > expires_at:
            self.destroy_session(session_id)
            return None

        last_activity = datetime.fromisoformat(session["last_activity"])
        if (now - last_activity).total_seconds() > self._idle_timeout:
            self.destroy_session(session_id)
            return None

        return SessionInfo(
            session_id=session["session_id"],
            user_id=session["user_id"],
            ip_address=session["ip_address"],
            user_agent=session.get("user_agent", ""),
            auth_methods=[AuthenticationMethod(m) for m in session.get("auth_methods", [])],
            risk_level=RiskLevel(session.get("risk_level", "low")),
            created_at=datetime.fromisoformat(session["created_at"]),
            expires_at=expires_at,
            last_activity=last_activity,
        )

    def touch_session(self, session_id: str) -> bool:
        session = self._get_session_data(session_id)
        if session is None or not session.get("is_active", True):
            return False
        session["last_activity"] = datetime.now(timezone.utc).isoformat()

        with self._lock:
            self._sessions[session_id] = session

        if self._redis is not None:
            try:
                remaining = self._absolute_timeout - (time.time() - datetime.fromisoformat(session["created_at"]).timestamp())
                if remaining > 0:
                    key = f"session:{session_id}"
                    self._redis.set(key, str(session), ex=int(remaining))
            except Exception:
                pass
        return True

    def destroy_session(self, session_id: str) -> bool:
        session = self._get_session_data(session_id)
        if session is None:
            return False

        user_id = session["user_id"]
        device_id = session.get("device_id", "")

        with self._lock:
            self._sessions.pop(session_id, None)
            if user_id in self._user_sessions:
                try:
                    self._user_sessions[user_id].remove(session_id)
                except ValueError:
                    pass
            if device_id:
                self._device_map.pop(device_id, None)

        if self._redis is not None:
            try:
                self._redis.delete(f"session:{session_id}")
            except Exception:
                pass

        logger.info("Session destroyed: %s for user %s", session_id[:16], user_id)
        return True

    def destroy_user_sessions(self, user_id: str, exclude_session_id: str | None = None) -> int:
        count = 0
        with self._lock:
            sessions = list(self._user_sessions.get(user_id, []))
            for sid in sessions:
                if exclude_session_id and sid == exclude_session_id:
                    continue
                if self.destroy_session(sid):
                    count += 1
        return count

    def get_user_sessions(self, user_id: str) -> list[SessionInfo]:
        sessions: list[SessionInfo] = []
        with self._lock:
            session_ids = list(self._user_sessions.get(user_id, []))
        for sid in session_ids:
            info = self.get_session(sid)
            if info is not None:
                sessions.append(info)
        return sessions

    def detect_hijacking(self, session_id: str, ip_address: str, user_agent: str, geolocation: dict[str, Any] | None = None) -> list[str]:
        session = self._get_session_data(session_id)
        if session is None:
            return ["session_not_found"]

        alerts: list[str] = []

        if ip_address and session.get("original_ip") and ip_address != session["original_ip"]:
            alerts.append("ip_address_change")

        if user_agent and session.get("original_ua") and user_agent != session["original_ua"]:
            alerts.append("user_agent_change")

        if geolocation and session.get("original_ip"):
            try:
                import ipaddress
                new_addr = ipaddress.ip_address(ip_address)
                orig_addr = ipaddress.ip_address(session["original_ip"])
                if str(new_addr)[:8] != str(orig_addr)[:8]:
                    alerts.append("geolocation_change")
            except (ValueError, TypeError):
                pass

        if alerts:
            logger.warning(
                "Session hijacking detected: %s for session %s: %s",
                session_id[:16], alerts,
            )

        return alerts

    def get_active_session_count(self, user_id: str) -> int:
        with self._lock:
            return len(self._user_sessions.get(user_id, []))

    def update_risk_level(self, session_id: str, risk_level: RiskLevel) -> bool:
        session = self._get_session_data(session_id)
        if session is None:
            return False
        session["risk_level"] = risk_level.value
        with self._lock:
            self._sessions[session_id] = session
        return True

    def _enforce_concurrent_limit(self, user_id: str) -> None:
        with self._lock:
            sessions = list(self._user_sessions.get(user_id, []))
        if len(sessions) >= self._max_concurrent:
            sessions.sort(key=lambda sid: self._get_session_data(sid).get("last_activity", "") if self._get_session_data(sid) else "")
            oldest = sessions[0]
            self.destroy_session(oldest)
            logger.info("Concurrent session limit reached for user %s, evicting oldest session", user_id)

    def _get_session_data(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is not None:
                return session

        if self._redis is not None:
            try:
                raw = self._redis.get(f"session:{session_id}")
                if raw:
                    import ast
                    try:
                        return ast.literal_eval(raw)
                    except (ValueError, SyntaxError):
                        pass
            except Exception:
                pass
        return None

    def set_idle_timeout(self, timeout: int) -> None:
        self._idle_timeout = timeout

    def set_absolute_timeout(self, timeout: int) -> None:
        self._absolute_timeout = timeout

    def set_max_concurrent(self, limit: int) -> None:
        self._max_concurrent = limit

    def cleanup_expired_sessions(self) -> int:
        count = 0
        with self._lock:
            expired = []
            now = datetime.now(timezone.utc)
            for sid, session in list(self._sessions.items()):
                expires_at = datetime.fromisoformat(session["expires_at"])
                last_activity = datetime.fromisoformat(session["last_activity"])
                if now > expires_at or (now - last_activity).total_seconds() > self._idle_timeout:
                    expired.append(sid)
            for sid in expired:
                self._sessions.pop(sid, None)
                user_id = None
                for uid, sids in list(self._user_sessions.items()):
                    if sid in sids:
                        user_id = uid
                        sids.remove(sid)
                        break
                if user_id and not self._user_sessions.get(user_id):
                    self._user_sessions.pop(user_id, None)
                count += 1
        return count
