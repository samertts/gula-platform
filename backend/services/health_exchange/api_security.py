"""Authentication helper for the health-exchange integration.

The integration key is runtime-only. It must never have a source-code default.
"""
from __future__ import annotations

import hmac
import os


API_KEY = os.getenv("LAB_PLATFORM_API_KEY")


def verify_key(key: str | None) -> bool:
    """Return True only for a configured key, using constant-time comparison."""
    if not API_KEY or not isinstance(key, str):
        return False
    return hmac.compare_digest(key, API_KEY)
