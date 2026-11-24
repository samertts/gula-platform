# DEVOPS AUDIT — PROGRAM-GULA-PARALLEL-001 (AGENT 08)

**Platform:** GULA National Healthcare Platform | Iraq
**Wave:** A — READ-ONLY AUDIT. No source/config file was modified. No build, test, server, deploy or scale command was executed.
**Date:** 2026-11-19
**Scope:** Docker/compose, CI/CD workflows, build/lint/typecheck/test gate wiring, observability plumbing.
**Evidence standard:** `path:line` references to the working tree at HEAD `2206654d`. Speculation is explicitly labelled.

---

## 0. Executive summary

The repository has a **large and mostly well-intentioned CI/DevOps surface**: 32 GitHub Actions workflows (the program brief says 30 — see A08-017), centrally pinned action SHAs in most workflows, least-privilege top-level `permissions` blocks in all 32, an opt-in monitoring profile, a token-protected Prometheus metrics endpoint, and a hardened MVP `docker-compose.yml`.

However, several **high-impact correctness defects** exist:

1. The backend image build context is inconsistent with `backend/Dockerfile`, so `make ci` and the nightly container scan are expected to fail at `COPY backend/requirements.txt` (A08-001).
2. CI runs Python 3.12 while every production/container image and several other gates run Python 3.14 (A08-002).
3. Two CodeQL workflows and two GitHub Pages workflows duplicate the same work on every `main` push/PR (A08-003, A08-016).
4. Blue-green/canary/auto-rollback workflows contain logic errors (detailed in `RELIABILITY_AUDIT.md`), so the advertised automated recovery is not actually automatic or effective.
5. A commercial/paid CLI (`safety check`) is used in the main CI gate despite free, already-referenced alternatives (`pip-audit`) — a Constitution violation requiring documented exception (A08-004).

**Constitution check (AGENTS.md):** Free First / Open Source First / Zero Paid Dependency is **NOT fully satisfied** in CI (`safety`) and in backup documentation (commercial SaaS recommendations — see Reliability report). No new dependency was introduced by this audit.

---

## 1. Inventory reviewed

| Surface | Count | Key paths |
|---|---|---|
| Control documents | 5 | `AGENTS.md`, `docs/parallel-program/{PROGRAM_CONTROL,AGENT_ASSIGNMENTS,FILE_OWNERSHIP_MATRIX,CONFLICT_REGISTER}.md` |
| Workflows | 32 (all enumerated; 18 read in full/targeted detail) | `.github/workflows/*.yml` |
| Dockerfiles | 15 | `Dockerfile`, `backend/Dockerfile`, `frontend-v3/Dockerfile`, `docker/Dockerfile`, `platform/Dockerfile`, `nhop-platform/Dockerfile`, `services/*/Dockerfile` (9) |
| Compose files | 12 inventoried, 5 read in full | `docker-compose.yml`, `docker-compose.full.yml`, `docker-compose.scale.yml`, `docker-compose.demo.yml`, `docker/docker-compose.yml` |
| Build manifests | 5 | `Makefile`, `package.json`, `frontend-v3/package.json`, `backend/pyproject.toml`, `backend/requirements*.txt`, `backend/pytest.ini` |
| Observability config | 6 | `config/prometheus/prometheus.yml`, `scripts/generate-metrics-token.sh`, `backend/app/routes/metrics.py`, `config/grafana/provisioning/datasources/datasources.yml`, `shared/logging/config.py`, `backend/app/core/logging_config.py` |
| Gate scripts | 7 | `config/quality-gates/*.py`, `frontend-v3/scripts/check-bundle-size.mjs`, `frontend-v3/playwright.config.ts`, `scripts/quality_changed_files_gate.py` |
| IaC (static read) | ~20 | `k8s/base/**`, `k8s/overlays/prod/**`, `helm/gula-platform/**`, `terraform/environments/**` |

**Approximate files inspected: 107.**

---

## 2. Findings

### A08-001 — P1 — Backend Docker build context contradicts backend/Dockerfile; local CI build and nightly container scan expected to fail

