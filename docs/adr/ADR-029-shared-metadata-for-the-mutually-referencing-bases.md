# ADR-029 — One `MetaData` for the seven mutually-referencing declarative bases

**Status:** Accepted — applied 2026-09-19
**Closes:** NR-086 (P1), NR-078 (P1), NR-075 (P1), and NR-006's residual anchor
**Unblocks:** NR-146's behavioural proof
**Does not close:** NR-080 (the drift), which is now held by an explicit refusal
instead of by an accident

## Context

SQLAlchemy resolves a `ForeignKey` inside the `MetaData` that owns the
**referring** table. This repository had eighteen registered declarative bases,
and **310 foreign keys named a table their own base did not own**.

Two consequences, measured separately and found to be the same defect:

* **NR-078** — Alembic reaches `sorted_tables` on every registered metadata
  before emitting one operation, and sorting resolves every foreign key. So
  `alembic revision --autogenerate` terminated with `NoReferencedTableError` on
  `ehr_allergies.citizen_id` and wrote nothing. The command CLAUDE.md names as
  mandatory for any schema change had no working path.
* **NR-086** — a flush sorts the mapper's tables too. So **76 mapped tables
  could not be written through the ORM at all**: every `INSERT` and `UPDATE`
  raised before emitting SQL. Reads were unaffected, which is why it hid —
  `SELECT` never sorts. Six live write endpoints were failing on it, including
  `POST /api/v1/trust/consent` and `/consent/{id}/withdraw`.

Two prior decisions bear on this:

* NR-078 measured both repair options and recorded **Option A (one shared
  `MetaData`) as decided and deliberately not applied**, because applying it
  also makes autogenerate *usable*, and NR-080 had measured what its first
  complete run proposes: 5039 operations, 1367 destructive, including
  `DROP COLUMN patients.national_id` — the column Security Invariant #8 requires
  to hold encrypted national identifiers. Its recorded order of operations was
  "reconcile the drift first, then merge".
* **Option B** (drop the ORM-level `ForeignKey`, keep the physical constraint)
  was measured and does not work: it hits
  `ValueError: Duplicate table keys ... "national_facilities"`, and it would
  raise NR-080's destructive budget by roughly 310 `DropConstraintOp` against
  constraints PostgreSQL enforces today.

## Decision

**Apply Option A, to the measured closure only, and replace the accidental block
on autogenerate with a deliberate one.**

### 1. Scope: seven bases, not eighteen

The bases that must share a namespace are the transitive closure of "declares a
cross-base foreign key" and "owns a table one of those names". Measured, and at
a fixed point immediately:

| Role | Bases | Cross-base FKs |
|---|---|---|
| referring | `CareContinuumBase` | 214 |
| | `EHRBase` | 70 |
| | `DataPlatformBase` | 13 |
| | `TrustBase` | 8 |
| | `IdentityBase` | 5 |
| owning the targets | `Base`, `NationalBase` | — |
| **closure** | **7** | **310** |

The other eleven registered bases declare nothing across a base boundary and are
untouched. This is what separates the change from a naive merge: `InsBase` and
`app.national.task_engine` are deliberately unregistered (NR-018), and a merge of
everything imported would put 28 tables in front of autogenerate that a recorded
decision keeps out of it.

Applied in `backend/app/orm_topology.py`; each base is constructed with
`declarative_base(metadata=SHARED_METADATA)`.

### 2. The one collision it forces

`national_facilities` was declared twice: by `models.clinical_scope.NationalFacility`
and, since NR-006, as a bare `Table` foreign-key anchor in
`app/national/domain/facility.py` so that seventeen `app/national` models could
resolve it inside `NationalBase`. Under one namespace the anchor is redundant
*and* illegal. It is deleted; the module re-exports the canonical table. The two
definitions were column-identical, so this is a deletion, not a choice of owner.

### 3. Autogenerate is refused explicitly, not accidentally

`app.orm_topology.refuse_unreconciled_destructive_autogenerate`, installed by
`migrations/env.py` as `process_revision_directives` on both the online and
offline paths, raises when a proposed revision contains any destructive
operation, naming the count, the kinds and the first ten targets.

* An additive diff passes through untouched.
* A destructive diff is refused **whole** — never silently filtered. A migration
  that quietly drops half of what it was asked to emit is worse than one that
  does not run.
* The guard lifts on its own as NR-080 is reconciled, with no change to itself.

`target_metadata` in `env.py` is deduplicated by identity, because Alembic
rejects a multi-metadata target that claims one table twice and seven of its
entries are now the same object.

