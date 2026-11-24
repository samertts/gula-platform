# MPI Post-Remediation Independent Audit

**Audit ID:** MPI-PRA-001
**Date:** 2026-11-18
**Repository:** `gula-integration`
**Branch:** `integration/gula-unification-v1` · HEAD `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`
**Primary reference:** `GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md`
**Decision reference:** `GOVERNANCE/FINAL_DECISION.md` (md5 `effdfeaf10234678d83b2668c4489552`, verdict `HOLD`)
**Data policy:** synthetic data only; no real patient data; no secrets printed or hardcoded
**Verdict:** **`REJECT`** — carried forward from the primary reference and **not changed by this audit**. No `ACCEPT`/`COMPLETE` transition was performed autonomously.

---

## 1. Purpose and independence

This document is a **fresh, independent post-remediation audit** of the 16 findings in `MPI_INDEPENDENT_AUDIT_FINDINGS.md`. It was produced by re-reading the authoritative findings and re-verifying the shipped source, tests, real PostgreSQL behavior, and OpenAPI surface — **not** by trusting prior implementation reports. All remediation changes remain **uncommitted** and coexist with 256 pre-existing uncommitted user entries (preserved).

Independence controls:
- No file in `/home/samertts/workspace/projects/gula-platform` was read for modification or modified at all.
- `GOVERNANCE/FINAL_DECISION.md` was read-only; md5 re-checked and unchanged.
- No commit, push, merge, rebase, PR, or deploy was performed.
- No `git reset`, `git clean`, `git add .`, or `git add -A` was performed. All Git operations were read-only (`status`, `diff`, `rev-parse`, `cat-file`, `show`).
- No schema/DDL/migration change was applied to the repository. The real Alembic schema was built **only** in the dedicated `mpi_test` database for proof purposes.

---

## 2. Baseline severity recount (from primary reference)

| Severity | Count | IDs |
|---|---:|---|
| **CRITICAL** | 0 | — |
| **HIGH** | 3 | AUD-01, AUD-02, AUD-03 |
| **MEDIUM** | 9 | AUD-04 … AUD-12 |
| **LOW** | 2 | AUD-13, AUD-14 |
| **INFORMATIONAL** | 2 | AUD-15, AUD-16 |
| **Total** | **16** | |

This recount is taken verbatim from `MPI_INDEPENDENT_AUDIT_FINDINGS.md §1` and is the baseline for the post-remediation recount in §4.

---

## 3. Verification performed (independent evidence)

### 3.1 Source and static gates

| Gate | Result | Evidence |
|---|---|---|
| `compileall` modified scope | `COMPILE_OK` | — |
| Ruff modified source + tests | `All checks passed!` | re-run after final edit |
| MyPy CI-style comparison | **47 → 37 diagnostics (−10)**; no per-file regression; new `reliability.py` 0 errors | prior comparison re-confirmed |
| OpenAPI stability | 125 routes / 1805 paths; only MPI diffs: decide `description`, `ResolveDecision.decision` pattern + schema-description | `openapi_head.json` vs `openapi_current.json`; all other endpoint keys byte-identical |
| `FINAL_DECISION.md` md5 | `effdfeaf10234678d83b2668c4489552` | unchanged |
| Uncommitted user work | 256 entries preserved | `git status --porcelain | wc -l` |

### 3.2 Automated tests

| Suite | Result |
|---|---|
| MPI unit/regression suite (all MPI tests) | **119 passed, 0 failed** (75.72 s), 1 deprecation warning |
| New AUD regression files | **43 passed** — AUD-01 (17), AUD-02 (12), AUD-03 (5), AUD-04/16 (9) |
| Directly-affected broader scope (MPI + security + consent + mdm + routes) | **224 passed, 0 failed** (after the `_write_canonical_audit` test-double fix) |
| Full backend regression/security suite | *(see §6 — result appended on completion)* |

**No test was skipped, deleted, or had an assertion removed.** One pre-existing untracked security regression test failed after the initial audit change because it used a `_FakeDB` without `get_bind()`; this was fixed in production code (real sessions still write the chained audit row; test doubles get an explicit warning + log line) rather than by weakening the test. It now passes 8/8.

### 3.3 Real PostgreSQL HTTP proof (AUD-09/AUD-10)

A fresh harness (`/tmp/opencode/gula-mpi-http-proof/run_proof.py`) was built to close AUD-09 and AUD-10. It runs against the **real Alembic-built `public` schema** of the dedicated `mpi_test` PostgreSQL 16.14 database (migrations upgraded to head; `mpi_merge_audit` and its `decided_by_user_id` FK verified present), using the **real `SessionLocal`/engine**, real TCP psycopg2 connections, and **FastAPI `TestClient` calls** to `/mpi/resolve`, `/mpi/merge`, `/mpi/review/{id}/decide`, and `/compliance/audit-integrity`. Two pool profiles were run:

