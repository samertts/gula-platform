# P0-2 M4 — Batch, prescription, inventory and dispensing reconciliation

**Status:** PARTIALLY VERIFIED. The identity and relational model is complete and
drift-free; two named gaps remain, both recorded rather than worked around.
**Physical authority:** migration-built PostgreSQL 16, `alembic upgrade head`,
105 revisions.

---

## 1. What M4-0 found

The physical schema was already right. All 27 Pharmacy tables key on `INTEGER`,
and the relational graph between catalog, batches, stock, prescriptions and
dispensing is complete and fully constrained — 48 intra-Pharmacy foreign keys,
all enforced.

The **ORM** was the fiction. Across seventeen models:

- **145 columns** the ORM mapped that the database does not have;
- **150 physical columns** nothing mapped;
- ~90 type mismatches on top.

The clearest case is the one M3 flagged: `DrugBatch.drug_catalog_id`. It was
never a column. The table names the catalog through `drug_id`, and
`pharmacy_drug_batches_drug_id_fkey` has been enforcing that all along. The ORM
mapped a name that does not exist, which is why no batch could ever be written.

**The dependency graph closed over all seventeen models.** Eight of them declare
`ForeignKey("pharmacy_drug_batches.id")`, so the moment that key became `INTEGER`
in the ORM, every one of them had to move too — there is no smaller coherent cut.

## 2. Canonical identity (M4-1, M4-2)

Derived from the physical constraints and the model M1–M3 already established.

| Entity | Internal key | Public identity | Business code |
| --- | --- | --- | --- |
| `pharmacy_drug_batches` | `id INTEGER` | `batch_id UUID4` | `batch_number` |
| `pharmacy_prescriptions` | `id INTEGER` | `prescription_id UUID4` | `prescription_number` |
| `pharmacy_prescription_items` | `id INTEGER` | `prescription_item_id UUID4` | — |
| `pharmacy_dispense_queue` | `id INTEGER` | `queue_id UUID4` | `queue_number` |
| `pharmacy_inventory_transfers` | `id INTEGER` | `transfer_id UUID4` | `transfer_number` |

Public identifiers were added to exactly the five entities the API addresses by
id (`/batches/{batch_id}`, `/prescriptions/{rx_id}`, `.../items/{item_id}`,
`/dispense-queue/{queue_id}`, `/inventory/transfers/{transfer_id}`). All five
were `str` on the wire already, so the shape is unchanged; what changed is that
the value is now a public identity rather than a Generation B key. The other
twelve entities are not addressed by id and did not get one.

**DrugBatch's catalog reference is `drug_id`, proven by constraint, not naming.**
`drug_catalog_id` has never existed physically.

**Prescription has no practitioner relationship.** `prescribed_by` is the
prescriber's name as free text and `prescriber_license` their licence number.
The previous ORM declared `prescriber_id`; M4 did not invent the relationship
the schema declines to model.

## 3. Ownership model (M4-4)

Kept distinct, as instructed:

- **National Drug Catalog** — global, no tenant column, one row per drug.
- **Facility inventory** (`pharmacy_stock_levels`) — tenant-scoped, references
  the global catalog by internal foreign key. No per-facility catalog rows.
- **Drug batch** — tenant-scoped lot of one catalog drug.
- **Stock movement** — append-only log; `reference_type`/`reference_id` is a
  polymorphic pointer, `reference_id` being `INTEGER`.
- **Dispensing** — records against prescription, item, drug and batch.

Two tenancy corrections came out of the physical schema:
`pharmacy_prescription_items` and `pharmacy_inventory_transfer_items` have **no**
`lab_id` (they are scoped through their parent), and
`pharmacy_clinical_guidelines` has none either — it is national reference data,
not tenant data, and the previous ORM gave it a tenant column that does not exist.

## 4. Group B — resolved

M3 deferred three references because their targets had no canonical application
model. M4 supplied one, so all three are now `INTEGER` with enforced foreign keys:

| Column | Now |
| --- | --- |
| `pharmacy_sale_lines.batch_id` | `fk_pharmacy_sale_lines_batch` → `pharmacy_drug_batches(id)` RESTRICT |
| `pharmacy_sale_lines.prescription_id` | `fk_pharmacy_sale_lines_prescription` → `pharmacy_prescriptions(id)` SET NULL |
| `pharmacy_drug_substitution_requests.prescription_id` | `fk_pharmacy_substitution_request_prescription` → `pharmacy_prescriptions(id)` SET NULL |

P0-2-SUBBLOCKER-A is closed.

## 5. Defects found and fixed on the way

