# PROGRAM-011 Report — Enterprise Operations, Observability & Self-Healing

**Status:** COMPLETE — **98% PRODUCTION READY** (101 PASS / 5 WARN / 0 FAIL)
**Date:** 2026-07-31 · **Certification:** `make ops-cert` → `reports/ops/OPERATIONS_READINESS_REPORT.md`
**Regression gate:** `make validate` VERDICT PASS (225 unit tests, tsc 0, eslint 0, ruff 379 at baseline)

## Summary

GULA already carried a deep operations layer (health endpoints, degradation
middleware, circuit breakers, auto-repair, healer agents, backup/DR scripts,
Prometheus/Grafana configs). PROGRAM-011 verified each phase, fixed the
defects that would fail in production, made the alert rules actually fireable,
and certified the result.

## Delivered

### Critical defects fixed
| Defect | Impact | Fix |
|---|---|---|
| `shared/circuit_breaker.py` missing `allow_request/record_success/record_failure` | AttributeError on first notification send | API added + `CircuitOpenError` + thread safety |
| `backup-verification.sh` was MySQL-based | Restore verification unusable on GULA (PostgreSQL) | Rewritten PG-aware (docker-first, like backup.sh) |
| SLO alert rules referenced non-exported metrics (`gula_request_duration_seconds*`, `gula_requests_total`, `gula_request_errors_total`, `gula_down`) | ~30 alerts could never fire | Request metrics exported from `RequestTimingMiddleware` (histogram + counters, in-process, thread-safe) |
| `gula-full.yml` security alerts (`gula_permission_denied_total`, `gula_auth_failures_total`, `gula_rate_limit_blocks_total`) referenced nothing | Security alerts dead | New `SecurityEventMiddleware` records 401/403/429 + metrics |
| `dr-test.sh` swallowed failover failure (`\|\| true`) | False-positive DR results | Exit code captured; verdict fails if failover failed |
| Encrypted backups invisible to verifier (discovery only matched `.sql.gz`) | Verification step 1 exited 1 on encrypted dirs | Found by local drill; fixed to count `.enc` |

### New capabilities
- **Encrypted backups:** `backup.sh` supports `BACKUP_ENCRYPT_KEY` → AES-256-CBC (openssl, zero new deps); decrypt-on-verify; verified live against gula-postgres (337 tables restore OK).
- **CI backup drill** (`nightly.yml`): real PostgreSQL pipeline — backup → checksum verify → restore-verify, plaintext + encrypted variants. Committed automation replaces host-only cron comments.
- **Committed ops scheduling:** `server-setup.sh` now installs backup (daily+hourly), backup-verification (06:00), cert-renew (03:00), monitor.sh (5 min) crons — previously only healers were scheduled.
- **PITR runbook:** `docs/dr/PITR_RUNBOOK.md` (was referenced by `pitr-recover.sh`, missing).
- **Operations Manual:** `docs/ops/OPERATIONS_MANUAL.md` — system map, monitoring guide, alert catalog, incident response, recovery guide, maintenance guide.
- **`LOG_LEVEL` env-driven** (was hardcoded INFO).
- **Certification engine:** `scripts/operations_certification.py` — 9 phases, 106 evidence-based checks → phase reports + `overall_health.json`.

### WARN burn-down (post-certification)
| WARN | Fix | Evidence |
|---|---|---|
| ASHS restart-loop risk (no per-signal cooldown) | `scripts/self_heal.py`: `ACTION_COOLDOWN_S` (600s default) + file-persisted cooldown map (`/tmp/gula-ashs-cooldown.json`) so cron-invoked ASHS runs cannot restart a service twice inside the window | `test_self_heal_cooldown.py` (8 tests) |
| Outbox-backlog auto-repair (detected, not repaired) | `auto_repair.py`: `outbox_poll` action — backlog > 200 → `outbox_service.set_poll_interval(2)` (10s→2s); auto-restored to default when queue drains below warn. Policy-gated, idempotent, reversible | `test_outbox_auto_repair.py` (12 tests) |

### Verification
- 225 unit tests (179 → 225: circuit breaker, shared encryption, request metrics, security events, ops certification, ASHS cooldown, outbox repair).
- 114 resilience/control-layer tests (`test_control_layer`, `test_hard_scenarios`, `test_runtime_isolation`, `test_stability_assertions`) pass with the new auto-repair wiring.
- Local live drills: plaintext + encrypted backup→verify→restore pipelines (337 tables, audit chain intact).
- `test_resilience_smoke.py` (22) passes with the new middleware stack.
- Ruff clean on all touched files; shellcheck clean on all touched shell scripts.

## Platform Health Score by Phase

| Phase | PASS | WARN | FAIL |
|---|---|---|---|
| 1. Observability | 13 | 1 | 0 |
| 2. Monitoring | 11 | 1 | 0 |
| 3. Self-Diagnostics | 14 | 0 | 0 |
| 4. Self-Healing | 10 | 0 | 0 |
| 5. Backup & Recovery | 12 | 1 | 0 |
| 6. Operations Dashboard | 8 | 1 | 0 |
| 7. Security Operations | 14 | 1 | 0 |
| 8. Automation | 11 | 0 | 0 |
| 9. Documentation | 8 | 0 | 0 |

## Remaining WARNs (next iteration candidates)

1. OpenTelemetry SDK export (Jaeger/Tempo/collector provisioned, no sender)
2. Grafana alert provisioning files
3. Cloud snapshot restore unimplemented (documented)
4. Frontend page consuming `/metrics` (observability page is an API explorer)
5. ENCRYPTION_KEY rotation re-encryption deferred on-read
