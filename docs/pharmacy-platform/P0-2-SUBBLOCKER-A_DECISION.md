# P0-2-SUBBLOCKER-A — M3-0 decision report

**Status:** analysis complete. **No schema, migration or ORM change was made.**
**Physical authority:** migration-built PostgreSQL 16, `alembic upgrade head`, 103 revisions.
**Scope:** the six `VARCHAR(26)` columns on `pharmacy_sale_lines` and
`pharmacy_drug_substitution_requests` that name integer-keyed targets without a
foreign key.

---

## 1. Root cause — one cause, not six

All six columns share a single origin: **a Generation B identity assumption
materialised into the physical schema.**

Migrations `20260815_0022` (POS sales) and `20260815_0023` (substitution) were
authored in the Generation B worldview, where every pharmacy entity has a
`String(26)` `_ulid()` key. Read as evidence of intent rather than by naming,
both migrations show the author making a _correct_ choice three ways:

| Reference kind                                       | Target's real PK | What the migration wrote    |
| ---------------------------------------------------- | ---------------- | --------------------------- |
| `lab_id`, `billing_patient_id`, `billing_invoice_id` | `INTEGER`        | `Integer` **with** FK       |
| `sale_id`, `rule_id`, `consumed_sale_id`             | `VARCHAR(26)`    | `String(26)` **with** FK    |
| the six in question                                  | `INTEGER`        | `String(26)` **without** FK |

The FK is missing on exactly the columns where the ORM believed `String(26)`
but the physical target is `INTEGER`. That constraint is not merely absent — it
is **impossible**: PostgreSQL rejects a `varchar` foreign key onto an `integer`
primary key. The missing FK is the symptom; the type is the defect.

**This is not ORM↔schema drift.** `GULA-SCHEMA-002` reports zero findings on all
six columns: the ORM says `String(26)` and the database says `varchar(26)`, and
they agree. The disagreement is between the column's type and the key type of
the entity it names.

## 2. The six columns are two groups, not one

| Group                        | Columns                                                                                                   | Target                                                                  | Target state         |
| ---------------------------- | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | -------------------- |
| **A — catalog**              | `sale_lines.drug_catalog_id`, `requests.original_drug_catalog_id`, `requests.alternative_drug_catalog_id` | `pharmacy_drug_catalog.id` `INTEGER`                                    | **reconciled by M1** |
| **B — batch / prescription** | `sale_lines.batch_id`, `sale_lines.prescription_id`, `requests.prescription_id`                           | `pharmacy_drug_batches.id`, `pharmacy_prescriptions.id`, both `INTEGER` | **unreconciled, M4** |

Group B cannot be resolved yet. `DrugBatch` and the prescription models are
still Generation B, and the divergence is not only type-level: the ORM writes
`DrugBatch.drug_catalog_id`, a column the physical table **does not have** (it
has `drug_id integer`). Their canonical integer identity does not yet exist in
the application.

## 3. Decision matrix

| Column                                     | Semantic target | Current type           | Canonical type | FK status                            | Mapping evidence                                                                                                              | Data migration                                | Recommended action                                             | Risk                          |
| ------------------------------------------ | --------------- | ---------------------- | -------------- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- | -------------------------------------------------------------- | ----------------------------- |
| `pharmacy_sale_lines.drug_catalog_id`      | Drug (catalog)  | `varchar(26)` NOT NULL | `INTEGER`      | none; ORM declares an impossible one | Write path passes `DrugCatalog.id` (int since M1) → stored as decimal text; cast is deterministic **for post-M1 values only** | **None** — table is empty and unwritable (§4) | Convert with FK, as part of M3 sale-line entity reconciliation | Low, conditional on emptiness |
| `pharmacy_sale_lines.batch_id`             | Drug batch      | `varchar(26)` NOT NULL | `INTEGER`      | none                                 | **No mapping determinable.** `DrugBatch` unreconciled; ORM column absent from the physical table                              | Unknown until M4                              | **Defer to M4**                                                | Blocked on M4                 |
| `pharmacy_sale_lines.prescription_id`      | Prescription    | `varchar(26)` NULL     | `INTEGER`      | none; ORM declares an impossible one | **No mapping determinable.** Prescription identity unreconciled                                                               | Unknown until M4                              | **Defer to M4**                                                | Blocked on M4                 |
| `..._requests.original_drug_catalog_id`    | Drug (catalog)  | `varchar(26)` NOT NULL | `INTEGER`      | none; ORM declares no FK             | Write path passes `DrugCatalog.id` (int since M1)                                                                             | **None** (§4)                                 | Convert with FK, as part of M3                                 | Low, conditional on emptiness |
| `..._requests.alternative_drug_catalog_id` | Drug (catalog)  | `varchar(26)` NOT NULL | `INTEGER`      | none; ORM declares no FK             | As above                                                                                                                      | **None** (§4)                                 | Convert with FK, as part of M3                                 | Low, conditional on emptiness |
| `..._requests.prescription_id`             | Prescription    | `varchar(26)` NULL     | `INTEGER`      | none                                 | **No mapping determinable**                                                                                                   | Unknown until M4                              | **Defer to M4**                                                | Blocked on M4                 |

