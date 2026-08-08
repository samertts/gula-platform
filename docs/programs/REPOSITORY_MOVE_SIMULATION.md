# REPOSITORY MOVE SIMULATION

**Program:** PROGRAM-REPO-01 v1.0 — Repository Engineering & Open Source Excellence
**Phase:** 2.5-D / F — Repository Move Simulation (ANALYSIS ONLY — DRY-RUN; no mutations executed)
**Version:** 1.1 (expanded — 14-field simulation per migration)
**Date:** 2026-08-08
**Status:** DRAFT — simulated outcomes only. No files moved, no CI changed, no commits.

**Method:** every migration simulated against the dependency graph (Phase A), classification (Phase B)
and risk matrix (Phase C). Exact reference lines measured from workflows/scripts/generators below.

---

# MIGRATION M-1 — Root Markdown Consolidation → `docs/**` (Wave 1)

**Move:** ~120 root `.md` → `docs/{architecture,programs,reports,certification,niam,production,audit}/` via `git mv`; ~16 kept at root; ~25 archived (superseded).

| Field | Assessment |
|---|---|
| **Affected files** | ~120 root `.md` (156 total → ~16 kept); `docs/README.md` (new index); 8 cross-link targets; `SUPPORT.md` broken link |
| **Affected workflows** | none directly (docs not CI-triggered); `ai-governance.yml` brain-freshness may flag AGENTS.md path refs |
| **Affected generators** | `scripts/architecture/docs.py` — **writes master docs to `ROOT`** (`p = ROOT / "MASTER_ARCHITECTURE_v2.md"` etc., lines 198/253/306/370/416/478/561). **Must be re-pointed to `ROOT / "docs/architecture"` in the SAME commit**, else the next `architecture-docs` run regenerates root copies (duplicate). Same for `scripts/architecture/report.py` (CONSTITUTION_PATH/CERTIFICATION_PATH) and `scripts/domains/*` outputs |
| **Affected documentation** | 8 inbound `CONTRIBUTING.md`-style links; root `.md` cross-links (`references/` 34, `runbooks/` 6, `adr/` 5); generator-sourced master docs (regenerate to new home) |
| **Affected CI** | none (code paths untouched); brain-freshness gate requires AGENTS.md regen (`scripts/project_brain.py`) |
| **Affected release pipeline** | none |
| **Affected Docker** | none |
| **Affected Kubernetes** | none |
| **Affected Terraform** | none |
| **Affected Helm** | none |
| **Rollback procedure** | `git revert <commit>` per move-commit (pure `git mv`, no content edits); restore generator paths via revert |
| **Rollback duration** | < 15 min (single revert + regen check) |
| **Estimated engineering effort** | 3–5 hrs (bucketing, generator re-point, link fixes, AGENTS.md regen, docs index) |
| **Confidence score** | **95/100** — pure file moves, fully revertible, zero runtime/CI surface |

---

# MIGRATION M-2 — Archive `frontend-v2/` (Wave 2, HIGHEST-RISK)

**Move:** `git mv frontend-v2/ → archive/frontend-v2/` (163 files).

| Field | Assessment |
|---|---|
| **Affected files** | 163 tracked files (src, public, package.json, lock, configs) |
| **Affected workflows** | **CRITICAL — `frontend-pwa.yml` (13 refs):** lines 7/13 (path triggers), 48 (`working-directory: frontend-v2`), 58 (cache path), 63 (node_modules path), 64 (hashFiles key), 98/106/164/207 (artifact paths), 118 (lighthouse working-dir), 137 (`frontend-v2/lighthouse.config.json`). Also `frontend-e2e.yml` triggers (lines 7/11) reference v2 paths |
| **Affected generators** | none (no generator writes into frontend-v2) |
| **Affected documentation** | AGENTS.md, CONTRIBUTING.md, DX_REPORT references to frontend-v2; Phase-1 R-05 records |
| **Affected CI** | frontend-pwa build job → **must be re-pointed to frontend-v3 or removed** BEFORE archive; otherwise CI fails |
| **Affected release pipeline** | none direct (no release job builds v2) |
| **Affected Docker** | none (root Dockerfile builds `server/_core`, not v2; compose has no v2 edge) |
| **Affected Kubernetes** | none (image names only) |
| **Affected Terraform** | none |
| **Affected Helm** | **`helm/gula-platform/values.yaml:228` — `repository: frontend-v2`** → must become `frontend-v3`/`frontend` (E-04) or the deployed image name breaks |
| **Rollback procedure** | revert CI re-point commit + revert `git mv` commit (2 reverts) |
| **Rollback duration** | 20–30 min |
| **Estimated engineering effort** | 4–6 hrs (CI re-point, helm image fix, script E-08 updates, move, verify frontend-v3 build parity) |
| **Confidence score** | **60/100** pre-condition; **85/100** after E-03/E-04/E-08 re-pointed and verified |

