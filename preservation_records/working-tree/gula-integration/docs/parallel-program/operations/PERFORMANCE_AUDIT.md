# PERFORMANCE AUDIT — PROGRAM-GULA-PARALLEL-001 (AGENT 08)

**Platform:** GULA National Healthcare Platform | Iraq
**Wave:** A — READ-ONLY STATIC ANALYSIS. No build, load test, benchmark, query, server or profile was executed. All performance statements are derived from source/config inspection; runtime impact is labelled **speculation** where not directly provable from code.
**Date:** 2026-11-19

---

## 0. Executive summary

Performance tooling is **present but not enforced**. The repository contains a bundle-budget script (wired in CI), a sophisticated SLO gate script (`config/quality-gates/performance-gate.py`), Locust benchmarks, k6 scenarios, Prometheus latency/DB gauges, PostgreSQL tuning, and numerous composite indexes. However:

- The central performance gate is **fail-open** when Prometheus is unreachable and is **not wired into any workflow**.
- Nightly Locust thresholds **print warnings only** and cannot fail the job.
- Production-like Kubernetes memory limits (512 MiB) appear incompatible with the documented multi-worker concurrency model (label: **speculation**, depends on live env).
- Bundle budget measures **raw file bytes**, not compressed transfer size, and uses a fragile hard-coded `dist/assets` path match.
- Several list endpoints call `.all()` with no `LIMIT`, creating unbounded-result-set risk.

No new service, licence, or infrastructure cost is recommended by this audit.

---

## 1. Scope reviewed

| Area | Key files |
|---|---|
| Frontend budget | `frontend-v3/scripts/check-bundle-size.mjs`, `frontend-v3/package.json`, `.github/workflows/frontend-bundle-budget.yml` |
| Perf gates & benchmarks | `config/quality-gates/performance-gate.py`, `.github/workflows/nightly.yml:179-288`, `tests/load/k6-scenarios.js`, `tests/performance/locustfile.py` (existence verified), `Makefile:408-425` |
| Backend hot paths | `backend/app/routes/metrics.py`, `backend/app/routes/admin.py`, `backend/app/routes/national_data.py`, `backend/app/routes/citizen_portal.py`, `backend/app/database.py` |
| DB tuning / indexes | `config/postgres/postgresql.conf`, `backend/app/services/mpi/models.py`, `backend/app/capabilities/fhir_interoperability/models.py`, `backend/app/document_intelligence/infrastructure/models.py` |
| Concurrency/caching | `docker-compose.yml:140-156`, `k8s/base/backend/deployment.yaml:92-99`, `k8s/overlays/prod/patch-resources.yaml:13-19`, `config/pgbouncer/pgbouncer.ini`, Redis `--maxmemory` flags in compose files |

Approximate files inspected: **24**.

---

## 2. Findings

### A08-P001 — P2 — Central SLO performance gate fails open when Prometheus is unreachable, and is not wired into CI

- **Evidence:**
  - `config/quality-gates/performance-gate.py:61-70` — `query_prometheus()` catches all exceptions, logs a warning and returns `[]`.
  - `:73-80` — `get_value_from_result([])` returns `0.0`.
  - `:37-45` — thresholds are *maximums* for latency/error-rate (e.g. `p95_latency_ms.max = 500`); a returned `0.0` therefore satisfies the gate.
  - `:47` — `BASELINE_REGRESSION_PCT = 10.0` comparison is likewise meaningless on synthetic zeros.
  - Workflow grep: no reference to `performance-gate.py` in `.github/workflows/*` or `Makefile`.
- **Affected components:** Performance SLO enforcement, release confidence.
- **Root cause:** Defensive "never crash" helper combined with numeric-default-from-empty; no explicit `up`/data-presence precondition.
- **Safe-fix possible?** Yes — return `None` on query failure and treat missing data as FAIL (or skip with explicit "insufficient data" + non-zero exit); then wire into a non-blocking shadow job first. (Gate file is clean.)
- **Approval required?** **Yes** — adding a CI gate changes gating semantics; coordinate with orchestrator/A09.

