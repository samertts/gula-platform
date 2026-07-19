"""Startup guard tests.

Covers:
  - validate_config: passes with all secrets set
  - validate_config: raises on missing SECRET_KEY (production)
  - validate_config: raises on weak SECRET_KEY (production)
  - validate_config: raises on missing ENCRYPTION_KEY (production)
  - validate_config: raises on missing NID_HMAC_KEY (production)
  - validate_config: dev env tolerates missing secrets
  - is_system_ready: returns False before startup completes
  - is_system_ready: returns degraded_redis when Redis is down post-startup
  - set_system_ready: can set and clear readiness manually
  - _is_weak: detects known weak patterns
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest

# ── validate_config ───────────────────────────────────────────────────────────

class TestValidateConfig:
    def _run(self, secret_key="", encryption_key="", nid_hmac_key="", is_prod=True):
        """Helper: patch app.config attributes and call validate_config().

        validate_config() does `from ..config import SECRET_KEY, ...` inside the
        function body, so we must mutate app.config attributes directly — not
        try to patch them on the startup_guard namespace where they don't exist.
        """
        import app.config as cfg
        from app.core import startup_guard
        old_sk   = cfg.SECRET_KEY
        old_ek   = cfg.ENCRYPTION_KEY
        old_nid  = cfg.NID_HMAC_KEY
        old_prod = cfg.IS_PRODUCTION
        try:
            cfg.SECRET_KEY     = secret_key
            cfg.ENCRYPTION_KEY = encryption_key
            cfg.NID_HMAC_KEY   = nid_hmac_key
            cfg.IS_PRODUCTION  = is_prod
            startup_guard.validate_config()
        finally:
            cfg.SECRET_KEY     = old_sk
            cfg.ENCRYPTION_KEY = old_ek
            cfg.NID_HMAC_KEY   = old_nid
            cfg.IS_PRODUCTION  = old_prod

    def test_passes_with_strong_secrets(self):
        from cryptography.fernet import Fernet
        fkey = Fernet.generate_key().decode()
        self._run(
            secret_key="a" * 64,
            encryption_key=fkey,
            nid_hmac_key="b" * 64,
            is_prod=True,
        )

    def test_raises_on_missing_secret_key_in_prod(self):
        from cryptography.fernet import Fernet
        fkey = Fernet.generate_key().decode()
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            self._run(secret_key="", encryption_key=fkey, nid_hmac_key="b" * 64, is_prod=True)

    def test_raises_on_weak_secret_key_in_prod(self):
        from cryptography.fernet import Fernet
        fkey = Fernet.generate_key().decode()
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            self._run(secret_key="changeme123", encryption_key=fkey, nid_hmac_key="b" * 64, is_prod=True)

    def test_raises_on_missing_encryption_key_in_prod(self):
        with pytest.raises(RuntimeError, match="ENCRYPTION_KEY"):
            self._run(secret_key="a" * 64, encryption_key="", nid_hmac_key="b" * 64, is_prod=True)

    def test_raises_on_missing_nid_hmac_key_in_prod(self):
        from cryptography.fernet import Fernet
        fkey = Fernet.generate_key().decode()
        with pytest.raises(RuntimeError, match="NID_HMAC_KEY"):
            self._run(secret_key="a" * 64, encryption_key=fkey, nid_hmac_key="", is_prod=True)

    def test_dev_env_tolerates_empty_secrets(self):
        # In non-production, missing secrets generate warnings but do not raise
        self._run(secret_key="", encryption_key="", nid_hmac_key="", is_prod=False)

    def test_raises_when_multiple_secrets_missing(self):
        with pytest.raises(RuntimeError) as exc_info:
            self._run(secret_key="", encryption_key="", nid_hmac_key="", is_prod=True)
        # Error message should list at least one problem
        assert "SECRET_KEY" in str(exc_info.value) or "ENCRYPTION_KEY" in str(exc_info.value)


# ── _is_weak ──────────────────────────────────────────────────────────────────

class TestIsWeak:
    def _is_weak(self, value: str) -> bool:
        from app.core.startup_guard import _is_weak
        return _is_weak(value)

    def test_detects_changeme(self):
        assert self._is_weak("changeme") is True

    def test_detects_default(self):
        assert self._is_weak("default_key") is True

    def test_detects_secret(self):
        assert self._is_weak("my_secret_key") is True

    def test_detects_example(self):
        assert self._is_weak("example-key-123") is True

    def test_detects_password(self):
        assert self._is_weak("password123") is True

    def test_strong_key_passes(self):
        assert self._is_weak("f3a9b2c1d0e7f6a5b4c3d2e1f0") is False

    def test_random_hex_passes(self):
        import secrets
        strong = secrets.token_hex(32)
        assert self._is_weak(strong) is False


# ── set_system_ready / is_system_ready ───────────────────────────────────────

class TestSystemReadiness:
    def setup_method(self):
        from app.core import startup_guard
        startup_guard.system_ready = False
        startup_guard._readiness_reason = "startup_in_progress"

    def teardown_method(self):
        from app.core import startup_guard
        startup_guard.system_ready = False

    def test_not_ready_before_startup(self):
        from app.core.startup_guard import is_system_ready
        ready, reason = is_system_ready()
        assert ready is False
        assert reason == "startup_in_progress"

    def test_set_system_ready_marks_ready(self):
        from app.core.startup_guard import is_system_ready, set_system_ready
        set_system_ready(True, "ok")
        # is_system_ready also checks DB — mock the DB check to pass
        with patch("app.database.check_db_connection", return_value=True):
            with patch("app.security.redis_client.cache") as mock_redis:
                mock_redis.set.return_value = True
                ready, _reason = is_system_ready()
        assert ready is True

    def test_set_system_ready_false_clears_readiness(self):
        from app.core.startup_guard import is_system_ready, set_system_ready
        set_system_ready(True, "ok")
        set_system_ready(False, "db_down")
        ready, _reason = is_system_ready()
        assert ready is False

    def test_database_down_after_startup_returns_503_reason(self):
        from app.core.startup_guard import is_system_ready, set_system_ready
        set_system_ready(True, "ok")
        with patch("app.database.check_db_connection", return_value=False):
            ready, reason = is_system_ready()
        assert ready is False
        assert reason == "database_unavailable"

    def test_redis_down_after_startup_returns_degraded_not_false(self):
        from app.core.startup_guard import is_system_ready, set_system_ready
        set_system_ready(True, "ok")
        with patch("app.database.check_db_connection", return_value=True):
            with patch("app.security.redis_client.cache") as mock_redis:
                mock_redis.set.side_effect = Exception("Redis connection refused")
                ready, reason = is_system_ready()
        # Redis failure post-startup → degraded, not totally down
        assert ready is True
        assert reason == "degraded_redis"
