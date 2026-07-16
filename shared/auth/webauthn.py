from __future__ import annotations

import json
from typing import Any

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    RegistrationCredential,
    AuthenticationCredential,
)
from webauthn.helpers import bytes_to_base64url


RP_ID = "gula.health"
RP_NAME = "GULA Health Platform"
RP_ORIGIN = "https://app.gula.health"


def generate_registration_options_for_user(
    user_id: str,
    user_name: str,
    user_display_name: str,
    existing_credentials: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    existing = []
    if existing_credentials:
        existing = [
            {"id": c["credential_id"], "type": "public-key"}
            for c in existing_credentials
        ]
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=user_id.encode(),
        user_name=user_name,
        user_display_name=user_display_name,
        exclude_credentials=existing,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    return json.loads(options.model_dump_json())


def verify_registration(
    credential: dict[str, Any],
    expected_challenge: str,
    expected_origin: str = RP_ORIGIN,
    expected_rp_id: str = RP_ID,
) -> dict[str, Any]:
    verification = verify_registration_response(
        credential=RegistrationCredential.model_validate(credential),
        expected_challenge=expected_challenge.encode(),
        expected_origin=expected_origin,
        expected_rp_id=expected_rp_id,
    )
    return {
        "credential_id": bytes_to_base64url(verification.credential_id),
        "public_key": bytes_to_base64url(verification.credential_public_key),
        "sign_count": verification.sign_count,
        "transports": [t.value for t in verification.transports] if verification.transports else [],
    }


def generate_authentication_options_for_user(
    credentials: list[dict[str, Any]],
    user_verification: str = "preferred",
) -> dict[str, Any]:
    allow_credentials = [
        {"id": c["credential_id"], "type": "public-key", "transports": c.get("transports", [])}
        for c in credentials
    ]
    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement(user_verification),
    )
    return json.loads(options.model_dump_json())


def verify_authentication(
    credential: dict[str, Any],
    expected_challenge: str,
    expected_origin: str = RP_ORIGIN,
    expected_rp_id: str = RP_ID,
    credential_public_key: str = "",
    credential_current_sign_count: int = 0,
) -> dict[str, Any]:
    verification = verify_authentication_response(
        credential=AuthenticationCredential.model_validate(credential),
        expected_challenge=expected_challenge.encode(),
        expected_origin=expected_origin,
        expected_rp_id=expected_rp_id,
        credential_public_key=credential_public_key.encode() if credential_public_key else b"",
        credential_current_sign_count=credential_current_sign_count,
    )
    return {
        "credential_id": bytes_to_base64url(verification.credential_id),
        "new_sign_count": verification.new_sign_count,
    }
