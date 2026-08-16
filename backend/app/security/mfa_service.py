from __future__ import annotations

import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import update
from sqlalchemy.orm import Session

from app._compat import UTC
from app.config import IS_PRODUCTION
from app.models.mfa_device import MFADevice, MFASession
from shared.auth.mfa import (
    generate_backup_codes,
    generate_totp_secret,
    generate_totp_uri,
    hash_backup_codes,
    verify_backup_code,
    verify_totp,
)
from shared.auth.webauthn import (
    generate_authentication_options_for_user,
    generate_registration_options_for_user,
    verify_authentication,
    verify_registration,
)

MFA_SESSION_TTL_MINUTES = 10

logger = logging.getLogger("gula.security.mfa")


class MFAService:
    def __init__(self, db: Session):
        self._db = db

    def _challenge_cache(self):
        from .redis_client import cache

        if IS_PRODUCTION and not cache.is_shared:
            raise RuntimeError("MFA challenge store unavailable")
        return cache

    # ── TOTP ──

    def setup_totp(self, user_id: int, email: str, device_name: str = "Authenticator App") -> dict[str, Any]:
        self._deactivate_existing(user_id, "totp")
        secret = generate_totp_secret()
        uri = generate_totp_uri(secret, email)
        backup = generate_backup_codes()
        device = MFADevice(
            user_id=user_id, device_type="totp", device_name=device_name,
            secret=secret, is_active=True, is_primary=True,
            backup_codes=json.dumps(hash_backup_codes(backup)),
        )
        self._db.add(device)
        self._db.commit()
        return {"secret": secret, "uri": uri, "backup_codes": backup, "device_id": device.id}

    def verify_totp(self, user_id: int, token: str) -> bool:
        devices = self._db.query(MFADevice).filter(
            MFADevice.user_id == user_id,
            MFADevice.device_type == "totp",
            MFADevice.is_active.is_(True),
        ).with_for_update().all()
        for device in devices:
            if verify_totp(device.secret, token):
                device.last_used_at = datetime.now(UTC)
                self._db.commit()
                return True
            if device.backup_codes:
                codes = json.loads(device.backup_codes)
                matched = verify_backup_code(token, codes)
                if matched:
                    codes.remove(matched)
                    device.backup_codes = json.dumps(codes)
                    device.last_used_at = datetime.now(UTC)
                    self._db.commit()
                    return True
        return False

    # ── WebAuthn ──

    def begin_webauthn_registration(self, user_id: int, user_name: str, user_display_name: str) -> dict[str, Any]:
        existing = self._db.query(MFADevice).filter(
            MFADevice.user_id == user_id,
            MFADevice.device_type.in_(["webauthn", "fido2", "passkey"]),
            MFADevice.is_active.is_(True),
        ).all()
        existing_creds = [
            {"credential_id": json.loads(d.public_key)["credential_id"] if d.public_key else "", "transports": d.transports or []}
            for d in existing if d.public_key
        ]
        options = generate_registration_options_for_user(
            user_id=str(user_id), user_name=user_name,
            user_display_name=user_display_name,
            existing_credentials=existing_creds,
        )
        cache = self._challenge_cache()
        try:
            cache.set(f"webauthn:challenge:{user_id}", options["challenge"], ex=300)
        except Exception as exc:
            logger.error("WebAuthn registration challenge cache failed for user %s", user_id)
            raise RuntimeError("WebAuthn challenge store unavailable") from exc
        return options

    def complete_webauthn_registration(self, user_id: int, credential: dict[str, Any],
                                        device_name: str = "Security Key") -> MFADevice:
        cache = self._challenge_cache()
        challenge = ""
        try:
            challenge = cache.get_and_delete(f"webauthn:challenge:{user_id}") or ""
        except Exception as exc:
            logger.error("WebAuthn registration challenge read failed for user %s", user_id)
            raise RuntimeError("WebAuthn challenge store unavailable") from exc
        result = verify_registration(credential, challenge)
        device = MFADevice(
            user_id=user_id, device_type="webauthn",
            device_name=device_name, is_active=True, is_primary=not self._has_mfa(user_id),
            credential_id=result["credential_id"],
            public_key=json.dumps(result),
            sign_count=result["sign_count"],
            transports=json.dumps(result.get("transports", [])),
        )
        self._db.add(device)
        self._db.commit()
        return device

    def begin_webauthn_authentication(self, user_id: int) -> dict[str, Any]:
        devices = self._db.query(MFADevice).filter(
            MFADevice.user_id == user_id,
            MFADevice.device_type.in_(["webauthn", "fido2", "passkey"]),
            MFADevice.is_active.is_(True),
        ).all()
        creds = [
            {"credential_id": d.credential_id or "",
             "public_key": d.public_key or "",
             "transports": json.loads(d.transports) if d.transports else []}
            for d in devices if d.credential_id
        ]
        options = generate_authentication_options_for_user(creds)
        cache = self._challenge_cache()
        try:
            cache.set(f"webauthn:challenge:{user_id}", options["challenge"], ex=300)
        except Exception as exc:
            logger.error("WebAuthn authentication challenge cache failed for user %s", user_id)
            raise RuntimeError("WebAuthn challenge store unavailable") from exc
        return options

    def complete_webauthn_authentication(self, user_id: int, credential: dict[str, Any]) -> bool:
        cache = self._challenge_cache()
        challenge = ""
        try:
            challenge = cache.get_and_delete(f"webauthn:challenge:{user_id}") or ""
        except Exception as exc:
            logger.error("WebAuthn authentication challenge read failed for user %s", user_id)
            raise RuntimeError("WebAuthn challenge store unavailable") from exc
        device = self._db.query(MFADevice).filter(
            MFADevice.user_id == user_id,
            MFADevice.credential_id == credential.get("id"),
            MFADevice.is_active.is_(True),
        ).first()
        if not device:
            return False
        pk = json.loads(device.public_key) if device.public_key else {}
        result = verify_authentication(
            credential, challenge,
            credential_public_key=pk.get("public_key", ""),
            credential_current_sign_count=device.sign_count,
        )
        device.sign_count = result["new_sign_count"]
        device.last_used_at = datetime.now(UTC)
        self._db.commit()
        return True

    # ── MFA Session ──

    def create_mfa_session(self, user_id: int, method: str) -> str:
        token = secrets.token_urlsafe(32)
        session = MFASession(
            user_id=user_id, session_token=token, mfa_method=method,
            expires_at=datetime.now(UTC) + timedelta(minutes=MFA_SESSION_TTL_MINUTES),
        )
        self._db.add(session)
        self._db.commit()
        return token

    def verify_mfa_session(self, session_token: str) -> int | None:
        now = datetime.now(UTC)
        candidate = self._db.query(MFASession.user_id).filter(
            MFASession.session_token == session_token,
            MFASession.is_verified.is_(False),
            MFASession.expires_at > now,
        ).first()
        if not candidate:
            return None
        result = self._db.execute(
            update(MFASession)
            .where(
                MFASession.session_token == session_token,
                MFASession.is_verified.is_(False),
                MFASession.expires_at > now,
            )
            .values(is_verified=True),
        )
        if result.rowcount != 1:
            return None
        self._db.commit()
        return candidate[0]

    def get_user_devices(self, user_id: int) -> list[dict[str, Any]]:
        devices = self._db.query(MFADevice).filter(
            MFADevice.user_id == user_id,
        ).order_by(MFADevice.is_primary.desc(), MFADevice.created_at.desc()).all()
        return [
            {"id": d.id, "device_type": d.device_type, "device_name": d.device_name,
             "is_active": d.is_active, "is_primary": d.is_primary,
             "last_used_at": d.last_used_at.isoformat() if d.last_used_at else None,
             "created_at": d.created_at.isoformat() if d.created_at else ""}
            for d in devices
        ]

    def remove_device(self, user_id: int, device_id: int) -> bool:
        device = self._db.query(MFADevice).filter(
            MFADevice.id == device_id, MFADevice.user_id == user_id,
        ).first()
        if not device:
            return False
        self._db.delete(device)
        self._db.commit()
        return True

    def has_mfa_enabled(self, user_id: int) -> bool:
        return self._has_mfa(user_id)

    def _has_mfa(self, user_id: int) -> bool:
        return self._db.query(MFADevice).filter(
            MFADevice.user_id == user_id,
            MFADevice.is_active.is_(True),
        ).first() is not None

    def _deactivate_existing(self, user_id: int, device_type: str) -> None:
        self._db.query(MFADevice).filter(
            MFADevice.user_id == user_id, MFADevice.device_type == device_type,
        ).update({"is_active": False})
