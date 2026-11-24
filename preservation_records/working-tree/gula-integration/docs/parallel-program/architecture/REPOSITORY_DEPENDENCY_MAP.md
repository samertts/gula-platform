# REPOSITORY DEPENDENCY MAP — PROGRAM-GULA-PARALLEL-001 (AGENT 01)

**Agent:** A01 — Repository & Architecture Auditor
**Wave:** A (parallel discovery, READ-ONLY)
**Date:** 2026-11-19
**Repository:** `gula-integration` @ `integration/gula-unification-v1` (HEAD `2206654d`)
**Companion report:** `docs/parallel-program/architecture/ARCHITECTURE_AUDIT.md`

---

## 0. Hard constraints observed by this map

1. **READ-ONLY** on all source, config, test, design and root control files. No code, refactor,
   rename, delete, migration, test, build, server or database action was performed.
2. **WRITE ONLY** to the two A01-owned paths under `docs/parallel-program/architecture/`.
3. **PROTECTED USER WORK** is reported on only: `backend/app/health_core/**`,
   `backend/app/domain_platform/**`, `backend/app/communication/**`, `shared/communication/**`,
   20 staged renames into `archive/legacy/`, untracked migrations and governance documents.
4. **PLATFORM-CORE MUST NOT BE RESTRUCTURED BY THIS PROGRAM.** This map does not recommend moving,
   merging, deleting or rewiring `platform/core/**` or the upstream `gula-platform` core.
   The standing prohibition is recorded in `GOVERNANCE/GECS/MASTER_CONTROL.md:48`,
   `GOVERNANCE/GECS/DECISION_REGISTRY.md:42`,
   `GOVERNANCE/GULA_STABLE_V1_PROGRAM_CHARTER.md:20`,
   `GOVERNANCE/NATIONAL_INTEGRATION_ROADMAP.md:172` and `GOVERNANCE/FINAL_DECISION.md:313`.
5. Findings are evidence-based. Inferences are labelled *(inferred)*. No architecture is invented
   and PROGRAM-CONSTITUTION-001 is not weakened.

---

## 1. Method and evidence base

- Filesystem/git enumeration of top-level trees, tracked manifests, lockfiles and workflow paths.
- Read-only Python `ast` analysis of 2,031 modules under `backend/app/` (Wave-A pass):
  **0 exact module-level SCCs**, **11 package-level cycles**, **90 lazy cross-package edges**.
- Static inspection of `package.json`, `pnpm-workspace.yaml`, lockfiles, `tsconfig.json`,
  `vite.config.ts`, `docker-compose.yml` and `.github/workflows/*.yml`.
- Existing architecture artifacts reused rather than re-created (Reuse Before Build):
  `CLAUDE.md`, `ARCHITECTURE.md`, `docs/architecture/CANONICAL_ARCHITECTURE.md`,
  `docs/architecture/MODULE_DEPENDENCY_MATRIX.md`, `docs/architecture/ADR-011-fhir-strategy.md`,
  `GOVERNANCE/AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md`,
  `frontend-v3/FRONTEND_UNIFICATION.md`.

**Limits:** no runtime, network, build, test or database observation was performed. Counts are
working-tree snapshots and include protected user work. “Deployed” below means **declared in
`docker-compose.yml`**, not observed at runtime.

---

## 2. Textual dependency graph

### 2.1 Deployed runtime graph (observed declarations)

```
docker-compose.yml
├── postgres / redis
│   └──> gula-backend, gula-worker
├── gula-backend
│   └── backend/app/main.py
│       └── backend/app/factory.py            [91 include_router registrations]
│           ├── config / database / models / security / services / routes
│           ├── shared.*                       [37 backend importers]
│           ├── domain_platform, communication [wired at factory.py:822-828]
│           └── 60+ vertical slices
├── frontend
│   └── frontend-v3 only                       [docker-compose.yml:243-268]
├── api-gateway
│   └── depends_on gula-backend + frontend     [docker-compose.yml:270-299]
├── device-bridge                              [docker-compose.yml:428]
└── observability: prometheus / grafana / alertmanager / ntfy
```

