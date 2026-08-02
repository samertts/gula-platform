# Enterprise Certification — Reliability & Continuity v1.0

**Platform:** GULA National Health Platform
**Date:** 2026-08-02
**Level:** Enterprise Certification (P4 program)

## Scope

Event-driven architecture, offline-first capability, backup/DR, observability,
and self-healing — verified by code audit + live checks.

## 1. Event Bus & Outbox Pattern — CERTIFIED

- Kernel EventBus composing dispatcher, store, outbox/inbox, retry queue,
  dead-letter queue, replay, snapshot, versioning, recovery
  (`kernel/event_bus/` — 10 modules).
- **Transactional outbox** (`models/outbox.py`, `services/outbox_service.py`):
  `emit_to_outbox` writes inside the business transaction (`:66`), worker
  loop (`:97,176`) runs in `worker.py:104`.
- 13 outbox unit tests pass; consumers: national streaming, claims,
  data-platform.

## 2. Offline-First — CERTIFIED

- Frontend PWA: vite-plugin-pwa, RTL manifest, offline.html
  (`frontend-v3/`).
- Backend sync: `services/offline_sync_service.py` (SyncOperation queue,
  conflict resolution LWW/timestamp/CRDT/manual);
  `integration/offline.py StoreForwardEngine` (max_retries=5);
  `platform/sync.py`.
- LIMS offline-capable models (`lims/models.py:107,430`);
  certification evaluator `certification/dimensions/offline.py`.

## 3. Backup & Disaster Recovery — CERTIFIED

- `scripts/backup.sh`: pg_dump daily/hourly, AES-256-CBC encryption,
  SHA-256 sidecars, 30-day retention.
- **Backup verifier** (`scripts/backup-verification.sh`, PROGRAM-011):
  restore into `labdb_verify`, checksum + core-table + audit-chain
  verification, docker-aware, cron-ready.
- DR runbooks: `docs/production/DISASTER_RECOVERY_GUIDE.md` (WAL streaming,
  pg_basebackup, replication), PITR runbook, `scripts/dr-failover/failback/
  test.sh`, `emergency-recover.sh`; `backup-cron` service in full compose.
- Make targets: backup, dr-*, pitr-recover.

## 4. Observability — CERTIFIED

- `/metrics` (JSON, auth) + `/metrics/prom` (Prometheus text,
  bearer-guarded in production).
- Prometheus with 3 SLO rules (`config/prometheus/rules/slo.yml`), Grafana
  provisioned (10 dashboards, alert rules, notifiers → Alertmanager →
  Telegram/Discord/Slack).
- OTel SDK auto-instrumentation (FastAPI + SQLAlchemy, OTLP HTTP exporter),
  collector + Tempo/Jaeger configs (active in `.full.yml` profile).
- Health: `/health`, `/health/status` (**honest readiness** — P4 fix
  `a02090ea`: now reflects the startup guard), `/health/deep`; startup
  guard atomic chain with 120s timeout.

## 5. Self-Healing & Resilience — CERTIFIED

- Circuit breaker, bulkhead (P4 clean: dead asyncio branch removed), retry
  with backoff (`core/resilience.py`), auto-repair (`auto_repair.py`),
  self-heal cooldowns, chaos-survival tests, disaster-recovery tests —
  113 resilience-related tests pass.

## Verdict

**RELIABILITY & CONTINUITY: CERTIFIED v1.0** — transactional outbox event
bus, offline-first stack, encrypted backup + verified restore, SLO
alerting, OTel tracing, and self-healing all verified. OTel/Tempo activation
in the default profile is a documented deployment condition.
