# AI Agent Guidance for GULA Platform

> **AUTHORITY:** The supreme AI constitution is `AI_OPERATING_CONSTITUTION.md`.
> All rules below are summaries. The constitution is the single source of truth.
> If any conflict exists, the constitution wins. See Section 1.4 for precedence.

All AI agents (Claude Code, ChatGPT, Gemini, OpenCode, GitHub Copilot, and future agents)
working on this repository MUST automatically enforce the following rules.

## Structural Migration Constitution — PROGRAM-MIGRATION-001 (ADR-028)

> **Full text:** `docs/constitution/33_STRUCTURAL_MIGRATION_CONSTITUTION.md` +
> `docs/adr/ADR-028-structural-migration.md`. Applies to every structural
> migration commit (Commit 1.x series).

1. **Behavior preservation is mandatory** — runtime, API, business rules,
   security, authorization, audit, and database behavior never change.
2. **Every deletion must be evidence-based** — unused / superseded /
   duplicated / intentionally deprecated, justified in the report.
3. **Backend remains the authoritative source of truth** — verify OpenAPI
   compatibility, frontend consumers, client types, permissions, request/
   response models, route compatibility after every migration.
4. **Migration Impact Report is mandatory per commit** — files removed/moved/
   replaced, duplicate code eliminated, LOC reduction, dependency changes,
   API impact, frontend impact, rollback procedure.
5. **Prefer moving before deleting** — archive first, delete after verification.
6. **Every migration must remain independently reversible** — a single
   `git revert` restores the previous state.
7. **One commit at a time** — after each commit run the complete verification
   cycle, produce the report, STOP, and await explicit approval.

## Permanent Platform Constitution — PROGRAM-CONSTITUTION-001

> **Full text:** `AI_OPERATING_CONSTITUTION.md` Section 2.
> The rules below are summaries. The constitution is authoritative.

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

