# GULA CI Truth

**Which workflows actually gate a pull request, and what "green" means.**

Generated from the workflow `on:` blocks, not from memory. Regenerate with
`scripts/enterprise_readiness/ci_truth.py`. Companion data: `GULA_CI_TRUTH.json`.

## 1. Why this document exists

PR #258 reported **6/6 checks green** while the pipeline containing the
2,766-test backend suite had never run on it. `ci.yml` triggers only on pull
requests into `main` or `staging`; #256, #257 and #258 target each other, so it
never fired. "Green" meant a narrow identity gate had passed. Recorded as
**MCM-P0-4**.

A count of passing checks is not a statement about coverage. This document
makes the three tiers explicit so that mistake cannot be made silently again.

## 2. The three tiers

### (a) PR checks — run on **every** pull request

| Workflow | What it actually runs |
|---|---|
| `iam-hardening.yml` | ruff on `app/identity` + `app/clinical_gateway`; pytest on `tests/identity`, `test_clinical_gateway_contracts`, `test_clinical_gateway_service`, `test_security_regression`, `test_tenant_isolation_matrix`, and 4 identity migration tests; `alembic upgrade head` + downgrade/re-upgrade; frontend-v3 contract/type/build |
| `frontend-bundle-budget.yml` | frontend bundle size budget |

**These two are the entire gate on a stacked PR.** Everything below is absent.

### (b) Full CI — runs only on PRs into `main` / `staging`

`ci.yml`: syntax-gate (`py_compile` + import walk + flake8 E9,F) → then
data-preservation-gate, migration-check (fresh postgres:17, upgrade + downgrade
round trip), lint (ruff + eslint + tsc + frontend build), **test** (clinical
safety regression subset, then `pytest tests/ -x`), security-scan (safety,
bandit), build-and-push (8 images + Trivy).

Also main-only: `quality-changed-files.yml`, `quality-gate.yml`,
`constitution-compliance.yml`, `formatting.yml`, `security-hardening.yml`,
`codeql.yml`, `codeql-analysis.yml`, `dependency-review.yml`,
`frontend-e2e.yml`, `frontend-pwa.yml`, `preview-deploy.yml`, the four
`mobile-*` workflows.

### (c) Not PR checks at all

`nightly.yml` (schedule), `foundation-gate.yml` (push to main / manual),
`scorecard.yml`, `sdk-publish.yml`, `release.yml`, and the deployment set —
`deploy.yml`, `blue-green-deploy.yml`, `canary-deploy.yml`, `rollback.yml`,
`auto-rollback.yml`, `staging-verify.yml`, `opt-in-pr-auto-merge.yml`.

**2 of 30 workflows gate every PR. 16 gate only PRs into a protected branch.
12 never gate a PR.**

## 3. Measured full-CI truth on this branch

`ci.yml` has never run on the stacked PRs, so its result was unknown rather than
green. Measured locally at `09935dff` + the BATCH-1 changes, against
postgres:17 migrated to `20260912_0001`:

| `ci.yml` job | Measured result |
|---|---|
| syntax-gate (flake8 `E9,F`) | **PASS** — ruff equivalent, exit 0 |
| lint (`ruff check backend/app/ --select=E9,F`) | **PASS** — exit 0 |
| migration-check | **PASS** — 106 revisions, single head, round trip |
| test → clinical safety regression gate | **PASS** — 30/30 |
| test → `pytest tests/` | **PASS** — 2,746 passed, 157 skipped, 0 failed |

**Full CI on this branch is now green.** It was RED on one clinical-safety test
until NR-020 was resolved: the transfusion state machine had no `verified`
state, so `start_transfusion_safely` — which requires `status == VERIFIED` and
targets `in_progress` — could never succeed. One key was added to the shared
transition table. The measurement above was taken after that fix; before it the
same run reported 1 failed, 2,743 passed.

## 4. The decision this leaves open

Making `ci.yml` run on stacked PRs is a one-line trigger change. It has **not
been made**, and it remains the repository owner's call: widening a trigger
changes which checks are required on three open PRs, which is merge policy.

What has changed is the risk of doing it. The blocker that made this a hard
choice is gone — full CI now measures green locally, so widening the trigger
would be expected to keep the stack green rather than turn it red. That is a
measurement on this branch at this commit, not a guarantee about the GitHub
runner, which differs in Python version, service containers and timing.

If you widen it, the honest expectation is: the stack stays green, and any red
that does appear is a real difference between this environment and CI's, worth
knowing about.

## 5. Gate states

`scripts/quality_changed_files_gate.py` distinguishes five states. A tool that
did not run can no longer be counted as clean (NR-016):

| State | Meaning |
|---|---|
| `PASS` | every tool ran; no regression against the baseline |
| `FAIL` | every tool ran; a regression was measured |
| `BLOCKED` | a tool did not run on one side or the other, so non-regression cannot be established. Exit 1, distinct from FAIL |
| `DID_NOT_RUN` | per tool: exited outside `{0, 1}` — no analysis produced |
| `UNMEASURED` | per tool: exited `0`/`1` but the result was unusable (e.g. unparseable output) |

`DID_NOT_RUN` and `UNMEASURED` report `diagnostic_count: null`, never `0`: a
zero would read as a measurement. Covered by 20 tests in
`scripts/tests/test_quality_changed_files_gate.py`.
