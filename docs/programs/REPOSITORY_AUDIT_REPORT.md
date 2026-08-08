# REPOSITORY AUDIT REPORT

**Program:** PROGRAM-REPO-01 v1.0 — Repository Engineering & Open Source Excellence
**Phase:** 1 / 8 — Repository Audit (ANALYSIS ONLY — no mutations, no commits)
**Date:** 2026-08-08
**Branch:** `remediate-security-001`
**Status:** DRAFT — awaiting Program Director review

---

## 1. Executive Summary

GULA Platform is a large, feature-rich, actively-engineered monorepo (6,389 tracked files,
≈1.4 GB working tree, 814 commits, 5 months of history). Engineering quality of the *application*
code is high (backend 5089 tests passing, ruff 378 baseline, tsc 0, eslint 0, architecture gate
25/25, domain 11/11). **Repository engineering quality is low** — the repository itself has not
received the same rigor as the application code. This report documents the full repository state
and the concrete engineering debt that PROGRAM-REPO-01 is designed to remediate.

**Overall Repository Health Score (preliminary, Phase 1): 48 / 100** (detailed scorecard in
Phase 7). This will be recomputed after the 10-dimension Phase 7 scoring.

---

## 2. Repository Facts (Measured)

### 2.1 Git History
| Metric | Value |
|---|---|
| Total commits | 814 |
| Merge commits | 120 (14.7%) |
| First commit | `3eeb9155` — 2026-03-08 (`Initial NHOP platform commit`) |
| Active period | 2026-03-08 → 2026-08-08 (5 months) |
| Commit message hygiene (last 500) | Conventional Commits dominant (`feat`, `fix`, `docs`, `refactor`, `chore`); some mixed conventions |
| `.git` size | 144 MB (pack 68.73 MiB, 1224 objects index, **5 garbage temp packs found**) |
| Branch count | 125 (62 local + 63 remote-tracking) |
| Tags | 38 (mostly non-semver feature tags, 2 RC tags, 1 `v2.1.0-*`) |
| Remotes | 1 (origin: `ssh://git@ssh.github.com:443/samertts/gula-platform.git`) |

### 2.2 Working Tree
| Metric | Value |
|---|---|
| Tracked files | 6,389 |
| Largest top-level dirs | backend 648 MB, frontend-v3 314 MB, docs 9.8 MB, scripts 5.8 MB, mobile 3.8 MB, shared 2.6 MB |
| `.py` files | 3,139 |
| `.md` files | 1,192 total — **156 at repo root** |
| `.tsx` / `.ts` | 505 / 278 |
| Mobile | 155 `.kt`, 150 `.dart`, 118 `.swift` |
| Infra | 57 `.tf`, 43 k8s, 38 helm, 26 workflows |
| `.env` tracked | **0** (good — secrets policy respected) |
| Temp/artifact files tracked | **0** (good) |

### 2.3 Root-Level Clutter (Highest Severity Finding)
**156 Markdown files at the repository root.** This is the single most damaging structural issue
for a would-be open-source project. A new contributor (or a GitHub code reviewer) is confronted
with ~156 report/design/certification documents before reaching `README.md`. Categories:

- Live program docs (PROGRAM-01*, PROGRAM_01*, WAVE*, COMMIT_*)
- Engine reports (ARCHITECT_*, BUILDER_*, REVIEWER_*, OPTIMIZER_*, LEARNER_*, DEPLOYER_*, KERNEL_*)
- Certification / audit docs (CERTIFICATION*, *CERTIFICATION.md, *_AUDIT_REPORT.md)
- Master architecture docs (MASTER_*, ARCHITECTURE_*, SHARED_CORE_*, DOMAIN_*, WORKSPACE_*)
- Design docs (ABAC_DESIGN.md, BREAK_GLASS_POLICY.md, BUSINESS_PLAN.md, etc.)
- 7 `DOMAIN_*.md`, 10+ `PROGRAM*`, 6 `IDENTITY*`/`CITIZEN*`/`WORKSPACE*` reports
- MISSION_STATUS.md, CHANGELOG.md, VERSION, ROLE_PERMISSION_MATRIX.csv, etc.