Last updated: **PROGRAM-01 FINAL CLOSURE — COMPLETE + ARCHITECTURE LOCKED** — Wave 5 orders 20–21: #2 ecosystem `EncryptionEngine` (AES-256 branch) + #1 doc-intel `EncryptionService` delegated to canonical `shared/security/encryption.py` (added `encrypt_bytes`/`decrypt_bytes`; ecosystem SHA-256 derivation preserved → ciphertexts round-trip identically; last `Fernet(` constructions removed from `backend/app`), 9 new regression tests (`test_encryption_canonical.py`) → **full backend 5089 passed / 0 failed (598s)**, ruff clean, boot 118 routes, OpenAPI 2006 methods / 1677 paths unchanged; orders 22–24 froze all remaining findings (baseline 27→**25 frozen**: 19 Domain-Owned + 1 Strategic Exception #18 + 3 kernel-domain #11/#32/#33 + 2 False Positive #26/#48; ADR-030/034); **architecture gate PASS — 25/25 ack, 0 new**, domain 11/11, country PASS, policy PASS, `test_architecture_constitution.py` 22 passed; `TECHNICAL_DEBT_REGISTER.md` frozen (25 frozen + 2 resolved, TD-01..12); classification/dashboard/SHARED_CORE_REPORT/ARCHITECTURE_CONSTITUTION/CERTIFICATION + 7 master docs all marked **PROGRAM-01 ARCHITECTURE LOCKED**; **`PROGRAM_01_FINAL_CERTIFICATION.md` written; single closing commit created; PROGRAM-01 CERTIFIED COMPLETE — STOP, do not start PROGRAM-02; await Program Director.** Prior: **PROGRAM-01 WAVE 4 — COMMIT 3.6 DONE** — order 19 (#44 broken national workflow_runtime → canonical `backend/app/workflows`, ADR-036, baseline 31→**27**): whole `national/workflow_runtime/` package (13 files, `application/service.py` was **0 bytes** → every `/national/workflows/*` handler returned HTTP 500) + dead `platform/workflow.py` (zero importers) archived via `git mv` into `archive/platform-shared-core/` with provenance headers (ADR-028 archive-first, single-`git revert` reversible), factory `include_router` removed (**boot 119→118**), frontend national page/route/nav + generated-client section (API object + 10 hooks) removed, generator + zero-drift registries updated, **OpenAPI 2028→2006 methods / 1696→1677 paths (−22/−19; removed paths = exactly the broken surface, nothing added)**; 14 new regression tests (`test_workflow_runtime_retired.py`) → **full backend 5080 passed / 0 failed (658s)**, ruff 378 (< 379 baseline), tsc 0, eslint 0, vitest 122 passed, architecture gate 27 ack + **0 new** (domain 11/11, country PASS, policy PASS); baseline regenerated 31→27 (−1 this commit; −3 from already-committed orders 16–18 #5 doc-intel audit ADR-031 `5b52e7a1`, #9 task_engine audit ADR-031 `f0715216`, #50 notification adapters ADR-032 `70d77d5b` — their baseline regeneration was deferred to this commit and is accounted in report §4); ADR-036 accepted + `docs/adr/README.md` updated, classification + dashboard + SHARED_CORE_REPORT + `COMMIT_3_6_VERIFICATION_REPORT.md` written, ARCHITECTURE_CONSTITUTION/CERTIFICATION + 7 master docs regenerated, PROJECT_BRAIN refreshed. Prior: **PROGRAM-01 WAVE 3 — COMMIT 3.3 DONE + WAVE 3 CERTIFIED** — order 15 (#46+#47 national document PDF → canonical `shared/pdf`, ADR-033, baseline 33→**31**): new canonical adapter `capabilities/document_management/pdf_generator.py` (`SharedPdfGenerator(PDFGenerator)`, thin wrapper over `shared/pdf/generator.py` via `asyncio.to_thread`, subtitle-less template — avoids a pre-existing reportlab 5.0.0 `styles["Subtitle"]` KeyError in the canonical generator), national route handler renamed `generate_pdf`→`export_document_pdf` (operationId + summary pinned → OpenAPI byte-identical), service delegator renamed `generate_pdf`→`export_pdf`, `_get_service` now injects the adapter so `POST /national/documents/{id}/generate-pdf` returns a real PDF (was 422); 13 new regression tests (`test_document_platform_pdf.py`) → **full backend 5030 passed / 0 failed**, ruff 378 (< 379 baseline), architecture gate 31 ack + **0 new**, domain 11/11, boot 119 routes, baseline regenerated (31), classification + dashboard + SHARED_CORE_REPORT + `COMMIT_3_3_VERIFICATION_REPORT.md` + **`WAVE_3_CERTIFICATION.md`** written, ARCHITECTURE_CONSTITUTION/CERTIFICATION + master docs regenerated. **STOP for explicit approval before Wave 4** (orders 16–19: #5/#9 ADR-031, #50 ADR-032, #44 ADR-036). Prior: **PROGRAM-01 WAVE 3 — COMMIT 3.2 DONE + COMMITTED (`57d829eb`)** — order 14 (#35+#36 doc-intel search → canonical `backend/app/capabilities/search_service`, ADR-033, baseline 35→**33**): `DefaultSearchService` + `DefaultSearchIndexer` + `InfrastructureSemanticSearchService` promoted verbatim (indexer/search/semantic modules + standalone exceptions + structural-mirror dataclasses + composition root), stub `/search-service` router (5 ops) re-wired to the live in-memory indexer (real index/list/update/delete), sole consumer `document_intelligence/application/wiring.py` re-pointed atomically, old namespace fully vacated (no facade); **OpenAPI before/after byte-identical (2028 methods / 1696 paths)**, boot 119 routes, 40 new regression tests (`test_search_promoted.py`) → **full backend 5017 passed / 0 failed**, ruff clean (378 < 379 baseline), architecture gate 33 ack + **0 new**, domain 11/11, baseline regenerated (33), classification + dashboard + SHARED_CORE_REPORT + `COMMIT_3_2_VERIFICATION_REPORT.md` written, ARCHITECTURE_CONSTITUTION/CERTIFICATION regenerated. **STOP for explicit approval before Commit 3.3** (order 15 PDF #46/#47 national document PDF, ADR-033, →31), then Wave 3 certification, STOP before Wave 4 (orders 16–19: #5/#9 ADR-031, #50 ADR-032, #44 ADR-036). Prior: **PROGRAM-01 WAVE 3 — COMMIT 3.1 DONE + COMMITTED (`09773f84`)** — order 13 (#24+#49 identity notification queue → canonical `backend/app/notifications`, ADR-032, baseline 37→**35**): `git mv` of identity/notifications/{models,services,routes}.py promoted into the canonical package (delivery + queue now co-located), queue class renamed `NotificationService`→`NotificationQueueService` (avoids collision with canonical sync `NotificationService`), consumers re-pointed atomically (NIAM router `include_router(notifications_routes)` + test_niam_v2.py), old namespace fully vacated; **OpenAPI before/after diff byte-identical (2028 methods / 1696 paths)**, boot 119 routes, 23 new regression tests (`test_notifications_queue_promoted.py`) → **full backend 4977 passed / 0 failed**, ruff clean, architecture gate 35 ack + **0 new**, domain 11/11, baseline regenerated (35), inventory regenerated, ADR-032/033 accepted + `docs/adr/README.md` updated, classification + dashboard + SHARED_CORE_REPORT + verification report written, PROJECT_BRAIN refreshed. **STOP for explicit approval before Commit 3.2** (order 14 search, ADR-033, →33), then 3.3 (order 15 PDF, →31), Wave 3 certification, STOP before Wave 4 (orders 16–19: #5/#9 ADR-031, #50 ADR-032, #44 ADR-036). Operational note: **PG container reachable only at `172.18.0.3:5432`** (localhost refused) — set `DATABASE_URL="postgresql://postgres:gula_dev_2026@172.18.0.3:5432/gula"` for the full suite. Prior: **PROGRAM-BETA COMPLETE** — Production Readiness certified across 8 phases: (1) **Security CERTIFIED** — real SQLi found & fixed (`ai/knowledge_graph.py::create_node` JSON interpolated into `text()` → bind params + `CAST(... AS jsonb)`, regression test added), HIGH react-router RSC-CSRF advisory fixed by migrating `react-router-dom@7.18.2`→`react-router@8.3.0` across 10 files (**npm audit 0 vulns**), `reencrypt_encryption_key.py` hardened with `_validate_identifier` regex guard (4 tests), nginx `frontend.conf` security headers added (CSP/HSTS/frame-ancestors none); Semgrep (p/default + owasp-top-ten) + bandit clean on scope, bcrypt/HS256/env-secret guards/CORS allowlist/rate-limiting/audit hash-chain all verified; (2) **Performance** — 0 bottlenecks, 18/18 budget tests (query counts, indexes, payload ≤30 fields, limit clamp 500), p95 ≤35 ms, ~24 s boot (once-per-worker, tracked); (3) **Reliability** — retry/backoff, circuit breaker, bulkhead, timeout, safe-call, outbox auto-repair + Redis in-memory fallback (28 tests); (4) **Observability** — Prometheus `/metrics/prom`, OTLP/HTTP tracing (vendor-neutral, env-gated), JSON logs, health/ready/deep (30 tests); (5) **Deployment** — multi-stage non-root image + compileall gate + HEALTHCHECK, hardened compose (limits/no-new-privileges/127.0.0.1), **43 valid K8s manifests** + HPA/PDB/PVC/region overlays; (6) **Disaster Recovery** — **live DR drill on PG16**: backup → drop table → restore (same + fresh DB), 0 errors, RPO≈1 min WAL→S3; (7) **Quality Gates** — `validate --fast` PASS (ruff 379 baseline, tsc 0, eslint 0, brain fresh, 56-migration chain), architecture gate PASS (57 ack, 0 new), domain isolation 11/11; (8) **Autonomous Repair** — self-heal dry-run e2e + cooldown + repair engine (20 tests). **9 root reports** (PRODUCTION_READINESS, SECURITY_CERTIFICATION, PERFORMANCE_REPORT, RELIABILITY_REPORT, OBSERVABILITY_REPORT, PRODUCTION_DEPLOYMENT, DISASTER_RECOVERY_REPORT, MASTER_RISK_REGISTER, MASTER_REMAINING_WORK); PROJECT_BRAIN refreshed. Next: migrate the 57 Shared Core findings to canonical providers. Prior: **PROGRAM-ALPHA COMPLETE** — the sovereign national platform architecture consolidated and constitution-gated: Shared Core elevated to ONE authoritative **50-service registry** (`SHARED_CORE_CATALOG` in `backend/app/domain_platform/shared_core.py` grew 23→50, every provider path verified on disk, catalog ⇄ `SHARED_CORE_SERVICES` tuple kept in lockstep by test `test_catalog_matches_service_list`); **Architecture Constitution engine built** (`scripts/architecture/` = core.py rules + gate.py baseline-gated enforcement + report.py + docs.py + cli.py + `scripts/architecture.py` launcher): `architecture-scan/gate/country/report/constitution/docs/baseline/check` wired into the Kernel, **17 new unit tests** (`backend/tests/unit/test_architecture_constitution.py`); deterministic baseline gate — 57 acknowledged Shared Core reimplementation findings + 2 country-hardening findings tracked at `.ai/core/architecture/constitution_baseline.json`, **any NEW finding fails the gate** (future PRs automatically fail on duplicated identity/notification/audit/barcode/QR/workflow/rules/encryption/cache/events/DI/scheduler/search/document engines); gate = Shared Core scan + Domain certification 11/11 (isolation PASS) + country-agnostic scan; **architecture-check added to CI (`ai-governance.yml`) as a HARD gate**; 7 master documents generated by `scripts/architecture/docs.py`: MASTER_ARCHITECTURE_v2.md, SHARED_CORE_REGISTRY.md, DOMAIN_SOVEREIGNTY.md, DOMAIN_DEPENDENCY_GRAPH.md, WORKSPACE_ARCHITECTURE.md, DIGITAL_TRUST_PLATFORM.md, MASTER_REMAINING_WORK.md (+ ARCHITECTURE_CONSTITUTION.md + ARCHITECTURE_CERTIFICATION.md); **143 identity+domain+architecture tests pass; ruff clean on all new scope**; PROJECT_BRAIN refreshed. Prior: **PROGRAM-STABLE-004 COMPLETE** — the permanent Domain Platform Framework built (Domain Sovereignty for every current/future GULA module): `backend/app/domain_platform` package (core Blueprint vocabulary with 8 sections, 23-service Shared Core catalog, 11 canonical Domains in manifest.py with workspace bindings incl. emergency→hospital/citizen_portal→citizen/provider_portal→professional, IsolationValidator with real-source scanning for cross-domain imports/circular deps/shared mutable state/permission leakage/direct DB coupling/table overlaps, ContractRegistry + CrossDomainGateway, DomainLifecycle state machine, SemVer versioning with backward-compat gate, WorkspaceBindingRegistry, 9-check DomainCertificationEngine); Alembic `20260806_0001_domain_platform.py` (6 niam_domain_* tables, down 20260805_0002); 16 REST routes under `/niam/domains` (list/canonical/register/get/activate/suspend/upgrade/rollback/versions/binding/contracts/health/metrics/certify/history) wired into `factory.py`; `scripts/domains` governance engine (core.py + pipeline.py + report.py + cli.py + `scripts/domains.py` launcher) exposing `domain-audit/isolate/certify/docs/report/check` through the Kernel; **platform verdict CERTIFIED 11/11 Domains at 100% with isolation PASS (0 findings in all 6 categories)**; fixed real bugs found by the framework (WORKSPACE_DOMAIN_MAP lost the hospital workspace to emergency → primary-owner + unioned `workspace_ui_for`; `DomainService.transition` referenced undefined `from_state`); 71 new unit tests (`backend/tests/unit/test_domain_platform.py`) → **197 identity+domain unit tests pass**; ruff clean on domain_platform + scripts/domains scope; 7 DOMAIN_*.md docs at repo root; Orchestrator now detects the Domain Platform as present (**13 systems**, ENGINES += architect, domain). Prior: **PROGRAM-STABLE-003 IN PROGRESS** — the single permanent National Identity Platform (NIAM) established: IdentityType extended to 11 canonical types with legacy-alias `canonical()` mapping; Workspace Platform built (8 tables niam_workspaces/roles/members/permission_templates/departments/teams/invitations/delegations, 23 endpoints under `/niam/workspaces`, ONE active workspace per identity, permissions never cross workspaces); Cross-Org Guard built (OrganizationAccessGuard — zero cross-domain administration); Professional Registry built (12 professions, verify() is the ONLY privilege-activation path, is_privileged() single enforcement point); Citizen Registry built (country-agnostic configurable identity providers, 8 identifier types, hashed storage); Session Security extended (workspace binding + enforce_max_concurrent_sessions); 29 new audit actions; Alembic migration 20260805_0002 applied to PostgreSQL head (single linear chain); 55 new tests (workspaces 16, professional 12, citizen 10, session 9, org-guard 8) -> 130 identity/unit tests pass; ruff clean on all new modules; 7 Phase-8 reports at repo root + PROJECT_BRAIN refreshed. Prior: **GULA-ARCHITECT-001 COMPLETE** — the Enterprise Autonomous Architecture & Strategic Decision Engine built (deterministic architecture model, strategic ADRs, dependency analysis, technology roadmap, risk register, design review, scale simulation, AI coordination, health/maturity): 11 phases (audit → model → decisions → dependencies → evolution → risk → review → simulation → coordination → health → report), `architect-*` commands wired into the Kernel (audit, model, decisions, dependencies, evolution, risk, review, simulation, coordination, health, report, run, check), 92 architect tests → **984 engine tests pass** (architect 92 + optimizer 112 + learner 105 + deployer 126 + orchestrator 139 + reviewer 39 + builder 131 + kernel-ext 240); `architect-check`, `optimizer-check`, `kernel check`, `builder-check`, `reviewer-check`, `orchestrator-check`, `deployer-check`, `learner-check` all PASS; ruff clean on architect scope; Orchestrator detects the Architect as present (**11/11 systems**). Success criterion runs end-to-end idempotently: `architect-run` (16 audit surfaces verified → 12 bounded contexts → 10 strategic ADRs → 34 dependency findings (22 circular + 12 skip-layer) → 9 roadmap milestones → 11 risks → 8-dimension design review → 5 scale projections 100→1M → 6 AI contracts → health 59/100, maturity 72/100 quantitatively-managed → readiness 64/100 → implementation report). Prior: **GULA-OPTIMIZER-001 COMPLETE** — the Optimization Engine built (continuous performance, scalability, reliability, maintainability, DX, and resource-efficiency improvement without changing business behavior): 11 phases (audit → analysis → bottlenecks → architecture → resources → DX → debt → safe → evolution → quality → report), `optimizer-*` commands wired into the Kernel (audit, analyze, bottlenecks, architecture, resources, dx, debt, optimize, evolve, validate, report, run, check), 112 optimizer tests → **892 engine tests pass** (optimizer 112 + learner 105 + deployer 126 + orchestrator 139 + reviewer 39 + builder 131 + kernel-ext 240); `optimizer-check`, `kernel check`, `builder-check`, `reviewer-check`, `orchestrator-check`, `deployer-check`, `learner-check` all PASS; ruff clean on optimizer scope; enterprise validation VERDICT PASS (ruff baseline 379, tsc 0, eslint 0, brain fresh); Orchestrator now detects the Optimizer as present (**11/11 systems**). Success criterion runs end-to-end idempotently: `optimizer-run` (audit → 11 metrics → 2 bottlenecks → 10 arch recs → 10 resource recs → 8 DX dims → 7 debt records → 2 verified safe optimizations −8% → 7 evolution proposals → quality score 100/100 → implementation report); every optimization is measured, verified, reversible, and never changes business behavior (OPT-000001..2 verified, EVO-000001..7 proposals pending governance). Prior: **GULA-LEARNER-001 COMPLETE** — the Learning Engine built (the permanent engineering memory of the platform): 11 phases (audit → extraction → skill → playbook → runbook → memory → pattern → improve → quality → search → report), `learner-*` commands wired into the Kernel, 105 learner tests → 780 engine tests pass; knowledge quality gate 7/7 PASS; every mission produces permanent, versioned, searchable knowledge (SKILL-000008, PLAYBOOK-000005, RUNBOOK-000006, KNOW-000002, knowledge graph, proposals PRO-000001..6).

