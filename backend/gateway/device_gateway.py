"""Fail-closed containment for the retired experimental device gateway.

This module previously opened a raw TCP socket and forwarded parsed device values
through a direct HTTP request using default configuration. That behavior is not
an approved clinical device-integration path and must not be started. Future
integration belongs to the separately reviewed Device Bridge design, which
requires explicit enablement, mTLS, gateway controls, and human UAT.
"""

from __future__ import annotations

import logging
from typing import NoReturn

logger = logging.getLogger(__name__)


class LegacyDeviceGatewayDisabledError(RuntimeError):
    """Raised whenever code attempts to use the retired direct device gateway."""


def _raise_disabled(operation: str) -> NoReturn:
    logger.critical(
        "legacy device gateway operation rejected",
        extra={"operation": operation, "reason": "retired_unreviewed_device_path"},
    )
    raise LegacyDeviceGatewayDisabledError(
        "The legacy device gateway is disabled. Use the approved Device Bridge "
        "integration process; direct sockets and result forwarding are prohibited."
    )


def parse_message(_message: str) -> NoReturn:
    """Reject legacy parsing so no caller can progress toward direct forwarding."""
    _raise_disabled("parse_message")


def send_result(_data: object) -> NoReturn:
    """Reject all direct device-result forwarding attempts."""
    _raise_disabled("send_result")


def run_server() -> NoReturn:
    """Reject raw socket-server startup from the backend repository."""
    _raise_disabled("run_server")


if __name__ == "__main__":
    run_server()
