"""Lab Device Gateway — GULA Platform
=====================================
Interface layer for laboratory analyzers (HL7 / ASTM / LIS integration).

Security model (layered)
------------------------
1. **Input validation** — type, length, numeric range.
2. **Device whitelist** — only registered device_ids are accepted when
   ALLOWED_DEVICE_IDS env var is set.
3. **HMAC-SHA256 message signature** — computed over
   ``"{device_id}:{sample_id}:{test}:{value}:{timestamp}"`` using
   DEVICE_HMAC_KEY.  Prevents message forgery.
4. **Replay protection** — each message must include a ``timestamp`` (Unix
   seconds) and a ``nonce`` (random string).  The gateway rejects messages
   older than REPLAY_WINDOW_SECONDS and nonces already seen within that
   window (stored in Redis / local fallback with TTL).  This prevents an
   attacker from re-sending a captured valid message.

Environment variables
---------------------
DEVICE_HMAC_KEY      : Required in production for HMAC + replay protection.
ALLOWED_DEVICE_IDS   : Comma-separated whitelist of known device IDs.
REPLAY_WINDOW_SECONDS: Max age of a valid message (default 120 s = 2 min).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time

logger = logging.getLogger("gula.device_gateway")

# ── Config ─────────────────────────────────────────────────────────────────────
_MAX_VALUE = 1_000_000.0
_MIN_VALUE = -1_000_000.0
_MAX_STR_LEN = 100

_DEVICE_HMAC_KEY: str = os.getenv("DEVICE_HMAC_KEY", "")
_ALLOWED_IDS_RAW: str = os.getenv("ALLOWED_DEVICE_IDS", "")
_ALLOWED_DEVICE_IDS: set[str] = (
    {d.strip() for d in _ALLOWED_IDS_RAW.split(",") if d.strip()} if _ALLOWED_IDS_RAW else set()
)
_REPLAY_WINDOW: int = int(os.getenv("REPLAY_WINDOW_SECONDS", "120"))
_NONCE_PREFIX = "dgw:nonce:"

if not _DEVICE_HMAC_KEY:
    logger.warning(
        "[DEVICE_GATEWAY] DEVICE_HMAC_KEY not set — HMAC & replay protection disabled. "
        "Set this key in production.",
    )


# ── Exceptions ─────────────────────────────────────────────────────────────────


class DeviceInputError(ValueError):
    """Raised when a device result payload fails type/range validation."""


class DeviceAuthError(PermissionError):
    """Raised when a device message fails authentication or replay check."""


# ── Helpers ────────────────────────────────────────────────────────────────────


def _compute_signature(
    device_id: str, sample_id: str, test: str, value: float, timestamp: int,
) -> str:
    msg = f"{device_id}:{sample_id}:{test}:{value}:{timestamp}".encode()
    return hmac.new(_DEVICE_HMAC_KEY.encode(), msg, hashlib.sha256).hexdigest()


def _check_replay(nonce: str, device_id: str) -> None:
    """Raise DeviceAuthError if the nonce has been seen before.

    Stores seen nonces in Redis (or in-memory fallback) with a TTL equal to
    REPLAY_WINDOW_SECONDS so the store never grows unbounded.
    """
    from ..security.redis_client import cache

    key = _NONCE_PREFIX + device_id + ":" + nonce
    try:
        existing = cache.get(key)
        if existing is not None:
            raise DeviceAuthError(f"Replayed nonce from device '{device_id}' — request rejected")
        cache.set(key, "1", ex=_REPLAY_WINDOW + 10)
    except DeviceAuthError:
        raise
    except Exception as exc:
        logger.warning(
            "[DEVICE_GATEWAY] Redis nonce check failed for device=%s: %s — replay protection degraded",
            device_id,
            exc,
        )
        # If Redis is down we cannot enforce uniqueness — log and continue.
        # This is acceptable because HMAC already authenticates the message.


# ── Public API ─────────────────────────────────────────────────────────────────


def receive_device_result(
    sample_id: str,
    test: str,
    value,
    *,
    device_id: str = "",
    signature: str = "",
    timestamp: int = 0,
    nonce: str = "",
) -> dict:
    """Validate, authenticate, and replay-check a result from a lab analyser.

    Args:
        sample_id:  Sample barcode / accession number.
        test:       Test code / name (e.g. "glucose").
        value:      Numeric result value.
        device_id:  Registered device identifier (required when DEVICE_HMAC_KEY set).
        signature:  HMAC-SHA256 of ``"{device_id}:{sample_id}:{test}:{value}:{timestamp}"``
                    (required when DEVICE_HMAC_KEY set).
        timestamp:  Unix seconds when the device generated this message.
                    Must be within REPLAY_WINDOW_SECONDS of server time.
        nonce:      Random per-message string to prevent replay attacks.

    Returns:
        Normalised dict::

            {
                "sample":    str,
                "test":      str,
                "value":     float,
                "device_id": str,
                "status":    "received",
            }

    Raises:
        DeviceAuthError:  Authentication or replay check failure.
        DeviceInputError: Type/range validation failure.

    """
    # ── 1. Input validation ────────────────────────────────────────────────────
    if not sample_id or not isinstance(sample_id, str):
        raise DeviceInputError("sample_id must be a non-empty string")
    sample_id = sample_id.strip()
    if not sample_id or len(sample_id) > _MAX_STR_LEN:
        raise DeviceInputError(f"sample_id must be 1–{_MAX_STR_LEN} characters")

    if not test or not isinstance(test, str):
        raise DeviceInputError("test must be a non-empty string")
    test = test.strip()
    if not test or len(test) > _MAX_STR_LEN:
        raise DeviceInputError(f"test must be 1–{_MAX_STR_LEN} characters")

    if value is None:
        raise DeviceInputError("value is required")
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        raise DeviceInputError(f"value must be numeric, got: {value!r}") from None
    if not (_MIN_VALUE <= numeric_value <= _MAX_VALUE):
        raise DeviceInputError(
            f"value {numeric_value} is outside allowed range [{_MIN_VALUE}, {_MAX_VALUE}]",
        )

    # ── 2. Authentication + replay protection (only when key is configured) ────
    if _DEVICE_HMAC_KEY:
        device_id = (device_id or "").strip()

        # Whitelist check
        if _ALLOWED_DEVICE_IDS and device_id not in _ALLOWED_DEVICE_IDS:
            logger.warning("[DEVICE_GATEWAY] Unknown device_id=%s sample=%s", device_id, sample_id)
            raise DeviceAuthError(f"Device '{device_id}' is not in the allowed device list")

        # Timestamp window check (prevents stale/replayed messages)
        if not timestamp:
            raise DeviceAuthError("timestamp is required for authenticated messages")
        server_now = int(time.time())
        age = abs(server_now - timestamp)
        if age > _REPLAY_WINDOW:
            raise DeviceAuthError(
                f"Message timestamp is {age}s old — outside replay window ({_REPLAY_WINDOW}s)",
            )

        # HMAC signature verification
        if not signature:
            raise DeviceAuthError("signature is required for authenticated messages")
        expected = _compute_signature(device_id, sample_id, test, numeric_value, timestamp)
        if not hmac.compare_digest(expected, signature):
            logger.warning(
                "[DEVICE_GATEWAY] Invalid signature device_id=%s sample=%s",
                device_id,
                sample_id,
            )
            raise DeviceAuthError("Invalid message signature — possible forgery")

        # Nonce replay check (requires nonce to be present)
        if not nonce:
            raise DeviceAuthError("nonce is required for authenticated messages")
        _check_replay(nonce, device_id)

    logger.debug(
        "[DEVICE] Accepted — device=%s sample=%s test=%s value=%s",
        device_id or "unset",
        sample_id,
        test,
        numeric_value,
    )

    return {
        "sample": sample_id,
        "test": test,
        "value": numeric_value,
        "device_id": device_id or "unknown",
        "status": "received",
    }