The sibling table `pharmacy_drug_substitution_rules` already carries the
canonical shape — `original_drug_catalog_id` / `alternative_drug_catalog_id` as
`INTEGER` with real FKs — from the NR-003 correction. It is the worked example
of the target state.

## 4. Data: none exists, and none can be written

Measured, not assumed:

- **0 rows** in `pharmacy_sales`, `pharmacy_sale_lines`,
  `pharmacy_drug_substitution_rules`, `pharmacy_drug_substitution_requests`,
  `pharmacy_drug_batches`, `pharmacy_prescriptions`.
- **No row can be written through the application.** All four owning tables
  carry ORM-only `fhir_id` / `fhir_resource_type`, so every ORM `INSERT` fails
  with `UndefinedColumn` before a row is created. Verified for each of the four.
  `DrugBatch` fails earlier still, on `drug_catalog_id`.
- **Raw SQL accepts anything.** A direct insert of
  `drug_catalog_id='NOT-A-REAL-DRUG-XXXXXXXXXX'` succeeded. There is no
  referential integrity on these columns at all. (Probe rows removed.)

**Production remains `PRODUCTION_DATA_NOT_PRESENT_IN_VERIFICATION_ENVIRONMENT`.**
One derived statement is safe: if a production deployment runs this application
against this schema, these tables cannot have been populated _by the
application_, because the insert fails before any write. Rows could only exist
from direct SQL or from an older schema.

## 5. Affected contracts

- **Public API:** `backend/app/pharmacy/routes.py` declares `drug_catalog_id`,
  `batch_id` and `prescription_id` as `str` in ~14 request/response schemas.
  Converting the storage type does not by itself change the wire contract, but
  the canonical public identity for a drug is `drug_id` (UUID4, contract §8),
  which is **M5/P1-1** and deliberately out of M3-0 scope.
- **Services:** `create_pos_sale`, `create_substitution_request` and the
  dispensing paths write these columns. All are already non-functional against
  the migrated schema.
- **Tests:** `test_pharmacy_pos.py` asserts the sale line's `drug_catalog_id`
  as **text** and names this sub-blocker in a comment; it becomes an integer
  comparison when the conversion lands.

## 6. Verification performed

Smallest set sufficient to establish the findings:

1. Physical types and PKs of the six columns and their three targets.
2. Migration source of both tables read for intent, not naming.
3. ORM declarations for both models.
4. Write-path tracing in `services.py`.
5. Row counts on all six related tables.
6. ORM insert probes for all four owning tables (all fail; cause captured).
7. Raw-SQL insert probe proving absence of referential integrity.
8. `GULA-SCHEMA-002` run against the migrated schema for per-table drift.

## 7. Conclusion

**The blocker is understood and is not ambiguous.** Root cause proven, canonical
direction unambiguous, and no data migration is required for Group A because no
data exists and none can be written.

**Group A (3 catalog columns) is ready to convert.** **Group B (3
batch/prescription columns) is BLOCKED on M4** — no deterministic mapping exists
until those entities are reconciled, and inventing one is forbidden.

The remaining question is sequencing, which is an architecture decision, not a
finding. See §8.

## 8. Decision required

Converting a foreign-key column to `INTEGER` while its own table's primary key
stays `VARCHAR(26)` leaves a half-migrated entity and guarantees a second
migration later. `pharmacy_sale_lines.id`, `pharmacy_sales.id` and
`pharmacy_drug_substitution_requests.id` are all still `varchar(26)`.

**Option 1 — narrow.** One migration now converting only the three Group A
columns to `INTEGER` with FKs, guarded fail-closed on emptiness. Removes the
sub-blocker for the catalog relationship immediately; leaves the owning tables'
identity unchanged and requires a further migration at M3/M4.

**Option 2 — whole-entity (recommended).** Fold the six into the M3 and M4
entity reconciliations, converting each entity's own key and its outbound
references in one coherent migration per entity. Fewer migrations, no
half-migrated state, and Group B is only solvable this way regardless.

Either option requires an explicit emptiness precondition enforced **in** the
migration (the NR-003 fail-closed pattern), because production row counts are
not knowable from this repository.
