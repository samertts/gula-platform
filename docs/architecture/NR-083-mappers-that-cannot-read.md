# NR-083 — mappers that cannot read, and the measurement that finally asked

**Status:** GUARDED AND PARTLY REPAIRED — 44 measured, 8 repaired, 36 pinned and ratcheted
**Evidence:** EXECUTED — 715 mapper `SELECT`s against PostgreSQL 16 at migration head
**Related:** NR-074 (NHDW), NR-078 (autogenerate), NR-080 (drift), NR-082 (radiology)

## The question nobody had asked

This repository has accumulated a good number of schema guards. They check that
migrations apply, that every declarative base is registered with Alembic, that
the built tables match the database, that autogenerate runs and that its
destructive proposals are explained.

Every one of them compares a *description* of the schema to another
*description*: metadata against metadata, migration against model, list against
list. Not one had ever handed a mapper's own query to PostgreSQL and looked at
what came back.

So this survived every gate:

```
SELECT radiology_orders.id, ..., radiology_orders.encounter_id, ... FROM radiology_orders LIMIT 1
ProgrammingError: column radiology_orders.encounter_id does not exist
```

`alembic upgrade head` is untroubled by it. A table-existence check passes. The
SQLite-backed unit suite never sees it, because there the schema is built from
the mappers themselves and so agrees with them by construction. The condition is
visible only to PostgreSQL, only at statement time, and only if something
actually executes a statement.

## What executing it found

715 tables are registered across the 18 metadata objects in `migrations/env.py`.
Against `nr078_probe` (PostgreSQL 16, `alembic upgrade head`):

| | count |
|---|---|
| mapped, no physical table | **303** |
| mapped, physical, readable | 368 |
| mapped, physical, **unreadable** | **44** |

The 303 is worth pausing on: the autogenerate gate independently derives a
`CreateTableOp` count of **303**, by a completely different route — it reads what
Alembic emits, this reads what PostgreSQL lacks. Two instruments, two methods,
one number. That is the cross-check §10 asks for, and it passed.

The 44 are not degraded, they are dead. SQLAlchemy builds the column list from
the mapper, so `SELECT`, `INSERT`, `UPDATE` and `COUNT` all fail before a row is
examined. There is no partial success and no fallback.

| block | tables | finding |
|---|---|---|
| radiology | 17 | NR-082 |
| NHDW | 14 | NR-074 |
| governance | 6 | repaired here |
| ecosystem | 3 | 2 repaired here |
| financial | 3 | Phase A, schema-only by design |
| identity | 1 | `niam_machine_identities`, 10 columns |

## What was repaired, and what deliberately was not

Eight of the 44 were not drift in any interesting sense: the mapper inherits a
timestamp or optimistic-lock mixin and the migration that created the table
simply never built those columns. Migration `20260915_0001` adds the eleven
missing columns — guarded on `_has_table`/`_has_column`, nullable with a
`server_default`, nothing dropped, renamed, retyped or backfilled — and the
round trip (`downgrade -1` → `upgrade head`) was executed and verified.

Two of those eight matter beyond tidiness. `gov_break_glass_accesses` records
emergency override of normal access control; `gov_merge_proposals` records
proposals to merge two patient identities. On both, the column that did not
exist was **`version`** — so CLAUDE.md Security Invariant #6, "optimistic lock
MUST be checked on every mutation", could not be satisfied on the two tables
where a lost update is least acceptable. It could not be satisfied because there
was nothing to check.

A ninth table is left failing on purpose. `ecosystem_partner_agreements` also
fails on `version`, but there the mapper declares
`version = Column(String(20), nullable=False)` — a *document* version, shadowing
the integer lock it inherits — while the table carries `agreement_version`.
Adding an integer `version` would contradict the mapper. Mapping `version` onto
`agreement_version` would quietly confirm that partner agreements have no
optimistic lock. Which of those is intended is a question about the entity, not
about the schema, so it stays in the ledger rather than being guessed at.

## The direction of repair, and why the guard pins both ends

The obvious way to make a mapper and a table agree is to change whichever is
easier. For the 36 that remain, that would be catastrophic, and the radiology
block shows why: the physical tables carry `lab_id` with a foreign key to `labs`
(14 of them), `created_by`/`updated_by` to `lab_users`, and `patient_id` to
`patients`. The mappers carry none of it. Autogenerate's answer to that
disagreement is `DROP COLUMN`, forty-three times, on columns this platform's
first security invariant is written about.

So the physical schema is canonical here and the mappers are what moves. Which
creates the opposite hazard: a mapper could be made *readable* by deleting the
fields PostgreSQL does not have, and the unreadable ledger would shrink while
the platform got worse.

`test_mapped_tables_are_readable.py` therefore ratchets both ends. The
unreadable ledger may never grow, entries must be removed once repaired, the
per-table missing-column tuples must stay exact — and `MINIMUM_READABLE` pins
the readable population at 370 against a measured 376, so emptying the ledger by
deleting mapper fields fails the same run. A floor on the instrument itself
(`MINIMUM_PROBED`, 400 against a measured 412) closes the NR-079 failure mode,
where a guard whose instrument silently measures nothing reports success
forever.

Four negative proofs were executed against a disposable copy and the file
restored byte-identical (md5 verified): removing a ledger entry, adding a
resolved one, corrupting a missing-column tuple, and pointing the probe at an
empty database. Each produced the intended failure with the intended message.

## What is still open

The 36 remaining entries are domain reconciliations, not line edits. Radiology
(NR-082) is the largest and the worst: 50 registered HTTP paths over 18 mappers
of which none can touch the database. It needs the pharmacy treatment — mappers
rewritten from the physical schema, `lab_id` restored and enforced in the
service layer, then `services.py` and `routes.py` reconciled — and it needs a
domain owner's decision on the 170 Generation-B fields before any of that.

The ledger is the point. Until this measurement existed, none of it was visible
from CI, and a green migration gate said nothing about whether a single mapper
could read its own table.