- **Evidence:**
  - `backend/Dockerfile:3` — comment: `Repository-root build context: this file lives in backend/Dockerfile.`
  - `backend/Dockerfile:11` — `COPY backend/requirements.txt ./requirements.txt`
  - `backend/Dockerfile:33-38` — `COPY backend/app ./app`, `COPY backend/migrations ./migrations`, `COPY shared ./shared`
  - `docker-compose.yml:88-90` — `build: context: ./backend` (no `dockerfile:` override → defaults to `backend/Dockerfile`)
  - `docker-compose.full.yml:713` — `build: ./backend`
  - `.github/workflows/nightly.yml:300` — `docker build -t gula-backend:nightly ./backend`
  - `Makefile:264` — `docker compose build gula-backend`
  - Verified absence: no `backend/backend/` directory exists on disk.
- **Affected components:** `make ci`, nightly container security scan, `docker compose build`, all `*-build` developer flows.
- **Root cause:** `backend/Dockerfile` was authored for repository-root context; every caller passes `./backend` as context. `COPY backend/...` therefore resolves to non-existent `./backend/backend/...`.
- **Safe-fix possible?** Yes — set compose/nightly build context to `.` with `dockerfile: backend/Dockerfile` (or change the Dockerfile COPY paths). Static-only: not applied.
- **Approval required?** **Yes.** Changes CI/build semantics and touches several operational files; orchestrator + A07 (backend) review needed before Wave C.

### A08-002 — P1 — Python runtime drift: CI tests on 3.12, production images and other gates on 3.14

- **Evidence:**
  - `.github/workflows/ci.yml:18` — `PYTHON_VERSION: "3.12"` with comment `Keep CI aligned with the Python version used by the Railway backend` (contradicted below).
  - `.github/workflows/quality-changed-files.yml:28`, `.github/workflows/nightly.yml:20` — `"3.12"`
  - `.github/workflows/quality-gate.yml:20`, `.github/workflows/foundation-gate.yml:19`, `.github/workflows/constitution-compliance.yml:17` — `"3.14"`
  - `Dockerfile:5,13`, `backend/Dockerfile:7,18`, all `services/**/Dockerfile:1` — `FROM python:3.14-slim`
  - `backend/pyproject.toml:9` — `requires-python = ">=3.12"`
- **Affected components:** CI test/migration gates, lint gate, nightly integration/performance jobs, all container images.
- **Root cause:** No single source of truth for runtime version; env vars duplicated across 32 workflows and Dockerfiles.
- **Safe-fix possible?** Yes (align to one version, ideally the image version 3.14, after confirming dependency compatibility).
- **Approval required?** **Yes.** Changing gate runtime can change pass/fail outcomes; A07 owns backend compatibility assessment.

### A08-003 — P2 — Duplicate CodeQL workflows scan the same languages and publish to the same categories

- **Evidence:**
  - `.github/workflows/codeql.yml:12-20` — name `CodeQL Advanced`; push/PR `main`; weekly `cron: '39 23 * * 0'`; matrix `python`, `javascript-typescript` (`:48-52`).
  - `.github/workflows/codeql-analysis.yml:1-9` — name `CodeQL Analysis`; push `main` + `release/*`, PR `main`; weekly `cron: '0 6 * * 1'`; identical language matrix (`:26-31`).
  - Both use the same `category: '/language:${{ matrix.language }}'` (`codeql.yml:101`, `codeql-analysis.yml:47`) and the same pinned `github/codeql-action` SHA.
- **Affected components:** Code scanning, Actions minutes, alert deduplication.
- **Root cause:** Two generations of the CodeQL template coexist; neither was retired.
- **Safe-fix possible?** Yes — keep one (recommend `codeql-analysis.yml`, which uses `+security-and-quality` at `:42`) and disable/delete the other, or differentiate categories. Both files are clean in `git status`.
- **Approval required?** **Yes.** Removing a security gate requires orchestrator/A04 approval even if redundant.

### A08-004 — P2 — Constitution violation: commercial `safety` CLI used as a blocking CI gate; free alternative already available

