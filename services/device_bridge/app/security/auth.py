"""Inbound authentication for the device bridge.

IA-053. `verify_api_key` used to call `sys.exit(1)` when LABLINK_API_KEY was
unset. Measured: the SystemExit is raised inside the request, where the ASGI
stack turns it into a 500 -- the process survives, and every authenticated
endpoint answers 500 while /health keeps returning 200. It fails closed, so it
was never an authorization hole; it was undiagnosable.

That state is the *default* for a documented deployment:
docker-compose.yml passes `LABLINK_API_KEY: "${LABLINK_API_KEY:-}"`, so
`docker compose --profile device-bridge up device-bridge` with nothing set runs a
service whose every real endpoint 500s, whose healthcheck passes, and whose logs
show a SystemExit traceback per request.

A missing credential is a configuration error, not a request error. It is now
detected where the monolith detects its own (app/config.py hard-fails on missing
secrets): at import, once, with a message naming the variable.
"""
from __future__ import annotations

import os

from fastapi import Header, HTTPException

API_KEY_ENV = "LABLINK_API_KEY"


class MissingApiKeyError(RuntimeError):
    """Raised at import when LABLINK_API_KEY is absent or empty."""


def require_configured_api_key() -> str:
    """Return the configured key, or refuse to start.

    Called at import time by this module. A deployment without a key cannot
    serve a single authenticated request, so starting and then failing each one
    is strictly worse than not starting: the healthcheck would pass either way,
    and only this way does the operator get told what is wrong.
    """
    expected = os.getenv(API_KEY_ENV, "").strip()
    if not expected:
        raise MissingApiKeyError(
            f"{API_KEY_ENV} is not set. The device bridge authenticates every "
            "device and operator request with it and cannot serve any of them "
            "without it. docker-compose.yml passes it through as "
            f'"${{{API_KEY_ENV}:-}}", so set it in the environment or .env '
            "before starting the device-bridge profile.",
        )
    return expected


# Read once, at import, so a misconfigured deployment fails to start instead of
# answering 500 on every authenticated request.
_EXPECTED_API_KEY = require_configured_api_key()


def verify_api_key(x_api_key: str | None = Header(default=None)) -> str:
    if x_api_key != _EXPECTED_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