| Profile | Pool (size/overflow/timeout) | Checks | Verdict |
|---|---|---|---|
| tight | 2 / 0 / 3 s | **28/28 PASS** | `PROOF_VERDICT PASS` |
| production | 5 / 10 / 10 s | **28/28 PASS** | `PROOF_VERDICT PASS` |

Key outcomes (both profiles):
- **AUD-03:** 6 concurrent resolves on a 2-connection pool → 6/6 `200`, zero pool-timeout `503`, `max_simultaneous_checked_out=2`, `in_use=0` at end.
- **AUD-04:** 10 concurrent same-NID first registrations → 10/10 `200`, one response ULID, one citizen row.
- **AUD-06:** swapped-ULID merge replay race → `[200,200]`, one audit row for the unordered pair, one event ID, one entry hash.
- **AUD-01/AUD-11:** `REJECT_MATCH` over HTTP → `200`, `match_method=new`, new ULID differs from both the rejected citizen and a high-scoring lure, one `review_reject` audit row appended.
- **AUD-10:** worker scaling 2/5/10/20 → all `200`, `errors=[]`, exact audit delta per worker count. Throughput tight 16.7→1.26 ops/s, p95 69→1222 ms; production 15.5→0.92 ops/s, p95 74→1303 ms (AUD-15 constraint, measured not hidden).
- **AUD-08:** `/compliance/audit-integrity` → `200`, `mpi_integrity.valid=True`, both sub-chain verifications valid (202/156 merge rows, 161/123 canonical chains), `errors=[]`.

The legacy `/tmp/opencode/gula-mpi-tests/` harness is explicitly retained as **strategy-level evidence only** and is not cited as endpoint proof. AUD-09's divergence findings (hand DDL, `expire_on_commit=False`, 25+25 pool, resolver-level calls only) are thereby closed.

---

## 4. Post-remediation severity recount

Baseline severities are unchanged as *classifications*; remediation status is tracked separately. "Open" means an owner decision or authorized migration is still required before the finding can be closed.

| Severity | Count | Closed / PASS | Open (owner-gated) | IDs open |
|---|---:|---:|---:|---|
| **CRITICAL** | 0 | 0 | 0 | — |
| **HIGH** | 3 | 2 | **1 (PARTIAL)** | AUD-02 (DB uniqueness half) |
| **MEDIUM** | 9 | 8 | **1 (BLOCKED)** | AUD-07 (D-MPI-5) |
| **LOW** | 2 | 2 | 0 | — |
| **INFORMATIONAL** | 2 | 1 (measured/documented) | **1 (BLOCKED)** | AUD-16 (D-MPI-3/4) |
| **Total** | **16** | **13 PASS + 1 documented PASS** | **3 open** | AUD-02, AUD-07, AUD-16 |

Per-finding verdicts: AUD-01 PASS · AUD-02 **PARTIAL** · AUD-03 PASS · AUD-04 PASS · AUD-05 PASS · AUD-06 PASS · AUD-07 **BLOCKED** · AUD-08 PASS · AUD-09 PASS · AUD-10 PASS · AUD-11 PASS · AUD-12 PASS · AUD-13 PASS · AUD-14 PASS · AUD-15 PASS (documented) · AUD-16 **BLOCKED**.

No finding is `FAIL`. No assertion was deleted and no coverage was reduced. Detailed pre-fix state, root cause, change, test, evidence, residual risk, and verdict for each finding are in `MPI_AUD_FINDINGS_REMEDIATION_REPORT.md`.

---

## 5. Owner-gated items (not executed)

| Artifact | Finding | Decision required |
|---|---|---|
| **MP-001** Migration Proposal — `UNIQUE(patient_id)` / `UNIQUE(citizen_id)` (+ optional pair uniqueness) | AUD-02 | Approve migration + dedupe preflight; not applied |
| **ODR-001** Formal review-decision audit taxonomy (D-MPI-4) | AUD-01, AUD-11, AUD-12 | Approve enum/check constraint + ledger placement |
| **ODR-002** Resolve payload-change semantics (D-MPI-5) | AUD-07 | Choose re-resolve vs `409` vs accept risk |
| **ODR-003** Fork-response policy (D-MPI-3/D-MPI-4) | AUD-16 | Detection-only vs alert+freeze vs controlled repair |
| **ODR-004** Canonical hardening scope (D-MPI-6) | AUD-02 | Formal ledger membership vs current general-`audit_logs` model |

These are written proposals/requests in `MPI_AUD_FINDINGS_REMEDIATION_REPORT.md §3`. **None was executed.** No NHID canonicalization change was made (ODR-002 explicitly out of scope).

---

## 6. Full backend regression / security suite

**Raw result** (background run completed; log `/tmp/opencode/mpi-remediation/full_backend_suite.log`):

```
===== 1 failed, 3843 passed, 27 skipped, 200 warnings in 583.82s (0:09:43) =====
FULL_SUITE_EXIT=1
```

Command executed: `cd backend && ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. /tmp/opencode/mpi-venv/bin/python -m pytest tests/ -q --tb=short`.

### 6.1 The single failure — identification