## Why the recorded order of operations was inverted

NR-078 said reconcile the drift (NR-080) first, then merge. That ordering existed
for exactly one reason: merging makes autogenerate usable. It weighed a tooling
risk against a tooling inconvenience and got that pair right.

It was the wrong pair. The same 310 declarations were also **76 unwritable
tables and six failing clinical write endpoints**, and that cost was not in the
comparison — NR-086 measured it afterwards. The two halves are separable: the
merge repairs the ORM, and the refusal hook keeps the autogenerate hazard shut.
Reconciling ~365 unmapped columns first would have left consent capture broken
for the duration, to protect against a command nobody could run.

NR-080's drift is unchanged: 5039 operations, 1367 destructive, ratcheted by
`backend/tests/test_autogenerate_is_safe.py`. Nothing about it was hidden,
lowered, or worked around.

## Consequences

**Repaired.** All 310 foreign keys resolve. Zero unwritable mapped tables, down
from 76. Three things that had never run now run:

* the trust consent write path — a real `Session`, a real `ConsentRecord`,
  `flush`, `UPDATE`, `commit`, pinned as
  `test_mapped_tables_are_writable.py::test_the_repaired_write_path_actually_writes`;
* `POST /admin/citizen-relationships` (**NR-075**) against a real PostgreSQL 16
  migrated to head. `test_citizen_relationship_postgres.py` carried four strict
  xfails on `NoReferencedTableError`, one saying "remove this xfail when NR-075
  is repaired — `strict=True` means it fails loudly the moment the endpoint
  starts working". All four XPASSed and are removed; its nine tests pass,
  including the two-connection `with_for_update` concurrency test;
* **NR-146**'s two-lab behavioural suite, which its own blocked test said to
  write "when NR-078 lands". Written, and negative-proved.

And the refusal was proved at the CLI, not only in a unit test:
`alembic revision --autogenerate` against that migrated database now reaches the
hook and raises `REFUSED: autogenerate proposed 1367 destructive operations
(DropColumnOp=365, DropConstraintOp=538, DropIndexOp=454, DropTableOp=10)` —
**identical, operation kind for operation kind, to `DECLARED_DESTRUCTIVE_BUDGET`
in the gate**, which is two independently derived instruments agreeing — and
`migrations/versions/` went from 113 files to 113.

**Unchanged.** No DDL. No migration. No constraint or index changes name: not one
base carried a `naming_convention`, and the `Table` objects are the same objects
collected in one namespace instead of seven.

**Changed for callers.** `Base.metadata.tables` now answers for all seven bases
(447 tables), not one. `app.orm_topology.own_tables(base)` returns a single
base's own tables for code that meant that. Measured blast radius across the
suite: **two** tests, both of which were the designed signals — the duplicate-key
ledger and NR-146's blocked-proof marker. 3321 other tests unaffected.

**Still true.** The shared namespace is only as complete as the import graph: a
foreign key resolves once its target's module has been imported. Fixtures that
build tables from it call `app.factory.import_all_models()`, which is what the
application itself does at startup.

## Ledgers this empties, and the ratchets that stay

| Ledger | Was | Now |
|---|---|---|
| `UNRESOLVABLE_CROSS_BASE_FKS` | 5 bases / 310 | `{}` |
| `DECLARED_UNWRITABLE` | 76 tables / 310 | `{}` |
| `TABLE_NAME_COLLISIONS` | `{national_facilities}` | `frozenset()` |
| `DECLARED_DUPLICATE_TABLE_KEYS` | `{national_facilities}` | `frozenset()` |
| `test_alembic_can_sort_every_registered_metadata` | strict `xfail` | passes |
| `DECLARED_DESTRUCTIVE_BUDGET` (NR-080) | 1367 | 1367 — unchanged |

Every emptied ledger stays in place. The first mapper to declare a foreign key
across a base boundary again fails `test_no_undeclared_table_is_unwritable` with
the table named, and reads will still work, so nothing else would notice.

## What is still open

* **NR-080** — the drift itself. Largest clusters radiology (~231 columns) and
  NHDW (~111), both blocked on a domain owner; then the five SNDHS Phase 1
  columns on `patients` and `lab_orders`. Until it is reconciled,
  `alembic revision --autogenerate` refuses and schema changes are hand-written
  with `alembic revision -m "..."`.
* **NR-146** remains LATENT, not live: no migration creates the `cc_*` tables, so
  none of its holes is reachable by a caller today.
  `test_z_this_domain_is_still_unbuilt` pins that.
