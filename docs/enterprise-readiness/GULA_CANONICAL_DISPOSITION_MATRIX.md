# GULA Canonical Disposition Matrix

**BATCH-2 · generated 2026-09-10 · head `1d62d57d` · `production_ready: false`**

Machine-readable companion: `GULA_CANONICAL_DISPOSITION_MATRIX.json` (every one of the
807 tables, with its full evidence row). Regenerate with
`scripts/enterprise_readiness/disposition.py`.

Every disposition below is **rule-derived from measured evidence**. None is hand-assigned,
and no table was given a disposition its evidence does not support.

## 0. Method

Physical schema read from a database at alembic head 20260912_0001. Declarative bases and drift come from the GULA Intelligent Core detectors (GULA-SCHEMA-002/003/004, GULA-ARCH-002), not a reimplementation. Reachability comes from the booted-app route survey. Dispositions are rule-derived from that evidence; none is hand-assigned.

The rules, in order — order matters:

| # | Condition | Disposition |
|---|---|---|
| 1 | mapped by two declarative bases | `MERGE` — ownership question before anything else |
| 2 | physical **and** column drift | `RECONCILE` |
| 3 | physical, no drift | `KEEP` |
| 4 | missing, FKs target tables outside its base | `CROSS_DOMAIN_OWNER` — cannot be created alone |
| 5 | missing, reachable API operations touch it | `CREATE_PHYSICAL` (P0) |
| 6 | missing, referenced by a service/route module | `CREATE_PHYSICAL` (P1) |
| 7 | missing, named in the migration chain | `BLOCKED` — dropped, conditional, or never applied? |
| 8 | missing, referenced more than once in app code | `DEFER` |
| 9 | otherwise | `RETIRE` |

Rule 3 is why the old picture looked healthy: calling a drifting physical table `KEEP`
is how 1,677 findings stayed invisible.

## 1. Totals

| Measure | Count |
|---|---|
| Mapped tables | **807** |
| Physical at head | **405** |
| No physical table | **402** |
| Declarative bases | **19** |
| Bases in alembic `target_metadata` | **9** |
| Reachable operations | **2102** |

## 2. Disposition counts

| Disposition | Count | Meaning |
|---|---|---|
| `KEEP` | **209** | physical and agrees with the ORM |
| `RECONCILE` | **194** | physical but the ORM disagrees |
| `CREATE_PHYSICAL` | **216** | required persistence that does not exist |
| `CROSS_DOMAIN_OWNER` | **77** | cannot be built until another domain's schema is settled |
| `DEFER` | **70** | referenced but not required by any reachable path |
| `RETIRE` | **39** | no evidence it was ever shipped |
| `MERGE` | **2** | one table, two owners |

Unused this pass: `REPLACE`, `PROJECTION`, `EXTERNAL_REFERENCE`, `BLOCKED`, `UNMEASURED` —
no table's evidence matched them. They are not removed; they were simply not earned.

## 3. By domain

| Domain | Keep | Reconcile | Create Physical | Cross Domain Owner | Defer | Retire | Merge | Total |
|---|---|---|---|---|---|---|---|---|
| `national` | 3 | 79 | 57 |  | 34 | 17 | 1 | 191 |
| `models` | 70 | 50 | 22 |  |  |  | 1 | 143 |
| `identity` | 83 | 4 |  |  |  |  |  | 87 |
| `governance` |  | 6 | 56 |  |  | 2 |  | 64 |
| `care_continuum` |  |  |  | 45 |  |  |  | 45 |
| `clinical` |  | 2 | 27 |  | 1 | 11 |  | 41 |
| `national_data` |  |  | 14 | 9 | 9 | 4 |  | 36 |
| `financial` | 22 | 3 | 5 |  |  | 1 |  | 31 |
| `pharmacy` | 27 |  |  |  |  |  |  | 27 |
| `health_data` |  |  | 1 |  | 20 | 3 |  | 24 |
| `document_intelligence` |  |  | 21 |  |  |  |  | 21 |
| `ehr` |  |  | 2 | 16 |  |  |  | 18 |
| `radiology` |  | 17 |  |  |  |  |  | 17 |
| `nursing` |  | 13 |  | 2 |  |  |  | 15 |
| `hospital` | 4 |  | 9 |  |  | 1 |  | 14 |
| `nhdw` |  | 14 |  |  |  |  |  | 14 |
| `insurance` |  |  | 2 | 5 | 6 |  |  | 13 |
| `trust` |  | 6 |  |  |  |  |  | 6 |

**Pharmacy is 27/27 `KEEP`** — the only domain with no outstanding disposition at all.
**Identity is 83 `KEEP` / 4 `RECONCILE`.** Those two are the finished reference points.

## 4. The structural finding

Four of the five most-depended-on tables in the repository do not exist.

| Table | Referenced by | Physical | Mapped by |
|---|---|---|---|
| `national_practitioners` | 58 | **no** | `national` |
| `national_citizens` | 51 | **no** | `national` |
| `national_patients` | 51 | **no** | `national` |
| `national_facilities` | 44 | yes | `models` |
| `national_encounters` | 42 | **no** | `national` |
| `patients` | 22 | yes | `models` |
| `lab_users` | 21 | yes | `models` |
| `national_organizations` | 8 | **no** | `national` |

`care_continuum`, `ehr`, `nursing` and `national_data` all hang off a `national` core —
patient, citizen, practitioner, encounter — that has never been built. **EHR is not the
critical path; the national core is.** Building EHR first would only move the same
unresolved foreign keys one layer up.

The single exception is `national_facilities`, which *is* physical — and is the one table
mapped by two bases (`app.models.base.Base` and `app.national.base.AuditEntity`). The one
anchor the national layer already has is the one whose ownership is ambiguous. That is
NR-006, reached here independently from FK evidence.

| Consumer | Owner | References |
|---|---|---|
| `care_continuum` | `national` | 153 |
| `ehr` | `national` | 60 |
| `care_continuum` | `models` | 39 |
| `nursing` | `models` | 27 |
| `national_data` | `models` | 12 |
| `nursing` | `national` | 12 |
| `trust` | `models` | 8 |
| `insurance` | `models` | 5 |
| `ehr` | `models` | 4 |
| `identity` | `models` | 4 |

## 5. Operations

| Classification | Operations |
|---|---|
| `MEASURED` — resolve to a mapped table | 1923 |
| `NOT_REACHABLE_NO_PERSISTENCE` — domain has zero ORM tables | 118 |
| `UNRESOLVED` — domain has tables, the operation resolves to none | **61** |

The 179 previously unmeasured operations reduce to **61 genuinely unresolved** (58 `national`,
3 `identity`). The other 118 belong to `ai_fabric`, `kernel`, `integration`, `platform` and
`certification` — orchestration layers that map no tables at all, so having no table is the
correct answer for them, not a gap. The remaining 61 stay `UNRESOLVED`, not healthy.