---

# MIGRATION M-3 — Archive `platform/`, `nhop-platform/`, `packages/`, `frontend/` (Wave 2)

**Move:** `git mv platform/ → archive/platform-apps/` (616), `nhop-platform/ → archive/nhop-platform/` (55), `packages/ → archive/packages-uap/` (52), `frontend/ → archive/frontend-static/` (14).

| Field | Assessment |
|---|---|
| **Affected files** | 737 tracked files across 4 trees |
| **Affected workflows** | none (no workflow references these dirs) |
| **Affected generators** | none |
| **Affected documentation** | AGENTS.md (project_brain.py National scan root `nhop-platform/`, line 322); CONTRIBUTING/DX refs |
| **Affected CI** | none directly (no CI path triggers) |
| **Affected release pipeline** | none |
| **Affected Docker** | none for compose/root; `nhop-platform/Dockerfile` and `platform/Dockerfile` move WITH their trees (no build context references them) |
| **Affected Kubernetes** | none (image names only) |
| **Affected Terraform** | none |
| **Affected Helm** | none |
| **Affected scripts** | **`scripts/dependency_guardian.py`:** lines 56/68 (`nhop-platform/requirements.txt`), 61 (`FRONTEND_DIR = frontend-v2`); **`scripts/repository_scorecard.py`:** line 360 (`module_dirs` incl. frontend-v2, nhop-platform, edge_agent), 638 (`frontend-v2/package.json`); **`scripts/project_brain.py`:** line 322 (National scan root). Update to archive paths or drop |
| **Rollback procedure** | revert move commits (pure `git mv`); revert script-path commits |
| **Rollback duration** | < 30 min |
| **Estimated engineering effort** | 3–5 hrs (moves + 3 script path updates + run engines to verify) |
| **Confidence score** | **90/100** — low edge count, all script edges identified |

---

# MIGRATION M-4 — Archive DORMANT/EXPERIMENTAL set (Wave 2)

**Move:** `git mv` `assessment/` (47), `reports/` (49), `ai/` (32), `architecture/` (25), `sample_tracking/` (7), `test_library/` (4), `tests/` (14), `hospital_desktop/` (26), `database/` (2), `identity_report/` (8), `supabase/` (2), `digitalocean/` (2), `edge_agent/` (10), `client/` (12), `cli/` (9), `pitch-deck/` (3), `k6/` (1), `logs/` (1), `tmp/` (0), `backups/` (0), `gula-platform/` (1).

| Field | Assessment |
|---|---|
| **Affected files** | ~244 tracked files (+ 5 empty/placeholder dirs) |
| **Affected workflows** | none (no workflow references any of these) |
| **Affected generators** | none (they write to docs/.ai/root only) |
| **Affected documentation** | `dependency_guardian_report.md` writes to `assessment/` (dependency_guardian.py:50) → **must be re-pointed or the tool errors post-archive**; AGENTS.md refs |
| **Affected CI** | none (no path triggers) |
| **Affected release pipeline** | none |
| **Affected Docker** | none |
| **Affected Kubernetes** | none |
| **Affected Terraform** | none |
| **Affected Helm** | none |
| **Affected scripts** | `repository_scorecard.py:360` module_dirs (edge_agent, ai, client, frontend-v2); `project_brain.py:321` (edge_agent); `dependency_guardian.py:57/69` (edge_agent/requirements.txt) |
| **Rollback procedure** | revert move commits; re-point report-path commit |
| **Rollback duration** | < 20 min |
| **Estimated engineering effort** | 2–4 hrs |
| **Confidence score** | **95/100** — near-zero inbound edges, all identified |

---

# MIGRATION M-5 — Git Housekeeping: gc + branch/tag cleanup (Wave 2)

