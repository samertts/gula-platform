"""Tests for the 3 elite improvements:
  1. State Persistence — sliding window persist/restore via Redis
  2. Cross-Layer Correlation — user_id + lab_id ContextVars
  3. Controlled Degradation Levels — DegradationLevel enum + middleware
"""
import os
import sys
import threading
import time

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_elite.db")
os.environ.setdefault("SECRET_KEY", "test-secret-for-elite-tests")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# 1. State Persistence
# =============================================================================

class TestSlidingWindowPersistence:

    def _make_window(self):
        from app.database import _SlidingWindow
        return _SlidingWindow(max_age_s=300, max_size=500)

    def test_persist_to_redis_calls_set(self):
        w = self._make_window()
        w.record("refused")
        w.record("ok")
        redis = MagicMock()
        w.persist_to_redis(redis, key="test:window")
        redis.set.assert_called_once()
        call_key, call_val = redis.set.call_args[0]
        assert call_key == "test:window"
        import json
        events = json.loads(call_val)
        assert len(events) == 2
        types = {e[1] for e in events}
        assert types == {"refused", "ok"}

    def test_persist_sets_ttl(self):
        w = self._make_window()
        w.record("timeout")
        redis = MagicMock()
        w.persist_to_redis(redis, key="test:window")
        _, kwargs = redis.set.call_args
        assert "ex" in kwargs
        assert kwargs["ex"] >= 300  # at least max_age_s

    def test_persist_swallows_redis_error(self):
        w = self._make_window()
        w.record("refused")
        redis = MagicMock()
        redis.set.side_effect = Exception("Redis down")
        # Must not raise
        w.persist_to_redis(redis)

    def test_restore_from_redis_loads_events(self):
        # Create source window, record events, persist
        src = self._make_window()
        src.record("refused")
        src.record("refused")
        src.record("ok")
        redis = MagicMock()
        import json
        src.persist_to_redis(redis)
        persisted_payload = redis.set.call_args[0][1]
        # Now restore into a fresh window
        redis.get.return_value = persisted_payload
        dst = self._make_window()
        dst.restore_from_redis(redis)
        assert dst.count("refused") == 2
        assert dst.count("ok")      == 1

    def test_restore_noop_on_redis_none(self):
        w = self._make_window()
        redis = MagicMock()
        redis.get.return_value = None
        w.restore_from_redis(redis)  # should not raise
        assert w.count("refused") == 0

    def test_restore_swallows_redis_error(self):
        w = self._make_window()
        redis = MagicMock()
        redis.get.side_effect = Exception("Redis gone")
        w.restore_from_redis(redis)  # must not raise

    def test_restore_skips_expired_events(self):
        """Events older than max_age_s must be dropped on restore."""
        import json
        w = self._make_window()
        redis = MagicMock()
        # Craft a payload with a wall-clock timestamp from 600s ago (outside 300s window)
        old_wall_ts = time.time() - 600
        redis.get.return_value = json.dumps([[old_wall_ts, "refused"]])
        w.restore_from_redis(redis)
        assert w.count("refused") == 0  # expired — should not be loaded

    def test_restore_db_window_from_redis_helper(self):
        """Public helper must call restore_from_redis on db_window."""
        from app.database import db_window, restore_db_window_from_redis
        mock_cache = MagicMock()
        mock_cache.get.return_value = None  # empty Redis
        with patch("app.security.redis_client.cache", mock_cache):
            restore_db_window_from_redis()  # must not raise

    def test_persist_db_window_to_redis_helper(self):
        """Public helper must call persist_to_redis on db_window."""
        from app.database import persist_db_window_to_redis
        mock_cache = MagicMock()
        with patch("app.security.redis_client.cache", mock_cache):
            persist_db_window_to_redis()
        mock_cache.set.assert_called_once()


# =============================================================================
# 2. Cross-Layer Correlation ContextVars
# =============================================================================

class TestCorrelationContextVars:

    def test_user_id_var_exists_with_none_default(self):
        from app.database import _user_id_var
        assert _user_id_var.get(None) is None

    def test_lab_id_var_exists_with_none_default(self):
        from app.database import _lab_id_var
        assert _lab_id_var.get(None) is None

    def test_user_id_set_and_reset(self):
        from app.database import _user_id_var
        token = _user_id_var.set(42)
        assert _user_id_var.get(None) == 42
        _user_id_var.reset(token)
        assert _user_id_var.get(None) is None

    def test_lab_id_set_and_reset(self):
        from app.database import _lab_id_var
        token = _lab_id_var.set(7)
        assert _lab_id_var.get(None) == 7
        _lab_id_var.reset(token)
        assert _lab_id_var.get(None) is None

    def test_user_lab_isolated_between_threads(self):
        from app.database import _lab_id_var, _user_id_var
        results = {}

        def thread_a():
            t1 = _user_id_var.set(100)
            t2 = _lab_id_var.set(200)
            time.sleep(0.05)
            results["a_user"] = _user_id_var.get(None)
            results["a_lab"]  = _lab_id_var.get(None)
            _user_id_var.reset(t1)
            _lab_id_var.reset(t2)

        def thread_b():
            time.sleep(0.02)
            results["b_user"] = _user_id_var.get(None)
            results["b_lab"]  = _lab_id_var.get(None)

        ta = threading.Thread(target=thread_a)
        tb = threading.Thread(target=thread_b)
        ta.start()
        tb.start()
        ta.join()
        tb.join()

        assert results["a_user"] == 100
        assert results["a_lab"]  == 200
        assert results["b_user"] is None  # thread B sees default
        assert results["b_lab"]  is None

    def test_all_four_vars_independent(self):
        from app.database import _endpoint_var, _lab_id_var, _request_id_var, _user_id_var
        t1 = _request_id_var.set("req-xyz")
        t2 = _endpoint_var.set("/api/orders")
        t3 = _user_id_var.set(5)
        t4 = _lab_id_var.set(9)
        assert _request_id_var.get("") == "req-xyz"
        assert _endpoint_var.get("")   == "/api/orders"
        assert _user_id_var.get(None)  == 5
        assert _lab_id_var.get(None)   == 9
        _request_id_var.reset(t1)
        _endpoint_var.reset(t2)
        _user_id_var.reset(t3)
        _lab_id_var.reset(t4)
        assert _user_id_var.get(None) is None
        assert _lab_id_var.get(None)  is None


# =============================================================================
# 3. Controlled Degradation Levels
# =============================================================================

class TestDegradationLevel:

    def test_enum_values_ordered(self):
        from app.core.self_healing import DegradationLevel
        assert DegradationLevel.NONE.value            == 0
        assert DegradationLevel.L1_CACHE_HEAVY.value  == 1
        assert DegradationLevel.L2_READ_ONLY.value    == 2
        assert DegradationLevel.L3_CRITICAL_ONLY.value == 3

    def test_none_less_than_all_levels(self):
        from app.core.self_healing import DegradationLevel
        for level in (DegradationLevel.L1_CACHE_HEAVY,
                      DegradationLevel.L2_READ_ONLY,
                      DegradationLevel.L3_CRITICAL_ONLY):
            assert DegradationLevel.NONE.value < level.value


class TestSystemHealthDegradationLevel:

    def _fresh_health(self):
        """Return a fresh SystemHealth-like object (bypass singleton for testing)."""
        from app.core.self_healing import DegradationLevel, SystemHealth
        h = object.__new__(SystemHealth)
        h._init()
        return h

    def test_initial_level_is_none(self):
        from app.core.self_healing import DegradationLevel
        h = self._fresh_health()
        assert h.degradation_level == DegradationLevel.NONE
        assert h.degraded is False

    def test_enter_l2_sets_degraded_true(self):
        from app.core.self_healing import DegradationLevel
        h = self._fresh_health()
        h.enter_degraded_mode("test", DegradationLevel.L2_READ_ONLY)
        assert h.degraded is True
        assert h.degradation_level == DegradationLevel.L2_READ_ONLY

    def test_enter_l3_escalates_from_l2(self):
        from app.core.self_healing import DegradationLevel
        h = self._fresh_health()
        h.enter_degraded_mode("first", DegradationLevel.L2_READ_ONLY)
        h.enter_degraded_mode("storm", DegradationLevel.L3_CRITICAL_ONLY)
        assert h.degradation_level == DegradationLevel.L3_CRITICAL_ONLY

    def test_cannot_downgrade_during_incident(self):
        """L3 must never drop back to L2 without explicit exit."""
        from app.core.self_healing import DegradationLevel
        h = self._fresh_health()
        h.enter_degraded_mode("storm",  DegradationLevel.L3_CRITICAL_ONLY)
        h.enter_degraded_mode("slight", DegradationLevel.L2_READ_ONLY)  # should be ignored
        assert h.degradation_level == DegradationLevel.L3_CRITICAL_ONLY

    def test_exit_resets_to_none(self):
        from app.core.self_healing import DegradationLevel
        h = self._fresh_health()
        h.enter_degraded_mode("test", DegradationLevel.L2_READ_ONLY)
        h.exit_degraded_mode()
        assert h.degradation_level == DegradationLevel.NONE
        assert h.degraded is False

    def test_to_dict_includes_level_name(self):
        from app.core.self_healing import DegradationLevel
        h = self._fresh_health()
        h.enter_degraded_mode("test", DegradationLevel.L2_READ_ONLY)
        d = h.to_dict()
        assert d["degradation_level"] == "L2_READ_ONLY"
        assert d["degradation_value"] == 2
        assert d["degraded_mode"] is True

    def test_default_enter_level_is_l2(self):
        from app.core.self_healing import DegradationLevel
        h = self._fresh_health()
        h.enter_degraded_mode("no level arg")
        assert h.degradation_level == DegradationLevel.L2_READ_ONLY


class TestDegradedModeMiddleware:
    """Test level-based request filtering without running a live server."""

    def _make_request(self, method: str, path: str) -> MagicMock:
        req = MagicMock()
        req.url.path = path
        req.method   = method
        return req

    async def _dispatch(self, health_mock, method, path):
        """Helper — runs middleware dispatch with a mocked health singleton."""
        from app.core.self_healing import DegradedModeMiddleware
        mw = DegradedModeMiddleware(app=MagicMock())
        req = self._make_request(method, path)
        passed_through = []

        async def call_next(_req):
            passed_through.append(True)
            resp = MagicMock()
            resp.headers = {}
            return resp

        with patch("app.core.self_healing.health", health_mock):
            result = await mw.dispatch(req, call_next)
        return result, passed_through

    @pytest.mark.asyncio
    async def test_none_level_passes_all(self):
        from app.core.self_healing import DegradationLevel, SystemHealth
        h = object.__new__(SystemHealth)
        h._init()
        assert h.degradation_level == DegradationLevel.NONE
        _resp, passed = await self._dispatch(h, "POST", "/api/orders")
        assert passed  # passed through

    @pytest.mark.asyncio
    async def test_l2_blocks_post(self):
        from app.core.self_healing import DegradationLevel, SystemHealth
        h = object.__new__(SystemHealth)
        h._init()
        h.enter_degraded_mode("test", DegradationLevel.L2_READ_ONLY)
        resp, passed = await self._dispatch(h, "POST", "/api/orders")
        assert not passed
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_l2_allows_get(self):
        from app.core.self_healing import DegradationLevel, SystemHealth
        h = object.__new__(SystemHealth)
        h._init()
        h.enter_degraded_mode("test", DegradationLevel.L2_READ_ONLY)
        _resp, passed = await self._dispatch(h, "GET", "/api/patients")
        assert passed  # GET passes in L2

    @pytest.mark.asyncio
    async def test_l3_blocks_get_on_non_critical(self):
        from app.core.self_healing import DegradationLevel, SystemHealth
        h = object.__new__(SystemHealth)
        h._init()
        h.enter_degraded_mode("storm", DegradationLevel.L3_CRITICAL_ONLY)
        resp, passed = await self._dispatch(h, "GET", "/api/patients")
        assert not passed
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_l3_allows_health(self):
        from app.core.self_healing import DegradationLevel, SystemHealth
        h = object.__new__(SystemHealth)
        h._init()
        h.enter_degraded_mode("storm", DegradationLevel.L3_CRITICAL_ONLY)
        _resp, passed = await self._dispatch(h, "GET", "/health")
        assert passed  # /health is in _ALWAYS_ALLOWED

    @pytest.mark.asyncio
    async def test_l3_allows_auth_login(self):
        from app.core.self_healing import DegradationLevel, SystemHealth
        h = object.__new__(SystemHealth)
        h._init()
        h.enter_degraded_mode("storm", DegradationLevel.L3_CRITICAL_ONLY)
        _resp, passed = await self._dispatch(h, "POST", "/auth/login")
        assert passed  # /auth/login is in _CRITICAL_PATHS

    @pytest.mark.asyncio
    async def test_l3_allows_kill_switch_deactivate(self):
        from app.core.self_healing import DegradationLevel, SystemHealth
        h = object.__new__(SystemHealth)
        h._init()
        h.enter_degraded_mode("storm", DegradationLevel.L3_CRITICAL_ONLY)
        _resp, passed = await self._dispatch(h, "POST", "/admin/kill-switch/deactivate")
        assert passed  # operator recovery path must always work

    @pytest.mark.asyncio
    async def test_l2_response_includes_level_name(self):
        from app.core.self_healing import DegradationLevel, SystemHealth
        h = object.__new__(SystemHealth)
        h._init()
        h.enter_degraded_mode("test", DegradationLevel.L2_READ_ONLY)
        resp, _ = await self._dispatch(h, "DELETE", "/api/orders/1")
        assert resp.status_code == 503
        body = resp.body
        assert b"L2_READ_ONLY" in body

    @pytest.mark.asyncio
    async def test_l1_passes_writes_with_header(self):
        from app.core.self_healing import DegradationLevel, SystemHealth
        h = object.__new__(SystemHealth)
        h._init()
        h.enter_degraded_mode("pressure", DegradationLevel.L1_CACHE_HEAVY)
        _resp, passed = await self._dispatch(h, "POST", "/api/orders")
        assert passed  # L1 allows writes


class TestTriggerFunctionsUseLevels:

    def test_trigger_circuit_open_uses_l2(self):
        from app.core.self_healing import DegradationLevel
        from app.database import _trigger_circuit_open
        mock_health = MagicMock()
        from app.core.self_healing import CircuitState
        mock_health.db_circuit.state = CircuitState.CLOSED
        mock_health.db_circuit._failure_threshold = 3
        with patch("app.core.self_healing.health", mock_health):
            _trigger_circuit_open(25)
        mock_health.enter_degraded_mode.assert_called_once()
        _, kwargs = mock_health.enter_degraded_mode.call_args
        assert kwargs.get("level") == DegradationLevel.L2_READ_ONLY

    def test_trigger_system_degradation_uses_l3(self):
        from app.core.self_healing import DegradationLevel
        from app.database import _trigger_system_degradation
        mock_health = MagicMock()
        with patch("app.core.self_healing.health", mock_health):
            _trigger_system_degradation(55)
        mock_health.enter_degraded_mode.assert_called_once()
        _, kwargs = mock_health.enter_degraded_mode.call_args
        assert kwargs.get("level") == DegradationLevel.L3_CRITICAL_ONLY
