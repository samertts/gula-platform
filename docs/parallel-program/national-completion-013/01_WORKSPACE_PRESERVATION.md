# 01 — Workspace Preservation — GULA-NATIONAL-COMPLETION-013

## Scope

Prove that `/home/samertts/workspace/projects/gula-platform` was not modified, reset, switched, stashed, cleaned, or otherwise interfered with, and that all program work occurred in `/tmp/opencode/gula-national-completion-013`.

## Methodology

Read-only Git commands (`status`, `rev-parse`, `remote`, `worktree list`, `stash list`) plus process/resource observation. No write command, `git checkout`, `reset`, `clean`, `stash`, `switch`, `merge`, `rebase`, `cherry-pick`, `pull`, or `push` was executed in or from the protected directory. The clone was created from the remote using SSH after confirming the target path did not exist.

## Environment

See `00_EXECUTIVE_BASELINE.md`. Protected workspace is one of six worktrees of the same repository; all were left untouched.

## Commands and exit codes

Commands are preserved verbatim in `evidence/p00_collect.sh`; output in `evidence/p00_preservation_manifest.txt`. All exit codes were 0.

| Measurement | Before engineering | After clone/branch creation |
|---|---|---|
| Branch | `remediate-security-001` | `remediate-security-001` |
| HEAD | `f478676b6fc375338648dde46fbf076c015a3f91` | unchanged |
| `status --porcelain -uall` SHA-256 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | unchanged |
| Remote | `ssh://git@ssh.github.com:443/samertts/gula-platform.git` | unchanged |
| Worktrees | 6 (one prunable) | unchanged |
| Stashes | 2 | unchanged |
| Running processes | Docker/PostgreSQL/Redis/Ollama/OpenCode were observed, not touched | unchanged |

## Evidence paths

- `evidence/p00_collect.sh`
- `evidence/p00_preservation_manifest.txt`

## Findings

- **PRES-01 — INFO — No protected-workspace mutation detected.** All measured invariants remained identical.
- **PRES-02 — LOW — Upstream of active branch is gone.** `[gone]` is reported by Git; this is pre-existing and was not “fixed” by fetching or retargeting.
- **PRES-03 — LOW — Concurrent processes exist.** PostgreSQL/Redis containers and OpenCode processes were running. They were not stopped, restarted, or used without isolation.

## Verification state

`RECONCILED` — preservation verified for the observed window. This is not a guarantee against external concurrent activity outside this program.

## Limitations

- Preservation was measured at discrete checkpoints, not continuously.
- A concurrent process could change the protected tree between checkpoints; the program performs a fresh check at each major phase for this reason.

## Residual risks

- External work in the same repository may continue; no program action may assume earlier status remains valid.

## Required actions

Re-run `evidence/p00_collect.sh` after every major phase and diff against the initial manifest. Stop if branch, HEAD, status hash, remotes, worktrees, or stashes change without an external explanation.