**Action:** `git gc --prune=now` + `git prune-packed`; delete ~100 stale branches (archived as `refs/archive/branches/*` first); re-tag 38 → semver (archived as `refs/archive/tags/*`).

| Field | Assessment |
|---|---|
| **Affected files** | 0 working-tree files (refs + packfiles only) |
| **Affected workflows** | none (no workflow depends on branch/tag names; verify none reference feature branches) |
| **Affected generators** | none |
| **Affected documentation** | GIT_STRATEGY.md, release notes |
| **Affected CI** | none (triggers are path + branch-name independent) |
| **Affected release pipeline** | tag cleanup touches release tags → requires PD approval (public refs) |
| **Affected Docker/K8s/Terraform/Helm** | none |
| **Rollback procedure** | branch/tag re-creation from archive refs; gc is non-destructive to reachable objects |
| **Rollback duration** | < 15 min |
| **Estimated engineering effort** | 2–4 hrs (fsck before/after, triage 125 branches, archive refs, delete) |
| **Confidence score** | **85/100** — irreversible only if archive-refs skipped; gated |

---

# MIGRATION M-6 — Documentation De-duplication (Wave 3)

**Move/Consolidate:** CHANGELOG ×8, ARCHITECTURE ×12, PERFORMANCE_REPORT ×8, SECURITY ×4, TECHNICAL_DEBT ×2, final_report ×2 → single canonical home each; superseded copies → archive.

| Field | Assessment |
|---|---|
| **Affected files** | ~25 duplicate docs (+ their inbound links, E-11) |
| **Affected workflows** | none |
| **Affected generators** | docs/baselines regenerated by `scripts/architecture/*` — verify canonical homes align |
| **Affected documentation** | every inbound link to a removed duplicate must re-point to canonical |
| **Affected CI** | none (no doc CI); broken-link gate (new) will enforce |
| **Affected release pipeline** | keep root `CHANGELOG.md` (release uses it) |
| **Affected Docker/K8s/Terraform/Helm** | none |
| **Rollback procedure** | archive-first per file; revert commits |
| **Rollback duration** | < 20 min |
| **Estimated engineering effort** | 2–4 hrs |
| **Confidence score** | **85/100** — depends on inbound-link audit (E-11) |

---

# MIGRATION M-7 — CI Consolidation 26 → 12 + repo-hygiene gate (Wave 3)

**Action:** merge deploy-family (7) + quality-family (5) per GITHUB_GOVERNANCE §3; add `repo-hygiene.yml`.

| Field | Assessment |
|---|---|
| **Affected files** | 14 workflow files (merged), 1 new workflow, `.github/actions/*`, `.github/scripts/*` |
| **Affected workflows** | **ALL 26** (triggers/paths reviewed); merged names change → **branch-protection required-check names must be updated in the same change** (else CI blocks merges) |
| **Affected generators** | none |
| **Affected documentation** | GITHUB_GOVERNANCE.md, README badges |
| **Affected CI** | the entire surface (this IS the CI change) |
| **Affected release pipeline** | release.yml retained (checks must match) |
| **Affected Docker** | build-images/deploy contexts retained |
| **Affected Kubernetes** | none |
| **Affected Terraform** | none |
| **Affected Helm** | none |
| **Rollback procedure** | per-workflow revert (git history restores each original workflow) |
| **Rollback duration** | 30–60 min |
| **Estimated engineering effort** | 8–12 hrs (merge + check-name sync + hygiene job + full validation) |
| **Confidence score** | **75/100** — highest blast radius of Wave 3; must run full validation after every merge |

---

# MIGRATION M-8 — Remove generated audit JSON from git (Wave 3)

**Action:** `git rm` `security-audit/*.json` (~8 MB), `assessment/brain/*.json` (~3 MB); add to `.gitignore`; output as CI artifacts.

| Field | Assessment |
|---|---|
| **Affected files** | 6+ JSON files (~11 MB total) removed from tracking |
| **Affected workflows** | scan workflows write these — re-point artifact upload to CI artifacts, add .gitignore entry |
| **Affected generators** | security scans (bandit/semgrep/trivy/grype/sbom) — output stays on disk locally, ignored |
| **Affected documentation** | SECURITY_CERTIFICATION references may point at them |
| **Affected CI** | scan jobs must upload artifacts (not rely on tracked files) |
| **Affected release pipeline** | SBOM: keep `contracts/SBOM.md` + release SBOM artifact (not repo JSON) |
| **Affected Docker/K8s/Terraform/Helm** | none |
| **Rollback procedure** | restore from git history (files remain in history) |
| **Rollback duration** | < 10 min |
| **Estimated engineering effort** | 1–2 hrs |
| **Confidence score** | **95/100** — pure removal, recoverable from history |

