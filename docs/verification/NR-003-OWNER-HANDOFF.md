# NR-003 — Owner Handoff

**Generated:** 2026-09-25 · **Analysed from:** `fe961550` · **production_ready:** `false`

This is a handoff, not a repair. The repair already exists, was authored with an
explicit owner authorization, and was re-verified here by execution. Nothing was
merged, pushed or cherry-picked; the owner branch was read in a detached
`git worktree`, which changes no branch.

Companions: [`MIGRATION_HEAD_TRUTH.md`](./MIGRATION_HEAD_TRUTH.md) ·
[`NR-028-AUTHORIZATION-PACKET.md`](./NR-028-AUTHORIZATION-PACKET.md)

---

## 1. The defect, exactly

`20260815_0023_drug_substitution.py` creates `pharmacy_drug_substitution_rules`
with two foreign keys onto `pharmacy_drug_catalog.id`. That primary key is
`Integer`, created by `20260716_0003`. The revision declared both referencing
columns as `String(26)`.

```
CONSTRAINT pharmacy_drug_substitution_rules_original_drug_catalog_id_fkey
  FOREIGN KEY (original_drug_catalog_id) REFERENCES pharmacy_drug_catalog (id)

original_drug_catalog_id   character varying(26)   -- declared
pharmacy_drug_catalog.id   integer                 -- referenced
```

PostgreSQL refuses to implement the constraint:

```
psycopg2.errors.DatatypeMismatch: foreign key constraint
"pharmacy_drug_substitution_rules_original_drug_catalog_id_fkey"
cannot be implemented
DETAIL: Key columns "original_drug_catalog_id" and "id" are of
incompatible types: character varying and integer.
```

The abort happens **inside** the revision, so nothing ordered after it can run.

### Observed on `fe961550` (this branch, unrepaired)

| Measurement                | Value                                                            |
| -------------------------- | ---------------------------------------------------------------- |
| Fresh database             | `gula_precond_090016`, PostgreSQL 16, 0 tables at start          |
| Exit code                  | `1`                                                              |
| Revisions Alembic executed | 94                                                               |
| Aborting revision          | `20260815_0023`                                                  |
| Stamp left behind          | `20260505_0005` — a rollback boundary, **not** the failure point |
| Tables left behind         | 32                                                               |

`20260505_0006` opens an `autocommit_block` for a concurrent index build, which
commits everything open at that moment. The 62 revisions that ran after it roll
back together. Reading the stamp as the failure point sends a diagnostician to the
wrong file.

---

## 2. Owner branch and repair commit

| Field                   | Value                                                                                                                         |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Owner branch            | `claude/nr-003-canonical-drug-identity`                                                                                       |
| Branch tip              | `dcf00fa1`                                                                                                                    |
| **Repair commit**       | **`f92d4132`** — _fix(pharmacy): establish canonical drug identity and unblock upgrade head (NR-003)_                         |
| Merged into `main`?     | **No.** `git merge-base --is-ancestor … origin/main` → not an ancestor.                                                       |
| Files changed by repair | 3 — `20260815_0023_drug_substitution.py`, `20260909_0001_pharmacy_canonical_drug_identity.py` (new), `app/pharmacy/models.py` |

### What `f92d4132` does

1. **Corrects `20260815_0023` in place.** Only the two catalog foreign keys change
   `String(26)` → `Integer`. `id` and `rule_id` stay `String(26)` — they are these
   tables' own identities, not catalog references.
2. **Adds `20260909_0001`**: `pharmacy_drug_catalog.drug_id`, a server-generated
   immutable UUID4 public identity from `gen_random_uuid()`. The `Integer` primary
   key is unchanged and stays internal; `drug_code` is untouched. Backfill is
   guarded and fail-closed — it re-checks for NULLs and duplicates and aborts with a
   diagnostic rather than transforming or discarding data.
3. **Reconciles the ORM**, retyping the two `DrugSubstitutionRule` catalog foreign
   keys to `Integer`.