## Objective
Transform the GULA monorepo into a production-grade national healthcare platform by fixing infrastructure, security, architecture, frontend–backend alignment, and code quality across the entire codebase.

## Important Details
- Python 3.12 is the fixed target (all Dockerfiles, CI, mypy config `python_version = "3.12"`, `requires-python = ">=3.12"`). **System `python3` may be 3.10 — use `backend/.venv/bin/python` for repo scripts.**
- `_compat.py` simplified to direct stdlib imports (no more Python 3.10/3.11 fallback).
- Arabic is the primary language; `frontend-v3` is Arabic‑first with `dir="rtl"` in `index.html`.
- Backend integration tests require PostgreSQL (available via `backend/.venv/bin/python -m pytest tests/` with `ENV=test PYTHONPATH=..`); **2845 tests pass** across all suites (integration + unit + governance).
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
- Unit test coverage: **200 tests** across 14 test files (10 service + governance + architecture + ops).
- Frontend test coverage: **54 tests** across 3 files (utils, hooks).

### Blocked
- 62 `backref=` remain in inactive bounded contexts — not blocking.
- `mypy` times out on full backend codebase (too many capabilities/ modules).
- `docker compose` v2 unavailable (no sudo). `docker-compose` v1 broken. Multi-container orchestration uses raw `docker` commands.
- `test_comprehensive.py` (103 tests) passes in ~2.4s locally; 120s CI timeout sufficient.
- Constitution enforcer (advisory) fails Rule 1: 52 source files without tests (mostly dormant contexts) — tracked.

