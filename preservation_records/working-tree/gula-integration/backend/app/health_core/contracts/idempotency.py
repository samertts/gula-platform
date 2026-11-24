"""Idempotency contract for retryable synthetic write operations.

Naming and semantics align with the national contracts (``Idempotency-Key``
header, per-tenant scope, 24 h TTL, replay of the stored response) while using
only opaque ``SYN-`` keys. Conflict uses the shared ``DUPLICATE_ENTITY`` code;
nothing here stores keys, enforces TTL at runtime, or exposes an endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.health_core.common import (
    DuplicateEntityError,
    HealthCoreError,
    is_synthetic_id,
    new_synthetic_id,
    reject_national_identifier,
)

IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_TTL_SECONDS = 86_400
IDEMPOTENCY_KEY_PREFIX = "IDK"
IDEMPOTENCY_CONFLICT_CODE = DuplicateEntityError.code
IDEMPOTENCY_CONFLICT_STATUS = DuplicateEntityError.status_code


class ReplaySemantics(StrEnum):
    """Documented outcomes when a key is presented again."""

    REPLAY_STORED_RESPONSE = "replay_stored_response"
    CREATE_NEW = "create_new"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class IdempotencyPolicy:
    """A documented idempotency policy from the national platform.

    Documentation only. The synthetic in-memory services use opaque ``SYN-``
    keys through :func:`validate_idempotency_key`; no HTTP header parsing, TTL
    store, ``If-Match`` enforcement or status-code emission exists here.
    """

    name: str
    key_header_required: bool
    max_key_length: int
    if_match_header: str | None
    missing_if_match_status: int | None
    stale_version_status: int | None
    source_contract: str


#: Two policies are in force. General writes make the key optional (max 255);
#: clinical commands require it (max 128) and additionally require ``If-Match``
#: with 428 when absent and 409 on a stale version.
IDEMPOTENCY_POLICIES: tuple[IdempotencyPolicy, ...] = (
    IdempotencyPolicy(
        name="general",
        key_header_required=False,
        max_key_length=255,
        if_match_header=None,
        missing_if_match_status=None,
        stale_version_status=None,
        source_contract="backend/app/core/idempotency.py",
    ),
    IdempotencyPolicy(
        name="clinical",
        key_header_required=True,
        max_key_length=128,
        if_match_header="If-Match",
        missing_if_match_status=428,
        stale_version_status=409,
        source_contract="backend/app/clinical/command_guard.py",
    ),
)


#: The documented replay contract. ``CONFLICT`` maps to ``DUPLICATE_ENTITY``.
IDEMPOTENCY_SEMANTICS: dict[ReplaySemantics, str] = {
    ReplaySemantics.CREATE_NEW: "No stored entry for (tenant, key) inside the TTL: process once.",
    ReplaySemantics.REPLAY_STORED_RESPONSE: (
        "Same (tenant, key, operation, payload) inside the TTL: return the stored response "
        "without re-applying the write."
    ),
    ReplaySemantics.CONFLICT: (
        "Same (tenant, key) reused with a different operation or payload inside the TTL: "
        f"reject with {IDEMPOTENCY_CONFLICT_CODE} ({IDEMPOTENCY_CONFLICT_STATUS})."
    ),
}


def new_idempotency_key() -> str:
    """Generate a fresh, opaque ``SYN-`` prefixed idempotency key."""
    return new_synthetic_id(IDEMPOTENCY_KEY_PREFIX)


def validate_idempotency_key(key: object) -> str:
    """Validate a key shape; fail closed for empty/real-looking/non-SYN values."""
    if not isinstance(key, str):
        raise ValueError("idempotency key must be a string")
    try:
        reject_national_identifier(key, field="idempotency_key")
    except HealthCoreError as exc:
        raise ValueError(str(exc)) from exc
    if not is_synthetic_id(key):
        raise ValueError("idempotency key must be a SYN- prefixed synthetic reference")
    return key


@dataclass(frozen=True, slots=True)
class IdempotencyScope:
    """The identity of a replay record: a key is never global across tenants."""

    tenant_id: str
    idempotency_key: str
    operation: str

    def __post_init__(self) -> None:
        validate_idempotency_key(self.idempotency_key)
        validate_idempotency_key(self.tenant_id)
        if not self.operation:
            raise ValueError("idempotency operation must not be empty")
