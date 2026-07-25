from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import threading
import time as time_module
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import pyotp

from security.modules.identity.models import AuthFactor, RiskLevel

logger = logging.getLogger("gula.security.modules.identity.mfa")

_RECOVERY_CODE_COUNT = 10
_RECOVERY_CODE_LENGTH = 12
_STEP_UP_TTL = 300


class MFAManager:
    def __init__(self, redis_client: Any = None) -> None:
        self._redis = redis_client
        self._lock = threading.Lock()
        self._enrolled_users: dict[str, dict[str, Any]] = {}
        self._step_up_sessions: dict[str, dict[str, Any]] = {}
        self._adaptive_policies: list[dict[str, Any]] = []
        self._backend_service: Any = None

        try:
            from backend.app.security.mfa_service import MFAService
            self._backend_service = MFAService
        except ImportError:
            pass

    def generate_totp_secret(self) -> str:
        return pyotp.random_base32()

    def generate_totp_uri(self, secret: str, email: str, issuer: str = "GULA Platform") -> str:
        return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)

    def generate_hotp_secret(self) -> str:
        return pyotp.random_base32()

    def generate_hotp_uri(self, secret: str, email: str, counter: int = 0, issuer: str = "GULA Platform") -> str:
        return pyotp.hotp.HOTP(secret).provisioning_uri(name=email, issuer_name=issuer, initial_count=counter)

    def verify_totp(self, secret: str, token: str, tolerance: int = 1) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=tolerance)

    def verify_hotp(self, secret: str, token: str, counter: int) -> bool:
        hotp = pyotp.HOTP(secret)
        return hotp.verify(token, counter)

    def get_totp_remaining_seconds(self, secret: str) -> int:
        totp = pyotp.TOTP(secret)
        return totp.interval - (int(time_module.time()) % totp.interval)

    def generate_recovery_codes(self, count: int = _RECOVERY_CODE_COUNT) -> list[str]:
        codes: list[str] = []
        for _ in range(count):
            code = secrets.token_hex(_RECOVERY_CODE_LENGTH // 2)
            parts = [code[i:i + 4] for i in range(0, len(code), 4)]
            codes.append("-".join(parts).upper())
        return codes

    def hash_recovery_code(self, code: str) -> str:
        return hashlib.sha256(code.encode()).hexdigest()

    def verify_recovery_code(self, code: str, hashed_codes: list[str]) -> str | None:
        hashed = self.hash_recovery_code(code)
        for stored in hashed_codes:
            if hmac.compare_digest(hashed, stored):
                return stored
        return None

    def enroll_totp(self, user_id: str, email: str, device_name: str = "Authenticator App") -> dict[str, Any]:
        secret = self.generate_totp_secret()
        uri = self.generate_totp_uri(secret, email)
        backup_codes = self.generate_recovery_codes()

        device: dict[str, Any] = {
            "device_type": "totp",
            "device_name": device_name,
            "secret": secret,
            "is_active": True,
            "is_primary": True,
            "backup_codes": [self.hash_recovery_code(c) for c in backup_codes],
            "enrolled_at": datetime.now(timezone.utc).isoformat(),
        }

        with self._lock:
            if user_id not in self._enrolled_users:
                self._enrolled_users[user_id] = {"devices": [], "methods": []}
            self._enrolled_users[user_id]["devices"].append(device)
            if AuthFactor.TOTP not in self._enrolled_users[user_id]["methods"]:
                self._enrolled_users[user_id]["methods"].append(AuthFactor.TOTP)

        return {"secret": secret, "uri": uri, "backup_codes": backup_codes, "device_name": device_name}

    def verify_mfa(self, user_id: str, token: str, factor: AuthFactor = AuthFactor.TOTP) -> bool:
        user_data = self._enrolled_users.get(user_id)
        if user_data is None:
            return False

        devices = [d for d in user_data.get("devices", []) if d.get("device_type") == factor.value and d.get("is_active")]
        for device in devices:
            secret = device.get("secret", "")
            if factor == AuthFactor.TOTP:
                if self.verify_totp(secret, token):
                    device["last_used_at"] = datetime.now(timezone.utc).isoformat()
                    return True
            elif factor == AuthFactor.SMS or factor == AuthFactor.EMAIL:
                if self._verify_sms_email_code(user_id, token, factor):
                    return True

            backup = device.get("backup_codes", [])
            matched = self.verify_recovery_code(token, backup)
            if matched:
                backup.remove(matched)
                device["backup_codes"] = backup
                return True

        return False

    def _verify_sms_email_code(self, user_id: str, code: str, factor: AuthFactor) -> bool:
        if self._redis is not None:
            try:
                key = f"otp:{factor.value}:{user_id}"
                stored = self._redis.get(key)
                if stored is not None and hmac.compare_digest(stored, code):
                    self._redis.delete(key)
                    return True
            except Exception:
                pass
        return False

    def store_otp_code(self, user_id: str, code: str, factor: AuthFactor, ttl: int = 300) -> None:
        if self._redis is not None:
            try:
                key = f"otp:{factor.value}:{user_id}"
                self._redis.set(key, code, ex=ttl)
            except Exception as exc:
                logger.warning("Failed to store OTP code: %s", exc)

    def get_enrolled_methods(self, user_id: str) -> list[AuthFactor]:
        user_data = self._enrolled_users.get(user_id)
        if user_data is None:
            return []
        return list(user_data.get("methods", []))

    def is_mfa_enabled(self, user_id: str) -> bool:
        return len(self.get_enrolled_methods(user_id)) > 0

    def remove_device(self, user_id: str, device_type: str) -> bool:
        user_data = self._enrolled_users.get(user_id)
        if user_data is None:
            return False
        with self._lock:
            before = len(user_data["devices"])
            user_data["devices"] = [d for d in user_data["devices"] if d.get("device_type") != device_type]
            user_data["methods"] = [m for m in user_data["methods"] if m.value != device_type]
        return len(user_data["devices"]) < before

    def step_up_authentication(
        self,
        user_id: str,
        target_risk: RiskLevel,
        current_risk: RiskLevel = RiskLevel.LOW,
    ) -> dict[str, Any]:
        risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        if risk_order.index(current_risk) >= risk_order.index(target_risk):
            return {"step_up_required": False, "message": "Current risk level sufficient"}

        session_token = secrets.token_urlsafe(32)
        step_up_data: dict[str, Any] = {
            "user_id": user_id,
            "current_risk": current_risk.value,
            "target_risk": target_risk.value,
            "session_token": session_token,
            "created_at": time_module.time(),
            "expires_at": time_module.time() + _STEP_UP_TTL,
            "verified": False,
        }
        with self._lock:
            self._step_up_sessions[session_token] = step_up_data

        return {
            "step_up_required": True,
            "session_token": session_token,
            "target_risk": target_risk.value,
            "message": f"Additional authentication required for {target_risk.value} risk level",
        }

    def verify_step_up(self, session_token: str) -> bool:
        with self._lock:
            session = self._step_up_sessions.pop(session_token, None)
        if session is None:
            return False
        if time_module.time() > session["expires_at"]:
            return False
        session["verified"] = True
        return True

    def add_adaptive_policy(
        self,
        condition_fn: Callable[[dict[str, Any]], bool],
        action: str,
        name: str = "",
    ) -> None:
        self._adaptive_policies.append({"name": name, "condition": condition_fn, "action": action})

    def evaluate_adaptive_policy(self, context: dict[str, Any]) -> str | None:
        for policy in self._adaptive_policies:
            try:
                if policy["condition"](context):
                    logger.debug("Adaptive MFA policy triggered: %s -> %s", policy.get("name"), policy["action"])
                    return policy["action"]
            except Exception as exc:
                logger.warning("Adaptive policy evaluation error: %s", exc)
        return None

    def get_user_devices(self, user_id: str) -> list[dict[str, Any]]:
        user_data = self._enrolled_users.get(user_id)
        if user_data is None:
            return []
        return [
            {
                "device_type": d.get("device_type"),
                "device_name": d.get("device_name"),
                "is_active": d.get("is_active", True),
                "is_primary": d.get("is_primary", False),
                "enrolled_at": d.get("enrolled_at", ""),
                "last_used_at": d.get("last_used_at", ""),
            }
            for d in user_data["devices"]
        ]

    def enroll_backend(
        self,
        db_session: Any,
        user_id: int,
        email: str,
        device_name: str = "Authenticator App",
    ) -> dict[str, Any] | None:
        if self._backend_service is None:
            return None
        try:
            service = self._backend_service(db_session)
            return service.setup_totp(user_id, email, device_name)
        except Exception as exc:
            logger.warning("Backend MFA enrollment failed: %s", exc)
            return None

    def verify_backend(self, db_session: Any, user_id: int, token: str) -> bool:
        if self._backend_service is None:
            return False
        try:
            service = self._backend_service(db_session)
            return service.verify_totp(user_id, token)
        except Exception:
            return False
