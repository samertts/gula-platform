"""Test-only environment setup for the isolated device bridge service."""

import pytest

from app.security.auth import API_KEY_ENV
from _test_support import TEST_API_KEY


@pytest.fixture(autouse=True)
def configured_test_api_key(monkeypatch: pytest.MonkeyPatch):
    """Provide credentials only inside tests; production has no default key."""
    monkeypatch.setenv(API_KEY_ENV, TEST_API_KEY)
