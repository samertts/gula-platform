"""Shared fixtures for device_bridge tests.

verify_api_key() (app/security/auth.py) requires the LABLINK_API_KEY env var
to be set — there is deliberately no hardcoded default key in production
code (a hardcoded fallback credential is itself a vulnerability). Tests need
their own key, so this fixture sets one for the duration of each test.
"""
from __future__ import annotations

import pytest

TEST_API_KEY = "test-only-lablink-bridge-key"


@pytest.fixture(autouse=True)
def _lablink_api_key(monkeypatch):
    monkeypatch.setenv("LABLINK_API_KEY", TEST_API_KEY)


@pytest.fixture()
def api_key_headers() -> dict[str, str]:
    return {"x-api-key": TEST_API_KEY}
