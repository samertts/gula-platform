# 00 — Executive Baseline — GULA-NATIONAL-COMPLETION-013

**Date:** 2026-11-20  
**Program:** GULA-NATIONAL-COMPLETION-013  
**Baseline:** `main` @ `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`  
**Isolated workspace:** `/tmp/opencode/gula-national-completion-013`  
**Protected workspace:** `/home/samertts/workspace/projects/gula-platform`  
**Working branch:** `execution/gula-national-completion-013`

## Scope

This document records the authoritative starting point for the program. It covers the protected-workspace preservation check, isolated clone creation, GitHub source-of-truth discovery, historical evidence availability, toolchain discovery, and the program baseline decision.

## Methodology

1. Read-only inspection of the protected workspace before any engineering operation.
2. Full SSH clone of `samertts/gula-platform` into a new dedicated directory after confirming the directory did not exist.
3. GitHub REST API inventory via `gh api` (branches, PRs, workflows, runs, releases, tags, protection).
4. Read-only review of historical evidence available in `/home/samertts/workspace/projects/gula-integration`.
5. Tool discovery using `--version`/`list` commands only.

## Environment

- Linux / WSL2, 2 vCPU, 3.8 GiB RAM, 159 GiB free disk.
- Python 3.10.12 / 3.11 / 3.12 available; backend declares Python ≥3.12, device bridge declares ≥3.10.
- Node v24.18.0, npm 11.16.0, Docker 29.1.3, Docker Compose 2.40.3.
- Free/open-source toolchain only: pytest 9.1.1, Ruff 0.15.21, MyPy 2.2.0, Bandit 1.9.4, pip-audit 2.10.1, Semgrep 1.168.0, Trivy 0.72.0, Ollama (`llama3`, `nomic-embed-text`), local PostgreSQL/Redis containers.
- No commercial software or paid external service introduced. Free alternatives were evaluated by the repository's Cost Governance Constitution; this program adds no paid dependency.

## Commands and exit codes

| Command | Exit | Result |
|---|---:|---|
| `git -C /home/samertts/workspace/projects/gula-platform status --porcelain=v1 -uall \| sha256sum` | 0 | `e3b0c442…b855` (clean) |
| `git ls-remote --symref ssh://git@ssh.github.com:443/samertts/gula-platform.git HEAD refs/heads/main` | 0 | `main` = `2ee9e8bc…` |
| `git clone ssh://git@ssh.github.com:443/samertts/gula-platform.git /tmp/opencode/gula-national-completion-013` | 0 | Full clone, 150 branch refs including remotes |
| `gh api repos/samertts/gula-platform/branches/main/protection` | 1 | HTTP 404 — branch not protected |
| `gh api --paginate '.../branches?per_page=100'` | 0 | 148 branches, none protected |

Full raw preservation output: `evidence/p00_preservation_manifest.txt`.

## Evidence paths

- `evidence/p00_collect.sh`
- `evidence/p00_preservation_manifest.txt`
- `01_WORKSPACE_PRESERVATION.md`
- `02_GITHUB_REPOSITORY_INVENTORY.md`
- `03_BRANCH_AND_PULL_REQUEST_GRAPH.md`
- `04_UNIFIED_FINDINGS_REGISTER.md` and `evidence/unified_findings_register.json`

## Findings

- **P00-01 — MEDIUM — Baseline not green.** `main` has 14 failing check runs; Nightly Build has repeated `startup_failure`; branch protection is absent. This is an inherited baseline condition, not introduced by this program.
- **P00-02 — MEDIUM — Prior isolated workspace missing.** `/tmp/opencode/gula-isolation-eval` does not exist; the previous verification report set cannot be re-read from disk. The conversation checkpoint and governance reports remain available as historical context and are marked as such.
- **P00-03 — HIGH — Numbered predecessor artifacts absent.** The exact program IDs 005/008/009/010/012 are not present as files/directories in the previous local worktree; equivalent unnumbered governance evidence exists and is cited with exact paths.
- **P00-04 — HIGH — No safe wholesale PR baseline.** All inspected PR heads are stale/diverged and have failing checks; #240/#247 are conflicted. PRs are treated as patch sources only.

## Verification state

- WORKSPACE PRESERVATION: `RECONCILED`
- BASELINE SELECTION: `RECONCILED`
- RELEASE READINESS: `HUMAN APPROVAL REQUIRED`

## Limitations

- Historical reports referenced only in the conversation checkpoint cannot be independently re-opened; they are not treated as primary filesystem evidence.
- GitHub Actions billing/account-level state was not fully determinable from the API; workflow-run failures are recorded as observed.
- No production access, deployment, or patient data was used.

## Residual risks

- Starting from an unprotected, non-green `main` means any delivery must regenerate its own evidence and cannot inherit CI credibility.
- Divergent PRs may contain fixes not present on `main`; selective reuse is required and must be revalidated.

## Required actions

1. Maintain the protected workspace manifest after every major phase.
2. Implement narrowly scoped, real fixes on the isolated branch.
3. Regenerate tests and scans on the final combined head.
4. Record all human approvals as external blockers; never fabricate them.
