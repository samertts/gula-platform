# Database & Migration Readiness Report

**Repository:** `gula-integration`, branch `integration/gula-unification-v1`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**Date / environment:** 2026-11-19; disposable SQLite only for the new step-up migration test; no DDL on any operational DB.
**Status vocabulary:** `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`. No `PRODUCTION READY` awarded.

## 1. Step-up migration (this execution) — `TESTED`

| Check | Result |
|---|---|
| Revision | `20261119_0001_niam_step_up_events`, `down_revision = 20261118_0001`, single Alembic head, 98-revision chain |
| Upgrade on disposable `tmp_path` SQLite (via `MigrationContext`/`Operations`) | `niam_step_up_events` created with account/session/JTI/method/fingerprint/timestamp columns and `uq_niam_step_up_account_code` |
| Downgrade on same disposable DB | table removed cleanly |
| Additivity | New table only — no existing table or column altered |

The test imports the migration module directly and runs `upgrade()`/`downgrade()` against a throwaway
SQLite file. It does not use `create_all()` and does not `stamp()` over an unapplied revision.

## 2. Platform-wide migration readiness — `BLOCKED` (pre-existing, unchanged)

Authoritative sources: `GOVERNANCE/DATABASE_COMPATIBILITY_REPORT.md`,
`GOVERNANCE/MIGRATION_RECONCILIATION_MATRIX.md`, `GOVERNANCE/DATABASE_OWNERSHIP_MATRIX.md`,
`GOVERNANCE/PHASE_C_DATABASE_REHEARSAL_REPORT.md`, and `GOVERNANCE/EXECUTION_LEDGER.md` §4.

Open blockers (not introduced or fixed by this work item):

- **NR-011 (P0) — RESOLVED IN CODE (status corrected 2026-11-19, fresh Wave 0 verification):** the
  blocker no longer reproduces. `migrations/env.py` now registers all 17 declarative bases, imports
  `app.national.domain`, and merges them into one `MetaData`; cross-metadata `ehr_allergies →
  national_patients` FKs resolve. Evidence: `pytest tests/unit/test_nr011_metadata_discovery.py
  tests/unit/test_fk_target_integrity.py -q` → **19 passed, EXIT=0** (see `GOVERNANCE/WAVE_0_BASELINE.md`
  §2). The remaining ADR-A scope is the unmigrated-table backlog, not NR-011 itself.
- **ORM↔schema gap:** 340 ORM table slots absent from migrated schema; 82 tables missing 664 columns;
  3 downgrade-residual tables have ambiguous ownership (ADR-B).
- **W1 strict-schema gate:** 753 passed / 119 failed on a disposable PG16 Alembic-only clone
  (all schema-induced) vs 872/872 under the SQLite `create_all()` control.
- `MIG-EXISTING` remains PARTIAL / NOT MET; `downgrade 20260815_0022` is a silent partial reversal.

## 3. Rules observed

No DDL against an operational database; no `create_all()` to hide gaps; no `stamp()` to bypass an
unexecuted migration; no migration replay or interruption test against a real environment; no test
deleted or weakened. All new evidence is from synthetic disposable data.

## 4. Care-continuum FK-closure migration `20261119_0003` — `INDEPENDENTLY VERIFIED` (engineering scope, fresh-context Team C)

New uncommitted revision `backend/migrations/versions/20261119_0003_care_continuum_closure.py`
(`down_revision = 20261119_0002`, single head) plus regression test
`backend/tests/migrations/test_care_continuum_closure_migration.py`.

- **Gap closed:** all 45 `cc_*` care-continuum ORM tables (1,706 columns, 249 FKs, 467 indexes) had
  ZERO migration coverage. True missing set derived from actual DB state at prior head = **62 tables
  (45 `cc_*` + 17 `national_*` FK-dependency targets)**; `national_facilities` already existed from
  `20260813_0004` and was correctly excluded. This reduces the §2 unmigrated-table backlog by 62;
  the broader ADR-A backlog remains.
- **Additive + reversible:** 62 `create_table` / 62 `drop_table`, 619 `create_index` / 619
  `drop_index`; no existing table, column, constraint, permission or API contract altered; no data
  migration, no `create_all()`, no fake stamp; idempotency guard skips cleanly when all targets exist.
- **Enum fix:** 24 shared native PG enum types are created by idempotent `CREATE TYPE` DO blocks and
  dropped with `DROP TYPE IF EXISTS`; every one of the 44 enum columns renders as
  `postgresql.ENUM(..., create_type=False)` (generic `sa.Enum` silently ignores `create_type` and
  caused a prior `type "gender" already exists` failure). Labels match ORM definitions exactly.
- **Authoritative lifecycle (disposable PG16, unique throwaway DB):** fresh `upgrade head` →
  `downgrade -1` → re-`upgrade head` passes with `45 cc + 17 national` target tables and 24 enum
  types after each upgrade, 0 after downgrade (`RESULT=OK`, EXIT=0, reproduced 4×). Synthetic-data
  probes confirmed FK, UNIQUE and enum-value rejection.
- **Regression tests:** 7 static parity tests + 1 opt-in DB lifecycle test → **8 passed, EXIT=0**
  (7 passed / 1 skipped when `GULA_CC_MIGRATION_ADMIN_DB_URL` is unset). Ruff clean; `py_compile`
  OK; whitespace/`git diff --check`/secret-PHI scan clean.
- **Team C finding (fresh-context, `VERDICT: BLOCKED`):** one reproducible **P1** defect — the ORM
  declares `national_encounters.referral_id → national_referrals.id` with `use_alter=True` to break a
  mutual FK cycle, but Alembic's `create_table()` silently skips such FKs, so 301 of 302 declared
  FKs existed and a bogus `referral_id` was accepted. **Fixed** by an explicit
  `op.create_foreign_key(...)` after both tables exist and a symmetric `op.drop_constraint(...)` in
  downgrade; regression tests now assert full live/declared FK-count parity, the specific FK's
  presence, and rejection of a bogus referral on a real migrated table. Two P2 residuals (enum guard
  checks only type name; 125 ORM-inherited duplicate indexes) are documented — neither triggered in
  this chain.
- **Team C re-verification (fresh-context, 2026-11-19):** `VERDICT: INDEPENDENTLY VERIFIED`
  (engineering scope) — report `/tmp/opencode/teamc_cc_reverify_report.md`. Checks A–G PASS: live FK
  parity 302 declared = 302 live, specific FK present with `ondelete=SET NULL`, bogus referral
  rejected, downgrade/re-upgrade clean with 0 pre-existing objects lost, both idempotency guards
  verified, no new defect; reverting the fix in a `/tmp` copy made the two new P1 guards fail
  (2 failed / 6 passed), proving the regression tests non-vacuous. The award was issued by Team C,
  not self-awarded; `PRODUCTION READY` is not awarded. This closes the "45 `cc_*` tables lack
  migrations" finding in `MASTER_EXECUTION_STATUS.md` §2 row 9 at the migration level; runtime
  service-integration evidence is still `BLOCKED`.

**Final decision:** step-up migration `TESTED`; care-continuum closure migration `INDEPENDENTLY VERIFIED`
(engineering scope, fresh-context Team C re-verification; `PRODUCTION READY` not awarded);
platform-wide readiness `BLOCKED` pending ADR-A/B, operational restore drills and owner decisions.
No production claim. Git SHA: `2206654dc713ea2de8c564a3207dfe05fde23549`.
