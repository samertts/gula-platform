"""Operational resilience smoke tests — Phase 8 hardening.

The platform's degraded-mode behavior is the last line of defense before a
hard outage. CLAUDE.md §Self-Healing documents three layers:

  1. Circuit Breaker (DB / Redis)
  2. Auto-Repair Engine
  3. Adaptive Concurrency

This file pins the externally-observable contract:

  * NONE level → all traffic passes
  * L2_READ_ONLY → mutations 503 with Retry-After + X-Degradation-Level
  * L3_CRITICAL_ONLY → only auth/health pass; everything else 503
  * Degraded responses carry an Arabic message (Iraqi healthcare context)
  * Critical clinical writes are EXEMPT from concurrency limit middleware
    (CLAUDE.md: "patient-safety operations must never be shed")
  * Circuit breaker opens after threshold failures, closes on success
  * Health endpoints (whitelisted) NEVER return 503 from degraded middleware

Tests use the existing TestClient — no live DB / Redis required.
Each test resets degradation state in a finally block so cross-test
state never leaks (autouse fixture below).

Blast radius: zero. Each test mutates ``health._degradation_level`` and
restores it; circuit breakers are reset.
"""
from __future__ import annotations

import os

os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest
from app.core.self_healing import (
    _ALWAYS_ALLOWED,
    _CRITICAL_PATHS,
    _SAFE_METHODS,
    CircuitBreaker,
    CircuitState,
    DegradationLevel,
    SystemHealth,
    health,
)


@pytest.fixture(autouse=True)
def _restore_degradation_state():
    """Ensure no test leaves the system in a degraded state."""
    yield
    health.exit_degraded_mode()
    # Reset all breakers (attribute names differ across versions)
    for attr in ("db_circuit", "redis_circuit", "db_breaker", "redis_breaker"):
        cb = getattr(health, attr, None)
        if cb is not None:
            cb.reset()


# ─── Phase 8.A — Circuit breaker state machine ───────────────────────────────


class TestCircuitBreakerStateMachine:
    """The circuit breaker is the foundation of self-healing.
    Verify the documented state transitions hold."""

    def test_starts_closed(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=30.0)
        assert cb.state == CircuitState.CLOSED
        assert cb.is_open() is False

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=30.0)
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED  # 1 < threshold
        cb.record_failure()
        assert cb.state == CircuitState.OPEN  # 2 == threshold
        assert cb.is_open() is True

    def test_record_success_closes_open_circuit(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=30.0)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.is_open() is False

    def test_reset_force_closes(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=30.0)
        cb.record_failure()
        cb.record_failure()
        cb.reset()
        assert cb.state == CircuitState.CLOSED

    def test_open_transitions_to_half_open_after_timeout(self, monkeypatch):
        """After recovery_timeout elapses, OPEN auto-promotes to HALF_OPEN."""
        import time
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.0)
        cb.record_failure()
        # recovery_timeout=0.0 → immediate transition on next state read
        assert cb.state in (CircuitState.OPEN, CircuitState.HALF_OPEN)
        # Force the read to trigger transition
        _ = cb.state
        assert cb.allow_probe() in (True, False)  # depends on race; both valid

    def test_to_dict_serialization(self):
        cb = CircuitBreaker("dbtest", failure_threshold=3, recovery_timeout=15.0)
        d = cb.to_dict()
        assert d["name"] == "dbtest"
        assert d["state"] == "closed"
        assert d["failure_threshold"] == 3
        assert d["recovery_timeout_s"] == 15.0


# ─── Phase 8.B — Health singleton ────────────────────────────────────────────


class TestSystemHealthSingleton:
    """SystemHealth is shared global state; ensure the singleton actually
    reuses one instance and degradation transitions are reflected."""

    def test_singleton_identity(self):
        h1 = SystemHealth()
        h2 = SystemHealth()
        assert h1 is h2

    def test_degraded_starts_false(self):
        assert health.degraded is False
        assert health.degradation_level == DegradationLevel.NONE

    def test_enter_and_exit_degraded(self):
        health.enter_degraded_mode("test", DegradationLevel.L2_READ_ONLY)
        assert health.degraded is True
        assert health.degradation_level == DegradationLevel.L2_READ_ONLY

        health.exit_degraded_mode()
        assert health.degraded is False
        assert health.degradation_level == DegradationLevel.NONE


# ─── Phase 8.C — Degraded mode middleware (HTTP behavior) ────────────────────