### The in-place modification, and why it is not a policy breach

`CLAUDE.md` states **never modify an existing migration**, because deployed
databases have already applied it. The repair's own commit message argues, and the
execution above confirms, that the rationale does not hold for this revision: **no
migration-built database can ever have applied it** — it aborts inside itself on
every clean database. The alternatives were each worse:

- a _later_ corrective migration is provably unreachable, because the abort happens
  before it;
- an _earlier_ one would have to rewire this revision's `down_revision`, which is
  also a modification of published history.

This is recorded as an authorized exception, not as a precedent. The owner reviews
whether that reasoning is accepted.

---

## 3. Migration graph, before and after

|                       | Before (`fe961550`) | After (`f92d4132` lineage, tip `dcf00fa1`)    |
| --------------------- | ------------------- | --------------------------------------------- |
| Revisions             | 101                 | 102                                           |
| Heads                 | `20260908_0001`     | `20260909_0001`                               |
| Head count            | 1                   | **1**                                         |
| New revision's parent | —                   | `20260909_0001.down_revision = 20260908_0001` |

**Single head is preserved.** The new revision chains off the previous head rather
than forking beside it, so no merge revision is needed. Read from
`ScriptDirectory.get_heads()` on each tree, not inferred.

---

## 4. Fresh-upgrade evidence on the owner branch

Executed here, in a detached worktree, against databases created empty moments
before. No manual column, no `ALTER TABLE`, no SQLite, no `create_all`.

### 4a. The repair's own effect — `upgrade 20260815_0023`

| Measurement                   | Value                                         |
| ----------------------------- | --------------------------------------------- |
| Database                      | `gula_nr003b_*`, PostgreSQL 16, created empty |
| Exit code                     | **`0`** (previously always aborted)           |
| Stamp reached                 | `20260815_0023`                               |
| `original_drug_catalog_id`    | `integer`                                     |
| `alternative_drug_catalog_id` | `integer`                                     |
| `id`                          | `character varying` — correctly left alone    |
| `pharmacy_drug_catalog.id`    | `integer`                                     |
| FK constraints created        | 3 of 3 — both catalog keys plus `lab_id`      |

### 4b. Full `upgrade head` on the owner branch

| Measurement        | Value                                                                                   |
| ------------------ | --------------------------------------------------------------------------------------- |
| Database           | `gula_nr003_*`, PostgreSQL 16, created empty                                            |
| Exit code          | `1`                                                                                     |
| Revisions executed | **98** (vs 94 unrepaired)                                                               |
| Aborting revision  | `20260820_0004`                                                                         |
| Error              | `psycopg2.errors.UndefinedTable: relation "hospital_operation_theaters" does not exist` |

**NR-003 is cleared. The next blocker is NR-028**, and it is the only one left in
front of head. The blocker chain is therefore exactly two links — established by
execution (94 → 98 revisions), not by argument.

---

## 5. Side-effect analysis — Pharmacy / POS / FHIR / LIMS

Every call site of the two retyped columns was enumerated across `backend/`,
`services/`, `frontend-v3/` and `tools/`.

| Area                   | Finding                                                                                                                                                                                                           | Evidence level           |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| **Pharmacy service**   | `app/pharmacy/services.py` (10 sites) always passes `original.id` / `alternative.id` — the catalog object's own primary key. Retyping the column to match that key makes these sites _more_ consistent, not less. | STATIC                   |
| **POS**                | `tests/test_pharmacy_pos.py:164-165, 214` builds rules from `original.id` and asserts on sale-line metadata. Type-agnostic; unaffected.                                                                           | STATIC                   |
| **FHIR / HL7**         | No reference to `drug_catalog`, `DrugCatalog` or `substitution` anywhere in `app/integration`, `app/lims` or `app/nhdw`. The new `drug_id` UUID is not yet exposed through any interoperability mapper.           | STATIC — grep, zero hits |
| **LIMS**               | Same: no reference.                                                                                                                                                                                               | STATIC — grep, zero hits |
| **`tools/gula_intel`** | `test_gula_intel.py:107` asserts the columns _exist_, not their type. Unaffected.                                                                                                                                 | STATIC                   |

