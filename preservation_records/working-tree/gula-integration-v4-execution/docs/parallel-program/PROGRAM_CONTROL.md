# PROGRAM CONTROL — PROGRAM-GULA-PARALLEL-001

**Program:** GULA Parallel Engineering & Comprehensive Remediation Program
**Platform:** National Healthcare Platform | Iraq
**Role:** Principal Engineering Orchestrator (OpenCode orchestrator session)
**Status:** WAVE A + WAVE B COMPLETE — WAVE C BLOCKED (NOT AUTHORIZED)
**Control records created:** 2026-11-19

---

## 1. Purpose

This file is the single source of truth for program state. It records the repository
state *before* any agent work, the isolation decision, wave authorization, and gate
results. No agent may modify this file — only the orchestrator.

---

## 2. PHASE 0 — Repository Safety Snapshot (READ-ONLY VERIFIED)

All data below was captured with read-only git/filesystem commands. No state-changing
git operation was executed. No user work was touched, moved, deleted, or rewritten.

### 2.1 Repository identity

| Field | Value |
|---|---|
| Working directory | `/home/samertts/workspace/projects/gula-integration` |
| Git repository | yes |
| Current branch | `integration/gula-unification-v1` |
| HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` |
| HEAD date | 2026-11-18 22:09:47 +0300 |
| HEAD subject | `feat(national-integration): add Phase B synthetic engineering evidence tranche` |
| Upstream | `origin/main` |
| Divergence vs upstream | **ahead 2 / behind 0** |
| Merge-base with upstream | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` (VALID merge-base exists) |
| Remote `origin` (fetch) | `ssh://git@ssh.github.com:443/samertts/gula-platform.git` |
| Remote `origin` (push) | `ssh://git@ssh.github.com:443/samertts/gula-platform.git` |

**Finding PC-0001 (resolved historical concern):** The program brief warned of two
unrelated Git histories with no valid merge-base. **Re-verification shows a valid
merge-base exists** and the current branch is a clean fast-forward-able +2 commits
ahead of `origin/main`. No divergent-history merge is required or authorized.

The 2 local-only commits are:
- `0cb067ae` — `governance(national-integration): establish Phase A evidence baseline and registry gate`
- `2206654d` — `feat(national-integration): add Phase B synthetic engineering evidence tranche`

### 2.2 Working tree state (USER WORK — PROTECTED)

| Category | Count | Notes |
|---|---|---|
| Modified (unstaged, `M`) | 126 | backend, frontend-v3, governance docs, workflows |
| Staged renames (`R`) | 20 | `backend/app/.../workflow_runtime/**` → `archive/legacy/workflow_runtime/**` (R100) |
| Untracked files (`??`) | 232 | includes large untracked code trees (health_core, communication, domain_platform, GLOSI, GOVERNANCE) |
| Untracked directories | 17 top-level | GLOSI/, GOVERNANCE/ACCELERATION/, GOVERNANCE/ADVERSARIAL_ASSURANCE/, GOVERNANCE/GECS/, GOVERNANCE/HEALTH_CORE/, GOVERNANCE/IDENTITY_ARCHITECTURE_STUDY/, GOVERNANCE/IDENTITY_REMEDIATION/, GOVERNANCE/PRODUCTION_READINESS/, GOVERNANCE/PROGRAM_STATUS/, docs/goc/, etc. |

**PROTECTION DIRECTIVE:** Every path listed above is **user-owned / pre-existing work**.
No agent may modify, stage, unstage, move, rename, or delete any of them. This includes
(not exhaustively):

- `.github/dependabot.yml`, `.github/workflows/frontend-pwa.yml`,
  `.github/workflows/security-hardening.yml`
- `GOVERNANCE/NATIONAL_INTEGRATION/13_*`, `14_*`, `status_registry.json`
- `SECURITY_REMEDIATION_REPORT.md`
- The 20 staged renames into `archive/legacy/`
- All of `backend/app/health_core/**`, `backend/app/domain_platform/**`,
  `backend/app/communication/**`, `shared/communication/**`, `GLOSI/**`,
  `GOVERNANCE/**` (untracked trees)
- `frontend-v3/package.json`, `frontend-v3/package-lock.json`,
  `frontend-v3/vite.config.ts`, `frontend-v3/src/api/endpoints.ts`,
  `frontend-v3/src/components/navigation/MobileBottomNav.test.tsx`
