"""Self-contained, file-backed audit-anchor engine (synthetic data only).

This local hash chain is an engineering building block. It is NOT an externally
anchored or independently notarized audit log; owner-gated D-020 remains blocked.

No real credentials are used: keys are deterministic synthetic HMAC keys and
tenant/actor identifiers are synthetic.
"""

from app.health_core.audit_anchor.chain import (
    REDACTED,
    append,
    record_authorization_failure,
    redact,
)
from app.health_core.audit_anchor.keys import KeyProvider, RotatingKeyProvider
from app.health_core.audit_anchor.store import (
    AuditAnchorStore,
    AuditChainError,
    AuditStoreError,
    open_store,
)
from app.health_core.audit_anchor.verification import (
    GENESIS_HASH,
    VerificationReport,
    canonical_json,
    payload_hash,
    record_body,
    record_hash,
    verify_chain,
)

__all__ = [
    "GENESIS_HASH",
    "REDACTED",
    "AuditAnchorStore",
    "AuditChainError",
    "AuditStoreError",
    "KeyProvider",
    "RotatingKeyProvider",
    "VerificationReport",
    "append",
    "canonical_json",
    "open_store",
    "payload_hash",
    "record_authorization_failure",
    "record_body",
    "record_hash",
    "redact",
    "verify_chain",
]
