# Monitoring Engineering Memory

**Mission:** GAIOS-MASTER-001
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

Bridge to monitoring knowledge. The GULA Platform uses Prometheus
and Grafana for monitoring.

---

## Components

| Component | Purpose |
|---|---|
| Prometheus | Metrics collection |
| Grafana | Metrics visualization |

---

## Architecture

- **Metrics Format:** Prometheus exposition format
- **Collection:** Pull-based (Prometheus scrapes endpoints)
- **Visualization:** Grafana dashboards
- **Alerting:** Prometheus Alertmanager

---

## Key Endpoints

| Endpoint | Purpose |
|---|---|
| `/metrics` | Prometheus metrics |
| `/health` | Health check |

---

## Related Knowledge

- `.ai/core/performance/` — Performance metrics
- `.ai/core/observability/` — OpenTelemetry tracing
- `.ai/core/devops/` — DevOps infrastructure

---

## References

- `docs/production/` — Production monitoring setup
- `backend/app/routes/metrics.py` — Metrics endpoint