## Next Move
0. **COMPLETE — PROGRAM-BETA:** Production Readiness certified across 8 phases — Security (real SQLi fixed in `ai/knowledge_graph.py::create_node` via bind params + CAST jsonb, react-router 7.18.2→8.3.0 migration kills HIGH RSC-CSRF advisory → npm audit 0 vulns, `reencrypt_encryption_key.py` identifier guard, nginx frontend CSP/HSTS headers, Semgrep+bandit clean on scope), Performance (0 bottlenecks, 18/18 budget tests, p95 ≤35 ms), Reliability (retry/backoff + circuit breaker + bulkhead + timeout + outbox auto-repair + Redis fallback, 28 tests), Observability (Prometheus `/metrics/prom` + OTLP/HTTP vendor-neutral tracing + JSON logs + health/ready/deep, 30 tests), Deployment (multi-stage non-root image + compileall gate + HEALTHCHECK, hardened compose, 43 valid K8s manifests + HPA/PDB/PVC/overlays), Disaster Recovery (live PG16 backup→drop→restore round-trip, 0 errors, WAL→S3, RPO≈1 min), Quality Gates (`validate --fast` PASS: ruff 379 baseline/tsc 0/eslint 0/brain fresh/56-migration chain; architecture gate 57 ack + 0 new; domain 11/11), Autonomous Repair (self-heal dry-run e2e + 600s cooldown + RepairEngine, 20 tests). **9 root reports** (PRODUCTION_READINESS, SECURITY_CERTIFICATION, PERFORMANCE_REPORT, RELIABILITY_REPORT, OBSERVABILITY_REPORT, PRODUCTION_DEPLOYMENT, DISASTER_RECOVERY_REPORT, MASTER_RISK_REGISTER, MASTER_REMAINING_WORK §0); PROJECT_BRAIN refreshed; **full backend suite 4865 passed / 0 failed (9m50s)** + latent self-diagnostics CWD bug fixed (`scripts/kernel/diagnostics.py` `_component_present` anchored to REPO_ROOT, regression test). Next: migrate the 57 acknowledged Shared Core findings (notifications/audit/authorization/engines/barcode/qr/encryption) to canonical providers, behaviour-preserving, one at a time.
1. **COMPLETE — PROGRAM-ALPHA:** sovereign national platform architecture consolidated + constitution-gated. ONE authoritative Shared Core (`SHARED_CORE_CATALOG` 23→**50 services**, provider paths verified, catalog⇄tuple lockstep test); **Architecture Constitution engine** (`scripts/architecture/` + `scripts/architecture.py`: scan/gate/country/report/constitution/docs/baseline/check, wired into Kernel, **17 new tests** → 143 identity+domain+architecture pass); **deterministic baseline gate** — 57 acknowledged reimplementation + 2 country findings at `.ai/core/architecture/constitution_baseline.json`, any NEW finding fails (`architecture-check` = Shared Core scan + domain 11/11 isolation PASS + country-agnostic, **added to `ai-governance.yml` as a HARD gate**); 9 master docs generated by `scripts/architecture/docs.py` (MASTER_ARCHITECTURE_v2, SHARED_CORE_REGISTRY, DOMAIN_SOVEREIGNTY, DOMAIN_DEPENDENCY_GRAPH, WORKSPACE_ARCHITECTURE, DIGITAL_TRUST_PLATFORM, MASTER_REMAINING_WORK + ARCHITECTURE_CONSTITUTION + ARCHITECTURE_CERTIFICATION). Next: migrate the 57 acknowledged findings to canonical providers, behaviour-preserving, one at a time.
1. **COMPLETE — PROGRAM-STABLE-004:** permanent Domain Platform Framework built and certified. `backend/app/domain_platform` (8-section Blueprint, 23-service Shared Core catalog, 11 canonical Domains, real-source IsolationValidator, ContractRegistry/CrossDomainGateway, DomainLifecycle, SemVer versioning, WorkspaceBindingRegistry, 9-check DomainCertificationEngine) + Alembic `20260806_0001` (6 niam_domain_* tables) + 16 routes under `/niam/domains` wired in `factory.py` + `scripts/domains` engine (`domain-audit/isolate/certify/docs/report/check`) through the Kernel. **Platform CERTIFIED 11/11 Domains @ 100%, isolation PASS (0 findings)**; 71 new tests → 197 identity+domain tests pass; ruff clean on scope; 7 DOMAIN_*.md docs; Orchestrator detects 13 systems. Fixed real bugs (WORKSPACE_DOMAIN_MAP primary-owner collision, `DomainService.transition` undefined `from_state`). Next: wire the DB-backed `/niam/domains` API into a service test with the sqlite conftest pattern, run PG migration `20260806_0001`, and integrate certification into CI as a hard gate.
2. **COMPLETE — PROGRAM-STABLE-003:** National Identity Platform established — IdentityType 11 canonical types + legacy `canonical()` aliases; Workspace Platform (8 tables, 23 endpoints, ONE active workspace, permissions never cross workspaces); Cross-Org Guard (zero cross-domain admin); Professional Registry (verify() = ONLY privilege-activation path); Citizen Registry (country-agnostic configurable providers); Session security (workspace binding + max concurrent). Alembic `20260805_0002` applied to PG head; 55 new tests → 130 identity tests pass; ruff clean; 7 Phase-8 reports at root; brain refreshed. Next: wire `check_permission`/`OrganizationAccessGuard` into domain authorization, call `enforce_max_concurrent_sessions` at login, frontend workspace selector.
3. **COMPLETE — GULA-ARCHITECT-001:** Enterprise Architecture & Strategic Decision Engine built and e2e-verified (`architect-run`/`architect-check` PASS, 92 tests, ruff clean on scope, wired into Kernel as `architect-*`). Engine outputs: 16 audit surfaces, 12 bounded contexts, 10 ADRs, 34 dependency findings, 9 roadmap milestones, 11 risks, 8-dimension review, 5 scale projections 100→1M, 6 AI contracts, health 59/100 + maturity 72/100 (quantitatively-managed) + readiness 64/100.
4. **COMPLETE — Reviewer acceptance workflow:** `reviewer-verify <mission> [file...] [--git]` reviews a Builder change-set (scoped checks across all 8 areas, deterministic verdict); `reviewer-gate <mission> [file...] [--git]` gates the change-set before merge, `reviewer-gate` still gates the whole repo when no mission is given. 41 tests → **933 engine tests pass** (reviewer 80 + optimizer 112 + learner 105 + deployer 126 + orchestrator 139 + builder 131 + kernel-ext 240). Next: PROGRAM-011 WARN burn-down.
5. **COMPLETE — PROGRAM-011 WARN burn-down:** (a) ASHS per-signal cooldown (`scripts/self_heal.py`, `ASHS_ACTION_COOLDOWN=600` + file-persisted map), (b) outbox-backlog repair (`auto_repair.py` `outbox_poll` 10s→2s, auto-restored), (c) OpenTelemetry SDK export (`app/telemetry.py` OTLP/HTTP → Jaeger/Tempo, env-gated, wired in `factory.py`; 27 tests: `test_self_heal_cooldown.py` 8 + `test_outbox_auto_repair.py` 12 + `test_telemetry.py` 7). Remaining WARNs: cloud snapshot restore, frontend `/metrics` page, ENCRYPTION_KEY rotation re-encryption.
6. **COMPLETE — MASTER_ROADMAP Q3/Q4 governance:** component-level baselines (`reports/validation/baseline.json` v2: backend/frontend-v3/android), Android + DB validators in the engine (`_validator_android_consistency`, `_validator_db_migrations`), brain auto-refresh post-merge (`ai-governance.yml` `brain-refresh` job). Next: remaining WARNs (cloud snapshot restore, frontend `/metrics` page, ENCRYPTION_KEY rotation) or the concrete Next Moves below.
7. Reduce architecture debt (32 L1 layer violations, L3 75, L4 375 — L2 circular deps now 0; score 21.4/100) — advisory but tracked
8. **COMPLETE — Frontend component tests:** **122 tests across 9 files**; all 8 UI primitives (Badge, Button, Card, Input, Select, Textarea, Dialog, DataTable) covered via `primitives.test.tsx` (19) + `ui-components.test.tsx` (24) + `DataTable.test.tsx` (5/8) + `Dialog.test.tsx` (6) — committed `9ea90238`/`fdef3bb6`.
9. Backend unit-test coverage gaps (active services with no unit test file): `care_continuum_service`, `consent_service`, `device_trust_service`, `hospital_service`, `offline_sync_service`, `patient_service`, `risk_based_auth_service`, `claims_service` (`identity_service` is covered; `pricing_service` does not exist — stale)
10. Fix remaining N999 module naming violations (71, mostly dormant `national_data/models/warehouse/` star-schema modules)

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
- `backend/migrations/versions/20260805_0002_stable_identity_platform.py` — PROGRAM-STABLE-003: 8 workspace tables + professional registry + citizen providers + session workspace binding (applied to PG head)
- Docker run: `-v /path/to/shared:/app/shared:ro -e REDIS_URL="redis://:password@gula-redis:6379/0"`

