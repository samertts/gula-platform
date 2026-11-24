# Complete Ecosystem Asset Inventory — Team A (Independent Adversarial Audit)

- **audit_id:** A1
- **auditor_role:** Team A — independent adversarial auditor, Architecture + Full Ecosystem Asset Inventory (no file ownership in the audited change set)
- **generated_at:** 2026-11-18
- **repository:** `/home/samertts/workspace/projects/gula-integration`
- **branch / HEAD:** `integration/gula-unification-v1` / `2206654dc713ea2de8c564a3207dfe05fde23549` (`git rev-parse HEAD`)
- **sibling repository:** `/home/samertts/workspace/projects/gula-platform` — READ-ONLY, verified pinned & clean at `f478676b6fc375338648dde46fbf076c015a3f91`; not written to, not modified.
- **method:** read-only `find` / `grep -R` / `rg` / `sed` / `git ls-files` / `git status --porcelain` and Python 3.12 AST static counting. No pytest, no DB connection, no network, no source/config/index/history mutation. The only files created are the two artifacts in this directory.
- **status vocabulary used:** IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED. This auditor **awards no `INDEPENDENTLY VERIFIED` and no `PRODUCTION READY`** status to any item (Team C exclusive). All findings carry finding-status `DISCOVERED`.

---

## 0. Headline result (on-disk reality vs documentation claims)

| Check | Documentation claim | On-disk / command result | Verdict |
|---|---|---|---|
| Repository HEAD | `00_MASTER_EXECUTION_PLAN.md:7` → `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`; `status_registry.json:38` → `0cb067aef8c4276f60e2ec0e53e2a78f335c269b` | `git rev-parse HEAD` = `2206654dc713ea2de8c564a3207dfe05fde23549` | **Three different HEAD values**; drift partially self-declared "advisory by design" in `status_registry.json:39`, but doc `00` value appears nowhere else |
| Architecture compliance | `foundation-gate.yml:20-23` runs `architecture_compliance_engine.py` as a hard gate; docs report architecture/domain gates PASS | Engine run read-only (`--json`, stdout only): **`score 7.1/100`; L1 FAIL, L2 FAIL (7 cycles), L3 FAIL (112 forbidden imports), L4 FAIL (376 cross-domain), L5 FAIL, L6 FAIL, L7 WARNING** | ** contradicted**; gate returns exit 1 on any FAIL but workflow triggers only on `push` to `main` and `workflow_dispatch` — never on this integration branch |
| Shared Core catalog | `shared_core.py:17-18`: "Every entry maps to a real, existing module"; 50-service authoritative catalog | 50 keys / 50 tuple entries (lockstep OK), but `shared_core.py:90-93` maps `rule_engine → shared/rules_engine`, which **does not exist on disk** | **1 dangling provider** |
| WS-E structural guard | zero FastAPI/APIRouter under `backend/app/health_core/` | `rg 'from fastapi\|import fastapi\|APIRouter\|FastAPI\(' backend/app/health_core/` → **no matches**; route decorators → none | **HOLDS** (verified) |
| FHIR HTTP route activation | T6 interface deliberately NON-activated | `backend/app/interoperability/fhir_http/router.py:3-6` says so; `grep fhir_http backend/app/factory.py` → no match | **HOLDS** (verified) |
| Production readiness | `14_FINAL_ACCEPTANCE_REPORT.md:10,25` → `BLOCKED`, `PRODUCTION READY: 0 items` | No artifact in this audit contradicts this | **HOLDS** — this audit adds no release claim |

---

## 1. Repository-level inventory

| Category | Deterministic count | Evidence / method |
|---|---|---|
| Root directories (incl. hidden) | **57** | `find . -maxdepth 1 -type d -not -name '.' | wc -l` |
| Files on disk (excl. `.git`, `node_modules`, `__pycache__`, `*.pyc`) | **7,244** | `find … | wc -l` |
| Git-tracked files at HEAD | **6,514** | `git ls-files | wc -l` |
| Untracked files (not ignored) | **209** | `git status --porcelain | grep '^??' | wc -l` |
| Modified tracked files (` M`) | **109** | `git status --porcelain=v1 | cut -c1-2 | sort | uniq -c` |
| Staged renames (`R `) | **20** | same |
| Total pending status entries | **338** | `git status --short | wc -l` |
| Python source files (excl. caches) | **3,228** | `find . -name '*.py' … | wc -l` |
| Root Markdown docs | ~120 (top-level `*.md`) | `ls *.md | wc -l` — includes multiple overlapping certification/atlas reports |

