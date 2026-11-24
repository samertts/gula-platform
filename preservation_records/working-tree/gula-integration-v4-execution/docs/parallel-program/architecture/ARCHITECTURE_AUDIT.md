# ARCHITECTURE AUDIT — PROGRAM-GULA-PARALLEL-001 (AGENT 01)

**Agent:** A01 — Repository & Architecture Auditor
**Wave:** A (parallel discovery, READ-ONLY)
**Date:** 2026-11-19
**Repository:** `gula-integration` @ `integration/gula-unification-v1` (HEAD `2206654d`)
**Companion report:** `docs/parallel-program/architecture/REPOSITORY_DEPENDENCY_MAP.md`

---

## 0. Hard constraints observed by this audit

1. **READ-ONLY** on all source, config, test and design files. No code, refactor, rename, delete,
   migration, test, build or server execution was performed. No git state change of any kind.
2. **WRITE ONLY** to the two owned paths under `docs/parallel-program/architecture/`.
3. **PROTECTED USER WORK:** 379 paths in `git status --porcelain` at audit time (Phase 0 recorded
   378; the delta is not from this agent). This includes all of `backend/app/health_core/**`,
   `backend/app/domain_platform/**`, `backend/app/communication/**`, `shared/communication/**`,
   20 staged renames into `archive/legacy/`, untracked migrations and governance documents.
   These trees are **reported on only**.
4. **PLATFORM-CORE MUST NOT BE RESTRUCTURED BY THIS PROGRAM.** This is an explicit standing
   prohibition recorded repeatedly in `GOVERNANCE/GECS/MASTER_CONTROL.md:48`,
   `GOVERNANCE/GECS/DECISION_REGISTRY.md:42`, `GOVERNANCE/GULA_STABLE_V1_PROGRAM_CHARTER.md:20`,
   `GOVERNANCE/NATIONAL_INTEGRATION_ROADMAP.md:172`, and `GOVERNANCE/FINAL_DECISION.md:313`.
   It applies both to the upstream `gula-platform` core (the source of truth for `backend/app/`)
   and to any local `platform/core/**` kernel tree. A01 makes **no recommendation to restructure,
   merge, move, delete or rewire Platform-Core**. Findings below are observations and
   approval-gated options only.
5. PROGRAM-CONSTITUTION-001 is evaluated, never weakened: Free First, Open Source First,
   Self-Hosted First, No Vendor Lock-In, Zero Paid Dependency, Reuse Before Build, Local AI First,
   Free Security First (`AGENTS.md:6-41`; full policy `docs/constitution/COST_GOVERNANCE.md`).

---

## 1. Method and evidence base

Read-only commands and static analysis only:

- Filesystem enumeration of **51 non-hidden top-level directories** (57 including 6 hidden:
  `.audit`, `.githooks`, `.github`, `.mypy_cache`, `.ruff_cache`, `.semgrep`), 54 tracked
  top-level directories at `HEAD`.
- Read-only git inspection: `git status --porcelain`, `git ls-tree`, `git log --diff-filter=D`,
  `git show -s` (no index/worktree mutation).
- Read-only **AST parsing** (Python `ast`, no module import/execution) of 2,031 Python modules
  under `backend/app/` to build an internal import graph, package-level cycle detection and
  strongly-connected-component analysis; analogous inspection of TypeScript `package.json`,
  `tsconfig`, `pnpm-workspace.yaml`, lockfiles and CI workflow paths.
- Existing artifacts reused rather than re-created (Reuse Before Build):
  `CLAUDE.md`, `ARCHITECTURE.md`, `docs/architecture/CANONICAL_ARCHITECTURE.md`,
  `docs/architecture/MODULE_DEPENDENCY_MATRIX.md`, `docs/architecture/ADR-011-fhir-strategy.md`,
  `GOVERNANCE/AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md`, `DEPENDENCY_INTELLIGENCE_REPORT.md`,
  `ARCHITECTURE_CLEANUP_REPORT.md`, `frontend-v3/FRONTEND_UNIFICATION.md`.

**Limits of evidence:** line counts and file counts are snapshots of the working tree and include
protected user work. No runtime behaviour, performance benchmark or database state was measured.
Where a conclusion is inferred rather than directly observed it is explicitly labelled
*(inferred)*.

---

## 2. Executive summary