- **Evidence:**
  - `.github/workflows/ci.yml:317-322` — `pip install safety` → `safety check -r requirements.txt --full-report` (blocking step).
  - `backend/requirements.txt:35` — comment explicitly references `pip-audit` as the tool that found 55 findings.
  - `AGENTS.md:9-24` — Free First / Open Source First / Zero Paid Dependency.
- **Affected components:** `CI Pipeline / security-scan` job; cost & license compliance.
- **Root cause:** Historical tooling choice not re-evaluated against the Constitution; modern Safety CLI requires account/auth for full database access (label: **speculation** regarding current licensing terms — verify with A04 before action).
- **Safe-fix possible?** Yes — replace with `pip-audit` (Apache-2.0), which is already the documented audit source.
- **Approval required?** **Yes.** Security-gate change; A04 must approve.

### A08-005 — P2 — Image pinning gate accepts mutable tags; no Dockerfiles are digest-pinned

- **Evidence:**
  - `.github/workflows/quality-gate.yml:60-76` — case `*@sha256:*` → OK(digest), `*:*` → OK(tagged); only `:latest`/bare distro names fail.
  - All 15 Dockerfiles use mutable tags, e.g. `Dockerfile:5,13` and `backend/Dockerfile:7,18` `python:3.14-slim`; `frontend-v3/Dockerfile:3` `node:22.13-alpine`, `:13` `nginx:1.28-alpine`; `services/lab/Dockerfile:1` etc.
  - `docker-compose.yml` image tags are generally pinned to version tags (`postgres:17-alpine`, `prom/prometheus:v2.56.1`) — better, but still not digest-pinned.
- **Affected components:** Reproducible builds, supply-chain posture.
- **Root cause:** Gate defines "tagged" as "pinned"; no digest pinning policy exists.
- **Safe-fix possible?** Partial — the gate text can be corrected statically; actual digest pinning requires resolving current digests (network) and coordinated updates.
- **Approval required?** **Yes** for gate semantics; **no** for documentation-only note.

### A08-006 — P2 — Legacy `docker/docker-compose.yml` stack is internally inconsistent and unhardened

- **Evidence:**
  - `docker/Dockerfile:26-30` — gunicorn binds port **10000**.
  - `docker/Dockerfile:23-24` — healthcheck probes `http://localhost:10000/health`.
  - `docker/docker-compose.yml:8-9` — maps host `8000:8000` (container port 8000, not 10000).
  - `docker/docker-compose.yml:12,18` — `image: redis`, `image: nginx` (floating `latest`).
  - `docker/docker-compose.yml:1` — obsolete `version: "3"`; no `restart`, `mem_limit`, `security_opt`, or healthchecks.
- **Affected components:** Any developer following `docker/docker-compose.yml`; potential confusion with the hardened root compose.
- **Root cause:** Stale parallel dev environment not aligned with the current `docker-compose.yml` (which correctly uses `/health/ready`, resource limits, `no-new-privileges`, `restart: always`).
- **Safe-fix possible?** Yes — either deprecate with a README header or align ports/images/hardening.
- **Approval required?** **Yes** (operational semantics).

### A08-007 — P2 — Full-stack compose: Vault in dev mode, public MinIO metrics, monitoring ports exposed, version drift vs MVP compose

- **Evidence:**
  - `docker-compose.full.yml:418-421` — `vault server -dev -dev-root-token-id=${VAULT_TOKEN}`; comment at `:418` admits "INSECURE - data is in-memory only" despite `vault-data` volume at `:430`.
  - `docker-compose.full.yml:352` — `MINIO_PROMETHEUS_AUTH_TYPE: public`.
  - `docker-compose.full.yml:454-455,463-471,481-487,512-518` — Prometheus/Grafana/Loki/Jaeger ports bound to all interfaces; contrast `docker-compose.yml:305-309` (internal-only, SSH tunnel) and `:283` (`127.0.0.1:8080:80`).
  - Version drift: `docker-compose.full.yml:446` `prom/prometheus:v2.56.0` vs `docker-compose.yml:359` `v2.56.1`; `:463` `grafana/grafana:11.6.0` vs `docker-compose.yml:392` `11.7.1`.
  - `docker-compose.full.yml:469` — runtime plugin install `GF_INSTALL_PLUGINS: grafana-piechart-panel,grafana-worldmap-panel` (supply-chain surface).
