from __future__ import annotations

import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
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
WEBAUTHN_CHALLENGE_TTL_SECONDS = 300

logger = logging.getLogger("gula.security.mfa")


class WebAuthnError(ValueError):
    """A WebAuthn ceremony failed or its challenge was invalid/consumed.

    Fail closed: callers must treat this as an authentication failure and must
    not fall back to accepting the credential. Routes translate it to a 4xx.
    """


class MFAService:
    def __init__(self, db: Session):
        self._db = db

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
        ).all()
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

    @staticmethod
    def _challenge_key(user_id: int, purpose: str) -> str:
        """Namespaced key: registration and authentication never share state."""
        if purpose not in {"reg", "auth"}:
            raise ValueError("Invalid WebAuthn challenge namespace")
        return f"webauthn:challenge:{purpose}:{user_id}"

    @staticmethod
    def _store_challenge(user_id: int, purpose: str, challenge: str) -> None:
        """Persist a challenge using the fail-closed shared security store.

        Store errors are *not* swallowed: if the challenge cannot be written,
        the ceremony cannot be completed and must not appear to succeed.
        """
        from .redis_client import security_store

        store = security_store("WebAuthn challenge write")
        key = MFAService._challenge_key(user_id, purpose)
        store.set(key, challenge, ex=WEBAUTHN_CHALLENGE_TTL_SECONDS)
        # A new ceremony invalidates any prior single-use claim for this user.
        store.delete(f"{key}:consumed")

    @staticmethod
    def _consume_challenge(user_id: int, purpose: str) -> str:
        """Atomically claim and return a challenge, or fail closed.

        Missing/expired challenges and replay attempts raise
        :class:`WebAuthnError`. The ``set_if_absent`` claim makes consumption
        atomic across workers, so a challenge cannot be verified twice.
        """
        from .redis_client import security_store

        store = security_store("WebAuthn challenge read")
        key = MFAService._challenge_key(user_id, purpose)
        challenge = store.get(key)
        if not challenge:
            raise WebAuthnError("WebAuthn challenge is missing or expired; restart the ceremony")
        if not store.set_if_absent(
            f"{key}:consumed", "1", ex=WEBAUTHN_CHALLENGE_TTL_SECONDS,
        ):
            raise WebAuthnError("WebAuthn challenge has already been used")
        return challenge

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
        self._store_challenge(user_id, "reg", options["challenge"])
        return options

    def complete_webauthn_registration(self, user_id: int, credential: dict[str, Any],
                                        device_name: str = "Security Key") -> MFADevice:
        challenge = self._consume_challenge(user_id, "reg")
        try:
            result = verify_registration(credential, challenge)
        except WebAuthnError:
            raise
        except Exception as exc:  # webauthn raises several Invalid* exception types
            raise WebAuthnError("WebAuthn registration verification failed") from exc
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
        self._store_challenge(user_id, "auth", options["challenge"])
        return options

    def complete_webauthn_authentication(self, user_id: int, credential: dict[str, Any]) -> bool:
        device = self._db.query(MFADevice).filter(
            MFADevice.user_id == user_id,
            MFADevice.credential_id == credential.get("id"),
            MFADevice.is_active.is_(True),
        ).first()
        if not device:
            return False
        challenge = self._consume_challenge(user_id, "auth")
        pk = json.loads(device.public_key) if device.public_key else {}
        try:
            result = verify_authentication(
                credential, challenge,
                credential_public_key=pk.get("public_key", ""),
                credential_current_sign_count=device.sign_count,
            )
        except WebAuthnError:
            raise
        except Exception as exc:  # webauthn raises several Invalid* exception types
            raise WebAuthnError("WebAuthn authentication verification failed") from exc
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
        session = self._db.query(MFASession).filter(
            MFASession.session_token == session_token,
            MFASession.is_verified.is_(False),
            MFASession.expires_at > datetime.now(UTC),
        ).first()
        if session:
            session.is_verified = True
            self._db.commit()
            return session.user_id
        return None

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
