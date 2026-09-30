# NATIONAL_PATIENTS DECISION PACKAGE

Lane `claude/independent-audit-1`, worktree `/home/user/gula-audit`, database
`gula_agent2` (head `20260916_0001`, 423 tables, untouched). No migration authored, no
schema changed, no ORM changed. IA-004 not modified.

**Headline: this is not a new decision. It is NR-022, already named and owned.**

The integration lineage's own migration `20260914_0001_citizen_relationship_person_fk.py`
says so in its docstring, and reaches the same conclusion this lane reached independently
from different evidence:

> `patient_id` is deliberately untouched. It names `national_patients`, also unbuilt, and
> the built clinical patient table keys on `INTEGER` against this `VARCHAR(26)` column —
> so there is no target to point it at **until NR-022 decides the clinical subject**.

So the deliverable here is not a proposal. It is the evidence NR-022 needs, gathered
adversarially and independently.

---

## 1. The four live referencing tables, end to end

61 of the 65 FK columns naming `national_patients` sit on tables that do not exist. Only
four are on present tables. **RUNTIME VERIFIED** against `gula_agent2`.

| # | table | physical column | physical FK | rows |
|---|---|---|---|---|
| 1 | `pharmacy_prescriptions` | `patient_id INTEGER` nullable | → **`patients.id`** | 0 |
| 2 | `pharmacy_dispense_records` | `patient_id INTEGER` nullable | → **`patients.id`** | 0 |
| 3 | `pharmacy_drug_returns` | `patient_id INTEGER` nullable | → **`patients.id`** | 0 |
| 4 | `niam_citizen_relationships` | `patient_id VARCHAR` nullable | **none** | 0 |

Two further pharmacy tables carry the same physical shape (`pharmacy_dispense_queue`,
`pharmacy_drug_monitoring` → `patients.id`), so the physical pattern is six tables wide.

### The full chain, per lineage

The chain differs by lineage, and that difference is the whole story. **This lane's ORM is
176 commits behind the lineage that built the database (IA-008), so both are stated.**

| layer | integration lineage `ce097a0c` — **what ships** | this lane `18626dbe` |
|---|---|---|
| route request schema | `patient_id: int \| None` (5 sites) | `patient_id: str` (5 sites) |
| route → service | `routes.py:743 create_prescription` → `services.py:222` | same shape |
| service → model | `Prescription(**data)` — pass-through, no coercion | same |
| ORM column | `Column(Integer, nullable=True)` | `Column(String(26), FK national_patients.id)` |
| physical column | `INTEGER` → FK `patients.id` | (same database) |
| **coherent?** | **yes — all three layers agree on `patients.id INTEGER`** | **no** |

**Finding: there is NO pharmacy patient-identity defect in the shipping lineage.**
Route, ORM and physical schema agree. **NO DEFECT FOUND**, recorded as a result in its own
right. What this lane measured earlier as a 216-column pharmacy drift was cross-lane
staleness, retracted under IA-008.

### Does the application send integer or string patient ids?

The shipping lineage sends **integers** on the write paths (`patient_id: int | None`), and
that matches the column. But it still declares **string** on five sites in the same file,
five `str` against five `int`. One of those is a served read endpoint and is a live defect
— see **IA-012** in `findings.md`.

`POSSaleCreate` (lineage `routes.py:1641`) is the clearest statement of intent: it carries
**both** `patient_id: str | None` **and** `billing_patient_id: int | None`. That is
deliberate dual identity, not confusion — and it mirrors `national_patients.lab_patient_id`.

## 2. Historical archaeology