### NIAM Identity Platform (PROGRAM-STABLE-003)
- `backend/app/identity/models/identity.py` — `IdentityType` 11 canonical types + legacy `canonical()` aliases + `CANONICAL_IDENTITY_TYPES`- `backend/app/identity/workspaces/` — models.py (8 tables), services.py (`WorkspaceService`: create/suspend/close, roles, members, `select_active_workspace` = ONE active, `check_permission` never crosses workspaces, invitations, permission templates, departments, teams, delegation), routes.py (23 endpoints)
- `backend/app/identity/organizations/guard.py` — `OrganizationAccessGuard`: zero cross-domain administration
- `backend/app/identity/professional_registry/` — models.py, services.py (`verify()` = ONLY privilege activation; `is_privileged()` single enforcement point; 12 professions), routes.py (7 endpoints)
- `backend/app/identity/citizen_registry/` — models.py (configurable providers, 8 identifier types, hashed storage), services.py, routes.py (4 endpoints)
- `backend/app/identity/services/session_service.py` — `bind_workspace`/`unbind_workspace`/`get_workspace_bound_sessions`/`enforce_max_concurrent_sessions`
- `backend/app/identity/models/session.py` — `workspace_id` FK + `workspace_bound_at`
- `backend/app/identity/models/audit.py` — 29 new PROGRAM-STABLE-003 AuditAction values
- `backend/tests/unit/test_niam_workspaces.py` (16), `test_niam_professional_registry.py` (12), `test_niam_citizen_registry.py` (10), `test_niam_session_security.py` (9), `test_niam_org_guard.py` (8)
- Root reports: `IDENTITY_PLATFORM_CERTIFICATION.md`, `WORKSPACE_CERTIFICATION.md`, `ORGANIZATION_PLATFORM_REPORT.md`, `PROFESSIONAL_REGISTRY_REPORT.md`, `CITIZEN_PLATFORM_REPORT.md`, `SESSION_SECURITY_REPORT.md`, `IDENTITY_API_REFERENCE.md`

