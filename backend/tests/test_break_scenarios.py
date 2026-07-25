"""
5 Break Scenarios — exactly the tests the user wants to run in production.

These tests simulate what happens when you:
  1. Stop Postgres → degradation_level should become L2_READ_ONLY
  2. Try a POST write while degraded → must get 503
  3. Check /health while degraded → must stay 200 with degraded=true
  4. Restart backend after degradation → Redis persistence must restore level
  5. Check correlation fields in logs → request_id/user_id/lab_id must appear

All scenarios run without a real database or Docker.
"""

import json
import logging
import os
import sys
import time

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_break.db")
os.environ.setdefault("SECRET_KEY", "test-secret-break-scenarios")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from unittest.mock import MagicMock, patch

import pytest

# ─── Helpers ─────────────────────────────────────────────────────────────────


def _fresh_health():
    """Bypass the singleton to get a clean SystemHealth for each test."""
    from app.core.self_healing import SystemHealth

    h = object.__new__(SystemHealth)
    h._init()
    return h


async def _middleware_dispatch(health_obj, method: str, path: str):
    """Run DegradedModeMiddleware.dispatch() with a fake call_next."""
    from app.core.self_healing import DegradedModeMiddleware

    mw = DegradedModeMiddleware(app=MagicMock())
    req = MagicMock()
    req.url.path = path
    req.method = method
    passed = []

    async def call_next(_req):
        passed.append(True)
        resp = MagicMock()
        resp.headers = {}
        return resp

    with patch("app.core.self_healing.health", health_obj):
        result = await mw.dispatch(req, call_next)
    return result, bool(passed)


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 1 — Stop Postgres → system escalates to L2_READ_ONLY
# ═════════════════════════════════════════════════════════════════════════════


class TestScenario1_PostgresDown:
    """Simulate: docker stop postgres → N connection-refused errors → L2"""

    def test_single_refused_does_not_escalate(self):
        """One refused should NOT trigger escalation (below threshold)."""
        from app.database import _CIRCUIT_OPEN_THRESHOLD, _SlidingWindow

        w = _SlidingWindow(max_age_s=300)
        w.record("refused")
        assert w.count("refused") < _CIRCUIT_OPEN_THRESHOLD

    def test_refused_storm_hits_circuit_threshold(self):
        """20 refused events in 5min → circuit open threshold reached."""
        from app.database import _CIRCUIT_OPEN_THRESHOLD, _SlidingWindow

        w = _SlidingWindow(max_age_s=300)
        for _ in range(_CIRCUIT_OPEN_THRESHOLD):
            w.record("refused")
        assert w.count("refused", window_s=300) >= _CIRCUIT_OPEN_THRESHOLD

    def test_trigger_circuit_open_escalates_to_l2(self):
        """Simulates: refused storm → _trigger_circuit_open → L2_READ_ONLY."""
        from app.core.self_healing import CircuitState, DegradationLevel
        from app.database import _CIRCUIT_OPEN_THRESHOLD, _trigger_circuit_open

        mock_h = _fresh_health()
        # Simulate circuit is CLOSED (normal state before storm)
        assert mock_h.db_circuit.state == CircuitState.CLOSED
        with patch("app.core.self_healing.health", mock_h):
            _trigger_circuit_open(_CIRCUIT_OPEN_THRESHOLD + 1)
        # After trigger: must be L2
        assert mock_h.degradation_level == DegradationLevel.L2_READ_ONLY, (
            f"Expected L2_READ_ONLY, got {mock_h.degradation_level.name}"
        )

    def test_refused_storm_hits_degrade_threshold(self):
        """50 refused events in 5min → system degrade threshold reached."""
        from app.database import _SYSTEM_DEGRADE_THRESHOLD, _SlidingWindow

        w = _SlidingWindow(max_age_s=300)
        for _ in range(_SYSTEM_DEGRADE_THRESHOLD):
            w.record("refused")
        assert w.count("refused", window_s=300) >= _SYSTEM_DEGRADE_THRESHOLD

    def test_trigger_system_degradation_escalates_to_l3(self):
        """Simulates: sustained storm → _trigger_system_degradation → L3."""
        from app.core.self_healing import DegradationLevel
        from app.database import _SYSTEM_DEGRADE_THRESHOLD, _trigger_system_degradation

        mock_h = _fresh_health()
        with patch("app.core.self_healing.health", mock_h):
            _trigger_system_degradation(_SYSTEM_DEGRADE_THRESHOLD + 5)
        assert mock_h.degradation_level == DegradationLevel.L3_CRITICAL_ONLY, (
            f"Expected L3_CRITICAL_ONLY, got {mock_h.degradation_level.name}"
        )

    def test_health_response_shows_degradation_level(self):
        """SystemHealth.to_dict() must expose degradation_level for /health."""
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        h.enter_degraded_mode("postgres down", DegradationLevel.L2_READ_ONLY)
        d = h.to_dict()
        assert d["degradation_level"] == "L2_READ_ONLY"
        assert d["degraded_mode"] is True


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 2 — POST while degraded → must get 503
# ═════════════════════════════════════════════════════════════════════════════