### 1.1 Uncommitted-state / supply-chain risk (material)

| Surface | Tracked at HEAD | Untracked on disk | Note |
|---|---|---|---|
| `backend/app/health_core/**` (`.py`) | **11** | **71** | Total 82 `.py` (+82 `.pyc` bytecode) — the large majority of the WS-A…WS-F synthetic package is **not** in the commit |
| `GOVERNANCE/NATIONAL_INTEGRATION/**` | **17** | **1** | Untracked file: `15_CONSOLIDATED_EXECUTION_BACKLOG.md` |
| `backend/app/interoperability/fhir_http/**` | **7** | **0** | Fully tracked (T6) |
| `.github/workflows/frontend-pwa.yml`, `SECURITY_REMEDIATION_REPORT.md` | modified | — | Uncommitted modifications |
| `backend/app/national/workflow_runtime/**`, `backend/app/identity/workflows/{engine,models}.py`, `backend/app/platform/workflow.py` | 20 staged `R ` entries into `archive/legacy/workflow_runtime/` | — | Staged renames, uncommitted |

A fresh clone at `2206654d` does **not** reproduce the audited tree. CI at HEAD validates a materially different source set. See finding AUD-ARCH-002.

### 1.2 Case-collision note (informational, not a finding)

Both `GOVERNANCE/` (169 files: decision records, surveys, evidence) and `governance/` (26 files: Python governance/catalog/engine package) exist at root. They are distinct in content, but collide on case-insensitive filesystems (macOS/Windows — relevant to the hospital_desktop/Flutter clients). Not verified whether any tooling assumes one canonical case.

---

## 2. Backend architecture inventory

| Category | Count | Evidence |
|---|---|---|
| `backend/app/` immediate sub-packages | **67** (excluding `__pycache__`) | `find backend/app -mindepth 1 -maxdepth 1 -type d` |
| Top-level packages in independent cross-import scan | **67** | Python AST scan of `backend/app/**/*.py` |
| Cross-package import edges | **184** across **51** packages | same |
| Distinct cross-package import cycles (independent scan) | **14** | same —详见 findings AUD-ARCH-004 |
| Cycles reported by repo's own `architecture_compliance_engine.py` (L2) | **7** | `python scripts/architecture_compliance_engine.py --verbose` (read-only, stdout) |
| Forbidden imports (L3) | **112** | same |
| Cross-domain bounded-context violations (L4) | **376** | same |
| `factory.py` `include_router(...)` calls | **91** | `grep -c include_router backend/app/factory.py` |
| Shared Core catalog entries | **50** | AST parse of `shared_core.py:23` |
| `SHARED_CORE_SERVICES` tuple entries | **50** | AST parse of `core.py:44`; set-equal to catalog |
| Catalog provider paths present on disk | **49 / 50** | `os.path.exists` over all provider values; missing = `rule_engine → shared/rules_engine` |
| Canonical domains | **11** | `manifest.py:63` — `laboratory, pharmacy, radiology, hospital, blood_bank, public_health, insurance, emergency, research, citizen_portal, provider_portal` |
| Domain certification claim | 11/11 @100%, isolation PASS (docs) | `12_NATIONAL_DOMAIN_SURVEY.md`; not re-awarded by this audit |
| Migrations under `backend/migrations/versions/` | **107** | `find … -name '*.py'` (plus `env.py` → 108 total) |
| Other migration trees | 5 | `apps/gula-platform-ui-refresh/drizzle/migrations`, `apps/gula-web-suite/drizzle/migrations`, `backend/tests/migrations`, `platform/migration`, `frontend-v3/src/pages/migration` (UI page, not migration) |
| ORM tables unmigrated (doc claim) | **426** / 833 ORM tables, 40 contexts | `12_NATIONAL_DOMAIN_SURVEY.md`; `BLOCKED` (ADR-A) |

### 2.1 Top-level `backend/app/` package list (67)

`ai, ai_fabric, audit, billing, biomedical, blood_bank, capabilities, care_continuum, certification, chronic_care, citizen_platform, clinical, clinical_gateway, command_center, command_intelligence, communication, contracts, control_plane, core, critical_care, devices, document_intelligence, domain, domain_platform, edge, ehr, ems, engineering, fhir, financial, firewall, gateways, governance, health_core, health_data, hospital, identity, insurance, integration, interoperability, kernel, knowledge_graph, legal, lifecycle_platform, lims, models, national, national_data, nhdw, notifications, nursing, payments, pharmacy, pilot_platform, platform, public_health, radiology, reference, research_platform, roadmap, routes, security, services, simulation, tasks, trust, workflows` (+ `__pycache__`, excluded).