| Area | Verdict | Evidence |
|---|---|---|
| Production backend | **Complete / dominant** — FastAPI monolith, 63 route modules on disk, 91 `include_router` registrations, health/self-healing/startup guard | `backend/app/factory.py:579-834`, `CLAUDE.md:80-248`, `docker-compose.yml:84-196` |
| Canonical frontend | **Complete for declared scope** — `frontend-v3` is the sole program FE reference, deployed via compose; many pages remain contract-gated | `frontend-v3/FRONTEND_UNIFICATION.md:5`, `docker-compose.yml:240-268`, `frontend-v3/package.json:6-23` |
| Monorepo consolidation | **Partial** — legacy `frontend/`/`frontend-v2/` are deleted, but catalogs, docs, bridge routes and parallel app trees still reference them | `git log b2b73850` (2026-08-14), `frontend-v3/src/pages/migration/frontendSurfaceCatalog.ts:22-25` |
| Workspace/build topology | **Fragmented** — root `pnpm-workspace.yaml` includes only `packages/*`; 11 other `package.json` trees, 9 lockfiles, 4 TypeScript majors | `pnpm-workspace.yaml:1-4`, manifests table in companion report |
| Microservices | **Stubs** — 7 of 9 `services/` services are 2-file `main.py`+`Dockerfile` scaffolds, yet CI image matrix and compose tooling treat them as deployable | `services/{lab,order,patient,result,sample,notification,ai,autonomous_manager}/`, `CLAUDE.md:159-166` |
| New untracked domain trees | **Partial / parallel** — `domain_platform` and `communication` are wired into `factory.py`; `health_core` is self-contained and not wired to the app | `backend/app/factory.py:822-828`; zero `health_core` references in `main.py`/`factory.py` |
| Architecture governance docs | **Stale / self-contradictory** — documented invariants ("no circular deps", "36 route modules", "17 models") no longer match the tree | `docs/architecture/MODULE_DEPENDENCY_MATRIX.md:40-44`, `ARCHITECTURE.md:135-136`, AST analysis |
| Constitution posture | **Mostly compliant with documented ADRs; one unreviewed coupling risk** — S3 SDK + MySQL stack in `apps/*` vs self-hosted PostgreSQL/MinIO baseline | `apps/gula-web-suite/package.json:16-17,64`, `docs/constitution/COST_GOVERNANCE.md:78-99` |

**Finding counts:** P0 = 0 · P1 = 4 · P2 = 11 · P3 = 4 (19 total).
No P0 was found; no component is halted by this audit. Nine findings are **BLOCKED for Wave C**
because they require architecture decisions beyond A01's reviewer role and/or touch protected paths.

---

## 3. Repository topology (what actually exists)

### 3.1 Consolidation history vs current state

`CLAUDE.md:8-14` records the three-repository consolidation:

| Former repo | Documented location | Current on-disk state (verified) |
|---|---|---|
| `samertts/gula-platform` | `backend/`, `services/`, `nhop-platform/`, `ai/` | Present; `backend/app/` is the production source of truth |
| `samertts/LabLink-Core` | `services/device_bridge/` | Present (47 files); active in `docker-compose.yml:428` (`device-bridge`) |
| `samertts/Front-end-` | `frontend-v2/` | **Deleted** in `b2b73850` (2026-08-14) — `frontend-v2/` and `frontend/` are absent at HEAD |

Later parallel trees were added without being declared in that consolidation table:
`apps/gula-web-suite/`, `apps/gula-platform-ui-refresh/`, `platform/` (8 role apps + kernel +
UI + reports), `mobile-expo/` alongside native `mobile/`, root demo `client/`+`server/`,
`packages/uap/`, and the untracked `health_core`/`domain_platform`/`communication` trees.

### 3.2 Layer model in the production monolith

The declared model (`docs/architecture/MODULE_DEPENDENCY_MATRIX.md:22-37`) is:

```
config / _compat (leaf)
   -> database.py -> models/ -> services/ -> routes/ -> factory.py/main.py
                      core/  -> security/
                      domain/ (pure)
   + 60+ vertical slices (national/, capabilities/, identity/, ehr/, ...)
```

Verified: **no module-level (import-time) circular imports** exist in `backend/app/`
(exact-module SCC analysis: 0). Layering is largely respected: zero `services→routes`,
`domain→routes`, `health_core→routes`, `models→routes` imports. Three lazy `core→services`
imports exist inside composition functions (`backend/app/core/startup.py:270,305-306`).
The real coupling problem is at **package scope** (see A01-006).

`backend/app/factory.py` is the single composition root: **91 `include_router` calls**
(`:579-834`), including the untracked-user-work registrations at `:822-828`.

### 3.3 New untracked domain trees (report only)

| Tree | State | Wiring | Architecture shape |
|---|---|---|---|
| `backend/app/health_core/` (≈40 `.py` + caches, 45 test files in `backend/tests/health_core/`) | **Untracked user work** | **Not imported by `main.py` or `factory.py`; no external consumers outside its own package and `scripts/phase_b_gate.py:41,72-75,261,283`** | Clean Architecture-style: `contracts/`, `common/`, `identity/ports`, `clinical/{entities,ports,repositories,services}`, `lab/`, `fhir/`, `audit_anchor/`, `authorization/`, `reliability/`; self-contained imports only |
| `backend/app/domain_platform/` (18 `.py` + config + caches) | **Untracked user work** | **Wired**: `backend/app/factory.py:822-824` | Domain manifest/contract/lifecycle/dormancy certification; uses `app.database`, `app.identity.security`, `app.domain_platform.*` |
| `backend/app/communication/` + `shared/communication/` (8 + 13 `.py`) | **Untracked user work** | **Wired**: `backend/app/factory.py:826-828`; imports `shared.communication` (`backend/app/communication/__init__.py:21-30`) | Ports/sinks/domain/gateway + shared providers/policy/queue/audit |

