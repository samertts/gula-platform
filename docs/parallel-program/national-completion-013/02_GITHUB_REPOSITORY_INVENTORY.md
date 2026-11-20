# 02 — GitHub Repository Inventory — GULA-NATIONAL-COMPLETION-013

## Scope

Repository-wide read-only inventory of `samertts/gula-platform`: metadata, default branch, branches, PRs, issues, workflows, runs, releases, tags, and branch protection.

## Methodology

`gh api` with pagination and `jq` formatting. No clone, checkout, push, PR creation, merge, or settings change. The repository inventory agent's command list is reproduced in `evidence/github_inventory_commands.md`.

## Environment

GitHub REST API, authenticated as `samertts` with `repo`, `workflow`, `gist`, `read:org` scopes. Git operations configured for SSH in the isolated clone.

## Commands and exit codes

| Command pattern | Exit | Key result |
|---|---:|---|
| `gh api repos/samertts/gula-platform` | 0 | Apache-2.0, public, not archived, size 69083 KB |
| `gh api repos/samertts/gula-platform/git/ref/heads/main` | 0 | `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa` |
| `gh api --paginate '.../branches?per_page=100'` | 0 | 148 branches; all `protected=false` |
| `gh api --paginate '.../pulls?state=open&per_page=100'` | 0 | 49 open PRs |
| `gh api --paginate '.../issues?state=open&per_page=100'` | 0 | 0 open non-PR issues |
| `gh api --paginate '.../actions/workflows?per_page=100'` | 0 | 35 active workflow entries |
| `gh api '.../actions/runs?per_page=50'` | 0 | Repeated Nightly Build `startup_failure`; Security Hardening failure |
| `gh api repos/samertts/gula-platform/branches/main/protection` | 1 | HTTP 404 — not protected |
| `gh api --paginate '.../releases?per_page=100'` | 0 | One draft release `v1.0.0-RC2` |
| `gh api --paginate '.../tags?per_page=100'` | 0 | `v2.1.0-engineering-factory`, `v1.0.0-RC2`, `v1.0.0-RC1` |

## Evidence paths

- `evidence/github_inventory_commands.md`
- `evidence/github_inventory_summary.json`
- `03_BRANCH_AND_PULL_REQUEST_GRAPH.md`

## Findings

- **GH-01 — HIGH — `main` is unprotected.** No required status checks or review requirements exist.
- **GH-02 — HIGH — `main` is not green.** 88 check runs at HEAD: 71 success, 14 failure, 2 skipped, 1 cancelled. Failures include Backend Tests, Migration Check, PostgreSQL migration/schema gate, Security and tenant isolation regression, Frontend v3 gates, Constitution Compliance, Prettier, Ruff Format, Secret Scan, Dependency Review, Python Dependency Audit, Build Linux, `foundation-ci`.
- **GH-03 — MEDIUM — 49 open PRs, none green.** Every requested PR head has failing checks; #240 and #247 are conflicted.
- **GH-04 — LOW — No open non-PR issues.** The public issue tracker is not an additional source of active defect tickets.
- **GH-05 — INFO — Only a draft release exists.** `v1.0.0-RC2` is draft with no published date.

## Verification state

`RECONCILED` for the observed API state; `HUMAN APPROVAL REQUIRED` for any branch-protection change or release declaration.

## Limitations

- Billing/account-level GitHub Actions blockers were not conclusively determined; observed failures are recorded without assuming their root cause.
- Dependency alerts were not fully enumerated here; scanner results are recorded separately.

## Residual risks

- Unprotected `main` can receive changes that bypass CI.
- Draft release artifacts are not authoritative release evidence.

## Required actions

Use `main` as implementation baseline only; regenerate all evidence on the final commit; do not claim CI success from PR descriptions.
