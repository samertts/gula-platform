# Current Engineering Baseline

Phase 1 of the "GULA — Master Engineering Closure Directive." Measures the
CURRENT repository state independently rather than copying numbers from
prior reports, then reconciles against what already exists. Per the
directive's own rule: a previous report saying "135→0" is not accepted at
face value — it is checked against the actual current source and git
history in this document.

## Scope note (read before anything below)

The Master Closure Directive and the Authorization Expansion directive
together specify a multi-week, whole-organization security/architecture/
authorization program (20+ phases, 9 capability-expansion batches, a
38-category production-readiness matrix rebuild) against a monorepo that
already carries **59 previously-dispositioned findings** in
`docs/engineering/MUSTAFA_ACTIVE_REPAIR_QUEUE.md` and **two existing,
evidence-based production-readiness matrices**
(`docs/qa/GULA_PRODUCTION_READINESS_GAP_MATRIX.md`,
`docs/architecture/PRODUCTION_READINESS_DELTA.md`). This document does not
re-fabricate that work. It: (1) independently re-measures the facts that
change turn-to-turn (git state, migration state, test counts, CI), (2)
reconciles the two things this session's own prior work directly changed
(NIAM sync/async closure) against what the existing reports assumed, and
(3) closes one concrete, previously-open, now-reproduced P1 as real,
proven, bounded work — rather than claiming to have executed all 20+
phases of both directives against a codebase this large in a single pass.
Continuing the remaining phases is a real, iterative next-step queue (see
end of this document), not a completed claim.

## BEFORE (what the existing reports state, as of their own writing)

From `docs/architecture/PRODUCTION_READINESS_DELTA.md` (predates this
session's NIAM lifecycle work):

> "Two real P1s remain open... `niam-broad-sync-db-mismatch` (94
> category-A + 41 category-F occurrences) and the unrelated pre-existing
> `pharmacy_drug_substitution_rules` migration defect... Overall
> classification: NOT Production Ready."

From `docs/engineering/MUSTAFA_ACTIVE_REPAIR_QUEUE.md`: 59 dispositioned
rows spanning RBAC tenant-scope (F5), nhop-platform trust boundary,
authorization-route ownership, tenant-scope mass-assignment sweep (32
candidates, fully triaged), Laboratory/Imaging/EMS/Nursing/NHDW vertical
slices (role gates, CAS/concurrency, audit-argument-order bugs), the
autonomous-repair-family inventory, and the Hospital-domain migration gap
(previously characterized as blocking only NHDW's own admission
queries, not the full alembic chain — see CURRENT MEASURED STATE below
for why that characterization is now known to be incomplete).

## CURRENT MEASURED STATE (this pass, independently verified)

**Git**
- Branch: `claude/mustafa-parallel-engineering`
- HEAD (at start of this pass): `a36b29f6` — "docs(security): NIAM
  sync/async closure engine final report — 135/135 closed"
- Working tree: clean at start; in sync with `origin/claude/mustafa-
  parallel-engineering`
- No force-push, no merge, no reset performed this pass

**Database / migrations**
- PostgreSQL 16 (disposable local cluster), Redis 7 — both required a
  restart this pass after a container/session reset (routine; no data
  loss, confirmed via `alembic_version`)
