# Team A5 — Adversarial Performance & Scalability Audit

**Audit ID:** A5
**Scope:** `gula-integration` working tree at HEAD `2206654dc713ea2de8c564a3207dfe05fde23549` (dirty tree; audited as observed, including tracked modifications/untracked deliverables).
**Method:** READ-ONLY static adversarial review. No operational DB, no network, no benchmark execution.
**Overall verdict on audited work:** **BLOCKED** — performance and scalability assertions in the repository are **NOT MEASURED** by any reproducible end-to-end artifact; where artifacts exist they report failure. No claim of `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` is awarded.

## 0. What was independently confirmed (not awarded)

The following are confirmed to **exist in source** (`IMPLEMENTED` at code level only). This is not verification of runtime behaviour:

- Stats caching helpers, SLO recording/alert rules, a Prometheus-format metrics endpoint, k6 load scripts, Redis cache manager with L1/L2 tiers, DB pool configuration, a read-replica session factory, and a performance-budget test module.
- None of the above was executed. **No latency, throughput, concurrency, availability, or error-budget value in this report is measured by this audit.** All such values are `NOT MEASURED`.

## 1. Headline finding

The **99.99% availability SLO is nonfunctional as written.** The gauge it consumes is a hardcoded constant, so the SLO cannot observe downtime. Simultaneously, the repository's `PERFORMANCE_CERTIFICATION.md` reports `Status: PASS` with worker/pool values that **contradict the code defaults**, while the only benchmark result artifact on disk reports `overall_status: FAIL`, and no k6 result artifact exists. The performance assurance chain is broken at the measurement source, the rule layer, and the certification layer.

## 2. Findings

### AUD-PERF-001 — Availability SLO computed from a hardcoded gauge; 99.99% target is unobservable (HIGH)

- **Evidence**
  - `backend/app/services/metrics_service.py:385-392` — metrics exposition emits literal `gula_up 1` and `gula_down 0` on every scrape; no probe determines these values.
  - `config/prometheus/rules/slo.yml:12-18` — `slo:availability_window` uses `sum(rate(gula_up[30d])) / sum(rate(gula_up{}[30d]) + rate(gula_down{}[30d]))`. `rate()` over a gauge that is permanently `1` yields no downtime signal.
  - `config/prometheus/rules/slo.yml:116-126` — `SLOAvailabilityBelow` alerts on `slo:availability_window < 99.99`, therefore can never fire for real downtime.
  - `backend/app/services/metrics_service.py:15-25` — request counters/latency are process-local dicts, so even the error-budget rules (`slo.yml:31-50`) aggregate only one worker's view unless externally combined.
- **Reproduction / falsification:** Read the three cited locations. Falsify by demonstrating any code path that sets `gula_up` to `0` based on a real health probe and a scrape showing it; or by producing a recorded availability series from an external black-box probe. None found.
- **Root cause:** Availability was modelled as a static self-report rather than a probed signal.
- **Impact:** A declared 99.99% availability target provides false assurance; real outages are invisible to its alert. Availability is `NOT MEASURED`.
- **Severity:** HIGH · **Likelihood:** HIGH (deterministic — the rule is inert) · **Status:** `DISCOVERED` · **owner_gated:** YES (SLO targets/definitions are owner decisions; do not change the 99.99% target without approval).
- **Recommended remediation:** Replace the hardcoded gauges with black-box probe results (e.g. exporter recording actual `/health/ready` outcomes), keep the owner-approved 99.99% target unchanged, and aggregate counters across workers before recording error-budget rules. Add a regression test that flips the probe to down and asserts `SLOAvailabilityBelow` evaluates true.
- **Alternatives:** (a) Compute availability from a load-balancer/ingress access-log SLI instead of app gauges; (b) keep the app metric but rename it to `gula_self_report_up` and explicitly exclude it from SLO rules.

### AUD-PERF-002 — Performance certification claims contradict source defaults; supporting evidence is failing or absent (HIGH)

- **Evidence**
  - `backend/app/database.py:188-192` — defaults `WEB_CONCURRENCY=2`, `DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=10`.
  - `PERFORMANCE_CERTIFICATION.md:58-63` — claims `Workers 3 (default)`, `DB pool 18 conn (3 × 6)`, and `## Status: PASS ✅`.
  - `contracts/quality/benchmark-results.json:7` — `"overall_status": "FAIL"` (the only benchmark result artifact discovered on disk).
  - `k6/load_test.js` — load script present; no corresponding k6 result/export artifact found anywhere in the tree (verified by repository-wide filename search).
