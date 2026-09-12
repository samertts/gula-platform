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

---

# UPDATE — both options measured, and the conclusion inverted

**Status: PARTIALLY VERIFIED.** Autogenerate now executes inside a CI gate. The
topology change is **decided (Option A) and deliberately not applied.**

Everything above was written before either option was run. Running them changed
the answer, and this section supersedes the framing above rather than extending
it: **the topology was never the bottleneck.**

## Option B does not work, for a reason nobody had found

Drop the ORM-level `ForeignKey` on the 310 cross-base declarations, keep the
columns and the physical constraints.

It costs less than it appeared to. A runtime census of all 18 SQLAlchemy
registries finds 218 `relationship()` declarations, and **not one of them is on
any of the 76 tables that hold a cross-base foreign key.** There is no ORM
navigation to lose. Removing all 310 from the metadata leaves zero unresolved.

And then it fails anyway:

```
ValueError: Duplicate table keys across multiple MetaData objects: "national_facilities"
```

Alembic refuses a multi-metadata target that claims one table twice. NR-006's
repair deliberately declares `national_facilities` a second time, as a bare
**foreign-key anchor**, so that seventeen `app/national` models can resolve
`ForeignKey("national_facilities.id")` inside their own `MetaData`. That anchor
is simultaneously what makes those foreign keys work and what makes autogenerate
refuse. Option B cannot hold both goals; it is not a matter of doing it more
carefully.

## Option A works, and is one deleted declaration away

| Measured | Result |
|---|---|
| duplicate table keys | **1** (`national_facilities`) |
| are the two definitions identical? | **yes**, column for column |
| unresolved foreign keys | **0** |
| `sorted_tables` | **succeeds** |
| `autogenerate` | **runs** |

So the collision is resolved by deleting one declaration, not by choosing an
owner — and Option A is the mechanically correct topology.

## Why it is still not applied

Because running is not the same as usable. The diff:

```
5060 operations
  2372  CreateIndexOp        377  DropColumnOp
   585  ModifyTableOps       314  AddColumnOp
   538  DropConstraintOp     303  CreateTableOp
   454  DropIndexOp           73  AlterColumnOp
                              27  CreateForeignKeyOp
                              10  DropTableOp
  ── 1379 destructive ──
```

None of that is caused by the topology change. It is pre-existing drift that the
topology change merely made visible, and two cross-checks confirm both
instruments are telling the truth:

* `CreateTableOp` = **303** = the independently measured count of mapped tables
  with no physical table;
* `DropTableOp` = **10** = the independently measured count of physical tables
  with no ORM, and **exactly** the list already pinned as
  `UNMAPPED_PHYSICAL_TABLES` — two derivations, one from subtraction and one
  from Alembic, agreeing entry for entry.

The serious half is the columns:

```
DROP COLUMN patients.national_id        -- varchar(20), four indexes,
DROP COLUMN patients.sndhs_health_id       one partial unique index
DROP COLUMN patients.identity_level
DROP COLUMN patients.consent_flags
DROP COLUMN lab_orders.visit_id
```

`patients.national_id` is the column CLAUDE.md Security Invariant #8 requires to
hold **encrypted national identifiers**. `app/models/patient.py` maps
`national_id_hash` beside it and none of these.

Applying Option A today would convert a loud, honest failure — *autogenerate
cannot run* — into a quiet and dangerous capability — *autogenerate runs, and
proposes dropping your encrypted national IDs*. That is the same trade NR-076
refuses when it declines to make an abstract repository instantiable without
implementing it, and it is refused here for the same reason and in the same
direction.

Recorded as **NR-080**.

## What is applied instead

`backend/tests/test_autogenerate_is_safe.py` performs the merge **inside the
gate**, so autogenerate executes for real against a disposable PostgreSQL
migrated to head while `migrations/env.py`, every declarative base and every
model stay exactly as they are. Runtime risk: none.

Seven tests: the merge resolves every cross-base FK; there is exactly one
duplicate table key; autogenerate actually runs; its output is deterministic
across two runs; no unexplained `DROP TABLE`; the protected-column drop set is
exactly as declared, in **both** directions; and the destructive budget may fall
but never rise.

Four negative proofs, every source restored byte-identical:

| Perturbation | Fails |
|---|---|
| a `ForeignKey` to a table in no metadata | cross-base FK resolution |
| a second anchor `Table` for `labs` | duplicate-table-key guard |
| map `patients.national_id` in the ORM | protected-column ledger (**shrink it**) |
| rename a mapped `__tablename__` | unexplained `DROP TABLE` + destructive budget |

The third is worth noting: it proves the *fix* direction works. Mapping a
protected column removes it from the DROP set and the guard tells you to update
the ledger.

## Order of operations, revised

1. **Reconcile the drift** (NR-080), per entity, largest cluster first:
   radiology (~170 columns / 12 tables), then nhdw (NR-074), then the SNDHS
   Phase 1 columns on `patients` and `lab_orders`. Map protected columns; never
   drop them. The destructive budget in the gate falls as this proceeds.
2. **Then** delete the `national_facilities` anchor and adopt one `MetaData`.
3. **Then** `alembic revision --autogenerate` becomes usable at the CLI, and
   NR-075 and NR-064 can be re-evaluated against a topology that resolves.

The previous version of this document put step 2 first. That was wrong, and the
measurement is what showed it.
