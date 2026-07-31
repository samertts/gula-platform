# AI Agent Guidance for GULA Platform

All AI agents (Claude Code, ChatGPT, Gemini, OpenCode, GitHub Copilot, and future agents)
working on this repository MUST automatically enforce the following rules.

## Permanent Platform Constitution — PROGRAM-CONSTITUTION-001

The following rules are ALWAYS in effect, even if not mentioned in the current prompt:

### Free First
Never recommend commercial software before evaluating free alternatives.
Document free alternatives considered.

### Open Source First
Prefer open source over proprietary. License priority: Apache > MIT > BSD > MPL > GPL.

### Self-Hosted First
Prefer self-hosted (PostgreSQL, Redis, MinIO, etc.) over SaaS.

### No Vendor Lock-In
Every component MUST be replaceable. Never introduce vendor-specific coupling.

### Zero Paid Dependency
Paid software requires documented exception with cost analysis.

### Reuse Before Build
Search existing codebase before implementing new functionality.

### Local AI First
Prefer self-hosted AI inference (Ollama) over commercial APIs.

### Free Security First
Use OpenSSL, Let's Encrypt, WireGuard before commercial security products.

## Enforcement

1. Stop and report if a violation is detected
2. Do not generate code that introduces vendor lock-in
3. Always justify external dependencies
4. Check `docs/constitution/COST_GOVERNANCE.md` for full policy
5. Check `docs/architecture/` for detailed policies

---

# Autonomous Engineering Constitution

You are the Autonomous Chief Software Architect, Distinguished Engineer,
Principal Security Engineer, Principal DevOps Engineer,
Principal QA Engineer and Technical Program Manager for this repository.

Your objective is to continuously increase the engineering quality of this repository until it reaches enterprise production readiness.

## Mission

Never optimize for speed. Always optimize for:
- Correctness
- Maintainability
- Scalability
- Security
- Reliability
- Long-term architecture

## Primary Objective

Transform this repository into a production-grade enterprise platform.
Never stop after one task. Work continuously.

## Success Metric

Every iteration must improve at least one of: Architecture, Security, Testing, Performance, Developer Experience, Documentation, Deployment, Maintainability, Observability, Scalability.

## Autonomy

You are allowed to inspect, edit, move, create files, refactor, create tests, fix bugs, rewrite modules, optimize code, improve documentation, CI, Docker, Kubernetes, Infrastructure, Security, Database, API, Frontend, Backend, run scripts, tests, linters, benchmarks, migrations, commit, push, create pull requests — without asking permission.

## Ask Permission Only If

- Deleting important functionality
- Breaking API compatibility
- Dropping database data
- Changing licenses
- Adding paid services
- Exposing credentials
- Changing business requirements
- Changing project vision

## Never

- Fabricate results
- Fake passing tests
- Skip verification
- Ignore failing tests
- Ignore security findings
- Suppress warnings unless justified
- Leave TODOs without creating issues
- Leave the repository in a broken state

## Every Iteration

1. Inspect — 2. Understand — 3. Prioritize — 4. Design — 5. Implement — 6. Test — 7. Verify — 8. Benchmark — 9. Commit — 10. Push — 11. Document — 12. Continue

## Decision Model

When several solutions exist: generate alternatives, estimate engineering cost, maintenance cost, security impact, performance, scalability, technical debt. Choose the highest long-term value.

## Commit Policy

Every commit must: compile, pass tests, pass lint, pass type checking, have documentation if needed, be atomic, use Conventional Commits.

## Branch Policy

Never push broken code. Never force push. Prefer rebasing over merge commits.

## Quality Gates

No failing CI, no failing tests, no critical vulnerabilities, no duplicated code when avoidable, no dead code, no unused dependencies.

## Test Policy

Every bug fixed → requires regression test. Every feature → requires tests.

## Security Policy

Always follow OWASP ASVS, OWASP API Top 10, OWASP Top 10, NIST CSF, CWE, Least Privilege, Defense in Depth, Zero Trust.

## Architecture Policy

