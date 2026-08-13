import base64
import json
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.integration.identity_bundle import verify_identity_bundle


def _keys():
    private = Ed25519PrivateKey.generate()
    private_pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private, private_pem, public_pem


def _bundle(private):
    unsigned = {
        "bundle_id": "bundle-1",
        "schema_version": 1,
        "source_service": "identity-credential",
        "tenant_id": "tenant-1",
        "subject_id": "subject-1",
        "credential_id": "credential-1",
        "credential_version": 1,
        "credential_state": "active",
        "actor_id": "operator-1",
        "issued_at": datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat(),
        "idempotency_key": "identity-key-1",
        "claims": {"role": "laboratory_staff"},
        "key_id": "identity-key-1",
    }
    canonical = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return {**unsigned, "signature": base64.urlsafe_b64encode(private.sign(canonical)).decode("ascii")}


def test_signed_identity_bundle_becomes_pending_mapping_event():
    private, _, public_pem = _keys()
    envelope = verify_identity_bundle(_bundle(private), public_pem)
    assert envelope.event_type == "identity.subject.mapped"
    assert envelope.entity_id == "subject-1"
    assert envelope.payload["credential_state"] == "active"


def test_tampered_identity_bundle_is_rejected():
    private, _, public_pem = _keys()
    bundle = _bundle(private)
    bundle["payload_injection"] = "reject me"
    try:
        verify_identity_bundle(bundle, public_pem)
    except ValueError:
        pass
    else:
        raise AssertionError("tampered bundle must be rejected")