### 2.2 Health Core (WS-A…WS-F synthetic slice)

| Sub-package | `.py` files |
|---|---|
| `audit_anchor` | 5 |
| `authorization` | 6 |
| `client_integration`, `clinical`, `common`, `contracts`, `fhir`, `identity`, `integration`, `lab`, `reliability`, `terminology` | remainder of 82 total |
| **Total `.py`** | **82** (11 tracked / 71 untracked) |
| FastAPI / APIRouter under `health_core` | **0** — WS-E guard HOLDS |
| Tests for health_core | **42** files under `backend/tests/health_core/` (0 `test_*.py` inside `health_core` itself) |

`backend/app/health_core/authorization/engine.py:3` declares itself "the only authority for permissions" but is instantiated only at `backend/app/health_core/authorization/guard.py:869`; only 5 files outside `health_core` import it, all in `interoperability/fhir_http/`. The main app uses `backend/app/routes/authorization.py`, `backend/app/identity/services/authorization_service.py`, and `shared/rbac/permissions.py`. See AUD-ARCH-003.

### 2.3 FHIR HTTP (T6, Phase B)

`backend/app/interoperability/fhir_http/`: 7 tracked `.py`, 14 raw files incl. bytecode. `router.py:3-6` states it is intentionally not registered; confirmed absent from `factory.py`. 51 tests claimed (`14_FINAL_ACCEPTANCE_REPORT.md:18`) — **test execution not re-run by this auditor** (status: `TESTED` per owner docs, not re-awarded).

### 2.4 Duplicated / federated engines (multiple sources of truth candidates)

| Concern | Locations found |
|---|---|
| Identity | `backend/app/identity/`, `backend/app/health_core/identity/`, `backend/app/integration/identity/`, `backend/app/services/mpi/`, `shared/identity/` |
| Audit | `backend/app/audit/`, `backend/app/health_core/audit_anchor/`, `backend/app/health_core/reliability/audit.py`, `shared/audit/`, `backend/app/identity/models/audit.py` (cataloged) |
| Authorization | `backend/app/health_core/authorization/`, `backend/app/routes/authorization.py`, `backend/app/identity/services/authorization_service.py`, `backend/app/national/permissions/`, `shared/rbac/` |
| Events | `shared/events/` (3 `.py`), `backend/app/kernel/event_bus/` (13), `backend/app/health_data/event_store/` (3), `backend/app/national_data/models/event_store/` (4), `backend/app/national/events/`, plus 10 capability-local `backend/app/capabilities/*/events/` dirs |
| Workflow | `backend/app/workflows/`, `backend/app/identity/workflows/routes.py`, `backend/app/capabilities/workflow_engine/`, archived `archive/legacy/workflow_runtime/**` (20 staged renames) |

Presence alone is not proof of duplication; only the authorization conflict is raised as a finding (AUD-ARCH-003). Events are raised as AUD-ARCH-006 with explicit "no single backbone verified".

---

## 3. Client / application inventory

| Surface | Files (excl. `node_modules`, caches) | Notes |
|---|---|---|
| `frontend-v3/` | **389** | Arabic-first RTL; `dir="rtl"` per repo guidance (not re-verified in this audit) |
| `mobile/` | **538** | Native Android/iOS source tree |
| `mobile-expo/` | **133** | Expo client |
| `hospital_desktop/` | **27** | Desktop client |
| `apps/gula-platform-ui-refresh/`, `apps/gula-web-suite/` | **327** combined | Two additional web app trees with their own `drizzle/migrations` |
| `services/` (10 subdirs) | **67** | `ai, autonomous_manager, device_bridge, lab, notification, order, patient, result, sample, shared` |
| `platform/` | **636** | Contains `platform/migration` |
| `nhop-platform/` | **55** | Separate deployment surface |
| `client/`, `cli/`, `edge_agent/` | 14 / 9 / 10 | Thin clients / CLI / edge |
| `archive/experimental/**`, `archive/legacy/**`, `archive/scripts/` | present | Dormant / archived trees; `workflow_runtime` newly staged into `archive/legacy/` |

**Client status:** real platform integration remains `BLOCKED`/`NOT IMPLEMENTED` per `14_FINAL_ACCEPTANCE_REPORT.md:21,37`; no client build or RTL/WCAG run was executed by this auditor.

---

## 4. Governance / CI / infrastructure inventory

