"""
Lab Device Gateway — GULA Platform
=====================================
Interface layer for laboratory analyzers (HL7 / ASTM / LIS integration).

Previously this was a stub that echoed back raw input without any validation,
which could allow garbage values to enter the system.  Now performs:
  - Type checking on all inputs
  - sample_id must be a non-empty string
  - test must be a non-empty string (≤ 100 chars)
  - value must be numeric and within a safe range (−1 000 000 to 1 000 000)

Note: This gateway is a **receiving layer only** — it validates and normalises
the incoming device message but does NOT write to the database.  The caller
is responsible for persisting the returned payload.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("gula.device_gateway")

_MAX_VALUE = 1_000_000.0
_MIN_VALUE = -1_000_000.0
_MAX_STR_LEN = 100


class DeviceInputError(ValueError):
    """Raised when a device result payload fails validation."""


def receive_device_result(
    sample_id: str,
    test: str,
    value,
) -> dict:
    """Validate and normalise a result received from a lab analyser.

    Args:
        sample_id: Unique identifier for the sample (barcode / accession number).
        test:      Test code / name as reported by the device (e.g. "glucose").
        value:     Numeric result value reported by the device.

    Returns:
        Normalised dict ready for downstream processing::

            {
                "sample":  str,
                "test":    str,
                "value":   float,
                "status":  "received",
            }

    Raises:
        DeviceInputError: If any input fails validation.
    """
    # --- sample_id ---
    if not sample_id or not isinstance(sample_id, str):
        raise DeviceInputError("sample_id must be a non-empty string")
    sample_id = sample_id.strip()
    if not sample_id or len(sample_id) > _MAX_STR_LEN:
        raise DeviceInputError(f"sample_id must be 1–{_MAX_STR_LEN} characters")

    # --- test ---
    if not test or not isinstance(test, str):
        raise DeviceInputError("test must be a non-empty string")
    test = test.strip()
    if not test or len(test) > _MAX_STR_LEN:
        raise DeviceInputError(f"test must be 1–{_MAX_STR_LEN} characters")

    # --- value ---
    if value is None:
        raise DeviceInputError("value is required")
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        raise DeviceInputError(f"value must be numeric, got: {value!r}")
    if not (_MIN_VALUE <= numeric_value <= _MAX_VALUE):
        raise DeviceInputError(
            f"value {numeric_value} is outside allowed range "
            f"[{_MIN_VALUE}, {_MAX_VALUE}]"
        )

    logger.debug(
        "[DEVICE] Received result — sample=%s test=%s value=%s",
        sample_id, test, numeric_value,
    )

    return {
        "sample": sample_id,
        "test": test,
        "value": numeric_value,
        "status": "received",
    }
