"""Crypto helpers — keypair generation and (optional) task signature checks.

The control plane HMAC-signs task payloads with EDGE_TASK_SIGNING_KEY (server
side). The agent does NOT have that secret, so it can't independently verify
task signatures cryptographically. What the agent CAN do:

  - Generate its long-lived RSA keypair on first registration
  - Discard tasks whose `kind` is not in the locally-pinned ALLOWED_KINDS
  - Reject tasks whose payload exceeds a hard ceiling

A future hardening step is to ship a public verification key with the agent so
HMAC becomes signed JWTs. Tracked under Section 6 — Device Attestation.
"""
from __future__ import annotations

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


# Mirrored from backend.app.edge.config.ALLOWED_TASK_KINDS so that even if the
# server somehow allowlists a new kind, the agent won't run it without an
# explicit agent update.
ALLOWED_KINDS: frozenset[str] = frozenset({
    "ai.summarize_report", "ai.translate", "ai.transcribe", "ai.classify",
    "ai.extract_lab_values", "ai.embed",
    "image.thumbnail", "pdf.extract_text",
    "agent.self_update", "agent.warmup_model", "agent.gc",
    "diag.ping", "diag.benchmark",
})

MAX_PAYLOAD_BYTES: int = 256 * 1024


def generate_keypair() -> tuple[str, str]:
    """Return (private_key_pem, public_key_pem). 2048-bit RSA."""
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem
