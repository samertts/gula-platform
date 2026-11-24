# GULA National Transformation V4 — Execution Workspace Provenance

**Record type:** additive, reversible, evidence-only  
**Generated:** 2026-11-24 UTC  
**Directive:** `GULA-MASTER-MANDATE-V4.0`  
**Status:** `EXECUTION WORKSPACE ESTABLISHED · ORIGINALS PRESERVED`

## 1. Source and execution boundary

| Item | Value |
|---|---|
| Source repository | `/home/samertts/workspace/projects/gula-integration` |
| Source HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` |
| Source branch | `integration/gula-unification-v1` |
| Execution workspace | `/home/samertts/workspace/projects/gula-integration-v4-execution` |
| Execution branch | `execution/gula-national-v4` |
| Execution HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` |
| Copy method | `cp -a` of the complete source tree, including `.git`, staged index, unstaged edits, and untracked files |
| Sibling repository | `/home/samertts/workspace/projects/gula-platform` remains the common object store; its working tree is untouched |

**Isolation correction (same day):** the source repository was discovered to be a Git worktree whose `.git` file points into `gula-platform/.git/worktrees/gula-integration`. The initial `cp -a` preserved that pointer, so branch changes made from the execution copy also changed the source worktree HEAD. This was corrected by registering a separate worktree metadata directory (`gula-platform/.git/worktrees/gula-v4-execution`) for the execution copy, copying the baseline index into it, and restoring the source worktree HEAD to `integration/gula-unification-v1`. Final verification: source branch `integration/gula-unification-v1`, source status `705 untracked / 162 modified / 20 staged`, staged name-status MD5 `56c524d6ffe9872c3a3ac6eff8c8f203`; execution branch `execution/gula-national-v4`, same staged name-status MD5. No source file content or staged content was changed.

No destructive Git operation was used: no `reset --hard`, `clean`, `restore`, `stash`, force push, history rewrite, or deletion of untracked files.

## 2. Preserved mixed provenance

The execution copy was verified to contain the same Git state as the source:

- staged paths: **20** (all R100 renames)
- unstaged tracked paths: **162**
- untracked paths: **705**
- total status entries: **887**
- staged name-status MD5: `56c524d6ffe9872c3a3ac6eff8c8f203`

The source repository was not modified when the execution copy was created.

## 3. Integrity verification

| Check | Result |
|---|---|
| V2 additive manifest | `18/18 OK`, `0 FAILED` |
| V4 source snapshot manifest | `23/23 OK`, `0 FAILED` |
| `FINAL_DECISION.md` MD5 | `effdfeaf10234678d83b2668c4489552` |
| `MPI_FINAL_INDEPENDENT_AUDIT.md` MD5 | `1a02c01563c93b07a7cdb92c0462bf36` |
| `MPI_INDEPENDENT_AUDIT_FINDINGS.md` MD5 | `ea3969d09aaf7b0b28a065838b44a594` |
| `status_registry.json` | `production_ready_items = 0` preserved |

Snapshot manifest: `AUDIT_EXECUTION_RECORDS/V4_EXECUTION_SOURCE_SNAPSHOT_SHA256.txt`.

## 4. Rollback

The original source repository remains a byte-level restore point. To discard all V4 execution work, delete the execution workspace and continue from the untouched source repository. No merge into the source branch or into `gula-platform` is performed by this directive.

## 5. Authority boundary

This workspace implements engineering work under the V4 mandate. It does not declare Stable v1.0.0, does not lift HOLD, does not authorize production deployment, and does not use PHI, production services, provider/financial calls, or external network access.
