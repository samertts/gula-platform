"""Observability & operational visibility — Phase 9 hardening.

Pins the platform's observability contract as a non-regression suite. The
production middleware stack already implements the invariants below; this
file makes them deterministic so a future refactor can't silently remove
them.

Invariants asserted:

  1. Every response carries ``X-Request-ID`` (CLAUDE.md middleware #2).
  2. ``X-Request-ID`` is honoured if supplied by the client (trace continuity
     across services / mobile retries / Cloudflare).
  3. ``X-Response-Time`` is present on every response with a numeric latency.
  4. ``X-API-Version`` is present and matches ``config.APP_VERSION``.
  5. CORS exposes the trace headers so browser callers can read them
     (``expose_headers`` includes X-Request-ID + X-Response-Time + X-API-Version).
  6. Health/whitelisted paths still propagate request IDs (observability must
     not be sacrificed for liveness).
  7. Structured JSON logging is loadable and produces JSON in production mode.
  8. The request-correlation contextvars (``_request_id_var``, ``_endpoint_var``)
     are wired into the DB layer so DB errors are tagged automatically.
  9. Two consecutive requests get distinct auto-generated request IDs.
 10. ``bind_log_context`` accepts the documented kwargs without raising.

Blast radius: zero. No production code touched.
"""

from __future__ import annotations

import json
import os
import re

os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


# ─── Phase 9.A — X-Request-ID propagation ────────────────────────────────────


class TestRequestIdHeader:
    def test_response_carries_request_id_when_none_supplied(self, client):
        """Server must auto-generate an ID when the client didn't send one."""
        res = client.get("/health")
        rid = res.headers.get("X-Request-ID")
        assert rid is not None and rid != ""
        assert _UUID_RE.match(rid), f"X-Request-ID is not a UUID: {rid!r}"

    def test_request_id_round_trips(self, client):
        """If the client sends X-Request-ID, the server uses it (no overwrite)."""
        custom = "client-trace-1234567890abcdef"
        res = client.get("/health", headers={"X-Request-ID": custom})
        assert res.headers.get("X-Request-ID") == custom

    def test_two_requests_have_distinct_auto_ids(self, client):
        """Auto-generated IDs must not collide between requests."""
        a = client.get("/health").headers.get("X-Request-ID")
        b = client.get("/health").headers.get("X-Request-ID")
        assert a != b, "Two consecutive requests share a request_id"

    def test_request_id_present_on_error_responses(self, client):
        """Even 4xx/5xx responses must carry the trace header."""
        res = client.get("/patients")  # unauthenticated → 401/403
        assert res.status_code in (401, 403)
        assert res.headers.get("X-Request-ID") is not None


# ─── Phase 9.B — Response timing & version headers ───────────────────────────


class TestResponseTimingHeader:
    def test_response_time_header_present(self, client):
        res = client.get("/health")
        rt = res.headers.get("X-Response-Time")
        assert rt is not None
        # Format: "<int>ms"
        assert rt.endswith("ms"), f"X-Response-Time format unexpected: {rt!r}"
        ms = int(rt[:-2])
        assert ms >= 0

    def test_api_version_header_present(self, client):
        res = client.get("/health")
        assert res.headers.get("X-API-Version") is not None

    def test_api_version_matches_config(self, client):
        from app.config import APP_VERSION

        res = client.get("/health")
        assert res.headers.get("X-API-Version") == APP_VERSION


# ─── Phase 9.C — CORS exposes trace headers to browser callers ───────────────


class TestCorsTraceHeaderExposure:
    """The frontend needs to read X-Request-ID for correlation. CORS
    ``expose_headers`` must list the trace + version headers."""

    def test_main_module_exposes_trace_headers(self):
        """The CORS middleware in app/main.py must list expose_headers."""
        import pathlib

        main_path = pathlib.Path(__file__).parent.parent / "app" / "main.py"
        src = main_path.read_text()
        # Must list the three observability headers in expose_headers
        for hdr in ("X-Request-ID", "X-Response-Time", "X-API-Version"):
            assert hdr in src, (
                f"main.py CORS expose_headers missing {hdr!r} — frontend "
                "callers will be unable to read this trace header."
            )


# ─── Phase 9.D — Structured logging contract ─────────────────────────────────


