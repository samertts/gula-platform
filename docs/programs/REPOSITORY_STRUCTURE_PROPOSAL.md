# REPOSITORY STRUCTURE PROPOSAL

**Program:** PROGRAM-REPO-01 v1.0 — Repository Engineering & Open Source Excellence
**Phase:** 2 / 8 — Repository Structure Proposal (ANALYSIS ONLY — no mutations, no commits)
**Date:** 2026-08-08
**Status:** DRAFT — awaiting Program Director approval before execution

---

## 1. Objective

Define a clean, contributor-friendly, standard monorepo layout that:
1. Removes the 156 root-level `.md` files from the root surface.
2. Isolates legacy/dormant trees so active code is unambiguous.
3. Preserves the ADR-028 "move before delete, single `git revert` reversible" precedent.
4. Causes **zero** change to application behavior, routes, APIs, or business logic.
5. Remains independently reversible per migration commit.

## 2. Current State (from Phase 1 Audit)

- 6,389 tracked files; 156 `.md` at root; ~9 top-level legacy trees with no active-code importers.
- No build/deploy/compose references to `frontend-v2`, `nhop-platform`, `platform/apps`.
- 3 scripts reference legacy paths as scan roots (`scripts/dependency_guardian.py`, `scripts/repository_scorecard.py`, `scripts/project_brain.py`) — these become migration dependencies.
- `archive/` (208 files) already established as the ADR-028 destination.

## 3. Proposed Target Layout

### 3.1 Canonical top-level (goal state)
```
/                       # root = README.md, LICENSE, governance, AGENTS.md, CI
├── backend/            # FastAPI national platform (active)
├── frontend/           # single active frontend (promoted from frontend-v3)
├── mobile/             # Kotlin/Dart/Swift clients (active)
├── shared/             # canonical shared kernel (active)
├── security/           # security modules (active)
├── services/           # microservices / device_bridge (active)
├── scripts/            # governance engines + tooling (active)
├── contracts/          # integration contracts / SDKs (active)
├── config/             # runtime configs (active)
├── infra/              # terraform + k8s + helm + docker compose (moved from root/config)
├── docs/               # ALL documentation (moved from root)
├── .ai/                # AI governance state (unchanged)
└── archive/            # ADR-028 legacy (moved-to destination)
```

### 3.2 Root surface after migration (goal state — ≤ 25 files)
```
README.md  LICENSE  NOTICE  SECURITY.md  CONTRIBUTING.md  SUPPORT.md  GOVERNANCE.md
CODE_OF_CONDUCT.md  CITATION.cff  CHANGELOG.md  AGENTS.md  CLAUDE.md
VERSION  Makefile  .gitignore  .gitattributes  .editorconfig  .env.example
.pre-commit-config.yaml  .secrets.baseline  package.json  pyproject.toml
docker-compose.yml  docker-compose.full.yml  docker-compose.scale.yml  nginx.conf
```
All other current root files migrate per the maps below.

## 4. Migration Maps

### 4.1 Root Markdown → `docs/`
| Current root file(s) | Target |
|---|---|
| `MASTER_*.md`, `SHARED_CORE_*.md`, `DOMAIN_*.md`, `WORKSPACE_ARCHITECTURE.md`, `DIGITAL_TRUST_PLATFORM.md`, `ARCHITECTURE*.md` | `docs/architecture/` |
| `PROGRAM*.md`, `PROGRAM_*.md`, `COMMIT_*`, `WAVE_*` | `docs/programs/` (new) |
| `*_AUDIT_REPORT.md`, `*_IMPLEMENTATION_REPORT.md`, `MISSION_STATUS.md` | `docs/reports/` |
| `*_CERTIFICATION.md`, `CERTIFICATION*.md` | `docs/certification/` |
| `IDENTITY*`, `CITIZEN*`, `WORKSPACE*`, `PERMISSION*`, `ROLE*`, `TENANT_*`, `ABAC_*`, `BREAK_GLASS_*` | `docs/niam/` |
| `PRODUCTION_*`, `DISASTER_*`, `DEPLOYMENT*`, `*_PLATFORM.md` (release reports) | `docs/production/` |
| `*_REPORT.md` (one-off) | `docs/reports/` |
| `BATCH*`, `ACCESSIBILITY_*`, `API_CONTRACT_REPORT.md`, `COMPATIBILITY_REPORT.md` | `docs/audit/` |
| `TECHNICAL_DEBT_REGISTER.md` | merge into `docs/engineering/TECHNICAL_DEBT_REGISTER.md` (dedup) |
| `CHANGELOG.md` | keep at root (standard OSS) |