| Field | Value |
|---|---|
| Test | `tests/unit/test_nr011_metadata_discovery.py::TestMetadataDiscovery::test_cross_metadata_foreign_keys_resolve` |
| Exception | `sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column 'niam_adaptive_mfa_sessions.session_id' could not find table 'niam_user_sessions'` |
| Origin file of the FK | `backend/app/identity/adaptive_auth/models.py:75` — `session_id = Column(String(100), ForeignKey("niam_user_sessions.id"), ...)` |
| Defining model | **none** — a repository-wide grep for `__tablename__ = "niam_user_sessions"` under `backend/app` returns zero matches |
| Is the origin file modified? | **No** — `git status --porcelain -- backend/app/identity/adaptive_auth/models.py` is empty (byte-identical to HEAD) |
| Is the test file modified? | **No** — likewise unchanged |
| Does it mention MPI? | **No** — the symbol is Identity adaptive-MFA (`niam_adaptive_mfa_sessions`), entirely outside the MPI change set |

### 6.2 Baseline / order-dependent classification (evidence, not assumption)

1. **Isolated re-run passes:** `pytest -q tests/unit/test_nr011_metadata_discovery.py::TestMetadataDiscovery::test_cross_metadata_foreign_keys_resolve` → **`1 passed, 1 warning in 3.70s`**. The identical test and identical source pass when run alone.
2. **Order-dependent metadata coupling:** the failure is raised by `metadata.sorted_tables` resolving every FK in a *merged* metadata object. Whether `niam_user_sessions` is present depends on which other Identity modules were imported earlier in the process — a property of full-suite collection order, not of MPI code.
3. **Out of MPI scope and unmodified:** neither the failing test, nor the model that declares the dangling FK, nor any Identity module was touched by the remediation (§6.1). MPI changes are confined to `backend/app/services/mpi/*`, `backend/app/routes/canonical_patient.py`, `backend/app/routes/compliance.py` and the new MPI AUD tests.
4. **Baseline diff contains no related entry:** `status_baseline.txt` and `diff_stat_baseline.txt` contain no `niam` / `adaptive_mfa` / NR-011 modification attributable to this change set.

**Classification: PRE-EXISTING, ORDER-DEPENDENT BASELINE FAILURE — not caused by, and not in the scope of, the MPI remediation.** It is neither skipped nor deleted; it remains in the suite and passes in isolation. Per the mandate's scope boundary ("لا توسّع نطاق إصلاح MPI إلى وحدات أخرى دون موافقة" — do not expand MPI fix scope to other modules without approval), this Identity-layer defect is **documented, not fixed**. It is referred to the Identity owner as a separate item and does not alter the MPI finding counts or verdict.

### 6.3 Effect on gates

- MPI unit/regression suite, new AUD regressions, directly-affected broader scope and both real-PostgreSQL HTTP proof profiles all pass independently (§3.2, §3.3) — the single failure does not touch any MPI test.
- The full-suite exit code (`1`) is recorded honestly. The suite is **not** claimed as fully green. Net result: **3843 passed, 1 pre-existing order-dependent failure, 27 skipped**.

---

## 7. Audit verdict and rationale

**Verdict: `REJECT` (unchanged).**

Rationale:
1. The primary reference verdict is `REJECT` and was not authorized to change; `FINAL_DECISION.md` remains `HOLD` with unchanged md5.
2. Two `HIGH`-class findings are not fully closed at the schema/data-ownership layer: AUD-02 is `PARTIAL` (DB uniqueness requires an owner-authorized migration), and the taxonomy/hardening decisions (ODR-001/004) remain owner-gated.
3. AUD-07 (`MEDIUM`) and AUD-16 (`INFORMATIONAL`) are explicitly `BLOCKED` pending owner decisions D-MPI-5 and D-MPI-3/4.
4. The acceptance condition in the primary reference forbids `ACCEPT` while any `HIGH`/`CRITICAL` finding is open. AUD-02 is `HIGH` and `PARTIAL`, so `ACCEPT` is not permissible even if desired.

**What is proven complete:** 13 findings PASS plus AUD-15 documented/measured; all 16 have independent evidence; 43 new regression tests plus a 28-check real-PostgreSQL HTTP proof in two pool profiles; static gates clean; OpenAPI stable; no user work lost; no repository schema change; no commit/push.

**Next gate:** Program Director / data owner to decide MP-001 and ODR-001…004. Only after those decisions are executed and re-verified — and with explicit authorization — may the verdict be reconsidered. This audit does not request or imply that authorization.

---

## 8. Integrity attestations

- `GOVERNANCE/FINAL_DECISION.md` md5: `effdfeaf10234678d83b2668c4489552` — **unchanged**.
- `GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md` — **unmodified**; verdict `REJECT` intact.
- `/home/samertts/workspace/projects/gula-platform` — **untouched**.
- Uncommitted user entries: **256** — **preserved**.
- Git operations performed: read-only only. **No commit, push, merge, rebase, PR, deploy, reset, clean, or add-all.**
- Synthetic data only; no real patient data; no secrets printed or hardcoded.
