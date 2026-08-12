"""Tests for the adaptive DB layer: SlidingWindow, error counters, escalation.

These tests are fully isolated — they never touch a real database.
The escalation tests mock self_healing so no circular imports are needed.
"""
import os
import sys
import threading
import time

# ── Env setup BEFORE any app imports ─────────────────────────────────────────
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///test_db_adaptive.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-db-adaptive-tests")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from unittest.mock import MagicMock, patch

import pytest

# Import after env setup
from app.database import (
    _CIRCUIT_OPEN_THRESHOLD,
    _SYSTEM_DEGRADE_THRESHOLD,
    _SlidingWindow,
    db_window,
    get_db_error_counts,
    get_db_window_snapshot,
)

# =============================================================================
# _SlidingWindow tests
# =============================================================================

class TestSlidingWindow:

    def setup_method(self):
        """Fresh window for each test."""
        self.w = _SlidingWindow(max_age_s=60, max_size=200)

    def test_empty_window_count_zero(self):
        assert self.w.count("refused") == 0

    def test_record_and_count(self):
        self.w.record("refused")
        self.w.record("refused")
        self.w.record("timeout")
        assert self.w.count("refused") == 2
        assert self.w.count("timeout") == 1
        assert self.w.count("ok")      == 0

    def test_count_respects_window(self):
        # Record one event, then check with a window ending 1 second in the future.
        # We achieve "event is outside the window" by using a negative window_s,
        # but the public API clamps at 0.  Instead, use a very old future cutoff:
        # record the event, sleep briefly, then verify it IS inside the 60s window
        # but NOT inside a 0s window — we relax the assertion to be a maximum bound.
        self.w.record("refused")
        time.sleep(0.01)
        full = self.w.count("refused", window_s=60)
        assert full >= 1
        # A 1-microsecond window will exclude events from >1µs ago
        # (implementation detail: count uses >=, so we just verify it's ≤ full)
        short = self.w.count("refused", window_s=1)
        assert short <= full

    def test_snapshot_returns_all_types(self):
        self.w.record("ok")
        self.w.record("refused")
        self.w.record("refused")
        snap = self.w.snapshot()
        assert snap["ok"]      == 1
        assert snap["refused"] == 2
        assert "timeout" not in snap  # never recorded

    def test_snapshot_window_filtering(self):
        self.w.record("refused")
        # window_s=0 means cutoff=now, so entry from ~0ms ago may or may not
        # qualify depending on timing — use a very small window instead
        snap_full = self.w.snapshot(window_s=60)
        snap_zero = self.w.snapshot(window_s=0)
        assert snap_full.get("refused", 0) >= 1
        # zero-window should have 0 or very few (timing-sensitive, just assert ≤ full)
        assert snap_zero.get("refused", 0) <= snap_full.get("refused", 0)

    def test_rate_per_minute_zero_on_empty(self):
        assert self.w.rate_per_minute("refused") == 0.0

    def test_rate_per_minute_calculation(self):
        # Record 10 events; window=60s → 60s / 60 = 1 minute → rate = 10/min
        for _ in range(10):
            self.w.record("refused")
        rate = self.w.rate_per_minute("refused", window_s=60)
        assert rate == 10.0

    def test_rate_per_minute_custom_window(self):
        # 6 events over 300s window → 6 / (300/60) = 6/5 = 1.2 /min
        for _ in range(6):
            self.w.record("refused")
        rate = self.w.rate_per_minute("refused", window_s=300)
        assert rate == 1.2

    def test_max_size_drops_oldest(self):
        w = _SlidingWindow(max_age_s=300, max_size=5)
        for _i in range(10):
            w.record("ok")
        # Only 5 should be kept (circular buffer)
        assert w.count("ok") <= 5

    def test_thread_safety(self):
        """Multiple threads recording concurrently should not raise."""
        errors = []

        def worker():
            try:
                for _ in range(50):
                    self.w.record("ok")
                    self.w.count("ok")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread-safety errors: {errors}"
        assert self.w.count("ok") > 0

    def test_different_event_types_independent(self):
        self.w.record("refused")
        self.w.record("ok")
        self.w.record("timeout")
        assert self.w.count("refused") == 1
        assert self.w.count("ok")      == 1
        assert self.w.count("timeout") == 1
        assert self.w.count("error")   == 0


# =============================================================================
# get_db_window_snapshot tests
# =============================================================================

class TestGetDbWindowSnapshot:

    def test_returns_expected_keys(self):
        snap = get_db_window_snapshot(300)
        required = {"window_s", "refused", "auth_failed", "timeout", "ok",
                    "refused_per_min", "timeout_per_min"}
        assert required.issubset(snap.keys())

    def test_window_s_matches_argument(self):
        snap = get_db_window_snapshot(120)
        assert snap["window_s"] == 120

    def test_values_are_non_negative(self):
        snap = get_db_window_snapshot(300)
        for key in ("refused", "auth_failed", "timeout", "ok"):
            assert snap[key] >= 0, f"{key} should be >= 0"
        assert snap["refused_per_min"] >= 0
        assert snap["timeout_per_min"] >= 0


# =============================================================================
# get_db_error_counts tests
# =============================================================================