This is a **positive** Clean Architecture signal in the new trees, but it creates two concerns:
(a) `health_core` duplicates authorization/audit/terminology concepts with no production wiring;
(b) `domain_platform` and `communication` are live yet untracked, so Wave C cannot touch them.

---

## 4. Clean Architecture & SOLID assessment

| Principle | Observed adherence | Gap |
|---|---|---|
| Dependency direction (inner→outer) | Good in `backend/app/{domain,services,models,security}/`; zero direct reverse imports found | `core/startup.py:270,305-306` performs lazy composition imports of `services/`; documented invariant `MODULE_DEPENDENCY_MATRIX.md:43` says "Core never imports … services" — imprecise, not an import-time cycle |
| Single Responsibility | Partial: 91 routers in one `factory.py`; `national/` (346 files) and `capabilities/` (275 files) are large aggregators | Central composition root and very wide packages concentrate change risk (A01-007) |
| Interface Segregation / DIP | Good in new trees (`health_core/*/ports.py`, `domain_platform/contracts.py`, `shared/communication/*`) | Canonical FE (`frontend-v3`) does **not** consume `packages/uap` despite its ADR declaring it the single runtime (A01-003) |
| Open/Closed | Kernel plugin system exists (`backend/app/kernel/plugins/`, `platform/core/plugins/`) | Two parallel plugin/kernel implementations (`backend/app/kernel` vs `platform/core/kernel`) with no stated canonical owner |
| DRY / Reuse Before Build | `shared/` is genuinely reused by 37 backend modules; `CANONICAL_ARCHITECTURE.md:120-137` records real extractions | `services/shared/` legacy copies remain; 5 FHIR trees; two workflow engines (A01-010, A01-015, A01-016) |

**Conclusion:** the legacy monolith is *mostly* layered despite its size; the architecture risk is
**system duplication and ambiguous canonical ownership**, not gross layer inversion.

---

## 5. Bottlenecks and single points of failure (architectural, not benchmarked)

1. **Single composition root** — `backend/app/factory.py:579-834` (91 router registrations).
   An error in one late import can prevent all routes from registering. *(inferred from structure)*
2. **Single data plane** — all clinical paths converge on one SQLAlchemy engine/session
   (`backend/app/database.py`) and one PostgreSQL instance (`docker-compose.yml:14-50`);
   `CLAUDE.md:180-184` defines one connection-pool budget for the whole platform.
3. **Single global configuration** — `backend/app/config.py` is imported by essentially every
   module (`MODULE_DEPENDENCY_MATRIX.md:57`); secret/flag changes have global blast radius.
4. **Shared library fan-in** — 37 backend files import `shared.*`; a change in `shared/models`,
   `shared/audit`, `shared/events` or `shared/logging` propagates widely (A01-019).
5. **Event bus fan-out** — `GOVERNANCE/AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md:29,82-84` identifies
   the kernel event bus as the widest consumer set (outbox + national scheduling, observability,
   document, rules). This is the highest-blast-radius internal change point.
6. **Single canonical frontend** — `frontend-v3` is the only FE in `docker-compose.yml:243-268`
   and 22 CI references; other app trees have no deployment path. This is a deliberate
   consolidation, not a defect, but it means the unification gate is a delivery choke point.
7. **Gateway chain** — host nginx → Docker api-gateway → backend (`ARCHITECTURE.md:5-57`);
   `api-gateway` declares `depends_on` health conditions for both backend and frontend
   (`docker-compose.yml:290-299`), so either unhealthy service delays gateway readiness.
8. **Prototype demo runtime** — root `server/index.ts` keeps in-memory
   `demoAttempts`/`revokedDemoSessions` maps (`:35-36`); inherently single-process state
   *(inferred; not a production path)*.

---

## 6. Completed vs incomplete systems (evidence-based)

| System | Maturity | Evidence |
|---|---|---|
| FastAPI monolith, middleware, health endpoints, self-healing | **Complete (production)** | `CLAUDE.md:90-153`, `backend/app/factory.py`, `docker-compose.yml:84-196` |
| Alembic migration set | **Complete (101 tracked + 8 untracked user migrations)** | `PROGRAM_CONTROL.md:112-125` (verified counts); A01 did not execute migrations |
| `frontend-v3` SPA + verification gates | **Complete for declared scope; several pages contract-gated** | `frontend-v3/package.json:6-23`, `frontend-v3/FRONTEND_UNIFICATION.md:5,21-30` |
| `services/device_bridge` (LabLink-Core) | **Complete / deployed as profile** | `services/device_bridge/README.md:1-30`, `docker-compose.yml:428` |
| `nhop-platform` | **Partial but self-contained** (own FastAPI, Alembic, compose, tests, 2 CI references) | `nhop-platform/{app,alembic,tests,requirements.txt,Dockerfile,docker-compose.yml}` |
| `backend/app/health_core` | **Partial / unwired** | 45 test files; zero references in `main.py`/`factory.py`; `scripts/phase_b_gate.py` |
| `domain_platform` / `communication.experience` | **Partial / wired** | `backend/app/factory.py:822-828` |
| `platform/` national applications suite | **Partial; reports claim production but no CI/compose wiring found** | `platform/reports/MASTER_EXECUTION.md:203`, `platform/reports/pi-003/ARCHITECTURE.md:13`; zero `platform/` references in `.github/workflows/` |
| `packages/uap` | **Partial / orphan** (full API surface exported, zero consumers) | `packages/uap/package.json:9-62`; `@gula/uap` occurrences are docs/SBOM only |
| `services/*` (7 of 9) | **Stub** | each contains only `main.py` + `Dockerfile`; e.g. `services/lab/main.py` |
| Root `client/` + `server/` + `api/demo-api` | **Stub / demo-only** | `server/index.ts:53-87,286-341`, `client/src/App.tsx:80-138`, `api/demo-api/[...path].js` (single file) |
| `frontend/`, `frontend-v2/` | **Abandoned / deleted, still documented** | `git show b2b73850`; `CLAUDE.md:167-170`, `frontend-v3/FRONTEND_UNIFICATION.md:15,39` |
| Dormant generated workflow scaffold (ENG-A12) | **Dormant** | `GOVERNANCE/AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md:19,36,85-86` |

---

## 7. Findings

> Format: ID · Severity · Title · Evidence · Affected components · Root cause · Safe-fix? · Approval?

### A01-001
- **Severity:** P1
- **Title:** Multiple independent frontend application trees coexist outside the declared canonical surface and outside the root workspace.
- **Evidence:** `frontend-v3/FRONTEND_UNIFICATION.md:5` (frontend-v3 is the reference surface); `pnpm-workspace.yaml:1-4` (only `packages/*`); `apps/gula-web-suite/package.json:1-13`; `apps/gula-platform-ui-refresh/package.json:1-14`; `platform/apps/{citizen,doctor,hospital,laboratory,ministry,nurse,pharmacy,radiology}/package.json`; `docker-compose.yml:243-268` (only frontend-v3 deployed).
- **Affected components:** `frontend-v3`, `apps/*`, `platform/apps/*`, `packages/uap`, CI, deployment.
- **Root cause:** three-repo consolidation (`CLAUDE.md:8-14`) was followed by separate app-generation streams; no workspace or deployment registry enforces the "one canonical surface" decision.
- **Safe-fix possible?** No — retiring or rewiring an application changes user-facing routes and contract governance; A01 is read-only in Wave A.
- **Approval required?** **Yes** — canonical-surface and legacy-retirement decision is an architecture change; `AGENT_ASSIGNMENTS.md:66` makes A01 a reviewer only.

### A01-002
- **Severity:** P1
- **Title:** Root demo runtime (`server/index.ts` + `client/`) duplicates backend and frontend entry points and is invisible to production deployment.
- **Evidence:** `package.json:7-19` (`dev: tsx watch server/index.ts`, `start: node dist/server/index.js`, `build: tsc && vite build`); `vite.config.ts:8-22` (`root: .../client`); `tsconfig.json:22-43` (`@/* → client/src/*`); `server/index.ts:12-17,286-341` (Express demo session/dashboard); `client/src/App.tsx:80-138`; no `server`/`client` service in `docker-compose.yml`; no root `dist/` on disk.
- **Affected components:** root build scripts, `client/`, `server/`, `api/demo-api/`, developer/CI entry points.
- **Root cause:** an isolated demo-preview stack was integrated into the monorepo root without migrating root scripts or documenting it as non-production in `CLAUDE.md`/`ARCHITECTURE.md`.
- **Safe-fix possible?** No for code/scripts — changing root scripts affects all developers and CI semantics; documentation-only clarification would be safe but is outside A01's write set.
- **Approval required?** **Yes** — build/entry-point ownership decision affects CI and developer workflow (CR-004 precedent: verify commands before assuming).

### A01-003
- **Severity:** P1
- **Title:** `packages/uap` is declared the single application runtime but has zero production consumers; competing design systems remain.
- **Evidence:** `packages/uap/package.json:2-4,9-62` (exports 12 subpaths); `packages/uap/ADR.md:15-37` ("single Unified Application Platform package", "every future GULA application MUST import"); `packages/uap/APPLICATION_PLATFORM_REPORT.md:58-59` (migration still pending); repository-wide `@gula/uap` matches are confined to its own docs/SBOM and `docs/sbom/latest.sbom.json`; `frontend-v3/src` contains no `@gula/` import; parallel `platform/ui/package.json:1-21` (`@gula/ui-platform`).
- **Affected components:** `packages/uap`, `platform/ui`, `frontend-v3`, `mobile-expo`.
- **Root cause:** ADR adopted but migration not executed; three design-system packages now exist with no enforced consumer.
- **Safe-fix possible?** No — adoption or retirement requires a new ADR and coordinated code changes.
- **Approval required?** **Yes** — reversing/replacing an accepted architecture decision needs orchestrator and domain-owner approval.

