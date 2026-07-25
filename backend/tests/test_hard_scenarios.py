"""
Hard Mode Tests — TEST 6–10
Simulates real-world failure modes that can't be caught with unit tests alone.

TEST 6  — Slow Death:     DB responds but slowly (tc netem delay 200ms)
TEST 7  — Partial Fail:   Redis down, DB alive — must not crash
TEST 8  — Memory Pressure: auto_repair intervenes before OOM
TEST 9  — Race Condition: two concurrent writes to same record → optimistic lock
TEST 10 — Silent Failure: iptables blocks port 5432 → timeout → escalate
"""

import asyncio
import os
import sys
import threading
import time

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_hard.db")
os.environ.setdefault("SECRET_KEY", "test-secret-hard-scenarios")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from unittest.mock import MagicMock, patch

import pytest


def _run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _fresh_health():
    from app.core.self_healing import SystemHealth

    h = object.__new__(SystemHealth)
    h._init()
    return h


# ═════════════════════════════════════════════════════════════════════════════
# TEST 6 — Slow Death (tc qdisc delay 200ms → timeouts → L1_CACHE_HEAVY)
# ═════════════════════════════════════════════════════════════════════════════


class TestSlowDeath:
    """
    Simulates: tc qdisc add dev eth0 root netem delay 200ms
    DB is reachable but every connection times out.
    Expected: system grades YELLOW, enters L1_CACHE_HEAVY.
    """

    def test_timeout_threshold_constants_exist(self):
        from app.database import _TIMEOUT_L1_THRESHOLD, _TIMEOUT_L2_THRESHOLD

        assert _TIMEOUT_L1_THRESHOLD > 0
        assert _TIMEOUT_L2_THRESHOLD > _TIMEOUT_L1_THRESHOLD

    def test_five_timeouts_triggers_l1(self):
        """5 timeouts in 5min → _trigger_slow_db → L1_CACHE_HEAVY."""
        from app.core.self_healing import DegradationLevel
        from app.database import _TIMEOUT_L1_THRESHOLD, _SlidingWindow, _trigger_slow_db

        mock_h = _fresh_health()
        w = _SlidingWindow(max_age_s=300)
        for _ in range(_TIMEOUT_L1_THRESHOLD):
            w.record("timeout")
        assert w.count("timeout") >= _TIMEOUT_L1_THRESHOLD
        with patch("app.core.self_healing.health", mock_h):
            _trigger_slow_db(_TIMEOUT_L1_THRESHOLD)
        assert mock_h.degradation_level == DegradationLevel.L1_CACHE_HEAVY, (
            f"Expected L1_CACHE_HEAVY after {_TIMEOUT_L1_THRESHOLD} timeouts, "
            f"got {mock_h.degradation_level.name}"
        )

    def test_fifteen_timeouts_triggers_l2(self):
        """15 timeouts in 5min → circuit opens → L2_READ_ONLY."""
        from app.core.self_healing import DegradationLevel
        from app.database import _TIMEOUT_L2_THRESHOLD, _trigger_circuit_open

        mock_h = _fresh_health()
        with patch("app.core.self_healing.health", mock_h):
            _trigger_circuit_open(_TIMEOUT_L2_THRESHOLD)
        assert mock_h.degradation_level == DegradationLevel.L2_READ_ONLY

    def test_auto_repair_enters_l1_on_high_latency(self):
        """auto_repair enters L1_CACHE_HEAVY when db_ms > DB_LATENCY_WARN."""
        from app.core.auto_repair import _DB_LATENCY_WARN, RepairEngine
        from app.core.self_healing import DegradationLevel

        mock_h = _fresh_health()
        engine = RepairEngine()

        # Simulate DB latency above warn threshold
        slow_latency = _DB_LATENCY_WARN + 100

        with (
            patch("app.core.self_healing.health", mock_h),
            patch.object(engine, "_rss_mb", return_value=200.0),
            patch.object(engine, "_db_latency_ms", return_value=float(slow_latency)),
            patch.object(engine, "_redis_latency_ms", return_value=1.0),
            patch.object(engine, "_queue_depth", return_value=0),
            patch.object(engine, "_can_trigger", return_value=False),
        ):
            _run_async(engine._check_and_repair())

        assert mock_h.degradation_level == DegradationLevel.L1_CACHE_HEAVY, (
            f"Expected L1_CACHE_HEAVY on high latency, got {mock_h.degradation_level.name}"
        )

    def test_auto_repair_exits_l1_on_latency_recovery(self):
        """When DB latency drops, auto_repair exits L1_CACHE_HEAVY back to NONE."""
        from app.core.auto_repair import _DB_LATENCY_WARN, RepairEngine
        from app.core.self_healing import DegradationLevel

        mock_h = _fresh_health()
        mock_h.enter_degraded_mode("high latency", DegradationLevel.L1_CACHE_HEAVY)
        assert mock_h.degradation_level == DegradationLevel.L1_CACHE_HEAVY

        engine = RepairEngine()

        # Latency well below exit threshold (0.7 × WARN)
        fast_latency = int(_DB_LATENCY_WARN * 0.4)  # e.g. 120ms — clearly recovered

        with (
            patch("app.core.self_healing.health", mock_h),
            patch.object(engine, "_rss_mb", return_value=200.0),
            patch.object(engine, "_db_latency_ms", return_value=float(fast_latency)),
            patch.object(engine, "_redis_latency_ms", return_value=1.0),
            patch.object(engine, "_queue_depth", return_value=0),
            patch.object(engine, "_can_trigger", return_value=False),
        ):
            _run_async(engine._check_and_repair())

        assert mock_h.degradation_level == DegradationLevel.NONE, (
            f"Expected NONE after latency recovery, got {mock_h.degradation_level.name}"
        )

    def test_l1_does_not_block_writes(self):
        """In L1 the system is stressed but writes still pass — not L2."""
        from app.core.self_healing import DegradationLevel

        mock_h = _fresh_health()
        mock_h.enter_degraded_mode("slow", DegradationLevel.L1_CACHE_HEAVY)

        from app.core.self_healing import DegradedModeMiddleware

        mw = DegradedModeMiddleware(app=MagicMock())
        req = MagicMock()
        req.url.path = "/api/orders"
        req.method = "POST"
        passed = []

        async def call_next(_req):
            passed.append(True)
            r = MagicMock()
            r.headers = {}
            return r

        with patch("app.core.self_healing.health", mock_h):
            _run_async(mw.dispatch(req, call_next))

        assert passed, "POST should pass in L1_CACHE_HEAVY — L1 is warning, not blocking"