- `backend/migrations/versions/20261114_*`, `20261118_*`, `20261119_*` (untracked migrations)
- `.gula-lite-permission-test.txt`

### 2.3 Existing worktrees (PRESERVED — none created/removed by this program)

| Path | HEAD | Branch | State |
|---|---|---|---|
| `/home/samertts/workspace/projects/gula-platform` | `f478676b` | `remediate-security-001` | active |
| `/home/samertts/workspace/projects/gula-demo-preview` | `f6772ee6` | `feature/demo-preview-access` | active |
| `/home/samertts/workspace/projects/gula-integration` | `2206654d` | `integration/gula-unification-v1` | **current session** |
| `/home/samertts/workspace/projects/gula-showcase-security` | `60988833` | `feature/showcase-security-control` | active |
| `/home/samertts/workspace/projects/gula-wave-b` | `77a964d0` | `wave-b/B1-abac-route-enforcement` | active |
| `/tmp/opencode/wt-pre20` | `961e1ca6` | detached | **prunable** (gitdir points to missing location) — left untouched |

### 2.4 Branches (PRESERVED)

**Local (12):** `codex/fix-the-issue`, `codex/fix-unhealthy-gula-backend-container`,
`codex/fix-unhealthy-gula-backend-container-zjakxk`, `feature/demo-preview-access`*,
`feature/showcase-security-control`*, `fix/pin-pytest-asyncio-below-1x`,
`integration/gula-unification-v1`*, `main`, `remediate-security-001`*,
`security-audit-report-2026-07`, `wave-b/B1-abac-route-enforcement`*
(`*` = checked out in another worktree)

**Remote (4):** `origin/feature/demo-preview-access`,
`origin/fix/typescript-source-mode-20260812`, `origin/main`,
`origin/wave-b/B1-abac-route-enforcement`

### 2.5 Stashes (PRESERVED)

- `stash@{0}` — `On remediate-security-001: unstaged`
- `stash@{1}` — `WIP on remediate-security-001: 66ea075d feat(routes): register 4 FHIR sub-pages ...`

No stash was created, popped, dropped, or applied.

### 2.6 Git history safety — re-verification of historical migration claims

The brief cited historical figures (57 local / 101 remote / 50 shared / 7 local-only /
51 remote-only). These are **STALE**. Re-verified from git object store (no network):

| Metric | Historical claim | Verified actual |
|---|---|---|
| Migrations in local tracked tree (`HEAD`) | 57 | **101** |
| Migrations in `origin/main` tree | 101 | **101** |
| Migrations at merge-base | 50 shared (claimed) | **101** |
| Committed local-only migrations | 7 | **0** |
| Committed remote-only migrations | 51 | **0** |
| `.py` files on disk in `backend/migrations/versions/` | — | **109** (101 tracked + 8 untracked new migrations) |

**Finding PC-0002:** There is **no committed migration divergence**. The disk delta
(109 vs 101) is entirely untracked, user-owned migration files:
`20261114_0001..0006_unify_*`, `20261118_0001_oauth2_account_kind.py`,
`20261119_0001_niam_step_up_events.py`. These are protected user work. No migration
merge, cherry-pick, rebase, or DB execution is authorized.

---

## 3. PHASE 0 — Isolation Decision

**Parallelism capability:** The environment provides a `subagent` tool capable of
running multiple independent agent sessions concurrently (background execution with
session IDs). This is **genuine parallel agent execution**, not sequential cosplay.

**Filesystem isolation:** Full git-worktree isolation for remediation is **NOT authorized
at this time**, for three reasons:
1. The working tree contains 378 changed paths of user work; copying/cloning it into new
   worktrees risks duplicating or losing unsaved work.
2. Five worktrees already exist with their own branches; two stashes exist; one worktree
   is already prunable. Adding worktrees increases repository fragility.
3. The program forbids running git operations that could affect unsaved work.

**Decision:**
- **Wave A (audit):** RUN IN PARALLEL. Each of the 9 agents is read-only on source and
  writes only to its own disjoint set of report files under `docs/parallel-program/`.
  No two agents share a write path. This is safe without filesystem worktrees.
