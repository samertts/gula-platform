# P-02 / AUD-F02 — fresh independent review (2026-11-24)

Reviewer: independent read-only subagent, fresh context.
Baseline: HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`, branch
`integration/gula-unification-v1`.
Scope reviewed: `backend/app/routes/ai.py` P-02 hunk and
`backend/tests/test_p02_critical_alert_audit_postgres.py`.
No files were edited by the reviewer; no post-review code changes were made.

## Verdict

**DECISION-READY**

Findings: **0 CRITICAL · 0 HIGH · 0 MEDIUM · 2 LOW**.
The two LOW findings are non-blocking residuals recorded below. They were not
remediated after review so that this verdict remains valid for the exact code
that was reviewed.

## 1. REV3 option (a) conformance

| Required check | Result | Evidence |
|---|---|---|
| Canonical writer | PASS | `ai.py:662-674` calls `log_action(...)`; direct `AuditLog(...)` construction removed; action/resource/role/details preserved as a dict. |
| `db.commit()` retained immediately after `log_action` | PASS | `ai.py:675` directly follows the call; session close at `:958` cannot discard the row (R7). |
| Deterministic `lab_id` | PASS | `ai.py:661` resolves `LabOrder.lab_id` by order id and passes it at `:667`; no order resolves to `None`, no fabricated value. |
| Guarded rollback, no masked error | PASS | `ai.py:678-681` logs rollback failure; bare `raise` at `:682` preserves the original exception (R3). |
| Fail-closed before AI call | PASS | Caller waits for the audit executor at `ai.py:951-958` before the provider call at `:962`; R5 proves the provider mock stays uncalled. |

`contextlib` removal is correct. `AuditLog` and `json` imports remain legitimately
used by the read-side query at `ai.py:826-838`.

## 2. Scope and provenance

No P-02 behavior change exists outside `_emit_critical_alert`, its two imports and
the `contextlib` removal. The `require_ai_operator` import and `/operations`,
`/providers` dependency additions are disjoint pre-existing mixed-provenance work;
they do not touch `/interpret/{token}` or the audit helper. No schema, migration,
dependency, protected-file or SHA-registry change is attributable to P-02.

Non-finding: `GULA_CHANGE_PROVENANCE_RESOLUTION_REPORT.md` §2.2 attributes A1/A5/A6
in `ai.py` (`log_action` import, docstring, canonical-writer conversion) to WS-2
`AUDIT-BYPASS-001`; this hunk extends that work with `lab_id`, guarded rollback and
re-raise. Ownership overlap must be resolved at the separate staging-scope decision
required by owner directive §9.

## 3. RED/GREEN and R1–R7

- RED archive `app/routes/ai.py` MD5 `b19bb6faa7a4330de3f995957646a63e` equals
  `git show HEAD`; the test file copied into the archive is byte-identical to the
  working-tree file.
- RED: **6 failed / 2 passed**, exit 1. GREEN: **8 passed**, exit 0.
  Related suites: **224 passed / 9 skipped**, exit 0.
- The suite enforces disposable PG16, database `gula_int_gate`, Alembic head
  `20261119_0003`, `read committed`, required columns and both append-only triggers
  before assertions. `pytestmark` skips without `GULA_P02_PG_DSN`; no SQLite path,
  provider call, PHI value or production service is used.
- R1–R5 and R7 fail at HEAD and pass in the working tree. R6 passes at HEAD by
  design (packet §6 marks it N/A at HEAD) and passes GREEN with two chained rows;
  this is disclosed and is not a defect.
- Ruff: HEAD 4 findings → worktree 3, zero new; new test file clean. Strict MyPy
  normalized delta identical; new test file clean. `git diff --check` exit 0.
  `ai.py` formatter failure is pre-existing and unchanged.

## 4. Low-severity residuals (accepted, non-blocking)

### LOW-1 — stale “Non-fatal” wording

- Location: `backend/app/routes/ai.py:649` docstring; pre-existing caller comment at
  `:948` repeats the wording.
- Evidence: the helper now re-raises and the endpoint aborts (proved by R5).
- Impact: misleading maintenance/operational documentation only; no runtime effect.
- Disposition: accepted as a non-blocking documentation residual. The pre-existing
  caller comment belongs to separate provenance; both should be corrected in a
  later scoped documentation edit, not here.

### LOW-2 — explicit `lab_id=None` branch not directly asserted

- Location: `backend/tests/test_p02_critical_alert_audit_postgres.py:187-198`.
- Evidence: R4 asserts the resolvable-order case only; the no-order fallback at
  `ai.py:661,667` is not separately regression-tested.
- Impact: the no-fabrication branch lacks a dedicated guard.
- Disposition: accepted as a non-blocking test-coverage residual. No post-review
  changes were made so this verdict remains valid for the reviewed bytes.

## 5. Status statement

This review awards no `ACCEPTED`, `PRODUCTION READY`, commit, push, PR, merge,
release or deployment authorization. HOLD remains TRUE, `production_ready_items = 0`,
Stable v1.0.0 is NOT DECLARED, and PRODUCTION READY is NOT AUTHORIZED.