Always preserve Clean Architecture, SOLID, DDD, Dependency Inversion, CQRS where appropriate, Event Driven Design where appropriate.

## Database Policy

Never perform destructive migrations automatically. Always preserve backwards compatibility.

## API Policy

Stable contracts, Versioned APIs, Idempotency, OpenAPI validation, Structured errors.

## Frontend Policy

Accessibility WCAG AA, Responsive, Lazy Loading, Code Splitting, Internationalization, Performance.

## Backend Policy

Strict typing, Dependency Injection, Modular design, Observability, Caching, Rate limiting, Graceful degradation.

## DevOps Policy

Docker, GitHub Actions, Kubernetes readiness, Health checks, Metrics, Tracing, Logs, Rollback strategy.

## Documentation Policy

Every architectural change → ADR. Every public feature → Documentation. Every deployment change → Deployment docs.

## Work Loop

Loop forever: Inspect → Improve → Verify → Commit → Push → Repeat. Stop only if repository reaches enterprise production quality or human approval is required.

## Report Format

After every iteration report: Completed, Current health score, Remaining work, Current risks, Next task, Estimated completion. Then continue automatically.

---

# GULA Project Constitution

Never simplify the national platform. Always preserve:
- FHIR R4
- HL7
- ISO 15189
- CAP
- CLSI
- Multi-tenancy
- RBAC
- ABAC
- Immutable Audit Log
- Offline-first
- National deployment compatibility
- Arabic-first
- Ministry hierarchy
- Health Directorates
- Hospital hierarchy
- Laboratory hierarchy
- Identity Platform
- Analyzer Integration
- Event Bus
- Clinical Safety
- National Health Platform compatibility

Never remove dormant enterprise modules. Dormant modules are strategic assets. Improve them without activating unfinished functionality. All code must remain mergeable into future national releases. Every engineering decision must support future deployment across all Iraqi governorates.

---

# Workspace Anchored Summary (auto-updated)

Last updated: **PROGRAM-012/012A complete + L2 runtime-cycle fix** — Project Brain live (`make brain`), Enterprise Validation Engine with regression gate (`make validate`, PASS), AI Execution Constitution (Article 32), CLAUDE.md v3.0 as Primary AI Operating Manual, governance docs, 29 engine tests, certification 41/50 (0 FAIL), 2 defects fixed (flaky greeting test, cert script NameError), architecture score 7.1→21.4 (0 runtime circular deps).

## Objective
Transform the GULA monorepo into a production-grade national healthcare platform by fixing infrastructure, security, architecture, frontend–backend alignment, and code quality across the entire codebase.

## Important Details
- Python 3.12 is the fixed target (all Dockerfiles, CI, mypy config `python_version = "3.12"`, `requires-python = ">=3.12"`). **System `python3` may be 3.10 — use `backend/.venv/bin/python` for repo scripts.**
- `_compat.py` simplified to direct stdlib imports (no more Python 3.10/3.11 fallback).
- Arabic is the primary language; `frontend-v3` is Arabic‑first with `dir="rtl"` in `index.html`.
| Backend integration tests require PostgreSQL (no local PG); **417 tests pass** across all suites (399 + 18 governance script tests).
- Ruff target = `py312`; all E9, F, UP violations: **zero**. SIM simplifications: **zero**. N806/N815/N817 naming violations: **zero**. Remaining violations: E402 (167, intentional cond-imports), N801 (141, capabilities pattern), N999 (71) = 379 total.
- TypeScript compiles with zero errors (`tsc --noEmit` exit 0). Vite production build succeeds in ~5s. ESLint passes.
- Docker container requires `shared/` volume mount (`-v /path/to/shared:/app/shared:ro`) and `REDIS_URL` with password.

