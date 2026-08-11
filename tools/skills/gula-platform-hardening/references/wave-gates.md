# GULA Wave Gates

## Preflight

| Gate | Evidence |
|---|---|
| Repository state | branch, HEAD, remote, worktrees, status, certified commits, concurrent work |
| Governance | constitution, architecture rules, wave approval, HARD STOP scope |
| Source of truth | runtime, auth, account, policy, API, frontend, mobile, data, integrations |
| Change scope | explicit file list; legacy/concurrent files protected |

## Identity Wave 3

| Gate | Required evidence |
|---|---|
| Mapping | legacy kind/key → canonical key, organization/tenant context, role/verification provenance |
| Reversibility | rollback marker, idempotent batch, collision report, no destructive merge |
| Security | cookie/refresh/CSRF tests, revocation, permission version, object/tenant negative tests |
| Data | ACID transaction, optimistic version, no silent conflict, audit before/after |
| Rollout | feature flag, cohort, dual-read comparison, mismatch audit, kill switch |

## Dependency triage

For every advisory record manifest, package, installed/fixed versions, severity, reachability, runtime/CI path, compatibility impact, patch evidence, and exception expiry. Audit all lockfiles and package ecosystems. Never close a GitHub alert because a local audit omitted its manifest.

## Delivery

Run focused tests, full applicable suites, compile/type/lint/build, dependency audits, secret scan, migration fresh-build, `git diff --check`, and performance smoke. Stage explicit paths, inspect cached diff, commit a single wave, push a review branch, verify remote SHA, and report failures and residual risks.
