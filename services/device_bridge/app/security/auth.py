from __future__ import annotations

import os
import sys

from fastapi import Header, HTTPException

API_KEY_ENV = "LABLINK_API_KEY"
# Test/CLI compatibility constant only; production verification still requires
# LABLINK_API_KEY in the environment and never falls back to this value.
DEFAULT_API_KEY = "lablink-dev-key"


def verify_api_key(x_api_key: str | None = Header(default=None)) -> str:
    expected = os.getenv(API_KEY_ENV, "")
    if not expected:
        sys.exit(1)
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
