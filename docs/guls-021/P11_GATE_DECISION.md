# P11 — Gate Decision

Program: GULA-GULS-021
Branch: `execution/gula-guls-021` in `/tmp/opencode/gula-guls-021`
Date: 2026-11-21
Status: **NOT READY — BLOCKED**

## 1. Decision rule

A merge or production gate may pass only when every coherent gate in the table below is green. A failure in any hard gate blocks promotion. Pre-existing failures may be documented as not caused by this change, but they do not turn a red aggregate gate green. No approval, merge, deployment, or Draft PR is inferred from a partial pass.

## 2. Gate matrix

| Gate                                         | Requirement                                                                          | Evidence                                                                                                                                                          | Result                                           |
| -------------------------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| G1 — Correction implementation               | C1, H1–H4, M1–M3, M7–M9 applied with regression coverage                             | `FINAL_ACCEPTANCE_REPORT.md` §2; 81 focused backend tests pass on 3.11 and 3.12                                                                                   | **PASS**                                         |
| G2 — Backend static checks                   | Touched Python compiles; Ruff lint clean                                             | `py_compile` exit 0; `ruff check` exit 0                                                                                                                          | **PASS**                                         |
| G3 — Python formatting                       | `ruff format --check` clean for touched files                                        | exit 1 for `pack_manager.py`; Ruff 0.16.10 with `target-version=py314` rewrites valid 3.11/3.12 syntax                                                            | **FAIL**                                         |
| G4 — Frontend scoped checks                  | Typecheck, lint, Prettier, focused tests pass                                        | All scoped commands exit 0; 3 files, 21 tests pass                                                                                                                | **PASS**                                         |
| G5 — Full frontend suite                     | `npm test` green                                                                     | GULS-021: `2 failed                                                                                                                                               | 76 passed (78)`tests, exit 1; baseline:`2 failed | 54 passed (56)` tests, exit 1 | **FAIL** |
| G6 — CI / merge gate                         | PR checks green; merge state stable                                                  | `gh pr checks 308`: 10 failing required-style checks plus the generic `test` job (11 failing rows); `mergeStateStatus=UNSTABLE`; baseline runs reproduce failures | **FAIL**                                         |
| G7 — Native build verification               | Android, iOS, desktop targets buildable and exercised                                | `gradle`, `swift`, `xcodebuild`, `flutter`, `dotnet` = `NOT_FOUND`; only `java` present                                                                           | **FAIL**                                         |
| G8 — Human linguistic and clinical approvals | Documented approval for script/community choices, L3/L4 clinical catalogs, and fonts | No human approval recorded; `tk`/`syr` script choices remain human-blocked; clinical catalogs remain gated                                                        | **FAIL**                                         |
| G9 — Dynamic-pack client integration         | UI and native clients can discover, download, verify, and activate packs             | Web runtime module exists, but no UI installation flow; Android/iOS/Flutter/adjacent clients have no GULS pack integration                                        | **FAIL**                                         |
| G10 — Residual state risks                   | M4/M5/M6 resolved or accepted by an explicit production design decision              | Shared preference key/no ETag, per-process state, and unsigned local state remain residual                                                                        | **FAIL**                                         |
| G11 — Key management                         | Production signing key generated, protected, rotated, and approved                   | Only ephemeral test keys used; synthetic path restricted and startup-refused in production/staging                                                                | **FAIL**                                         |
| G12 — Preservation                           | Protected workspace, PR #307, and PR #308 unmodified; branch preserved               | Protected workspace SHA-256 unchanged; PR states unchanged; no force-push/reset                                                                                   | **PASS**                                         |
| G13 — Secret hygiene                         | No secrets in the diff                                                               | Secret scan exit 0, no matches                                                                                                                                    | **PASS**                                         |

## 3. Applied decision

Because gates G3, G5, G6, G7, G8, G9, G10, and G11 fail, the coherent green-gate condition is not satisfied. The final status is therefore:

> **NOT READY — BLOCKED**

This status is authoritative and matches `FINAL_ACCEPTANCE_REPORT.md`. It is not a statement of national readiness, merge readiness, or production readiness.

## 4. Consequential actions

- **Draft PR:** not opened. A stacked Draft PR would imply that the coherent gates passed; they did not.
- **Branch:** `execution/gula-guls-021` is preserved in `/tmp/opencode/gula-guls-021` with the corrections and documentation. No force-push, destructive reset, or deletion was performed.
- **PR #308:** remains OPEN, draft, `mergeable=MERGEABLE`, `mergeStateStatus=UNSTABLE`, `mergedAt=null`. It was inspected only.
- **PR #307:** remains OPEN draft and untouched.
- **Protected workspace:** unchanged at branch `remediate-security-001`, HEAD `f478676b6fc375338648dde46fbf076c015a3f91`, 6 worktrees, 2 stashes, status SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- **Human approvals:** none requested, granted, or fabricated by this program.

## 5. Re-entry criteria

The gate may be reconsidered only after all of the following are evidenced:

1. CI is green on the target branch and the full frontend suite passes.
2. The Ruff/py314 formatting conflict is resolved without breaking Python 3.11/3.12 runtime compatibility.
3. Native Android, iOS, and desktop build gates are executed in an environment with the required toolchains.
4. Documented human linguistic, community, and clinical approvals are recorded for all previously blocked identifiers and catalogs.
5. Dynamic-pack UI and native client integration are implemented and tested.
6. M4/M5/M6 are resolved with shared-state and key/state integrity designs, or explicitly accepted by authorized operators.
7. Production signing key management is established and approved.

Until then, the decision remains **NOT READY — BLOCKED**.
