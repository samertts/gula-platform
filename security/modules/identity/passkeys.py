from __future__ import annotations

import json
import logging
import secrets
import threading
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Any

from webauthn import generate_authentication_options, generate_registration_options
from webauthn import options as webauthn_options
from webauthn import verify_authentication_response, verify_registration_response
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    CredentialCreationOptions,
    CredentialRequestOptions,
    PublicKeyCredentialCreationOptions,
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialRequestOptions,
    PublicKeyCredentialType,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

logger = logging.getLogger("gula.security.modules.identity.passkeys")

_RP_ID = "gula-platform.org"
_RP_NAME = "GULA Platform"
_CHALLENGE_TTL = 300


class PasskeyManager:
    def __init__(self, rp_id: str = _RP_ID, rp_name: str = _RP_NAME, redis_client: Any = None) -> None:
        self._rp_id = rp_id
        self._rp_name = rp_name
        self._redis = redis_client
        self._lock = threading.Lock()
        self._credentials: dict[str, list[dict[str, Any]]] = {}
        self._challenges: dict[str, dict[str, Any]] = {}
        self._backend_webauthn: Any = None

        try:
            from backend.app.security.mfa_service import MFAService
            self._backend_service_cls = MFAService
        except ImportError:
            self._backend_service_cls = None

    def begin_registration(
        self,
        user_id: str,
        user_name: str,
        user_display_name: str = "",
        resident_key: bool = False,
        platform_authenticator: bool = False,
    ) -> dict[str, Any]:
        existing_credentials = self._credentials.get(user_id, [])
        exclude_credentials = [
            PublicKeyCredentialDescriptor(
                type=PublicKeyCredentialType.PUBLIC_KEY,
                id=urlsafe_b64decode(cred["credential_id"] + "==") if cred.get("credential_id") else b"",
            )
            for cred in existing_credentials
            if cred.get("credential_id")
        ]

        authenticator_selection = AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED if resident_key else ResidentKeyRequirement.DISCOURAGED,
            authenticator_attachment=AuthenticatorAttachment.PLATFORM if platform_authenticator else AuthenticatorAttachment.CROSS_PLATFORM,
            user_verification=UserVerificationRequirement.REQUIRED,
        )

        options = generate_registration_options(
            rp_id=self._rp_id,
            rp_name=self._rp_name,
            user_id=user_id.encode("utf-8"),
            user_name=user_name,
            user_display_name=user_display_name or user_name,
            exclude_credentials=exclude_credentials,
            authenticator_selection=authenticator_selection,
        )

        challenge_b64 = urlsafe_b64encode(options.challenge).rstrip(b"=").decode()
        self._store_challenge(user_id, challenge_b64)

        return {
            "publicKey": {
                "rp": {"id": self._rp_id, "name": self._rp_name},
                "user": {
                    "id": urlsafe_b64encode(user_id.encode()).rstrip(b"=").decode(),
                    "name": user_name,
                    "displayName": user_display_name or user_name,
                },
                "challenge": challenge_b64,
                "pubKeyCredParams": [{"type": "public-key", "alg": -7}],
                "timeout": 60000,
                "excludeCredentials": [
                    {"id": urlsafe_b64encode(cred["credential_id"].encode()).rstrip(b"=").decode() if cred.get("credential_id") else "",
                     "type": "public-key"}
                    for cred in existing_credentials
                ],
                "authenticatorSelection": {
                    "residentKey": "required" if resident_key else "discouraged",
                    "authenticatorAttachment": "platform" if platform_authenticator else "cross-platform",
                    "userVerification": "required",
                },
                "attestation": "none",
            }
        }

    def complete_registration(
        self,
        user_id: str,
        credential: dict[str, Any],
        device_name: str = "Passkey",
    ) -> dict[str, Any]:
        challenge = self._get_challenge(user_id)
        if challenge is None:
            raise ValueError("No registration challenge found for user")

        try:
            credential_bytes = json.dumps(credential).encode()

            class FakeResponse:
                def __init__(self, data: dict[str, Any]):
                    self.id = data.get("id", "")
                    self.raw_id = urlsafe_b64decode(data.get("rawId", "") + "==") if data.get("rawId") else b""
                    self.type = data.get("type", "public-key")
                    response = data.get("response", {})
                    self.response = type("resp", (), {})()
                    self.response.client_data_json = urlsafe_b64decode(response.get("clientDataJSON", "") + "==") if response.get("clientDataJSON") else b""
                    self.response.attestation_object = urlsafe_b64decode(response.get("attestationObject", "") + "==") if response.get("attestationObject") else b""
                    self.response.transports = response.get("transports", [])
                    self.client_extension_results = data.get("clientExtensionResults", {})
                    authenticator_attachment = data.get("authenticatorAttachment")
                    self.authenticator_attachment = authenticator_attachment

            fake = FakeResponse(credential)
            verification = verify_registration_response(
                credential=fake,
                expected_challenge=urlsafe_b64decode(challenge + "=="),
                expected_rp_id=self._rp_id,
                expected_origin=f"https://{self._rp_id}",
            )
        except Exception as exc:
            logger.error("WebAuthn registration verification failed: %s", exc)
            raise ValueError(f"Credential verification failed: {exc}") from exc

        cred_data = {
            "credential_id": urlsafe_b64encode(verification.credential_id).rstrip(b"=").decode(),
            "public_key": urlsafe_b64encode(verification.credential_public_key).rstrip(b"=").decode(),
            "sign_count": verification.sign_count,
            "device_name": device_name,
            "transports": credential.get("response", {}).get("transports", []),
            "created_at": time.time(),
            "is_active": True,
        }

        with self._lock:
            if user_id not in self._credentials:
                self._credentials[user_id] = []
            self._credentials[user_id].append(cred_data)

        self._delete_challenge(user_id)

        logger.info("Passkey registered for user %s: %s", user_id, cred_data["credential_id"][:16])
        return cred_data

    def begin_authentication(self, user_id: str | None = None) -> dict[str, Any]:
        if user_id:
            user_creds = self._credentials.get(user_id, [])
            allow_credentials = [
                PublicKeyCredentialDescriptor(
                    type=PublicKeyCredentialType.PUBLIC_KEY,
                    id=urlsafe_b64decode(cred["credential_id"] + "=="),
                    transports=cred.get("transports", []),
                )
                for cred in user_creds
                if cred.get("is_active", True) and cred.get("credential_id")
            ]
        else:
            allow_credentials = []

        options = generate_authentication_options(
            rp_id=self._rp_id,
            allow_credentials=allow_credentials,
            user_verification=UserVerificationRequirement.REQUIRED,
        )

        challenge_b64 = urlsafe_b64encode(options.challenge).rstrip(b"=").decode()
        uid = user_id or "__any__"
        self._store_challenge(uid, challenge_b64)

        return {
            "publicKey": {
                "challenge": challenge_b64,
                "timeout": 60000,
                "rpId": self._rp_id,
                "allowCredentials": [
                    {"id": urlsafe_b64encode(cred["credential_id"].encode()).rstrip(b"=").decode(),
                     "type": "public-key",
                     "transports": cred.get("transports", [])}
                    for cred in user_creds if cred.get("is_active", True) and cred.get("credential_id")
                ]
                if user_id else [],
                "userVerification": "required",
            }
        }

    def complete_authentication(self, credential: dict[str, Any]) -> dict[str, Any]:
        cred_id = credential.get("id", "")
        user_id = self._find_user_by_credential_id(cred_id)
        if user_id is None:
            raise ValueError("Credential not found")

        challenge = self._get_challenge(user_id)
        if challenge is None:
            challenge = self._get_challenge("__any__")
        if challenge is None:
            raise ValueError("No authentication challenge found")

        user_cred = self._get_credential(user_id, cred_id)
        if user_cred is None:
            raise ValueError("Credential not found for user")

        try:
            class FakeAssertionResponse:
                def __init__(self, data: dict[str, Any]):
                    self.id = data.get("id", "")
                    raw_id = data.get("rawId", data.get("id", ""))
                    self.raw_id = urlsafe_b64decode(raw_id + "==") if raw_id else b""
                    self.type = data.get("type", "public-key")
                    response = data.get("response", {})
                    self.response = type("resp", (), {})()
                    self.response.client_data_json = urlsafe_b64decode(response.get("clientDataJSON", "") + "==") if response.get("clientDataJSON") else b""
                    self.response.authenticator_data = urlsafe_b64decode(response.get("authenticatorData", "") + "==") if response.get("authenticatorData") else b""
                    self.response.signature = urlsafe_b64decode(response.get("signature", "") + "==") if response.get("signature") else b""
                    self.response.user_handle = urlsafe_b64decode(response.get("userHandle", "") + "==") if response.get("userHandle") else None
                    self.client_extension_results = data.get("clientExtensionResults", {})

            public_key_bytes = urlsafe_b64decode(user_cred["public_key"] + "==")
            expected_challenge = urlsafe_b64decode(challenge + "==")

            fake = FakeAssertionResponse(credential)
            verification = verify_authentication_response(
                credential=fake,
                expected_challenge=expected_challenge,
                expected_rp_id=self._rp_id,
                expected_origin=f"https://{self._rp_id}",
                credential_public_key=public_key_bytes,
                credential_current_sign_count=user_cred["sign_count"],
                require_user_verification=True,
            )
        except Exception as exc:
            logger.error("WebAuthn authentication verification failed: %s", exc)
            raise ValueError(f"Authentication verification failed: {exc}") from exc

        user_cred["sign_count"] = verification.new_sign_count
        user_cred["last_used_at"] = time.time()

        self._delete_challenge(user_id)
        self._delete_challenge("__any__")

        return {"user_id": user_id, "credential_id": cred_id, "sign_count": verification.new_sign_count}

    def get_credentials(self, user_id: str) -> list[dict[str, Any]]:
        return [
            {
                "credential_id": c["credential_id"],
                "device_name": c.get("device_name", ""),
                "transports": c.get("transports", []),
                "created_at": c.get("created_at", 0),
                "last_used_at": c.get("last_used_at"),
                "is_active": c.get("is_active", True),
            }
            for c in self._credentials.get(user_id, [])
        ]

    def delete_credential(self, user_id: str, credential_id: str) -> bool:
        with self._lock:
            creds = self._credentials.get(user_id, [])
            before = len(creds)
            self._credentials[user_id] = [c for c in creds if c.get("credential_id") != credential_id]
        return len(self._credentials.get(user_id, [])) < before

    def _find_user_by_credential_id(self, credential_id: str) -> str | None:
        for uid, creds in self._credentials.items():
            for cred in creds:
                if cred.get("credential_id") == credential_id:
                    return uid
        return None

    def _get_credential(self, user_id: str, credential_id: str) -> dict[str, Any] | None:
        for cred in self._credentials.get(user_id, []):
            if cred.get("credential_id") == credential_id:
                return cred
        return None

    def _store_challenge(self, user_id: str, challenge: str) -> None:
        expiry = time.time() + _CHALLENGE_TTL
        if self._redis is not None:
            try:
                self._redis.set(f"webauthn:challenge:{user_id}", challenge, ex=_CHALLENGE_TTL)
                return
            except Exception:
                pass
        with self._lock:
            self._challenges[user_id] = {"challenge": challenge, "expires_at": expiry}

    def _get_challenge(self, user_id: str) -> str | None:
        if self._redis is not None:
            try:
                return self._redis.get(f"webauthn:challenge:{user_id}")
            except Exception:
                pass
        with self._lock:
            entry = self._challenges.get(user_id)
            if entry is None:
                return None
            if time.time() > entry["expires_at"]:
                self._challenges.pop(user_id, None)
                return None
            return entry["challenge"]

    def _delete_challenge(self, user_id: str) -> None:
        if self._redis is not None:
            try:
                self._redis.delete(f"webauthn:challenge:{user_id}")
                return
            except Exception:
                pass
        with self._lock:
            self._challenges.pop(user_id, None)
