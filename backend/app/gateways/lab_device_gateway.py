"""
Lab Device Gateway — GULA Platform
=====================================
Interface layer for laboratory analyzers (HL7 / ASTM / LIS integration).

Security model
--------------
Lab devices are untrusted network endpoints.  Any device on the network
could forge a result message.  To prevent this:

1. **Device whitelist** (DEVICE_HMAC_KEY env var required in production)
   Only devices whose device_id appears in the whitelist are accepted.
   Set ALLOWED_DEVICE_IDS as a comma-separated list of known device IDs.

2. **HMAC-SHA256 message signature** (when DEVICE_HMAC_KEY is set)
   Each message must include a ``signature`` computed as:
       HMAC-SHA256(DEVICE_HMAC_KEY, f"{device_id}:{sample_id}:{test}:{value}")
   Messages with missing or invalid signatures are rejected.
   In development (no DEVICE_HMAC_KEY), signatures are skipped with a warning.

3. **Input validation**
   - sample_id / test: non-empty strings, ≤ 100 chars each
   - value: numeric, within ±1 000 000

This gateway is a **receiving layer only** — it does NOT write to the
database.  The caller is responsible for persisting the returned payload.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os

logger = logging.getLogger("gula.device_gateway")

_MAX_VALUE   = 1_000_000.0
_MIN_VALUE   = -1_000_000.0
_MAX_STR_LEN = 100

# ── Security config ────────────────────────────────────────────────────────────
# Set DEVICE_HMAC_KEY in the environment to enable signature verification.
# Set ALLOWED_DEVICE_IDS to a comma-separated list of trusted device IDs.
_DEVICE_HMAC_KEY: str = os.getenv("DEVICE_HMAC_KEY", "")
_ALLOWED_IDS_RAW: str = os.getenv("ALLOWED_DEVICE_IDS", "")
_ALLOWED_DEVICE_IDS: set[str] = (
    {d.strip() for d in _ALLOWED_IDS_RAW.split(",") if d.strip()}
    if _ALLOWED_IDS_RAW
    else set()
)

if not _DEVICE_HMAC_KEY:
    logger.warning(
        "[DEVICE_GATEWAY] DEVICE_HMAC_KEY not set — HMAC verification disabled. "
        "Set this key in production to authenticate lab device messages."
    )


class DeviceInputError(ValueError):
    """Raised when a device result payload fails validation."""


class DeviceAuthError(PermissionError):
    """Raised when a device message fails authentication."""


# ── Helpers ────────────────────────────────────────────────────────────────────

def _compute_signature(device_id: str, sample_id: str, test: str, value: float) -> str:
    msg = f"{device_id}:{sample_id}:{test}:{value}".encode()
    return hmac.new(_DEVICE_HMAC_KEY.encode(), msg, hashlib.sha256).hexdigest()


def _verify_signature(device_id: str, sample_id: str, test: str, value: float, signature: str) -> bool:
    expected = _compute_signature(device_id, sample_id, test, value)
    return hmac.compare_digest(expected, signature)


# ── Public API ─────────────────────────────────────────────────────────────────

def receive_device_result(
    sample_id: str,
    test: str,
    value,
    *,
    device_id: str = "",
    signature: str = "",
) -> dict:
    """Validate, authenticate, and normalise a result from a lab analyser.

    Args:
        sample_id:  Unique sample barcode / accession number.
        test:       Test code / name as reported by the device (e.g. "glucose").
        value:      Numeric result value.
        device_id:  Registered device identifier (required when DEVICE_HMAC_KEY is set).
        signature:  HMAC-SHA256 of ``"{device_id}:{sample_id}:{test}:{value}"``
                    using DEVICE_HMAC_KEY (required when DEVICE_HMAC_KEY is set).

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
        DeviceAuthError:  If device_id is not whitelisted or signature is invalid.
        DeviceInputError: If any input fails type/range validation.
    """
    # ── Input validation ───────────────────────────────────────────────────────
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
        raise DeviceInputError(f"value must be numeric, got: {value!r}")
    if not (_MIN_VALUE <= numeric_value <= _MAX_VALUE):
        raise DeviceInputError(
            f"value {numeric_value} is outside allowed range [{_MIN_VALUE}, {_MAX_VALUE}]"
        )

    # ── Authentication (only when DEVICE_HMAC_KEY is configured) ───────────────
    if _DEVICE_HMAC_KEY:
        device_id = (device_id or "").strip()

        # 1. Device whitelist check
        if _ALLOWED_DEVICE_IDS and device_id not in _ALLOWED_DEVICE_IDS:
            logger.warning(
                "[DEVICE_GATEWAY] Rejected unknown device_id=%s sample=%s",
                device_id, sample_id,
            )
            raise DeviceAuthError(f"Device '{device_id}' is not in the allowed device list")

        # 2. HMAC signature check
        if not signature:
            raise DeviceAuthError("Message signature is required but was not provided")

        if not _verify_signature(device_id, sample_id, test, numeric_value, signature):
            logger.warning(
                "[DEVICE_GATEWAY] Invalid signature from device_id=%s sample=%s",
                device_id, sample_id,
            )
            raise DeviceAuthError("Invalid message signature — possible message forgery")

    logger.debug(
        "[DEVICE] Received result — device=%s sample=%s test=%s value=%s",
        device_id or "unset", sample_id, test, numeric_value,
    )

    return {
        "sample":    sample_id,
        "test":      test,
        "value":     numeric_value,
        "device_id": device_id or "unknown",
        "status":    "received",
    }