**Not in the deployed graph:** root `client/` + `server/`, `api/demo-api/`, `apps/*`,
`platform/apps/*`, `platform/ui`, `packages/uap`, `mobile*`, `nhop-platform`, and the seven
`services/` stubs. This is a consolidation fact, not by itself a defect; the risk is that
non-deployed trees still claim parity in documentation and CI.

Evidence: `docker-compose.yml:14-50,84-196,243-268,270-299,428`;
`backend/app/factory.py:579-834,822-828`; `CLAUDE.md:80-248`.

### 2.2 Production backend internal graph

```
config / _compat                         (leaves)
   └──> database.py
        └──> models/
             └──> services/
                  └──> routes/
                       └──> factory.py
                            └──> main.py

cross-cutting: core/ ──> database, models, security, services (3 lazy imports at startup)
               security/ ──> core, database, models, services
               domain/    (pure; no route imports observed)
shared.* ──> imported by 37 backend modules
vertical slices: national/, capabilities/, identity/, ehr/, clinical/, kernel/, ...
```

Verified invariants:

- **0 exact module-level import cycles** in `backend/app/`; the documented “no circular
  dependencies” rule holds only at exact-module/import-time scope.
- **11 package-level cycles** are suppressed by lazy imports. Examples from the Wave-A AST pass:
  `app.identity.workflows.routes:10` ↔ `app.workflows.models:5`;
  `backend/app/clinical_gateway/context.py:12-22` ↔
  `backend/app/identity/services/account_request_service.py:15`;
  `backend/app/kernel/rules_runtime.py:10,13` ↔
  `backend/app/national/scheduling_platform/application/service.py:9-10`;
  `backend/app/services/clinical_service.py:11-36` ↔ `backend/app/clinical/command_guard.py:22`.
- **90 lazy cross-package edges** preserve bidirectional coupling even though import-time failure
  is avoided.
- Residual layer leaks: `backend/app/routes/clinical_documentation.py:12-14` and
  `backend/app/routes/clinical_orders.py:12-14` import `app.database`, `app.models.lab_user` and
  `app.security.dependencies`; `backend/app/core/startup.py:270,305-306` reaches `app.services.*`
  lazily. The documented invariant is at `docs/architecture/MODULE_DEPENDENCY_MATRIX.md:40-44,577`.

Related findings: A01-006, A01-007, A01-009, A01-019.

### 2.3 Protected/new domain trees (report only)

```
backend/app/health_core/**          self-contained; no main.py/factory.py import
   ├── contracts / common / identity / clinical / lab / fhir
   ├── audit_anchor / authorization / reliability / terminology
   └── tests: backend/tests/health_core/** [45 test files]
        └── scripts/phase_b_gate.py:41,72-75,261,283

backend/app/domain_platform/**      wired: factory.py:822-824
   └── app.database, app.identity.security, app.domain_platform.*

backend/app/communication/**        wired: factory.py:826-828
   └── shared.communication/**      (ports / sinks / policy / queue / audit)
```

These trees show a positive ports/adapters shape, but they are untracked protected work. A01 makes
no wiring, merge or deletion recommendation. Related scope request: SCOPE-REQ-A01-02.

### 2.4 JavaScript/TypeScript workspace graph

```
pnpm-workspace.yaml:1-4
└── packages/*
     └── packages/uap                 [declared single runtime; zero production consumers]

independent manifest trees (not in root workspace):
├── package.json                     [demo runtime: server/index.ts + client/ via Vite]
├── frontend-v3/package.json         [canonical UI; npm lock; CI + compose wired]
├── mobile-expo/package.json         [Expo client; CI active]
├── apps/gula-web-suite/package.json
├── apps/gula-platform-ui-refresh/package.json
├── platform/apps/*/package.json     [8 role apps]
├── platform/{ui,update,ai}/package.json
└── contracts/sdk/typescript/package.json
```

Counts: **11 manifest trees / 18 tracked `package.json` files** (17 first-party + 1 vendored
`mobile-expo/vendor/image-size/package.json`) and **9 lockfiles**:
`package-lock.json`, `frontend-v3/package-lock.json`, `mobile-expo/package-lock.json`,
`apps/gula-web-suite/pnpm-lock.yaml`, `apps/gula-platform-ui-refresh/pnpm-lock.yaml`,
`contracts/sdk/typescript/package-lock.json`, `platform/apps/pharmacy/package-lock.json`,
`platform/ui/package-lock.json`, `pnpm-lock.yaml`.

