# PROGRAM-REPO-01 EXECUTION PLAN

**Program:** PROGRAM-REPO-01 v1.0 — Repository Engineering & Open Source Excellence
**Phase:** 8 / 8 — Execution Plan (ANALYSIS ONLY — execution requires Program Director approval)
**Date:** 2026-08-08
**Status:** DRAFT — FOR APPROVAL. No repository mutation has been performed in this program.

---

## 0. Program Constraint

Per the Program Director: **no application architecture changes, no business logic changes, no new
platform features, no repository mutations** during analysis. This plan defines what execution
WOULD do — it is submitted for approval and is not yet authorized.

Governance alignment: all execution commits follow ADR-028 (move before delete, single `git revert`
reversible, evidence-based deletion, behavior preservation) and AGENTS.md (atomic commits,
Conventional Commits, verification cycle per commit, one commit at a time with STOP for approval).

## 1. Wave Plan (4 waves)

### Wave 1 — Root & Documentation Consolidation (LOW risk)
| Task | Detail | Est. commits |
|---|---|---|
| 1.1 | Move root `.md` (~115 files) → `docs/{architecture,programs,reports,certification,niam,production,audit}/` via `git mv` (Phase 2 map) | 2–3 |
| 1.2 | Archive superseded root duplicates (~25 files, evidence-based per DOCUMENTATION_AUDIT §3) | 1 |
| 1.3 | Create `docs/README.md` index + fix `SUPPORT.md` broken link + restructure root `README.md` quick-start | 1 |
| 1.4 | Move root one-off scripts (`gula_*.sh`) → `scripts/dev/`; `PERMISSION_MATRIX.csv`, `ROLE_PERMISSION_MATRIX.csv` → `docs/niam/`; `openapi.json` → `docs/api/`; root infra files → `infra/` or `config/` | 1–2 |
| **Verification per commit** | architecture gate PASS, boot, OpenAPI byte-identical, ruff/tsc/eslint unchanged, full backend suite PASS | — |
| **Rollback** | single `git revert` per commit | — |

**Wave 1 exit criteria:** root non-hidden file count ≤ 25; zero broken links; docs index live.

### Wave 2 — Legacy Isolation & Git Housekeeping (LOW risk)
| Task | Detail | Est. commits |
|---|---|---|
| 2.1 | `git mv` legacy trees → `archive/`: `frontend-v2`, `nhop-platform`, `platform`, `packages/uap`, `assessment`, `supabase`, `digitalocean`, `edge_agent`, `identity_report` (Phase 2 §4.2) | 3–4 |
| 2.2 | Tooling alignment: `scripts/dependency_guardian.py`, `scripts/repository_scorecard.py`, `scripts/project_brain.py` path updates (Phase 2 §4.4); re-run engines to verify green | 1 |
| 2.3 | Git gc + prune (`git gc --prune=now`, `git prune-packed`); `git fsck --full` before/after | 1 |
| 2.4 | Branch cleanup: archive ambiguous branches as `refs/archive/branches/*`, delete merged/stale (GIT_STRATEGY §3), delete remote stale with per-branch verification | 1–2 |
| **Verification** | full validation cycle + architecture gate; `git fsck` clean; branch count ≤ 5 active | — |
| **Rollback** | `git revert` for moves; archive-refs recreate any deleted branch | — |

**Wave 2 exit criteria:** all legacy trees under `archive/`, zero importers outside archive, branch
count ≤ 5, `.git` pack ≤ ~70 MiB, no garbage packs.

### Wave 3 — Documentation De-duplication & CI Governance (MEDIUM risk)
| Task | Detail | Est. commits |
|---|---|---|
| 3.1 | Dedup doc families: `CHANGELOG.md`, `ARCHITECTURE.md`, `PERFORMANCE_REPORT.md`, `SECURITY.md`, `TECHNICAL_DEBT_REGISTER.md`, `final_report.md` — keep canonical, archive superseded (evidence per file) | 2–3 |
| 3.2 | `docs/` subdir consolidation (~90 → ~25) per DOCUMENTATION_AUDIT §4 | 1–2 |
| 3.3 | CI consolidation 26 → 12 workflows (GITHUB_GOVERNANCE §3); add `repo-hygiene.yml` (root-file, branch/tag count, git gc, broken-link gates) | 2–3 |
| 3.4 | Remove generated audit JSON from git (`security-audit/*.json`, `assessment/brain/*.json`) → gitignore + CI artifact (R-08) | 1 |
| **Verification** | full suite + all 12 workflows green; hygiene gate passes | — |
| **Rollback** | per-workflow revert; JSON restore from git history | — |