### A08-P002 — P2 — Nightly Locust threshold check cannot fail the job; missing results are silently ignored

- **Evidence:**
  - `.github/workflows/nightly.yml:250-288` — on p95/p99 breach (`:268-269`) and error-rate breach (`:284-285`) the script only calls `print("WARNING: …")`; there is **no `sys.exit(1)`** and no `violations` accumulator.
  - `:261-271,273-287` — `FileNotFoundError` handlers only print `"No benchmark stats file found"` and continue.
  - `:255-259` — thresholds exist (p95 500 ms, p99 1000 ms, error rate 1.0%) but are advisory.
  - Contrast `frontend-v3/scripts/check-bundle-size.mjs:52` which correctly does `process.exit(1)` on violations.
- **Affected components:** Nightly performance regression detection.
- **Root cause:** Reporting script written as informational diagnostic rather than an enforceable gate.
- **Safe-fix possible?** Yes — accumulate violations and exit 1, with `continue-on-error: true` initially if a baseline is needed.
- **Approval required?** **Yes** (CI semantics).

### A08-P003 — P2 — Kubernetes backend memory limit appears incompatible with documented worker/pool concurrency

- **Evidence:**
  - `k8s/base/backend/deployment.yaml:92-99` — `limits.memory: 384Mi`; `k8s/overlays/prod/patch-resources.yaml:17-19` — prod `limits.memory: 512Mi`.
  - `docker-compose.yml:140-145` — `WEB_CONCURRENCY: ${WEB_CONCURRENCY:-3}`, `DB_POOL_SIZE: ${DB_POOL_SIZE:-6}`, `DB_MAX_OVERFLOW: ${DB_MAX_OVERFLOW:-12}` with comment `:141` "each ~120 MB RSS".
  - 3 workers × ≈120 MB ≈ 360 MB before Python/interpreter/PDF font overhead; a 512 MiB hard cap leaves very little headroom.
- **Affected components:** Kubernetes backend availability under load (OOMKill risk).
- **Root cause:** Compose-derived sizing guidance not applied to k8s manifests; k8s/Helm and compose are maintained independently (see also A08-002 in DevOps report).
- **Speculation label:** Actual pod env may override `WEB_CONCURRENCY` via `envFrom: configMapRef` (`k8s/base/backend/deployment.yaml:64-66`); `k8s/base/configmap.yaml` was not fully inspected for that key. Confirm before sizing changes.
- **Safe-fix possible?** Yes as a documentation/alerting change; raising limits is a capacity decision, not automatically safe.
- **Approval required?** **Yes** (capacity + cost; no new cost should be added without proven need).

### A08-P004 — P2 — Horizontal scaling can exceed PostgreSQL `max_connections`

- **Evidence:**
  - `config/postgres/postgresql.conf:12` — `max_connections = 100`.
  - `docker-compose.yml:141-142` — documented formula `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < max_connections` with 3 × (6+12) = 54 per container.
  - `docker-compose.scale.yml:33-42` — default `BACKEND_REPLICAS=3` (→ 3 × 54 = 162 > 100).
  - `k8s/overlays/prod/patch-resources.yaml:27-28` — HPA `minReplicas: 5` (→ 5 × 54 = 270 > 100) and `k8s/overlays/prod/patch-replicas.yaml:9` — `replicas: 5`.
  - `docker-compose.full.yml:90-92` — PgBouncer `MAX_CLIENT_CONN: 1000`, `DEFAULT_POOL_SIZE: 50`; the full stack routes microservices through PgBouncer (`docker-compose.full.yml:555` etc.) but the **MVP** compose connects directly to PostgreSQL (`docker-compose.yml:112`).
