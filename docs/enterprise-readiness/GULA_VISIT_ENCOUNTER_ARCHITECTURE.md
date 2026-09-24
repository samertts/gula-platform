# Visit / Encounter / CanonicalEncounter — Architecture Closure

**Batch:** BATCH-2.7 — documentation. Nothing is renamed, migrated or created.

---

## 1. The three entities, and what each actually is

| | `visits` | `national_encounters` | `CanonicalEncounter` |
|---|---|---|---|
| Kind | **physical table** | **ORM model, no table** | **abstract class, no table** |
| Where | migration `20260505_0003` | `app/national/domain/encounter.py` | `app/national_data/models/canonical_encounter.py` |
| Key | `UUID` (`gen_random_uuid()`) | `String(26)` `_ulid()` | none — it is a query |
| Tenancy | derived via `patients.lab_id` | `lab_id NOT NULL` (contradicts national scope) | derived from `national_patients.lab_id` |
| Columns | 6 | 20 | 16 projected |
| Referenced by | `lab_orders.visit_id` (**enforced FK**) | 47 ORM foreign keys, **0 physical** | nothing |
| Read/written by code | **nothing** | one service that cannot run | `query_all()` / `get_by_id()` |
| Rows possible today | no writer exists | table does not exist | n/a |

### The decisive evidence

Migration `20260505_0003_sndhs_phase1_visits_table.py` states the architecture
in its own docstring:

> *Visit-based architecture: every clinical action is anchored to a visit.*

and the database enforces it:

```
lab_orders.visit_id UUID  →  visits.id     constraint fk_lab_orders_visit_id
visits.patient_id   INT   →  patients.id
```

**Correction to BATCH-2.6.** That batch reported `visits` as having code
consumers. It has **none**. Every apparent hit was a substring false positive —
`national_visits`, `FactPatientVisit`, `max_visits`, `"visits": 0` in a JSON
payload, `anc_visits`, and an external `/api/visits` URL. An exact-name search
finds no query, insert or update anywhere in `backend/app/`.

That makes adoption *lower* risk than BATCH-2.6 implied: there is no live usage
to migrate. It also makes the table inert — it is schema without behaviour.

## 2. Semantic roles — resolved

| Role | Owner | Justification |
|---|---|---|
| **Transactional owner** | `visits` | The only episode entity that is physical, and the only one any table has a real foreign key to |
| **Clinical episode anchor** | `visits` | Stated by its own migration; `lab_orders.visit_id` already implements it |
| **National projection** | `national_encounters` | Non-physical, `PROJECTION` disposition; no foreign key may point at it |
| **Projection implementation** | `CanonicalEncounter` | Already the read model: `__abstract__`, joins encounter → national patient → lab order |
| **FHIR representation** | `Encounter` | `visits.visit_type`/`status` map to `Encounter.class`/`Encounter.status`; the national `EncounterType`/`EncounterStatus` enums are the richer vocabulary |
| **Interoperability mapping** | `national/fhir/encounter.py` | Already exists; it maps the *national* model, so it must be repointed when Visit is adopted |
| **Lifecycle** | `open → closed` (`status`, `closed_at`) | Six columns only; the national `EncounterStatus` has eight states |
| **Tenant scope** | **derived**, via `patients.lab_id` | `visits` carries no `lab_id` — the open question below |

## 3. The canonical relationship

```
patients  (Core, INTEGER, lab_id NOT NULL)
    │
    │  visits.patient_id  ──►  enforced FK
    ▼
visits    (Core, UUID, tenancy derived through patients)
    │
    │  the anchor every clinical action references
    ├──────────────► lab_orders.visit_id            ENFORCED TODAY
    ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌► pharmacy_sales.encounter_id     VARCHAR(26),  no FK
    ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌► blood_bank_*.encounter_id       VARCHAR(100), no FK  (3 tables)
    ├╌╌╌╌╌╌╌╌╌╌╌╌╌╌► billing_invoices.encounter_ref  VARCHAR(128), no FK
    └╌╌╌╌╌╌╌╌╌╌╌╌╌╌► 47 ORM FKs aimed at national_encounters (a PROJECTION)
                     care_continuum 16 · ehr 14 · nursing 12 · national 5

        ═══► enforced      ╌╌╌► intended, unconstrained, six incompatible types
```

**One domain out of six is wired correctly.** Laboratory has the foreign key;
pharmacy, blood bank, billing, nursing and the clinical/EHR packages each
invented their own untyped reference.

## 4. Per-consumer disposition

| Domain | Today | Target | Migration shape |
|---|---|---|---|
| Laboratory | `lab_orders.visit_id UUID` + FK | unchanged | none |
| Pharmacy | `pharmacy_sales.encounter_id VARCHAR(26)` | `visit_id UUID` + FK | backfill NULL, retype, add FK |
| Blood Bank | 3 × `encounter_id VARCHAR(100)` | `visit_id UUID` + FK | same |
| Billing | `encounter_ref VARCHAR(128) NOT NULL` | `visit_id UUID` + FK | **hardest** — NOT NULL with no default |
| Nursing | 12 ORM columns, **none physical** | `visit_id UUID` | ORM only; nothing deployed |
| Clinical / EHR / Care Continuity | 30 ORM FKs to a projection | repoint to `visits` | ORM only; none physical |

Nursing, Clinical, EHR and Care Continuity are ORM-only — 42 of the 47
references cost nothing to repoint because no table carries them.

## 5. What `visits` needs before it can carry this

Six columns is not an encounter. Missing, and each is a decision rather than an
oversight:

- **`lab_id`** — or the explicit ruling that tenancy stays derived;
- **`facility_id`**, **`practitioner_id`** — the national core supplies both,
  and both are unbuilt;
- **encounter type taxonomy** — `visit_type VARCHAR(40)` versus the national
  `EncounterType` enum's ten values;
- **period semantics** — `created_at`/`closed_at` versus
  `period_start`/`period_end`/`duration_minutes`;
- **`fhir_id`** — every other clinical entity carries one.

## 6. Status

**Visit is formally established as the existing clinical episode anchor.**
Nothing in the repository disproves it, and three independent lines of evidence
support it: the migration's own statement of intent, the enforced foreign key
from `lab_orders`, and the absence of any competing physical episode table.

**Still BLOCKED — CLINICAL OWNER REQUIRED**, unchanged from BATCH-2.6:

1. Does `visits` gain an explicit `lab_id`, or does tenancy stay derived?
2. Is `visit_type` extended, or replaced by the national `EncounterType`?
3. Does adoption require enabling `SNDHS_ENABLE_VISITS`, and what is the
   backfill path for the four physical string columns — most sharply
   `billing_invoices.encounter_ref`, which is `NOT NULL`?

## 7. Not done

No rename, no migration, no ORM model for `visits`, no repointing of the 47
foreign keys. `visits` stays in the NR-030 exclusion list, classified
**BLOCKED**, until question 1 is answered.
