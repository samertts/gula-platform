# PROGRAM-REPO-01 MASTER EXECUTION PLAN

**Program:** PROGRAM-REPO-01 v1.0 — Repository Engineering & Open Source Excellence
**Phase:** 2.5-H / F — Execution Blueprint (ANALYSIS ONLY — no mutations)
**Date:** 2026-08-08
**Status:** DRAFT — FOR PROGRAM DIRECTOR APPROVAL. Execution begins only after approval; repository
mutations remain strictly forbidden until then.

**Governance:** every wave honors ADR-028 (move-first, single-revert reversible, evidence-based),
AGENTS.md (atomic commits, Conventional Commits, verification cycle, STOP after each wave), and the
new REPOSITORY_CONSTITUTION.

---

## PROGRAM LEVEL

- **Total waves:** 4
- **Estimated total hours:** 38–58 (per-wave below)
- **Estimated total commits:** 24–38
- **Estimated total PRs:** 7–10
- **Primary risk:** Wave 2 frontend-v2 CI dependency (E-03) — mitigated by ordering.
- **Unconditional gate before program start:** PD approval + branch `remediate-security-001` merged
  to `main` (it holds the PROGRAM-01 closure).

---

# WAVE 1 — Root Documentation Consolidation

| Attribute | Value |
|---|---|
| **Objectives** | (1) Move ~120 root `.md` → `docs/{architecture,programs,reports,certification,niam,production,audit}/`; (2) create `docs/README.md` index; (3) fix SUPPORT.md broken link + re-point 8 cross-links; (4) root non-hidden file count ≤ 25; (5) re-point generators so they write to `docs/architecture/` |
| **Expected files** | ~120 `.md` moved; ~16 kept at root; ~25 archived (superseded dup); `docs/README.md` new; `scripts/architecture/docs.py` + `report.py` path edits; AGENTS.md regen |
| **Expected directories** | new: `docs/{programs,audit}` (merge into existing others); no root dirs changed |
| **Risk level** | **LOW** |
| **Rollback plan** | `git revert` per move-commit (pure `git mv`); generator-path revert restores root writes |
| **Validation gates** | architecture gate 25/25 · boot 118 · OpenAPI byte-identical · ruff 378 · tsc 0 · eslint 0 · backend suite PASS · 0 broken links · `git revert --no-commit HEAD` clean · brain-fresh |
| **Estimated engineering hours** | 3–5 |
| **Success criteria** | root `.md` ≤ 16 canonical; docs index live; generators write to `docs/`; 0 broken links; full validation PASS |
| **STOP CONDITIONS** | any validation gate fails → halt, revert that commit, report, await PD |

---

# WAVE 2 — Legacy Isolation + Git Housekeeping

| Attribute | Value |
|---|---|
| **Objectives** | (1) Re-point `frontend-pwa.yml` v2→v3 (E-03) + `helm values.yaml` image (E-04); (2) update 3 scripts (E-08) to archive/ or canonical paths; (3) `git mv` legacy/dormant trees → `archive/` (~1,100 files); (4) `git gc` + branch/tag cleanup (125→≤5 active; archive-refs first) |
| **Expected files** | ~1,100 moved; 3 script files edited; frontend-pwa.yml + helm values.yaml edited; refs (branches/tags) restructured |
| **Expected directories** | archive gains: frontend-v2, nhop-platform, platform-apps, packages-uap, frontend-static, assessment, reports, ai, architecture, sample_tracking, test_library, tests, hospital_desktop, database, identity_report, supabase, digitalocean, edge_agent, client, cli, pitch-deck, k6, logs (+ empty placeholders) |
| **Risk level** | **LOW→MEDIUM** (CRITICAL only if E-03 skipped — plan mandates E-03 first) |
| **Rollback plan** | revert CI-repoint commit; revert script-path commit; revert each `git mv` commit; re-create branches/tags from `refs/archive/*` |
| **Validation gates** | Wave-1 gates + `dependency_guardian`/`repository_scorecard`/`project_brain` green + frontend-v3 build in CI green + `git fsck --full` clean + pack ≤ ~70 MiB + active branches ≤ 5 + 0 importers outside archive |
| **Estimated engineering hours** | 6–10 |
| **Success criteria** | all legacy/dormant trees under `archive/`; CI builds v3; scripts green; git clean |
| **STOP CONDITIONS** | E-03 not verified green → do not archive frontend-v2; any gate failure → halt + revert + report |

---

# WAVE 3 — Documentation Dedup + CI Consolidation + JSON Removal

