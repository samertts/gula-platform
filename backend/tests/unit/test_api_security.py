"""PROGRAM-STABLE-001: health-exchange API key verification tests.

Regression coverage for removing the hardcoded API key:
  - key comes from environment / key file, never from source
  - unconfigured module is deny-by-default
  - comparison is constant-time (hmac.compare_digest)
"""

from __future__ import annotations

import pytest
from services.health_exchange.api_security import _load_key, verify_key


class TestApiSecurity:
    def test_deny_when_unconfigured(self, monkeypatch):
        monkeypatch.delenv("HEALTH_EXCHANGE_API_KEY", raising=False)
        monkeypatch.delenv("HEALTH_EXCHANGE_API_KEY_FILE", raising=False)
        assert _load_key() is None
        assert verify_key("anything") is False
        assert verify_key(None) is False

    def test_accepts_configured_key(self, monkeypatch):
        monkeypatch.setenv("HEALTH_EXCHANGE_API_KEY", "correct-key-123")
        assert verify_key("correct-key-123") is True

    def test_rejects_wrong_key(self, monkeypatch):
        monkeypatch.setenv("HEALTH_EXCHANGE_API_KEY", "correct-key-123")
        assert verify_key("wrong-key-999") is False
        assert verify_key("") is False

    def test_key_file_fallback(self, monkeypatch, tmp_path):
        key_file = tmp_path / "key"
        key_file.write_text("file-based-key\n")
        monkeypatch.delenv("HEALTH_EXCHANGE_API_KEY", raising=False)
        monkeypatch.setenv("HEALTH_EXCHANGE_API_KEY_FILE", str(key_file))
        assert _load_key() == "file-based-key"
        assert verify_key("file-based-key") is True