### Domain Platform Framework (PROGRAM-STABLE-004)
- `backend/app/domain_platform/core.py` — Blueprint vocabulary (8 sections), Shared Core service list, lifecycle states/transitions, ContractKind, `DOMAIN_WORKSPACE_TYPES` (emergency→hospital, citizen_portal→citizen, provider_portal→professional), `DomainContract`/`DomainManifest`, `assert_blueprint_rule`
- `backend/app/domain_platform/shared_core.py` — **50-service** `SHARED_CORE_CATALOG` (authoritative Shared Core registry, PROGRAM-ALPHA: providers verified on disk), `is_shared_core_import`, `is_infrastructure_reimplementation` (word-boundary regex signals)
- `backend/app/domain_platform/manifest.py` — `CANONICAL_DOMAINS` (11 Domains with hand-curated blueprints + api namespaces), `WORKSPACE_DOMAIN_MAP` (primary owner per workspace), `workspace_ui_for` (union of hosted Domains), `assert_no_cross_domain_administration`
- `backend/app/domain_platform/isolation.py` — `IsolationValidator` + `DomainIsolationReport`: cross-domain imports, circular deps (DFS), shared mutable state, permission leakage (namespace ownership), direct DB coupling, table overlaps; real-source scanning via repo_root
- `backend/app/domain_platform/contracts.py` — `ContractRegistry` (versioned/documented/distinct-domain enforcement) + `CrossDomainGateway` (single legal cross-domain path)
- `backend/app/domain_platform/lifecycle.py` — `DomainLifecycle` state machine (install/activate/suspend/upgrade/rollback/backup/restore/health/metrics) with auditable `LifecycleEvent` history
- `backend/app/domain_platform/versioning.py` — `parse_version`/`compare_versions`/`is_compatible` (MAJOR = breaking), `DomainVersionRegistry`
- `backend/app/domain_platform/binding.py` — `WorkspaceBindingRegistry` (assert_domain_workspace, assert_ui_allowed = no cross-workspace UI)
- `backend/app/domain_platform/certification.py` — 9-check `DomainCertificationEngine` + `platform_certification` verdict
- `backend/app/domain_platform/models.py` / `services.py` / `routes.py` — 6 `niam_domain_*` tables, `DomainService` (register/transition/certify/…), 16 routes under `/niam/domains`
- `backend/migrations/versions/20260806_0001_domain_platform.py` — 6 niam_domain_* tables (down_revision 20260805_0002)
- `scripts/domains/{core,pipeline,report,cli}.py` + `scripts/domains.py` — governance engine; `domain-audit/isolate/certify/docs/report/check` wired into Kernel
- `backend/tests/unit/test_domain_platform.py` — **71 tests** (blueprint, shared core, lifecycle, versioning, contracts, binding, isolation, certification)
- Root docs: `DOMAIN_FRAMEWORK.md`, `DOMAIN_BLUEPRINT.md`, `DOMAIN_CONTRACTS.md`, `DOMAIN_ISOLATION_CERTIFICATION.md`, `DOMAIN_LIFECYCLE.md`, `DOMAIN_VERSIONING.md`, `DOMAIN_REGISTRY.md`; state at `.ai/core/domains/state/DATA.json`

