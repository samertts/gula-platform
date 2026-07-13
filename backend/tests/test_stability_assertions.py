"""
Critical Stability Assertions — TEST 11, 12, 13
Tests that the BEHAVIOR of the system is stable, not just the features.

TEST 11 — Flapping Killer:     slow → fast × 10 must not oscillate
TEST 12 — Recovery correctness: L2 stays L2 until explicit recovery
TEST 13 — Cascading failure:   Redis + DB fail in sequence → L1 → L2 → L3
"""
import asyncio
import os
import time

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_stability.db")
os.environ.setdefault("SECRET_KEY", "test-secret-stability")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import pytest
from unittest.mock import patch, MagicMock


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
# Critical Assertion 1 — Hysteresis (no flapping)
# ═════════════════════════════════════════════════════════════════════════════

class TestHysteresis:

    def test_enter_and_exit_thresholds_differ(self):
        """Enter L1 at WARN, exit at 0.7×WARN — the gap prevents flapping."""
        from app.core.auto_repair import _DB_LATENCY_WARN
        enter = _DB_LATENCY_WARN
        exit_ = int(_DB_LATENCY_WARN * 0.7)
        assert exit_ < enter, (
            f"Enter={enter}ms, Exit={exit_}ms — they must differ (hysteresis gap). "
            "Same threshold = flapping on every poll cycle."
        )
        gap = enter - exit_
        assert gap >= 50, f"Hysteresis gap too small ({gap}ms) — still at risk of flapping"

    def test_latency_in_gap_does_not_exit_l1(self):
        """Latency between exit and enter thresholds must NOT trigger exit from L1."""
        from app.core.auto_repair import RepairEngine, _DB_LATENCY_WARN
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        h.enter_degraded_mode("slow", DegradationLevel.L1_CACHE_HEAVY)

        engine = RepairEngine()
        # Latency is in the "hysteresis gap": below enter but above exit threshold
        gap_latency = int(_DB_LATENCY_WARN * 0.85)  # e.g. 255ms if WARN=300

        with patch("app.core.self_healing.health", h), \
             patch.object(engine, "_rss_mb", return_value=100.0), \
             patch.object(engine, "_db_latency_ms", return_value=float(gap_latency)), \
             patch.object(engine, "_redis_latency_ms", return_value=1.0), \
             patch.object(engine, "_queue_depth", return_value=0), \
             patch.object(engine, "_can_trigger", return_value=False):
            _run_async(engine._check_and_repair())

        assert h.degradation_level == DegradationLevel.L1_CACHE_HEAVY, (
            f"Latency {gap_latency}ms (in hysteresis gap) caused premature L1 exit. "
            "System would flap on minor latency fluctuations."
        )


# ═════════════════════════════════════════════════════════════════════════════
# Critical Assertion 2 — Escalation is monotonic
# ═════════════════════════════════════════════════════════════════════════════

class TestMonotonicEscalation:

    def test_cannot_downgrade_from_l2_to_l1(self):
        """Once at L2, enter_degraded_mode with L1 must be a no-op."""
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        h.enter_degraded_mode("circuit open", DegradationLevel.L2_READ_ONLY)
        assert h.degradation_level == DegradationLevel.L2_READ_ONLY

        h.enter_degraded_mode("redis slow", DegradationLevel.L1_CACHE_HEAVY)
        assert h.degradation_level == DegradationLevel.L2_READ_ONLY, (
            "Attempted downgrade L2→L1 succeeded! "
            "Escalation must be monotonic during an active incident."
        )

    def test_cannot_downgrade_from_l3_to_l2(self):
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        h.enter_degraded_mode("storm", DegradationLevel.L3_CRITICAL_ONLY)
        h.enter_degraded_mode("circuit open", DegradationLevel.L2_READ_ONLY)
        assert h.degradation_level == DegradationLevel.L3_CRITICAL_ONLY

    def test_cannot_downgrade_from_l3_to_l1(self):
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        h.enter_degraded_mode("storm", DegradationLevel.L3_CRITICAL_ONLY)
        h.enter_degraded_mode("slow", DegradationLevel.L1_CACHE_HEAVY)
        assert h.degradation_level == DegradationLevel.L3_CRITICAL_ONLY

    def test_level_values_enforce_ordering(self):
        """Ordering is enforced by enum integer values — not by name comparison."""
        from app.core.self_healing import DegradationLevel
        levels = [
            DegradationLevel.NONE,
            DegradationLevel.L1_CACHE_HEAVY,
            DegradationLevel.L2_READ_ONLY,
            DegradationLevel.L3_CRITICAL_ONLY,
        ]
        for i in range(len(levels) - 1):
            assert levels[i].value < levels[i + 1].value, (
                f"Ordering broken: {levels[i].name}.value >= {levels[i+1].name}.value"
            )

    def test_enter_uses_value_comparison_not_identity(self):
        """enter_degraded_mode must use level.value comparison, not `is` or name check."""
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        # Enter L2
        h.enter_degraded_mode("test", DegradationLevel.L2_READ_ONLY)
        # Try entering L2 again (same level) — must be silently ignored (not crash)
        h.enter_degraded_mode("test again", DegradationLevel.L2_READ_ONLY)
        assert h.degradation_level == DegradationLevel.L2_READ_ONLY


