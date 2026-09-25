# Evidence Package — ICU high-alert infusion, independent verification

**Operation:** `POST /critical-care/infusions/{infusion_id}/verify`
**Service:** `CriticalCareService.verify_infusion_safely`
**Generated:** 2026-09-25 · **Head:** `d8c2a31b` · **production_ready:** `false`
**Tests:** `backend/tests/verification/test_icu_infusion_verify_slice.py` (15) ·
`backend/tests/verification/test_schema_drift_guard.py` (10)

## Why this operation

It carries every control this layer exists to test in a single request: a state
transition, an authorization boundary, a tenant predicate, a row lock, an
optimistic version, a durable idempotency claim, an audit write — and one
clinical rule no generic framework could infer, the second-actor check on a
high-alert infusion.

`critical_care` also had the platform's worst ratio of protected clinical
commands to executed evidence: **8 guarded commands, 0 PostgreSQL tests, 0
concurrency tests.**

## Environment

| Item                      | Value                                                                                                                                                                                                   |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PostgreSQL                | 16.13                                                                                                                                                                                                   |
| Python                    | 3.13.12                                                                                                                                                                                                 |
| Schema built by           | `alembic upgrade 20260908_0002` — exit 0, 391 tables, ~4 min                                                                                                                                            |
| Why not `head`            | `alembic upgrade head` fails on an empty database at `20260505_0005`, on the pharmacy `original_drug_catalog_id` varchar ↔ `id` integer foreign key (NR-003). Reproduced twice, on two fresh databases. |
| `ENV` / `RUNTIME_MODE`    | `test` / `test`                                                                                                                                                                                         |
| Mocks replacing a control | none                                                                                                                                                                                                    |
| Authentication            | the real dependency for the 401 case; a seeded actor override for the rest                                                                                                                              |

## Part A — as the platform ships today

Every row executed over real HTTP against the migration-built database.

| #   | Scenario                              | Expected         | Observed                                  | Verdict               |
| --- | ------------------------------------- | ---------------- | ----------------------------------------- | --------------------- |
| A1  | Unauthenticated                       | 401              | **401**                                   | INVARIANT HOLDS       |
| A2  | Role `technician`                     | 403              | **403**                                   | HOLDS                 |
| A3  | Role `doctor`                         | 403              | **403**                                   | HOLDS                 |
| A4  | Roles `lab_admin`, `staff`, `citizen` | 403              | **403**                                   | HOLDS                 |
| A5  | Authorized, same tenant (happy path)  | 200 + transition | **500** `INTERNAL_ERROR`                  | **DEFECT — NR-023**   |
| A6  | Authorized, cross-tenant              | 404              | **500**                                   | **MASKED — NR-023**   |
| A7  | Stale `If-Match: 99`                  | 409              | **500**                                   | MASKED                |
| A8  | Absent `If-Match`                     | 428              | **500**                                   | MASKED                |
| A9  | Absent `Idempotency-Key`              | 400              | **500**                                   | MASKED                |
| A10 | Committed state after A5–A9           | unchanged        | `awaiting_verification`, version 1        | **no partial effect** |
| A11 | Durable claims                        | ≥ 1              | **0**                                     | **DEFECT — NR-024**   |
| A12 | Audit rows                            | ≥ 1              | **0**                                     | **DEFECT — NR-024**   |
| A13 | `DELETE FROM audit_logs`              | refused          | **refused** — `audit_logs is append-only` | INVARIANT HOLDS       |

Root cause, from the server log, not inferred:

```
(psycopg2.errors.UndefinedColumn) column critical_care_infusions.verified_by does not exist
[SQL: SELECT ... critical_care_infusions.verified_by ... FROM critical_care_infusions
      WHERE id = %(id_1)s AND lab_id = %(lab_id_1)s LIMIT 1 FOR UPDATE]
```

The route's opening statement selects every ORM column. Two of them do not exist.
So the failure precedes the guard, the version check, the tenant check and the
clinical rule — which is why A6 through A9 return 500 rather than their own
codes, and why the `except` branch's `guard.reject` is also lost.

### Why the column is missing

`20260820_0005_icu_infusion_independent_verification` adds `verified_by` and
`verified_at`. Its position in the graph was read, not assumed:

