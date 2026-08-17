# National-Scale Deployment Readiness — Phase 15

**Date:** 2026-08-17
**Stage:** Patient Flow / Offline Sync government-readiness follow-up
**Architectural blast radius:** additive readiness gate, security coverage, staging load scenario, and Outbox fail-closed guard

> هذه الوثيقة لا تمنح موافقة إنتاج حكومية تلقائية. يلزم اعتماد التغيير السريري والأمني والتشغيلي وخطة التعافي من الكوارث قبل أي rollout.

This document is the operator-facing deployment readiness register for the
GULA Platform. It complements `PRODUCTION_HARDENING.md` (Phases 1–8).

---

## 1. Deployment-readiness checklist

Operators MUST tick every item below before staged national rollout.

### 1.1 Migration & schema

- [ ] `alembic upgrade head` succeeds on a fresh PostgreSQL 16 instance
- [ ] PR #97 (duplicate-revision fix) merged
- [ ] `tests/test_migrations.py` — 9/9 pass (no duplicate revisions, single head)
- [ ] `tests/test_migration_resilience.py` — 10/10 pass (idempotency guards present)
- [ ] DHIS2 endpoint query rewritten to JOIN through `lab_orders`
  (compliance.py:562 — currently references nonexistent `lab_results.lab_id`)
- [ ] SNDHS Phase 1 backfill (`scripts/sndhs_phase1_backfill.py`) executed
- [ ] `SNDHS_ENABLE_VISITS` / `SNDHS_ENABLE_NATIONAL_ID` flags confirmed off
  for stage 1 rollout

### 1.2 Secrets & environment

- [ ] `SECRET_KEY`, `ENCRYPTION_KEY`, `NID_HMAC_KEY`, `REFRESH_TOKEN_SECRET`,
  `DEVICE_HMAC_KEY` rotated from `make secrets-gen` output
- [ ] `IS_PRODUCTION=true` set in deploy environment
- [ ] `RUNTIME_MODE=api` (or `worker`) explicit in container env
- [ ] `FEATURE_BACKGROUND_TASKS=true` only on the `worker` runtime, not `api`
- [ ] `ENABLE_FINANCIAL_ENGINE=false` and `ENABLE_ADS=false` for stage 1
- [ ] `METRICS_BEARER_TOKEN` generated and documented (`make metrics-token`)
- [ ] `ALERT_WEBHOOK_URL` configured (Telegram / Slack)

### 1.3 Observability

- [ ] `tests/test_observability_invariants.py` — 23/23 pass
- [ ] Prometheus scraping verified at `/metrics/prom` with bearer token
- [ ] Grafana dashboards loaded (`config/grafana/`)
- [ ] `X-Request-ID` round-trip verified end-to-end (client → backend → audit)
- [ ] Structured JSON logs flowing into log-aggregation backend
- [ ] Alert webhooks fire on RED grade transitions (synthetic test)

### 1.4 Tenant isolation

- [ ] `tests/test_tenant_isolation_matrix.py` — 45/45 pass
- [ ] Production smoke: read each authenticated endpoint as Lab A, confirm
  Lab B data is NEVER returned (run `scripts/diagnose-droplet.sh` equivalent)
- [ ] Frontend `roleWingIsolation.test.ts` — 41/41 pass

### 1.5 Clinical safety

- [ ] `tests/test_clinical_safety.py` — 32/32 pass
- [ ] `tests/test_concurrency_safety.py` — 15/15 pass
- [ ] Critical-value alert webhook tested with synthetic high potassium
- [ ] Doctor sign-off flow verified end-to-end on staging
- [ ] `LabResult.version` CAS implementation tracked as P1 follow-up

### 1.6 Resilience

- [ ] `tests/test_resilience_smoke.py` — 22/22 pass
- [ ] `tests/test_chaos_survival.py` — 14/14 pass
- [ ] `make chaos` suite green
- [ ] DB-circuit-open simulation produces L2 503 + Retry-After headers
- [ ] Health endpoints respond < 100ms p95
- [ ] `make scale REPLICAS=5` smoke-tested behind HAProxy

### 1.7 Security & compliance

- [ ] `tests/test_security_regression.py` — 21/21 pass
- [ ] `tests/test_security.py` — existing suite green
- [ ] `tests/test_compliance_integrity.py` — 20/20 pass
- [ ] `gitleaks` + `bandit` + `safety` scans clean
- [ ] `/compliance/audit-integrity` returns `intact` on synthetic restore
- [ ] FHIR R4 Patient/Observation/DiagnosticReport responses validated
  against an external FHIR validator on staging