- **Affected components:** Secrets management, metrics confidentiality, observability consistency.
- **Root cause:** Two independently maintained compose stacks with divergent hardening baselines.
- **Safe-fix possible?** Yes for tag alignment and documentation; **No** for Vault productionisation (needs KMS/unseal design and A04 approval).
- **Approval required?** **Yes** (security semantics; A04).

### A08-008 — P2 — Floating action tags in frontend bundle workflow, inconsistent with repo-wide SHA pinning policy

- **Evidence:** `.github/workflows/frontend-bundle-budget.yml:27` `actions/checkout@v4`, `:30` `actions/setup-node@v4`; compare SHA-pinned actions in `ci.yml:31-32`, `codeql.yml:70`, `nightly.yml:303`.
- **Affected components:** Supply-chain integrity of the bundle-budget gate.
- **Root cause:** Workflow added later without applying the SHA-pinning convention documented in `codeql.yml:66` ("Any added action must be pinned to a full 40-character commit SHA").
- **Safe-fix possible?** Yes — replace `@v4` with the same SHAs already used in `ci.yml` (`checkout@3d3c42e…`, `setup-node@820762…`). File is clean.
- **Approval required?** **Yes** (CI change, per program rule).

### A08-009 — P2 — Frontend governance gates effectively unwired; aggregate `check` script uses a different package manager than CI

- **Evidence:**
  - `frontend-v3/package.json:21` — `check` = `pnpm typecheck && pnpm test && pnpm verify:unification && … && pnpm build && pnpm check:bundle`.
  - `frontend-v3/package.json:8-23` — scripts are npm-invoked elsewhere; `package-lock.json` is committed; `frontend-v3/Dockerfile:8` uses `npm ci`; `ci.yml:198,207` uses `npm ci` / `npm run build`.
  - No workflow invokes `npm run check`; grep across `.github/workflows/` for `verify:unification`, `verify:contracts`, `verify:integration-boundary`, `verify:data-sources`, `verify:audit-artifacts` → **no matches**.
  - `frontend-bundle-budget.yml:43` does wire `check:bundle` directly (correct).
- **Affected components:** Frontend unification/contract/data-source/audit-artifact governance gates; build reproducibility.
- **Root cause:** `pnpm` used in the aggregate script while the repository standardised on npm; orchestrator never wired the aggregate.
- **Safe-fix possible?** Yes — change `pnpm` → `npm` and add an aggregate CI step (but **file is USER-MODIFIED** per `PROGRAM_CONTROL §2.2` → ineligible for Wave C).
- **Approval required?** **Yes** (user-owned file + CI semantics). Logged as SCOPE_REQUEST.

### A08-010 — P2 — Makefile quality gates are non-blocking even in "strict" mode

- **Evidence:** `Makefile:312-318` — both `quality-gate` and `quality-gate-strict` end with `|| true`.
- **Affected components:** Local/foundation quality enforcement; any caller relying on exit codes.
- **Root cause:** Deliberate warning-only design; "strict" is misleading.
- **Safe-fix possible?** Yes — remove `|| true` from `quality-gate-strict`.
- **Approval required?** **Yes** (gate semantics).

### A08-011 — P2 — `preview-deploy.yml` is a no-op and suppresses install failures

- **Evidence:** `.github/workflows/preview-deploy.yml:19-23` — `npm install --ignore-scripts 2>/dev/null || true` followed by `echo "Frontend install attempted"`. No build, preview URL, artifact, or deployment step exists, despite the workflow name and `pull_request` trigger.
- **Affected components:** PR preview assurance; developer expectations.
- **Root cause:** Placeholder workflow committed as if complete.
- **Safe-fix possible?** Yes (implement build + artifact + PR comment, or rename to `verify-frontend-install` and drop `|| true`).
- **Approval required?** **Yes** (CI semantics).