Version bands:

| Tree | TypeScript | React |
|---|---:|---|
| root (`package.json:59`) | `6.0.3` | `^19.2.8` (:26) |
| `frontend-v3/package.json:54` | `~5.7.0` | `^19.2.8` (:32) |
| `apps/*` (`gula-web-suite:102`) | `5.9.3` | `^19.2.1` (:67) |
| `packages/uap` | `^6.0.3` | `^18.0.0 || ^19.0.0` peer |
| `platform/{ui,apps,ai,update}`, `contracts/sdk/typescript` | `~7.0.2` / `^7.0.2` | `^19.2.8` / `^19.0.0` / `^18.2.0 || ^19.0.0` |
| `mobile-expo` | `~5.9.2` | `19.1.0` |

Evidence: `pnpm-workspace.yaml:1-4`; `package.json:7-19,26,59`;
`frontend-v3/package.json:6-23,32,54`; `apps/gula-web-suite/package.json:16-17,64,67,102`;
`apps/gula-platform-ui-refresh/package.json:17-18,57,65`; `platform/ui/package.json:1-21,40`;
`packages/uap/package.json:9-62`; `packages/uap/ADR.md:14-40`.

Related findings: A01-001, A01-003, A01-012, A01-013.

### 2.5 CI and deployment reachability

```
.github/workflows/ci.yml
├── backend jobs
├── frontend-v3 install/lint/typecheck/build  [ci.yml:196-208]
└── npm cache: frontend-v3/package-lock.json  [ci.yml:196]

frontend workflows: frontend-pwa.yml, frontend-e2e.yml, frontend-bundle-budget.yml,
                    iam-hardening.yml, preview-deploy.yml  -> frontend-v3 only
mobile workflows:   mobile-android.yml -> mobile/android
                    mobile-ios.yml, mobile-flutter-desktop.yml
                    mobile-expo.yml -> mobile-expo
sdk workflow:       sdk-publish.yml -> contracts/sdk/typescript

no path reference found in .github/workflows/*.yml for:
    platform/**, apps/**, packages/uap/**, root server/index.ts or root client/
```

Consequence: CI validates several trees that do not deploy, while the deployed tree is the only
one with full frontend gate coverage. Related findings: A01-001, A01-004, A01-005, A01-011,
A01-012, A01-017.

### 2.6 External coupling graph

```
production backend ──> PostgreSQL 17, Redis 7, self-hosted gateway/monitoring stack
                       [docker-compose.yml:14-50,270-410]
apps/*             ──> @aws-sdk/client-s3, @aws-sdk/s3-request-presigner, mysql2, drizzle-orm
                       [apps/gula-web-suite/package.json:16-17,56,64]
services/lab       ──> direct asyncpg pool; @app.on_event hooks
                       [services/lab/main.py:11-13,38-48,58-64]
shared/*           ──> fan-in to 37 backend modules
                       [docs/architecture/CANONICAL_ARCHITECTURE.md:37-74]
```

Constitution note: AWS SDK packages are open source; the observed issue is **vendor-coupling risk**
to a proprietary object-store API, not a proven paid dependency. The documented self-hosted
alternative is MinIO (`docs/constitution/COST_GOVERNANCE.md:78-99`). No new dependency is proposed.

---

## 3. Per-project status inventory table

Legend: **Workspace** = listed by root `pnpm-workspace.yaml`; **CI** = path/reference observed in
`.github/workflows/`; **Compose** = service declared in `docker-compose.yml`.

