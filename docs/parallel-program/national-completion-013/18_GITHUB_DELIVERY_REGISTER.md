# 18 — GitHub Delivery Register — GULA-NATIONAL-COMPLETION-013

## Scope

Record all local commits, pushes, and pull requests created by this program.

## Methodology

Delivery is permitted only after the change is implemented in the isolated workspace, relevant to GULA, free of secrets/PHI, tested for its modified scope, documented, and not creating an unresolved critical regression. No force-push, branch deletion, history rewrite, merge to `main`, or deployment is permitted.

## Environment

Repository `samertts/gula-platform`; local branch `execution/gula-national-completion-013`; remote via SSH.

## Commands and exit codes

```bash
git -C /tmp/opencode/gula-national-completion-013 checkout -b execution/gula-national-completion-013
# exit 0
git -C /tmp/opencode/gula-national-completion-013 rev-parse HEAD
# 2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa at branch creation
```

## Evidence paths

- `evidence/implementation_log.md`
- `01_WORKSPACE_PRESERVATION.md`

## Findings

- DEL-01 — RESOLVED — Branch pushed and draft PR created (see delivery record below).
- DEL-02 — HIGH — `main` is unprotected; delivery must not rely on CI status inherited from baseline.
- DEL-03 — INFO — Two independent adversarial passes completed; all discovered code gaps closed and re-validated.
- DEL-04 — HIGH — Governance approvals remain `BLOCKED`; PR #307 is a **draft** and no merge/deployment is authorized.
- DEL-05 — HIGH — NC013-C05 (pre-existing transfusion transition failure) remains open and requires a clinical workflow owner decision.
- DEL-06 — INFO — GitHub reported 384 pre-existing Dependabot vulnerabilities on the default branch at push time (20 critical, 194 high, 142 moderate, 28 low); not introduced by this program.
- DEL-07 — RESOLVED — CI `Secret Scan` initially failed on a gitleaks `generic-api-key` false positive in `14_SECURITY_SCAN_AND_SBOM.md` line 5 of docs commit `5079d67d` (phrase "dependency/vulnerability"). A targeted stopword was added and the sentence rephrased; the re-run reports `no leaks found`, exit 0.
- DEL-08 — MEDIUM — CI `Ruff Format (Python)` fails repo-wide: 1,012 files need reformat. Pre-existing and unrelated to NC013; `ruff check` on changed files passes.
- DEL-09 — HIGH — CI identity, security/tenant-isolation and backend-test jobs failed because `backend/requirements.txt` omitted `greenlet` although the app imports `sqlalchemy.ext.asyncio`. FIXED by declaring `greenlet>=3.5.5` (MIT, free/open source, already pinned in `requirements-lock.txt`).
- DEL-10 — HIGH — CI `Migration Check` passes `alembic upgrade head` but fails `alembic downgrade -1` with `Ambiguous walk`. Baseline head `20260908_0001` already has three parents; pre-existing, not introduced by NC013.
- DEL-11 — MEDIUM — CI `Constitution Compliance` crashed on Python 3.14 at `ast.Str`; a local diff-mode audit found four pre-existing/scope-limited rule failures (duplicate-code heuristic, quality-gate/py_compile on 3.12-only syntax plus tool timeout, aggregate rule, dead-code heuristic). No secret, vendor-lock-in, paid-dependency or SaaS violation was introduced.
- DEL-12 — MEDIUM — CI Prettier fails on a pre-existing JSON syntax error and pre-existing files; all 18 NC013 markdown/JSON files were formatted with Prettier 3.10.1 and now pass locally.
- DEL-13 — INFO — Frontend v3 test failure (`Open all sections`) is in unchanged frontend code; pre-existing.
- DEL-14 — INFO — Environment restart removed the first isolated clone. It was recreated from the pushed branch at `a5c2a0de7bdf73a2aad4801a64c2df5aef49a684`; no approved work was lost and the protected workspace stayed unchanged.

## Delivery record

