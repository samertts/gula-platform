# Final CI verification — PR #307

Verified commit: `a406cde1f991cd5cbb23676a7606ce1fcb600450`  
Observation command: `gh pr checks 307`  
Raw output: `pr_checks_final_nc013.log`  
Result: **23 PASS / 6 FAIL** (29 checks total). CI is **not green** and is not treated as acceptance.

## Checks that now PASS after the CI-fix commit

| Check                                                           | Evidence                                                                               |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Backend identity unit and compile gates                         | run `44771751763`, job `136410929246` — PASS (previously failed on missing `greenlet`) |
| Security and tenant isolation regression                        | run `44771751763`, job `136410929885` — PASS (previously failed on missing `greenlet`) |
| Secret Scan                                                     | run `44771751586`, job `136410929429` — PASS (`no leaks found`)                        |
| PostgreSQL migration and schema gate                            | run `44771751763`, job `136410929659` — PASS                                           |
| Python Dependency Audit (backend lock / edge_agent / nhop)      | three runs under `44771751586` — PASS                                                  |
| Ruff/MyPy changed-files non-regression                          | run `44771752112`, job `136410930029` — PASS                                           |
| Security Scan, Syntax Gate, Lint, Data Preservation Gate        | run `44771751653` — PASS                                                               |
| CodeQL, Analyze (python ×2), Analyze (javascript-typescript ×2) | PASS                                                                                   |

## Remaining 6 failures — all pre-existing or out of scope

| Check                                              | Exact observed cause                                                                                                              | Disposition                                                                                                                           |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Backend Tests                                      | `app.blood_bank.exceptions.BloodBankWorkflowError: Invalid transfusion transition: verified -> in_progress`                       | NC013-C05; reproduced on untouched baseline; clinical owner decision required                                                         |
| Constitution Compliance (PROGRAM-CONSTITUTION-001) | `AttributeError: module 'ast' has no attribute 'Str'` on Python 3.14; also `git diff failed (base=origin/main)` in CI checkout    | Tool/runtime defect, pre-existing; local diff-mode audit found no secret/vendor-lock-in/paid-dependency violation introduced by NC013 |
| Frontend v3 contract, type and build gates         | `TestingLibraryElementError: Unable to find an accessible element with the role "button" and name "Open all sections"`            | No frontend file changed by NC013                                                                                                     |
| Migration Check                                    | `alembic upgrade head` OK; `alembic downgrade -1` → `ERROR [alembic.util.messaging] Ambiguous walk`                               | Pre-existing three-parent baseline head `20260908_0001`                                                                               |
| Prettier (TypeScript/JSON/MD)                      | `config/runtime-protection/seccomp-profile.json: SyntaxError: Unexpected token, expected "," (11:1)` plus pre-existing docs/files | All 18 NC013 files pass local Prettier 3.10.1 check; remaining items pre-existing                                                     |
| Ruff Format (Python)                               | repository-wide `ruff format --check` reports 1,012 files needing reformat                                                        | Pre-existing; whole-repo reformat out of NC013 scope                                                                                  |

## PR state

`gh pr view 307 --json number,state,isDraft,url,headRefOid,mergeable` → `pr=307 state=OPEN draft=true sha=a406cde1f991cd5cbb23676a7606ce1fcb600450 mergeable=MERGEABLE url=https://github.com/samertts/gula-platform/pull/307`.

`mergeable=MERGEABLE` is only GitHub's structural assessment. The PR remains a **draft**, CI is red, no human approval exists, and no merge or deployment is authorized.

The repository's Vercel integration also reported an automatic preview deployment (`Vercel ... Deployment has completed`). This is a preview generated by the existing PR webhook, not a production release, and was not initiated as a deployment action by this program.