### A01-004
- **Severity:** P1
- **Title:** `platform/` is a parallel 636-file national applications platform with its own kernel, 8 role apps and reported "production" status, but no root workspace, CI or deployment wiring.
- **Evidence:** `platform/core/**` (kernel, CQRS, plugins, event bus, workflow, observability), `platform/apps/*` (8 apps), `platform/ui/package.json:1-21`; `platform/reports/MASTER_EXECUTION.md:203` ("✅ Production"); `platform/reports/pi-003/ARCHITECTURE.md:13` (micro-frontend architecture); `pnpm-workspace.yaml:1-4` (platform absent); `.github/workflows/` contains no `platform/` path; `docker-compose.yml` contains no platform service.
- **Affected components:** `platform/**`, `frontend-v3` (claimed duplicate role surfaces), CI/CD, deployment.
- **Root cause:** a parallel program produced a second application platform inside the same repository without integration into the canonical workspace/pipeline.
- **Safe-fix possible?** No.
- **Approval required?** **Yes** — **and the standing prohibition applies: Platform-Core MUST NOT be restructured by this program** (`GOVERNANCE/GECS/MASTER_CONTROL.md:48`; `GOVERNANCE/GULA_STABLE_V1_PROGRAM_CHARTER.md:20`). A01 recommends *no* structural action on `platform/core/**` or upstream Platform-Core.

### A01-005
- **Severity:** P2
- **Title:** Seven `services/` microservices are 2-file stubs with direct SQL access and deprecated lifespan hooks, while CI treats the tree as deployable.
- **Evidence:** `services/{ai,autonomous_manager,lab,notification,order,patient,result,sample}/` each contain only `main.py` + `Dockerfile`; `services/lab/main.py:11-13,38-48,58-64` (direct asyncpg pool, `@app.on_event`); `CLAUDE.md:121-123` forbids reintroducing `@app.on_event` in the monolith; `CLAUDE.md:159-166` and `CLAUDE.md:398-399` describe CI image matrix for 8 images.
- **Affected components:** `services/*`, CI image matrix, deployment manifests.
- **Root cause:** forward-decomposition scaffolds were shipped and included in build tooling before business logic/tenant/audit contracts were defined.
- **Safe-fix possible?** No — removing images or changing service behaviour is a deployment/API decision.
- **Approval required?** **Yes** — CI semantics and published artefacts are affected (`AGENT_ASSIGNMENTS.md:62`; PROGRAM_CONTROL §7).

### A01-006
- **Severity:** P2
- **Title:** Eleven package-level import cycles contradict the documented "no circular dependencies" invariant; all are currently broken by lazy imports.
- **Evidence:** `docs/architecture/MODULE_DEPENDENCY_MATRIX.md:40-44,577` ("no circular deps", lazy imports); AST analysis found 11 package-level cycles and 90 lazy cross-package edges, with **0 exact module-level SCCs**; examples: `backend/app/identity/workflows/routes.py:10` → `app.workflows.engine` ↔ `backend/app/workflows/models.py:5` → `app.identity.base`; `backend/app/clinical_gateway/context.py:12-22` ↔ `backend/app/identity/services/account_request_service.py:15`; `backend/app/kernel/rules_runtime.py:10,13` ↔ `backend/app/national/scheduling_platform/application/service.py:9-10`; `backend/app/services/clinical_service.py:11-36` ↔ `backend/app/clinical/command_guard.py:22`.
- **Affected components:** `app/identity`, `app/workflows`, `app/clinical_gateway`, `app/services`, `app/clinical`, `app/kernel`, `app/national`, `app/ehr`, `app/national_data`.
- **Root cause:** vertical slices import each other's internals instead of public interfaces; lazy imports suppress import-time failure but preserve bidirectional coupling.
- **Safe-fix possible?** No — introducing public interfaces/ports across nine packages is a refactor with behaviour risk; A01 is reviewer.
- **Approval required?** **Yes** — modular-monolith boundary change (`PLATFORM-CONSTITUTION.md:38` treats cross-module interface violations as blockers).

### A01-007
- **Severity:** P2
- **Title:** `backend/app/factory.py` is a 91-registration single composition root and an architectural single point of failure.
- **Evidence:** `backend/app/factory.py:579-834` (91 `include_router` calls; late imports at `:801-834`); `docs/architecture/MODULE_DEPENDENCY_MATRIX.md:60` (explicitly labels it a central composition root with tight coupling); `CLAUDE.md:108-123` (middleware/lifespan ownership).
- **Affected components:** all backend routes, app startup.
- **Root cause:** all route registration is centralised in one function to control middleware/startup ordering.
- **Safe-fix possible?** No — splitting registration changes startup semantics and middleware order (security-sensitive).
- **Approval required?** **Yes** — startup/auth behaviour is approval-gated (`CLAUDE.md:365-372`).