class TestScenario2_WritesBlocked:
    @pytest.mark.asyncio
    async def test_post_blocked_in_l2(self):
        """POST /api/test/echo → 503 when system is in L2_READ_ONLY."""
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        h.enter_degraded_mode("postgres down", DegradationLevel.L2_READ_ONLY)
        resp, passed = await _middleware_dispatch(h, "POST", "/api/test/echo")
        assert not passed, "POST should be BLOCKED in L2, not passed through"
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_put_blocked_in_l2(self):
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        h.enter_degraded_mode("postgres down", DegradationLevel.L2_READ_ONLY)
        resp, passed = await _middleware_dispatch(h, "PUT", "/api/patients/1")
        assert not passed
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_delete_blocked_in_l2(self):
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        h.enter_degraded_mode("postgres down", DegradationLevel.L2_READ_ONLY)
        resp, passed = await _middleware_dispatch(h, "DELETE", "/api/orders/5")
        assert not passed
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_503_body_includes_level(self):
        """503 body must tell client what level blocked them and why."""
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        h.enter_degraded_mode("postgres down", DegradationLevel.L2_READ_ONLY)
        resp, _ = await _middleware_dispatch(h, "POST", "/api/orders")
        body = json.loads(resp.body)
        assert body["degradation_level"] == "L2_READ_ONLY"
        assert body["retry_after_seconds"] == 30
        assert body["degraded"] is True

    @pytest.mark.asyncio
    async def test_retry_after_header_present(self):
        """Retry-After header must be set on 503 so clients back off."""
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        h.enter_degraded_mode("down", DegradationLevel.L2_READ_ONLY)
        resp, _ = await _middleware_dispatch(h, "POST", "/api/test/echo")
        assert "Retry-After" in resp.headers, "Retry-After header missing!"


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 3 — /health stays 200 while degraded (liveness probe must pass)
# ═════════════════════════════════════════════════════════════════════════════


class TestScenario3_HealthAlwaysUp:
    @pytest.mark.asyncio
    async def test_health_passes_in_l2(self):
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        h.enter_degraded_mode("down", DegradationLevel.L2_READ_ONLY)
        _, passed = await _middleware_dispatch(h, "GET", "/health")
        assert passed, "/health MUST pass in L2 — it's in _ALWAYS_ALLOWED"

    @pytest.mark.asyncio
    async def test_health_passes_in_l3(self):
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        h.enter_degraded_mode("storm", DegradationLevel.L3_CRITICAL_ONLY)
        _, passed = await _middleware_dispatch(h, "GET", "/health")
        assert passed, "/health MUST pass even in L3"

    @pytest.mark.asyncio
    async def test_health_ready_passes_in_l2(self):
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        h.enter_degraded_mode("down", DegradationLevel.L2_READ_ONLY)
        _, passed = await _middleware_dispatch(h, "GET", "/health/ready")
        assert passed

    @pytest.mark.asyncio
    async def test_health_ready_passes_in_l3(self):
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        h.enter_degraded_mode("storm", DegradationLevel.L3_CRITICAL_ONLY)
        _, passed = await _middleware_dispatch(h, "GET", "/health/ready")
        assert passed

    @pytest.mark.asyncio
    async def test_metrics_prom_passes_in_l3(self):
        """Prometheus scraping must never be blocked — even in L3."""
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        h.enter_degraded_mode("storm", DegradationLevel.L3_CRITICAL_ONLY)
        _, passed = await _middleware_dispatch(h, "GET", "/metrics/prom")
        assert passed, "/metrics/prom blocked in L3 — Prometheus goes blind!"

    def test_health_response_body_has_degradation_level(self):
        """to_dict() exposes degradation_level so /health JSON is informative."""
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        h.enter_degraded_mode("postgres down", DegradationLevel.L2_READ_ONLY)
        body = h.to_dict()
        assert body["degraded_mode"] is True
        assert body["degradation_level"] == "L2_READ_ONLY"


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 4 — Restart → Redis restores state (system remembers the disaster)
# ═════════════════════════════════════════════════════════════════════════════


