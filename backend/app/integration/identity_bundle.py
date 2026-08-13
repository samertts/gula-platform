from __future__ import annotations

import base64
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field

from app.contracts.integration import IntegrationEventEnvelope


class SignedIdentityBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(min_length=1, max_length=120)
    schema_version: int = Field(ge=1)
    source_service: str = Field(pattern=r"^identity-credential$")
    tenant_id: str = Field(min_length=1, max_length=120)
    subject_id: str = Field(min_length=1, max_length=160)
    credential_id: str = Field(min_length=1, max_length=160)
    credential_version: int = Field(ge=1)
    credential_state: str = Field(min_length=1, max_length=40)
    actor_id: str = Field(min_length=1, max_length=160)
    issued_at: str = Field(min_length=1, max_length=80)
    idempotency_key: str = Field(min_length=1, max_length=200)
    claims: dict[str, str]
    signature: str = Field(min_length=1)
    key_id: str = Field(min_length=1, max_length=120)


def _canonical_unsigned(bundle: SignedIdentityBundle) -> bytes:
    data = bundle.model_dump(mode="json", exclude={"signature"})
    import json

    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_identity_bundle(bundle_data: dict[str, Any], public_key_pem: bytes) -> IntegrationEventEnvelope:
    bundle = SignedIdentityBundle.model_validate(bundle_data)
    public_key = serialization.load_pem_public_key(public_key_pem)
    if not isinstance(public_key, Ed25519PublicKey):
        raise ValueError("identity bundle requires an Ed25519 public key")
    try:
        public_key.verify(
            base64.urlsafe_b64decode(bundle.signature.encode("ascii")),
            _canonical_unsigned(bundle),
        )
    except Exception as exc:
        raise ValueError("identity bundle signature verification failed") from exc

    issued_at = datetime.fromisoformat(bundle.issued_at.replace("Z", "+00:00"))
    if issued_at.tzinfo is None:
        raise ValueError("identity bundle issued_at must be timezone-aware")
    now = datetime.now(UTC)
    max_age = int(os.getenv("GULA_IDENTITY_BUNDLE_MAX_AGE_SECONDS", "86400"))
    if issued_at > now + timedelta(minutes=5):
        raise ValueError("identity bundle issued_at is in the future")
    if issued_at < now - timedelta(seconds=max_age):
        raise ValueError("identity bundle has expired")

    return IntegrationEventEnvelope.model_validate(
        {
            "event_id": bundle.bundle_id,
            "event_type": "identity.subject.mapped",
            "schema_version": bundle.schema_version,
            "source_service": bundle.source_service,
            "tenant_id": bundle.tenant_id,
            "occurred_at": bundle.issued_at,
            "actor_id": bundle.actor_id,
            "entity_id": bundle.subject_id,
            "correlation_id": bundle.credential_id,
            "idempotency_key": bundle.idempotency_key,
            "payload": {
                "subject_id": bundle.subject_id,
                "credential_id": bundle.credential_id,
                "credential_version": bundle.credential_version,
                "credential_state": bundle.credential_state,
                "claims": bundle.claims,
                "key_id": bundle.key_id,
            },
        }
    )