**Wave 3 exit criteria:** ≤ 12 workflows green; hygiene gate active; dedup complete.

### Wave 4 — OSS Governance & Release Stream (MEDIUM risk; requires explicit decision on rename)
| Task | Detail | Est. commits |
|---|---|---|
| 4.1 | `SECURITY.md` coordinated-disclosure section; CODEOWNERS expansion; CONTRIBUTING/SUPPORT/GOVERNANCE refresh vs Phase 2 layout | 1 |
| 4.2 | Branch protection `main`: PR required, checks required, force-push blocked, auto-delete head branches ON, squash-merge default (GitHub settings — PD action) | (settings) |
| 4.3 | Version single-source: `VERSION` canonical; sync root `package.json`; align SDKs; release workflow `vX.Y.Z` tags + GitHub Release + CHANGELOG | 1–2 |
| 4.4 | Semver tag stream: replace 38 feature tags with clean release tags (archive old as refs) | 1 |
| 4.5 | **(OPTIONAL, PD decision)** `frontend-v3` → `frontend/` rename + import path rewrite (scoped; highest risk of this program) | 1–2 |
| **Verification** | full cycle; release dry-run in CI; tags/versions consistent | — |
| **Rollback** | revert release/tag commits; re-tag from archive refs | — |

**Wave 4 exit criteria:** release stream live; `VERSION` == package.json == latest tag; branch
protection active; OSS governance verified.

## 2. Aggregate Estimates

| Metric | Estimate |
|---|---|
| **Total commits** | 18–26 |
| **Engineering hours** | 40–60 hrs (analysis 8 done; execution 32–52) |
| **Files relocated** | ~1,400 (root docs + legacy trees) |
| **Files archived (superseded)** | ~60 |
| **Workflows** | 26 → 12 |
| **Branches** | 125 → ≤ 5 active (rest archived) |
| **Root `.md`** | 156 → ≤ 16 |
| **Tags** | 38 → clean semver stream |

## 3. Effort / Risk / Rollback Matrix

| Wave | Effort | Risk | Rollback |
|---|---|---|---|
| 1 Root/Docs | 8–12 h | LOW | single revert per commit |
| 2 Legacy+Git | 8–12 h | LOW (branch deletions gated by archive-refs) | revert moves; recreate branches from refs |
| 3 Docs+CI | 10–14 h | MEDIUM (workflow consolidation) | per-workflow revert |
| 4 OSS+Release | 12–18 h | MEDIUM (rename optional; tags public) | revert commits; re-tag from archive refs |

## 4. Benefits (justification)

- **Structure:** root clutter eliminated → contributor clarity, review efficiency.
- **Git:** bloat removed, branch chaos ended, linear history, clean semver releases.
- **CI:** 14 fewer workflows → faster runs, less maintenance, one hygiene gate prevents regressions.
- **Docs:** canonical single-home documentation → trust and searchability.
- **DX:** 30-minute onboarding, one-command tests.
- **OSS readiness:** standard governance verified, releases live, Scorecard-friendly.
- **Projected health score:** 48 → ≈85 (Phase 7 scorecard).

## 5. Success Criteria (program-level)

- Root file count ≤ 25; zero broken links; ≤ 12 workflows; ≤ 5 active branches; semver release
  stream live; health score ≥ 80; all application gates unchanged (architecture 25/25, domain 11/11,
  backend tests PASS, OpenAPI byte-identical, ruff/tsc/eslint at baseline).
- Every commit reversible via single `git revert`; zero history rewrites; no force-push.

## 6. Approval Required

This plan executes **real repository mutations** (file moves, branch/tag deletion, CI changes).
Per the Program Director's constraint, **no execution begins until explicit approval** of this plan.

**Estimated total: 18–26 commits, 40–60 hours, health 48 → ~85.**