### A01-008
- **Severity:** P2
- **Title:** Untracked `health_core` is a parallel Clean Architecture domain with its own authorization, audit anchor and FHIR adapters, and is not wired into the production app.
- **Evidence:** 40+ `.py` files under `backend/app/health_core/{authorization,audit_anchor,clinical,fhir,identity,lab,reliability,terminology,...}`; zero `health_core` references in `backend/app/main.py` or `backend/app/factory.py`; only external references are `scripts/phase_b_gate.py:41,72-75,261,283` and 45 test files under `backend/tests/health_core/`. Tree is untracked user work (`PROGRAM_CONTROL.md:67`).
- **Affected components:** `app/health_core`, `app/security`, `app/services/audit_service.py`, `app/terminology`, FHIR surfaces.
- **Root cause:** an independent "synthetic" clean-core implementation was developed in parallel with the production monolith; integration decision is not recorded in source.
- **Safe-fix possible?** No — and **forbidden in Wave A**: the files are protected user work.
- **Approval required?** **Yes** — any wiring/deletion requires the user and orchestrator; two authorization/audit sources of truth must not be silently merged.

### A01-009
- **Severity:** P2
- **Title:** Route→ORM/database imports and lazy core→services imports persist despite the cleanup report claiming full layer separation.
- **Evidence:** `backend/app/routes/clinical_documentation.py:12-14` and `backend/app/routes/clinical_orders.py:12-14` import `app.database`, `app.models.lab_user`, `app.security.dependencies`; `backend/app/core/startup.py:270,305-306` imports `app.services.*` inside functions; `ARCHITECTURE_CLEANUP_REPORT.md:113-120` claims 35 ORM-violating routes resolved; `docs/architecture/MODULE_DEPENDENCY_MATRIX.md:43` states "Core never imports routes or services".
- **Affected components:** `app/routes`, `app/core`, `app/services`, architecture documentation.
- **Root cause:** extraction was completed for three routes only; the invariant was documented as universal rather than as a target state; composition code legitimately reaches services via lazy imports.
- **Safe-fix possible?** No — moving query logic changes clinical behaviour and tenant-scoping paths.
- **Approval required?** **Yes** — clinical/DB behaviour and documented invariants (`CLAUDE.md:365-372`).

### A01-010
- **Severity:** P3
- **Title:** Legacy `services/shared/` copies of canonical `shared/` modules remain with no consumers.
- **Evidence:** `services/shared/{audit.py,messaging.py,circuit_breaker.py,__init__.py}`; `docs/architecture/CANONICAL_ARCHITECTURE.md:124-126` marks these "✅ Bridged"; repository grep found no production import of `services.shared`.
- **Affected components:** `services/shared`, `shared/`.
- **Root cause:** consolidation copied canonical modules before bridges were declared complete; copies were never retired.
- **Safe-fix possible?** Yes in principle (delete after import-gate proof), but not by A01 in Wave A.
- **Approval required?** **Yes** — deletion of tracked source requires orchestrator approval and a clean-file check (`FILE_OWNERSHIP_MATRIX.md:69-79`).

### A01-011
- **Severity:** P2
- **Title:** Frontend unification gate validates string fragments in a stale catalog whose `frontend-v2` source was deleted; this gives false assurance of source coverage.
- **Evidence:** `frontend-v3/src/pages/migration/frontendSurfaceCatalog.ts:22-25` still lists `sourcePath: "frontend-v2"`, `status: "bridge"`; `frontend-v3/scripts/verify-frontend-unification.mjs:8-11,31-35` checks only literal `fragments`; `git show -s b2b73850` (2026-08-14 removed `frontend/` and `frontend-v2/`); `frontend-v3/FRONTEND_UNIFICATION.md:39` records the 13 Aug 2026 inventory.
- **Affected components:** `frontend-v3` verification gate, `LegacyRouteBridge`, migration documentation.
- **Root cause:** verification asserts text presence, not filesystem existence or semantic equivalence; the catalog was not updated after deletion.
- **Safe-fix possible?** Yes technically (update catalog/gate to assert existence), but A01 is not the remediator and the change alters gate semantics.
- **Approval required?** **Yes** — gate semantics change; CR-004 requires verification before relying on named gates.

### A01-012
- **Severity:** P2
- **Title:** Eleven `package.json` trees, nine lockfiles and four TypeScript majors create incompatible dependency graphs inside one repository.
- **Evidence:** manifests at root, `frontend-v3`, `mobile-expo`, `packages/uap`, `platform/ui`, `platform/update`, `platform/ai`, `platform/apps/*` (8), `apps/*` (2), `contracts/sdk/typescript`; lockfiles list in companion report; TypeScript `6.0.3` (`package.json:59`), `~5.7.0` (`frontend-v3/package.json:54`), `5.9.3` (`apps/gula-web-suite/package.json:102`), `~7.0.2` (`platform/ui/package.json:40`); React `19.2.8` vs `19.2.1` across manifests.
- **Affected components:** all JS/TS surfaces, CI caching, bundle budgets, SBOM.
- **Root cause:** no enforced monorepo package manager topology; root `pnpm-workspace.yaml` covers only `packages/*` while both npm and pnpm lockfiles are used.
- **Safe-fix possible?** No — dependency upgrades/consolidation affect builds and are not A01's write scope.
- **Approval required?** **Yes** — dependency policy `docs/architecture/DEPENDENCY_APPROVAL_POLICY.md`.

