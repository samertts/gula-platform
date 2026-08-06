# Commit 0.0 Verification Report

**Commit:** `d6574f8e` — `chore(repository): establish pre-migration baseline`
**Branch:** `remediate-security-001`
**Date:** 2026-08-06

This report is the permanent verification record for the baseline commit and for the
test-infrastructure root-cause fix applied immediately after it (both are the immutable
starting point for the Phases 0–2 migration).

---

## 1. Final Test Summary

| Suite | Result |
|---|---|
| Complete backend suite (`pytest tests/`, clean env) | **4865 passed / 0 failed / 148 warnings** in 1253.46 s |
| Parity file (historically hung) | 36 passed in 102.46 s |
| Service subset A/B/C (semantics + determinism) | 95 passed ×3 (identical) |

## 2. Build Status

- Backend `compileall`: **PASS** (exit 0)
- `tsc --noEmit`: **0 errors**
- ESLint: **0 errors**
- `vite build`: **PASS** in 5.12 s
- `pip check`: **clean**

## 3. Architecture Gate

`scripts/architecture.py check` → **PASS** (exit 0): Shared Core scan **57 findings
(57 acknowledged, 0 new)**; domain certification **11/11 (isolation PASS)**;
country-agnostic scan **PASS**.

## 4. Constitution Gate

`scripts/domains.py check` → **PASS** (exit 0): **11/11 certification, isolation PASS**.
Constitution gate (`architecture-gate`) is wired as a HARD gate in `.github/workflows/ai-governance.yml`.

## 5. Baseline Metrics (verified)

| Metric | Value |
|---|---|
| Tracked files / dirs | 6,311 (+1 gitlink) / 1,352 |
| Python LOC | 478,082 (3,111 files) |
| TS+TSX LOC | 133,480 |
| Ruff (backend/app) | 379 (E402 167 / N801 141 / N999 71) |
| OpenAPI paths | 1,699 unique (0 dup) |
| Top-level routes | 126 |
| Migrations | 56 |
| Full-suite wall clock | 20:53 (WSL2) |
| Peak RSS | ~448 MB |
| `create_all` | ~40 s after fix (was ~112 s) |

Full table in `docs/baselines/PRE_MIGRATION_BASELINE.md`.

## 6. Root-Cause Summary

The historical pytest hang was a **test-infrastructure I/O stall**, not a test or app
bug: the file-backed SQLite `_session_engine` in `tests/conftest.py` issued ~1,300 DDL
statements with an fsync per statement (default rollback journal) on the WSL2 virtual
disk. Evidence: faulthandler SIGABRT dump pinned the block at `create_all → visit_index →
do_execute` (conftest.py:161); live process showed `D`-state with a `.db-journal` file;
timing probe measured `create_all` at 112 s.

## 7. Permanent Fix Summary

`tests/conftest.py`: a `connect` event listener sets `PRAGMA journal_mode=MEMORY` and
`PRAGMA synchronous=OFF` on the test session engine. SQLite lock/transaction semantics
are unchanged; the disk-journal fsync path is removed. A/B + determinism verification
(95 passed ×3, identical outcomes) confirms no change to test semantics, transaction
behavior, isolation guarantees, or result determinism.

## 8. Remaining Known Limitations

- Alembic `sys.path` bootstrap missing (`shared` import fails without `PYTHONPATH=..`);
  root `alembic.ini` shadows `backend/alembic.ini`; PG unreachable at `localhost:5432`.
- Startup-guard 15× DB retry when `DATABASE_URL` unset (non-test boots only).
- WSL2 disk latency dominates suite runtime (20:53 vs ~10 min on faster hardware).
- MyPy times out on full backend (not a gate).
- 148 warnings (SAWarning FK-cycle on `drop_all`, OpenAPI duplicate op id — pre-existing).
- Dormant contexts `ai/`, `nhop-platform/`, `edge_agent/` slated for archiving in Commit 1.4.

## 9. Rollback Readiness

- Conftest fix: `git checkout d6574f8e -- backend/tests/conftest.py` (A/B-verified).
- Baseline docs: additive; lossless to remove.
- Whole baseline: `git revert` (no schema/data/API changes).

## 10. Verdict

**GREEN.** All hard gates pass; complete suite green; the previously-hanging pytest
environment is deterministic. Ready to proceed to **Commit 0.1** (dormancy registry +
ADR-014 + 10th certification check + tests) — **pending explicit user approval**.