- **Reproduction / falsification:** Compare the four cited sources. Falsify by supplying a reproducible load-run artifact (k6 summary JSON) and a deployment manifest showing workers=3/pool=18 with matching env overrides. Neither was found.
- **Root cause:** Certification text was authored from intended rather than effective configuration, and no result artifact is bound to the PASS claim.
- **Impact:** `PASS` is unsupported; a reader cannot reproduce any stated number. Throughput and latency are `NOT MEASURED`.
- **Severity:** HIGH · **Likelihood:** HIGH (documented values are demonstrably inconsistent) · **Status:** `DISCOVERED` · **owner_gated:** YES (certification status and target topology are owner/governance decisions).
- **Recommended remediation:** Regenerate the certification from a checked-in, timestamped load artifact; reconcile worker/pool values with `database.py` defaults or document the exact env overrides in the deployment manifest; change status to `BLOCKED` until a passing, reproducible run exists.
- **Alternatives:** (a) Downgrade the document to an explicitly labelled design target with no PASS status; (b) pin configuration in code so documentation and runtime cannot diverge.

### AUD-PERF-003 — Per-call Redis client creation, sequential bulk operations, and blocking Redis calls inside async methods (MEDIUM)

- **Evidence**
  - `backend/app/services/stats_service.py:22-53` — `_get_redis()` calls `_redis.from_url(...)` on every `_cache_get` / `_cache_set`; no shared connection pool.
  - `backend/app/services/stats_service.py:242-287` — `stats_summary` issues nine sequential `.scalar()` COUNT queries (patients, orders, tests, critical, today/week/month orders, critical-today) with no batching or combined query.
  - `backend/app/core/cache_manager.py:314-338` — `get_many` / `set_many` iterate keys sequentially with individual awaits.
  - `backend/app/core/cache_manager.py:402-419` — `_l2_get` / `_l2_set` invoke synchronous `redis_cache.get/set` from `async def` methods without offloading, blocking the event loop on network I/O.
- **Reproduction / falsification:** Static trace of the cited call sites. Falsify by showing a module-level pooled client reused across calls and non-blocking L2 access (e.g. `asyncio.to_thread` or an async Redis client).
- **Root cause:** Convenience helpers written synchronously and later wrapped in async signatures without I/O offload or connection reuse.
- **Impact:** Connection churn (TCP/TLS handshake per cache op), event-loop stalls under load, and nine round-trips per stats cache miss. Actual latency amplification is `NOT MEASURED`.
- **Severity:** MEDIUM · **Likelihood:** HIGH under concurrent load · **Status:** `DISCOVERED` · **owner_gated:** NO.
- **Recommended remediation:** Create one module-level Redis client with a bounded pool; replace the nine counts with a single grouped aggregate query; convert bulk cache ops to pipeline/MGET and offload blocking L2 calls via `asyncio.to_thread` or an async client. Add a regression test asserting one client construction and bounded query count.
- **Alternatives:** (a) Replace per-key caching with a single cached summary blob keyed by `(lab_id, window)`; (b) materialise dashboard counters via a scheduled aggregate table.

### AUD-PERF-004 — Async compatibility layer runs blocking SQL; read replica is defined but unused (MEDIUM)

- **Evidence**
  - `backend/app/database.py:301-317` — `_AwaitableProxy` wraps an already-computed **synchronous** result and merely makes it awaitable; it does not yield control, so the underlying SQL executes inline.
  - `backend/app/database.py:379-384` — `get_read_db()` is defined with a docstring directing read-only routes to use it.
  - `backend/app/database.py:246` — comment states "Routes use get_read_db() for read-only operations to distribute load."
  - Repository-wide search: **no route imports or depends on `get_read_db`**; the only other occurrence is the comment above.
- **Reproduction / falsification:** `grep -rn "get_read_db" backend/app --include='*.py'` returns only the definition and the comment. Falsify by identifying any route dependency on it.
- **Root cause:** Read-scaling path was added but never wired; async-looking API is a compatibility shim over synchronous SQLAlchemy sessions.
- **Impact:** Read scaling is inert; async endpoints can block workers on DB I/O. Any read-capacity claim is `NOT MEASURED`.
- **Severity:** MEDIUM · **Likelihood:** HIGH (code fact) · **Status:** `DISCOVERED` · **owner_gated:** NO (wiring/dead-code decision; enabling an actual replica has a separate infra dependency).
- **Recommended remediation:** Either route genuinely read-only endpoints through `get_read_db` and verify replica lag, or remove the dead dependency/comment to prevent false capacity assumptions. Move blocking session work to a threadpool where async endpoints require it.
- **Alternatives:** (a) Adopt a fully async SQLAlchemy engine for the affected paths; (b) keep sync sessions but declare those routes `def` (FastAPI threadpool) rather than presenting them as async.

### AUD-PERF-005 — Metrics endpoint is process-local and performs synchronous work per scrape (MEDIUM)

