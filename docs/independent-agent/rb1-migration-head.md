# RB-1 — migration head: root cause, layers, and proof

**Verdict:** RB-1 is **RESOLVED on the integration lineage**
(`claude/p0-2-pharmacy-reconciliation`, `ce097a0c`) and **UNRESOLVED on
`claude/autonomous-run-1`**, which is missing two already-authored commits. No new
repair was written, because writing one would have duplicated work that exists.

## Acceptance criterion, met

Fresh PostgreSQL database (`gula_agent2`, dropped and recreated) →
`alembic upgrade head` → **exit 0**.

| measurement | value |
|---|---|
| migrations applied (`Running upgrade` lines) | **112 of 112** |
| errors | **0** |
| declared head | `20260916_0001` |
| final `alembic_version` | `20260916_0001` |
| tables created | **423** |
| `downgrade -1` then `upgrade head` | **both OK**, back at `20260916_0001` |

The round-trip matters: it is the gate `.github/workflows/ci.yml`'s
`migration-check` job runs, so this is the same assertion CI would make if CI
could run at all (RB-6).

## The layers, in the order they surfaced

RB-1 was not one failure. Each layer was reproduced on a freshly created database
before being attributed.

### Layer 1 — `DatatypeMismatch` at `20260815_0023`

```
psycopg2.errors.DatatypeMismatch: foreign key constraint
"pharmacy_drug_substitution_rules_original_drug_catalog_id_fkey"
cannot be implemented
```

* `20260716_0003_pharmacy_platform.py:52` creates `pharmacy_drug_catalog.id` as
  `sa.Integer()`.
* `20260815_0023:27-28` declares `original_drug_catalog_id` and
  `alternative_drug_catalog_id` as `sa.String(26)` with foreign keys to it.

PostgreSQL cannot implement a `varchar → integer` foreign key. A ULID-shaped
column referencing an integer key — the same two-identity-generations collision
ADR-006 exists to settle.

**Existing repair used:** `f92d4132` *"fix(pharmacy): establish canonical drug
identity and unblock upgrade head (NR-003)"*. Its own commit message contains the
argument this audit reached independently: the repository's "never modify an
existing migration" rule exists because deployed databases have already applied
the revision, and **no migration-built database can have applied this one**, since
it aborts deterministically on every clean database. Verified: cherry-picked onto
the audit branch (`048e2725`) and the `DatatypeMismatch` is gone.

### Layer 2 — `UndefinedTable: hospital_operation_theaters`

With layer 1 removed the build stops at `20260820_0004`, which carries an
unconditional foreign key to a table no migration in that lineage creates. This is
NR-073 in the master register.

**Existing repair:** `efcc4b6e` *"fix(hospital): create the core schema the
surgical checklist requires (P0-1)"*, which adds
`20260820_0003_hospital_core_schema.py` and amends `20260820_0004`.

### No layer 3

Both repairs are ancestors of `claude/p0-2-pharmacy-reconciliation`, and that
lineage reaches head cleanly. So the chain terminates at two layers.

## The cherry-pick conflict, resolved by aborting

Applying `efcc4b6e` onto the audit branch conflicted. Inspected rather than
guessed:

```
Changes to be committed:
  new file:   backend/migrations/versions/20260820_0003_hospital_core_schema.py
  modified:   backend/migrations/versions/20260820_0004_surgical_safety_checklists.py
Unmerged paths:
  deleted by us:   docs/delivery/MOH_DELIVERY_BASELINE.md
```

Classification: **modify/delete, documentation only.** Both migration files staged
without conflict — no content conflict, no add/add, no rename, **no Alembic
ancestry conflict**. `git log -- docs/delivery/MOH_DELIVERY_BASELINE.md` on this
lineage is empty: the file has never existed here, so `efcc4b6e` edits a document
this branch does not carry.

Resolution: `git cherry-pick --abort`, worktree clean. Because both commits are
already in the integration lineage, duplicating them onto an audit branch would
have created a competing history for no gain; the lineage was proven directly
instead.

## Separately observed: Alembic transaction behaviour (documented, NOT changed)

The upgrade runs as **one transaction across many migrations**, not one per
migration. On the failing lineage the log shows migrations executing up to
`20260901_0004` — roughly sixty revisions past the last commit — and then the
failure at `20260815_0023` rolls all of them back. The operator is left with:

| | |
|---|---|
| `alembic_version` stamp | `20260505_0005` |
| tables | 32 |
| migrations the log said ran | ~60 beyond that stamp |

So **the recorded revision can sit far behind the migration log**, and the visible
stamp understates what was attempted. Two consequences worth naming:

1. a single mid-chain failure discards every successful migration after the last
   commit point, which makes a partial upgrade impossible to resume from;
2. anyone diagnosing from the stamp alone will look for the fault near
   `20260505_0005`, which is about sixty revisions away from where it is.

`transaction_per_migration=True` on `context.configure` in `migrations/env.py`
would change this. **Not changed here**, per instruction, and it should not be
changed casually: per-migration commits mean a failure leaves a partially migrated
database, which is a different risk and wants its own decision rather than being
bundled into a blocker fix.

## Consequence for the other blockers — measured, not inferred

The proven build was then queried directly:

| check | result | meaning |
|---|---|---|
| `ehr_*` tables | **0** | **RB-3 is confirmed and independent of RB-1.** A database that reaches head cleanly still has no EHR schema, so RB-3 is not a downstream symptom. |
| `hospital*` tables | 4 | present once `efcc4b6e` is in the lineage |
| `nursing*` tables | 15 | present. So RB-5's "unwritable" is an ORM/physical-schema contradiction, not a missing schema — consistent with NR-076's 149/176/41 measurement |

## Integration action

Nothing to implement. `claude/autonomous-run-1` needs `f92d4132` and `efcc4b6e`
in its lineage; the integration line already has both. Every release-blocker
figure previously measured against `gula_canon` remains valid, because `gula_canon`
was itself built from a lineage containing both commits.