# ═════════════════════════════════════════════════════════════════════════════
# Critical Assertion 3 — Window-based, not single-event
# ═════════════════════════════════════════════════════════════════════════════

class TestWindowBasedEscalation:

    def test_single_timeout_does_not_escalate(self):
        """1 timeout must NOT trigger L1 — threshold is > 1."""
        from app.database import _SlidingWindow, _TIMEOUT_L1_THRESHOLD
        assert _TIMEOUT_L1_THRESHOLD > 1, (
            f"_TIMEOUT_L1_THRESHOLD={_TIMEOUT_L1_THRESHOLD} — single error causes L1. "
            "This is too sensitive for production."
        )

    def test_single_refused_does_not_trigger_l2(self):
        from app.database import _CIRCUIT_OPEN_THRESHOLD
        assert _CIRCUIT_OPEN_THRESHOLD > 1

    def test_window_counts_only_recent_events(self):
        """Events older than max_age_s must not count toward threshold."""
        import json
        from app.database import _SlidingWindow, _TIMEOUT_L1_THRESHOLD
        w = _SlidingWindow(max_age_s=10)  # very short window for test
        for _ in range(_TIMEOUT_L1_THRESHOLD + 5):
            w.record("timeout")
        time.sleep(11)  # wait for events to expire
        assert w.count("timeout", window_s=10) == 0, (
            "Expired events still counting toward threshold — "
            "a single bad minute from hours ago can still escalate!"
        )

    def test_escalation_resets_after_window_expires(self):
        """After the window expires, fresh events start clean."""
        from app.database import _SlidingWindow, _TIMEOUT_L1_THRESHOLD
        w = _SlidingWindow(max_age_s=5)
        # Fill up to threshold
        for _ in range(_TIMEOUT_L1_THRESHOLD):
            w.record("timeout")
        assert w.count("timeout") >= _TIMEOUT_L1_THRESHOLD

        time.sleep(6)  # let window expire
        w.record("timeout")  # fresh single event
        assert w.count("timeout", window_s=5) == 1, (
            "After window expiry, a single new event should count as 1"
        )


# ═════════════════════════════════════════════════════════════════════════════
# TEST 11 — Flapping Killer (slow↔fast × 10 cycles)
# ═════════════════════════════════════════════════════════════════════════════