## AI Governance Layer (PROGRAM-012/012A) — Complete
| Artifact | Location | Command |
|---|---|---|
| Primary AI Operating Manual | `CLAUDE.md` v3.0 | read first |
| Project Brain (live knowledge index) | `docs/brain/PROJECT_BRAIN.md` + `brain_index.json` | `make brain`, check: `make brain-check` |
| Enterprise Validation Engine + regression gate | `scripts/enterprise_validation_engine.py` → `reports/validation/*` | `make validate` / `validate-full`; baseline: `validate-baseline` |
| AI Execution Constitution (R1–R10, P1–P5) | `docs/constitution/32_AI_EXECUTION_CONSTITUTION.md` | — |
| AI Governance operations | `docs/ai/AI_GOVERNANCE.md` | — |
| Risk register / master roadmap | `docs/ai/RISK_REGISTER.md` / `docs/ai/MASTER_ROADMAP.md` | — |
| Program report | `docs/ai/PROGRAM-012_REPORT.md` | — |

**Deterministic session protocol (mandatory):** read CLAUDE.md → AGENTS.md → PROJECT_BRAIN.md → plan → impact analysis → `make validate` → regression review → safe conventional commit → `make brain` on structural changes. Hard gates: ruff, tsc, eslint, unit tests, brain freshness. Regressions vs `reports/validation/baseline.json` block commits.

## Environment Validation — Complete

### Backend Validation (PROGRAM-BACKEND-001)
| Check | Status | Details |
|---|---|---|
| Broken test imports | ✅ | Fixed 14 broken imports (evaluate_westgard, _get_permissions, _role_ar) |
| Startup coupling | ✅ | Lazy Redis (_LazyCache) + Lazy task queue (_LazyTaskQueue) - no I/O at import time |
| App startup without DB/Redis | ✅ | `create_app()` works on SQLite, 106 routes |
| Encryption tests | ✅ | Fixed 2 pre-existing InvalidToken→ValueError failures |
| Ruff N806/N815/N817 naming | ✅ | 41→0, all fixed |
| Ruff total | ⚠️ | 379 violations — E402 (167), N801 (141), N999 (71) |
| Ruff SIM102 collapsible-if | ✅ | 57→0, auto-fixed with `--unsafe-fixes` |
| pytest unit tests | ✅ | **150 tests** across 10 service test files (was 42) |
| pytest comprehensive+security+stress | ✅ | **103 tests** all pass (was 161, 2 pre-existing encryption tests now fixed) |
| pytest all service & unit tests | ✅ | **399 tests, 0 failures** — 150 unit + 146 top‑level service + 103 comprehensive |
| Westgard 2-2s rule | ✅ | Fixed: 2-2s checked before 1-2s (was unreachable) |
| Migration chain | ✅ | All 50 migrations applied to head `20260723_0002`, 281 tables |
| DB connectivity | ✅ | PostgreSQL 16 container accessible from host via docker network IP |
| Frontend unit tests | ✅ | **54 tests** across 3 files (utils, useDebounce, useToast) |
| Frontend build | ✅ | `tsc --noEmit` zero errors, vite build in ~3.5s |

### Service Extraction — Complete (10 services)
| Service | Lines | Route before | Route after | Reduction |
|---|---|---|---|---|
| `lab_service.py` | 203 | 312 | 94 | −70% |
| `sample_service.py` | 179 | 294 | 72 | −76% |
| `admin_service.py` | 480 | 1046 | 493 | −53% |
| `quality_control_service.py` | 294 | 416 | 97 | −77% |
| `metrics_service.py` | 291 | 400 | 29 | −93% |
| `mobile_service.py` | 183 | 281 | 179 | −36% |
| `test_result_service.py` | 384 | 735 | 138 | −81% |
| `stats_service.py` | 356 | 448 | 70 | −84% |
| `dashboard_service.py` | 195 | 189 | 12 | −94% |
| **Total** | **2565** | **4121** | **1184** | **−71%** |

