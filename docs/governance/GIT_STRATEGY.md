# GIT STRATEGY

**Program:** PROGRAM-REPO-01 v1.0 — Repository Engineering & Open Source Excellence
**Phase:** 3 / 8 — Git Strategy
**Date:** 2026-08-08
**Status:** EXECUTED (Wave 4) — branch/tag/version cleanup complete 2026-08-08; this
document is now the authoritative git strategy for the repository.

---

## 1. Current State (from Phase 1 Audit, post-Wave-4 execution)

| Metric | Value | Verdict |
|---|---|---|
| Commits | ~850 | healthy volume for 5 months |
| Merge commits | 120 (14.7%) | violates AGENTS.md "rebase over merge" |
| Branches | 2 remote (`main`, `remediate-security-001`) | **clean** — 61 stale branches archived to `refs/archive/branches/*` (Wave 4) |
| Branches merged into main (remote) | 2 | cleanup completed (Wave 4) |
| Tags | 3 (`v1.0.0-RC1`, `v1.0.0-RC2`, `v2.1.0-engineering-factory`) | semver stream; 35 feature tags archived to `refs/archive/tags/*` (Wave 4) |
| `.git` size | 144 MB (68.73 MiB pack) | 5 garbage `tmp_pack_*` objects present |
| Current branch | `remediate-security-001` (synced with origin) | — |
| Version markers | `VERSION`=1.0.0, package.json=1.0.0 | **aligned** (Wave 4 single-source sync) |

## 2. Guiding Principles

1. **Never force-push shared branches.**
2. **Rebase, not merge** (AGENTS.md Branch Policy already mandates this).
3. **Every cleanup operation is reversible** (ADR-028: a single `git revert` or a re-fetch restores state).
4. **History is immutable for public/shared refs** — cleanup targets *branches and tags*, not commit rewriting.
5. **Work on `main` via short-lived feature branches** with branch protection (Phase 4).

## 3. Branch Cleanup Plan

### 3.1 Deletion criteria
Delete (locally and remotely) any branch that is:
- **Merged into `main`** (already the case for 2 remote + most local `claude/*`), OR
- **Stale ≥ 60 days with no un-merged meaningful work** (verify by comparing commit date vs branch tip merged-ness), OR
- **A superseded duplicate** (`claude/add-test-results-api-1ozK2` vs `-KTbDN`; `fix-unhealthy-gula-backend-container` vs `-zjakxk`).

### 3.2 Safety gates before deletion
1. `git branch --contains main` → identify merged branches first.
2. For un-merged branches: check whether tip commits are already reachable in `main` history (cherry-picked) via `git cherry main <branch>`.
3. **Preserve before delete:** create a lightweight ref namespace for anything ambiguous: `refs/archive/branches/<name>` (a tag-like ref, zero cost, invisible in normal branch listing, fully reversible). This satisfies ADR-028 "archive before delete."
4. Delete local + remote: `git branch -d` / `git push origin --delete`.

### 3.3 Execution sequence (Wave 2 of Phase 8 execution plan)
1. Merge `remediate-security-001` (current branch) into `main` first — its 22-file PROGRAM-01 closure commit is the canonical reference point.
2. Identify the 2 merged-remote + merged-local set → delete (~70 branches estimated).
3. For the ~30 un-merged stale branches: `git fetch origin` → `git cherry` triage → archive-ref the keepers, delete the rest.
4. Delete all remote stale branches via `git push origin --delete` (verified individually).

### 3.4 Post-cleanup expected state
- **≤ 5 branches**: `main` (protected), `develop` (optional long-lived integration), `release/*` (ephemeral), `remediate-security-001` (merged then deleted), current feature branch.
- All keepers preserved in `refs/archive/branches/`.

## 4. Repository Housekeeping (`git gc`)

### 4.1 Immediate actions
- Remove 5 garbage tmp packs: `git gc --prune=now` + `git prune-packed` (this does NOT rewrite history; it only packs/removes unreferenced objects).
- After legacy-file relocations (Phase 2 waves), optionally `git gc --aggressive` if size remains high.

