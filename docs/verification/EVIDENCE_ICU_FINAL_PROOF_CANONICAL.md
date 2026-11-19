# ICU Final Proof — canonical lineage

**Executed:** 2026-09-25 · **Result: VERIFIED** · 22 tests passed, 3 negative proofs

Subject: `POST /critical-care/infusions/{id}/verify` — the independent second-actor
check standing between a clinician and activating a high-alert infusion
(norepinephrine, insulin, heparin, potassium chloride, propofol, fentanyl, midazolam,
epinephrine).

This supersedes the tripwire slice, which asserted the _defective_ behaviour. Here the
repaired behaviour is asserted **positively**: nothing below is inferred from the
negation of a tripwire.

---

## Lineage and commit

| Field                                 | Value                                                                                                                                |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Verification lineage                  | `claude/p0-1-hospital-migrations`                                                                                                    |
| **Commit**                            | **`efcc4b6e4769caf9a03f4c18051a15408ed1ce05`** (`efcc4b6e`, 2026-09-09)                                                              |
| NR-003 correction present             | **yes** — `f92d4132` proven an ancestor by `git merge-base --is-ancestor`                                                            |
| `critical_care` / `clinical` app code | **byte-identical** to `claude/http-idempotency-phase-14b-6g7fna` (`git diff` empty), so the result is not an artefact of the lineage |
| Database                              | `gula_canon`, PostgreSQL 16, created empty, schema from migrations only — **0 probe-created tables, 0 manual columns**               |

The `http-idempotency` branch was **not** used as the verification lineage, per the
brief: it still carries the pre-canonical pharmacy identity.

## Preconditions

| #   | Precondition                                  | Result                  | Evidence                                                                                       |
| --- | --------------------------------------------- | ----------------------- | ---------------------------------------------------------------------------------------------- |
| 1   | Current git commit                            | **VERIFIED**            | `efcc4b6e4769caf9a03f4c18051a15408ed1ce05`                                                     |
| 2   | `pharmacy_drug_catalog.id` INTEGER end-to-end | **PARTIAL — see below** | physical PASS, ORM DEFECT                                                                      |
| 3   | Single Alembic head                           | **VERIFIED**            | `ScriptDirectory.get_heads()` → `['20260909_0001']`, 1 head, 103 revisions                     |
| 4   | Fresh PostgreSQL upgrade to head              | **VERIFIED**            | 0 tables → `alembic upgrade head` **exit 0**, 103 revisions, stamp `20260909_0001`, 423 tables |
| 5   | `downgrade -1`                                | **VERIFIED**            | **exit 0** → stamp `20260908_0001`, `pharmacy_drug_catalog.drug_id` gone (0 columns)           |
| 6   | Re-upgrade to head                            | **VERIFIED**            | **exit 0** → stamp `20260909_0001`, `drug_id` restored (1 column), 423 tables                  |

Round trip is clean in both directions.

### Precondition 2 — split result, and a new finding

**Physical layer: VERIFIED.** `pharmacy_drug_catalog.id` is `integer`, and **all 18**
foreign keys referencing it are `integer → integer`, read from `pg_constraint` with
both column types joined — including the two `pharmacy_drug_substitution_rules`
columns that NR-003 repaired.

**ORM layer: VERIFIED DEFECT.** Ten **live** classes in `app.pharmacy.models` declare
a `drug_catalog_id` column as `VARCHAR(26)` with a foreign key onto that `integer`
primary key: `DrugBatch`, `DrugReturn`, `InventoryForecast`, `InventoryTransferItem`,
`PrescriptionItem`, `Recall`, `PharmacySaleLine`, `StockLevel`, `StockMovement`,
`WasteRecord`. The physical columns are named `drug_id` and are `integer`, so these
ORM attributes are both mistyped _and_ misnamed relative to the schema.

This is **not a migration defect** — the migrations produce the correct integer
columns — so **no migration was created**, per the brief. It is an ORM-side finding,
recorded as **NR-031**.

**It does not block this proof, and that is measured rather than asserted:**
`critical_care` declares **10 foreign keys and zero of them reference pharmacy**. The
two domains do not touch.

---

## The verification — 22 tests, all passing

`backend/tests/verification/test_icu_final_proof.py`, real HTTP through the real app,
real PostgreSQL, per-test seeding.