### 2.4 Documentation Duplication
Name-only duplicates between root and subdirectories (a subset):
- `CHANGELOG.md` — duplicated 8+ times (root, docs/, contracts/, security/, packages/uap/, platform/reports/, backend/app/governance/, etc.)
- `ARCHITECTURE.md` — duplicated 12+ times
- `PERFORMANCE_REPORT.md` — duplicated 8+ times (platform/reports/pi-003..006)
- `README.md` — duplicated **125 times** (many legit per-module, but `assessment/*`, `platform/reports/*`, `docs/freeze/*`, `identity_report/*` are stale duplicates)
- `PERMISSION_CATALOG.md` / `ROLE_CATALOG.md` / `TENANT_MODEL.md` / `IDENTITY_ARCHITECTURE.md` — root + `identity_report/`
- `TECHNICAL_DEBT_REGISTER.md` — root + `docs/engineering/`
- `WORKSPACE_ARCHITECTURE.md` — root + `docs/certification/`
- `SECURITY.md` — root + 3 subdirs (national, packages/uap, security/)
- `final_report.md` — root + `reports/`

### 2.5 Git Housekeeping
- **125 branches**; 60+ are stale `claude/*` (3–5 months old) and `codex/*`/`fix/*` working branches. Only 2 remote branches are merged into `main`. No branch cleanup policy.
- **5 garbage temp packs** in `.git/objects/pack/` (`tmp_pack_*`) — repo needs `git gc` / `git prune`.
- **120 merge commits** (14.7%) — no consistent merge strategy; AGENTS.md already mandates rebase-over-merge.
- **38 tags**, mostly feature-tags (`national-*-v1.0`, `platform-*-v1.0`, `-RC1/RC2`) rather than a clean semver release stream. `VERSION` file says `1.0.0-RC2`; root `package.json` says `1.0.0` — **version drift across the repo.**

### 2.6 CI/CD
- **26 workflows** in `.github/workflows/` (4,388 lines total) + 6 composite actions + 4 shell scripts.
- Overlapping responsibilities and likely redundancy: `blue-green-deploy`/`canary-deploy`/`auto-rollback`/`rollback`/`deploy`/`preview-deploy`/`release` (7 deployment-related), `quality-gate`/`ci`/`constitution-compliance`/`foundation-gate`/`ai-governance(-enforcement)` (5 quality gates), `mobile-android`/`mobile-ios`/`mobile-flutter-desktop` (3 mobile).
- Naming is inconsistent: `ci.yml` (generic) vs `quality-gate.yml` vs `foundation-gate.yml`; no per-area naming convention.
- 2 Dependabot/security monitors (`dependency-review`, `secret-scanning`) + CodeQL + scorecard — good.
- No single "repo hygiene" gate (e.g. root-file-count limit, markdown link checker).

### 2.7 Dormant / Legacy Directories
Multiple top-level legacy or superseded trees (Program Director must confirm disposition):
- `frontend-v2/` (163 files) — superseded by `frontend-v3/` (168 files). Contains `dist/`, `count_braces.js`, `find_duplicates.js`, `fix_ku.js` (one-off scripts).
- `nhop-platform/` (55 files) — superseded by `backend/` + `national/` architecture.
- `platform/` (616 files) — appears to be an older app platform (`platform/apps/laboratory`, `platform/reports/pi-*`).
- `packages/uap/` (52 files), `contracts/` (121 files), `assessment/` (47 files), `archive/` (208 files — by design, ADR-028), `identity_report/`, `security-audit/`, `services/`, `supabase/`, `digitalocean/`, `edge_agent/`.

### 2.8 Large Tracked Files
- `security-audit/bandit.json` 3.9 MB, `assessment/brain/knowledge_graph.json` 2.6 MB, `security-audit/sbom.json` 2.0 MB, `security-audit/semgrep.json` 1.0 MB, `security-audit/trivy.json` + `grype.json` 0.6 MB each.
- Generated tooling artifacts (bandit/semgrep/trivy/grype JSON reports, knowledge graph dumps) are **tracked in git** — these belong in CI artifacts or git-ignored local state, not in the repo history. Recurring binary bloat on every scan.