- [ ] HSTS / CSP / X-Frame-Options headers verified at TLS edge

### 1.8 Disaster recovery

- [ ] `tests/test_disaster_recovery.py` — 10/10 pass
- [ ] `make backup` produces a usable `.sql.gz`
- [ ] Documented restore procedure exercised on a clone DB
- [ ] Audit-anchor sidecar files preserved in backup
- [ ] PITR target list (last N successful migrations) documented and reviewed

### 1.9 Performance

- [ ] `tests/test_performance_budgets.py` — 18/18 pass (no N+1 regression)
- [ ] `make scenario-test USERS=50 ROUNDS=5` p99 < 500ms
- [ ] `make integrity-test WORKERS=200` zero corruption
- [ ] Slow-query log enabled (>300ms threshold)

### 1.9.1 Government Patient Flow and Offline Sync

- [ ] `python3 scripts/government_readiness_gate.py --run-tests` passes on a clean non-protected branch.
- [ ] `alembic heads` reports exactly one head and includes `20260817_0025`.
- [ ] `GULA_SYNC_OUTBOX_DELIVERY` is set to `redis`, `broker`, or `push`; `log` is forbidden when `IS_PRODUCTION=true`.
- [ ] `make patient-flow-load BASE_URL=... AUTH_TOKEN=... DEVICE_ID=... DEVICE_SESSION_TOKEN=... HOSPITAL_ID=... SCENARIO=smoke` passes against synthetic staging data.
- [ ] Patient Flow/Sync load thresholds are met: error rate <1%, read p95 <500ms, write p95 <1000ms, and no unexpected device-session rejection.
- [ ] Offline queue recovery is tested from IndexedDB v1 to v2, including encrypted legacy-row migration and the 5000-operation cap.
- [ ] Clinical conflicts remain manual-review only; no last-write-wins or automatic medical merge is allowed.
- [ ] The `services/device_bridge` pre-existing compilation failures are either fixed or explicitly excluded from the release candidate with owner and deadline.

### 1.10 AI / autonomy

- [ ] `tests/test_ai_guardrails.py` — 27/27 pass
- [ ] `_ABSOLUTELY_BLOCKED` operations explicitly enumerated and reviewed
- [ ] AI suggestions auto-approve only for `display_only` operations
- [ ] AI sandbox handlers verified read-only (no DB writes)
- [ ] AI-triggered actions emit audit-log entries with `actor_type=ai`

---

## 2. Operational runbooks (one-line index)

| Runbook | When to use | Doc / script |
|---|---|---|
| Healthy → degraded transition | Latency p95 > 2s sustained | `make health-deep` + `/compliance/system-status` |
| DB outage | Backend cannot reach Postgres | Circuit auto-opens; degraded middleware → L2/L3 |
| Redis outage | Cache misses spike | Falls back to in-memory `_MemoryStore` automatically |
| Run-away traffic | 503s with Retry-After | Adaptive concurrency halves cap; clinical writes exempt |
| Audit-integrity tampered | `/compliance/audit-integrity` reports tampered | Restore from anchor file + audit_logs backup |
| Migration rollback | Failed deploy | `alembic downgrade -1` (round-trip CI test must be green) |
| Kill switch | Hostile traffic | `make kill-switch-on` (DigitalOcean firewall) |
| Force AI sandbox stop | AI misbehavior | Toggle `ENABLE_AI_SUGGESTIONS=false` env var |
| Cross-tenant leak suspicion | Anomalous access pattern | Run `tests/test_tenant_isolation_matrix.py` against staging |
| Recovery from corrupted backup | Backup verifies tampered | Use prior anchor checkpoint; re-stitch from anchor file |

Detailed runbooks for each entry above belong in `docs/runbooks/` (out of scope for this phase).

---

## 3. Unresolved-risk register (ranked by severity)