- `head` = `20260908_0001`, a merge of `("20260819_0004", "20260820_0005", "20260908_0002")`.
- `20260820_0005` ∈ ancestors(head) — **true** (101 ancestors).
- `20260820_0005` ∈ ancestors(`20260908_0002`) — **false** (73 ancestors).

So the columns arrive only via `head`, and `head` cannot be applied. On a fresh
`upgrade head` the stamped revision reaches `20260505_0005` and
`critical_care_infusions` is **not created at all**.

## Part B — the same operation with the two columns present

The two columns were added by hand to the **disposable** verification database
(`ALTER TABLE ... ADD COLUMN`), never to a shared or persistent one, and dropped
again afterwards. This establishes two things: that the controls are correct, and
that adding the columns is a sufficient fix.

| #   | Scenario                                   | Observed                                                                                                                   | Invariant                     |
| --- | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| B1  | Happy path                                 | **200** · `awaiting_verification → active` · `verified_by=75102` · version 1→2 · **1 completed receipt** · **1 audit row** | INV-STATE-01, INV-AUDIT-01    |
| B2  | Replay, same key and actor                 | **409** · state unchanged · still exactly **1 receipt**                                                                    | INV-IDEM-01                   |
| B3  | Initiator verifies their own infusion      | **422** "High-alert infusion verification requires an independent clinical actor" · state unchanged                        | **INV-ICU-01**                |
| B4  | Cross-tenant                               | **404** · row untouched                                                                                                    | INV-TENANT-01                 |
| B5  | Stale `If-Match`                           | **409**                                                                                                                    | INV-CAS-01                    |
| B6  | Absent `If-Match`                          | **428**                                                                                                                    | INV-CAS-01                    |
| B7  | Absent `Idempotency-Key`                   | **400**                                                                                                                    | INV-IDEM-01                   |
| B8  | **Two different actors race one infusion** | outcomes exactly **[200, 409]** · version 1→2 · 2 audit rows (1 success, 1 rejection)                                      | **INV-CONC-01**               |
| B9  | **Same actor, same key, raced**            | outcomes exactly **[200, 409]** · exactly **1 receipt**                                                                    | INV-IDEM-01 under concurrency |

B8 is the one that could not have been obtained on SQLite. Two independent
connections, released from a `threading.Barrier`, contend on the same
`SELECT ... FOR UPDATE`. Exactly one transition committed. Note what serialised
them: the receipts table is unique on `(lab_id, actor_user_id, operation, key)`,
so two _different_ actors hold two distinct claims — the idempotency key does not
separate them. Only the row lock does. That is INV-IDEM-02, and it matters
because widening the idempotency scope to the tenant would not strengthen this
operation; it would collide with the second-actor rule.

## Part C — negative proof

The protection perturbed here is the schema itself, on a disposable database.