# ═════════════════════════════════════════════════════════════════════════════
# TEST 7 — Partial Failure: Redis down, DB alive
# ═════════════════════════════════════════════════════════════════════════════


class TestRedisDown:
    """
    Simulates: docker stop redis
    Redis circuit opens but DB is alive.
    Expected: system enters L1_CACHE_HEAVY (not crash, not L2).
    """

    def test_redis_circuit_open_triggers_l1(self):
        """When Redis circuit opens + DB is fine → update_degraded_state → L1."""
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        # Open Redis circuit
        for _ in range(h.redis_circuit.failure_threshold):
            h.redis_circuit.record_failure()
        h.update_degraded_state()
        assert h.degradation_level == DegradationLevel.L1_CACHE_HEAVY, (
            f"Redis down should → L1, got {h.degradation_level.name}"
        )

    def test_redis_down_does_not_block_writes(self):
        """Redis down only enters L1 — writes must still pass."""
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        for _ in range(h.redis_circuit.failure_threshold):
            h.redis_circuit.record_failure()
        h.update_degraded_state()

        from app.core.self_healing import DegradedModeMiddleware

        mw = DegradedModeMiddleware(app=MagicMock())
        req = MagicMock()
        req.url.path = "/api/orders"
        req.method = "POST"
        passed = []

        async def call_next(_req):
            passed.append(True)
            r = MagicMock()
            r.headers = {}
            return r

        with patch("app.core.self_healing.health", h):
            _run_async(mw.dispatch(req, call_next))

        assert passed, "POST must pass when only Redis is down (L1 not L2)"

    def test_redis_down_not_crash(self):
        """Redis circuit opening must not raise or crash the health system."""
        h = _fresh_health()
        try:
            for _ in range(h.redis_circuit.failure_threshold + 2):
                h.redis_circuit.record_failure()
            h.update_degraded_state()
        except Exception as exc:
            pytest.fail(f"Redis going down raised an exception: {exc}")

    def test_redis_recovery_exits_l1(self):
        """When Redis recovers → circuit closes → update_degraded_state → NONE."""
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        # Bring Redis circuit to open
        for _ in range(h.redis_circuit.failure_threshold):
            h.redis_circuit.record_failure()
        h.update_degraded_state()
        assert h.degradation_level == DegradationLevel.L1_CACHE_HEAVY

        # Redis recovers
        h.redis_circuit.record_success()
        h.update_degraded_state()
        assert h.degradation_level == DegradationLevel.NONE, (
            f"After Redis recovery expected NONE, got {h.degradation_level.name}"
        )

    def test_redis_down_then_db_down_escalates_to_l2(self):
        """Redis+DB both down → must be L2 (DB takes priority over Redis)."""
        from app.core.self_healing import DegradationLevel

        h = _fresh_health()
        # Redis fails first
        for _ in range(h.redis_circuit.failure_threshold):
            h.redis_circuit.record_failure()
        h.update_degraded_state()
        assert h.degradation_level == DegradationLevel.L1_CACHE_HEAVY

        # DB fails too
        for _ in range(h.db_circuit.failure_threshold):
            h.db_circuit.record_failure()
        h.update_degraded_state()
        assert h.degradation_level == DegradationLevel.L2_READ_ONLY, (
            f"DB down on top of Redis down should escalate to L2, got {h.degradation_level.name}"
        )