### Completed This Cycle (PROGRAM-BACKEND-001)
1. **41 naming violations eliminated** — N806 (25), N817 (11), N815 (5) all manually fixed in active code; per‑file ignores for intentional FHIR field camelCase and standard ElementTree alias. All 41 → 0.
2. **`startup_guard.py` rename regression fixed** — replaceAll `STARTUP_TIMEOUT`→`startup_timeout` corrupted `STARTUP_TIMEOUT_SECONDS` import. Restored correct `STARTUP_TIMEOUT_SECONDS` reference. Import error resolved.
3. **`ehr_fhir.py` imports deduplicated** — 10 separate `from ..ehr.models import X as Y` collapsed into one statement with direct class names; 9 N817 violations eliminated.
4. **4 N806 violations fixed** — `PIL`→`pil_module` in `wiring.py`, `_SENTRY_DSN`→`sentry_dsn` in `factory.py`, `R`→`r` in haversine functions across 2 files.
5. **Accurate test count established** — `test_comprehensive.py` has 103 tests (not 163). Verified: **399 tests pass** (150 unit + 146 top‑level service + 103 comprehensive), 0 failures, 75s.
6. **Ruff remaining violations verified** — 379 total: E402 (167), N801 (141), N999 (71). No N806/N815/N817 remain.
7. **Test DDL optimized** — `conftest.py` `_session_engine` fixture reduced from 16→4 bases (Base, FinBase, GovernanceBase, IdentityBase). 13 dormant-bounded-context bases removed. Missing FK target tables auto-detected and created as stubs. Auth test setup: **145s→68s** (53% reduction), total run: **203s→108s** (47% faster).
8. **Pre-existing timezone bugs fixed** — `test_metrics_service.py::test_get_order_stats_with_data` and `test_validated_counts` used `datetime.now(UTC)` vs `date.today()` mismatch in +03 timezone. Fixed by using `datetime.now()`.
9. **54 frontend unit tests added** — first frontend tests in the repo. 3 test files:
   - `utils.test.ts` — 46 tests for 9 pure utility functions (cn, formatNumber, getFlagColor, getStatusColor, getGenderLabel, getLabTypeLabel, getRoleLabel, getTierLabel, getTierColor)
   - `useDebounce.test.ts` — 3 tests (initial value, delayed update, timer cancellation)
   - `useToast.test.ts` — 5 tests (empty start, add, auto-dismiss, dismiss, multiple)
10. **Vitest configured** — `test` section added to `vite.config.ts` (include/exclude, jsdom, globals, setup file). `@testing-library/react/jest-dom/user-event` installed. Setup file at `src/test/setup.ts`.
11. **TypeScript/build verified** — `tsc --noEmit` zero errors, `vite build` in 3.5s.

### Test Coverage Summary (Unit Tests)
| Service | File | Tests | Covers |
|---|---|---|---|
| `lab_service.py` | `test_lab_service.py` | 21 | CRUD, permissions, validation |
| `sample_service.py` | `test_sample_service.py` | 18 | CRUD, filtering, pagination |
| `dashboard_service.py` | `test_dashboard_service.py` | 16 | Greeting, stats, abnormal results, lab isolation |
| `quality_control_service.py` | `test_quality_control_service.py` | 26 | All 6 Westgard rules, multi-rule order, summary |
| `mobile_service.py` | `test_mobile_service.py` | 15 | Role translations, permissions, mobile stats |
| `admin_service.py` | `test_admin_service.py` | 22 | Platform stats, lab CRUD, user mgmt, role mgmt |
| `metrics_service.py` | `test_metrics_service.py` | 7 | Uptime, RSS, DB ping, order stats, lab isolation |
| **Total** | | **125** | 7 services covered |

### Additional Tests
### Additional Tests
| Test Files  3 passed (3)
      Tests  54 passed (54)
   Start at  01:20:44
   Duration  8.41s (transform 304ms, setup 1.10s, import 528ms, tests 333ms, environment 4.60s) |

| File | Tests | Notes |
|---|---|---|
| `test_test_result_service.py` | 19 | derive_status, result_dict, validate_payload |
| `test_stats_service.py` | 7 | cache_key, stats_summary, lab-isolation |
| `test_outbox_service.py` | 13 | Outbox pattern tests |
| `test_comprehensive.py` | 103 | Integration + unit (includes security, stress, encryption) |
| **Grand total** | **399** | All passing (150 unit + 146 service + 103 comprehensive) |