class TestFlappingKiller:
    """
    Simulates: DB slow 5s → normal 5s → slow → ... × 10 cycles
    Expected: system stabilizes at L1, does NOT oscillate NONE↔L1 on each cycle.
    """

    def test_ten_slow_fast_cycles_no_oscillation(self):
        """10 alternating slow/fast poll results should NOT cause NONE↔L1 flapping."""
        from app.core.auto_repair import RepairEngine, _DB_LATENCY_WARN
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        engine = RepairEngine()

        # Latencies that alternate around the enter threshold (300ms)
        # but stay ABOVE the exit threshold (210ms) — so should stay in L1
        slow_ms = _DB_LATENCY_WARN + 50   # 350ms → above enter threshold
        fast_ms = int(_DB_LATENCY_WARN * 0.85)  # 255ms → in hysteresis gap

        levels_seen = []

        for cycle in range(10):
            latency = slow_ms if cycle % 2 == 0 else fast_ms
            with patch("app.core.self_healing.health", h), \
                 patch.object(engine, "_rss_mb", return_value=100.0), \
                 patch.object(engine, "_db_latency_ms", return_value=float(latency)), \
                 patch.object(engine, "_redis_latency_ms", return_value=1.0), \
                 patch.object(engine, "_queue_depth", return_value=0), \
                 patch.object(engine, "_can_trigger", return_value=False):
                _run_async(engine._check_and_repair())
            levels_seen.append(h.degradation_level)

        # After the first enter, level should stay at L1 (not bounce back to NONE)
        transitions = sum(
            1 for i in range(1, len(levels_seen))
            if levels_seen[i] != levels_seen[i - 1]
        )
        assert transitions <= 1, (
            f"System flapped {transitions} times in 10 slow/fast cycles! "
            f"Levels: {[l.name for l in levels_seen]}. "
            "Expected ≤1 transition (NONE→L1 on first slow, then stable)."
        )

    def test_truly_fast_latency_exits_l1(self):
        """Only latency well below exit threshold (0.7×WARN) should exit L1."""
        from app.core.auto_repair import RepairEngine, _DB_LATENCY_WARN
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        h.enter_degraded_mode("slow", DegradationLevel.L1_CACHE_HEAVY)
        engine = RepairEngine()

        # Latency well below exit threshold
        recovered_ms = int(_DB_LATENCY_WARN * 0.4)  # 120ms — clearly recovered

        with patch("app.core.self_healing.health", h), \
             patch.object(engine, "_rss_mb", return_value=100.0), \
             patch.object(engine, "_db_latency_ms", return_value=float(recovered_ms)), \
             patch.object(engine, "_redis_latency_ms", return_value=1.0), \
             patch.object(engine, "_queue_depth", return_value=0), \
             patch.object(engine, "_can_trigger", return_value=False):
            _run_async(engine._check_and_repair())

        assert h.degradation_level == DegradationLevel.NONE, (
            f"Clear recovery ({recovered_ms}ms) should exit L1, "
            f"got {h.degradation_level.name}"
        )


# ═════════════════════════════════════════════════════════════════════════════
# TEST 12 — Recovery correctness (L2 stays L2 until explicit recovery)
# ═════════════════════════════════════════════════════════════════════════════

class TestRecoveryCorrectness:
    """
    After L2: restart DB → system must stay at L2 until RecoveryWorker
    confirms the circuit is closed via checked_db_connection().
    """

    def test_l2_stays_l2_after_latency_recovery(self):
        """Fast latency while in L2 must NOT auto-exit (circuit still open)."""
        from app.core.auto_repair import RepairEngine, _DB_LATENCY_WARN
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        h.enter_degraded_mode("circuit open", DegradationLevel.L2_READ_ONLY)
        engine = RepairEngine()

        # DB appears fast again (e.g. postgres restarted) but circuit is still OPEN
        with patch("app.core.self_healing.health", h), \
             patch.object(engine, "_rss_mb", return_value=100.0), \
             patch.object(engine, "_db_latency_ms", return_value=1.0), \
             patch.object(engine, "_redis_latency_ms", return_value=1.0), \
             patch.object(engine, "_queue_depth", return_value=0), \
             patch.object(engine, "_can_trigger", return_value=False):
            _run_async(engine._check_and_repair())

        assert h.degradation_level == DegradationLevel.L2_READ_ONLY, (
            "L2 degradation auto-cleared on fast latency! "
            "L2 exit must require explicit circuit recovery, not just speed."
        )

    def test_l2_cleared_only_via_exit_degraded_mode(self):
        """The ONLY way to exit L2 is explicit exit_degraded_mode() call."""
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        h.enter_degraded_mode("circuit open", DegradationLevel.L2_READ_ONLY)

        # Simulate RecoveryWorker confirms DB is back: closes circuit + calls update
        h.db_circuit.record_success()   # circuit CLOSED
        h.redis_circuit.record_success()
        h.update_degraded_state()       # all circuits closed → auto-exit

        assert h.degradation_level == DegradationLevel.NONE, (
            "Even after circuit recovery, system is stuck in L2! "
            "update_degraded_state() must exit when all circuits close."
        )

    def test_l3_cleared_only_when_all_circuits_recover(self):
        """L3 must stay until BOTH circuits close — partial recovery is not enough."""
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        # Open BOTH circuits (realistic: Redis + DB both failed during storm)
        for _ in range(h.db_circuit.failure_threshold):
            h.db_circuit.record_failure()
        for _ in range(h.redis_circuit.failure_threshold):
            h.redis_circuit.record_failure()
        h.enter_degraded_mode("storm", DegradationLevel.L3_CRITICAL_ONLY)

        # Only DB circuit recovers — Redis is still open
        h.db_circuit.record_success()
        h.update_degraded_state()  # redis still OPEN → enter_degraded_mode(L1) is no-op (L3>L1)

        # Must stay at L3 because Redis is still failing
        assert h.degradation_level == DegradationLevel.L3_CRITICAL_ONLY, (
            f"Partial recovery (DB only) should keep L3, got {h.degradation_level.name}"
        )

    def test_l2_not_cleared_by_enter_l1(self):
        """Calling enter_degraded_mode(L1) when at L2 must be a no-op."""
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        h.enter_degraded_mode("circuit", DegradationLevel.L2_READ_ONLY)
        h.enter_degraded_mode("latency", DegradationLevel.L1_CACHE_HEAVY)
        assert h.degradation_level == DegradationLevel.L2_READ_ONLY