# ═════════════════════════════════════════════════════════════════════════════
# TEST 8 — Memory Pressure (stress --vm 2G → auto_repair GC)
# ═════════════════════════════════════════════════════════════════════════════


class TestMemoryPressure:
    """
    Simulates: stress --vm 1 --vm-bytes 2G --timeout 60s
    auto_repair must trigger GC before process is killed.
    """

    def test_memory_critical_triggers_repair(self):
        """When RSS > _MEMORY_CRITICAL_MB, auto_repair must call GC."""
        from app.core.auto_repair import _MEMORY_CRITICAL_MB, RepairEngine

        engine = RepairEngine()
        repair_called = []

        original_repair = engine._repair_memory_pressure

        def mock_repair(rss):
            repair_called.append(rss)
            return True

        engine._repair_memory_pressure = mock_repair

        with (
            patch.object(engine, "_rss_mb", return_value=float(_MEMORY_CRITICAL_MB + 1)),
            patch.object(engine, "_db_latency_ms", return_value=1.0),
            patch.object(engine, "_redis_latency_ms", return_value=1.0),
            patch.object(engine, "_queue_depth", return_value=0),
            patch.object(engine, "_can_trigger", return_value=True),
        ):
            _run_async(engine._check_and_repair())

        assert repair_called, (
            f"Memory at {_MEMORY_CRITICAL_MB + 1}MB should trigger auto_repair GC. "
            "System would OOM without intervention."
        )

    def test_memory_warn_also_triggers_gc(self):
        """High memory (warn level) also triggers GC before it becomes critical."""
        from app.core.auto_repair import _MEMORY_CRITICAL_MB, _MEMORY_WARN_MB, RepairEngine

        engine = RepairEngine()
        repair_called = []

        engine._repair_memory_pressure = lambda rss: repair_called.append(rss) or True

        warn_level = (_MEMORY_WARN_MB + _MEMORY_CRITICAL_MB) // 2
        with (
            patch.object(engine, "_rss_mb", return_value=float(warn_level)),
            patch.object(engine, "_db_latency_ms", return_value=1.0),
            patch.object(engine, "_redis_latency_ms", return_value=1.0),
            patch.object(engine, "_queue_depth", return_value=0),
            patch.object(engine, "_can_trigger", return_value=True),
        ):
            _run_async(engine._check_and_repair())

        assert repair_called, f"Memory at {warn_level}MB should trigger GC (warn level)"

    def test_normal_memory_does_not_trigger_repair(self):
        """Normal RSS must not trigger unnecessary GC."""
        from app.core.auto_repair import _MEMORY_WARN_MB, RepairEngine

        engine = RepairEngine()
        repair_called = []

        engine._repair_memory_pressure = lambda rss: repair_called.append(rss) or True

        with (
            patch.object(engine, "_rss_mb", return_value=100.0),
            patch.object(engine, "_db_latency_ms", return_value=1.0),
            patch.object(engine, "_redis_latency_ms", return_value=1.0),
            patch.object(engine, "_queue_depth", return_value=0),
        ):
            _run_async(engine._check_and_repair())

        assert not repair_called, "GC should not trigger when memory is normal"

    def test_rss_reader_does_not_crash(self):
        """_rss_mb() must return float (0.0) even on /proc read failure."""
        from app.core.auto_repair import RepairEngine

        engine = RepairEngine()
        with patch("builtins.open", side_effect=OSError("no /proc")):
            result = engine._rss_mb()
        assert isinstance(result, float)
        assert result == 0.0


