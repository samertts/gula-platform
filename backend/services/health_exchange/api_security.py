"""API key verification for the health-exchange integration.

PROGRAM-STABLE-001: the key is read from the environment (or a key file)
instead of being hardcoded. When unconfigured the module is DENY-BY-DEFAULT:
no key, no access. Comparison is constant-time (hmac.compare_digest).
"""
from __future__ import annotations

import hmac
import os
from pathlib import Path


def _load_key() -> str | None:
    key = os.environ.get("HEALTH_EXCHANGE_API_KEY")
    if key:
        return key
    key_file = os.environ.get("HEALTH_EXCHANGE_API_KEY_FILE")
    if key_file:
        path = Path(key_file)
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    return None


def verify_key(key: str | None) -> bool:
    """Constant-time check of a caller-supplied key against the configured key."""
    expected = _load_key()
    if expected is None or not key:
        return False
    return hmac.compare_digest(key.encode("utf-8"), expected.encode("utf-8"))