| Attribute | Value |
|---|---|
| **Objectives** | (1) Dedup ~25 doc families to canonical homes (archive-first); (2) consolidate 26→12 workflows (deploy-family merged into deploy.yml; quality-family into quality-gate.yml; + repo-hygiene.yml); (3) remove ~11 MB generated JSON from git → .gitignore/CI artifacts; (4) align branch-protection status-check names |
| **Expected files** | ~25 docs deduped; 14 workflows merged into 12 (1 new); `.gitignore` edit; ~6 JSON files removed; CODEOWNERS/README badge updates |
| **Expected directories** | none new at root; `docs/` subdir consolidation (~90→~25 sub-areas) |
| **Risk level** | **MEDIUM** |
| **Rollback plan** | per-workflow revert; doc archive-first revert; JSON recoverable from git history |
| **Validation gates** | all Wave-1/2 gates + all 12 workflows green + hygiene gate PASS + 0 broken links + no tracked generated JSON + branch protection checks match |
| **Estimated engineering hours** | 8–12 |
| **Success criteria** | 12 green workflows; hygiene gate active; dedup complete; repo size reduced |
| **STOP CONDITIONS** | any workflow red after merge → revert that workflow; check-name mismatch → coordinate protection first |

---

# WAVE 4 — OSS Governance + Release Stream (+ Optional Rename)

| Attribute | Value |
|---|---|
| **Objectives** | (1) SECURITY.md coordinated-disclosure; CODEOWNERS expansion; CONTRIBUTING/SUPPORT/GOVERNANCE refresh; (2) branch protection + auto-delete; (3) VERSION single-source + sync package.json/SDKs; (4) 38 tags → semver stream (archive-refs first, PD-approved); (5) GitHub Release for `v1.0.0`; (6) **OPTIONAL:** `frontend-v3 → frontend/` rename (last) |
| **Expected files** | SECURITY/CONTRIBUTING/SUPPORT/GOVERNANCE/CODEOWNERS/VERSION/package.json/contracts SDKs/release.yml; + rename (if approved): 168 files + generator/CI/helm re-point |
| **Expected directories** | `frontend/` replaces `frontend-v3/` (if approved); no other new dirs |
| **Risk level** | **MEDIUM** (tags public-ref; rename HIGH) |
| **Rollback plan** | revert doc/version commits; re-tag from archive-refs; rename revertible |
| **Validation gates** | all prior gates + VERSION==package.json==latest tag + GitHub Release live + zero-drift PASS + branch protection active + semver tag stream |
| **Estimated engineering hours** | 8–14 |
| **Success criteria** | release stream live; OSS governance verified; health dims at target (Release 85, Gov 85, OSS 85); optional rename done cleanly |
| **STOP CONDITIONS** | tag cleanup not PD-approved → skip (partial wave); rename not PD-approved → skip; any gate failure → halt + revert + report |

---

## EXECUTION ORDER & STOP DISIPLINE

```
PD approval
   → Wave 1 (3–5h, 3–5 commits, 1 PR) → verify → REPORT → STOP → PD sign-off
   → Wave 2 (6–10h, 6–9 commits, 2 PRs) → verify → REPORT → STOP → PD sign-off
   → Wave 3 (8–12h, 8–12 commits, 2–3 PRs) → verify → REPORT → STOP → PD sign-off
   → Wave 4 (8–14h, 6–10 commits, 2–3 PRs) → verify → REPORT → STOP → PD sign-off
   → PROGRAM-REPO-01 CERTIFICATION
```

---

## PROGRAM SUCCESS CRITERIA

1. Root non-hidden file count ≤ 25; 0 broken links; ≤ 12 workflows; ≤ 5 active branches; semver
   release stream live.
2. All application gates unchanged: architecture 25/25, domain 11/11, backend suite PASS, OpenAPI
   byte-identical, ruff 378, tsc 0, eslint 0, vitest 122.
3. Every commit reversible via single `git revert`; zero history rewrites; no force-push.
4. REPOSITORY_CONSTITUTION ratified and enforced by repo-hygiene gate.
5. 14-dimension health model at target (Organization 85, Docs Org 85, Git 80, CI/CD 80, Release 85,
   Gov 85, DX 80, Maintainability 75, Scalability 80, OSS 85; App/Arch/Testing/Security hold).

## PROGRAM STOP CONDITIONS
- Any Wave validation gate fails twice on the same check → halt program, full report to PD.
- Any evidence of behavior/API change (OpenAPI drift, route change, business logic change) →
  halt program immediately (this program must be behavior-preserving).
- Program Director may halt at any STOP point.
