"""API-key authentication for the isolated device bridge service."""

from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException

API_KEY_ENV = "LABLINK_API_KEY"


def verify_api_key(x_api_key: str | None = Header(default=None)) -> str:
    """Require a configured key and reject missing or mismatched credentials.

    A single misconfigured/unauthenticated request must not take down the
    whole process (it previously called ``sys.exit(1)``, killing every other
    device's in-flight connection along with it) — fail that one request
    with 503 instead. The comparison uses ``hmac.compare_digest`` so a wrong
    guess can't be timed byte-by-byte against the real key.
    """
    expected = os.getenv(API_KEY_ENV, "")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Device bridge authentication is not configured",
        )
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
