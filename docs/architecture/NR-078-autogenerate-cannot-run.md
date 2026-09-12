# NR-078 — `alembic revision --autogenerate` cannot run against this repository

**Status:** MEASURED. Not fixed. The fix is a declarative-base topology decision
and is reserved for a human.

## The claim, and how to reproduce it

```
$ cd backend && alembic revision --autogenerate -m "anything"
sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column
'ehr_allergies.citizen_id' could not find table 'national_citizens' with which
to generate a foreign key to target column 'id'
```

No revision file is written. Run against a PostgreSQL 16.13 database migrated to
head, so this is not a "your database is out of date" failure — it is Alembic
refusing to begin.

`CLAUDE.md` names that command as the mandatory way to make any schema change:

> **All schema changes = new revision** — `alembic revision --autogenerate -m "describe"`

So the documented procedure for every schema change in this platform has no
working path, and has not had one for as long as the condition below has held.

## Why

SQLAlchemy resolves a `ForeignKey` inside the `MetaData` that owns the
**referring** table. Alembic reaches `MetaData.sorted_tables` on every registered
metadata *before* it emits a single operation, and sorting resolves every foreign
key. One unresolvable declaration anywhere stops the whole run.

Measured against exactly what `backend/migrations/env.py` hands Alembic — loaded
by replaying that file rather than by restating its list — **310** foreign keys
point at a table their own base does not own:

| Declarative base | Unresolvable foreign keys |
|---|---|
| `CareContinuumBase` | 214 |
| `EHRBase` | 70 |
| `DataPlatformBase` | 13 |
| `TrustBase` | 8 |
| `IdentityBase` | 5 |
| **Total** | **310** |

The targets are real, populated tables owned by other bases:

| Target | Owned by | References |
|---|---|---|
| `national_practitioners` | `NationalBase` | 78 |
| `national_patients` | `NationalBase` | 51 |
| `national_citizens` | `NationalBase` | 50 |
| `national_facilities` | `Base`, `NationalBase` | 49 |
| `national_encounters` | `NationalBase` | 30 |
| `national_organizations` | `NationalBase` | 9 |
| `labs`, `lab_users`, `patients`, `users`, … | `Base` | 20 |
| eight more national tables | `NationalBase` | 23 |

NR-075 — the five on `niam_citizen_relationships` that stop
`POST /admin/citizen-relationships` from inserting a row — is 1.6% of this. It
was found first only because its endpoint was executed.

## Why nothing caught it

`backend/tests/test_alembic_metadata_registry.py` already guards foreign keys.
Its third invariant reads:

> every foreign key names a table that exists **somewhere**, except a pinned list

`PHANTOM_FK_TARGETS` is empty, and correctly so: all 310 targets exist. But
"exists somewhere in the registry" is one qualifier weaker than what SQLAlchemy
requires, which is "exists in the referring table's own `MetaData`". The guard
asked the answerable half of the question.

The deeper reason is the one worth keeping: **every guard in that file reasons
about what autogenerate *would* propose, and not one of them has ever asked
autogenerate to propose anything.** The capability was assumed by the guards that
depend on it and exercised by none of them. That is the same failure class as
NR-064 (a workflow tested only through a fake session) and NR-073 (a guard that
asked whether the table was built, when the ORM was the broken part).

## What is applied here, and what is not

Applied, in `backend/tests/test_alembic_metadata_registry.py`:

* `UNRESOLVABLE_CROSS_BASE_FKS` — a per-base ledger that may shrink and may never
  grow, plus a rot check requiring the numbers to come down when a base improves;
* a guard-the-guard floor, so a drifted scan cannot ratchet nothing;
* `test_alembic_can_sort_every_registered_metadata`, an `xfail(strict=True)`. It
  fails loudly the moment autogenerate starts working, which is the signal to
  close NR-078 and NR-075 — not to delete the test.

Negative-proved, both restored byte-identical: removing one foreign key from
`CitizenRelationship` fails the rot check with `IdentityBase (5, 4)`; adding a
cross-base foreign key to a `PharmacyBase` model fails the ratchet with
`['PharmacyBase']`.

Not applied: the fix.

## The two options, and the risk that reserves the decision

**Option A — share one `MetaData` across the bases that reference each other.**
Resolves every one of the 310. Changes the topology NR-018 registered
deliberately, and merges table namespaces: `national_facilities` is already
claimed by two bases (NR-006), so a merge forces that collision to be resolved
first.

**Option B — drop the ORM-level `ForeignKey` and keep the physical constraint.**
Cheaper per declaration and far riskier. The physical constraints exist because
migrations create them by name — `fk_citizen_relationship_user`,
`fk_citizen_relationship_lab_user` and so on, all enforced by PostgreSQL today.
Once autogenerate runs and no longer sees those declarations, it may propose
`drop_constraint` for constraints that are protecting live data.

That risk is the reason this stops here. The standing instruction is explicit:
if a topology change causes Alembic to propose dropping physical constraints,
tables or indexes that are not intentionally retired, **stop that decision**. The
first working autogenerate run will propose operations nobody in this repository
has ever seen. Every one of them must be classified before a revision is
generated, and that classification is the beginning of the work, not the end of
it.

## Order of operations, when someone takes it

1. Take the topology decision (A or B) explicitly, and record it as an ADR.
2. Apply it and confirm `test_alembic_can_sort_every_registered_metadata` passes.
3. Run `alembic revision --autogenerate` against a database migrated to head and
   **do not commit the output**. Classify every operation: intended, unintended,
   or unexplained.
4. Stop on the first unintended `drop_*`. Explain it before continuing.
5. Only then write the revision, and only the operations that survived step 3.