| #   | Requirement                | Result       | Observed                                                                                                                                                                                          |
| --- | -------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Real HTTP authentication   | **VERIFIED** | **401** with the real auth dependency in place (`actor=None`), state unchanged                                                                                                                    |
| 2   | Authorization              | **VERIFIED** | **403** for `technician`, `doctor`, `lab_admin`, `staff`, `citizen`; none changed state                                                                                                           |
| 3   | Tenant isolation           | **VERIFIED** | **404**, not 403 — indistinguishable from the row not existing, so a foreign tenant learns nothing                                                                                                |
| 4   | Ownership (INV-ICU-01)     | **VERIFIED** | initiator verifying their own infusion → **422** "requires an independent clinical actor"; `verified_by`/`verified_at` still NULL                                                                 |
| 5   | Valid transition           | **VERIFIED** | **200**; `awaiting_verification → active`, version 1→2, `verified_by = 74202`, `verified_at` set, `verified_by != initiated_by`                                                                   |
| 6   | Invalid transition         | **VERIFIED** | second activation of an active infusion refused; status, version and `verified_by` all unchanged                                                                                                  |
| 7   | `If-Match` absent          | **VERIFIED** | **428**                                                                                                                                                                                           |
| 8   | `If-Match` stale           | **VERIFIED** | **409**                                                                                                                                                                                           |
| 9   | Idempotency key absent     | **VERIFIED** | **400**                                                                                                                                                                                           |
| 10  | Replay                     | **VERIFIED** | same key → refused, durable state byte-identical, **exactly one** receipt                                                                                                                         |
| 11  | Concurrent actors          | **VERIFIED** | two _different_ verifiers, barrier-released, own connections → **exactly one 200**; version 1→2 once                                                                                              |
| 12  | Exactly one durable effect | **VERIFIED** | across replay and the race: one reservation of the transition, one receipt, one version bump                                                                                                      |
| 13  | Audit persistence          | **VERIFIED** | one audit row per activation, correct actor and `resource_type`, chain hash present, `state_before`/`state_after`/`version_before`/`version_after` all recorded; `DELETE` refused by the database |
| 14  | Rollback on failure        | **VERIFIED** | a real in-transaction clinical failure leaves status, version and both verification columns untouched                                                                                             |
| 15  | Retry behaviour            | **VERIFIED** | after a 409 for a stale `If-Match`, a corrected retry with a fresh key succeeds — no dead end for a clinical action                                                                               |
| 16  | Regression guards          | **VERIFIED** | both columns physically present; `missing_physical_columns` empty; `alembic_version` pinned to `20260909_0001` so a `create_all` database cannot pass                                             |

Concurrency uses two **different** actors deliberately: receipts are unique per
`(lab_id, actor_user_id, operation, idempotency_key)`, so the receipt cannot serialise
them (INV-IDEM-02). Only the row lock can — which is what test 11 actually tests.

### Failure injection — NOT_TESTED, with the reason

`critical_care` contains **no `maybe_fail` call site** (all nine are in Blood Bank plus
one shared helper). Injection-based rollback therefore has no mechanism for this
operation. Rollback was proven instead through a real clinical-rule failure, and the
injection variant is reported **NOT_TESTED** rather than folded into the pass.

## Negative proofs

| #   | Mutation                                          | Expected                      | Observed                                                                                                   |
| --- | ------------------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------- |
| 1   | Drop `verified_by` on a clone of the database     | the proof must fail           | **20 of 22 failed**; clone discarded; pristine migration-built database → **22 passed**                    |
| 2   | Delete the receipt before the replay              | the replay must be accepted   | **failed** as required — `the replay created a second receipt … 0 == 1`                                    |
| 3   | Make the verifier the initiator on the happy path | the clinical rule must refuse | **failed** as required — **422** "High-alert infusion verification requires an independent clinical actor" |

Negative proof 3 is the clinically decisive one: it shows the second-actor rule is
load-bearing rather than incidental. Negative proof 1 is the one the schema question
turned on — without the column, the operation is unreachable.

## Findings recorded, not patched

| ID         | Finding                                                                                                                                                                                                                                                                                                                                                               | Classification                                                                                          |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **NR-031** | 10 live `app.pharmacy.models` classes declare `drug_catalog_id VARCHAR(26)` onto the `integer` catalog PK; the physical columns are `drug_id integer`. Migrations are correct — this is ORM-side.                                                                                                                                                                     | **BLOCKED_BY_UPSTREAM_FAILURE** for pharmacy; **does not affect ICU** (zero critical_care↔pharmacy FKs) |
| **NR-032** | `audit_logs.resource_id` is `integer` while all **13** `critical_care_*` tables have `character varying` primary keys, so `ClinicalCommandGuard._audit_resource_id` returns None and the identity is preserved in `details.resource_id` instead. A deliberate compensation, documented in the guard — but no audit query can filter clinical events by `resource_id`. | **VERIFIED DEFECT (MEDIUM)** — fixing it is a schema change, so not done here                           |

### NR-024 refined by this proof

NR-024 recorded that "a failing protected clinical command writes no receipt and no
audit row". On the canonical lineage a refused ICU verification **is** audited:
`clinical.icu.infusion.verify.rejected`, naming the actor, the infusion, the state
before, and the reason — _"High-alert infusion verification requires an independent
clinical actor"_. Asserted positively in test 18.

NR-024's original measurement was taken when the **database itself** was the failure
(`UndefinedColumn`), so `guard.reject` shared the broken dependency it was trying to
record. That narrower statement still stands and is still a real gap. The blanket
claim does not.

---

## FINAL STATUS

**VERIFIED** — `POST /critical-care/infusions/{id}/verify` on commit `efcc4b6e`,
against PostgreSQL 16 built from migrations alone to canonical head `20260909_0001`,
with 22 passing tests and 3 negative proofs.

Scope stated plainly:

- **VERIFIED:** authentication, authorization, tenant isolation, ownership, valid and
  invalid transitions, `If-Match`, idempotency, replay, concurrent actors, exactly one
  durable effect, audit persistence, rollback on a real failure, retry, regression.
- **NOT_TESTED:** injection-based rollback for ICU — no call site exists.
- **BLOCKED_BY_UPSTREAM_FAILURE:** nothing on this path. NR-031 blocks pharmacy work,
  not this operation.
- **UNKNOWN:** nothing on this path.

The one conditionality that remains is not about the operation but about the lineage:
`efcc4b6e` is **unmerged**, so this evidence cannot be reproduced on `main` until that
chain lands. The proof itself is unconditional on the lineage it names.

No merge, no push, no deployment. NR-003 unmodified. No second pharmacy identity
implementation. No migration created.