### A08-012 — P2 — No test-coverage gate wired in CI

- **Evidence:**
  - `ci.yml:288-301` — `python -m pytest tests/ -v --timeout=60 -x` with no `--cov`/threshold.
  - `package.json:14` — `test:coverage` script exists but is not referenced by any workflow.
  - `frontend-v3/package.json:13` — `vitest run …` with no coverage; `ci.yml:200-208` runs lint/typecheck/build but **not** `npm test`.
- **Affected components:** Regression assurance for backend and frontend unit suites.
- **Root cause:** Gate list assembled from available scripts, but coverage and FE unit tests were never added to the pipeline.
- **Safe-fix possible?** Yes (add `--cov` with a non-blocking baseline first, and `npm test` step).
- **Approval required?** **Yes** (gate semantics; A09 for test ownership).

### A08-013 — P2 — Two GitHub Pages workflows deploy on every `main` push

- **Evidence:**
  - `.github/workflows/jekyll-gh-pages.yml:4-8` push `main` + workflow_dispatch; `:30-51` Jekyll build + `deploy-pages`.
  - `.github/workflows/static.yml:4-8` push `main` + workflow_dispatch; `:33-43` static artifact + `deploy-pages`.
  - Both declare `pages: write`, `id-token: write` (`jekyll-gh-pages.yml:15-16`, `static.yml:15-16`).
- **Affected components:** GitHub Pages publishing (race/conflict possible; impact **speculation** — actual Pages configuration was not inspected).
- **Root cause:** Template duplication.
- **Safe-fix possible?** Yes — disable one after confirming which Pages source is canonical.
- **Approval required?** **Yes** (deployment semantics).

### A08-014 — P3 — Node.js version drift across workflows

- **Evidence:** `ci.yml:19` `22`; `frontend-bundle-budget.yml:32` `22`; `iam-hardening.yml:19` `22`; vs `frontend-e2e.yml:28`, `preview-deploy.yml:18`, `formatting.yml:35`, `nightly.yml:19`, `release.yml:28`, `sdk-publish.yml:22`, `frontend-pwa.yml:35` → `24`. `frontend-v3/package.json` has no `engines` field; root `package.json:82-84` requires `>=22`.
- **Affected components:** Build reproducibility; "works on my runner" failures.
- **Root cause:** No central Node version env at organization level.
- **Safe-fix possible?** Yes (document + align); **Approval required?** Yes (CI change).

### A08-015 — P3 — Prometheus scrapes exporters that do not exist in the MVP stack

- **Evidence:** `config/prometheus/prometheus.yml:58-76` defines `postgres-exporter:9187`, `redis-exporter:9121`, `nginx-exporter:9113` with comment `:63` `Will fail silently if not running — that is OK`; no such services in `docker-compose.yml`. Full-stack jobs (`:80-91`) are commented out, so RabbitMQ/ClickHouse/MinIO are never scraped even in the full stack.
- **Affected components:** Monitoring coverage / false confidence in dashboards.
- **Root cause:** Config copied from a fuller topology; exporters not included in the deployed profile.
- **Safe-fix possible?** Yes (document `up==0` expectations or add exporters — adding services is **not** recommended without proven need per program rules). **Approval required?** No for documentation-only change; Yes if adding services.

### A08-016 — P3 — Service/container hardening gaps outside the primary backend/frontend images

- **Evidence:**
  - Unpinned pip dependencies: `services/ai/Dockerfile:5`, `services/lab/Dockerfile:5`, `services/patient/Dockerfile:5` (e.g. `pip install fastapi uvicorn[standard] requests pika …`).
  - No HEALTHCHECK: `nhop-platform/Dockerfile:1-27`, `platform/Dockerfile:1-19`, `services/device_bridge/Dockerfile:1-15`.
  - `services/device_bridge/Dockerfile:7-8` copies `pyproject.toml` but installs a hardcoded dependency list, creating dependency drift.
  - `frontend-v3/Dockerfile:15` comment claims "Run the static server as the unprivileged nginx user" but there is **no `USER nginx`** directive (`:13-23`).
  - No `frontend-v3/.dockerignore` (only root and `backend/` have one), so local `node_modules` can enter the build context.