| Category | Count | Evidence |
|---|---|---|
| `GOVERNANCE/` files | **167 at audit start** (count grows concurrently as parallel audit teams write `ADVERSARIAL_ASSURANCE/`) | `find GOVERNANCE -type f | wc -l` — first pass; this auditor created exactly 2 files (the two deliverables in this directory) |
| `GOVERNANCE/` immediate subdirectories | **10** | `ACCELERATION, GECS, HEALTH_CORE, IDENTITY_ARCHITECTURE_STUDY, IDENTITY_REMEDIATION, NATIONAL_INTEGRATION, PHASE_B_EVIDENCE, PRODUCTION_READINESS, PROGRAM_STATUS, evidence` |
| NATIONAL_INTEGRATION docs | **18** files | `00`–`15` (16), `ADVERSARIAL_REVIEW_RECORD.md`, `status_registry.json`; 17 tracked + 1 untracked |
| CI workflows (`.github/workflows/`) | **32** | `find … -type f | sort` |
| Hard architecture gate | present but branch-scoped | `foundation-gate.yml:20-23` → engine; triggers only `main` push / `workflow_dispatch` (`:3-6`) |
| Constitution gate | present | `constitution-compliance.yml:34-36` → `constitution_enforcer.py --diff-mode --base origin/main` |
| Ephemeral baseline file | **`/tmp/constitution_baseline.json`** | `scripts/constitution_enforcer.py:88` — not tracked; environment resets wipe it (see `00` §4 toolchain note) |
| Scripts engines (dirs) | 6 functional | `contract-audit, domains, health-probes, security, self-heal, tests` |
| Script launcher `.py` at `scripts/` root | **54** | `find scripts -maxdepth 1 -name '*.py' | wc -l` |
| Dockerfiles | **15** | root, backend, docker, frontend-v3, nhop-platform, platform, 8 under `services/` |
| Compose files | **12** | `docker-compose*.yml`, `docker/docker-compose.yml`, `nhop-platform/docker-compose.yml`, `config/*/docker-compose*.yml`, `archive/docker-compose.v1.yml` |
| K8s YAML | **37** | `find k8s -type f -name '*.y*ml'` |
| Helm templates | **38**, 1 chart (`helm/gula-platform/Chart.yaml`) | `find helm …` |
| Terraform `.tf` | **57** | `find terraform -name '*.tf'`; envs `dev, dr, pilot, prod, staging` + modules |
| `config/` files (≤2 depth) | **78** | `find config -maxdepth 2 -type f` |
| Test suites | backend `test_*.py` **320** total; `backend/tests` 156 top-level + 42 health_core + 41 kernel + 23 identity + 17 unit + others; capabilities-local 20; frontend/mobile/desktop `*.test.*`/`*.spec.*` **54** | `find …` |
| `conftest.py` files | **7** | `backend/tests/conftest.py`, `backend/tests/health_core/`, `kernel/`, `kernel_hardening/`, `communication_providers/`, `backend/app/national/tests/`, `backend/app/reference/tests/` |

---

## 5. Explicit "not present / not verified" entries

| Item | Statement |
|---|---|
| Platform-repo architecture constitution engine | **NOT PRESENT** in integration repo: no `scripts/architecture/`, no `scripts/architecture.py`, no `.ai/core/architecture/constitution_baseline.json`, no `architecture-check` command in Makefile/CI. Present instead: `scripts/architecture_compliance_engine.py` (L1–L7 score engine) and `scripts/constitution_enforcer.py`. |
| `.ai/` runtime state directory | **NOT PRESENT** (`ls .ai` → no such file). |
| New architecture finding baseline | **NOT VERIFIED** — no committed baseline of acknowledged architecture findings exists in this repo; the only baseline is ephemeral `/tmp/constitution_baseline.json`. |
| Provider-path existence test | **NOT PRESENT** — `backend/tests/test_domain_platform.py:146-164` asserts catalog⇄tuple set equality only; no test calls `os.path.exists` on provider paths. Root cause of AUD-ARCH-005. |
| WS-E guard in CI / pre-commit | **NOT VERIFIED as enforced** — `scripts/phase_b_gate.py:70` contains the guard comment; `grep phase_b_gate .github Makefile` → no match. |
| `INDEPENDENTLY VERIFIED` / `PRODUCTION READY` | **NOT AWARDED** by this auditor to any artifact. Owner-gated decisions (HOLD, MPI REJECT, MP-001, ODR-001…004, D-020/D-021, ADR-A…J, AUD-02/07/16) preserved unchanged; no approval fabricated. |
| Clinical validation / external FHIR validation / licensed SNOMED CT / production DB rehearsal / real client platforms | **NOT PRESENT / BLOCKED** per `14_FINAL_ACCEPTANCE_REPORT.md` §2–§4. |
| Test execution | **NOT RE-RUN** by this auditor (read-only constraint; no pytest). All test counts are documentation claims or file counts, not independently reproduced pass counts. |
| DB state | **NOT INSPECTED** — no operational DB connection attempted. |
| Known disclosed failure | `test_nr011_metadata_discovery.py::TestMetadataDiscovery::test_cross_metadata_foreign_keys_resolve` (co-collection `NoReferencedTableError`) is pre-existing/disclosed; **not re-reported** as a new finding. |