| question | evidence |
|---|---|
| when did `patients` appear? | `20250322_0000_create_base_schema.py` — the immutable bootstrap snapshot. `id INTEGER` from a sequence, 16 columns, demographics + identity only. |
| when did `national_patients` appear? | **never, physically.** No migration in either lineage creates it. It exists only as an ORM model, `app/national/domain/patient.py`, `id VARCHAR(26)`, 45 columns. |
| which migrations touch their relationship? | `20260811_0002_citizen_relationship_foundation.py` declared an FK to `national_patients` and had to guard it on `_has_table`, so it never created it (**IA-004**). `20260914_0001_citizen_relationship_person_fk.py` re-pointed the sibling column `citizen_id` to `niam_persons` and **deliberately left `patient_id` alone**. |
| which ADRs assign ownership? | **ADR-016** composes the EHR Patient from `patients`, `lab_results`, `lab_orders`, `visits` — it never names `national_patients`. `CLAUDE.md` gives the national citizen registry to `nhop-platform`, which owns its own `citizens` table in its own service. |
| which code still uses `national_patients`? | the 61 dormant FK columns (`cc_*` 35, `ehr_*` 15, `national_*` 11), `ehr_service.get_national_patient_or_404` reached by every patient-scoped `/ehr` route, and `app/national/fhir/patient.py`. All over a table that does not exist. |
| legacy/dormant, or intended canonical? | **Neither cleanly.** It is *unbuilt but structurally central*: 45 columns of Iraqi-specific clinical identity, 65 inbound FKs, and `lab_patient_id` pointing back at legacy `patients` — a model written to coexist with `patients`, not replace it. |

### How this squares with NR-022 and NR-064

* **NR-064** is resolved: `20260914_0001` fixed the `citizen_id` arm by pointing it at
  `niam_persons`, on NR-022's finding that a natural person is `niam_persons`. The FK
  `fk_citizen_relationship_person` exists in `gula_agent2`. **INDEPENDENTLY VERIFIED.**
* **NR-022** still owns the clinical subject, and that is exactly what `patient_id` needs.
  The migration author said so explicitly rather than guessing — the same discipline this
  lane is held to.

### Is `patients` the canonical clinical patient, or the lab-local one?

The honest answer from the evidence is **both, unresolved**:

* **for `patients`:** it is the bootstrap table, it is what every migrated FK points at
  (six pharmacy tables, `ins_claims.patient_id`), and ADR-016 composes the EHR Patient
  from it. Every layer that was actually reconciled chose it.
* **against `patients`:** 16 columns, no clinical content, no Iraqi name structure, no
  governorate/district, no blood group, no merge lineage, no `citizen_id` link. It is
  scoped by `lab_id` — a per-lab record, which is what `CLAUDE.md` calls "the per-lab LIMS
  view".
* **three demographic stores exist**, not two: `patients` (16 cols, present),
  `niam_persons` (25 cols, present, no clinical linkage), `national_patients` (45 cols,
  absent).

## 3. Why an incremental path exists but cannot start yet

* the **61 dormant references cost nothing** — their tables do not exist, so changing
  their ORM columns has no data implication. **STATIC VERIFIED.**
* the **4 live references are already integer-typed in the database** and hold 0 rows, so
  aligning the ORM to the schema would be ORM-only, no DDL. **RUNTIME VERIFIED.**
* what **cannot** be done incrementally is choosing the clinical subject. A straight
  re-point is not datatype-compatible: `VARCHAR(26)` against `INTEGER` across 63 NOT NULL
  columns. And if `national_patients` is dropped, 45 columns of Iraqi clinical identity
  have no home, because `patients` at 16 columns cannot absorb them.

## 4. What NR-022 has to decide, stated as options

Neutral, with evidence both ways. **No recommendation — this needs the committee.**

| option | for | against |
|---|---|---|
| **A. `patients` is the canonical clinical subject.** Retire `national_patients`; re-point the 61 dormant FKs to `patients.id INTEGER`. | matches every reconciled layer and ADR-016; no new table; the 4 live references already conform | loses 45 columns of Iraqi identity and merge lineage; `patients` is `lab_id`-scoped, so a national record becomes per-lab; contradicts `lab_patient_id`'s design intent |
| **B. `national_patients` is canonical; build it.** | preserves the Iraqi clinical identity model and the 65-FK topology as designed; `lab_patient_id` bridges to legacy cleanly | needs a migration plus a statement of how it reconciles with `patients` and nhop's `citizens` without becoming a third source of truth for patient identity; 63 NOT NULL columns to convert |
| **C. `niam_persons` is the person, `patients` is the clinical encounter subject.** | `niam_persons` already exists and NR-022 already chose it for *person*; consistent with the `citizen_id` fix | `niam_persons` has no clinical linkage at all — no `lab_patient_id`, no `citizen_id`, no merge lineage; still leaves the clinical subject unnamed |

**Status: BLOCKED — NR-022 architectural decision.** Nothing in this package was
implemented. `national_patients` was not created, no FK was added or removed, no ORM type
changed, and IA-004's migration was not touched.