- **Affected components:** Secondary services, frontend runtime hardening, build context size.
- **Root cause:** Dockerfiles authored ad hoc per service; no shared base/lint gate beyond the weak `quality-gate.yml` check.
- **Safe-fix possible?** Yes; **Approval required?** Yes (container runtime/CI semantics). `services/lab/Dockerfile` is **USER-MODIFIED** and ineligible.

### A08-017 — P3 — Workflow inventory mismatch: 32 workflows present vs 30 stated in the program brief

- **Evidence:** `ls -1 .github/workflows/*.yml` → 32 files (full list in §1); `PROGRAM_CONTROL.md:171` states 30.
- **Affected components:** Program accounting only.
- **Root cause:** Stale program brief figure (two additional workflows: likely `codeql-analysis.yml` and one mobile/static variant — attribution is **speculation**).
- **Safe-fix possible?** N/A (report only). **Approval required?** No.

### A08-018 — P3 — Tracked placeholder metrics-token file has no ignore rule; real token can be committed accidentally

- **Evidence:** `config/prometheus/metrics_token` is tracked (`git ls-files` confirms) and contains a 33-byte placeholder beginning `REPL…` (value intentionally not reproduced here). `scripts/generate-metrics-token.sh:16,26-27` writes the real token into that same tracked path and `chmod 600`. `.gitignore` has no rule for it.
- **Positive control:** `backend/app/routes/metrics.py:139-145` fails closed in production (503 if no token, 401 on mismatch), and `config/prometheus/prometheus.yml:40-42` uses `credentials_file`.
- **Affected components:** Metrics scraping credential hygiene.
- **Root cause:** Generated secret stored at a tracked path.
- **Safe-fix possible?** Yes — add `.gitignore` entry + ship `metrics_token.example` (file is clean). **Approval required?** Yes (small config change; coordinate with A04).

---

## 3. Gate coverage matrix (static wiring only — nothing executed)

| Gate / script | Exists | Wired in CI | Effective? | Evidence |
|---|---|---|---|---|
| Python syntax compile (all `backend/app`) | Yes | Yes | Yes | `ci.yml:35-81` |
| flake8 / ruff E9,F (F401,F841 ignored) | Yes | Yes | Yes (partial) | `ci.yml:82-87,190-191` |
| Backend pytest (full suite) | Yes | Yes | Yes | `ci.yml:288-301` |
| Clinical P0 regression subset | Yes | Yes | Yes | `ci.yml:266-286` |
| Alembic upgrade/downgrade round-trip | Yes | Yes | Yes | `ci.yml:147-176` |
| Data Preservation Gate | Yes | Yes | Yes (exit 2 blocks) | `ci.yml:99-117` |
| Frontend ESLint + `tsc --noEmit` | Yes | Yes | Yes | `ci.yml:200-205` |
| Frontend production build | Yes | Yes | Yes | `ci.yml:206-208`, `frontend-bundle-budget.yml:39-40` |
| Frontend unit tests (`vitest`) | Yes (`frontend-v3/package.json:13`) | **No** | No | no workflow reference |
| Frontend bundle budget | Yes | Yes | Yes | `frontend-bundle-budget.yml:42-43` → `check:bundle` |
| Frontend E2E (Playwright) | Yes | Yes (path-filtered) | Yes | `frontend-e2e.yml:34-38`; `playwright.config.ts:31-38` supplies webServer |
| Frontend governance `verify:*` (6 scripts) | Yes | **Only via `pnpm`-based `check` aggregate, which no workflow calls** | No | `frontend-v3/package.json:14-21` |
| Coverage (`--cov`, `test:coverage`) | Yes | **No** | No | `package.json:14`; `ci.yml:301` |
| Changed-files ruff/mypy non-regression | Yes | Yes | Yes | `quality-changed-files.yml:40-46` |
| YAML validity (workflows/compose) | Yes | Yes | Yes | `quality-gate.yml:23-55` |
| Dockerfile FROM check | Yes | Yes | Weak (A08-005) | `quality-gate.yml:56-81` |
| Architecture compliance | Yes | Yes (push main only) | Yes | `foundation-gate.yml:20-23` |
| Performance SLO gate (`config/quality-gates/performance-gate.py`) | Yes | **No** | No | grep: no workflow reference |
| FHIR / offline quality gates | Yes | **No** | No | `config/quality-gates/{fhir,offline}-gate.py` unreferenced |
| Unified quality gate (`scripts/quality_gate.py --ci`) | Yes | Makefile only, `|| true` | No (non-blocking) | `Makefile:312-318` |
| Backup verification / restore validation | Yes | Makefile only | Not in CI | `Makefile:394-396`; see Reliability report |
| SAST (CodeQL ×2, Bandit), secret scan, dependency review, Scorecard | Yes | Yes | Yes (with duplicates) | `codeql*.yml`, `ci.yml:323-328`, others |

