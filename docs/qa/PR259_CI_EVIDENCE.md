# PR #259 — CI Failure Evidence

Investigation-only. No CI workflow was modified, no full test suite was run,
no reruns were triggered as part of producing this document (one rerun
attempt, and one PR comment, were already made in the prior turn before this
directive arrived — restated in §6 for completeness, not repeated here).

Tags: **VERIFIED** (read directly from workflow source, job metadata, or a
local reproduction run this pass), **INFERRED** (a conclusion from VERIFIED
evidence, not itself directly provable from what's accessible),
**UNKNOWN** (no evidence found, access blocked), **BLOCKED** (needs
access/action this session doesn't have).

Head commit under investigation: `550c67d13d0ff1284c722e550e7c8947ec1c5512`
(Phase 9's architecture doc commit). PR: `samertts/gula-platform#259`,
base `main` @ `46158e90`.

---

## 1. Which workflows/checks failed

**VERIFIED** — 23 check runs reported `conclusion: failure` on this head,
spanning at least 11 structurally distinct workflow files (matched by
reading each workflow's `name:`/job `name:` against the failing check names):

| Check name(s) | Workflow file | Run ID |
|---|---|---|
| Syntax Gate | `ci.yml` | 35527691114 |
| Constitution Compliance (PROGRAM-CONSTITUTION-001) | `constitution-compliance.yml` | 35527691113 |
| Backend identity unit and compile gates, PostgreSQL migration and schema gate, Security and tenant isolation regression, Frontend v3 contract/type/build gates | `iam-hardening.yml` (4 jobs, 1 workflow, 1 run) | 35527691149 |
| Ruff Format (Python), Prettier (TypeScript/JSON/MD) | `formatting.yml` (2 jobs, 1 run) | 35527691195 |
| Analyze (python), Analyze (javascript-typescript) | `codeql.yml` and/or `codeql-analysis.yml` — **two separate CodeQL runs appeared** (35527691158 and 35527691189), consistent with both `codeql.yml` and `codeql-analysis.yml` existing as separate, possibly-duplicate workflow files (VERIFIED both files exist; not resolved which run belongs to which file in this pass) | 35527691158, 35527691189 |
| Dependency Review | `security-hardening.yml`'s `dependency-review` job **and/or** `dependency-review.yml` — two separate runs appeared (35527691142, and one bundled with Secret Scan/Python Dependency Audit under 35527691181), same duplicate-workflow caveat as CodeQL | 35527691142, 35527691181 |
| Secret Scan, Python Dependency Audit (backend/requirements-lock.txt), Python Dependency Audit (nhop-platform/requirements.txt), Python Dependency Audit (edge_agent/requirements.txt) | `security-hardening.yml` (matrix job + secret-scan job, 1 run) | 35527691181 |
| Ruff/MyPy changed-files non-regression | `quality-changed-files.yml` | 35527691146 |
| quality-gate | `quality-gate.yml` | 35527691139 |
| preview | `preview-deploy.yml` | 35527691167 |

All 23 `check_run.completed` events arrived within `2026-09-20T18:01:05Z`
–`18:01:12Z` (a 7-second window), immediately following the push that
produced `550c67d1`.

## 2. Whether jobs actually executed meaningful steps

**VERIFIED, for the two jobs whose timing was checked against the GitHub
Actions job API:**
- `Syntax Gate` (job `106122624252`, run `35527691114`): `created_at`/
  `started_at` = `18:01:05Z`, `completed_at` = `18:01:08Z` — **3 seconds
  total**, for a job whose defined steps are: checkout, `setup-python`
  (Python 3.12), two inline Python syntax-check scripts, and a `flake8`
  invocation that itself first `pip install`s flake8.
- `Backend identity unit and compile gates` (job `106122624365`, run
  `35527691149`, workflow `iam-hardening.yml`): same `18:01:05Z` →
  `18:01:08Z`, 3 seconds — for a job whose defined steps are: checkout,
  `setup-python` with a pip cache, `pip install -r backend/requirements.txt
  -r backend/requirements-dev.txt` (dozens of packages including
  `sqlalchemy`, `fastapi`, `cryptography`), a `ruff check` over
  `backend/app/identity`, a `pytest` run over the identity/clinical-gateway
  test suites, a `compileall`, and an artifact upload.
- **INFERRED, not proven**: a `pip install` of a multi-package
  `requirements.txt`/`requirements-dev.txt` pair, even served entirely from
  a warm pip cache, is not normally a sub-second operation, and the pytest
  step alone (collecting and running a real test suite) is very unlikely to
  complete inside a 3-second job budget that also has to fit checkout and
  Python setup. This is a structural/timing inconsistency, not direct proof
  of *where* the job stopped — see the explicit caveat below.
- **Explicit caveat, not glossed over**: `pip install` **can** fail near-
  instantly if dependency resolution hits an unsatisfiable constraint
  before any download begins, so a 3-second failure is not automatically
  proof that the job died before reaching that step. This was checked
  directly rather than assumed away: `backend/requirements.txt` and
  `backend/requirements-dev.txt` were not observed to have been modified in
  the commits that produced this PR's head (this session's own commits
  touched only `docs/`, `backend/app/{hospital_service.py,routes/hospital.py,
  nhdw/*,nursing/*,lims/*}`, and `scripts/*` — no requirements file), which
  makes an install-time dependency conflict introduced by this branch
  **unlikely but not independently disproven** for this specific job.
- **Not checked this pass, for the other 21 failing checks**: no other
  job's per-job start/complete timestamps were pulled (time budget), so the
  "steps couldn't have executed" inference above is **verified only for
  the two jobs named**, not generalized to all 23 without further evidence.

## 3. Where in the pipeline failures occurred

**UNKNOWN for all 23 checks, and stated as such rather than guessed.**
Both available diagnostic paths were attempted and both are blocked:
- `mcp__github__get_job_logs` (both by `job_id` and by `run_id` +
  `failed_only`) returned `HTTP 404` for every job tried (`106122624252`,
  and all 4 jobs in run `35527691149`) — log content is not retrievable
  with this session's GitHub token.
- `pull_request_read` with `method: get_status` (combined commit status)
  returned `HTTP 403 Resource not accessible by integration` — this
  session's token also cannot read commit-level combined status.
- `get_check_run` was tried for `Syntax Gate`, `Backend identity unit and
  compile gates`, and `Constitution Compliance` — all three returned an
  **empty** `output.summary`/`output.text`/`output.title`. This is expected
  behavior for a plain GitHub Actions check run (only custom GitHub Apps
  populate `output` text; Actions relies on the job log instead), so the
  empty result is not itself evidence of anything beyond "this API doesn't
  carry the detail for an Actions-native check" — noted so the empty result
  isn't mistaken for a finding.
- No `steps` breakdown (per-step conclusion/timing) was returned by
  `get_workflow_job` for the jobs queried — whatever step-level detail the
  underlying GitHub API may expose was not surfaced by the available tool,
  so step-level attribution (checkout vs. Python setup vs. dependency
  install vs. command execution vs. test execution vs. artifact/reporting)
  is **UNKNOWN, not inferred**, for every one of the 23 checks.

Per this phase's explicit instruction, this is recorded as **UNKNOWN**
rather than resolved by inference from timing alone.

## 4. Whether downstream failures are consequences of an upstream failure

**VERIFIED, but narrower in scope than it might first appear.**
`ci.yml`'s own `needs:` graph (read directly from the workflow file) has
`data-preservation-gate`, and (per the job list pulled for run
`35527691114`) `Backend Tests`, `Lint`, `Migration Check`, and
`Security Scan` all depend, directly or transitively, on `syntax-gate`.
Querying that run's job list confirmed all five of those jobs show
`conclusion: skipped` — **not** `failure` — which is why they do **not**
appear among the 23 failing checks at all. This is a real, source-verified
cascade, but it explains an *absence* of separate failures within `ci.yml`,
not a shared cause across the other ~10 independent workflow files.
**Cross-workflow, there is no `needs:` relationship at all** — `ci.yml`,
`iam-hardening.yml`, `constitution-compliance.yml`, `formatting.yml`,
`security-hardening.yml`, `quality-gate.yml`, `quality-changed-files.yml`,
`codeql.yml`, `codeql-analysis.yml`, `dependency-review.yml`, and
`preview-deploy.yml` are separate GitHub Actions workflows, each triggered
independently by the same `pull_request` `synchronize` event; nothing in
any of their `on:`/`jobs:` definitions makes one depend on another. So the
23 failures cannot be explained as *one* upstream failure cascading via
`needs:` — if they share a cause, it is not a dependency-graph cause, but
something common to how/when/where each of these otherwise-independent
workflows executed.

**VERIFIED, as the one concrete structural commonality found:** every
workflow file read this pass (`ci.yml`, `iam-hardening.yml`,
`constitution-compliance.yml`, `formatting.yml`, `security-hardening.yml`,
`quality-gate.yml`, `quality-changed-files.yml`, `codeql.yml`,
`preview-deploy.yml`) opens its first (or an early) job with the identical
pinned action reference `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`.
This SHA was independently verified (`git ls-remote
https://github.com/actions/checkout
3d3c42e5aac5ba805825da76410c181273ba90b1`) to resolve to real, currently-
existing tags (`refs/tags/v7`, `refs/tags/v7.0.1`) on the upstream
`actions/checkout` repository — **ruling out** "the pinned checkout
reference is dangling/deleted" as the mechanism, without ruling out a
transient failure *executing* that (valid) action at that specific moment
(rate limiting, a runner-provisioning failure, a GitHub Actions platform
incident — none of which this session's tools can directly confirm or
deny; see §3).
`setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97` and
`setup-node@820762786026740c76f36085b0efc47a31fe5020` were also checked via
the same method; both returned no result — **this is INCONCLUSIVE, not
negative evidence**: `git ls-remote <repo> <sha>` only resolves a bare
commit SHA when the remote advertises it as a ref (e.g. a tag), which an
arbitrary pinned commit that isn't itself tagged will not do, regardless of
whether it's valid. No conclusion is drawn from these two empty results.

## 5. Whether any actual test/lint/type-check command demonstrably failed

**VERIFIED — not for this exact commit, on the one check independently
reproduced:** `Syntax Gate`'s own documented logic (`.github/workflows/
ci.yml`, `syntax-gate` job) was executed locally against
`550c67d13d0ff1284c722e550e7c8947ec1c5512`, using Python 3.12 (matching
`ci.yml`'s pinned `env.PYTHON_VERSION: "3.12"` — explicitly *not* this
container's default Python 3.11, which would falsely report a syntax error
against this repo's pre-existing PEP 695 generic-class syntax in
`backend/app/clinical_gateway/contracts.py`, confirmed by running both
interpreters and comparing results):

- `compile()` over every `.py` file under `backend/app/` and
  `backend/migrations/` → 0 errors.
- `compile()` over every `.py` file under `services/`, `nhop-platform/`,
  `edge_agent/`, `shared/` (mirroring the job's second script exactly,
  including its `__pycache__`/`node_modules` skip and zero-byte-file skip)
  → 0 errors.
- `flake8 backend/app/ --select=E9,F --ignore=F401,F841 --count` (the
  job's exact third step) → `0`.

This is the only one of the 23 failing checks whose actual documented
command was reproduced end-to-end locally this pass. **It demonstrably did
not fail on content.** No other failing check's actual command (Ruff
Format, Prettier, the two CodeQL analyses, Dependency Review, the three
Python Dependency Audits, Constitution Compliance's enforcer script,
Quality Gate's YAML validation, the changed-files Ruff/MyPy gate, the
IAM Hardening Gate's other three jobs, or the frontend build) was
reproduced locally this pass — for all of those, **whether their actual
command would have failed on this commit's content remains UNKNOWN**, not
assumed clean by association with Syntax Gate's result.

One targeted, cheap check was made on a check named specifically in this
phase's context: `nhop-platform/requirements.txt` (the manifest for one of
the three failing `Python Dependency Audit` matrix legs) was read directly
— it is well-formed (11 pinned/floor-bounded package specifiers, valid
`pip` requirement syntax, no parse errors visible) and not obviously
malformed. **A full `pip-audit` resolution against it was not run** (would
require live dependency resolution against PyPI within this session's
scope/time budget), so whether it contains an actual flagged vulnerability
remains **UNKNOWN**, not cleared.

---

## 6. Prior-turn actions (restated for the record, not repeated here)

Before this directive arrived, the prior turn already: posted one comment
on PR #259 documenting the timing observations available at that point,
attempted `rerun_failed_jobs` on all 11 distinct run IDs (all returned
`403 Resource not accessible by integration` — this session's token cannot
trigger reruns either), and scheduled a 60-minute check-in. Per this
phase's instruction not to trigger reruns automatically, **no further
rerun was attempted in producing this document** — the one rerun attempt
already on record stands as the only one made.

---

## CI STATUS

**UNKNOWN.**

Not `VERIFIED FAILURE` — the one check fully reproduced (`Syntax Gate`)
demonstrably does not fail on this commit's actual content under the
correct runtime, which is direct evidence against a real regression for
that check specifically.

Not `VERIFIED PASS` — 22 of 23 failing checks were not independently
reproduced; their content-level correctness on this commit is unverified,
not assumed.

Not `INFRASTRUCTURE FAILURE` — that classification is reserved by this
phase's own instruction for a *concretely proven* case, and this
investigation could not obtain job logs, step-level timing, or combined
commit status (404/403/empty-output at every attempted access point) to
prove *where* any of the 23 jobs actually failed. The evidence gathered
(near-simultaneous failure across 11 structurally-independent workflows
sharing one identical, verified-valid checkout action; one check's
documented logic demonstrably clean on this content; job durations
inconsistent with their defined steps for the two jobs timed) is
suggestive of a shared, non-content cause, but "suggestive" is explicitly
not the bar this phase set. Recorded honestly as **UNKNOWN** rather than
stretched into a stronger claim.

## Files

- Created: `docs/qa/PR259_CI_EVIDENCE.md` (this file).
- No other file created or modified. No workflow file changed. No rerun
  triggered in producing this document (the one prior-turn rerun attempt,
  which failed with 403, is not repeated).