- **Wave C (remediation):** HELD until (a) the master remediation register is approved,
  (b) a file-ownership matrix is confirmed, and (c) each candidate file is verified to
  be free of user modifications. Remediation will proceed only on disjoint, unmodified,
  agent-owned files. No protected path from §2.2 may be touched.
- If a safe remediation path cannot be established, the program will report it as
  **BLOCKED** rather than fabricate parallel edits.

**Honesty statement:** Wave A uses real concurrent subagents. It does **not** use
filesystem-level git worktree isolation. Any later single-threaded remediation will be
explicitly labeled as sequential — no false claim of parallelism.

---

## 4. Repository Map (High Level)

51 top-level directories. Primary engineering surfaces identified:

| Surface | Path | Role |
|---|---|---|
| Backend monolith | `backend/app/` | FastAPI production monolith (source of truth) |
| Migrations | `backend/migrations/versions/` | Alembic (immutable once merged) |
| Frontend v3 | `frontend-v3/` | Primary React SPA (program's sole FE reference) |
| Shared libs | `shared/` | Cross-service Python libraries |
| Services | `services/` | Future microservices (not primary deployment) |
| CI/CD | `.github/workflows/` (30 workflows) | Pipelines |
| Governance | `GOVERNANCE/`, `docs/constitution/`, `docs/architecture/` | Policy & evidence |
| Other | `platform/`, `nhop-platform/`, `ai/`, `mobile*/`, `client/`, `edge_agent/`, `k8s/`, `terraform/`, `docker/`, `cloudflare/`, etc. | Supporting/parallel systems |

---

## 5. Discovered Technical Gates (from package manifests — not assumed)

**Root `package.json`:** `dev`, `build`, `build:frontend`, `start`, `dev:frontend`,
`test` (delegates to frontend-v3), `test:coverage`, `test:watch`, `lint`, `format`,
`type-check`, `type-check:frontend`.

**`frontend-v3/package.json` (all Phase 4 named commands EXIST here):**
`dev`, `build`, `check:bundle`, `preview`, `lint`, `typecheck`, `test`,
`verify:unification`, `verify:contracts`, `verify:integration-boundary`,
`generate:data-source-inventory`, `verify:data-sources`, `generate:route-gate`,
`verify:audit-artifacts`, `check` (aggregate), `test:watch`, `test:e2e`.

**Backend:** orchestrated via root `Makefile` (`make ci` = syntax-gate + lint + docker
build; `make test` = pytest; `make health-deep`, `make migration-check` equivalent, etc.).

Gates will be run in Wave D from the appropriate package directory. Results recorded in
`INTEGRATION_LOG.md`. No command will be assumed present in a project where it is not.

---

## 6. Wave Authorization State

| Wave | Status | Authorization |
|---|---|---|
| Phase 0 — Safety | **COMPLETE** | Verified read-only |
| Phase 1 — Orchestrator | **COMPLETE** | This document + 6 control files |
| Wave A — Parallel Discovery | **COMPLETE** | 9 disjoint read-only agents; all reports landed (24 files) |
| Wave B — Consolidation | **COMPLETE** | `MASTER_REMEDIATION_REGISTER.md`: 175 unique findings (P0:8/P1:47/P2:78/P3:42) |
| Wave C — Safe Remediation | **BLOCKED — NOT AUTHORIZED** | 8 open P0s + insufficient isolation + no USER release + no SEC/CLIN/DB-API/ARCH approvals + no gate baseline |
| Wave D — Integration & Verification | PENDING | Requires Wave C |
| Phase 6 — Final Report | PENDING | Requires Wave D |

**Wave B closure (2026-11-19):** All 9 Wave A audits complete; every P0 independently
re-verified read-only; 2 confirmed duplicate pairs deduplicated (177→175). Register state:
Discovered 175 / Fixed 0 / Verified 0. Verification of program footprint: exactly 28 new
untracked files under `docs/parallel-program/`; **zero** source/config/migration files
modified; **zero** state-changing git operations. Wave C does not start — see
`MASTER_REMEDIATION_REGISTER.md §11` for the six exact blockers.

---

## 7. Prohibitions Reaffirmed

No merge, cherry-pick, rebase, force-push, reset, clean, forced checkout, stash pop,
history rewrite, branch/stash/worktree deletion, direct `main` modification, migration
execution against real DB, production deploy, paid dependency, or clinical/security
behavior change without independent approval. P0 findings halt the related work immediately.