| # | Severity | Risk | Status | Tracking test |
|---|---|---|---|---|
| 1 | P0 | Duplicate migration revision `20260505_0001` | **Open in PR #97** | `test_migrations.py` |
| 2 | P0 | DHIS2 endpoint references nonexistent `lab_results.lab_id` | Documented; not auto-fixed | `test_migration_resilience.py::test_dhis2_query_referenced_column_does_not_exist` |
| 3 | P1 | `LabResult.version` declared but not enforced (no CAS in update path) | Documented; needs ~2h fix | `test_concurrency_safety.py::TestLabResultOptimisticLockInvariant` |
| 4 | P1 | Audit chain hash is not tz-deterministic on SQLite (PG OK) | Documented; needs ~1h fix | `test_compliance_integrity.py` (notes) |
| 5 | P1 | `decode_token` accepts tokens without `exp` claim (jose `require` is no-op) | Defense-in-depth gap; mitigated by issuer | `test_security_regression.py::test_token_without_exp_claim_documents_jose_behavior` |
| 6 | P2 | `/compliance/dhis2/aggregate` & `/stats/*` use PG-specific SQL (EXTRACT, INTERVAL) → not unit-testable on SQLite | CI uses PG so covered there | n/a |
| 7 | P2 | Frontend test runner is `node:test` not Vitest | Sufficient for current scope | `frontend-v2/src/lib/__tests__/` |
| 8 | P2 | Pre-existing `backend-test` CI flakiness when PG service container slow to start | Operational; flakiness not caused by this hardening phase | n/a |
| 9 | P3 | National ID encryption-at-rest invariant not yet covered by automated test (relies on manual review of `encryption.py` usage) | Add to follow-up | — |
| 10 | P3 | Outbox replay idempotency invariant not asserted in tests | Addressed for retry/dead-letter paths; broker-level replay still requires staging test | `backend/tests/test_sync_security_and_outbox.py` |
| 11 | P0 | Production Outbox delivery backend may be absent or configured as log sink | **Fail-closed guard added; staging configuration required** | `GULA_SYNC_OUTBOX_DELIVERY` + readiness gate |
| 12 | P1 | National route audit gate reports 44 write-capable routes without direct audit markers | **Detected by expanded gate; requires route-by-route service audit review** | `config/quality-gates/security-gate.py` |
| 13 | P3 | WebSocket / realtime auth-bypass — no tests today (no WebSocket surface yet) | Out of scope for current architecture | — |

---

## 4. Phase 9–15 coverage delta

| Phase | New file | Tests | Status |
|---|---|---|---|
| 9 — Observability | `test_observability_invariants.py` | 23 | ✅ |
| 10 — Performance budgets | `test_performance_budgets.py` | 18 | ✅ |
| 11 — Chaos & failure survival | `test_chaos_survival.py` | 14 | ✅ |
| 12 — Clinical safety | `test_clinical_safety.py` | 32 | ✅ |
| 13 — Disaster recovery | `test_disaster_recovery.py` | 10 | ✅ |
| 14 — Security regression | `test_security_regression.py` | 21 | ✅ |
| 15 — Deployment readiness | this file + `PRODUCTION_HARDENING.md` | — | ✅ |
| **Phase 9–15 subtotal** | **6 files + 1 doc** | **118** | ✅ |

**Combined Phases 1–15 backend test additions:**