### 2.9 Governance Files (Good News)
All standard OSS governance files exist at root: `SECURITY.md`, `CONTRIBUTING.md`, `SUPPORT.md`, `GOVERNANCE.md`, `CODE_OF_CONDUCT.md`, `LICENSE`, `NOTICE`, `CITATION.cff`, `CHANGELOG.md`, `CODEOWNERS`, `PULL_REQUEST_TEMPLATE.md`, 4 issue templates, `dependabot.yml`, `.gitattributes`, `.pre-commit-config.yaml`, `.secrets.baseline` (gitleaks).

### 2.10 Release / Versioning
- `VERSION` = `1.0.0-RC2`; root `package.json` = `1.0.0`; tag stream is feature-based not release-based.
- No automated version sync; `release.yml` exists but tags do not follow the release workflow conventions.

---

## 3. Findings Register

| ID | Severity | Area | Finding |
|---|---|---|---|
| R-01 | CRITICAL | Structure | 156 root-level `.md` files clutter the repo; new-contributor and review friction |
| R-02 | CRITICAL | Git | 125 branches, 60+ stale `claude/*` 3–5 months old, no cleanup policy |
| R-03 | HIGH | Git | 5 garbage tmp packs in `.git`; needs `git gc` |
| R-04 | HIGH | Docs | Widespread name-duplicate docs (CHANGELOG ×8, ARCHITECTURE ×12, PERFORMANCE_REPORT ×8) |
| R-05 | HIGH | Legacy | Superseded trees unremoved: `frontend-v2`, `nhop-platform`, `platform/`, `packages/uap`, `identity_report` |
| R-06 | HIGH | Versioning | Version drift: `VERSION`=RC2 vs `package.json`=1.0.0 vs feature tags; no release stream |
| R-07 | MEDIUM | CI | 26 workflows with overlapping concerns (7 deploy, 5 quality gates); naming inconsistent |
| R-08 | MEDIUM | Size | Generated audit artifacts (bandit/sbom/semgrep/trivy/grype JSON, knowledge graph) tracked in git |
| R-09 | MEDIUM | Git | 120 merge commits vs AGENTS.md rebase policy |
| R-10 | MEDIUM | Docs | 38 non-semver tags; tag semantics undocumented |
| R-11 | LOW | Docs | One-off root scripts (`gula_autofix.sh`, `gula_health.sh`, `count_braces.js`, `find_duplicates.js`, `fix_ku.js`) |
| R-12 | LOW | CI | No repo-hygiene gate in CI (root-file count, broken-link check, git hygiene) |

---

## 4. What Is Healthy (Do Not Touch)

- Secrets policy: zero tracked `.env`, `.secrets.baseline` gitleaks gate active.
- Zero tracked temp/artifact extensions (`.tmp`, `.pyc`, `.log`, `.bak`) in `git ls-files`.
- Standard OSS governance surface present and complete.
- Application quality gates strong: ruff 378 baseline, tsc 0, eslint 0, 5089 backend tests, architecture gate 25/25, domain 11/11.
- `.dockerignore`, `.gitattributes`, `.editorconfig`, `.pre-commit-config.yaml` all present.
- `archive/` pattern (ADR-028) already provides the safe "move before delete" precedent that will be reused.

---

## 5. Risks (if no action taken)

- Open-sourcing the repo in current state: 156 root docs, 125 branches, non-semver tags → poor first impression, low contributor trust, potential "abandoned project" signal.
- `.git` bloat (tmp packs, large generated JSON in history) grows unbounded; future clones slow.
- Legacy trees (`frontend-v2`, `nhop-platform`, `platform/`) confuse contributors and duplicate attack surface in security scanning.
- Version drift breaks tooling assumptions and release traceability.

---

## 6. Recommended Immediate Next Steps (Phase 2 preview — NO action yet)

1. Phase 2: Repository structure proposal — target layout, migration map, rollback design.
2. Phase 3: Git strategy — branch cleanup plan, gc, tag re-flow, commit hygiene.
3. Phase 4: GitHub governance — repo settings, branch protection, issue/PR conventions, OSS release readiness.
4. Phase 5: Documentation audit — dedup/consolidation map for root `.md` files.
5. Phase 6: DX report — contribution onboarding, local dev flow, tooling.
6. Phase 7: Health score — 10-dimension scorecard (this Phase 1 score of 48/100 to be refined).
7. Phase 8: Execution plan — 4 waves with effort/risk/rollback/benefit.

All Phase 2–8 work remains ANALYSIS ONLY until the Program Director approves execution.
