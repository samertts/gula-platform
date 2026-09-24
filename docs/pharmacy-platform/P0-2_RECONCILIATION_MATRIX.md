# P0-2 — Pharmacy ORM ↔ Physical Schema Reconciliation Matrix (Phase 2A)

**Status:** Phase 2A COMPLETE — analysis only. **No code was modified.**
**M1 applied:** `pharmacy_drug_catalog` is now fully reconciled (34/34 columns
KEEP); its rows below describe the pre-M1 state and are retained as the record
of what was changed. Every other table is unchanged and still accurate.
**Physical authority:** migration-built PostgreSQL 16, `alembic upgrade head`,
103 revisions, exit 0. Not SQLite, not ORM metadata, not documentation.
**Machine-readable:** `P0-2_RECONCILIATION_MATRIX.json` (full records + rename
analysis) and `P0-2_RECONCILIATION_MATRIX.csv` (one row per column).

Every record carries: table, column, ORM type, PostgreSQL type, nullable,
default, PK, FK target, unique, index, ORM-only, DB-only, classification.

---

## 1. Scope actually measured

| Measure                             | Value   |
| ----------------------------------- | ------- |
| Pharmacy tables mapped by the ORM   | 27      |
| Pharmacy tables present physically  | 27      |
| ORM tables with no physical table   | **0**   |
| Physical pharmacy tables not mapped | **0**   |
| Column-level records                | **867** |

The 23-entity figure is confirmed exactly: **23 of 27 tables carry a primary-key
type conflict** (`VARCHAR(26)` in the ORM vs `INTEGER` physically). The four
without one are precisely the KEEP+RECONCILE set — `pharmacy_sales`,
`pharmacy_sale_lines`, `pharmacy_drug_substitution_rules`,
`pharmacy_drug_substitution_requests`.

The "~540 column-level differences" figure resolves to **568** non-KEEP records
once timestamp false positives are removed (see §6).

## 2. Classification totals

| Classification  | Count | Meaning                                                                             |
| --------------- | ----: | ----------------------------------------------------------------------------------- |
| KEEP            |   299 | ORM already matches physical schema                                                 |
| RECONCILE       |   219 | same field, wrong name/type/nullability/FK in the ORM                               |
| REMOVE_FROM_ORM |   173 | ORM declares a column with no physical counterpart                                  |
| DEFER           |   153 | physical column absent from ORM but nullable or defaulted; plus 8 ambiguous renames |
| REPLACE         |    23 | primary-key identity conflict — the Generation B `_ulid()` model                    |

## 3. Per-table matrix

| Table                                 | KEEP | RECONCILE | REPLACE | REMOVE_FROM_ORM | DEFER | Total |
| ------------------------------------- | ---: | --------: | ------: | --------------: | ----: | ----: |
| `pharmacy_allergy_rules`              |    8 |         7 |       1 |               5 |     5 |    26 |
| `pharmacy_clinical_guidelines`        |   14 |         4 |       1 |               5 |     7 |    31 |
| `pharmacy_contraindication_rules`     |    9 |         4 |       1 |               7 |     5 |    26 |
| `pharmacy_dispense_queue`             |    8 |         7 |       1 |               7 |     6 |    29 |
| `pharmacy_dispense_records`           |   10 |        12 |       1 |              11 |     9 |    43 |
| `pharmacy_dose_guidelines`            |   10 |        11 |       1 |               9 |     9 |    40 |
| `pharmacy_drug_batches`               |   13 |        10 |       1 |               5 |     5 |    34 |
| `pharmacy_drug_catalog`               |   14 |        15 |       1 |              16 |    13 |    59 |
| `pharmacy_drug_interaction_rules`     |    9 |         4 |       1 |               8 |     4 |    26 |
| `pharmacy_drug_monitoring`            |   10 |         5 |       1 |               6 |    13 |    35 |
| `pharmacy_drug_returns`               |    8 |        13 |       1 |               4 |     3 |    29 |
| `pharmacy_drug_substitution_requests` |   24 |         1 |       0 |               2 |     0 |    27 |
| `pharmacy_drug_substitution_rules`    |   16 |         1 |       0 |               2 |     0 |    19 |
| `pharmacy_drug_suppliers`             |   10 |        11 |       1 |               3 |     3 |    28 |
| `pharmacy_inventory_forecasts`        |    7 |        10 |       1 |               7 |    10 |    35 |
| `pharmacy_inventory_transfer_items`   |    5 |         5 |       1 |               7 |     5 |    23 |
| `pharmacy_inventory_transfers`        |    8 |         9 |       1 |               6 |     9 |    33 |
| `pharmacy_prescription_items`         |    8 |        11 |       1 |              15 |     7 |    42 |
| `pharmacy_prescriptions`              |    9 |         9 |       1 |              14 |    10 |    43 |
| `pharmacy_recalls`                    |   11 |        10 |       1 |               3 |     7 |    32 |
| `pharmacy_sale_lines`                 |   24 |         4 |       0 |               2 |     0 |    30 |
| `pharmacy_sales`                      |   24 |         3 |       0 |               2 |     0 |    29 |
| `pharmacy_stock_levels`               |    7 |        14 |       1 |               6 |     7 |    35 |
| `pharmacy_stock_movements`            |    9 |        11 |       1 |               6 |     3 |    30 |
| `pharmacy_stores`                     |    8 |        10 |       1 |               3 |     1 |    23 |
| `pharmacy_warehouses`                 |    8 |         8 |       1 |               6 |    10 |    33 |
| `pharmacy_waste_records`              |    8 |        10 |       1 |               6 |     2 |    27 |