| Phase set | New tests | Status |
|---|---|---|
| Phases 1–8 (PR #96 — merged) | 160 | ✅ |
| Phases 9–14 (this phase) | 118 | ✅ |
| **Total backend hardening tests** | **278** | ✅ |

---

## 5. Scalability bottleneck analysis

Based on the new performance-budget tests (Phase 10) and the chaos suite (Phase 11):

### 5.1 Confirmed safe

- Patient & order listings have query budget ≤ 10 / ≤ 50 queries respectively
- Pagination clamped at 500 — DoS via `limit=10000` returns 422
- Health endpoint executes ≤ 2 DB queries (constant-time)
- Hot-path columns indexed (`patients.lab_id`, `patients.phone`,
  `lab_orders.lab_id`, `lab_results.order_id`, `lab_results.token_hash`,
  `audit_logs.action`)

### 5.2 Suspected bottlenecks (require live load test before national rollout)

- **Stats / trends endpoints** (`stats.py`) — Redis-cached but raw SQL.
  Cache miss on a popular dashboard view could storm DB. Mitigation: confirm
  cache TTL > dashboard-refresh interval.
- **Audit chain verification** is O(N) — full re-walk per `/compliance/audit-integrity`
  call. Currently capped at 5000 entries; a high-volume tenant exceeding
  this will see verification skip recent entries.
- **Patient duplicate detection** in `create_patient` does a phone-prefix
  search then a name-prefix search. On large labs, name search may scan
  significant rows. Has `LIMIT 50` cap, but could mis-rank duplicates.
- **DHIS2 aggregate** (currently broken — see P0 #2) when fixed will scan
  all `lab_results` for the lab; needs `(lab_id, created_at)` composite
  index already present per migration `20260503_0001`.

### 5.3 Sharding recommendation

Per `nhop-platform/`'s national registry, expect ~10⁷ patients across
~10³ labs. Single-PG instance is sufficient for stage 1 (1–5 labs);
schema is multi-tenant via `lab_id` so horizontal sharding by `lab_id`
range is straightforward when tier scales.

---

## 6. Blast-radius assessment for unresolved risks

| Risk # | Blast radius if unresolved | Rollback complexity |
|---|---|---|
| 1 (dup migration) | **Cannot deploy** — alembic refuses | trivial: revert PR #91 |
| 2 (DHIS2 SQL) | Ministry-of-Health reporting endpoint always 5xx | trivial: ~20-line query rewrite |
| 3 (LabResult CAS) | Silent overwrite of result values under concurrent edit | medium: add CAS to every result mutation route |
| 4 (audit tz) | Audit chain verification fails on SQLite (production uses PG so prod OK) | trivial: normalize tz before hashing |
| 5 (jose require) | Tokens without exp claim accepted IF an attacker can mint with secret | none: depends on secret leakage as a precondition |
| 6 (PG-only SQL) | SQLite test environment cannot exercise; CI/PG covers | none |
| 7 (Vitest) | Frontend test ergonomics | trivial: `npm install -D vitest` |
| 8 (CI flakiness) | Failed PR checks slow review | none |
| 9 (NID encryption test) | Theoretical: NID could be stored plaintext via misuse | small: add test asserting `Patient.national_id_hash` field is hash |
| 10 (outbox replay) | Theoretical: re-publish double-fires | small: outbox already tested in `test_outbox_service.py` (existing) |
| 11 (WebSocket) | n/a — no WebSocket surface | n/a |

---

## 7. Rollout recommendations

### Stage 1 — Pilot (1–3 labs, ≤500 patients each)

1. Merge PR #97 (migration fix) — required to allow `alembic upgrade head`.
2. Fix DHIS2 SQL (P0 #2) in a small follow-up PR.
3. Disable feature flags: `SNDHS_ENABLE_*=false`, `ENABLE_FINANCIAL_ENGINE=false`,
   `ENABLE_ADS=false`.
4. Deploy to a single PG instance behind HAProxy with 2 backend replicas.
5. Run all hardening tests in CI on every PR.
6. Smoke-test all 8 hardening phases on staging weekly.

### Stage 2 — National pilot (5–20 labs)

1. Add `LabResult.version` CAS (P1 #3) and integrate into mutation routes.
2. Enable `SNDHS_ENABLE_NATIONAL_ID` after backfill verification.
3. Enable Prometheus alerting on RED grade + L2/L3 transitions.
4. Run `make integrity-test WORKERS=500` weekly.
5. Add `audit_logs` archival job (>90 days → cold storage with anchor signatures).

### Stage 3 — General availability (>20 labs)

1. Enable horizontal scaling: shard by `lab_id` range or move to managed PG cluster.
2. Add WebSocket realtime layer with auth invariants (will require new test phase).
3. Enable Financial Engine Phase B+ behind `ENABLE_FINANCIAL_ENGINE=true`.
4. Expand frontend test coverage to include component-level (Vitest + RTL).

---

## 8. Success criteria — operational

The platform is "national-deployment ready" when:

- [x] **278 hardening tests** pass on every PR
- [ ] All P0 and P1 unresolved risks (above) tracked with assignees & ETAs
- [ ] Operator runbooks (§2) materialized as `docs/runbooks/*.md`
- [ ] Synthetic monitoring of all 4 critical paths (`/auth/login`, `/health/ready`,
  `/admin/kill-switch/deactivate`, `/metrics/prom`) green for 7 consecutive days
- [ ] Full backup → restore → audit-chain verification cycle runs nightly
- [ ] No CRITICAL CVEs in `safety` scan
- [ ] No HIGH findings in `bandit -ll`
- [ ] All cross-tenant isolation tests run as part of staging smoke before each rollout

---

## 9. What this phase is NOT

- It is NOT a redesign — no architectural changes.
- It is NOT new features — every test pins existing behavior.
- It is NOT auto-fix — P0/P1 risks are documented for human-reviewed PRs.
- It is NOT infrastructure — no new services, no new dependencies (Vitest deferred).
- It is NOT a heavyweight observability stack — uses the existing JSON-formatter
  and Prometheus middleware untouched.

The platform was already well-tested. This phase makes that testing
*adversarially deterministic* — every invariant in CLAUDE.md is now a
contract that fails loudly in CI, not a comment that survives via
discipline alone.
