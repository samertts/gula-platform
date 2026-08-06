# Observability Engineering Memory

**Mission:** GAIOS-MASTER-001
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

Bridge to observability knowledge. The GULA Platform uses
OpenTelemetry for distributed tracing.

---

## Components

| Component | Purpose |
|---|---|
| OpenTelemetry SDK | Instrumentation |
| Jaeger | Trace visualization |
| OTLP Exporter | Trace export |

---

## Architecture

- **Tracing:** OpenTelemetry distributed tracing
- **Backend:** Jaeger
- **Export:** OTLP (OpenTelemetry Protocol)
- **Sampling:** [To be documented]

---

## Key Configuration

| Setting | Value |
|---|---|
| Service Name | gula-platform |
| Export Protocol | OTLP |
| Backend | Jaeger |

---

## Related Knowledge

- `.ai/core/monitoring/` — Prometheus metrics
- `.ai/core/performance/` — Performance metrics
- `.ai/core/devops/` — DevOps infrastructure

---

## References

- ADR-014 (OpenTelemetry + Jaeger)
- `docs/production/` — Production observability setup