### Architecture Constitution Engine (PROGRAM-ALPHA)
- `scripts/architecture/core.py` — constitution vocabulary: 18 guarded capabilities (identity/authentication/authorization/notifications/audit/workflow/rule/barcode/QR/search/encryption/cache/events/DI/scheduler/document engines), canonical provider allowlists, word-boundary signal scanner, deterministic `iter_source_files`
- `scripts/architecture/gate.py` — baseline-gated enforcement: `run_constitution_gate` (57 acknowledged findings), `run_domain_gate` (11/11 certification + isolation via Domain Platform), `run_country_agnostic_scan` (national markers only in national layer); **any NEW finding fails**
- `scripts/architecture/report.py` — regenerates `ARCHITECTURE_CONSTITUTION.md` + `ARCHITECTURE_CERTIFICATION.md`
- `scripts/architecture/docs.py` — regenerates the 7 master docs (MASTER_ARCHITECTURE_v2, SHARED_CORE_REGISTRY, DOMAIN_SOVEREIGNTY, DOMAIN_DEPENDENCY_GRAPH, WORKSPACE_ARCHITECTURE, DIGITAL_TRUST_PLATFORM, MASTER_REMAINING_WORK)
- `scripts/architecture/cli.py` + `scripts/architecture.py` — commands `architecture-scan/gate/country/report/constitution/docs/baseline/check`, wired into Kernel
- `.ai/core/architecture/constitution_baseline.json` — 57 reimplementation + 2 country findings (acknowledged debt; never grow)
- `.github/workflows/ai-governance.yml` — `architecture-check` HARD CI gate
- `backend/tests/unit/test_architecture_constitution.py` — **17 tests** (rules, canonical exemption, scan detection, baseline logic, repo gates PASS)

### Frontend Tests
- `frontend-v3/src/lib/__tests__/utils.test.ts` — **46 tests**: cn, formatNumber, getFlagColor, getStatusColor, getGenderLabel, getLabTypeLabel, getRoleLabel, getTierLabel, getTierColor
- `frontend-v3/src/hooks/__tests__/useDebounce.test.ts` — **3 tests**: initial value, delayed update, timer cancellation
- `frontend-v3/src/hooks/__tests__/useToast.test.ts` — **5 tests**: empty start, add, auto-dismiss, dismiss, multiple
- `frontend-v3/src/test/setup.ts` — vitest setup file (@testing-library/jest-dom matchers)

### Reviewer Engine (GULA-REVIEWER-001)
- `scripts/reviewer/core.py` — shared scoring/decision primitives (area weights, severity penalties, Decision enum)
- `scripts/reviewer/{architecture,code,security,test,deployment,docs,performance,knowledge}_review.py` — 8 area review modules
- `scripts/reviewer/decision.py` + `report.py` — deterministic verdict aggregation, JSON state, gate()
- `scripts/reviewer/verify.py` — Phase 11 change-set verification (`reviewer-verify <mission>`): resolves a Builder change-set (mission record → explicit files → git), runs scoped checks across all 8 areas, writes `REVIEWER_VERIFY_REPORT.md` + `state/latest_verify.json`; `reviewer-gate <mission>` gates only the change-set
- `scripts/reviewer/audit.py`, `scripts/reviewer/cli.py`, `scripts/reviewer.py` — Phase 0 audit + CLI + launcher
- `REVIEWER_AUDIT_REPORT.md` / `REVIEWER_IMPLEMENTATION_REPORT.md` — root audit + verdict reports
- Commands: `reviewer-audit`, `reviewer-review`, `reviewer-area`, `reviewer-gate`, `reviewer-report`, `reviewer-check`, `reviewer-verify`, plus per-area shortcuts
- `frontend-v3/vite.config.ts` — added `test` section (vitest config)

### Orchestrator Engine (GULA-ORCHESTRATOR-001)
- `scripts/orchestrator/core.py` — shared constants, enums, dataclasses, engine/surface maps
- `scripts/orchestrator/{audit,classifier,planner,router,dependencies}.py` — phases 0-4 (audit, classify, plan, route, DAG schedule)
- `scripts/orchestrator/{checkpoint,failure,resources,dashboard,history,report}.py` — phases 5-10 (checkpoint, failure, resources, dashboard, history, report)
- `scripts/orchestrator/cli.py` + `scripts/orchestrator.py` — CLI + launcher; wired into `scripts/kernel/cli.py` as `orchestrator-*`
- `.ai/core/orchestrator/` — README + mission registry (`history/registry.json`); runtime checkpoints/missions gitignored
- `MISSION_STATUS.md` / `ORCHESTRATOR_AUDIT_REPORT.md` / `ORCHESTRATOR_IMPLEMENTATION_REPORT.md` — root reports
- Commands: `orchestrator-audit`, `orchestrator-mission`, `orchestrator-classify`, `orchestrator-plan`, `orchestrator-route`, `orchestrator-checkpoint`, `orchestrator-resume`, `orchestrator-status`, `orchestrator-history`, `orchestrator-report`, `orchestrator-check`
- Tests: `backend/tests/unit/test_orchestrator_*.py` — **139 tests** across 11 files

