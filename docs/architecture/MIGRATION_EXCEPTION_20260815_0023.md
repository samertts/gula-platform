# Migration Policy Exception — `20260815_0023`

**Status:** GRANTED (one-off), by the project owner
**Date:** 2026-09-09
**Scope:** `backend/migrations/versions/20260815_0023_drug_substitution.py` only
**Related:** NR-003, ADR-006 (pharmacy drug identity model)

## The rule being excepted

`CLAUDE.md`, Migration Policy (MANDATORY): **"Never modify an existing
migration"** — because existing databases have already run it.

## Why the rule's rationale does not hold here

`20260815_0023` declared two foreign keys to `pharmacy_drug_catalog.id` as
`String(26)`, while that primary key is `Integer` (created by `20260716_0003`).
PostgreSQL rejects the constraint, so the migration **aborted inside itself on
every migration-built database**. No such database can have applied it, which
is precisely the condition the rule protects.

## Executable evidence

Reproduced on disposable PostgreSQL 16 before the correction:

```
Running upgrade 20260815_0022 -> 20260815_0023, Institution-scoped drug substitution rules…
psycopg2.errors.DatatypeMismatch: foreign key constraint
  "pharmacy_drug_substitution_rules_original_drug_catalog_id_fkey" cannot be implemented
alembic_version after the attempt: 20260505_0005
```

Three findings followed, each verified rather than argued:

1. **A later corrective migration is provably unreachable.** The abort happens
   inside `0023` and the transaction rolls back, so no revision ordered after it
   ever runs.
2. **An earlier corrective migration would also modify published history**,
   because inserting one requires rewiring this revision's `down_revision`.
3. **The repair shape works.** Pre-creating the table with `Integer` foreign
   keys on a probe database caused `0023`'s existing `_table_exists` guard to
   skip its create and complete, recording `20260815_0023`.

In-place correction was therefore the only available repair.

## What was changed

Two column type declarations, nothing else:

```
original_drug_catalog_id     String(26) -> Integer
alternative_drug_catalog_id  String(26) -> Integer
```

Deliberately unchanged: the revision id, `down_revision`, migration ordering,
table names, all other columns, the guarded behaviour, and the downgrade.

`id` and `rule_id` remain `String(26)` — they are these tables' own identities,
not catalog references. The two `String(26)` columns on
`pharmacy_drug_substitution_requests` carry no foreign key and were **left
alone rather than guessed at**; they are recorded as a follow-up inconsistency.

## Verification after the correction

- Clean database `alembic upgrade 20260815_0023`: **exit 0** (previously impossible).
- Both columns confirmed `integer` via `pg_constraint`.
- A clean database now applies **98 revisions**, up from ~30 followed by rollback.
- Detector `GULA-SCHEMA-001`: **VERIFIED**, no findings (previously two P0s).

## Limits of this exception

This is **not** a policy change. It applies to `20260815_0023` alone and does
not authorise modifying any other published migration. The bar that was met
here — executable proof that the revision cannot succeed on any
migration-built database, and that no corrective migration can reach it — must
be met again, and granted again, for any future in-place correction.