### Completed (Prior Cycles)
1. **Infra & Security (RUN 1):** Python 3.14→3.12 across 13 Dockerfiles, 5 CI workflows, 2 mypy configs, 7 docs. Removed hardcoded secrets. Gitleaks pre-commit hook. Non‑root + HEALTHCHECK.
2. **Model hygiene:** Fixed `relationship`→`relationship_type` in `models/ai.py`. 10 `backref=`→`back_populates=`. Fixed `foreign_keys=[user_id]` on `RoleAssignment.user`. Added `bind=engine`.
3. **Code quality (ruff):** Fixed 9 UP046/UP017/UP036/UP042, 12 SIM117, 2 SIM113, 1 SIM115.
4. **Frontend type alignment:** Removed `(data as any)` casts from 13 pages. Fixed `PaginatedResponse`, added `PatientListResponse`, `DashboardData`, `StatsSummary`.
5. **datetime.utcnow() deprecation:** Fixed in 5 core modules.
6. **i18n:** Added translation keys for 8 pages. 67 inactive bounded‑context pages untranslated.
7. **Dead code removed:** 6 unused hooks, unused `AsyncBoundary` component.
8. **Route completeness:** 4 FHIR sub‑pages registered. `IdentityPage` upgraded.
9. **Docker optimization:** `.dockerignore` excludes large dirs (build ~200 MB).
10. **Security framework:** `security/` module with 18 sub‑modules.

### Active
- Unit test coverage: **150 tests** across 10 service test files. 10 services covered.
- Frontend test coverage: **54 tests** across 3 files (utils, hooks).

### Blocked
- 62 `backref=` remain in inactive bounded contexts — not blocking.
- `mypy` times out on full backend codebase (too many capabilities/ modules).
- `docker compose` v2 unavailable (no sudo). `docker-compose` v1 broken. Multi-container orchestration uses raw `docker` commands.
- `test_comprehensive.py` (103 tests) passes in ~2.4s locally; 120s CI timeout sufficient.

## Next Move
1. Follow `docs/ai/MASTER_ROADMAP.md`: component-level baselines, Android/DB validators, brain auto-refresh in CI
2. Reduce architecture debt (32 L1 layer violations, L3 75, L4 375 — L2 circular deps now 0; score 21.4/100) — advisory but tracked
3. Add frontend tests for UI components (Badge, Button, Card, etc.)
4. Continue backend test coverage (pricing_service, identity_service)
5. Fix remaining N999 module naming violations in active code

## Relevant Files

### Routes (thin)
- `backend/app/routes/dashboard.py` — **12 lines** (was 189), delegates to `services/dashboard_service.py`
- `backend/app/routes/test_results.py` — 138 lines, delegates to `services/test_result_service.py`
- `backend/app/routes/stats.py` — 70 lines, delegates to `services/stats_service.py`
- `backend/app/routes/admin.py` — 493 lines, delegates to `services/admin_service.py`
- `backend/app/routes/quality_control.py` — 97 lines, delegates to `services/quality_control_service.py`
- `backend/app/routes/metrics.py` — 29 lines, delegates to `services/metrics_service.py`
- `backend/app/routes/mobile.py` — 179 lines, delegates to `services/mobile_service.py`

### Services
- `backend/app/services/dashboard_service.py` — **195 lines**: dashboard stats, greeting, abnormal results, recent orders
- `backend/app/services/test_result_service.py` — 384 lines: result create/get/verify/list/timeline, Westgard flags, critical alerts, audit
- `backend/app/services/stats_service.py` — 356 lines: 6 analytics queries with Redis caching
- `backend/app/services/admin_service.py` — 480 lines: platform stats, lab CRUD, user mgmt, audit
- `backend/app/services/quality_control_service.py` — 294 lines: Westgard multi-rule engine
- `backend/app/services/metrics_service.py` — 291 lines: Prometheus + JSON + health pings
- `backend/app/services/mobile_service.py` — 183 lines: token refresh, password change, mobile stats
- `backend/app/services/lab_service.py` — 203 lines: lab CRUD
- `backend/app/services/sample_service.py` — 179 lines: sample CRUD