- **Affected components:** Scaling, connection exhaustion under load.
- **Root cause:** The documented connection-budget formula is not enforced by the scale profile or k8s overlays; PgBouncer exists only in the full stack.
- **Speculation label:** Live env may lower `DB_MAX_OVERFLOW`; still, the defaults in committed manifests breach the document's own rule.
- **Safe-fix possible?** Yes — reduce per-worker pool defaults in scale/k8s profiles, or document that PgBouncer is mandatory when replicas > 1. **Do not add new infrastructure** (PgBouncer already exists in `docker-compose.full.yml:83-106`).
- **Approval required?** **Yes** (capacity/semantics; coordinate with A07).

### A08-P005 — P3 — Bundle budget measures uncompressed bytes with a path-fragile asset filter

- **Evidence:**
  - `frontend-v3/scripts/check-bundle-size.mjs:5-9` — budgets: total 2 500 000 B, entry JS 400 000 B, CSS 180 000 B (raw).
  - `:28` — `assetSizes` filter uses `path.includes(join("dist","assets"))` with a slash-normalising fallback; since `distDir = resolve(...)` (`:4`) is absolute, this works for the default path but breaks if the script is pointed at a differently named build directory.
  - `:29` — `totalBytes` sums **all** files (including source maps if emitted).
  - `:30` — entry detection depends on Vite's `index-<hash>.js` naming.
  - No gzip/Brotli measurement, no per-route/chunk budget, no lazy-load assertion.
- **Affected components:** Frontend transfer-size regression detection.
- **Root cause:** Budget implemented as a simple filesystem-size check.
- **Safe-fix possible?** Yes — add compressed-size reporting (non-blocking initially) and replace the path filter with a `relative(distDir, path)` based check. Script is clean, but `frontend-v3/vite.config.ts` is USER-MODIFIED — do not touch it.
- **Approval required?** **Yes** for gate change; No for report-only enhancement.

### A08-P006 — P3 — Unbounded `.all()` result sets in list endpoints

- **Evidence (representative, non-exhaustive):**
  - `backend/app/routes/national_data.py:562` (`RetentionPolicy.query…all()`), `:602` (consent directives), `:661` (deidentification jobs), `:687` (feature store), `:764` (feature values), `:788` (training datasets).
  - `backend/app/routes/admin.py:120,136,147,265,920` — `.all()` without visible `limit()` in the same statements.
  - Contrast bounded patterns in the same files: `national_data.py:291,454` and `admin.py:128,270,352,478,683` use `.offset(skip).limit(limit)`.
- **Affected components:** Admin/national-data list endpoints under large national datasets.
- **Root cause:** Mixed pagination discipline; some endpoints were authored without pagination.
- **Speculation label:** Whether these tables grow large enough to matter in the Iraqi national deployment was not measured; A07 owns data-volume assessment.
- **Safe-fix possible?** Yes (add pagination with backward-compatible defaults) — **but this is backend code, outside A08's write set**.
- **Approval required?** **Yes** (API contract change; A07 + orchestrator). Logged as SCOPE_REQUEST.

### A08-P007 — P3 — Redis eviction policy differs between compose stacks

- **Evidence:**
  - `docker-compose.yml:61-62` — `--maxmemory 256mb --maxmemory-policy volatile-lru`
  - `docker-compose.full.yml:116-117` and `:143-144` — `--maxmemory 512mb --maxmemory-policy allkeys-lru`
  - `docker-compose.demo.yml:33` — `--maxmemory 128mb --maxmemory-policy volatile-lru`
- **Affected components:** Cache hit rate / eviction behaviour across environments.
- **Root cause:** Independent compose evolution.
- **Speculation label:** Impact depends on which keys carry TTLs; not measured.
- **Safe-fix possible?** Yes (document the intended policy in one place and align). **Approval required?** Yes (runtime semantics).

### A08-P008 — P3 — PgBouncer pool sizing has no wait-time observability wired

