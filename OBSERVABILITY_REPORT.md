# GULA Platform — Observability Report (PROGRAM-BETA Phase 4)

**Date:** 2026-08-06
**Status:** VERIFIED — metrics, tracing, and structured logs all present, env-gated, and tested.

---

## 1. Executive Summary

The platform has a complete observability stack: Prometheus metrics, OTLP/HTTP
tracing (vendor-neutral → Jaeger/Tempo/OTel Collector), JSON structured logs,
distributed request IDs, health/readiness/deep-health endpoints, and Sentry (env-gated).

**Verdict: PASS.**

## 2. Pillars (verified)

### 2.1 Metrics
- `/api/metrics` JSON + `/api/metrics/prom` Prometheus text (`routes/metrics.py`,
  `metrics_service.py build_prometheus_response`).
- Exposed headers: `X-Request-ID`, `X-Response-Time`, `X-API-Version`.
- `RequestTimingMiddleware`, `SecurityEventMiddleware`, `KernelMiddleware`,
  `RequestIDMiddleware` in the middleware chain (`factory.py:424-436`).
- Backup exporter pushes `gula_backup_size_bytes` / `gula_backup_age_seconds` to a
  Prometheus pushgateway (`continuous-backup.sh:81-82`).

### 2.2 Tracing
- `app/telemetry.py`: OpenTelemetry SDK, OTLP/HTTP exporter
  (`{OTEL_EXPORTER_OTLP_ENDPOINT}/v1/traces`), batch span processor, 5 s export
  timeout.
- **Zero lock-in:** disabled (no-op) unless `OTEL_EXPORTER_OTLP_ENDPOINT` is set;
  any OTLP-compatible backend (Jaeger, Tempo, Collector) can be used.
- Wired in `factory.py:971-973` (`init_tracing()`).

### 2.3 Structured logs
- `shared/logging/config.py JSONFormatter` — JSON lines with `asctime`, `levelname`,
  `name`, `message` (`ensure_ascii=False` for Arabic).
- `configure_logging(is_production=...)` in `factory.py:964-966`; Sentry
  `LoggingIntegration(level=ERROR)` when enabled.

### 2.4 Health endpoints
- `/health`, `/health/ready`, `/health/status`, `/health/deep` (`routes/metrics.py`).
- `ReadinessMiddleware` + `DegradedModeMiddleware` drive readiness/degraded semantics;
  docker HEALTHCHECK hits `/health`; compose healthchecks + k8s liveness/readiness probes.

## 3. Tests (passing)
| Suite | Tests | Covers |
|---|---|---|
| `test_metrics_service.py` | 14 | uptime, RSS, DB ping, order stats, lab isolation |
| `test_stats_service.py` | 7 | cache key, stats summary, lab isolation |
| `test_telemetry.py` | 7 | OTLP pipeline env-gating, exporter wiring |

## 4. Residual / Tracked
| Item | Priority | Notes |
|---|---|---|
| Frontend `/metrics` page flagged in prior WARN burn-down | Low | Backend endpoints exist; UI page still to be built |
| Sentry DSN must be set via env in prod | Info | `_should_init_sentry()` gates it |

## 5. Conclusion

**PASS.** The four observability pillars are implemented, vendor-neutral, env-gated,
and test-covered. Production can be monitored end-to-end with standard OTel/Prometheus
tooling and JSON logs.
