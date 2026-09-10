# GULA Canonical Architecture Decisions

**BATCH-2 · 2026-09-10 · `production_ready: false`**

Only two kinds of entry appear here: a decision the repository's own evidence
settles, and a decision it does not. Nothing is recorded on the strength of what
would be reasonable, conventional, or clinically sensible. Where the evidence
runs out, the entry says so and names the question.

Evidence base: `GULA_CANONICAL_DISPOSITION_MATRIX.{md,json}`.

---

## 1. Canonical ownership

One owner, many consumers. Derived from foreign-key direction and from which
domain's base maps the table.

### Settled by evidence

| Entity | Canonical owner | Evidence |
|---|---|---|
| Drug / catalog | `pharmacy` | 27/27 tables physical, zero drift, `drug_id` UUID4 public identity — the finished reference implementation |
| Drug batch, prescription, dispense record, stock | `pharmacy` | reconciled in P0-2 M3/M4; settled, not reopened |
| Blood unit, component, crossmatch, transfusion | `blood_bank` | own base, own state machine, no cross-base FKs |
| Lab order, result, specimen, report | `models` (core) + `lims` | `app.models.base.Base` maps `patients`, `labs`, `lab_orders`, `lab_results`; 121/143 physical |
| Patient (lab-scoped) | `models` (core) — `patients`, physical, 22 inbound references |
| Lab user / staff | `models` (core) — `lab_users`, physical, 21 inbound references |
| Workspace, membership, session, authority | `identity` | 87/87 physical, 83 `KEEP` |
| Radiology study/report | `radiology` | 17/17 physical (drifting, hence `RECONCILE`) |
| Data-warehouse aggregates | `nhdw` | 14/14 physical |

### Unsettled — ownership genuinely ambiguous

| Entity | Competing owners | Why the repository cannot decide |
|---|---|---|
| **`national_facilities`** | `app.models.base.Base` **and** `app.national.base.AuditEntity` | The only table mapped by two bases. It is physical, so both mappings are live against one table. NR-006. |
| **Person / patient at national scope** | `national` (`national_patients`, `national_citizens`) vs core (`patients`) | Both exist as concepts; `patients` is physical and lab-scoped, `national_patients` is mapped, unbuilt, and referenced 51 times. Nothing states whether they are the same person seen twice or two entities. |
| **Practitioner** | `national` (`national_practitioners`, 58 references) vs core (`lab_users`, 21 references) | Same shape of question. |
| **Encounter** | `national` (`national_encounters`, 42 references) | No competing owner, but no owner has built it either. |

---

## 2. Identity classification

The Pharmacy model is the established pattern and is **not** reopened:
internal `INTEGER` primary key, immutable public `UUID4`, mutable business
`drug_code` that is never a key.

| Class | Rule | Status |
|---|---|---|
| Internal DB PK | `INTEGER`, never public | Pharmacy, identity, core: settled |
| Public ID | `UUID4`, immutable, the only identifier an API may expose | Pharmacy: settled |
| Business code | mutable, never a key, never a join target | Pharmacy `drug_code`: settled |
| External ID | identifier owned by another domain; **not** converted merely because the consumer uses integer keys | `patient_id`, `citizen_id`, `encounter_id`, `medication_dispense_id` remain `String(26)`: settled |

**Measured gap.** Every EHR table keys on `VARCHAR` — the Generation-B shape
Pharmacy was moved off. If EHR is built, it needs the same identity
reconciliation, not a copy of its current models. This is an observation from
the physical evidence, not yet a decision.

---

## 3. Tenancy scope

Derived from the presence of `lab_id` / `facility_id` / `patient_id` columns.

| Scope | Rule | Examples |
|---|---|---|
| `TENANT` | has `lab_id`; every query must filter it | pharmacy, lims, blood bank, core patients |
| `FACILITY` | has `facility_id` | parts of blood bank inventory, some EHR |
| `PATIENT` | patient-keyed, no `lab_id` | most EHR clinical records |
| `GLOBAL` | national reference data; a tenant filter would be **wrong** | clinical guidelines, `national_*` reference tables |

**A tenant filter must not be added to a `GLOBAL` entity, and must never be
missing from a `TENANT` one.** One live violation of the second half is recorded
as NR-021.

---

## 4. Decisions this batch deliberately did not make

Each would be irreversible, and none is derivable from the repository.

1. **Is `national_patients` the same entity as `patients`?** Merge, project, or
   keep both. Affects `ehr`, `care_continuum`, `nursing`, `national_data` —
   every domain whose foreign keys point at it.
2. **Who owns `national_facilities`?** Core or national. NR-006.
3. **Should the 216 `CREATE_PHYSICAL` tables be built, and in what order?**
   The matrix says they are required by reachable operations; it does not say
   the product wants those operations.
4. **Should the 39 `RETIRE` candidates be deleted?** Evidence says nothing uses
   them. Evidence cannot say nobody intends to.
5. **Which of the 10 unregistered declarative bases join `target_metadata`?**
   Registering changes what autogenerate emits — a schema decision, recorded in
   §5 of the final report with a recommendation per base.

---

## 5. Single platform contract

Checked, and holding: identity, authorization (RBAC + ABAC), the error envelope,
audit hash-chaining, the outbox event path and reference data are each
implemented once and consumed by every domain. No domain was found carrying its
own parallel implementation of any of them.

The divergence that does exist is not in the contract but beneath it: domains
disagree about which entity is canonical (§1), so they consume the same
contract against different notions of the same person.