## 4. The identity defect, precisely located

**54 columns are `VARCHAR(26)` in the ORM where PostgreSQL holds `INTEGER`:**

- **23** are primary keys → classification `REPLACE`. This is the
  `BaseEntity.id = Column(String(26), default=_ulid)` model in
  `app/pharmacy/base.py`.
- **31** are internal foreign keys → classification `RECONCILE`. These are
  contract §11 `INTERNAL_FK` fields and must match the relational primary key
  type. This is exactly the Phase 2C invariant 6 violation
  ("no `String(26)` internal FK pretending to reference an Integer PK"),
  now enumerated rather than estimated.

The catalog foreign key has **two distinct shapes**, and they must not be
treated alike:

| Shape             | Tables | ORM                           | Physical          | Action                            |
| ----------------- | -----: | ----------------------------- | ----------------- | --------------------------------- |
| Renamed FK        |      8 | `drug_catalog_id VARCHAR(26)` | `drug_id INTEGER` | rename + retype the ORM attribute |
| Denormalised code |      4 | `drug_code VARCHAR(50)`       | `drug_id INTEGER` | drop the ORM code, adopt the FK   |

## 5. Clinical rules — proven FK paths (Phase 2D prerequisite)

Queried from `pg_constraint` on the migration-built schema:

| Table                              | Physical FK column                                        | Type    | References                 |
| ---------------------------------- | --------------------------------------------------------- | ------- | -------------------------- |
| `pharmacy_contraindication_rules`  | `drug_id`                                                 | integer | `pharmacy_drug_catalog.id` |
| `pharmacy_allergy_rules`           | `drug_id`                                                 | integer | `pharmacy_drug_catalog.id` |
| `pharmacy_dose_guidelines`         | `drug_id`                                                 | integer | `pharmacy_drug_catalog.id` |
| `pharmacy_drug_monitoring`         | `drug_id`                                                 | integer | `pharmacy_drug_catalog.id` |
| `pharmacy_drug_interaction_rules`  | `drug_id_a`, `drug_id_b`                                  | integer | `pharmacy_drug_catalog.id` |
| `pharmacy_drug_substitution_rules` | `original_drug_catalog_id`, `alternative_drug_catalog_id` | integer | `pharmacy_drug_catalog.id` |

**`drug_code` exists on exactly one physical table: `pharmacy_drug_catalog`.**
No clinical-rule table has a physical `drug_code` column.

Consequences, both decisive for Phase 2D:

1. Contract §7 ("editing a business code can never detach a clinical safety
   rule") **already holds in the database**. It is an ORM-only defect.
2. There is **no data to migrate and no ambiguous value mapping** — the ORM's
   `drug_code` on rule tables has never been persisted. The fix is
   `REMOVE_FROM_ORM` plus adopting the existing `drug_id` FK. No data
   transformation is required or permitted.

## 6. Two false-positive classes eliminated

Recorded because both would have produced fabricated work:

1. **Timestamp timezone.** Reflecting a column as `str(type)` renders
   `TIMESTAMP(timezone=True)` as `"TIMESTAMP"`, fabricating a mismatch against
   the ORM's `DateTime(timezone=True)`. Verified against
   `information_schema`: `pharmacy_drug_catalog.created_at` really is
   `timestamp with time zone`. Both sides are now rendered through the
   PostgreSQL dialect. **84 spurious RECONCILE rows removed.**
2. **String-similarity renames.** Substring matching paired
   `fhir_resource_type` with `source` (`source` is inside `re-source-`) and
   `atc_description` with `package_description`. Replaced by token-subset
   matching requiring a unique best pairing in both directions.

## 7. Rename analysis

**35 unambiguous pairs** — one field under two names. These are `RECONCILE`
(rename the ORM attribute), never a drop plus an add.

**8 ambiguous pairs — fail-closed, unresolved.** Each has more than one
plausible counterpart, so no ORM change may be made against them until they are
resolved from per-column evidence:

| Table                               | ORM column           | Competing physical columns                                                         |
| ----------------------------------- | -------------------- | ---------------------------------------------------------------------------------- |
| `pharmacy_drug_catalog`             | `strength_value`     | `strength`, contested by `strength_unit`                                           |
| `pharmacy_drug_catalog`             | `strength_unit`      | `strength`, `unit`                                                                 |
| `pharmacy_inventory_transfer_items` | `quantity_requested` | `quantity`, `quantity_requested`, `quantity_received`                              |
| `pharmacy_inventory_transfer_items` | `quantity_shipped`   | as above                                                                           |
| `pharmacy_inventory_transfer_items` | `quantity_received`  | as above                                                                           |
| `pharmacy_stock_levels`             | `quantity`           | `quantity_available`, `quantity_reserved`, `quantity_on_hand`, `quantity_on_order` |
| `pharmacy_prescription_items`       | `drug_catalog_id`    | `drug_id`, contested by `drug_batch_id`/`batch_id`                                 |
| `pharmacy_prescription_items`       | `drug_batch_id`      | `batch_id`, contested as above                                                     |

## 8. Runtime-breaking gaps

**62 physical columns are `NOT NULL` with no default and unknown to the ORM.**
Any ORM `INSERT` into those tables fails outright. 13 are explained by an
unambiguous rename, leaving **49 genuinely unmapped**, of which **17 are the
catalog foreign key** across 16 tables.

`pharmacy_drug_catalog` alone has four: `drug_id` (UUID), `drug_code`,
`drug_name`, `dosage_form`.

## 9. Foreign-key divergences (35)

- **19 tables**: `lab_id` has a physical FK to `labs.id` that the ORM does not declare.
- **6 columns**: the ORM targets a different table than the database —
  `national_practitioners.id` vs `lab_users.id`, `national_patients.id` vs
  `patients.id`. These FKs cannot even be resolved from `PharmacyBase.metadata`,
  because those tables belong to a different declarative base.
- **6 columns** are `varchar(26)` **in PostgreSQL itself**, carry no FK
  constraint, and name a target whose primary key is `INTEGER` — see §9a. This
  is a physical defect, not an ORM one.

### 9a. BLOCKER — unconstrained `varchar(26)` references in the physical schema

Queried from `information_schema` and `pg_constraint`:

| Table                                 | Column                        | Physical type | FK constraint | Implied target PK                       |
| ------------------------------------- | ----------------------------- | ------------- | ------------- | --------------------------------------- |
| `pharmacy_sale_lines`                 | `drug_catalog_id`             | `varchar(26)` | **none**      | `pharmacy_drug_catalog.id` — `integer`  |
| `pharmacy_sale_lines`                 | `batch_id`                    | `varchar(26)` | **none**      | `pharmacy_drug_batches.id` — `integer`  |
| `pharmacy_sale_lines`                 | `prescription_id`             | `varchar(26)` | **none**      | `pharmacy_prescriptions.id` — `integer` |
| `pharmacy_drug_substitution_requests` | `original_drug_catalog_id`    | `varchar(26)` | **none**      | `pharmacy_drug_catalog.id` — `integer`  |
| `pharmacy_drug_substitution_requests` | `alternative_drug_catalog_id` | `varchar(26)` | **none**      | `pharmacy_drug_catalog.id` — `integer`  |
| `pharmacy_drug_substitution_requests` | `prescription_id`             | `varchar(26)` | **none**      | `pharmacy_prescriptions.id` — `integer` |

These sit on the four tables the Generation B disposition marks KEEP+RECONCILE,
so they are **not** reachable by the ORM replacement. Making the ORM "match the
physical schema" here would mean adopting a reference that can never resolve —
a `varchar(26)` value cannot address an `integer` primary key.

**Phase 2E is therefore fail-closed on these six columns.** Options are a schema
migration converting them to `INTEGER` foreign keys, or an explicit decision to
leave them unconstrained; both are schema decisions that `CLAUDE.md` places
behind human approval. Nothing here is guessed or transformed.

This supersedes delivery-baseline item **P2-2**, which recorded two such
columns; there are six, and three of them are on `pharmacy_sale_lines`.

## 10. Canonical invariants — physical status

| Invariant                                | Physical status                                |
| ---------------------------------------- | ---------------------------------------------- |
| Catalog internal PK is `Integer`         | HOLDS — `id integer`, `nextval(...)`           |
| Catalog public identity is UUID4         | HOLDS — `drug_id uuid NOT NULL`                |
| `drug_code` is a mutable business code   | HOLDS — `varchar(50) NOT NULL`, not a key      |
| Catalog is global, no tenancy            | HOLDS — no `lab_id` column exists physically   |
| Clinical rules keyed on FK, not code     | HOLDS — see §5                                 |
| No `String(26)` FK against an Integer PK | **VIOLATED in the ORM only** — 31 columns (§4) |

The ORM contradicts invariants 1, 2, 4 and 6. `lab_id` on the catalog is
ORM-only, which means the global-catalog decision needs **no migration** — only
removal of an ORM column that was never persisted.

## 11. Reproduction

```bash
createdb p02_matrix
DATABASE_URL=postgresql+psycopg2://…/p02_matrix alembic upgrade head   # 103 revisions
python build_matrix.py > matrix.json      # physical vs ORM, both dialect-rendered
python renames.py matrix.json renames.json
```

## 12. What Phase 2A does NOT establish

- No ORM, service, route or migration file was changed.
- No ORM query was executed against the physical schema yet (Phase 2H).
- The 8 ambiguous renames are unresolved by design.
- Endpoint impact is not re-counted here; the 63-endpoint figure is carried
  forward from the NR-003 analysis and not independently re-verified.