### Two things the owner should decide on, both pre-existing

**(a) `pharmacy_drug_substitution_requests` still disagrees with the catalog.**
`app/pharmacy/models.py:924-925` declares that table's `original_drug_catalog_id`
and `alternative_drug_catalog_id` as `String(26)` with **no foreign key**. The
repair deliberately left them alone rather than guessing, and recorded it as a
follow-up. The consequence reads as a functional break in the POS substitution
approval path:

- `services.py:657` passes `request.original_drug_catalog_id` (a `String(26)`) into
  `list_substitution_candidates(...)`, which calls `get_drug(...)` against an
  `Integer` primary key and raises `ValueError("original drug not found")` when it
  misses;
- `services.py:764` assigns `drug_id = substitution_request.alternative_drug_catalog_id`
  and uses it as a catalog reference.

This is **not a regression introduced by the repair** — both sides predate it, and
the repair does not touch that table. It is also **STATIC only: not executed**, so
it is recorded as _reads as broken_, not _proven broken_. It should not block the
merge; it should get its own finding.

**(b) API response shape.** `frontend-v3/src/api/endpoints.ts:1706-1707, 1731-1732`
types both fields as `string`. After the repair they serialise as integers.
`CLAUDE.md` classes API response-shape changes as needing human approval because
they break mobile clients. **Scope for the owner's decision, not changed here.**

---

## 6. What the owner needs to do

**Review and merge `f92d4132`.**

The three later commits on that branch — `a98bf95b`, `1a164ccd`, `27b9e123`,
`dcf00fa1` — do **not** touch `migrations/` or the FK types. `1a164ccd` adds a
service-level identity-immutability guard, a contract document and
`tests/test_pharmacy_drug_identity.py`; the rest are documentation. They are
desirable but they are **not** part of the unblocking change. If the owner wants the
smallest reviewable unblocking diff, `f92d4132` alone is it, and it is
self-contained: 3 files, 169 insertions.

What must be re-run after the merge, because it cannot be inherited:

1. `alembic upgrade head` on a fresh PostgreSQL database — expected to reach
   `20260820_0004` and stop there until NR-028 is authorized.
2. `tests/migrations/test_migration_corpus_completeness.py` — the ordering guard is
   **expected to fail** once NR-028 clears, by design; that failure is the signal to
   re-measure the ICU evidence rather than inherit it.

---

## 7. Why no alternative repair was written here

| Alternative                                                   | Why it is refused                                                                                                                      |
| ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| A new migration correcting the FK types after `20260815_0023` | **Provably unreachable.** The abort happens inside `20260815_0023`, so nothing ordered after it ever runs.                             |
| A new migration before it                                     | Requires rewiring `20260815_0023.down_revision` — itself a modification of published history, and a second edit rather than one.       |
| Re-authoring the same in-place fix on this branch             | A **duplicate migration**. Two branches editing one historical revision is how a double-add reaches a database that later merges both. |
| Changing only the ORM to `String(26)`                         | Would make the ORM agree with a constraint PostgreSQL refuses to create. It cannot fix the migration.                                  |
| Adding the columns by hand / `ALTER TABLE`                    | Explicitly out of scope, and it produces a database no operator can rebuild.                                                           |

The repair is authored, owner-authorized, minimal, and verified. Writing a second
one would create a conflict with it for no gain. **The correct action is review and
merge, by the owner.**

---

## FINAL STATUS

**NR-003 = OWNER-AUTHORIZED REPAIR AVAILABLE / NOT MERGED.**

Verified by execution on fresh PostgreSQL that the repair clears the blocker
(94 → 98 revisions) and preserves a single head. Not merged, not pushed, not
cherry-picked. Two pre-existing follow-ups recorded for the owner's decision, neither
of which the repair introduces.