---

## 4. Positive controls observed (do not regress)

- `docker-compose.yml` (MVP) is the strongest stack: required secrets with `:?` guards (`:24,63,114-120`), `no-new-privileges` (`:103-104,249-250,274-275`), CPU/memory limits (`:19-21,55-57,94-96,202-204`), readiness-based healthchecks and `depends_on: condition: service_healthy` (`:170-187,290-294`).
- All 32 workflows declare top-level `permissions`; none uses `write-all` (exception: `scorecard.yml:9` uses `read-all`, with job-level least privilege at `:16-19`).
- Most third-party actions are pinned to 40-char SHAs (e.g. `ci.yml:31-32`, `nightly.yml:303,367,390,406`).
- `/metrics/prom` fails closed in production (`backend/app/routes/metrics.py:139-145`).
- Structured JSON logging is implemented in `shared/logging/config.py:34-60` and wired from `backend/app/main.py:22-25`, `backend/app/factory.py:1108-1109`, `backend/app/worker.py:37-39`.
- `docker-compose.demo.yml` enforces strict environment isolation and required demo secrets (`:1-3,13-14,64-68,101-112`).

---

## 5. Wave C candidate eligibility (A08 scope)

**Eligible (clean in `git status --porcelain` for the checked ops paths):** `frontend-bundle-budget.yml`, `ci.yml`, `quality-gate.yml`, `preview-deploy.yml`, `Makefile`, `config/prometheus/*`, `frontend-v3/Dockerfile`, `backend/Dockerfile`, compose files (except user-modified workflows).

**INELIGIBLE — USER-MODIFIED, DO NOT TOUCH:**
- `.github/workflows/frontend-pwa.yml` — ` M` (verified).
- `.github/workflows/security-hardening.yml` — ` M` (verified).
- `.github/dependabot.yml` — protected per `PROGRAM_CONTROL §2.2` / `FILE_OWNERSHIP_MATRIX §4` (not verified by this agent, treated as protected).
- `services/lab/Dockerfile` — protected per program brief.
- `frontend-v3/package.json` / `vite.config.ts` — USER per `PROGRAM_CONTROL §2.2`.

Concrete safe remediation candidates are consolidated in `RELIABILITY_AUDIT.md §6`.

---

## 6. SCOPE_REQUESTs

1. **SCOPE_REQUEST-A08-01:** `frontend-v3/package.json:21` (`pnpm` → `npm`) is user-owned and outside A08's write set — route to orchestrator/user.
2. **SCOPE_REQUEST-A08-02:** Replacing `safety` with `pip-audit` in `ci.yml` requires A04 security approval (gate semantics).
3. **SCOPE_REQUEST-A08-03:** Aligning Python version in CI requires A07 backend-compatibility sign-off.
4. **SCOPE_REQUEST-A08-04:** Removing one CodeQL/Pages workflow requires orchestrator decision on canonical gate.
5. **SCOPE_REQUEST-A08-05:** Vault dev-mode remediation and MinIO public-metrics change require A04 + infrastructure owner approval; no new service/cost should be added without proven need.
