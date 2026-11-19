# Specimen — Independent Adversarial Audit (Account 2)

**Claim attacked:** LIMS `Specimen` and core `Sample` are two live specimen stores.
**Verdict: CONFIRMED.** Runtime proof `backend/tests/verification/test_specimen_dual_store.py` (6 tests).

## IA-066 — one physical label, two specimen rows · P1 · CONFIRMED

| | `samples` | `lims_specimens` |
|---|---|---|
| `barcode` | **unique=True** | **unique=True** |
| anchor | `order_id → lab_orders.id` | `order_id → lab_orders.id` |
| other FKs | — | `labs.id`, `lab_users.id`, `lims_specimens.id`, `lims_storage.id` |
| reference to the other store | **none** | **none** |

Uniqueness is **per table**, so the same barcode exists once in each. Measured:

```
barcode='SPEC-DUAL-0001' exists as samples.id=1 AND lims_specimens.id=1
```

`db.flush()` accepted both — there is no cross-table constraint to violate.

**What the per-table constraint does protect**, so the gap is precise: a second `samples`
row with the same barcode is refused with `IntegrityError`. Real protection, scoped to one
table.

**Correlation:** shared column *names* are `barcode`, `collected_by`, `collection_time`,
`created_at`, `id`, `order_id`, `rejection_reason`, `status` — descriptive, not identifying.
`barcode` is the only identifying overlap and it is not a key between them. No `sample_id`
on the LIMS side, no `specimen_id` on the core side.

### The intent contradiction, pinned

`Specimen`'s docstring: *"Complete specimen lifecycle — **replaces** existing Sample model."*
Yet the core `Sample` is still written by three served route modules, measured:
`routes/samples.py`, `routes/device_results.py`, `routes/test_results.py`. "Replaces" is not
what the route tree does.

**Chain-of-custody consequence:** a barcode scanned at the bench resolves to two rows whose
`status`, `collected_by` and `rejection_reason` can diverge independently, with no schema-level
way to detect it. This is the specimen analogue of IA-062 and the same decision gate applies.

**Not fixed.** No correlation column, no migration, no merge.