### Deployer Engine (GULA-DEPLOYER-001)
- `scripts/deployer/core.py` — shared constants, enums, dataclasses, path helpers
- `scripts/deployer/{audit,architecture,execution,infrastructure,health,rollback}.py` — phases 0-5 (audit, topology, pipeline, infra, health, rollback)
- `scripts/deployer/{scaling,observability,security,knowledge,report}.py` — phases 6-10 (scaling, observability, security, knowledge, report)
- `scripts/deployer/cli.py` + `scripts/deployer.py` — CLI + launcher; wired into `scripts/kernel/cli.py` as `deployer-*`
- `.ai/core/deployer/` — README + deployment registry (`history/registry.json`) + inventory + runbook
- `DEPLOYER_AUDIT_REPORT.md` / `DEPLOYER_IMPLEMENTATION_REPORT.md` — root reports
- Commands: `deployer-audit`, `deployer-architecture`, `deployer-pipeline`, `deployer-infrastructure`, `deployer-health`, `deployer-rollback`, `deployer-scaling`, `deployer-observability`, `deployer-security`, `deployer-knowledge`, `deployer-report`, `deployer-deploy`, `deployer-check`
- Tests: `backend/tests/unit/test_deployer_*.py` — **126 tests** across 5 files

### Learner Engine (GULA-LEARNER-001)
- `scripts/learner/core.py` — shared constants, enums, dataclasses, knowledge vocabulary
- `scripts/learner/{audit,extract,skills,playbooks,runbooks}.py` — phases 0-4 (audit, extraction, skills, playbooks, runbooks)
- `scripts/learner/{memory,patterns,improve,quality,search,report}.py` — phases 5-10 (memory, patterns, improve, quality, search, report)
- `scripts/learner/cli.py` + `scripts/learner.py` — CLI + launcher; wired into `scripts/kernel/cli.py` as `learner-*`
- `.ai/core/learner/` — README + search index (`search_index.json`) + state (`extractions`, `patterns`, `proposals`, `history`)
- `LEARNER_AUDIT_REPORT.md` / `LEARNER_IMPLEMENTATION_REPORT.md` — root reports
- Commands: `learner-audit`, `learner-extract`, `learner-skill`, `learner-playbook`, `learner-runbook`, `learner-memory`, `learner-patterns`, `learner-improve`, `learner-quality`, `learner-search`, `learner-report`, `learner-learn`, `learner-check`
- Tests: `backend/tests/unit/test_learner_*.py` — **105 tests** across 5 files
- Tests: `backend/tests/unit/test_learner_*.py` — **105 tests** across 5 files

### Optimizer Engine (GULA-OPTIMIZER-001)
- `scripts/optimizer/core.py` — shared constants, enums, dataclasses, metric/bottleneck/technique vocabulary
- `scripts/optimizer/{audit,analyze,bottlenecks,architecture,resources}.py` — phases 0-4 (audit, baseline analysis, bottleneck detection, architecture recommendations, resource optimization)
- `scripts/optimizer/{developer_experience,debt,safe,evolution,quality,report}.py` — phases 5-10 (DX, performance debt, safe optimization, evolution proposals, quality validation, report)
- `scripts/optimizer/cli.py` + `scripts/optimizer.py` — CLI + launcher; wired into `scripts/kernel/cli.py` as `optimizer-*`
- `.ai/core/optimizer/` — README + state (`benchmarks`, `runs`, `bottlenecks`, `debt`, `proposals`, `architecture`, `resources`, `developer_experience`)
- `OPTIMIZER_AUDIT_REPORT.md` / `OPTIMIZER_IMPLEMENTATION_REPORT.md` — root reports
- Commands: `optimizer-audit`, `optimizer-analyze`, `optimizer-bottlenecks`, `optimizer-architecture`, `optimizer-resources`, `optimizer-dx`, `optimizer-debt`, `optimizer-optimize`, `optimizer-evolve`, `optimizer-validate`, `optimizer-report`, `optimizer-run`, `optimizer-check`
- Tests: `backend/tests/unit/test_optimizer_*.py` — **112 tests** across 5 files

### Architect Engine (GULA-ARCHITECT-001)
- `scripts/architect/core.py` — shared constants, dataclasses, maturity levels, JSON helpers
- `scripts/architect/{audit,model,decisions,dependencies,evolution}.py` — phases 0-4 (audit, bounded-context model, strategic ADRs, dependency analysis with lock-in scan, technology roadmap)
- `scripts/architect/{risk,review,simulation,coordination,health,report}.py` — phases 5-10 (risk register, 8-dimension design review, scale simulation, AI coordination contracts, health+maturity, report)
- `scripts/architect/cli.py` + `scripts/architect.py` — CLI + launcher; wired into `scripts/kernel/cli.py` as `architect-*`
- `.ai/core/architect/` — README + state (`model`, `decisions`, `dependencies`, `evolution`, `risks`, `review`, `simulation`, `coordination`, `health`)
- `ARCHITECT_AUDIT_REPORT.md` / `ARCHITECT_IMPLEMENTATION_REPORT.md` — root reports
- Commands: `architect-audit`, `architect-model`, `architect-decisions`, `architect-dependencies`, `architect-evolution`, `architect-risk`, `architect-review`, `architect-simulation`, `architect-coordination`, `architect-health`, `architect-report`, `architect-run`, `architect-check`
- Tests: `backend/tests/unit/test_architect_*.py` — **92 tests** across 5 files