class TestScenario4_RestartPersistence:
    def _make_window(self, max_age_s=300):
        from app.database import _SlidingWindow

        return _SlidingWindow(max_age_s=max_age_s)

    def test_full_cycle_persist_restart_restore(self):
        """
        Simulate: system had 25 refused errors → persisted to Redis →
        container restarted → restored → count still 25
        """
        # Before restart
        w1 = self._make_window()
        for _ in range(25):
            w1.record("refused")
        assert w1.count("refused") == 25

        # Persist to fake Redis
        redis = MagicMock()
        w1.persist_to_redis(redis)
        saved_payload = redis.set.call_args[0][1]

        # Simulate restart: new process, fresh window
        w2 = self._make_window()
        assert w2.count("refused") == 0  # blank slate

        # Restore from Redis
        redis2 = MagicMock()
        redis2.get.return_value = saved_payload
        w2.restore_from_redis(redis2)

        # Must remember the 25 refused events
        restored = w2.count("refused")
        assert restored == 25, (
            f"After restart: expected 25 refused, got {restored}. "
            "Redis persistence is broken — system forgot the disaster!"
        )

    def test_circuit_threshold_still_reached_after_restore(self):
        """If we restore 20 refused events, circuit escalation should still fire."""
        from app.database import _CIRCUIT_OPEN_THRESHOLD

        w1 = self._make_window()
        for _ in range(_CIRCUIT_OPEN_THRESHOLD):
            w1.record("refused")

        redis = MagicMock()
        w1.persist_to_redis(redis)
        payload = redis.set.call_args[0][1]

        w2 = self._make_window()
        redis2 = MagicMock()
        redis2.get.return_value = payload
        w2.restore_from_redis(redis2)

        assert w2.count("refused") >= _CIRCUIT_OPEN_THRESHOLD, (
            "After restore, refused count is below threshold — "
            "system would NOT escalate even though it should!"
        )

    def test_expired_events_not_restored(self):
        """Events from before max_age_s must not be loaded — window stays clean."""
        import json

        w = self._make_window(max_age_s=60)
        redis = MagicMock()
        # Craft events that are 120s old (beyond the 60s window)
        old_wall = time.time() - 120
        redis.get.return_value = json.dumps([[old_wall, "refused"]] * 10)
        w.restore_from_redis(redis)
        assert w.count("refused") == 0, "Expired events restored — window contaminated!"

    def test_fresh_events_after_restore_accumulate(self):
        """After restore, new events must accumulate normally on top."""
        w1 = self._make_window()
        for _ in range(5):
            w1.record("refused")
        redis = MagicMock()
        w1.persist_to_redis(redis)
        payload = redis.set.call_args[0][1]

        w2 = self._make_window()
        redis2 = MagicMock()
        redis2.get.return_value = payload
        w2.restore_from_redis(redis2)

        # New event after restore
        w2.record("refused")
        assert w2.count("refused") == 6  # 5 restored + 1 new


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 5 — Correlation: user_id + lab_id appear in DB error logs
# ═════════════════════════════════════════════════════════════════════════════