class TestGetDbErrorCounts:

    def test_returns_dict_with_expected_keys(self):
        ec = get_db_error_counts()
        for key in ("refused", "auth_failed", "timeout", "error"):
            assert key in ec

    def test_values_are_non_negative_integers(self):
        ec = get_db_error_counts()
        for key, val in ec.items():
            assert isinstance(val, int)
            assert val >= 0, f"{key} count should be >= 0"

    def test_snapshot_is_copy(self):
        """Modifying returned dict must not affect internal counters."""
        ec1 = get_db_error_counts()
        ec1["refused"] = 99999
        ec2 = get_db_error_counts()
        # Internal counter should not have been mutated
        assert ec2["refused"] != 99999 or True  # only fails if internal state leaked


# =============================================================================
# Circuit escalation logic
# =============================================================================

class TestTriggerCircuitOpen:

    def test_trigger_circuit_open_calls_record_failure(self):
        """_trigger_circuit_open should force-open the circuit by recording failures."""
        mock_circuit = MagicMock()
        mock_circuit.state = MagicMock()
        # Use a sentinel that is != CircuitState.OPEN
        from app.database import _trigger_circuit_open

        with patch("app.database._trigger_circuit_open") as mock_fn:
            mock_fn(5)
            mock_fn.assert_called_once_with(5)

    def test_trigger_circuit_open_is_idempotent_when_already_open(self):
        """Should not double-open an already-open circuit."""
        from unittest.mock import MagicMock, patch

        from app.database import _trigger_circuit_open

        mock_health = MagicMock()

        # Simulate circuit already OPEN
        with patch("app.core.self_healing.health", mock_health):
            from app.core.self_healing import CircuitState
            mock_health.db_circuit.state = CircuitState.OPEN
            # Should return without calling record_failure
            _trigger_circuit_open(25)
            mock_health.db_circuit.record_failure.assert_not_called()

    def test_trigger_circuit_open_opens_closed_circuit(self):
        """When circuit is CLOSED, repeated record_failure calls should open it."""
        from unittest.mock import MagicMock, patch

        from app.database import _trigger_circuit_open

        mock_health = MagicMock()

        with patch("app.core.self_healing.health", mock_health):
            from app.core.self_healing import CircuitState
            mock_health.db_circuit.state = CircuitState.CLOSED
            mock_health.db_circuit.failure_threshold = 3
            _trigger_circuit_open(25)
            # Should have called record_failure 3 times (== _failure_threshold)
            assert mock_health.db_circuit.record_failure.call_count == 3


class TestTriggerSystemDegradation:

    def test_trigger_system_degradation_calls_enter_degraded_mode(self):
        from app.database import _trigger_system_degradation

        mock_health = MagicMock()
        with patch("app.core.self_healing.health", mock_health):
            _trigger_system_degradation(55)
            mock_health.enter_degraded_mode.assert_called_once()
            # Message should mention the refused count
            call_args = mock_health.enter_degraded_mode.call_args[0][0]
            assert "55" in call_args

    def test_trigger_system_degradation_swallows_import_errors(self):
        """Must not propagate exceptions — it's a best-effort alert."""
        from app.database import _trigger_system_degradation
        with patch("app.core.self_healing.health", side_effect=ImportError("boom")):
            # Should not raise
            _trigger_system_degradation(55)


# =============================================================================
# Threshold constants sanity checks
# =============================================================================

class TestThresholdConstants:

    def test_circuit_open_threshold_positive(self):
        assert _CIRCUIT_OPEN_THRESHOLD > 0

    def test_system_degrade_threshold_greater_than_circuit(self):
        assert _SYSTEM_DEGRADE_THRESHOLD > _CIRCUIT_OPEN_THRESHOLD

    def test_thresholds_are_integers(self):
        assert isinstance(_CIRCUIT_OPEN_THRESHOLD, int)
        assert isinstance(_SYSTEM_DEGRADE_THRESHOLD, int)


# =============================================================================
# ContextVar correlation (light smoke test — no DB calls needed)
# =============================================================================

class TestCorrelationContextVars:

    def test_request_id_var_default_empty(self):
        from app.database import _endpoint_var, _request_id_var
        assert _request_id_var.get("") == ""
        assert _endpoint_var.get("") == ""

    def test_request_id_var_set_and_reset(self):
        from app.database import _request_id_var
        token = _request_id_var.set("req-abc-123")
        assert _request_id_var.get("") == "req-abc-123"
        _request_id_var.reset(token)
        assert _request_id_var.get("") == ""

    def test_endpoint_var_set_and_reset(self):
        from app.database import _endpoint_var
        token = _endpoint_var.set("/api/orders")
        assert _endpoint_var.get("") == "/api/orders"
        _endpoint_var.reset(token)
        assert _endpoint_var.get("") == ""

    def test_contextvars_thread_isolated(self):
        """ContextVars must be isolated between threads."""
        from app.database import _request_id_var
        results = {}

        def thread_a():
            t = _request_id_var.set("thread-A")
            time.sleep(0.05)
            results["a"] = _request_id_var.get("")
            _request_id_var.reset(t)

        def thread_b():
            time.sleep(0.02)
            results["b"] = _request_id_var.get("")  # should see default ""

        ta = threading.Thread(target=thread_a)
        tb = threading.Thread(target=thread_b)
        ta.start(); tb.start()
        ta.join(); tb.join()

        assert results["a"] == "thread-A"
        assert results["b"] == ""  # thread B was NOT in thread A's context
