# PROGRAM-REPO-01 — FAILURE INJECTION
Pre-Execution Certification — Phase 3 (DRY RUN)
Date: 2026-08-08 · Status: **SIMULATED — 11 failure classes × 4 waves, all with detection/recovery/rollback/prevention**

## Failure taxonomy
For each failure: **Detection** (how it surfaces), **Recovery** (safe path), **Rollback** (revert unit), **Prevention** (gate/check).

---

### F-01 Broken path (script ref not re-pointed)
Occurs in every wave (H-01, H-02, E-08, logs/reports paths).
- **Detection:** `scripts/validate*`, `dependency_guardian`, `architecture` run fails; gate J (repo-hygiene) flags dangling path; CI fails on script step.
- **Recovery:** re-point path in-place, re-run validation.
- **Rollback:** revert the re-point commit (single `git revert`).
- **Prevention:** repo-hygiene gate J runs a dead-ref scan (path existence assertion) BEFORE each commit; Wave pre-flight checklist lists every path edge (Phase 1 table).

### F-02 Generator failure (docs.py / generate_dashboard.py)
- **Detection:** script raises on write; generated file missing → gate J link check fails.
- **Recovery:** fix output path, re-run generator, regenerate deterministic outputs.
- **Rollback:** revert output-path commit; old ROOT files restored.
- **Prevention:** deterministic generation (same input → same output); pre-commit re-run + diff check.

### F-03 Workflow failure (frontend-pwa.yml after v3 re-point)
- **Detection:** CI job fails on v3 build.
- **Recovery:** fix v3 build config (already validated by ci.yml precedent — v3 builds green today).
- **Rollback:** revert workflow commit → pwa returns to v2.
- **Prevention:** B-2 pre-condition: run frontend-pwa against v3 in a PR on a branch BEFORE merging the archive commit; gate = green pwa run.

### F-04 Broken documentation links (Wave 1 link pass)
- **Detection:** gate J link-checker fails on dangling relative refs.
- **Recovery:** rewrite affected refs, re-run link check.
- **Rollback:** revert link-pass commit.
- **Prevention:** link rewrite performed by deterministic script (sed pattern over known pairs), re-run after every move chunk.

### F-05 Rollback interruption (revert partially applied)
- **Detection:** `git revert --abort` state, or CI red mid-revert.
- **Recovery:** `git revert --continue` or `--abort` + clean tree; worktree is always clean before revert starts.
- **Rollback:** the revert IS the rollback; interrupted reverts are resumable by git.
- **Prevention:** one revert per commit; never batch multiple reverts in one command; stash/hook-free (no git hooks).

### F-06 Partial execution (half the files moved)
- **Detection:** gate J fails (root files still present + docs new files), link check partial.
- **Recovery:** complete remaining `git mv`, re-run gates.
- **Rollback:** revert partial commit (git tracks renames as one unit once committed).
- **Prevention:** atomic commits — each `git mv` set + its path re-points + its link rewrite lands in ONE commit; no commit lands half-finished (pre-commit gate).

### F-07 Interrupted migration (crash/network mid-move)
- **Detection:** shell exits non-zero; uncommitted renames present in status.
- **Recovery:** `git checkout -- .` + re-run the atomic script.
- **Rollback:** renames never committed → nothing to revert; if committed, `git revert`.
- **Prevention:** migration scripts idempotent (`git mv` fails cleanly if source missing); worktree backup not needed (git is the backup).

### F-08 Unexpected dependency (unscanned reference)
- **Detection:** gate J dead-ref scan + full `rg` pre-flight (Phase 1 surface).
- **Recovery:** classify new edge, re-point, continue.
- **Rollback:** revert the commit that touched it.
- **Prevention:** mandatory re-scan of Phase-1 surfaces at start of every wave (imports/workflows/generators/docs/release/deploy); the 6-surface scan is the wave entry gate.

### F-09 Repository corruption (git index damage)
- **Detection:** `git fsck`/`git status` error, non-zero exits.
- **Recovery:** `git fsck` repair; re-clone as last resort (remote is source of truth, push per commit).
- **Rollback:** reset to last green commit.
- **Prevention:** push each commit (remote is the backup); no force-push; no history rewrite.

### F-10 Branch conflict (status-check name change, W3 B-4)
- **Detection:** PR protected-branch check fails (required checks mismatch).
- **Recovery:** update branch-protection required-checks list to merged workflow names.
- **Rollback:** revert workflow-merge commit; restore old check names.
- **Prevention:** B-4 pre-condition — update protection rules in the SAME commit that renames checks; verify with a test PR before merge.

### F-11 Helm/deployment image missing (E-04 re-point)
- **Detection:** helm install fails `ImagePullBackOff` for new frontend image.
- **Recovery:** point to existing valid image tag; verify image registry contains the tag BEFORE commit.
- **Rollback:** revert values.yaml commit → back to `frontend-v2`.
- **Prevention:** registry tag existence check = gate before W2 commit touching helm; staged rollout (deploy to one env first).

---

## Per-wave failure matrix
| Wave | Applicable failures |
|---|---|
| W1 | F-01, F-02, F-04, F-06, F-07, F-09 |
| W2 | F-01, F-03, F-05, F-06, F-07, F-08, F-09, F-11 |
| W3 | F-01, F-04, F-06, F-07, F-09, F-10 |
| W4 | F-01, F-05, F-06, F-07, F-09 |

## Conclusion
Every failure class has a deterministic detection, recovery, rollback (single `git revert` or uncommitted-abort), and prevention (gate + pre-flight + atomic commit). **No failure class leaves the repository in an unrecoverable state.** Highest-surfacing risk is F-03/F-11 (frontend-v2 hand-off), which is exactly why B-2 (pwa-vs-v3 green run) and registry-existence checks are mandatory Wave-2 pre-conditions.
