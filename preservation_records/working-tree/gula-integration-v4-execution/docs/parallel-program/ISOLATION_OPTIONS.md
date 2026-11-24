# ISOLATION OPTIONS — PROGRAM-GULA-PARALLEL-001

**Status:** ANALYSIS ONLY — no isolation environment was created or modified for remediation
**Date:** 2026-11-19
**Related:** `PROGRAM_CONTROL.md §3` (isolation decision), `POST_WAVE_B_EXECUTION_PLAN.md §7`

> Requirement: investigate safe isolation options that **preserve all user work**.
> Do not modify or copy the protected working tree without explicit approval.
> No option below has been executed for remediation. The only environment touched was a
> pre-existing read-only evaluation clone (created in Wave A, no edits made).

---

## 1. What must be preserved

| Item | Verified state (Phase 0, unchanged) |
|---|---|
| Branch / HEAD | `integration/gula-unification-v1` @ `2206654dc713ea2de8c564a3207dfe05fde23549` |
| Working tree | 126 modified + 20 staged renames + 232 untracked = **378 protected paths** |
| Worktrees | 5 active + 1 prunable |
| Stashes | 2 |
| Git state | ahead 2 / behind 0 vs `origin/main`; valid merge-base `2827c1ff...` |
| Patch under review | `offline_sync_service.py` (` M`), `test_offline_sync.py` (` M`), `test_offline_conflict_synthetic.py` (`??`) |

Byte-for-byte preservation of all 378 paths and all Git state is a hard constraint for every option.

---

## 2. Options assessed

### Option A — In-place remediation (current working tree)
- **Mechanism:** edit files directly where they are.
- **Preserves user work:** No — any edit risks mixing agent changes with uncommitted user changes; A06-002 and A08-R001 are themselves user work.
- **Verdict:** **REJECTED.** Explicitly prohibited; insufficiently isolated by standing instruction.

### Option B — Clean clone from verified HEAD (already present)
- **Mechanism:** `/tmp/opencode/gula-isolation-eval`, clean clone at `2206654d`, 0 modifications, 101 committed migrations.
- **Preserves user work:** Yes — it never touches the protected tree.
- **Gaps:** contains the **unsafe HEAD `CRDT_MERGE`**, not the user's fix; omits all 378 user paths and `frontend-v3/node_modules`.
- **Verdict:** **USABLE ONLY for committed-code baselines** (e.g., HEAD test behavior, static checks). **Cannot verify the CONFLICT_QUARANTINE patch.**

### Option C — Full git worktree of the current branch
- **Mechanism:** `git worktree add` from the current HEAD/branch.
- **Preserves user work:** No — a worktree checks out committed state, not the uncommitted 378 paths; creating/removing worktrees is a Git state change (5 active + 1 prunable already exist).
- **Verdict:** **REJECTED.** Unauthorized Git state change; does not carry user work.

### Option D — Clean clone + explicitly approved replication of named user files (RECOMMENDED)
- **Mechanism:** use Option B's clone; replicate **only the three named files** of the patch (`backend/app/services/offline_sync_service.py`, `backend/tests/test_offline_sync.py`, `backend/tests/test_offline_conflict_synthetic.py`) by applying the exact captured diff and copying the untracked companion test. The original files remain byte-identical; the protected tree is never written to.
- **Preserves user work:** Yes, if and only if replication is read-source-only and the clone is throwaway.
- **Requires:** explicit USER release of those three files and ORCH authorization to replicate them into the clone (this is "copying protected work" in the narrow sense and is **not performed** in this session).
- **Enables:** full execution of the 31 designed tests + R1/R2/R3/R4 additions in genuine isolation with pytest 9.1.1 and cryptography 49.0.0 already available.
- **Verdict:** **RECOMMENDED once release + authorization are granted.** Only viable path to verify the patch without a commit.

### Option E — User-created clean commit containing the patch
- **Mechanism:** user commits the three files on a scratch branch; orchestrator clones that commit.
- **Preserves user work:** Yes — user controls the commit; no agent touches the protected tree.
- **Trade-off:** requires a user-driven Git operation (authorized by the user, not by this program).
- **Verdict:** **ACCEPTABLE alternative** if the user prefers a commit boundary; avoids any replication by agents.

### Option F — Archive/snapshot of the entire worktree
- **Mechanism:** copy all 378 paths to a scratch location.
- **Preserves user work:** Copy does not modify originals, but it duplicates a large, sensitive tree (potential PHI/config/material), expands the protected surface, and is expressly disallowed without approval.
- **Verdict:** **REJECTED** unless the user explicitly requests it; no need for the patch review.

---

## 3. Comparison matrix

| Option | Isolated | Carries patch | Touches protected tree | Git state change | Cost | Verdict |
|---|---|---|---|---|---|---|
| A In-place | No | Yes | **Yes** | No | zero | REJECTED |
| B Clean clone | Yes | No | No | No | low | Baseline only |
| C Full worktree | Partial | No | No | **Yes** | low | REJECTED |
| D Clone + named-file replication | Yes | **Yes** | No | No | low | RECOMMENDED (needs release) |
| E User-created commit | Yes | Yes | No | User-controlled | low | ACCEPTABLE |
| F Full snapshot | Yes | Yes | No (copy) | No | high/risky | REJECTED without approval |

---

## 4. Verification of isolation integrity (to run for the chosen option)

1. `git -C <clone> status --porcelain` shows only the intentionally replicated files.
2. `git -C <clone> rev-parse HEAD` = `2206654d…` (or the user's scratch commit for E).
3. `git status --porcelain` in the protected tree is byte-identical to the Phase 0 snapshot (378 paths) before and after all work — captured read-only, compared by hash.
4. `git stash list`, `git worktree list`, branch list unchanged.
5. All test artifacts written only inside the isolated clone.

---

## 5. Decision required

Choose **one** of:
- **D** (recommended): grant USER release + ORCH authorization to replicate the three named files into `/tmp/opencode/gula-isolation-eval` (or a fresh clone), then execute tests.
- **E**: create a user-owned scratch commit and provide the commit SHA for cloning.
- **B only**: keep testing to committed-code baselines; leave the patch unverified and certification halted.

Until a choice is made, no isolation environment is created or modified and no tests are executed against the patch.
