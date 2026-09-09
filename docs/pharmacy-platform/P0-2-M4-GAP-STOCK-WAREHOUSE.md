# P0-2-M4-GAP-STOCK-WAREHOUSE — Is `warehouse_id` part of stock identity?

Status: **split verdict.**

- The narrow question — *does `warehouse_id` belong in the `StockLevel`
  uniqueness key?* — is **VERIFIED: NOT REQUIRED**. The current invariant is
  already correct and no schema, migration, ORM, service or API change is
  needed.
- The broad question — *is a warehouse a first-class inventory location in
  GULA?* — is **BLOCKED**. The schema models one, the org model names roles for
  one, and no code anywhere implements one. Answering it is an architecture
  decision, not a reconciliation finding.

This document records the evidence for both halves so the question is not
re-opened from memory.

---

## 1. What the physical schema says

Four tables reference `pharmacy_warehouses`:

| Referencing column | Nullable | On delete |
|---|---|---|
| `pharmacy_stores.warehouse_id` | yes | CASCADE |
| `pharmacy_stock_levels.warehouse_id` | yes | SET NULL |
| `pharmacy_inventory_transfers.from_warehouse_id` | yes | SET NULL |
| `pharmacy_inventory_transfers.to_warehouse_id` | yes | SET NULL |

`pharmacy_warehouses` itself has exactly one outbound FK: `lab_id → labs`.
There is **no** FK from any pharmacy table to `national_facilities`. A warehouse
is therefore tenant(lab)-scoped, not facility-scoped. Nothing in the repository
connects the pharmacy warehouse to the national facility hierarchy.

Two consequences matter for identity:

1. **`pharmacy_stores.warehouse_id` is nullable.** A store need not sit inside a
   warehouse, so `store_id` does not functionally determine `warehouse_id`.
2. **Nothing ties `stock.warehouse_id` to `stock.store_id`.** There is no
   composite FK and `pharmacy_stock_levels` carries **no CHECK constraint at
   all**. The schema permits a stock row whose `store_id` belongs to warehouse
   W1 while its `warehouse_id` says W2. That contradiction is currently
   unreachable only because of §2 — not because the schema prevents it.

A third, separate location representation exists in parallel: a free-text
`location VARCHAR` column on `pharmacy_stock_levels`, `pharmacy_stores`,
`pharmacy_warehouses` and drug batches. So the repository contains three
competing notions of "where the stock is": warehouse FK, store FK, and free
text.

## 2. What the code says

Searched: routes, services, inventory, seeds, migrations, demo generator,
frontend, device bridge, edge agent.

- **No endpoint, service method, seed script, demo generator or migration ever
  constructs a `Warehouse` or a `Store`.** The two ORM classes are imported
  nowhere outside `models.py` and the tests written for this analysis.
- The demo generator creates a `warehouse_manager` **role**, and the org model
  names `warehouse_officer` / `warehouse_manager`. Those are permissions for a
  subsystem that does not exist.
- The frontend has zero references to pharmacy warehouses or stores.
- `receive_transfer` moves stock **by store only**, even though
  `pharmacy_inventory_transfers` carries `from_warehouse_id` / `to_warehouse_id`.
  The transfer table's warehouse columns are written by nothing and read by
  nothing but the response builder.

Empirically, on a migrated database: `pharmacy_warehouses` has 0 rows,
`pharmacy_stores` has 0 rows, and inserting a stock row with
`warehouse_id = 42` fails with a foreign-key violation. `warehouse_id` is
**reachable but unusable**: a caller may set it and cannot ever set it to a
valid value.

## 3. Governance evidence

- The Phase 2A reconciliation matrix classified `warehouse_id` as **RECONCILE
  (keep the column)**, not `REMOVE_FROM_ORM`. M4 honoured that.
- There is **no ADR** covering pharmacy inventory location. `ADR-017` concerns
  the *data* warehouse (NHDW) and is unrelated — the word collides, the concept
  does not.

## 4. Decision matrix

