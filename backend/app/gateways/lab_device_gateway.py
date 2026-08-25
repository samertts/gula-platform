"""Default-deny containment for the retired Lab Device Gateway.

This legacy module is not an approved device integration path. It must never
accept a laboratory device envelope, write a result, open a device connection,
or serve as a substitute for the reviewed Device Bridge/quarantine workflow.
Any future integration requires separate deployment approval, mutual TLS,
facility gateway controls, and human UAT.
"""

from __future__ import annotations

import logging
from typing import NoReturn

logger = logging.getLogger("gula.device_gateway")


class DeviceInputError(ValueError):
    """Retained for compatibility with callers that distinguish invalid input."""


class DeviceAuthError(PermissionError):
    """Raised whenever use of the retired device gateway is rejected."""


def receive_device_result(
    _sample_id: str,
    _test: str,
    _value: object,
    *,
    device_id: str = "",
    _signature: str = "",
    _timestamp: int = 0,
    _nonce: str = "",
) -> NoReturn:
    """Reject every legacy device envelope before parsing or accepting it."""
    logger.warning(
        "legacy lab device gateway envelope rejected",
        extra={
            "reason": "legacy_gateway_default_deny",
            "device_id_present": bool(device_id),
        },
    )
    raise DeviceAuthError(
        "legacy lab device gateway intake is disabled; use the approved Device Bridge "
        "and human measurement-review process"
    )