| Step | Action                                                                             | Result                                                                                                                                           |
| ---- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1    | Baseline: run the suite                                                            | **24 passed**                                                                                                                                    |
| 2    | Perturb: `ALTER TABLE critical_care_infusions ADD COLUMN verified_by, verified_at` | columns present                                                                                                                                  |
| 3    | Re-run                                                                             | **10 failed / 14 passed** — every tripwire fired, plus both drift assertions                                                                     |
| 4    | Confirm the tripwires are real detectors                                           | the happy-path, cross-tenant, precondition, audit-gap and drift tripwires all failed; the authorization tests were unaffected, as they should be |
| 5    | Restore: `DROP COLUMN verified_by, verified_at`                                    | `select count(*) ... like 'verified%'` → **0**                                                                                                   |
| 6    | Re-run                                                                             | **25 passed** (24 + the append-only proof added in step 4's wake)                                                                                |

Nothing was left perturbed. No migration was modified. No historical revision was
touched.

## Part D — what remains unproven for this operation

| Invariant                                                | Why                                                                                                                                                   |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| INV-TXN-02 — failure after commit, before response       | `failure_injection` has an `after_commit` stage but no call site in `critical_care`. Adding one is a production-code change; WP-002.                  |
| INV-RECOVERY-01 — survives a database or service restart | No mechanism exists in this layer (FM-010, FM-011).                                                                                                   |
| Every Part B row **as shipped**                          | Part B was obtained on a hand-patched database. Until NR-023 is fixed through migrations, none of B1–B9 describes any database an operator can build. |

## Part E — regression guards left behind

| Guard                                                                        | What it catches                                                                                                                                                          |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `test_schema_drift_guard.py::test_no_clinical_command_table_gains_new_drift` | Any guarded clinical table losing a column it writes. Zero tolerance. **This is the guard that found `pharmacy_prescriptions` (15 columns) and `radiology_orders` (7).** |
| `…::test_known_critical_drift_is_pinned_exactly`                             | Each recorded divergence, column for column. Fails on repair _and_ on growth.                                                                                            |
| `…::test_platform_wide_drift_does_not_grow`                                  | The 84-table count.                                                                                                                                                      |
| `…::test_only_the_known_table_is_mapped_by_more_than_one_class`              | NR-006 spreading, or being swapped for a different dual mapping.                                                                                                         |
| `…::test_the_verification_database_was_built_by_migrations`                  | Refuses a `create_all` database, on which every assertion above would pass vacuously.                                                                                    |
| The slice's tripwires                                                        | Each fails the moment NR-023 is fixed, forcing the correct expectations to be written deliberately.                                                                      |
| `harness.requires_postgres()`                                                | 25 tests **skip**, never pass, with no database configured. Verified both ways.                                                                                          |

---

## Addendum — the operation executed on canonical head, 2026-09-25

The slice was re-run unchanged against a database built only by migrations to
canonical head (`gula_recovery`, stamp `20260909_0001`, 423 tables, **0 probe-created
tables**, schema from `claude/p0-1-hospital-migrations` @ `efcc4b6e`).

Result: **7 passed, 8 failed** — and every one of the eight failures is a tripwire
firing exactly as designed. A tripwire asserts today's defective behaviour so that it
breaks when the defect is fixed; these broke.

| Tripwire assertion (the defect)           | Observed on canonical head                                                                                                     |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| happy path returns **500**                | **409** — the command runs; the 409 is a replay/state conflict from repeated runs against a shared seed, not `UndefinedColumn` |
| cross-tenant returns **500**              | **404** — INV-TENANT-01 behaves correctly                                                                                      |
| absent `If-Match` returns **500**         | **428** — its own correct status                                                                                               |
| stale `If-Match` returns **500**          | **409** — its own correct status                                                                                               |
| failed command writes no receipt/audit    | the command no longer fails this way                                                                                           |
| ORM drift is `{verified_by, verified_at}` | **`set()`** — no drift                                                                                                         |
| concurrency/idempotency unproven          | the operation now reaches the guard                                                                                            |
| no partial effect survives the failure    | status is `active`, i.e. the verification **succeeded**                                                                        |

The seven that passed are the ones that were never schema-dependent: the 401, the five
403s, and the database-level refusal to delete audit history.

### What this does and does not establish

**Does:** `POST /critical-care/infusions/{id}/verify` is functional on a database an
operator can build from that chain — cross-tenant isolation answers 404, both
precondition failures return their own status codes, and the ORM↔database drift that
caused NR-023 is gone. These are WP-001's acceptance criteria, met by execution.

**Does not:** this is not the ICU FINAL PROOF. That proof was not attempted — the
handoff brief rules it out, and the chain is unmerged. The happy path returning 409
rather than 200 needs its own run against a per-test seed before anything is claimed
about it; the tripwire only tells us it is no longer 500. Concurrency, idempotency and
the audit trail for this operation remain **unproven**, because asserting the negation
of a tripwire is not the same as proving the positive.

So the status is unchanged and unshortened: **VERIFIED CONDITIONAL**. What changed is
that the conditionality now has a name — `efcc4b6e` — and a verified build, rather than
being a hypothetical.

### Consequence for anyone running this suite

Against a **head** database the slice reports 8 failures; against any database this
branch can build, it passes. That is the guard working, not breakage. The tripwires must
be rewritten to the repaired expectations **in the same change that lands the chain** —
not before, or the suite would assert behaviour no buildable database exhibits.