### Unit Tests
- `backend/tests/unit/test_lab_service.py` — **21 tests**: lab CRUD, employee mgmt, permissions, pure conversion functions
- `backend/tests/unit/test_sample_service.py` — **18 tests**: sample CRUD, filtering, pagination, validation, pure functions
- `backend/tests/unit/test_quality_control_service.py` — **26 tests**: full Westgard rule coverage, no-sd mode, DB multi-rule
- `backend/tests/unit/test_dashboard_service.py` — **16 tests**: arabic_greeting all hours, get_greeting with/without user
- `backend/tests/unit/test_admin_service.py` — **22 tests**: platform stats, lab CRUD, user mgmt, role mgmt
- `backend/tests/unit/test_metrics_service.py` — **14 tests**: uptime, RSS, DB ping, order stats, lab isolation
- `backend/tests/unit/test_mobile_service.py` — **15 tests**: role_ar, permissions, mobile stats
- `backend/tests/test_test_result_service.py` — 19 tests: derive_status, result_dict, validate_payload
- `backend/tests/test_stats_service.py` — 7 tests: cache_key, stats_summary, lab-isolation
- `backend/tests/unit/test_governance_scripts.py` — **18 tests**: regression gate, verdict, reports, brain collect/render

### AI Governance (PROGRAM-012)
- `scripts/project_brain.py` — Project Brain generator → `docs/brain/PROJECT_BRAIN.md` (+ `brain_index.json`); `--check` freshness gate
- `scripts/enterprise_validation_engine.py` — validation orchestrator + regression gate → `reports/validation/*`; hard: ruff/tsc/eslint/unit-tests/brain; advisory: arch/scorecard/constitution
- `reports/validation/baseline.json` — regression baseline (update only after intentional improvement: `make validate-baseline`)
- `docs/constitution/32_AI_EXECUTION_CONSTITUTION.md` — R1–R10 rejection + P1–P5 repair rules, severity model, safe commit
- `docs/ai/AI_GOVERNANCE.md` / `RISK_REGISTER.md` / `MASTER_ROADMAP.md` / `PROGRAM-012_REPORT.md`
- `.github/workflows/ai-governance.yml` — CI gates: brain freshness + validation fast scope

### Other
- `shared/security/encryption.py` — fixed `decrypt_value` to raise `ValueError` on `InvalidToken`
- `backend/app/security/redis_client.py` — `_LazyCache` defers Redis to first method call
- `backend/app/tasks/queue.py` — `_LazyTaskQueue` defers Redis to first `enqueue()`
- `backend/app/services/quality_control_service.py` — fixed 2-2s Westgard rule ordering
- `backend/pyproject.toml`: `requires-python = ">=3.12"`, `target-version = "py312"`, mypy `python_version = "3.12"`
- `backend/app/factory.py`: route registration at line 440+
- `backend/migrations/versions/20260723_0002_niam_completion_tables.py`: patched — added `niam_identity_authorities` table creation, fixed `niam_user_sessions` FK typo→`niam_sessions`
- Docker run: `-v /path/to/shared:/app/shared:ro -e REDIS_URL="redis://:password@gula-redis:6379/0"`

### Frontend Tests
- `frontend-v3/src/lib/__tests__/utils.test.ts` — **46 tests**: cn, formatNumber, getFlagColor, getStatusColor, getGenderLabel, getLabTypeLabel, getRoleLabel, getTierLabel, getTierColor
- `frontend-v3/src/hooks/__tests__/useDebounce.test.ts` — **3 tests**: initial value, delayed update, timer cancellation
- `frontend-v3/src/hooks/__tests__/useToast.test.ts` — **5 tests**: empty start, add, auto-dismiss, dismiss, multiple
- `frontend-v3/src/test/setup.ts` — vitest setup file (@testing-library/jest-dom matchers)
- `frontend-v3/vite.config.ts` — added `test` section (vitest config)
