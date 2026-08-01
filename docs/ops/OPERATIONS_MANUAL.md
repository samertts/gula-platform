# GULA Platform — Operations Manual

**Version:** 1.0 · **Status:** Active · **Owner:** Platform Operations (SRE)
**Audience:** Platform operators, on-call engineers, ministry admins

This manual is the single entry point for operating GULA in production.
Runbooks, monitoring, recovery and maintenance procedures are referenced,
not duplicated.

---

## 1. System Overview

| Component | Container / Service | Port | Health |
|---|---|---|---|
| Backend API | `gula-backend` | 8000 (10000 alt) | `/health`, `/health/ready`, `/health/live`, `/health/deep` |
| Database | `gula-postgres` (PostgreSQL 16) | 5432 | `pg_isready` |
| Cache/queue | `gula-redis` | 6379 | `redis-cli ping` |
| Frontend | `gula-frontend` (v3, Arabic-first RTL) | 80/443 via nginx | — |
| Monitoring (opt-in) | prometheus / grafana / alertmanager / node-exporter | 9090/3000/9093/9100 | compose profile `monitoring` |
| Worker | gula-worker (async tasks) | — | task queue `gula:tasks` |

Logs: JSON-structured to stdout → collected by journald / Loki (promtail).
State: PostgreSQL (single source of truth), Redis (cache + task queue + ephemeral state).

## 2. Health & Monitoring Guide

| Endpoint | Meaning |
|---|---|
| `GET /health` | Liveness + DB detail + circuit breakers + pool status |
| `GET /health/live` | Liveness only (no dependencies) |
| `GET /health/ready` | Readiness: startup guard AND DB AND Redis → 503 while warming |
| `GET /health/deep` | Full diagnostic: grade GREEN/YELLOW/RED, latency, queue backlog, RSS |
| `GET /metrics/prom` | Prometheus text format (Bearer token in production) |
| `GET /metrics` | Human/JSON metrics (role-scoped) |

Metric families exported: `gula_up`, `gula_down`, `gula_uptime_seconds`,
`gula_memory_rss_mb`, `gula_db_up`, `gula_db_latency_ms`, `gula_redis_up`,
`gula_redis_latency_ms`, `gula_orders_total`, `gula_orders_pending`,
`gula_active_requests`, `gula_queue_backlog`, `gula_db_{refused,auth_failed,
timeout,error}_total`, `gula_db_*_rate_5m`, `gula_db_error_ratio_5m`,
`gula_policy_{block,allow}_total`, `gula_auto_repair_total`,
`gula_kill_switch_active`, `gula_degradation_level`,
`gula_requests_total{method,route,status}`, `gula_request_errors_total`,
`gula_request_duration_seconds` (histogram — powers the SLO rules).

Prometheus stack (`docker compose --profile monitoring up -d prometheus grafana`):
- Scrape targets: backend `/metrics/prom` (bearer), node-exporter, postgres-exporter, redis-exporter.
- Alert rules: `config/prometheus/rules/gula.yml` (core) + `slo.yml` (SLO/burn-rate).
- Grafana: 10 dashboards provisioned from `config/grafana/dashboards/`, folder `GULA`.
- Alertmanager: `config/alertmanager/alertmanager.yml` (webhook receiver).

Script-based fallback monitors (installed by `server-setup.sh` crons):
- `monitor.sh` (every 5 min) — `/health/ready` probe + Telegram alert.
- Backend `_health_alert_loop` — grades GREEN/YELLOW/RED and fires `ALERT_WEBHOOK_URL` on change.

## 3. Alert Catalog

### Critical (page immediately)
| Alert | Source | Meaning |
|---|---|---|
| DatabaseDown / RedisDown | gula.yml | dependency unreachable — expect degraded mode |
| BackendDown | gula.yml | `/metrics/prom` scrape failing |
| DatabaseAuthFailed | gula.yml | credential failure — immediate investigation |
| KillSwitchActive | gula.yml | emergency switch engaged |
| DiskSpaceCritical | gula.yml | host disk >85% |
| SLOErrorBudgetExhausted | slo.yml | error budget consumed |
| DatabaseConnectionRefusedCritical | gula.yml | refused connection rate elevated |

### Warning (next business day)
DatabaseSlow, RedisSlow, HighConcurrency, ConcurrencyLimitReached, HighMemory,
OrderBacklog, DiskSpaceWarning, PostgresConnectionsHigh, DatabaseErrorRatioHigh,
PolicyBlockSpike, DegradationL2ReadOnly, DegradationL3CriticalOnly,
SLOErrorBudgetFastBurn/SlowBurn, SLOAvailabilityBelow, SLOLatencyExceeded.

### Informational / recurring
`gula_policy_block_total`, `gula_auto_repair_total`, outbox backlog.

## 4. Incident Response Guide

Severity model:

| Severity | Definition | Response time |
|---|---|---|
| SEV-1 | Platform down / data loss / security breach | 15 min, page |
| SEV-2 | Major feature degraded (e.g. results posting) | 1 h |
| SEV-3 | Minor degradation, workaround exists | next business day |

Flow:
1. **Detect** — alert fires (webhook/Telegram/Prometheus) or user reports.
2. **Triage** — run `scripts/diagnose-droplet.sh` (read-only snapshot) or `scripts/health-probes/check-all.sh`.
3. **Contain** — for data-affecting issues engage kill switch (`/admin/kill-switch`); never restart DB while unsure.
4. **Repair** — follow the matching runbook in `docs/runbooks/`:
   - `backend-down.md`, `database-down.md`, `disk-full.md`, `high-latency.md`,
     `certificate-expiry.md`, `failed-deployment.md`, `security-incident.md`.
5. **Verify** — `/health/deep` grade GREEN, `/metrics` error ratio back to baseline.
6. **Post-incident** — log entry, update runbook with new knowledge, regression test if code-related.

Escalation: on-call engineer → Platform Ops lead → Ministry admin.

## 5. Recovery Guide

| Scenario | Procedure |
|---|---|
| Restore latest backup | `scripts/backup-verification.sh` (restore-verify into test DB) → `restore-test.sh` |
| Point-in-time recovery | `scripts/pitr-recover.sh` + `docs/dr/PITR_RUNBOOK.md` |
| DR failover | `scripts/dr-failover.sh` / `dr-failback.sh` (k8s) — `dr_recovery.sh` (docker) |
| Rollback deployment | `docs/operations/zero-downtime-upgrades.md`, CI `rollback.yml` |
| Snapshot restore | `scripts/manage-snapshots.sh` (cloud disk snapshot) |

Backups: daily (retention 30 d) + hourly (2 d) via `backup.sh`; optional
AES-256 encryption with `BACKUP_ENCRYPT_KEY`; SHA-256 sidecar per file;
restore verified nightly in CI (`backup-drill` job) and locally by
`backup-verification.sh`.

## 6. Maintenance Guide

### Scheduled tasks (crontab, installed by server-setup.sh)
| Schedule | Task |
|---|---|
| every 1 min | `self_heal.py` (ASHS — health repair agent) |
| every 5 min | `auto_heal.sh` (container watchdog, max 3 restarts/h) · `monitor.sh` |
| hourly | `backup.sh hourly` |
| 02:00 daily | `backup.sh daily` |
| 03:00 daily | `cert-renew.sh` (TLS expiry check + renewal + alert) |
| 06:00 daily | `backup-verification.sh` (restore test) |
| nightly CI | integration tests, chaos tests, benchmarks, container security, backup drill |

### Routine maintenance
- **Secrets rotation:** `scripts/rotate-secrets.sh` (PG/Redis/RabbitMQ/APP keys,
  verified + rollback per secret; log in `${GULA_LOG_DIR:-/var/log/gula}/secret-rotation.log`).
  `ENCRYPTION_KEY` rotation re-encrypts Fernet-encrypted fields first via
  `scripts/reencrypt_encryption_key.py` (batch, dry-run capable, abort on failure)
  — the key is only swapped after re-encryption succeeds.
- **Certificate rotation:** `scripts/cert-renew.sh` (alert at 30 d, renew at threshold).
- **Cache:** L1/L2 cache self-managed; `kill_switch` and degradation modes handle pressure.
- **Migrations:** always `alembic upgrade head` via `preflight.sh` before deploy;
  never destructive automatically.
- **Disk hygiene:** `auto_heal.sh` prunes docker at >90%; retention enforced by backup scripts.

### Reversible operations
All automations are reversible: container restarts (compose), safe-mode flag
(`/tmp/gula_safe_mode`), degraded-mode (L1→L3 with monotonic escalation),
kill switch (deactivation always reachable). No automation performs destructive
actions without human confirmation.

## 7. Environment & Deploy Checklist

```bash
scripts/verify_environment.sh   # toolchain + services
scripts/preflight.sh            # deploy gate (env, DB, migrations, imports, tests)
scripts/integration_test.sh     # 10 E2E checks
scripts/smoke-bootstrap.sh      # post-deploy: health, auth, latency p50/p95/p99, error rate
scripts/deploy.sh               # safe deploy: backup + health wait (180 s) + lock file
```

## 8. Related Documents

- `docs/runbooks/` — incident runbooks (7)
- `docs/dr/PITR_RUNBOOK.md` — point-in-time recovery
- `docs/DEPLOYMENT.md` — full deployment guide (Arabic)
- `docs/LAUNCH_RUNBOOK.md` — go-live checklist
- `docs/security/` — secrets management, rotation plans
- `reports/ops/OPERATIONS_READINESS_REPORT.md` — certification + platform health score