### A01-013
- **Severity:** P2
- **Title:** Parallel app trees couple to proprietary cloud SDKs and a MySQL stack without an ADR or free-alternative evaluation, contrary to the self-hosted baseline.
- **Evidence:** `apps/gula-web-suite/package.json:16-17` (`@aws-sdk/client-s3`, presigner), `:64` (`mysql2`), `:56` (`drizzle-orm`); `apps/gula-platform-ui-refresh/package.json:17-18,57,65`; `docs/constitution/COST_GOVERNANCE.md:78-99` (approved self-hosted PostgreSQL/MinIO); `ARCHITECTURE.md:106-124` (prohibited cloud-specific coupling); no ADR found for these dependencies.
- **Affected components:** `apps/*`, data layer, constitution compliance evidence.
- **Root cause:** external app-generation stream selected an S3/MySQL stack without passing the architecture/dependency approval gate.
- **Safe-fix possible?** No — replacing a storage/database adapter changes data contracts and requires an ADR.
- **Approval required?** **Yes** — `COST_GOVERNANCE.md:58-67` requires ADR, TCO analysis and Engineering Lead approval for commercial/self-hosted-alternative decisions. Note: the SDKs are open source; the finding is **vendor-coupling risk**, not a proven paid dependency.

### A01-014
- **Severity:** P3
- **Title:** Architecture documentation counts and component lists are stale relative to the current tree.
- **Evidence:** `ARCHITECTURE.md:135-138` ("36 route modules", "17 ORM models", "15 core modules") vs 63 route `.py` files and 33 model `.py` files on disk; `CLAUDE.md:167-170` documents `frontend-v2/` and `frontend/` as runnable while both are deleted (`git log --diff-filter=D`); `docs/architecture/CANONICAL_ARCHITECTURE.md:22-23` lists removed presentation surfaces.
- **Affected components:** onboarding/agent guidance, architecture governance evidence.
- **Root cause:** docs were not updated with the 2026-08-14 frontend deletion or later module growth.
- **Safe-fix possible?** Yes (documentation-only), but not in A01's write set except its own two reports.
- **Approval required?** **Yes** for root-level docs — orchestrator owns `AGENTS.md`/`CLAUDE.md`-adjacent governance; modifying them is outside A01's write paths.

### A01-015
- **Severity:** P2
- **Title:** Multiple workflow/event/task engines coexist, including a dormant generated scaffold and an unmounted national CDS router.
- **Evidence:** `GOVERNANCE/AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md:14-36` (ENG-A01 canonical, ENG-A12 "DORMANT", ENG-A05 widest fan-out), `:50` (ENG-B09 national CDS router unmounted by observed `factory.py`), `:82-88` (risk hotspots); `backend/app/capabilities/workflow_engine/**`, `backend/app/workflows/`, `backend/app/identity/workflows/`, archived legacy `archive/legacy/workflow_runtime/**` (20 staged renames, protected).
- **Affected components:** workflow, event bus, task queues, national CDS, archive.
- **Root cause:** successive programs added engines without retiring earlier ones; archive moves are staged user work not yet reflected in all docs.
- **Safe-fix possible?** No — enabling/deleting engines can alter clinical and authorization behaviour.
- **Approval required?** **Yes** — clinical/authorization behaviour requires independent sign-off; GOVERNANCE explicitly says "do not enable" ENG-B09.

### A01-016
- **Severity:** P2
- **Title:** Five distinct FHIR implementations coexist despite ADR-011 naming one canonical implementation.
- **Evidence:** `docs/architecture/ADR-011-fhir-strategy.md` ("`backend/app/routes/ehr_fhir.py` … canonical FHIR implementation"); on disk: `backend/app/fhir/` (6 files), `backend/app/interoperability/` (14), `backend/app/ehr/` (16), `backend/app/health_core/fhir/` (6, untracked), `backend/app/national/fhir/` (19).
- **Affected components:** interoperability, EHR, national FHIR, health_core, device bridge.
- **Root cause:** domain-sliced FHIR modules were added per programme without a single owner enforcing the ADR.
- **Safe-fix possible?** No — choosing a canonical mapping affects clinical exchange contracts (A05 domain).
- **Approval required?** **Yes** — clinical interoperability behaviour change; A01 only reports.

### A01-017
- **Severity:** P3
- **Title:** Two mobile stacks (`mobile/` native and `mobile-expo/`) are both CI-active with no documented single canonical client.
- **Evidence:** `.github/workflows/mobile-android.yml:73,114,240,301` builds/tests `mobile/android`; `.github/workflows/mobile-ios.yml`, `mobile-flutter-desktop.yml`; `.github/workflows/mobile-expo.yml:26,36` builds `mobile-expo`; `mobile-expo/package.json:1-12`; 538 files in `mobile/` vs 133 in `mobile-expo/`; neither `CLAUDE.md:171-176` nor `ARCHITECTURE.md` declares a canonical mobile client.
- **Affected components:** mobile clients, CI matrix, release pipelines.
- **Root cause:** native and cross-platform programmes run in parallel.
- **Safe-fix possible?** No — client retirement is a product decision.
- **Approval required?** **Yes** — release/CI semantics and API contract ownership.