| Tree / project | Observed or claimed role | Workspace | CI | Compose | Status and evidence | A01 finding(s) |
|---|---|---|---|---|---|---|
| `backend/` | Production FastAPI monolith and source of truth | N/A (Python) | Yes | Yes (`gula-backend`, `gula-worker`) | **Complete/dominant**: 63 route files, 91 router registrations; `CLAUDE.md:80-248`; `backend/app/factory.py:579-834`; `docker-compose.yml:84-196` | A01-006, A01-007, A01-009 |
| `shared/` | Canonical Python extraction layer | N/A | Yes (`ci.yml:150` PYTHONPATH) | Via backend image | **Canonical, wide fan-in**: 37 importers; `docs/architecture/CANONICAL_ARCHITECTURE.md:7,37-74`; `shared/pyproject.toml` | A01-019 |
| `services/device_bridge/` | LabLink-Core device bridge | N/A | Limited | Yes (`:428`) | **Complete / profile-deployed**: 47 files; `services/device_bridge/README.md:1-30` | — |
| `services/{ai,autonomous_manager,lab,notification,order,patient,result,sample}/` | Intended microservices | N/A | Image matrix claimed | No | **Stub**: two files each (`main.py` + `Dockerfile`); `services/lab/main.py:11-13,38-48,58-64`; `CLAUDE.md:159-166,398-399` | A01-005 |
| `services/shared/` | Legacy shared copies | N/A | No | No | **Orphaned duplicates**: `audit.py`, `messaging.py`, `circuit_breaker.py`; no production importer found; `CANONICAL_ARCHITECTURE.md:124-126` | A01-010 |
| `frontend-v3/` | Declared canonical web surface | No (own npm lock) | Yes (22 refs) | Yes (`:243-268`) | **Complete for declared scope**; `FRONTEND_UNIFICATION.md:5`; `frontend-v3/package.json:6-23`; stale catalog/gate noted | A01-001, A01-011, A01-012 |
| `client/`, `server/`, `api/demo-api/` | Root demo preview | No | No root-runtime path found | No | **Stub/demo only**: `package.json:7-19`; `vite.config.ts:8-22`; `tsconfig.json:22-43`; no root `dist/` | A01-002 |
| `apps/gula-web-suite/` | Parallel full-stack app suite | No (own pnpm lock) | No path ref | No | **Partial / vendor-coupled**: S3 SDK + `mysql2`; `apps/gula-web-suite/package.json:16-17,56,64,102` | A01-001, A01-012, A01-013 |
| `apps/gula-platform-ui-refresh/` | Parallel UI refresh app | No (own pnpm lock) | No path ref | No | **Partial / vendor-coupled**: same stack shape; `apps/gula-platform-ui-refresh/package.json:17-18,57,65` | A01-001, A01-012, A01-013 |
| `platform/apps/{citizen,doctor,hospital,laboratory,ministry,nurse,pharmacy,radiology}/` | 8 national role micro-frontends | No | No path ref | No | **Partial**: each has a manifest; only pharmacy has a lockfile; `platform/reports/pi-003/ARCHITECTURE.md:13` | A01-001, A01-004 |
| `platform/ui/` | Parallel platform design system | No | No path ref | No | **Partial / unconsumed**: `@gula/ui-platform` exports; `platform/ui/package.json:1-21,40` | A01-003, A01-004 |
| `platform/core/**` | Parallel national kernel, plugins, event bus, workflow | N/A | No path ref | No | **Partial / frozen**: 636-file `platform/` program; production claims at `platform/reports/MASTER_EXECUTION.md:203`; **no A01 structural action** | A01-004; SCOPE-REQ-A01-04 |
| `platform/{ai,update}/` | Platform AI and update packages | No | No path ref | No | **Partial**: own manifests; TypeScript `^7.0.2`; `platform/ai/package.json`, `platform/update/package.json` | A01-004, A01-012, A01-018 |
| `packages/uap/` | Declared single application runtime | **Yes** (`packages/*`) | No production consumer | No | **Partial / orphan**: 12 exported subpaths; `@gula/uap` matches confined to docs/SBOM; `packages/uap/ADR.md:14-40`; `packages/uap/package.json:9-62` | A01-003 |
| `contracts/sdk/typescript/` | Published TS SDK | No | `sdk-publish.yml` | No | **Tracked / publishable**: `@gula-platform/sdk`; own `package-lock.json`; TypeScript `^7.0.2` | A01-012 |
| `mobile/` | Native mobile clients | N/A | Yes (`mobile-android.yml`, `mobile-ios.yml`, `mobile-flutter-desktop.yml`) | No | **CI-active, 538 files**; no declared canonical client; `CLAUDE.md:171-176` | A01-017 |
| `mobile-expo/` | Expo mobile client | No (own npm lock) | Yes (`mobile-expo.yml:26,36`) | No | **CI-active, 133 files**; `mobile-expo/package.json:1-12` | A01-017 |
| `nhop-platform/` | Self-contained FastAPI/Alembic platform | N/A | 2 path refs | Own compose only | **Partial / self-contained**: `nhop-platform/{app,alembic,tests,requirements.txt,Dockerfile,docker-compose.yml}` | — |
| `ai/`, `backend/app/ai/`, `backend/app/ai_fabric/`, `platform/ai/` | Four AI implementation trees | Mixed | Mixed | Via backend for `app/ai*` | **Partial / no canonical owner**: `CLAUDE.md:176`; `GOVERNANCE/AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md:42-46` | A01-018 |
| `backend/app/health_core/` | Clean-Architecture health core | N/A | Gate script only | No | **Untracked protected / unwired**: 40+ `.py`, 45 tests, zero `main.py`/`factory.py` imports; `scripts/phase_b_gate.py:41,72-75,261,283` | A01-008; SCOPE-REQ-A01-02 |
| `backend/app/domain_platform/`, `backend/app/communication/`, `shared/communication/` | New domain and communication layers | N/A | No dedicated gate found | Via backend | **Untracked protected / wired**: `backend/app/factory.py:822-828`; report-only | SCOPE-REQ-A01-02 |
| `archive/legacy/**` | Staged legacy moves | N/A | No | No | **Protected staged user work**: 20 renames; `GOVERNANCE/AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md:36,85-86` | A01-015 |
| `frontend/`, `frontend-v2/` | Former web surfaces | N/A | No (deleted) | No | **Deleted 2026-08-14** in `b2b73850`, still referenced in catalogs/docs; `frontend-v3/FRONTEND_UNIFICATION.md:15,39`; `CLAUDE.md:167-170` | A01-011, A01-014 |