---

# MIGRATION M-9 — OSS Governance + Version Sync + Semver Tags (Wave 4)

**Action:** SECURITY.md disclosure section; CODEOWNERS expansion; CONTRIBUTING/SUPPORT refresh; branch protection; VERSION-sync; 38 tags → semver stream (archived).

| Field | Assessment |
|---|---|
| **Affected files** | SECURITY.md, CONTRIBUTING.md, SUPPORT.md, CODEOWNERS, VERSION, root package.json, SDK package versions, release.yml |
| **Affected workflows** | release.yml (version-sync step), none others |
| **Affected generators** | none |
| **Affected documentation** | all governance docs |
| **Affected CI** | branch protection status checks (name alignment) |
| **Affected release pipeline** | **the core change** (release stream) |
| **Affected Docker/K8s/Terraform/Helm** | none |
| **Rollback procedure** | revert doc/version commits; re-tag from archive refs |
| **Rollback duration** | < 30 min |
| **Estimated engineering effort** | 6–10 hrs |
| **Confidence score** | **85/100** — tag cleanup is public-ref (needs PD); everything else reversible |

---

# MIGRATION M-10 — OPTIONAL `frontend-v3 → frontend/` rename (Wave 4)

**Move:** `git mv frontend-v3/ → frontend/` (168 files) + import/generator/CI/helm re-point.

| Field | Assessment |
|---|---|
| **Affected files** | 168 tracked files; every `frontend-v3/...` import string |
| **Affected workflows** | `ci.yml` (170–182), `frontend-e2e.yml` (7–44), `preview-deploy.yml` (20–33), `frontend-pwa.yml` (if re-pointed here), `secret-scanning.yml:87` |
| **Affected generators** | `generate_frontend_client.py` output path (`frontend-v3/src/api/generated/types.ts`) + `zero_drift_engine.py` registry |
| **Affected documentation** | AGENTS.md, CONTRIBUTING, README, DX_REPORT |
| **Affected CI** | all frontend jobs (working-directory + cache paths) |
| **Affected release pipeline** | release.yml frontend build path |
| **Affected Docker** | none direct (image built from v3 context in workflows) |
| **Affected Kubernetes** | none |
| **Affected Terraform** | none |
| **Affected Helm** | values.yaml:228 image name → `frontend` |
| **Rollback procedure** | revert rename + re-point commits |
| **Rollback duration** | 30–60 min |
| **Estimated engineering effort** | 6–10 hrs |
| **Confidence score** | **55/100** — highest-risk single move (broad string surface); recommended OPTIONAL/last |

---

# SIMULATION SUMMARY TABLE

| Migration | Effort | Rollback | Confidence | Risk |
|---|---|---|---|---|
| M-1 Root docs | 3–5h | 15 min | 95 | LOW |
| M-2 frontend-v2 archive | 4–6h | 30 min | 60→85 | **CRITICAL (cond.)** |
| M-3 legacy trees | 3–5h | 30 min | 90 | LOW |
| M-4 dormant/experimental | 2–4h | 20 min | 95 | LOW |
| M-5 git housekeeping | 2–4h | 15 min | 85 | LOW (refs) |
| M-6 doc dedup | 2–4h | 20 min | 85 | MEDIUM |
| M-7 CI consolidation | 8–12h | 60 min | 75 | MEDIUM-HIGH |
| M-8 JSON removal | 1–2h | 10 min | 95 | LOW |
| M-9 OSS+version+tags | 6–10h | 30 min | 85 | MEDIUM (tags) |
| M-10 frontend rename (opt) | 6–10h | 60 min | 55 | **HIGH** |

**Highest-risk migration:** M-2 (frontend-v2 archive — CI dependency E-03).
**Lowest-risk migration:** M-1 (root docs consolidation) and M-8 (JSON removal).
**Recommended first execution:** M-1, then M-2 (after E-03 pre-condition), M-3/M-4, M-5, M-6/M-7/M-8, M-9, M-10 optional last.