### 4.2 Automated hygiene (prevent recurrence)
- Add a CI "repo hygiene" job (Phase 4): asserts `git count-objects` size threshold, branch count threshold, root-file count ≤ 25, and no `.tmp`/garbage packs. Gate on warnings only initially (advisory → hard).
- Document `git maintenance` (built-in periodic maintenance) in DX_REPORT.

## 5. Tag & Versioning Strategy

### 5.1 Problem (resolved Wave 4)
The tag stream was a feature-tag flood: 38 tags, ~30 feature-domain tags
(`national-*-v1.0`, `platform-*-v1.0`, `foundation-v1.0`, `governance-v1.0`,
etc.) — a one-time feature-tagging ceremony, not a release stream. Only
`v1.0.0-RC1`, `v1.0.0-RC2`, `v2.1.0-*` resembled releases. `VERSION`=1.0.0-RC2
conflicted with root `package.json`=1.0.0.

**Executed (2026-08-08, PD-approved):** 35 non-semver feature tags archived to
`refs/archive/tags/*` and deleted; semver stream (`vX.Y.Z`) now the only tag
pattern (aligned with `release.yml`'s `v*` validation); `VERSION` synced to
1.0.0 matching `package.json` and the backend/frontend package surfaces.

### 5.2 Proposed policy (SemVer 2.0 + GitHub Releases)
- **Release tags only:** `vX.Y.Z` (+ optional `-rc.N` pre-release). Every release tag must have a GitHub Release (CHANGELOG section + assets).
- **Remove obsolete feature tags:** delete the ~30 feature-domain tags after archiving their purpose in the release notes. This is a public-ref change → requires explicit Program Director approval; safe because tags are cheap and re-creatable from commit hashes (documented in this report).
- **Version drift resolution:** single source of truth = `VERSION` file; root `package.json` version synced by the release workflow (`release.yml` update as part of execution) OR a version-sync step in CI. Align all SDK package versions (`contracts/sdk/*`) to the same stream.

### 5.3 Branching model (recommended: trunk-based + release branches)
```
main        ────────●────────────────●────────  (protected; always releasable)
release/vX ├───────╲───── tag v1.1.0
feature/*   ╲──────────╱  short-lived, PR → main
```
- `feature/<issue-or-short-desc>` for all work, merged via squash-rebase PR (Phase 4 protection).
- `release/vX.Y.Z` only for stabilization before tagging.
- `main` requires CI green + review (Phase 4).

## 6. Commit Message Standard (already conventional; formalize)

- `type(scope): subject` — types: `feat` `fix` `docs` `refactor` `chore` `test` `ci` `build` `perf` `revert`.
- Atomic commits; body explains WHY; breaking changes annotated `BREAKING CHANGE:`.
- Pre-commit hook `[GULA-AI]` already enforces; add `conventional-commits` lint to the hook if missing (Phase 4).
- Enforce with `commitlint` in `.github/` if desired (optional; flag for PD).

## 7. Rollback & Risk Register

| Risk | Likelihood | Mitigation | Rollback |
|---|---|---|---|
| Deleting a branch with unique work | LOW (gated by archive-ref) | `refs/archive/branches/*` preserve ALL un-merged candidates | re-create branch from archive ref |
| Remote force concerns | NONE — no force-push anywhere in plan | branch protection blocks force-push to `main` | — |
| Tag deletion affects consumers | LOW (RC tags; no GA release consumed) | archive tags as `refs/archive/tags/*` before deletion | re-tag from commit |
| `git gc` prunes needed objects | NONE (gc only removes unreachable) | run `git fsck --full` before/after | `git fetch origin` restores |
| Version drift in package.json | MEDIUM | version-sync step in release workflow | revert the sync commit |

## 8. Success Criteria

- Branch count ≤ 5 active; all ambiguous branches archived as refs. **DONE — 2 remote branches.**
- `git count-objects` pack ≤ ~70 MiB; zero garbage tmp packs.
- Tags = clean SemVer stream; `VERSION` == package.json == latest release tag. **DONE — 3 semver tags; VERSION=1.0.0.**
- `git fsck --full` clean.
- Zero history rewrites; `git log` linear on `main`.