---

## 4. Duplicate / overlap map

| Overlap area | Competing trees or mechanisms | Concrete evidence | Risk | Required decision (not made by A01) | Finding IDs |
|---|---|---|---|---|---|
| Web application surface | `frontend-v3` vs `apps/*` (2) vs `platform/apps/*` (8) vs root `client/` | `FRONTEND_UNIFICATION.md:5`; `pnpm-workspace.yaml:1-4`; `apps/*/package.json`; `platform/apps/*/package.json`; `docker-compose.yml:243-268` | Ambiguous canonical surface; duplicated auth/routing/design patterns | Orchestrator must declare supported UI per environment | A01-001 |
| Demo vs production runtime | Root `server/index.ts` + `client/` vs `backend/` + `frontend-v3` | `package.json:7-19`; `vite.config.ts:8-22`; `tsconfig.json:22-43`; no compose service | Root scripts point at a non-deployed demo; onboarding confusion | Confirm root entry-point ownership | A01-002 |
| Application runtime / design system | `packages/uap` vs `platform/ui` vs `frontend-v3` direct React/Tailwind | `packages/uap/ADR.md:14-40`; `packages/uap/package.json:9-62`; `platform/ui/package.json:1-21`; no `@gula/uap` source imports found | Accepted ADR has no consumer; three design-system sources | Uphold, replace or retire the ADR via authorized change | A01-003 |
| National platform kernels | `backend/app/kernel/**` vs `platform/core/**` plugins/event bus/workflow | `GOVERNANCE/AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md:29,82-84`; `platform/reports/MASTER_EXECUTION.md:203` | Two kernel implementations; widest event-bus blast radius | **Platform-Core remains frozen; no restructuring by this program** | A01-004; SCOPE-REQ-A01-04 |
| Workflow / event / task engines | `ENG-A01` canonical, `ENG-A12` dormant, `ENG-B09` unmounted, `capabilities/workflow_engine`, `app/workflows`, `identity/workflows`, staged `archive/legacy/workflow_runtime` | `GOVERNANCE/AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md:14-36,50,82-88` | Clinical/authorization behaviour divergence; dormant code can be mistaken for live | Domain owner must rule on enable/retire; GOVERNANCE says do not enable ENG-B09 | A01-015 |
| FHIR implementations | `routes/ehr_fhir.py` (canonical by ADR) plus `app/fhir/`, `interoperability/`, `ehr/`, `health_core/fhir/`, `national/fhir/` | `docs/architecture/ADR-011-fhir-strategy.md`; five trees on disk | Conflicting terminology mappings and exchange contracts | Clinical interoperability owner must confirm canonical mapping | A01-016 |
| AI implementations | `ai/`, `backend/app/ai/`, `backend/app/ai_fabric/`, `platform/ai/` | `CLAUDE.md:176`; `GOVERNANCE/AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md:42-46` | Multiple RAG/orchestrator/provider paths; Local-AI-First policy ambiguity | Record canonical owner without introducing commercial APIs | A01-018 |
| Shared utility libraries | Canonical `shared/**` vs legacy `services/shared/**` copies | `CANONICAL_ARCHITECTURE.md:120-137`; four files in `services/shared/`; no production importer found | Drift between canonical and copied audit/messaging/circuit-breaker code | Delete only after import-gate proof and approval | A01-010, A01-019 |
| Monolith vs microservices | 91 monolith routers vs seven two-file service scaffolds | `backend/app/factory.py:579-834`; `services/*/main.py`; `CLAUDE.md:159-166` | Published images imply capability that does not exist in source | CI/image-matrix owner must confirm stub status | A01-005 |
| Dependency graphs | 11 manifest trees, 18 manifests, 9 lockfiles, TypeScript `5.x`/`6.x`/`7.x` bands | `pnpm-workspace.yaml:1-4`; `git ls-files '*package.json'`; lockfile list above; manifest versions above | Incompatible caches, SBOM drift, unreproducible builds | Dependency-policy approval required (`DEPENDENCY_APPROVAL_POLICY.md`) | A01-012 |
| Frontend verification truth | String-fragment gate vs deleted `frontend-v2` source | `frontendSurfaceCatalog.ts:22-25`; `verify-frontend-unification.mjs:8-11,31-35`; `git show -s b2b73850` | False assurance of source coverage | Assign authorized remediator; gate semantics change | A01-011; SCOPE-REQ-A01-03 |
| Documentation inventories | Canonical docs vs current tree | `ARCHITECTURE.md:135-138`; `CLAUDE.md:167-170`; `CANONICAL_ARCHITECTURE.md:22-23`; AST/file counts | Agents rely on stale counts and removed surfaces | Root-doc owner must update; outside A01 write set | A01-014 |