Each was a live bug, not a style issue:

| Defect | Effect |
| --- | --- |
| `~~StockLevel.is_deleted` (and on suppliers, movements, transfers, recalls, prescriptions, dispense queue) | The double negation cancels: these listings returned the **soft-deleted rows and only those**. Seven occurrences. |
| `not DrugBatch.is_quarantined` (three occurrences) | Python's `not` on a column object, not a SQL predicate — expiry auto-quarantine and cold-chain listing did not filter as written. |
| `initiated_by or str(self.user_id) if self.user_id else None` | Binds as `(a or b) if user else None`: an explicitly supplied initiator was discarded whenever there was no session user. |
| `resolve_recall` had no tenant filter | A recall could be resolved from another laboratory's session. |
| `calculate_reorder_quantity` had no tenant filter | Reorder maths aggregated across laboratories. |
| `ClinicalGuideline.version` typed `String(20)` under a base contributing `Integer` | Column shadowing. The physical column *is* `VARCHAR(20)` — the guideline's document version — so the entity now sits on a base without an optimistic-lock counter. |
| `get_prediction_accuracy` read `actual_consumption` | No such column. Actuals are now derived from the movement log, which is where dispensing is really recorded. |
| `get_affected_patients` read `recall.affected_patients` | No such column. Replaced by `get_notification_status`, returning what the schema does record. |
| `lazy="joined"` on locked relationships | A joined eager load emits a LEFT OUTER JOIN, and PostgreSQL refuses `FOR UPDATE` on the nullable side of one — every locked stock read would have failed. Caught by the concurrency test. |

## 6. Inventory integrity (M4-5, M4-8)

- Stock changes take `SELECT … FOR UPDATE` on the stock row and the batch, so
  two callers cannot both read the same quantity and each write their own total.
- Every quantity change writes a matching append-only `StockMovement` in the
  same transaction.
- `performed_by` and `wasted_by` are NOT NULL with foreign keys to `lab_users`:
  an inventory change is always somebody's action. The service now fails fast
  with a clear message rather than letting the database reject the write after
  recomputing the level.
- Quantities are floats throughout, because the physical columns are
  `DOUBLE PRECISION`. The previous `Integer` would have silently truncated half
  a tablet.

**Concurrency is proven on the database, not mocked.** Two independent
connections each try to take 6 units from a batch holding 10; the row lock
serialises them and the second sees 4 remaining and refuses.

## 7. Data safety (M4-6)

`20260911_0001` refuses to run in **either direction** unless the tables whose
identifier columns it retypes are empty, reporting per-table counts rather than
casting. Adding a public identity is not destructive and is not gated — it
backfills through `gen_random_uuid()` and is safe on populated tables.

Proven with a real legacy row (`batch_id = '01JLEGACYBATCHULID00000000'`):
upgrade refused, `alembic_version` stayed `20260910_0001`, `batch_id` stayed
`character varying`, and the row was intact afterwards.

## 8. API compatibility

This is the one place M4 changes contracts, and it is a deliberate, reported
change rather than a silent one.

Preserved: every identifier that was a string still is, now carrying a public
identity (`/batches/{batch_id}`, `/prescriptions/{rx_id}`, `drug_catalog_id`
everywhere, `batch_id` on sale lines).

Changed: the prescription, prescription-item, dispense-record, stock-level,
movement, transfer and recall response models advertised fields that do not
exist in any schema — `intent`, `priority`, `diagnosis_system`,
`substitution_allowed`, `strength_value`, `dose_quantity`, `refills`,
`manufacturer_batch`, `lot_number`, `total_amount` and others. Those endpoints
could never have returned a row, so there is no working client contract being
broken; keeping the fields would have meant publishing permanently-null data.
They now describe what the system actually stores. Quantities move from `int`
to `float` for the same reason as §6.

Responses are built through explicit builders rather than `model_validate`, so
an internal Integer key cannot leak into a payload.

## 9. Verification