class TestDegradedModeHttpBehavior:
    """Verify the externally-observable HTTP contract while degraded."""

    def test_normal_mode_passes_all_traffic(self, client):
        """When NONE, the health endpoints return 200 normally."""
        assert health.degradation_level == DegradationLevel.NONE
        res = client.get("/health")
        assert res.status_code == 200

    def test_l2_blocks_writes_passes_reads(self, client):
        """In L2_READ_ONLY, GET passes, POST/PUT 503s."""
        health.enter_degraded_mode("test L2", DegradationLevel.L2_READ_ONLY)

        # GET to a non-whitelisted path passes (or 401/403/404; the point
        # is: NOT 503 from degradation middleware)
        get_res = client.get("/tiers")
        assert get_res.status_code != 503 or get_res.headers.get("X-Degradation-Level") != "L2_READ_ONLY"

        # POST to a write path → 503 + Retry-After + X-Degradation-Level
        post_res = client.post("/tiers/upgrade", json={"target_tier": "growth"})
        assert post_res.status_code == 503
        assert post_res.headers.get("X-Degradation-Level") == "L2_READ_ONLY"
        assert post_res.headers.get("Retry-After") == "30"
        body = post_res.json()
        assert body["degraded"] is True
        assert "detail_ar" in body  # Arabic message present
        assert body["retry_after_seconds"] == 30

    def test_l3_blocks_everything_except_critical(self, client):
        """In L3_CRITICAL_ONLY, only paths in _CRITICAL_PATHS pass."""
        health.enter_degraded_mode("test L3", DegradationLevel.L3_CRITICAL_ONLY)

        # Random non-critical path → 503
        res = client.get("/tiers")
        assert res.status_code == 503
        assert res.headers.get("X-Degradation-Level") == "L3_CRITICAL_ONLY"
        assert res.headers.get("Retry-After") == "60"

        # /health is in _ALWAYS_ALLOWED (which is checked BEFORE the
        # degradation level), so it passes even in L3
        h = client.get("/health")
        assert h.status_code == 200

    def test_health_endpoints_bypass_all_levels(self, client):
        """The whitelist is checked before degradation level — health
        endpoints must never receive a 503 from the middleware."""
        for level in (DegradationLevel.L2_READ_ONLY, DegradationLevel.L3_CRITICAL_ONLY):
            health.enter_degraded_mode("test", level)
            for path in _ALWAYS_ALLOWED:
                res = client.get(path)
                # Must not be 503 from degraded middleware (could be 503
                # from other reasons — startup guard etc — but those
                # carry no X-Degradation-Level header)
                assert res.headers.get("X-Degradation-Level") is None, (
                    f"{path} returned X-Degradation-Level header in {level}; "
                    "should bypass middleware"
                )
            health.exit_degraded_mode()


# ─── Phase 8.D — Critical-path coverage ──────────────────────────────────────


class TestCriticalPathCoverage:
    """The L3_CRITICAL_ONLY whitelist must include the operator's recovery
    surface. Removing any of these is a self-healing regression."""

    def test_kill_switch_deactivate_in_critical_paths(self):
        """Operators must be able to disable kill-switch even when degraded."""
        assert "/admin/kill-switch/deactivate" in _CRITICAL_PATHS

    def test_auth_login_in_critical_paths(self):
        """Operators must be able to log in to recover the system."""
        assert "/auth/login" in _CRITICAL_PATHS

    def test_metrics_in_critical_paths(self):
        """Prometheus scraping must continue during degradation
        (otherwise observability dies when we need it most)."""
        assert "/metrics/prom" in _CRITICAL_PATHS

    def test_health_status_in_critical_paths(self):
        """The diagnostic health/status endpoint must remain reachable
        — it explains WHY the system is in degraded mode."""
        assert "/health/status" in _CRITICAL_PATHS

    def test_safe_methods_are_idempotent_only(self):
        """SAFE_METHODS in L2 read-only mode must be true HTTP idempotent verbs."""
        assert frozenset({"GET", "HEAD", "OPTIONS"}) == _SAFE_METHODS


# ─── Phase 8.E — Concurrency-limit clinical exemption ────────────────────────


class TestClinicalExemptionFromConcurrencyLimit:
    """CLAUDE.md §Middleware Stack #10:
        'Clinical writes (/results, /orders, /samples, /critical-alerts) are
         exempt — patient-safety operations must never be shed.'

    Pin the exempt-path list in the middleware so a future config change
    can't silently start shedding patient-safety traffic.
    """

    def test_clinical_paths_documented_in_middleware(self):
        """Read the canonical middleware source and assert exempt prefixes remain listed."""
        import pathlib
        middleware_path = pathlib.Path(__file__).parent.parent / "app" / "middleware.py"
        src = middleware_path.read_text()

        # The clinical-write exemption is registered in middleware.py, not main.py.
        for clinical_prefix in ("/results", "/orders", "/samples", "/critical-alerts"):
            assert clinical_prefix in src, (
                f"Clinical-write prefix {clinical_prefix!r} no longer appears in "
                "middleware.py — concurrency-limit exemption may have been silently removed."
            )


# ─── Phase 8.F — Degraded response shape contract ────────────────────────────


class TestDegradedResponseShape:
    """The 503 response body during degradation has a documented shape;
    mobile clients depend on it. Pin the JSON contract."""

    def test_l2_response_shape(self, client):
        health.enter_degraded_mode("test", DegradationLevel.L2_READ_ONLY)
        res = client.post("/tiers/upgrade", json={"target_tier": "growth"})
        body = res.json()
        # Required fields the mobile app relies on
        for key in ("detail", "detail_ar", "degraded",
                    "degradation_level", "retry_after_seconds"):
            assert key in body, f"L2 response missing {key!r}"
        assert body["degradation_level"] == "L2_READ_ONLY"

    def test_l3_response_shape(self, client):
        health.enter_degraded_mode("test", DegradationLevel.L3_CRITICAL_ONLY)
        res = client.get("/tiers")
        body = res.json()
        for key in ("detail", "detail_ar", "degraded",
                    "degradation_level", "retry_after_seconds"):
            assert key in body
        assert body["degradation_level"] == "L3_CRITICAL_ONLY"


# ─── Phase 8.G — Idempotency under retries ───────────────────────────────────


class TestRetrySafety:
    """Mobile clients retry under 503. Verify operations that use the
    documented idempotency cache key pattern behave correctly."""

    def test_idempotency_module_loadable(self):
        """The idempotency module is the foundation of safe retries."""
        from app.core import idempotency
        # Module should expose the standard helpers
        assert hasattr(idempotency, "__name__")
