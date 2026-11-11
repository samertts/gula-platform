"""API-key authentication for the isolated device bridge service."""

from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException

API_KEY_ENV = "LABLINK_API_KEY"


def verify_api_key(x_api_key: str | None = Header(default=None)) -> str:
    """Require a configured key and reject missing or mismatched credentials."""
    expected = os.getenv(API_KEY_ENV, "")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Device bridge authentication is not configured",
        )
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
