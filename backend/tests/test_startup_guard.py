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
    def _run(self, secret_key="", encryption_key="", nid_hmac_key="", resend_api_key="", is_prod=True):
        """Helper: patch app.config attributes and call validate_config().

        validate_config() does `from ..config import SECRET_KEY, ...` inside the
        function body, so we must mutate app.config attributes directly — not
        try to patch them on the startup_guard namespace where they don't exist.
        """
        import app.config as cfg
        from app.core import startup_guard

        old_sk = cfg.SECRET_KEY
        old_ek = cfg.ENCRYPTION_KEY
        old_nid = cfg.NID_HMAC_KEY
        old_resend = cfg.RESEND_API_KEY
        old_prod = cfg.IS_PRODUCTION
        try:
            cfg.SECRET_KEY = secret_key
            cfg.ENCRYPTION_KEY = encryption_key
            cfg.NID_HMAC_KEY = nid_hmac_key
            cfg.RESEND_API_KEY = resend_api_key
            cfg.IS_PRODUCTION = is_prod
            startup_guard.validate_config()
        finally:
            cfg.SECRET_KEY = old_sk
            cfg.ENCRYPTION_KEY = old_ek
            cfg.NID_HMAC_KEY = old_nid
            cfg.RESEND_API_KEY = old_resend
            cfg.IS_PRODUCTION = old_prod

    def test_passes_with_strong_secrets(self):
        from cryptography.fernet import Fernet

        fkey = Fernet.generate_key().decode()
        self._run(
            secret_key="a" * 64,
            encryption_key=fkey,
            nid_hmac_key="b" * 64,
            resend_api_key="re_" + "A" * 40,
            is_prod=True,
        )

    def test_raises_on_missing_resend_key_in_prod(self):
        from cryptography.fernet import Fernet

        fkey = Fernet.generate_key().decode()
        with pytest.raises(RuntimeError, match="RESEND_API_KEY"):
            self._run(
                secret_key="a" * 64,
                encryption_key=fkey,
                nid_hmac_key="b" * 64,
                resend_api_key="",
                is_prod=True,
            )

    def test_raises_on_weak_resend_key_in_prod(self):
        from cryptography.fernet import Fernet

        fkey = Fernet.generate_key().decode()
        with pytest.raises(RuntimeError, match="RESEND_API_KEY"):
            self._run(
                secret_key="a" * 64,
                encryption_key=fkey,
                nid_hmac_key="b" * 64,
                resend_api_key="changeme",
                is_prod=True,
            )

    def test_missing_resend_key_tolerated_in_dev(self):
        from cryptography.fernet import Fernet

        fkey = Fernet.generate_key().decode()
        # Non-production: missing RESEND_API_KEY warns but does not raise
        self._run(
            secret_key="a" * 64,
            encryption_key=fkey,
            nid_hmac_key="b" * 64,
            resend_api_key="",
            is_prod=False,
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
            self._run(
                secret_key="changeme123", encryption_key=fkey, nid_hmac_key="b" * 64, is_prod=True
            )

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
        with patch("app.database.check_db_connection", return_value=True), patch("app.security.redis_client.cache") as mock_redis:
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
        with patch("app.database.check_db_connection", return_value=True), patch("app.security.redis_client.cache") as mock_redis:
            mock_redis.set.side_effect = Exception("Redis connection refused")
            ready, reason = is_system_ready()
        # Redis failure post-startup → degraded, not totally down
        assert ready is True
        assert reason == "degraded_redis"


# ── Test-mode bypass ──────────────────────────────────────────────────────────


class TestTestModeBypass:
    """Verify that run_startup_guard() sets system_ready=True in test mode."""

    def setup_method(self):
        from app.core import startup_guard

        startup_guard.system_ready = False
        startup_guard._readiness_reason = "startup_in_progress"

    def teardown_method(self):
        from app.core import startup_guard

        startup_guard.system_ready = False
        startup_guard._readiness_reason = "startup_in_progress"
        # Restore RUNTIME_MODE if it was changed
        os.environ.pop("RUNTIME_MODE", None)

    def test_test_mode_sets_ready_immediately(self):
        """run_startup_guard() should set system_ready=True immediately in test mode."""
        import asyncio

        from app.core import startup_guard

        os.environ["RUNTIME_MODE"] = "test"

        asyncio.run(startup_guard.run_startup_guard())

        assert startup_guard.system_ready is True
        assert startup_guard._readiness_reason == "test_mode"

    def test_test_mode_skips_all_validation(self):
        """In test mode, no external services should be contacted."""
        import asyncio

        from app.core import startup_guard

        os.environ["RUNTIME_MODE"] = "test"

        with patch("app.core.startup_guard.validate_config") as mock_val:
            mock_val.side_effect = RuntimeError("should not be called")
            asyncio.run(startup_guard.run_startup_guard())

        # validate_config should NOT be called in test mode
        mock_val.assert_not_called()
        assert startup_guard.system_ready is True


# ── Startup timeout fallback ──────────────────────────────────────────────────


class TestStartupTimeout:
    """Verify that run_startup_guard() times out and sets partial readiness."""

    def setup_method(self):
        from app.core import startup_guard

        startup_guard.system_ready = False
        startup_guard._readiness_reason = "startup_in_progress"

    def teardown_method(self):
        from app.core import startup_guard

        startup_guard.system_ready = False
        startup_guard._readiness_reason = "startup_in_progress"
        os.environ.pop("STARTUP_TIMEOUT_SECONDS", None)

    def test_timeout_sets_partial_ready(self):
        """When startup validation times out, system_ready becomes True with reason."""
        import asyncio

        import app.config as cfg
        from app.core import startup_guard

        # Force non-test mode and short timeout.
        # Both are read by run_startup_guard() from config module at call time.
        saved_mode = cfg.RUNTIME_MODE
        saved_timeout = cfg.STARTUP_TIMEOUT_SECONDS
        cfg.RUNTIME_MODE = "api"
        cfg.STARTUP_TIMEOUT_SECONDS = 2

        # Mock wait_for_db to hang (never return) so the 2-second timeout fires.
        async def _never_return(*args, **kwargs):
            await asyncio.Event().wait()  # hangs forever

        async def _run():
            with patch.object(startup_guard, "wait_for_db", _never_return):
                await startup_guard.run_startup_guard()

        try:
            asyncio.run(_run())
            assert startup_guard.system_ready is True, "system_ready should be True after timeout"
            assert startup_guard._readiness_reason == "partial_startup_timeout", (
                f"expected 'partial_startup_timeout', got '{startup_guard._readiness_reason}'"
            )
        finally:
            cfg.RUNTIME_MODE = saved_mode
            cfg.STARTUP_TIMEOUT_SECONDS = saved_timeout