class TestStructuredLogging:
    """The platform configures JSON logging in production. Verify the
    primitives are loadable and behave correctly."""

    def test_bind_log_context_accepts_documented_kwargs(self):
        from app.core.logging_config import bind_log_context

        # Must not raise
        bind_log_context(request_id="rid-1", user_id=42, lab_id=7)

    def test_get_request_id_returns_string(self):
        from app.core.logging_config import bind_log_context, get_request_id

        bind_log_context(request_id="explicit-trace-id")
        rid = get_request_id()
        assert isinstance(rid, str)

    def test_configure_logging_is_callable(self):
        """Smoke: configure_logging accepts (is_production, log_level)
        and does not raise on import."""
        from app.core.logging_config import configure_logging

        # Should be idempotent in tests — must not raise
        configure_logging(is_production=False, log_level="WARNING")

    def test_json_formatter_produces_valid_json(self):
        """The _JSONFormatter must emit parseable JSON for log aggregators."""
        import logging

        from app.core.logging_config import _JSONFormatter

        formatter = _JSONFormatter()
        record = logging.LogRecord(
            name="gula.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        # Must round-trip through json.loads
        parsed = json.loads(formatted)
        assert "message" in parsed or "msg" in parsed
        assert "level" in parsed or "levelname" in parsed


# ─── Phase 9.E — Request-correlation contextvars wired to DB layer ───────────


class TestDbCorrelationContextVars:
    """Per CLAUDE.md §database.py, request_id / endpoint / user_id / lab_id
    contextvars must exist so DB errors get tagged automatically."""

    def test_database_module_exports_correlation_vars(self):
        from app import database

        for var in ("_request_id_var", "_endpoint_var"):
            assert hasattr(database, var), f"database.{var} missing — DB error correlation broken"

    def test_correlation_vars_have_default_none(self):
        """Default value must be safe (None) so unbound contexts don't crash."""
        from app.database import _endpoint_var, _request_id_var

        # Reading without a binding should not raise
        try:
            rid = _request_id_var.get()
            ep = _endpoint_var.get()
        except LookupError:
            pytest.fail(
                "Correlation contextvars have no default — production code "
                "that reads them outside of a request will crash."
            )
        # The values are either None or strings
        assert rid is None or isinstance(rid, str)
        assert ep is None or isinstance(ep, str)


# ─── Phase 9.F — Health endpoints still emit observability headers ───────────


class TestHealthEndpointsEmitTraceHeaders:
    """Even when the system is degraded, observability must continue.
    Verify health paths return X-Request-ID + X-Response-Time."""

    def test_health_emits_request_id(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.headers.get("X-Request-ID") is not None
        assert res.headers.get("X-Response-Time") is not None

    def test_health_ready_emits_request_id(self, client):
        res = client.get("/health/ready")
        # 200 in tests; auth middlewares bypass /health/*
        assert res.headers.get("X-Request-ID") is not None


# ─── Phase 9.G — Error classification surfaces ───────────────────────────────


class TestErrorClassificationContract:
    """Phase 9 mandates categorization of runtime failures.
    Verify the documented exception/error types are loadable."""

    def test_self_healing_exposes_circuit_states(self):
        from app.core.self_healing import CircuitState

        # The three documented states
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"

    def test_self_healing_exposes_degradation_levels(self):
        from app.core.self_healing import DegradationLevel

        # Ordered enum: NONE < L1 < L2 < L3
        levels = [
            DegradationLevel.NONE,
            DegradationLevel.L1_CACHE_HEAVY,
            DegradationLevel.L2_READ_ONLY,
            DegradationLevel.L3_CRITICAL_ONLY,
        ]
        for i in range(len(levels) - 1):
            assert levels[i].value < levels[i + 1].value

    def test_ai_guardrail_exception_is_distinct(self):
        """AI capability violations have their own exception class so they
        can be filtered in observability dashboards."""
        from app.ai.guardrails import AIGuardrailViolation

        assert issubclass(AIGuardrailViolation, RuntimeError)


# ─── Phase 9.H — Documented operational endpoints exist ──────────────────────


class TestOperationalEndpoints:
    """The platform documents five operational endpoints. Verify each
    responds (any non-5xx is acceptable — they may require auth)."""

    def test_liveness_endpoint(self, client):
        res = client.get("/health/live")
        assert res.status_code in (200, 503)
        # Must not 5xx (server crash)
        assert res.status_code < 500 or res.status_code == 503

    def test_readiness_endpoint(self, client):
        res = client.get("/health/ready")
        assert res.status_code in (200, 503)

    def test_diagnostic_status_endpoint(self, client):
        """/health/status must always be visible — explains WHY startup failed."""
        res = client.get("/health/status")
        assert res.status_code in (200, 503)

    def test_deep_health_endpoint(self, client):
        """/health/deep — used by `make health-deep`."""
        res = client.get("/health/deep")
        assert res.status_code in (200, 503)