| Question | Evidence | Conclusion | Confidence | Impact |
|---|---|---|---|---|
| Does `warehouse_id` identify a stock row? | No creation path exists; column is always NULL; FK rejects any value | **No** | High | None — status quo |
| Does `store_id` determine `warehouse_id`? | `pharmacy_stores.warehouse_id` is nullable | **No** | High | Blocks deriving one from the other |
| Would adding `warehouse_id` to the key strengthen it? | It would *weaken* it: an always-NULL column added to a `NULLS NOT DISTINCT` key adds a constant, and to a default key would void the constraint entirely | **No** | High | Would reintroduce the M4 gap |
| Is warehouse facility-scoped? | Zero FKs to `national_facilities`; only `lab_id` | **No — lab-scoped** | High | Rules out option C as currently modelled |
| Is warehouse first-class today? | Schema models it across 4 tables; no code implements it; no ADR | **Undecided** | — | Architecture decision required |
| Is `location VARCHAR` the real location? | Present on 4 tables, also written by nothing structured | **Unresolved duplicate** | Medium | Part of the same decision |

Against the objective's options: **(D) optional metadata only** describes what
`warehouse_id` *is* today, factually. **(B) first-class inventory location** is
what the schema was evidently *drafted* for. The repository does not contain
the evidence to choose between them — that is the blocked decision.

## 5. The invariant, and why it stands

```
UNIQUE NULLS NOT DISTINCT (lab_id, drug_id, batch_id, store_id)  -- uq_pharmacy_stock
```

This is correct as written and must not change:

- `lab_id` — tenant isolation, NOT NULL.
- `drug_id` — the item, NOT NULL.
- `batch_id` — nullable and legitimately so: a stock row can exist before batch
  attribution.
- `store_id` — nullable and legitimately so: receiving opens a stock row before
  a dispensing point is assigned.

`NULLS NOT DISTINCT` (added in `20260912_0001`) is what makes the nullable half
mean anything; SQL's default treats every NULL as unique, so before that
migration the constraint guaranteed nothing for exactly the rows that need it.

Adding `warehouse_id` would be actively harmful, not merely useless: the column
is unconditionally NULL, so under `NULLS NOT DISTINCT` it contributes a constant
to every tuple (no discrimination gained, one more column to keep consistent),
and under any future default-NULLS variant it would make every stock row
trivially distinct — silently restoring the duplicate-stock gap M4 closed.

## 6. Regression guard

`backend/tests/test_pharmacy_inventory_identity_postgres.py`:

- `test_warehouse_is_not_part_of_stock_identity` — asserts the physical
  constraint columns are exactly `(lab_id, drug_id, batch_id, store_id)` and
  that `warehouse_id` is absent.
- `test_nothing_can_create_a_warehouse_or_a_store` — asserts the premise of the
  first test rather than trusting this document: no `Warehouse(` or `Store(`
  construction in routes or services. **If a creation path is ever added, this
  test fails and the identity question above must be re-answered, not
  inherited.**

No schema, migration, ORM, service or API change was made.

## 7. Open items requiring a decision (not fixed here)

1. **Is a pharmacy warehouse a real entity?** If yes, it needs creation
   endpoints, a decision on lab- vs facility-scoping, a public identifier per
   CANONICAL_DRUG_CONTRACT §2, reconciliation with the free-text `location`
   column, and a rule tying `stock.warehouse_id` to `stock.store_id`. If no, the
   four columns and two tables are dead schema and should be retired
   deliberately. **Do not implement either until this is decided.**

2. **`GET /inventory/stock-levels` filters leak and mistype internal keys.**
   `warehouse_id` and `store_id` arrive as `str` query params and are compared
   directly against `Integer` columns
   (`backend/app/pharmacy/services.py:1512-1516`). A numeric string works by
   PostgreSQL's implicit literal typing; a non-numeric one raises
   `InvalidTextRepresentation` and surfaces as a 500 rather than a 422. It is
   also an internal integer key on the public API surface, which
   CANONICAL_DRUG_CONTRACT §3 forbids. Correcting it *properly* means giving
   warehouses and stores public identifiers — which is item 1. It is left
   untouched deliberately, and is currently unreachable because no warehouse or
   store can exist.