| Item                           | Value                                                                                                                              |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| Branch                         | `execution/gula-national-completion-013`                                                                                           |
| Base                           | `main` @ `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`                                                                                |
| Implementation commit          | `05c8fd870745a06fea41230cfe98d2b90501d957` — `feat(program-013): remediate critical clinical and identity defects`                 |
| Documentation/CI-fix commits   | `7174873477b26585998728317b193dcd5df44131`, `fa50f839fe904fc916c5bbacd3fee536d6a4c2a9`, `a5c2a0de7bdf73a2aad4801a64c2df5aef49a684` |
| Ancestor commit                | `5079d67d` — `docs(program-013): establish protected baseline and unified findings register`                                       |
| Initial pre-push fetch         | exit 0; `origin/main` unchanged; ahead 2 / behind 0; remote branch absent                                                          |
| Initial push                   | `git push -u origin execution/gula-national-completion-013`, exit 0, new branch                                                    |
| PR head at last verified check | `a5c2a0de7bdf73a2aad4801a64c2df5aef49a684`                                                                                         |
| Pull request                   | #307 — OPEN, `isDraft=true`                                                                                                        |
| PR URL                         | https://github.com/samertts/gula-platform/pull/307                                                                                 |
| Merge / deployment             | **None. Not authorized.**                                                                                                          |

Commands and raw outputs: `evidence/test_logs/prepush_fetch.log`, `push_nc013.log`, `pr_create_nc013.log`, `push_final_nc013.log`, `push_ci_fix_nc013.log`, `fetch_main_ref_final.log`, `ci_failure_triage.md`. Current head must be confirmed with `gh pr view 307 --json headRefOid` after any subsequent docs-only commit.

## Verification state

`HUMAN APPROVAL REQUIRED` for any merge to `main`. Delivery gates evaluated before push:

| Gate                              | Evidence                                                                                                                   | Result                                                        |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Isolated implementation           | clone at `/tmp/opencode/gula-national-completion-013`, branch `execution/gula-national-completion-013`                     | PASS                                                          |
| Relevant GULA scope               | targeted backend fixes in identity, LIMS, migrations, gateway, dependencies                                                | PASS                                                          |
| No secrets/PHI                    | Trivy secret scan 0 secrets; verifier grep no hits; synthetic data only                                                    | PASS                                                          |
| Tests pass                        | 22 focused (3.12), 17 focused (3.10), 471 regression, migration graph 3; full suite has one pre-existing NC013-C05 failure | PASS for NC013 scope                                          |
| Docs updated                      | all 22 phase docs + evidence log + register updated and Prettier-formatted                                                 | PASS                                                          |
| No unresolved critical regression | two independent passes; all discovered code gaps closed and re-validated; NC013-C05 pre-existing and escalating            | PASS with documented exception                                |
| Base/dependencies understood      | base `2ee9e8bc…`, ahead 5 / behind 0, lock upgraded and re-audited, `greenlet` dependency gap closed                       | PASS                                                          |
| No concurrent-work overwrite      | `git fetch origin refs/heads/main:refs/remotes/origin/main` exit 0; `origin/main` unchanged                                | PASS                                                          |
| Exact commit/evidence recorded    | implementation `05c8fd87…`, PR #307 draft, raw logs preserved                                                              | PASS                                                          |
| CI green                          | several failures; see `ci_failure_triage.md`                                                                               | **FAIL — pre-existing/scope-limited; not a release approval** |

A draft PR is the maximum authorized delivery. No merge, release promotion, or deployment.

## Limitations

- CI is not green. Failures were triaged in `evidence/test_logs/ci_failure_triage.md`; only the secret-scan false positive and the `greenlet` dependency omission were within the reachable scope.
- A repository-wide formatting audit (1,012 Python files) and repository-wide Prettier failures are outside NC013 scope.
- The isolated clone was recreated after an environment restart; all pushed work was preserved, and no protected-workspace mutation occurred.

## Residual risks

- Concurrent pushes could conflict; fetch/compare must be performed immediately before any push.
- Pre-existing CI failures could mask future regressions until the repository is stabilised.

## Required actions

After each verified coherent commit, record branch, commit SHA, files, tests, results, limitations, and next action. Push only when gates are satisfied.