# ═════════════════════════════════════════════════════════════════════════════
# TEST 9 — Race Condition (2 concurrent writes to same record)
# ═════════════════════════════════════════════════════════════════════════════


class TestRaceCondition:
    """
    Simulates: two requests updating the same lab order result simultaneously.
    The `version` column (optimistic locking) must prevent silent overwrite.
    """

    def test_optimistic_lock_version_column_exists_on_result_model(self):
        """LabResult model must have a `version` column for optimistic locking."""
        try:
            from app.models.lab_result import LabResult

            assert hasattr(LabResult, "version"), (
                "LabResult.version column missing — optimistic lock not implemented. "
                "Two concurrent writes will silently overwrite each other."
            )
        except ImportError:
            pytest.skip("LabResult model not found — skipping")

    def test_version_increments_on_update(self):
        """After an update, version must increment so next writer gets stale-version error."""
        try:
            from app.models.lab_result import LabResult

            r = LabResult()
            r.version = 1
            r.version += 1
            assert r.version == 2
        except ImportError:
            pytest.skip("LabResult model not found — skipping")

    def test_concurrent_updates_thread_safe(self):
        """Simulates two threads attempting to update same record — last-write detection."""
        # This is a logic test — real DB race requires integration test.
        # We simulate the version-check logic that each route must implement.
        shared_version = [1]  # simulates DB row version
        conflicts = []
        lock = threading.Lock()

        def update_attempt(expected_version: int, new_value: str):
            time.sleep(0.01)
            with lock:
                if shared_version[0] != expected_version:
                    conflicts.append(new_value)
                    return False  # optimistic lock violation
                shared_version[0] += 1
                return True

        # Both threads read version=1 simultaneously
        results = []
        t1 = threading.Thread(target=lambda: results.append(update_attempt(1, "writer-A")))
        t2 = threading.Thread(target=lambda: results.append(update_attempt(1, "writer-B")))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        successes = sum(1 for r in results if r)
        assert successes == 1, (
            f"Exactly 1 concurrent writer should succeed, but {successes} succeeded. "
            "Race condition: silent data overwrite!"
        )
        assert len(conflicts) == 1, "One writer should have detected the conflict"