| Evidence | Result |
| --- | --- |
| Clean PostgreSQL `alembic upgrade head` | pass, 105 revisions, single head `20260911_0001` |
| `downgrade -1` → `upgrade head` round trip | pass |
| 7/7 CI-required tables | pass |
| Fail-closed upgrade with a legacy ULID row | refused; revision, type and row all unchanged |
| ORM ↔ PostgreSQL parity, 27 tables | exact, both directions |
| `GULA-SCHEMA-002` | **VERIFIED, 0 findings** (243 at the start of M3 → 0) |
| `GULA-MIG-001` / `GULA-MIG-002` | VERIFIED, 0 findings, one head |
| `GULA-SCHEMA-001` | VERIFIED, 224 primary-key types resolved |
| `GULA-STATE-001` | VERIFIED, 0 findings |
| `GULA-ARCH-001` | 1 finding, `national_facilities` (NR-006 / P2-1), unchanged |
| Intelligent Core health | UNHEALTHY → **DEGRADED** |
| `test_pharmacy_inventory_identity_postgres.py` | 62 passed |
| All `-k pharmacy` tests | 140 passed |
| Tenant isolation / ABAC / clinical safety / stability | 145 passed |
| Ruff, changed scope | clean |
| MyPy, changed scope | **executed** (exit 1, "checked 6 source files"); 169 → 135, no new error categories |

## 10. Remaining gaps

**P0-2-M4-GAP-STOCK-NULL-STORE — CLOSED** by `20260912_0001`. See §12.

**P0-2-M4-GAP-STOCK-WAREHOUSE — open, needs a domain decision.** The schema and
the application disagree about whether a warehouse is part of a stock row's
identity. `uq_pharmacy_stock` covers `(lab_id, drug_id, batch_id, store_id)` and
excludes `warehouse_id`, while `StockAdjustmentService` looked stock up by
warehouse *and* store. M4 aligned the lookup to the constraint, because a filter
on a column the schema does not treat as identifying can miss a row the database
then refuses to insert. Nothing populates `warehouse_id` today — no production
path writes it — so the question is not yet reachable, but it is unresolved:
either warehouse-held stock is a first-class location and belongs in the
uniqueness key, or `warehouse_id` is vestigial and should go. Neither is
derivable from the repository.

**External-domain identifiers.** `pharmacy_sales.patient_id`, `.citizen_id`,
`.encounter_id`, `pharmacy_sale_lines.medication_dispense_id` and
`pharmacy_drug_substitution_requests.patient_id` / `.citizen_id` are still
`VARCHAR(26)`. These point *out* of the Pharmacy domain, at the national and EHR
models, which key on `String(26)` themselves. Reconciling them belongs to those
domains, not to P0-2. No Pharmacy entity keys on `String(26)` any more.

## 11. What M4 did not do

- did not invent a practitioner relationship for Prescription;
- did not invent an `actual_consumption` column or an affected-patient list;
- did not add the partial unique index above without knowing the data;
- did not modify any existing migration;
- did not touch domains outside Pharmacy.

The Generation B base is gone: `BaseEntity`, `TenantEntity`, `AuditEntity`,
`TenantAuditEntity` and `_ulid()` are deleted from `app/pharmacy/base.py`, as
that class's own docstring said they would be once the last model moved off.

---

## 12. Post-M4 hardening

**P0-2-M4-GAP-STOCK-NULL-STORE is closed** (`20260912_0001`).

The evidence settled it. `store_id` is **optional by design, not a legacy
artifact**: `PharmacyService.create_batch` — the batch-receipt path, and the
primary way stock enters the system — opens a stock row with no store *and* no
warehouse, because a dispensing point is assigned later, if ever. Making
`store_id` NOT NULL would break that path, so option A is disproven by the code
that runs.

What was wrong was never the nullability; it was that the constraint did not
mean what it said. `uq_pharmacy_stock` has covered
`(lab_id, drug_id, batch_id, store_id)` since the platform migration, and both
`batch_id` and `store_id` are nullable, so SQL's default — every NULL distinct —
voided the guarantee for exactly the rows that are the norm.

PostgreSQL provides the exact remedy: `UNIQUE NULLS NOT DISTINCT` (15+; every
deployment target here is 16 or 17, verified). It states the intent already
written into the constraint, without a partial index per nullable combination
and without touching nullability.

Fail-closed: tightening a uniqueness rule can only fail on data that already
violates it, so the migration counts the offending groups and aborts naming
them, rather than letting PostgreSQL reject the index with one opaque row.
Nothing is merged or deleted — which of two real stock rows is authoritative is
a data question. Proven: with two location-less rows for the same drug present,
the upgrade refused, the revision stayed `20260911_0001`, both rows survived and
the constraint was untouched.

Two smaller corrections came with it:

* the ORM declared `uq_pharmacy_stock_lab_drug_batch_store`, a constraint name
  that has never existed physically — M4 introduced it, and `GULA-SCHEMA-002`
  compares columns and types rather than constraint names, so nothing caught it;
* `adjust_stock` and `_stock_row` now filter on the uniqueness key itself, so a
  lookup cannot miss a row the database would then reject as a duplicate.