- `alembic heads`: **single head**, `20260908_0005` — no duplicate heads
- **NEW FINDING, reproduced against a real blank PostgreSQL 16 database**:
  a bare `alembic upgrade head` from an empty database does **not**
  currently reach head. It fails in two places, sequentially:
  1. `pharmacy_drug_substitution_rules`/`pharmacy_drug_substitution_requests`
     (migration `20260815_0023`): `original_drug_catalog_id`/
     `alternative_drug_catalog_id` were declared `String(26)` (both in the
     migration and in the ORM model, `app/pharmacy/models.py`'s
     `DrugSubstitutionRule`/`DrugSubstitutionRequest`) but
     `pharmacy_drug_catalog.id` (created by the earlier, already-
     successfully-deployed migration `20260716_0003`) is `Integer` —
     confirmed by grepping that same migration's own 14 other
     `drug_id`/`drug_id_a`/`drug_id_b` FK columns, all correctly declared
     `sa.Integer()`. This is an isolated copy-paste/inheritance-assumption
     bug (the author appears to have assumed every pharmacy entity uses
     the package's default ULID `String(26)` primary key, which is true
     for every OTHER pharmacy table but not for `pharmacy_drug_catalog`,
     whose PK predates and is Integer). **FIXED this pass** — see below.
  2. `hospital_surgical_safety_checklists` (migration `20260820_0004`):
     an unconditional `ForeignKeyConstraint` to `hospital_operation_theaters.id`,
     a table no migration anywhere creates. This is the same class of gap
     as the already-known, already-`BLOCKED`
     `nhdw-hospital-structure-migration-gap` repair-queue row (`hospitals`/
     `hospital_departments`/`hospital_rooms`/`hospital_beds` also have no
     migration) — but it is **new, sharper evidence**: the existing report
     characterized this gap as blocking only NHDW's own admission-journey
     runtime queries ("alembic's chain fails earlier for an unrelated
     reason [the pharmacy bug]... not investigated further"). With the
     pharmacy bug now fixed, this pass directly reproduced that the
     Hospital-domain gap **also blocks the entire alembic chain from ever
     reaching head on a blank database** — a strictly worse severity than
     previously recorded. **NOT fixed this pass** — designing the Hospital
     operational schema (hospitals/departments/rooms/beds/operation
     theaters, and possibly campuses/buildings/floors per the existing
     repair-queue note) is a genuine architectural/business decision, not
     something safely inventable, and DB schema changes require human
     approval per `CLAUDE.md`. Extended the existing pin test
     (`tests/test_nhdw_admission_lifecycle.py::test_hospital_structure_tables_have_no_migration`)
     to also cover `hospital_operation_theaters` so this sharper finding
     is now a permanent, always-run regression guard rather than a
     one-time manual discovery.
- The stale `test_migration_resilience.py` module docstring describing a
  duplicate-revision-ID conflict (`20260505_0001` used twice) is
  **out of date** — `test_no_duplicate_revision_ids` currently passes
  (verified this pass); the underlying conflict was resolved at some
  earlier point without the docstring being updated. Not fixed (cosmetic
  documentation debt, not a functional defect); noted here per the
  directive's own "do not copy old numbers" instruction.

**Tests**
- 236 backend test files, ~2,929 test functions (file-count and
  `def test_`-count, this pass's own measurement)
- Full identity + migration + pharmacy + NHDW regression run this pass:
  **308 passed, 4 skipped**, zero failures, zero regressions from the
  fix below

**Routes / models / architecture**
- 63 route modules, ~2,357 `@router.(get|post|put|patch|delete)` route
  declarations (grep count, not a deduplicated registry — Phase 8 of the
  Master directive, a full route contract registry, is NOT built this
  pass)
- 32 ORM model files under `app/models/`; **21 distinct
  `declarative_base()`/`DeclarativeBase` definitions** repo-wide (this
  pass's own count) — consistent with the repair queue's own
  already-documented multi-Base fragmentation findings (`NursingBase`,
  `NHDWBase`, `PharmacyBase`, etc., each its own registry) and the
  in-progress `app/orm_topology.py` consolidation effort referenced
  throughout the repair queue as another engineer's ("Abu Ali's") active,
  canonical work — not re-investigated further this pass to avoid
  duplicating/conflicting with that in-progress effort, per the repair
  queue's own established boundary (see `nursing-cross-base-fk-topology`
  row)

**CI**
- Not re-checked this pass. Last directly confirmed (same branch, same
  PR #259, prior turn this session): every check across every workflow
  failed with `runner_id: 0` / `0ms` billable duration / no runner ever
  dispatched, reproduced identically on a `main`-branch workflow run at
  the same timestamp — an account/org-level GitHub Actions execution
  block, not a defect in any workflow file or in this repository's code.
  Retained as `BLOCKED_BY_EXTERNAL_INFRA` per the existing reports' own
  standing instruction ("CI remains UNKNOWN/BLOCKED by standing
  instruction — not re-litigated without new evidence"); will be
  re-verified against the current HEAD once real Actions execution
  capacity is confirmed restored.

## DELTA (what changed this pass)

| Item | Before | After |
|---|---|---|
| NIAM sync/async occurrences | 94 category-A + 41 category-F (per `PRODUCTION_READINESS_DELTA.md`, written before this session's lifecycle work) | **0** — 135/135 closed, each with real HTTP+PostgreSQL proof, negative proof, and regression tests (this session's own prior work, independently re-confirmed present in source: `docs/security/NIAM_SYNC_ASYNC_CLOSURE_FINAL_REPORT.md`, all 5 lifecycle-class status docs, and the 40 new regression tests all present and passing in the 308-test run above) |
| `pharmacy_drug_substitution_rules`/`_requests` FK type mismatch | Open P1, blocks `alembic upgrade head` from blank at this migration | **FIXED** — `Integer` FK columns in both the migration and the ORM model; proven UP→DOWN→re-UP against a real disposable PostgreSQL 16 database; 308-test regression run clean |
| Hospital-domain migration gap | Characterized as blocking only NHDW admission-journey runtime queries | **Reproduced as blocking the entire alembic chain from blank** (worse than previously stated) — pin test extended to cover the newly-implicated `hospital_operation_theaters` table; still `BLOCKED_BY_EXPLICIT_HUMAN_DECISION` (schema design, requires human approval) |

## UNRESOLVED FINDINGS (carried forward, not re-litigated without new evidence this pass)

All 59 rows of `docs/engineering/MUSTAFA_ACTIVE_REPAIR_QUEUE.md` retain
their existing dispositions; this pass did not re-audit them. Of
particular note for continuation:

- `nursing-cross-base-fk-topology` — **BLOCKED**, handed to another
  engineer's active `orm_topology.py` consolidation work
- `nhdw-hospital-structure-migration-gap` — **BLOCKED_BY_EXPLICIT_HUMAN_DECISION**,
  sharpened this pass (see above)
- `adaptive-auth-account-id-idor` — **NEEDS_DECISION**, ~10 endpoints,
  genuinely ambiguous without NIAM login-flow domain ownership input
- `ai-approval-no-tenant` — **P2, documented, not actioned**
- `imaging-slice-device-status-ambiguous` — **NEEDS_DECISION**
- `lab-slice-sample-nonstatus-field-race` — **P3, documented, low
  priority**
- Autonomous-repair-family: 3 of 4 non-`self_audit_agent.py` components
  (`gula_autofix.py`, `gula_guardian.py`, `secure_self_patcher.py`) remain
  **DEPRECATE/DO_NOT_ACTIVATE/STUB**-marked in-file, not deleted (deletion
  requires explicit human sign-off per the queue's own prior decision)

## EXTERNAL BLOCKERS

- GitHub Actions CI (account/org-level execution block, not code) —
  `BLOCKED_BY_EXTERNAL_INFRA`, tracked on PR #259
- Hospital-domain schema design — `BLOCKED_BY_EXPLICIT_HUMAN_DECISION`
  (DB schema changes require human approval per `CLAUDE.md`)
- NIAM adaptive-auth login-flow semantics (`adaptive-auth-account-id-idor`)
  — `BLOCKED_BY_EXPLICIT_HUMAN_DECISION` (correct authorization semantics
  cannot be derived without knowing whether each caller is self,
  system-internal, or cross-account-admin)

## NEXT EXECUTION QUEUE (realistic, iterative — not claimed complete this pass)

In priority order, each independently boundable and provable:

1. Re-verify CI on the current HEAD once Actions execution is confirmed
   restored (no code action possible until then).
2. Fresh P0/P1 sweep of the ~2,357-route registry against the specific
   checklist in the Master directive §3 (auth/session/authorization/
   tenant-isolation/audit/idempotency/concurrency matrix) — bounded into
   per-domain batches the same way the existing repair queue already
   demonstrates (Laboratory → Imaging → EMS → Nursing → NHDW), continuing
   into the domains that queue has not yet reached.
3. Authorization Expansion directive, Batch 1 (Platform/Governance/
   Administration) — build the capability inventory
   (`docs/security/AUTHORIZATION_CAPABILITY_INVENTORY.md` +
   `authorization_capability_registry.json`) from the ALREADY-EXISTING
   `PlatformCapability` enum and NIAM RBAC/ABAC machinery (do not invent a
   parallel system), then proceed batch-by-batch per that directive's own
   §32 execution strategy.
4. Cross-Base FK/declarative-Base consolidation — coordinate with (not
   duplicate) the in-progress `orm_topology.py` effort referenced
   throughout the repair queue.
5. Production Readiness Matrix rebuild (Master directive §16) — once
   (1)-(3) produce new evidence; rebuilding it now would just restate the
   existing two matrices with one row (NIAM sync/async) updated.

This document will be superseded by an updated baseline each time a
future pass produces new measured evidence, per the directive's own
instruction never to copy forward stale numbers.