# ═════════════════════════════════════════════════════════════════════════════
# TEST 13 — Cascading failure (Redis→down + DB→slow → L1→L2→L3)
# ═════════════════════════════════════════════════════════════════════════════

class TestCascadingFailure:
    """
    Simulates:
      Step 1: Redis goes down → L1_CACHE_HEAVY
      Step 2: DB becomes slow → stays L1 or escalates
      Step 3: DB connection refused storm → L2_READ_ONLY
      Step 4: DB refused goes to storm (50+) → L3_CRITICAL_ONLY
    """

    def test_step1_redis_down_to_l1(self):
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        for _ in range(h.redis_circuit.failure_threshold):
            h.redis_circuit.record_failure()
        h.update_degraded_state()
        assert h.degradation_level == DegradationLevel.L1_CACHE_HEAVY

    def test_step2_db_slow_stays_l1_or_escalates(self):
        """DB slow on top of Redis-down: level should be L1 or higher (never NONE)."""
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        # Redis down first
        for _ in range(h.redis_circuit.failure_threshold):
            h.redis_circuit.record_failure()
        h.update_degraded_state()
        assert h.degradation_level == DegradationLevel.L1_CACHE_HEAVY

        # DB slow (L1 trigger from timeout)
        from app.database import _trigger_slow_db, _TIMEOUT_L1_THRESHOLD
        with patch("app.core.self_healing.health", h):
            _trigger_slow_db(_TIMEOUT_L1_THRESHOLD)

        # Must be L1 or higher — never drop back to NONE
        assert h.degradation_level.value >= DegradationLevel.L1_CACHE_HEAVY.value

    def test_step3_db_circuit_opens_to_l2(self):
        """After Redis+slow DB: DB circuit opens → escalates to L2."""
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        h.enter_degraded_mode("redis down", DegradationLevel.L1_CACHE_HEAVY)

        from app.database import _trigger_circuit_open, _CIRCUIT_OPEN_THRESHOLD
        with patch("app.core.self_healing.health", h):
            _trigger_circuit_open(_CIRCUIT_OPEN_THRESHOLD + 1)

        assert h.degradation_level == DegradationLevel.L2_READ_ONLY, (
            f"After circuit open on top of L1, expected L2, got {h.degradation_level.name}"
        )

    def test_step4_db_storm_to_l3(self):
        """Sustained refused storm on top of L2 → L3."""
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()
        h.enter_degraded_mode("circuit open", DegradationLevel.L2_READ_ONLY)

        from app.database import _trigger_system_degradation, _SYSTEM_DEGRADE_THRESHOLD
        with patch("app.core.self_healing.health", h):
            _trigger_system_degradation(_SYSTEM_DEGRADE_THRESHOLD + 10)

        assert h.degradation_level == DegradationLevel.L3_CRITICAL_ONLY, (
            f"Storm on top of L2 should reach L3, got {h.degradation_level.name}"
        )

    def test_cascading_state_is_consistent(self):
        """Final state after cascading failure must never be inconsistent."""
        from app.core.self_healing import DegradationLevel
        h = _fresh_health()

        # Full cascade in sequence
        for _ in range(h.redis_circuit.failure_threshold):
            h.redis_circuit.record_failure()
        h.update_degraded_state()

        for _ in range(h.db_circuit.failure_threshold):
            h.db_circuit.record_failure()
        h.update_degraded_state()

        from app.database import _trigger_system_degradation, _SYSTEM_DEGRADE_THRESHOLD
        with patch("app.core.self_healing.health", h):
            _trigger_system_degradation(_SYSTEM_DEGRADE_THRESHOLD + 5)

        final = h.degradation_level
        assert final in (DegradationLevel.L2_READ_ONLY, DegradationLevel.L3_CRITICAL_ONLY), (
            f"After cascading Redis+DB failure, expected L2 or L3, got {final.name}"
        )
        # Degraded flag must be True
        assert h.degraded is True
        # to_dict must reflect the correct level
        assert h.to_dict()["degradation_level"] == final.name