**Estimate:** 156 root `.md` → ~115 relocated, ~25 archived (superseded duplicates), ~16 kept at root.

### 4.2 Legacy trees → `archive/` (ADR-028 move, keep git history)
| Current | Target | Rationale |
|---|---|---|
| `frontend-v2/` (163 files) | `archive/frontend-v2/` | superseded by frontend-v3 |
| `nhop-platform/` (55 files) | `archive/nhop-platform/` | superseded by backend national architecture |
| `platform/` (616 files) | `archive/platform-apps/` | old app platform; no active consumers |
| `packages/uap/` (52 files) | `archive/packages-uap/` | dormant SDK |
| `identity_report/` (8 files) | merge into `docs/niam/` or archive | root-only docs |
| `security-audit/` (31 files incl. 8 MB JSON) | `docs/security-audit/` (text) + **remove generated JSON from git** | generated artifacts |
| `supabase/`, `digitalocean/`, `edge_agent/` (small) | `archive/` | experimental/superseded |
| `assessment/` (47 files) | `archive/assessment/` | superseded by live governance engines |

**Estimate:** ~1,080 files relocated to `archive/` (reversible per commit).

### 4.3 De-duplication targets
- `CHANGELOG.md` → single root + per-module only where genuinely maintained (keep `backend/app/governance/CHANGELOG.md` if live, else remove). Verify liveness before removal (ADR-028 evidence-based).
- `PERFORMANCE_REPORT.md` ×8, `ARCHITECTURE.md` ×12 → keep active canonical one in `docs/`, consolidate/archive the rest.
- `final_report.md` → consolidate into `docs/reports/`.

### 4.4 Tooling alignment (execution dependency)
- `scripts/dependency_guardian.py`: `nhop-platform/requirements.txt` path → `archive/nhop-platform/...`
- `scripts/repository_scorecard.py`: module_dirs list → drop `frontend-v2`, `nhop-platform` (or point to archive)
- `scripts/project_brain.py`: National scan root → `archive/nhop-platform/` + `docs/national/`
- Update `AGENTS.md` Relevant Files section to canonical paths.

## 5. Compatibility & Impact Analysis

| Concern | Assessment |
|---|---|
| Application behavior | **Zero change** — no runtime code touched; pure file moves |
| API/routes/OpenAPI | **Zero change** (nothing under backend/app moved) |
| Build/deploy | **Zero change** — no Dockerfile/compose references the moved trees (verified Phase 1 §2.7) |
| CI | **Zero change** — no workflow references legacy dirs; `docs/` and root `.github/` unchanged |
| Git history | **Preserved** — `git mv` retains history per file |
| Architecture gate | **Zero impact** — scan roots (`backend/app` + `shared`) untouched |
| Frontend | `frontend-v3` → `frontend/` rename is the ONLY risky move (import paths). **Option:** keep as `frontend-v3` in Wave 1, propose rename as separate optional wave (see §7) |

## 6. Rollback Procedure

Per commit: `git revert <commit>` restores all `git mv` relocations in one operation (ADR-028 requirement). Because all moves are pure relocations with no content edits, reverts are clean. De-duplication commits include an archive copy of the removed file before deletion (move→verify→delete chain, ADR-028 §5).

## 7. Waves Preview (full detail in Phase 8)

| Wave | Scope | Risk | Rollback |
|---|---|---|---|
| Wave 1 | Root `.md` → `docs/**` + root surface cleanup | LOW | single revert per commit |
| Wave 2 | Legacy trees → `archive/**` (frontend-v2, nhop-platform, platform, packages/uap, assessment, supabase, digitalocean, edge_agent) | LOW | single revert per commit |
| Wave 3 | Doc de-duplication + security-audit JSON removal from git (with `.gitignore`) | MEDIUM | archive-first; revert |
| Wave 4 | (Optional) `frontend-v3` → `frontend/` rename + tooling alignment | MEDIUM | revert; import rewrite scoped |

Wave 4 rename is explicitly **optional** — flag for Program Director decision; all other waves are safe by default.

## 8. Success Criteria

- Root file count (non-hidden) ≤ 25.
- All legacy trees relocated under `archive/` with zero importers outside archive (verified by script).
- `git log` shows only pure-move commits; `git revert HEAD~N` restores clean tree.
- Full verification cycle after each commit: architecture gate PASS, boot, OpenAPI byte-identical, ruff/tsc/eslint unchanged, full backend test suite PASS.