---

## 5. Change-risk hotspots (architectural, not benchmarked)

| Hotspot | Fan-in/out evidence | Blast radius | A01 posture |
|---|---|---|---|
| `backend/app/factory.py:579-834` | 91 `include_router` calls; late imports at `:801-834` | All route registration and startup ordering | Report only; splitting requires approval |
| `backend/app/database.py` + `backend/app/config.py` | Single engine/session and near-universal config import; `MODULE_DEPENDENCY_MATRIX.md:57` | All clinical data paths; secret/flag changes | Report only |
| `shared/**` | 37 backend importers; `CANONICAL_ARCHITECTURE.md:37-74` | Cross-cutting compatibility | Report only; versioning needs ADR |
| Kernel event bus | Widest consumer set: outbox, national scheduling, observability, documents, rules; `AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md:29,82-84` | Highest internal change fan-out | Report only; Platform-Core frozen |
| `frontend-v3` unification gate | `frontend-v3/package.json:14,21`; stale catalog/gate above | Delivery choke point for the only deployed UI | Report only; SCOPE-REQ-A01-03 |
| Root build scripts | `package.json:7-19`; `vite.config.ts:8-22`; `tsconfig.json:22-43` | Developer and CI entry-point semantics | Report only; A01-002 |

---

## 6. Scope requests inherited from the audit

This companion map creates no new remediation authority. It inherits
`SCOPE-REQ-A01-01` … `SCOPE-REQ-A01-05` from `ARCHITECTURE_AUDIT.md §9`:

1. Rule on the sole supported UI per environment.
2. Confirm status of protected `health_core` / `domain_platform` / `communication` trees.
3. Assign an authorized remediator for the frontend catalog/gate pair if correction is desired.
4. Confirm **Platform-Core remains frozen**; A01 recommends zero restructuring.
5. Route `apps/*` S3/MySQL vendor-coupling review to the constitution owner.

---

## 7. Attestation

No source, config, test, design or root control file was modified by A01. No git state change,
migration, test run, build, server start or database connection occurred. Only the two owned
reports under `docs/parallel-program/architecture/` were written:
`ARCHITECTURE_AUDIT.md` and this `REPOSITORY_DEPENDENCY_MAP.md`.