- **Evidence:** `docker-compose.full.yml:88-94` — `MAX_CLIENT_CONN: 1000`, `DEFAULT_POOL_SIZE: 50`, `MIN_POOL_SIZE: 10`; `config/prometheus/prometheus.yml:78-91` has the PgBouncer/RabbitMQ-style scrape jobs **commented out**; no PgBouncer exporter service in `docker-compose.full.yml`.
- **Affected components:** Ability to detect pool saturation before it becomes an incident.
- **Root cause:** Monitoring config and full-stack compose diverged.
- **Safe-fix possible?** Yes as documentation/alert-rule note using existing Prometheus. **Adding a new exporter is NOT recommended** without proven need (program rule: no new services/cost).
- **Approval required?** No for doc-only; Yes for new service.

### A08-P009 — P3 — Performance test entry points exist but are not consistently reusable

- **Evidence:**
  - `Makefile:408-425` — `load-test` (k6 → `tests/load/k6-scenarios.js`, HTML report via `scripts/generate-performance-report.py`), `stress-test`, `spike-test`, `soak-test`, `recovery-test`.
  - `.github/workflows/nightly.yml:229-248` — Locust run with `--users 50 --run-time 5m`, artifacts retained 30 days.
  - Two different load tools (k6 + Locust) with **no shared baseline or comparable metric schema**; `config/quality-gates/performance-gate.py:15-17` accepts `--load-test-results results.json` but no workflow produces that file from either tool.
- **Affected components:** Trend analysis, regression baselines.
- **Root cause:** Tool proliferation without a canonical results format.
- **Safe-fix possible?** Yes (document canonical tool/format). **Approval required?** No for documentation.

---

## 3. Positive controls observed

- `backend/app/services/mpi/models.py:65-69,159-161,194-196` and `backend/app/capabilities/fhir_interoperability/models.py:32-34` define purpose-built composite indexes for blocking/identity matching and FHIR lookups; `backend/app/document_intelligence/infrastructure/models.py:71-74` indexes tenant/patient/lab for document queries. (A07 owns deeper DB review.)
- `backend/app/routes/citizen_portal.py:317,376,442` uses `joinedload(LabOrder.results)` to avoid obvious N+1 on result-heavy reads.
- `config/postgres/postgresql.conf:12,18,21,74,76` sets `max_connections`, `shared_buffers`, `work_mem`, `idle_in_transaction_session_timeout = 60 s` and `statement_timeout = 30 s` — sensible runaway-query protection.
- `backend/app/database.py:188-190` exposes `WEB_CONCURRENCY` / `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` as environment-tunable knobs.
- `backend/app/routes/metrics.py:147-201` emits DB/Redis latency gauges and order stats; `config/prometheus/prometheus.yml:7-13` sets 15 s scrape/evaluation intervals.
- `frontend-v3/scripts/check-bundle-size.mjs:39-52` emits structured JSON and exits non-zero on real budget violations.

---

## 4. Wave C candidate eligibility (A08 scope)

Eligible clean files for performance-related doc/CI work: `config/quality-gates/performance-gate.py`, `.github/workflows/nightly.yml`, `frontend-v3/scripts/check-bundle-size.mjs`, `config/prometheus/prometheus.yml`, compose files.
**Ineligible:** `frontend-v3/vite.config.ts` (USER), `frontend-v3/package.json` (USER). Backend route files are outside A08 scope (A07).

---

## 5. SCOPE_REQUESTs

1. **SCOPE_REQUEST-A08-P01:** Add pagination to `backend/app/routes/national_data.py` and `admin.py` `.all()` endpoints — route to A07 (API contract impact).
2. **SCOPE_REQUEST-A08-P02:** Raise/right-size k8s backend memory limits after measuring real RSS — capacity decision for orchestrator; no new cost without proven need.
3. **SCOPE_REQUEST-A08-P03:** Wire `performance-gate.py` into CI (shadow mode) — orchestrator/A09 approval.
4. **SCOPE_REQUEST-A08-P04:** Confirm intended Redis eviction policy and PgBouncer pool defaults with infrastructure owner before aligning manifests.
