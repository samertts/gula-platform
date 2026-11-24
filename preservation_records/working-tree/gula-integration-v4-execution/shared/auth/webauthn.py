from __future__ import annotations

import base64
import dataclasses
import json
import os
from enum import Enum
from typing import Any, cast
from urllib.parse import urlparse

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    AuthenticatorTransport,
    PublicKeyCredentialDescriptor,
    UserVerificationRequirement,
)

# Relying-party configuration is deployment-specific (localhost / staging /
# national domains). P0-C: hardcoded production values broke every other
# environment, so these are overridable by environment variables. No secret
# material is involved.
RP_ID = os.getenv("WEBAUTHN_RP_ID", "gula.health")
RP_NAME = os.getenv("WEBAUTHN_RP_NAME", "GULA Health Platform")
RP_ORIGIN = os.getenv("WEBAUTHN_ORIGIN", "https://app.gula.health")


def validate_relying_party(rp_id: str, origin: str) -> None:
    """Reject configurations that cannot produce a valid WebAuthn ceremony."""
    if not rp_id or any(ch in rp_id for ch in " /:@\\"):
        raise ValueError("Invalid WebAuthn RP_ID")
    parsed = urlparse(origin)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Invalid WebAuthn origin")
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1"}:
        raise ValueError("WebAuthn origin must use HTTPS outside localhost")
    host = parsed.hostname
    if host != rp_id and not host.endswith("." + rp_id):
        raise ValueError("WebAuthn origin host must match RP_ID")


def _json_safe(value: Any) -> Any:
    """Make WebAuthn option objects JSON-safe without losing byte fidelity.

    WebAuthn options contain ``bytes`` (challenge, user id, credential ids) and
    string Enums. ``json.dumps(..., default=str)`` serialized bytes as their
    Python repr (``"b'...'"``), which is not a valid base64url challenge and
    caused verification to decode the wrong value. Every byte field is encoded
    as base64url here — the format browsers and the library expect.
    """
    if isinstance(value, (bytes, bytearray)):
        return bytes_to_base64url(bytes(value))
    if isinstance(value, Enum):
        return value.value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_safe(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _serialize_options(options: Any) -> dict[str, Any]:
    """Serialize options to a JSON-safe dict with a base64url challenge."""
    return cast("dict[str, Any]", json.loads(json.dumps(_json_safe(options))))


def _b64url_decode(value: str) -> bytes:
    """Decode a base64url string strictly into bytes."""
    if not isinstance(value, str) or not value:
        raise ValueError("Missing WebAuthn challenge")
    padding = "=" * (-len(value) % 4)
    try:
        decoded = base64.urlsafe_b64decode(value + padding)
    except Exception as exc:  # invalid client input — fail closed
        raise ValueError("Invalid WebAuthn challenge encoding") from exc
    if not decoded:
        raise ValueError("Empty WebAuthn challenge")
    return decoded


def _challenge_bytes(expected_challenge: str | bytes) -> bytes:
    """Accept our serialized base64url challenge (or raw bytes) for verify."""
    if isinstance(expected_challenge, (bytes, bytearray)):
        raw = bytes(expected_challenge)
        if not raw:
            raise ValueError("Empty WebAuthn challenge")
        return raw
    return _b64url_decode(expected_challenge)


def generate_registration_options_for_user(
    user_id: str,
    user_name: str,
    user_display_name: str,
    existing_credentials: list[dict[str, Any]] | None = None,
    rp_id: str | None = None,
    origin: str | None = None,
) -> dict[str, Any]:
    rp_id = rp_id or RP_ID
    origin = origin or RP_ORIGIN
    validate_relying_party(rp_id, origin)

    existing: list[PublicKeyCredentialDescriptor] = []
    if existing_credentials:
        existing = [
            PublicKeyCredentialDescriptor(id=_b64url_decode(c["credential_id"]))
            for c in existing_credentials
            if c.get("credential_id")
        ]
    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=RP_NAME,
        user_id=user_id.encode(),
        user_name=user_name,
        user_display_name=user_display_name,
        exclude_credentials=existing,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    return _serialize_options(options)


def verify_registration(
    credential: dict[str, Any],
    expected_challenge: str | bytes,
    expected_origin: str | None = None,
    expected_rp_id: str | None = None,
) -> dict[str, Any]:
    rp_id = expected_rp_id or RP_ID
    origin = expected_origin or RP_ORIGIN
    validate_relying_party(rp_id, origin)
    verification = verify_registration_response(
        credential=credential,  # dict is accepted by webauthn 3.x
        expected_challenge=_challenge_bytes(expected_challenge),
        expected_origin=origin,
        expected_rp_id=rp_id,
    )
    return {
        "credential_id": bytes_to_base64url(verification.credential_id),
        "public_key": bytes_to_base64url(verification.credential_public_key),
        "sign_count": verification.sign_count,
        # webauthn 3.x VerifiedRegistration has no `transports` field.
        "transports": [
            t.value if isinstance(t, AuthenticatorTransport) else str(t)
            for t in (getattr(verification, "transports", None) or [])
        ],
    }


def generate_authentication_options_for_user(
    credentials: list[dict[str, Any]],
    user_verification: str = "preferred",
    rp_id: str | None = None,
    origin: str | None = None,
) -> dict[str, Any]:
    rp_id = rp_id or RP_ID
    origin = origin or RP_ORIGIN
    validate_relying_party(rp_id, origin)

    allow_credentials: list[PublicKeyCredentialDescriptor] = []
    for c in credentials:
        credential_id = c.get("credential_id")
        if not credential_id:
            continue
        raw_id = (
            credential_id if isinstance(credential_id, bytes)
            else _b64url_decode(credential_id)
        )
        transports: list[AuthenticatorTransport] = []
        for value in c.get("transports", []) or []:
            try:
                transports.append(AuthenticatorTransport(value))
            except ValueError:
                continue  # ignore unknown transport hints; fail closed on verification
        allow_credentials.append(
            PublicKeyCredentialDescriptor(id=raw_id, transports=transports or None),
        )
    options = generate_authentication_options(
        rp_id=rp_id,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement(user_verification),
    )
    return _serialize_options(options)


def verify_authentication(
    credential: dict[str, Any],
    expected_challenge: str | bytes,
    expected_origin: str | None = None,
    expected_rp_id: str | None = None,
    credential_public_key: str = "",
    credential_current_sign_count: int = 0,
) -> dict[str, Any]:
    rp_id = expected_rp_id or RP_ID
    origin = expected_origin or RP_ORIGIN
    validate_relying_party(rp_id, origin)
    verification = verify_authentication_response(
        credential=credential,  # dict is accepted by webauthn 3.x
        expected_challenge=_challenge_bytes(expected_challenge),
        expected_origin=origin,
        expected_rp_id=rp_id,
        credential_public_key=_b64url_decode(credential_public_key) if credential_public_key else b"",
        credential_current_sign_count=credential_current_sign_count,
    )
    return {
        "credential_id": bytes_to_base64url(verification.credential_id),
        "new_sign_count": verification.new_sign_count,
    }