---

## 6. Coverage matrix (Team A scope)

| Scope element | Covered | Method | Result |
|---|---|---|---|
| Root dirs / file counts | Yes | `find` | §1 |
| Git tracking state | Yes | `git status`, `git ls-files` | §1.1 — material finding |
| `backend/app` domain inventory | Yes | `find`, AST | §2.1 |
| Clean Architecture / dependency direction | Yes | AST cross-import + repo engine | §2 — findings AUD-ARCH-001, AUD-ARCH-004 |
| Circular dependencies | Yes | AST DFS + engine L2 | 14 independent / 7 engine |
| Duplicated engines (identity/auth/audit/events/workflow) | Yes | `find`, `grep` | §2.4 — findings AUD-ARCH-003, AUD-ARCH-006 |
| Shared Core 50-service catalog | Yes | AST + `os.path.exists` | 49/50 — AUD-ARCH-005 |
| 11-domain platform | Yes (data structure) | AST | 11 manifests present; isolation certification **not re-awarded** |
| Migrations | Yes (file count) | `find` | 107 versions |
| Client apps | Yes (file counts) | `find` | §3 |
| CI workflows | Yes | `find`, `cat` | §4 — AUD-ARCH-001, AUD-ARCH-009 |
| Docker / K8s / Helm / Terraform | Yes (counts) | `find` | §4 |
| Test suites | Yes (file counts) | `find` | §4; execution not re-run |
| Governance docs 00–14 | Yes (claims read + falsified where possible) | `sed`, `grep` | §0 — AUD-ARCH-008 |
| WS-E structural guard | Yes | `rg`, `grep` | **HOLDS** |
| FHIR HTTP non-activation | Yes | `grep` | **HOLDS** |
| Owner-gated decision integrity | Yes (no edits attempted) | read-only | preserved |

---

## 7. Finding index (see JSON for full schema)

| ID | Title | Severity | Likelihood | owner_gated |
|---|---|---|---|---|
| AUD-ARCH-001 | CI-wired architecture engine FAILS at 7.1/100 and does not gate the integration branch | HIGH | HIGH | false |
| AUD-ARCH-002 | Audited tree is not reproducible from HEAD — 209 untracked / 109 modified / 20 staged renames | HIGH | HIGH | true |
| AUD-ARCH-003 | Two mutually exclusive "only authority" permission engines coexist | HIGH | MEDIUM | true |
| AUD-ARCH-004 | 14 cross-package import cycles and core→outer-layer dependency inversions | MEDIUM | HIGH | true |
| AUD-ARCH-005 | Shared Core catalog `rule_engine` provider path does not exist | MEDIUM | HIGH | true |
| AUD-ARCH-006 | Five-plus event engines/stores with no verified single event backbone | MEDIUM | MEDIUM | true |
| AUD-ARCH-007 | Governance score baseline stored in ephemeral `/tmp` | MEDIUM | HIGH | false |
| AUD-ARCH-008 | Program status docs carry three different HEADs and contradictory phase status | LOW | HIGH | false |
| AUD-ARCH-009 | WS-E guard and Phase B gate are manual-only, not CI/pre-commit enforced | LOW | MEDIUM | false |

**Severity totals:** CRITICAL 0 · HIGH 3 · MEDIUM 4 · LOW 2 · INFORMATIONAL 0 = **9 findings**.

---

_End of inventory — Team A. No source, git index/history, config or database was modified. Top three material findings: AUD-ARCH-001 (`scripts/architecture_compliance_engine.py:80,1037-1051` + `.github/workflows/foundation-gate.yml:3-6,20-23`), AUD-ARCH-002 (`git status --porcelain` / `backend/app/health_core/` 71 of 82 `.py` untracked), AUD-ARCH-003 (`backend/app/health_core/authorization/engine.py:3` vs `backend/app/routes/authorization.py` and `shared_core.py:33-35`)._