- **Evidence**
  - `backend/app/services/metrics_service.py:15-25` — all counters/buckets are module-level dicts, one set per process.
  - `backend/app/services/metrics_service.py:56-66` — `ping_redis()` performs a synchronous `cache.ping()` call.
  - `backend/app/services/metrics_service.py:101-115` — `get_queue_backlog()` opens a **new** `SessionLocal()` and runs a COUNT on every scrape, then closes it.
  - `config/prometheus/rules/slo.yml:24-25,31-50` — error-budget and latency rules consume these counters.
- **Reproduction / falsification:** Trace the cited functions. Falsify by showing cross-worker metric aggregation and a cached/background backlog collector.
- **Root cause:** Scrape-time computation and per-process instrumentation.
- **Impact:** With multiple workers, SLO error-budget/latency records reflect an arbitrary single process; scrapes add DB load proportional to scrape frequency. Error-budget and p99 values are `NOT MEASURED`.
- **Severity:** MEDIUM · **Likelihood:** MEDIUM · **Status:** `DISCOVERED` · **owner_gated:** NO.
- **Recommended remediation:** Export per-worker series and aggregate in Prometheus, or use a shared metrics backend; collect backlog in a background task rather than during scrape; bound scrape duration.
- **Alternatives:** (a) Use the app's existing OTLP/HTTP tracing pipeline for latency instead of in-process buckets; (b) derive error budget from ingress logs rather than app counters.

### AUD-PERF-006 — Load test covers health/read paths only; write path and concurrency unverified; no result artifact (MEDIUM)

- **Evidence**
  - `k6/load_test.js:115-179` — default function groups are liveness/health and read-only API calls; no POST/PUT/patch scenario and no sustained write mix.
  - `backend/tests/test_performance_budgets.py:19-21` — explicitly "pure SQLAlchemy + TestClient — no live DB profile needed"; these are query-count guards, not load tests.
  - Only `contracts/quality/benchmark-results.json` exists as a result artifact, and it reports `FAIL` at line 7.
- **Reproduction / falsification:** Inspect the k6 script for mutating HTTP verbs and search the tree for k6 summary exports. Falsify by providing a write-mixed k6 run with a checked-in result artifact.
- **Root cause:** Performance assurance scoped to read surfaces and micro-benchmarks.
- **Impact:** Throughput under write contention, lock behaviour, and cache-stampede resistance are `NOT MEASURED`.
- **Severity:** MEDIUM · **Likelihood:** HIGH (scope limitation is a code fact) · **Status:** `DISCOVERED` · **owner_gated:** NO.
- **Recommended remediation:** Add a write-heavy scenario with realistic tenant/lab mix and idempotency keys; check in the k6 summary artifact; gate the performance certification on its thresholds. Never run against production data.
- **Alternatives:** (a) Use a synthetic single-tenant dataset for write load; (b) add queue-depth/lock-wait instrumentation as a cheaper leading indicator.

### AUD-PERF-007 — Unbounded page size on administrative lab listing (LOW)

- **Evidence:** `backend/app/routes/admin.py:104-110` — `limit: int = 50` is a plain default with no `Query(..., le=...)`, so a caller may request an arbitrarily large page.
- **Reproduction / falsification:** Call `GET /admin/labs?limit=1000000` with an authorised principal; no upper-bound validation is applied at this signature. Falsify by showing a global query-param clamp middleware.
- **Root cause:** Missing bound on a FastAPI query parameter.
- **Impact:** Unbounded result materialisation/serialisation and memory pressure; a cheap amplification vector for authorised users.
- **Severity:** LOW · **Likelihood:** MEDIUM · **Status:** `DISCOVERED` · **owner_gated:** NO.
- **Recommended remediation:** Use `Query(50, ge=1, le=500)` consistent with other list endpoints; add a test for the 422 rejection above the cap.
- **Alternatives:** (a) Enforce a global list-endpoint cap middleware; (b) use cursor pagination for this endpoint.

## 3. Coverage and limitations

| Area inspected | Result |
|---|---|
| Stats aggregation & caching | AUD-PERF-003 |
| Metrics/SLO rule chain | AUD-PERF-001, AUD-PERF-005 |
| DB pool, session & replica wiring | AUD-PERF-002 (config), AUD-PERF-004 |
| Cache manager (L1/L2, bulk) | AUD-PERF-003 |
| Load/benchmark evidence | AUD-PERF-002, AUD-PERF-006 |
| List-endpoint bounds | AUD-PERF-007 |
| Latency / throughput / availability / error budget | **NOT MEASURED** — no execution permitted, no passing result artifact found |
| Production readiness | **BLOCKED** — no basis to award `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` |

**Disclosure discipline:** `10_RELIABILITY_OFFLINE_SURVEY.md:16-21` already discloses `BLOCKED`/`NOT IMPLEMENTED` for durability and RPO/RTO; those known disclosures are **not** re-reported as performance findings here. The pre-existing `NR-011` FK test under `tests/identity` was not re-reported.