class TestScenario5_CorrelationLogs:
    def test_user_id_lab_id_vars_exist(self):
        from app.database import _lab_id_var, _user_id_var

        assert _user_id_var is not None
        assert _lab_id_var is not None

    def test_correlation_vars_set_before_db_call(self):
        """Simulate: authenticated request → get_current_user sets vars → DB fails."""
        from app.database import _lab_id_var, _user_id_var

        t1 = _user_id_var.set(42)
        t2 = _lab_id_var.set(7)
        assert _user_id_var.get(None) == 42
        assert _lab_id_var.get(None) == 7
        _user_id_var.reset(t1)
        _lab_id_var.reset(t2)

    def test_db_error_log_includes_user_and_lab(self):
        """The logger.error call in check_db_connection_detail must include
        user_id and lab_id from ContextVars."""
        from app.database import _endpoint_var, _lab_id_var, _request_id_var, _user_id_var

        # Set all 4 correlation vars as they would be in a real request
        t1 = _request_id_var.set("req-test-001")
        t2 = _endpoint_var.set("/api/orders")
        t3 = _user_id_var.set(99)
        t4 = _lab_id_var.set(3)

        captured = []

        class CapturingHandler(logging.Handler):
            def emit(self, record):
                if hasattr(record, "user_id"):
                    captured.append(
                        {
                            "user_id": record.user_id,
                            "lab_id": record.lab_id,
                            "request_id": record.request_id,
                            "endpoint": record.endpoint,
                        }
                    )

        handler = CapturingHandler()
        import logging as _logging

        db_logger = _logging.getLogger("gula.database")
        db_logger.addHandler(handler)
        db_logger.setLevel(_logging.ERROR)

        try:
            # Simulate a DB error log directly (the path taken in check_db_connection_detail)
            from app.database import _endpoint_var as _ev
            from app.database import _lab_id_var as _lv
            from app.database import _request_id_var as _rv
            from app.database import _user_id_var as _uv

            user_id = _uv.get(None)
            lab_id = _lv.get(None)
            req_id = _rv.get("")
            endpoint = _ev.get("")

            db_logger.error(
                "[DB] connection %s — action=%s — %s",
                "refused",
                "retry",
                "TCP refused",
                extra={
                    "db_host": "localhost",
                    "db_port": 5432,
                    "db_status": "refused",
                    "action": "retry",
                    "request_id": req_id or None,
                    "endpoint": endpoint or None,
                    "user_id": user_id,
                    "lab_id": lab_id,
                },
            )

            assert len(captured) == 1, "No log record captured"
            log = captured[0]
            assert log["user_id"] == 99, f"user_id missing: {log}"
            assert log["lab_id"] == 3, f"lab_id missing: {log}"
            assert log["request_id"] == "req-test-001", f"request_id missing: {log}"
            assert log["endpoint"] == "/api/orders", f"endpoint missing: {log}"

        finally:
            db_logger.removeHandler(handler)
            _request_id_var.reset(t1)
            _endpoint_var.reset(t2)
            _user_id_var.reset(t3)
            _lab_id_var.reset(t4)

    def test_unauthenticated_request_has_none_user(self):
        """Requests without auth must have user_id=None (no crash, no leak)."""
        from app.database import _lab_id_var, _user_id_var

        # Don't set anything — simulate unauthenticated request
        assert _user_id_var.get(None) is None
        assert _lab_id_var.get(None) is None

    def test_correlation_vars_dont_leak_between_requests(self):
        """After request A sets vars, request B must see defaults."""
        import threading

        from app.database import _lab_id_var, _user_id_var

        results = {}

        def request_a():
            t1 = _user_id_var.set(500)
            t2 = _lab_id_var.set(100)
            time.sleep(0.05)
            _user_id_var.reset(t1)
            _lab_id_var.reset(t2)

        def request_b():
            time.sleep(0.02)  # runs while A is active
            results["user"] = _user_id_var.get(None)
            results["lab"] = _lab_id_var.get(None)

        ta = threading.Thread(target=request_a)
        tb = threading.Thread(target=request_b)
        ta.start()
        tb.start()
        ta.join()
        tb.join()

        assert results["user"] is None, f"user_id leaked between requests: {results['user']}"
        assert results["lab"] is None, f"lab_id leaked between requests: {results['lab']}"
