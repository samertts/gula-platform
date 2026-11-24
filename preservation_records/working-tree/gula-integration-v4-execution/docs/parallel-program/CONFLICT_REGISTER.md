# CONFLICT REGISTER — PROGRAM-GULA-PARALLEL-001

Records real or potential conflicts in file ownership, content, or git state.
Nothing here has been resolved by destructive action.

| ID | Type | Description | Status | Resolution path |
|---|---|---|---|---|
| CR-001 | Ownership | Working tree contains 126 modified + 20 staged renames + 232 untracked paths of pre-existing user work | **OPEN — PROTECTED** | Exclude from all writes. Report only. User must release explicitly. |
| CR-002 | Git-state | 5 active worktrees + 1 prunable worktree + 2 stashes exist on related branches | **OPEN — PRESERVED** | Do not create/delete/switch worktrees; do not touch stashes. Wave A needs no worktree. |
| CR-003 | Historical data | Brief's migration figures (57/101/50/7/51) conflict with verified state (101/101/101/0/0 committed; 109 on disk) | **RESOLVED (verified)** | Use verified values in PROGRAM_CONTROL §2.6. Historical numbers marked stale. |
| CR-004 | Tooling | Program gate list assumes commands exist in all projects; verified they exist only in `frontend-v3` (plus root-level subset) | **RESOLVED (verified)** | Run gates package-locally; record `N/A` elsewhere. See PROGRAM_CONTROL §5. |
| CR-005 | Scope overlap risk | A02 (design system, entire frontend-v3) and A03 (pages) could both touch shared components used by pages | **PREVENTED** | Explicit boundary: A02 owns shared components/tokens; A03 owns `src/pages/` only; scope requests go to orchestrator. |
| CR-006 | Migration risk | 8 untracked new migration files present; brief forbids migration merges and DB execution | **OPEN — BLOCKED** | Audit only (A07). No merge, no execution, no edit of user-owned files. |

## Rules

- A conflict is never "resolved" by deleting, overwriting, moving, or force-changing user work.
- Every new conflict is assigned an ID and an explicit non-destructive resolution path.
- Any write-write conflict between agents is a P0 process failure: halt both agents.