### A01-018
- **Severity:** P3
- **Title:** Four separate AI implementation trees exist with no recorded canonical owner.
- **Evidence:** top-level `ai/` (16 `.py`), `backend/app/ai/` (16), `backend/app/ai_fabric/` (25), `platform/ai/` (`package.json`); `CLAUDE.md:176` explicitly notes "`ai/` … separate from `backend/app/ai/`"; `GOVERNANCE/AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md:42-46` lists multiple RAG/orchestrator engines.
- **Affected components:** AI gateways, CDS, AI platform endpoints.
- **Root cause:** AI capabilities were added independently at repository root, inside the monolith, in a fabric package and in the parallel platform.
- **Safe-fix possible?** No — consolidation changes clinical-AI behaviour and provider contracts.
- **Approval required?** **Yes** — clinical AI and Local-AI-First policy decisions (`AGENTS.md:29-33`).

### A01-019
- **Severity:** P2
- **Title:** The canonical `shared/` library has wide fan-in with no versioning or boundary gate at the monorepo level.
- **Evidence:** 37 files under `backend/app/` import `shared.*` (examples `backend/app/core/logging_config.py:7-10`, `backend/app/core/events.py:16-17`, `backend/app/models/base.py:7`, `backend/app/communication/__init__.py:21-30`); `shared/pyproject.toml` exists but root `pnpm-workspace.yaml` and Python `PYTHONPATH` wiring are the only integration (`ci.yml:150`); `docs/architecture/CANONICAL_ARCHITECTURE.md:7,37-74` declares `shared/` the single source of truth.
- **Affected components:** all backend vertical slices, `shared/*`, CI import paths.
- **Root cause:** canonical extraction succeeded, but no compatibility contract or change gate limits blast radius.
- **Safe-fix possible?** No — introducing versioned interfaces is a cross-cutting refactor.
- **Approval required?** **Yes** — architecture and dependency policy.

---

## 8. Constitution posture (no change proposed)

- **Free/Open Source/Self-Hosted:** production stack is PostgreSQL 17/Redis 7/nginx/Prometheus/Grafana/OpenSSL/Let's Encrypt — consistent with `COST_GOVERNANCE.md:78-99` and `ARCHITECTURE.md:106-118`. `docs/architecture/VENDOR_LOCK_IN_POLICY.md` and `FREE_FIRST_POLICY.md` exist.
- **Vendor-lock-in risk (A01-013):** `@aws-sdk/client-s3` in `apps/*` is open-source client code but couples those apps to a proprietary object-store API; the documented free/self-hosted alternative is MinIO (S3-compatible). No paid line item was found in manifests, so **Zero Paid Dependency is not proven violated**; an ADR/free-alternative record is absent.
- **Reuse Before Build:** `CANONICAL_ARCHITECTURE.md:120-137` documents genuine extractions into `shared/`; `docs/architecture/GULA_INTELLIGENT_PLATFORM_CORE.md:7-27` explicitly reuses existing inventories rather than duplicating them. The duplication findings above are the counter-pattern.
- **Local AI First:** no A01 action; AI duplication is reported (A01-018) without recommending any commercial API.

---

## 9. SCOPE_REQUESTs (not acted on)

1. **SCOPE-REQ-A01-01:** Orchestrator to rule on which of `frontend-v3`, `apps/*`, `platform/apps/*`, root `client/` is the sole supported UI per environment, and to record retire/keep decisions. A01 cannot delete or rewire any of them.
2. **SCOPE-REQ-A01-02:** Orchestrator/user to confirm the status of the untracked `health_core`, `domain_platform`, `communication` trees (prototype vs intended production) before any integration is considered. They remain protected and unwired/wired as recorded in §3.3.
3. **SCOPE-REQ-A01-03:** Orchestrator to assign A08 (or another authorized remediator) the stale `frontendSurfaceCatalog.ts` + `verify-frontend-unification.mjs` pair if gate correction is desired; changing gate semantics is outside A01's write set and CR-004.
4. **SCOPE-REQ-A01-04:** Orchestrator to confirm that **Platform-Core remains frozen** and that no Wave B/C work touches `platform/core/**` or upstream `gula-platform` core; A01 recommends zero restructuring.
5. **SCOPE-REQ-A01-05:** Orchestrator to route ADR/cost-governance review of `apps/*` S3/MySQL dependencies to the constitution owner before any consolidation.

---

## 10. Attestation

No source, config, test, design or root control file was modified by A01. No git state change,
migration, test run, build, server start or database connection occurred. Only the two owned
report files under `docs/parallel-program/architecture/` were written.