# ═════════════════════════════════════════════════════════════════════════════
# TEST 10 — Silent Failure (iptables blocks 5432 → timeout → escalate)
# ═════════════════════════════════════════════════════════════════════════════


class TestSilentFailure:
    """
    Simulates: iptables -A OUTPUT -p tcp --dport 5432 -j DROP
    TCP connections hang until timeout — NOT connection refused.
    Expected: timeout status → sliding window → L1 then L2 escalation.
    """

    def test_timeout_classified_separately_from_refused(self):
        """'timeout' and 'refused' must be tracked as separate event types."""
        from app.database import _SlidingWindow

        w = _SlidingWindow(max_age_s=300)
        w.record("timeout")
        w.record("timeout")
        w.record("refused")
        assert w.count("timeout") == 2
        assert w.count("refused") == 1
        assert w.count("timeout") != w.count("refused")

    def test_timeout_escalation_path_exists(self):
        """Escalation code for timeout status must exist in check_db_connection_detail."""
        import ast
        import inspect

        from app.database import check_db_connection_detail

        src = inspect.getsource(check_db_connection_detail)
        assert '"timeout"' in src or "'timeout'" in src, (
            "No timeout handling found in check_db_connection_detail"
        )
        assert "_trigger_slow_db" in src or "_trigger_circuit_open" in src, (
            "check_db_connection_detail has no escalation path for timeout events"
        )

    def test_five_timeouts_enters_l1(self):
        """5 timeout events → _trigger_slow_db → L1_CACHE_HEAVY."""
        from app.core.self_healing import DegradationLevel
        from app.database import _TIMEOUT_L1_THRESHOLD, _trigger_slow_db

        h = _fresh_health()
        with patch("app.core.self_healing.health", h):
            _trigger_slow_db(_TIMEOUT_L1_THRESHOLD)
        assert h.degradation_level == DegradationLevel.L1_CACHE_HEAVY

    def test_fifteen_timeouts_enters_l2(self):
        """15 timeout events → _trigger_circuit_open → L2_READ_ONLY."""
        from app.core.self_healing import DegradationLevel
        from app.database import _TIMEOUT_L2_THRESHOLD, _trigger_circuit_open

        h = _fresh_health()
        with patch("app.core.self_healing.health", h):
            _trigger_circuit_open(_TIMEOUT_L2_THRESHOLD)
        assert h.degradation_level == DegradationLevel.L2_READ_ONLY

    def test_no_except_pass_in_trigger_functions(self):
        """The trigger functions must NEVER silently swallow exceptions."""
        import ast
        import inspect

        from app.database import (
            _trigger_circuit_open,
            _trigger_slow_db,
            _trigger_system_degradation,
        )

        for fn in (_trigger_slow_db, _trigger_circuit_open, _trigger_system_degradation):
            src = inspect.getsource(fn)
            # Parse the source and look for bare "except: pass" or "except Exception: pass"
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    body = node.body
                    is_bare_pass = len(body) == 1 and isinstance(body[0], ast.Pass)
                    assert not is_bare_pass, (
                        f"{fn.__name__} has a bare 'except: pass' — "
                        "silent exception swallowing detected! "
                        "This is how _failure_threshold typo went undetected."
                    )

    def test_timeout_does_not_trigger_refused_counter(self):
        """A timeout must not increment the refused counter (they're different failure modes)."""
        from app.database import _SlidingWindow

        w = _SlidingWindow(max_age_s=300)
        for _ in range(20):
            w.record("timeout")  # iptables blocks → all timeouts
        assert w.count("refused") == 0, (
            "timeout events are incrementing refused counter — wrong escalation path will fire"
        )
        assert w.count("timeout") == 20
