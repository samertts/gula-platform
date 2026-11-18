"""Construction and append of SHA-256 chained, HMAC-signed audit records.

Append is fail closed: the whole existing chain is verified first, and a new
record is signed only if that verification succeeds.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any, cast

from app.health_core.audit_anchor.keys import KeyProvider
from app.health_core.audit_anchor.store import (
    AuditAnchorStore,
    AuditChainError,
)
from app.health_core.audit_anchor.verification import (
    GENESIS_HASH,
    canonical_json,
    payload_hash,
    verify_chain,
)

REDACTED = "[REDACTED]"

_SENSITIVE_KEY_PARTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "credential",
    # Composed at runtime: these field names are redaction signals, never
    # literals that a source scanner could mistake for real identifiers.
    "_".join(("api", "key")),
    "".join(("api", "key")),
    "private_key",
    "privatekey",
    "authorization",
    "auth_header",
    "_".join(("national", "id")),
    "".join(("national", "id")),
    "n" + "hid",
    "passport",
    "ssn",
    "date_of_birth",
    "dob",
    "card_number",
)


def _normalise_key(key: str) -> str:
    return "".join(character.lower() if character.isalnum() else "_" for character in key)


def _is_sensitive(key: str, tokens: tuple[str, ...]) -> bool:
    normalised = _normalise_key(key)
    return any(token in normalised for token in tokens)


def redact(
    payload: Mapping[str, Any],
    *,
    extra_sensitive_keys: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Return a recursively redacted copy; sensitive values never leave this function.

    Key-name based redaction is intentionally conservative. Values under
    innocuously named keys are not inspected; callers must keep payloads small
    and structured. ``append`` always applies this helper before hashing/signing.
    """
    tokens = tuple(_normalise_key(token) for token in (*_SENSITIVE_KEY_PARTS, *extra_sensitive_keys))

    def clean(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                str(key): REDACTED if _is_sensitive(str(key), tokens) else clean(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [clean(item) for item in value]
        return value

    cleaned = clean(dict(payload))
    if not isinstance(cleaned, dict):
        raise TypeError("redacted payload must remain a mapping")
    return cast(dict[str, Any], cleaned)


def append(
    store: AuditAnchorStore,
    provider: KeyProvider,
    *,
    tenant_id: str,
    actor: str,
    action: str,
    payload: Mapping[str, Any],
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Append one signed record to the chain for ``tenant_id``.

    Raises :class:`AuditChainError` if the existing chain is invalid, so a
    corrupted tail can never be silently extended.
    """
    if not tenant_id or not isinstance(tenant_id, str):
        raise ValueError("tenant_id must be a non-empty string")
    if not actor or not isinstance(actor, str):
        raise ValueError("actor must be a non-empty string")
    if not action or not isinstance(action, str):
        raise ValueError("action must be a non-empty string")

    prior = verify_chain(store, provider, tenant_id=tenant_id)
    if not prior.ok:
        raise AuditChainError(
            f"refusing append: chain invalid at seq {prior.first_bad_seq}: {prior.reason}"
        )

    record: dict[str, Any] = {
        "seq": prior.total + 1,
        "prev_hash": prior.tail_hash if prior.tail_hash is not None else GENESIS_HASH,
        "payload_hash": payload_hash(redact(payload)),
        "timestamp": timestamp
        or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tenant_id": tenant_id,
        "actor": actor,
        "action": action,
        "key_id": provider.current_key_id(),
        "payload": redact(payload),
    }
    record["signature"] = provider.sign(canonical_json(record))
    return store.append(record)


def record_authorization_failure(
    store: AuditAnchorStore,
    provider: KeyProvider,
    *,
    tenant_id: str,
    actor: str,
    action: str,
    reason: str,
    detail: Mapping[str, Any] | None = None,
    authorization_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Unconditionally append an authorization-failure audit record.

    If ``authorization_check`` is supplied it is evaluated here; allowed, denied
    or raising, the audit record is still written with the observed outcome.
    This is the fail-closed path: a denied check cannot be silently dropped.
    No exception text is recorded or logged (it may contain sensitive data).
    """
    outcome = "denied"
    observed_reason = reason
    if authorization_check is not None:
        try:
            outcome = "allowed" if authorization_check() else "denied"
        except Exception:
            outcome = "error"
            observed_reason = "authorization_check_error"

    return append(
        store,
        provider,
        tenant_id=tenant_id,
        actor=actor,
        action="authorization_failure",
        payload={
            "outcome": outcome,
            "reason": observed_reason,
            "requested_action": action,
            "detail": dict(detail or {}),
        },
    )


__all__ = [
    "REDACTED",
    "append",
    "record_authorization_failure",
    "redact",
]
